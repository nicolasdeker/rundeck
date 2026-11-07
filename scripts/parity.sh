#!/usr/bin/env bash
# scripts/parity.sh — run the UPSTREAM functional-test suite (legacy/functional-test, Spock + testcontainers) against
# either the legacy image (baseline) or the Rust server `rdx`, and produce parity-report.json (MISSION §5 step 5, §7).
#
# Facts this script relies on (all in legacy/, pinned at v6.3.0 — never edited, MISSION §8):
#   - Gradle 8.14.5 wrapper (legacy/gradle/wrapper/gradle-wrapper.properties), JDK 17 (legacy/gradle/java-version.gradle:2-3).
#   - Test tasks in legacy/functional-test/build.gradle: apiTest (:120), pluginBlocklistTest (:134),
#     apiTestNodeExecutorSecureInput (:144), seleniumCoreTest (:156), alphaUiSeleniumCoreTest (:170), ldapTest (:186),
#     jdbcTest (:196). Each sets COMPOSE_PATH and a spock.configuration that includes one annotation
#     (apiTest → @APITest, spock-configs/IncludeAPITestsConfig.groovy). -PtestFiles=<newline list> includes specific
#     tests (:81-118, :129-131); Gradle --tests patterns also work (JUnit platform, useJUnitPlatform() :121).
#   - API specs live in legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/api/<package>/ (20 packages,
#     64 specs); jdbc and ldap carry @JdbcTest/@LdapTest and run only under jdbcTest/ldapTest with their own compose
#     files (docker/jdbc, docker/ldap) — Phase 4 items.
#   - BaseContainer (src/test/groovy/org/rundeck/util/container/BaseContainer.groovy:48-49, :104-116) connects to
#     TEST_RUNDECK_URL with TEST_RUNDECK_TOKEN (default admintoken) WITHOUT starting any fixture when that variable is
#     set; otherwise (:127-154) it starts the compose fixture through testcontainers (RdComposeContainer.groovy:54-72:
#     passes TEST_IMAGE, every TEST_<name>_IMAGE and TEST_RUNDECK_GRAILS_URL to compose, waits for the log line
#     "Grails application running at"). setupSpec() always generates the ssh keys first (BaseContainer.groovy:678-696)
#     into .build/tmp/keys (relative to the Gradle project dir legacy/functional-test) and reuses them when present.
#   - upstream CI runs: TEST_OSS_TOOLS_IMAGE=<prebuilt or "tools"> TEST_IMAGE=<image> ./gradlew :functional-test:<task>
#     -Penvironment=... (legacy/scripts/circleci/build-functions.sh:134-148).
#
# Usage: scripts/parity.sh [--target legacy|rdx] [--filter <package|SpecClass|glob>] [--task <gradle test task>]
#                          [--out <parity-report.json>] [--no-gate] [--help]
#        scripts/parity.sh <SpecClass or filter>        (MISSION §5 step 5 short form, same as --filter)
#   --target   legacy = baseline on the upstream image (env PARITY_TARGET, default rdx; PARITY_IMAGE overrides the image,
#              default rundeck/rundeck:6.3.0). rdx = the Rust server (see "rdx target" below).
#   --filter   an API package name (acl authorizations basic execution executor export_import filecopy jdbc job ldap
#              nodes plugin project resourceModel schedule scm storage system workflow workflowSteps) maps to
#              --tests "org.rundeck.tests.functional.api.<package>.*"; a fully qualified class is used as is; anything
#              else maps to --tests "*<filter>*". Empty = the whole task.
#   --task     Gradle test task, default apiTest.
#   --out      report path, default parity-report.json (JSON; the Markdown summary is printed and written next to it).
#   --no-gate  always exit 0 after writing the report (the legacy baseline behaves like this by default: a failing
#              upstream test on the upstream image is a fact to record in PARITY.md, not a gate).
#
# Exit codes: 0 all tests passed, or (target rdx) every failure is listed in tests/parity-skips.toml, or --no-gate,
#             or target legacy with a complete run; 1 unexcused failures (rdx) or no test result produced (both targets);
#             2 usage / missing tool (JDK 17, docker, python3); 3 target rdx and no rdx server is available.
#
# Environment handling (both targets):
#   JAVA_HOME      autodetected JDK 17: $JAVA_HOME if it is 17, else /usr/lib/jvm/java-17-openjdk-amd64, the
#                  actions/setup-java export JAVA_HOME_17_X64, or /usr/lib/jvm/*17*. Anything else → exit 2.
#   TESTCONTAINERS_RYUK_DISABLED=true  exported unless already set: the ryuk sidecar image pull is rate-limited by Docker
#                  Hub (429) in the cloud; ComposeContainer tears the fixture down itself when the JVM exits.
#   TEST_OSS_TOOLS_IMAGE  set to rdx-oracle-tools:6.3.0 when `docker image inspect` finds it (built by
#                  scripts/oracle/build-tools-image.sh with the proxy CA baked in) or to $ORACLE_TOOLS_IMAGE; otherwise
#                  left unset so the fixture builds its own `tools` stage (apt + pip, docker/compose/oss/Dockerfile:6-18).
#   No IPv6 (/proc/net/if_inet6 absent — the Claude Code cloud sandbox): the upstream rundeck service passes
#                  -agentlib:jdwp=...address=*:5005 and the JVM dies ("transport error 202"), so this script exports
#                  RDX_ORACLE_COMPOSE_OVERLAY=<repo>/scripts/oracle/compose-overlay and the Gradle init script
#                  scripts/gradle-init.d/rdx-oracle-overlay.gradle points COMPOSE_PATH at
#                  docker/compose/oss/docker-compose.rdx-cloud.yml (extends every upstream service, overrides only the
#                  rundeck and ssh-node commands). One line is printed when this happens. PARITY_FORCE_OVERLAY=1 forces it.
#   Maven Central 429: when ~/.ccr/ca-bundle.crt exists (cloud) or PARITY_GRADLE_MIRROR=1, the init script
#                  scripts/gradle-init.d/central-mirror.gradle redirects Central to Google's mirror. Init scripts already
#                  installed in ~/.gradle/init.d/ (scripts/cloud-setup.sh) are not passed twice.
#
# rdx target (Phase 1 provides the server; until then this exits 3 before running anything):
#   RDX_URL (or TEST_RUNDECK_URL) must name a running rdx server, e.g. http://localhost:4440, answering
#   GET /api/60/system/info with RDX_TOKEN (default admintoken). Intended wiring, implemented but not exercised yet:
#     1. `scripts/oracle.sh prepare` copies the fixture to .oracle/fixture and generates the ssh keys into
#        legacy/functional-test/.build/tmp/keys (the suite's own scratch dir, reused by setupPrivateSSHKeys) so that
#        ssh-node authorizes them (node/init.sh:21-22) — set PARITY_FIXTURE=0 to skip the fixture entirely.
#     2. `docker compose -p rdx-parity -f <fixture> up -d rundeck-db gitea ssh-node mock-server` starts every service
#        of the upstream compose file EXCEPT rundeck (host ports 3307 mysql, 3000 gitea, 8080 mock-server, ssh-node
#        dynamic). The rdx server must use that MySQL (jdbc:mysql://127.0.0.1:3307/rundeck rundeck/rundeck), the fixture's
#        tokens.properties and realm.properties, and expose the private keys at /home/rundeck/privatekeys
#        (JschNodeExecutorSpec.groovy:18) — Phase 1 adds the `rdx` start here (binary from target/ or an image).
#     3. TEST_RUNDECK_URL=$RDX_URL TEST_RUNDECK_TOKEN=$RDX_TOKEN ./gradlew ... (no fixture started by the tests).
#     4. Report with the known skips applied; exit 1 on unexcused failures unless --no-gate.
#   In parity.yml the rdx job is gated on the repository variable PARITY_RDX_ENABLED == 'true'; Phase 1 flips it with
#   `gh api -X PATCH repos/nicolasdeker/rundeck/actions/variables/PARITY_RDX_ENABLED -f value=true` (create it first with
#   `gh api -X POST repos/nicolasdeker/rundeck/actions/variables -f name=PARITY_RDX_ENABLED -f value=true`).
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LEGACY=$ROOT/legacy
FT=$LEGACY/functional-test
API_PKG_DIR=$FT/src/test/groovy/org/rundeck/tests/functional/api
API_PKG_PREFIX=org.rundeck.tests.functional.api
SKIPS=$ROOT/tests/parity-skips.toml
REPORT_PY=$ROOT/scripts/parity-report.py
DEFAULT_TOOLS_IMAGE=rdx-oracle-tools:6.3.0

TARGET=${PARITY_TARGET:-rdx}
FILTER=""
TASK=apiTest
OUT=parity-report.json
GATE=1

log() { echo "[parity] $*" >&2; }
die() { log "error: $1"; exit "${2:-1}"; }
usage() { sed -n '/^# Usage:/,/^# rdx target/p' "${BASH_SOURCE[0]}" | sed '$d' | sed 's/^# \{0,1\}//'; }
help_full() { sed -n '2,/^set -euo pipefail/p' "${BASH_SOURCE[0]}" | sed '$d' | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --target) [ $# -ge 2 ] || { usage; exit 2; }; TARGET=$2; shift 2 ;;
    --target=*) TARGET=${1#*=}; shift ;;
    --filter) [ $# -ge 2 ] || { usage; exit 2; }; FILTER=$2; shift 2 ;;
    --filter=*) FILTER=${1#*=}; shift ;;
    --task) [ $# -ge 2 ] || { usage; exit 2; }; TASK=$2; shift 2 ;;
    --task=*) TASK=${1#*=}; shift ;;
    --out) [ $# -ge 2 ] || { usage; exit 2; }; OUT=$2; shift 2 ;;
    --out=*) OUT=${1#*=}; shift ;;
    --no-gate) GATE=0; shift ;;
    -h|--help) help_full; exit 0 ;;
    -*) log "unknown argument: $1"; usage; exit 2 ;;
    *) # MISSION §5 step 5 form: scripts/parity.sh <SpecClass or filter>
       [ -z "$FILTER" ] || { log "only one filter is allowed (got '$FILTER' and '$1')"; usage; exit 2; }
       FILTER=$1; shift ;;
  esac
done
case "$TARGET" in legacy|rdx) ;; *) log "invalid --target '$TARGET' (legacy|rdx)"; usage; exit 2 ;; esac
[[ "$TASK" =~ ^[A-Za-z][A-Za-z0-9]*$ ]] || die "invalid --task '$TASK'" 2
case "$OUT" in /*) ;; *) OUT=$PWD/$OUT ;; esac

# --- JDK 17 -------------------------------------------------------------------------------------------------------------
java_major() { "$1/bin/java" -version 2>&1 | sed -n 's/.*version "\([0-9]*\).*/\1/p' | head -1; }
find_jdk17() {
  local c
  for c in "${JAVA_HOME:-}" /usr/lib/jvm/java-17-openjdk-amd64 "${JAVA_HOME_17_X64:-}" /usr/lib/jvm/temurin-17-jdk-amd64 \
           /usr/lib/jvm/*17* /opt/hostedtoolcache/Java_Temurin-Hotspot_jdk/17*/x64; do
    [ -n "$c" ] && [ -x "$c/bin/java" ] && [ "$(java_major "$c")" = "17" ] && { echo "$c"; return 0; }
  done
  return 1
}
JAVA_HOME=$(find_jdk17) || die "JDK 17 not found (legacy/gradle/java-version.gradle requires it); install openjdk-17-jdk-headless or set JAVA_HOME" 2
export JAVA_HOME
log "JAVA_HOME=$JAVA_HOME ($("$JAVA_HOME/bin/java" -version 2>&1 | grep -m1 ' version ' || true))"
command -v python3 >/dev/null || die "python3 is required for the report" 2
[ -x "$LEGACY/gradlew" ] || die "$LEGACY/gradlew missing" 2

# --- filter → --tests -----------------------------------------------------------------------------------------------------
GRADLE_TESTS=()
if [ -n "$FILTER" ]; then
  if [ -d "$API_PKG_DIR/$FILTER" ]; then
    GRADLE_TESTS=(--tests "$API_PKG_PREFIX.$FILTER.*")
  elif [[ "$FILTER" == *.* ]]; then
    GRADLE_TESTS=(--tests "$FILTER")
  else
    GRADLE_TESTS=(--tests "*$FILTER*")
  fi
  log "filter '$FILTER' -> ${GRADLE_TESTS[*]}"
fi

# --- shared environment -----------------------------------------------------------------------------------------------------
export TESTCONTAINERS_RYUK_DISABLED=${TESTCONTAINERS_RYUK_DISABLED:-true}
have_docker() { command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; }
if [ -z "${TEST_OSS_TOOLS_IMAGE:-}" ]; then
  if [ -n "${ORACLE_TOOLS_IMAGE:-}" ]; then
    export TEST_OSS_TOOLS_IMAGE=$ORACLE_TOOLS_IMAGE
  elif have_docker && docker image inspect "$DEFAULT_TOOLS_IMAGE" >/dev/null 2>&1; then
    export TEST_OSS_TOOLS_IMAGE=$DEFAULT_TOOLS_IMAGE
    log "TEST_OSS_TOOLS_IMAGE=$DEFAULT_TOOLS_IMAGE (prebuilt tools stage found)"
  fi
fi
GRADLE_INIT=()
add_init_script() { # <file>: pass --init-script unless cloud-setup.sh already installed it in ~/.gradle/init.d
  [ -f "$HOME/.gradle/init.d/$(basename "$1")" ] || GRADLE_INIT+=(--init-script "$1")
}
if [ ! -e /proc/net/if_inet6 ] || [ "${PARITY_FORCE_OVERLAY:-0}" = "1" ]; then
  export RDX_ORACLE_COMPOSE_OVERLAY=$ROOT/scripts/oracle/compose-overlay
  add_init_script "$ROOT/scripts/gradle-init.d/rdx-oracle-overlay.gradle"
  log "no IPv6 on this host (/proc/net/if_inet6 absent): RDX_ORACLE_COMPOSE_OVERLAY=$RDX_ORACLE_COMPOSE_OVERLAY -> docker/compose/oss/docker-compose.rdx-cloud.yml"
fi
if [ "${PARITY_GRADLE_MIRROR:-auto}" = "1" ] || { [ "${PARITY_GRADLE_MIRROR:-auto}" = "auto" ] && [ -f "$HOME/.ccr/ca-bundle.crt" ]; }; then
  add_init_script "$ROOT/scripts/gradle-init.d/central-mirror.gradle"
fi

# --- target-specific setup ------------------------------------------------------------------------------------------------
IMAGE=""
FIXTURE_COMPOSE=()
# shellcheck disable=SC2317  # invoked through the EXIT trap of the rdx target
cleanup_rdx_fixture() {
  if [ ${#FIXTURE_COMPOSE[@]} -gt 0 ] && [ "${PARITY_KEEP_FIXTURE:-0}" != "1" ]; then
    docker compose -p rdx-parity "${FIXTURE_COMPOSE[@]}" down --remove-orphans --volumes >/dev/null 2>&1 || true
  fi
}
case "$TARGET" in
  legacy)
    # Exactly as upstream: the tests start the compose fixture themselves (no TEST_RUNDECK_URL).
    have_docker || die "the legacy target needs a reachable Docker daemon (testcontainers starts the fixture)" 2
    unset TEST_RUNDECK_URL TEST_RUNDECK_TOKEN
    IMAGE=${PARITY_IMAGE:-rundeck/rundeck:6.3.0}
    export TEST_IMAGE=$IMAGE
    log "target legacy: TEST_IMAGE=$TEST_IMAGE (the suite starts the compose fixture itself)"
    ;;
  rdx)
    RDX_URL=${RDX_URL:-${TEST_RUNDECK_URL:-}}
    RDX_TOKEN=${RDX_TOKEN:-${TEST_RUNDECK_TOKEN:-admintoken}}
    if [ -z "$RDX_URL" ]; then
      cat >&2 <<EOF
[parity] no rdx server is available: RDX_URL (or TEST_RUNDECK_URL) is not set.
[parity] The Rust server does not exist yet (Phase 1 provides the binary/image and the start-up wiring, see
[parity] 'scripts/parity.sh --help', section "rdx target"). Nothing was run. Use --target legacy for the baseline.
EOF
      exit 3
    fi
    command -v curl >/dev/null || die "curl is required to probe the rdx server" 2
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 -H "X-Rundeck-Auth-Token: $RDX_TOKEN" \
           -H 'Accept: application/json' "$RDX_URL/api/60/system/info" 2>/dev/null || true)
    if [ "$code" != "200" ]; then
      log "no rdx server answered 200 at $RDX_URL/api/60/system/info (got '${code:-no response}'); nothing was run"
      exit 3
    fi
    if [ "${PARITY_FIXTURE:-1}" != "0" ]; then
      have_docker || die "the rdx target needs Docker for the fixture services (PARITY_FIXTURE=0 to skip them)" 2
      # Keys first (BaseContainer.groovy:678-679 order), into the suite's scratch dir so setupPrivateSSHKeys reuses them.
      mapfile -t fixture_files < <(ORACLE_KEYS_DIR="$FT/.build/tmp/keys" bash "$ROOT/scripts/oracle.sh" prepare)
      for f in "${fixture_files[@]}"; do FIXTURE_COMPOSE+=(-f "$f"); done
      trap cleanup_rdx_fixture EXIT
      log "starting the fixture services except rundeck (project rdx-parity)"
      TEST_IMAGE=unused TEST_RUNDECK_GRAILS_URL="$RDX_URL" TEST_RUNDECK_FEATURE_NAME=placeholderFeatureName \
        docker compose -p rdx-parity "${FIXTURE_COMPOSE[@]}" up -d --build rundeck-db gitea ssh-node mock-server
    fi
    export TEST_RUNDECK_URL=$RDX_URL TEST_RUNDECK_TOKEN=$RDX_TOKEN
    IMAGE="rdx@$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown) ($RDX_URL)"
    log "target rdx: TEST_RUNDECK_URL=$TEST_RUNDECK_URL"
    ;;
esac

# --- run Gradle --------------------------------------------------------------------------------------------------------------
RESULTS=$FT/build/test-results/$TASK
rm -rf "$RESULTS"   # stale XML from a previous run must not leak into this report (Gradle output dir, not a source)
STARTED=$(date -u +%FT%TZ)
GRADLE_ARGS=(--no-daemon --continue --console=plain -Penvironment=development
             -Dorg.gradle.internal.repository.max.retries=8 -Dorg.gradle.internal.repository.initial.backoff=3000)
log "cd legacy && ./gradlew ${GRADLE_ARGS[*]} ${GRADLE_INIT[*]} :functional-test:$TASK ${GRADLE_TESTS[*]}"
set +e
(cd "$LEGACY" && ./gradlew "${GRADLE_ARGS[@]}" "${GRADLE_INIT[@]}" ":functional-test:$TASK" "${GRADLE_TESTS[@]}")
GRADLE_EXIT=$?
set -e
FINISHED=$(date -u +%FT%TZ)
log "gradle exited with $GRADLE_EXIT"

shopt -s nullglob
XMLS=("$RESULTS"/TEST-*.xml)
shopt -u nullglob
if [ ${#XMLS[@]} -eq 0 ]; then
  die "no JUnit XML under $RESULTS — the suite did not run (gradle exit $GRADLE_EXIT); nothing to report" 1
fi

# --- report -------------------------------------------------------------------------------------------------------------------
REPORT_ARGS=(--target "$TARGET" --image "$IMAGE" --task "$TASK" --filter "$FILTER" --started "$STARTED"
             --finished "$FINISHED" --gradle-exit "$GRADLE_EXIT" --skips "$SKIPS" --out "$OUT" --markdown)
[ "$TARGET" = "rdx" ] && [ "$GATE" = "1" ] && REPORT_ARGS+=(--gate)
MD=${OUT%.json}.md
set +e
python3 -I "$REPORT_PY" "${REPORT_ARGS[@]}" "${XMLS[@]}" | tee "$MD"
STATUS=${PIPESTATUS[0]}
set -e
log "report: $OUT (markdown: $MD)"
if [ "$TARGET" = "legacy" ]; then
  [ "$GATE" = "1" ] && log "legacy baseline: failures are recorded, not gated (see --help); exit 0"
  exit 0
fi
[ "$GATE" = "1" ] || { log "--no-gate: exit 0"; exit 0; }
exit "$STATUS"
