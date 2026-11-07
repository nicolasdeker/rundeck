#!/usr/bin/env bash
# scripts/oracle.sh — the legacy Rundeck 6.3.0 oracle (MISSION §5 step 3 "golden files", §6 Phase 0 "Prove the oracle").
#
# Runs the UPSTREAM functional-test compose fixture, unchanged, as a black box to compare `rdx` against:
#   fixture:  legacy/functional-test/src/test/resources/docker/compose/oss/docker-compose.yml
#             services rundeck (built over ${TEST_IMAGE} with a `tools` stage selectable via TEST_OSS_TOOLS_IMAGE, lines
#             2-8), rundeck-db mysql:8.4.11 (line 77), gitea (line 86), ssh-node from rundeck/node-demo (line 103, node/
#             Dockerfile:1), mock-server nginx (line 114). Host ports are fixed by the fixture: 4440 (rundeck), 3307 (db),
#             3000 (gitea), 8080 (mock-server); ORACLE_PORT only remaps the rundeck port through an override file.
#   token:    tokens.properties (`admin:admintoken,admin`) mounted at /home/rundeck/server/config/tokens.properties
#             (docker-compose.yml:44 + RUNDECK_TOKENS_FILE line 17); realm.properties has admin/admin123 (line 45).
#   keys:     the tests generate RSA keypairs id_rsa and id_rsa_passphrase (passphrase testpassphrase123, comment
#             "test private key", mode 0600) into the fixture's keys/ dir before starting compose
#             (BaseContainer.groovy:678-696 setupSpec/setupPrivateSSHKeys, :867-891 generatePrivateKey with JSch, PEM RSA).
#             ssh-node authorizes both public keys (node/init.sh:21-22) and the rundeck image gets the private keys at
#             /home/rundeck/privatekeys (oss/Dockerfile:26-28). This script does the same with ssh-keygen -m PEM.
#   readiness: testcontainers waits for the log line "Grails application running at" (RdComposeContainer.groovy:69-72).
#
# legacy/ is never written (MISSION §8): the resources tree is copied under .oracle/fixture/ (git-ignored) and the keys
# are generated there. The compose file's relative volume paths (../../../tokens.properties, docker-compose.yml:44-57)
# are preserved by copying the whole layout. No IPv6 on the host (/proc/net/if_inet6 absent, e.g. the Claude Code
# cloud sandbox): the upstream rundeck service passes -agentlib:jdwp=...address=*:5005 and the JVM dies with
# "transport error 202"; then the overlay scripts/oracle/compose-overlay/docker/compose/oss/docker-compose.rdx-cloud.yml
# (extends every upstream service, overrides only the rundeck/ssh-node commands) is copied next to the upstream file
# and used instead. Docker Hub rate-limits anonymous pulls (429): when the prebuilt tools image rdx-oracle-tools:6.3.0
# exists (scripts/oracle/build-tools-image.sh) or ORACLE_TOOLS_IMAGE is set, it is passed as TEST_OSS_TOOLS_IMAGE so the
# fixture skips its network-heavy `tools` stage.
#
# Usage: scripts/oracle.sh <command> [args]
#   up                      build + start the fixture (project rdx-oracle), wait until ready, print URL and token
#   down                    stop and remove the fixture containers, networks and volumes (images are kept)
#   logs [compose args]     docker compose logs (default: --tail=200 rundeck)
#   url                     print the oracle base URL (http://localhost:${ORACLE_PORT})
#   token                   print the static admin API token read from the fixture's tokens.properties
#   prepare                 only refresh .oracle/fixture (copy + keys); prints the compose file(s) to use (used by parity.sh)
#   capture <name> <METHOD> <path> [json-body-file]
#                           perform the request against the running oracle with X-Rundeck-Auth-Token and write
#                           tests/golden/<name>.json {request, status, normalized headers, body} (see tests/golden/README.md)
# Env: ORACLE_IMAGE (rundeck/rundeck:6.3.0), ORACLE_PORT (4440), ORACLE_COMPOSE (the upstream compose file; another file
#      in the same directory such as docker-compose-context-path.yml also works), ORACLE_TOOLS_IMAGE (prebuilt tools image;
#      default: rdx-oracle-tools:6.3.0 when it exists), ORACLE_KEYS_DIR (where the ssh keys live, default .oracle/keys),
#      ORACLE_READY_TIMEOUT (seconds, 600 like testcontainers), ORACLE_ACCEPT / ORACLE_CONTENT_TYPE (capture headers,
#      default application/json), ORACLE_FORCE_OVERLAY=1 (use the no-IPv6 overlay even when IPv6 exists).
# Exit codes: 0 ok, 1 runtime failure (oracle not ready, request failed), 2 usage / missing tool.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
ORACLE_IMAGE=${ORACLE_IMAGE:-rundeck/rundeck:6.3.0}
ORACLE_PORT=${ORACLE_PORT:-4440}
LEGACY_RESOURCES=$ROOT/legacy/functional-test/src/test/resources
ORACLE_COMPOSE=${ORACLE_COMPOSE:-$LEGACY_RESOURCES/docker/compose/oss/docker-compose.yml}
ORACLE_DIR=$ROOT/.oracle
ORACLE_KEYS_DIR=${ORACLE_KEYS_DIR:-$ORACLE_DIR/keys}
ORACLE_READY_TIMEOUT=${ORACLE_READY_TIMEOUT:-600}
FIXTURE=$ORACLE_DIR/fixture
OVERLAY_SRC=$ROOT/scripts/oracle/compose-overlay/docker/compose/oss/docker-compose.rdx-cloud.yml
DEFAULT_TOOLS_IMAGE=rdx-oracle-tools:6.3.0
PROJECT=rdx-oracle
GOLDEN_DIR=$ROOT/tests/golden
TOKEN_FALLBACK=admintoken   # RdComposeContainer.groovy:20 STATIC_TOKEN default

log() { echo "[oracle] $*" >&2; }
die() { log "error: $1"; exit "${2:-1}"; }
usage() {
  sed -n '/^# Usage:/,/^# Exit codes:/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}
need() { command -v "$1" >/dev/null 2>&1 || die "missing tool: $1" 2; }
need_docker() {
  need docker
  docker info >/dev/null 2>&1 || die "the Docker daemon is not reachable (docker info failed)" 2
  docker compose version >/dev/null 2>&1 || die "docker compose (v2 plugin) is required" 2
}

base_url() { echo "http://localhost:${ORACLE_PORT}"; }

# The static token comes from the first line of the fixture's tokens.properties (`admin:admintoken,admin`).
read_token() {
  local f="$LEGACY_RESOURCES/tokens.properties" line
  if [ -r "$f" ]; then
    line=$(grep -m1 '^admin:' "$f" || true)
    if [ -n "$line" ]; then line=${line#admin:}; echo "${line%%,*}"; return; fi
  fi
  echo "$TOKEN_FALLBACK"
}

has_ipv6() { [ -e /proc/net/if_inet6 ]; }

# --- fixture copy and keys ------------------------------------------------------------------------------------------
# Mirrors BaseContainer.generatePrivateKey (BaseContainer.groovy:867-891): RSA keypair, PEM private key (JSch writes
# "BEGIN RSA PRIVATE KEY", ssh-keygen -m PEM writes the same container), public key comment "test private key", 0600.
# Keys are reused when both files exist (same rule as the tests, :875-877).
generate_key() { # <dir> <name> [passphrase]
  local dir=$1 name=$2 pass=${3:-}
  if [ -s "$dir/$name" ] && [ -s "$dir/$name.pub" ]; then return; fi
  rm -f "$dir/$name" "$dir/$name.pub"
  ssh-keygen -q -t rsa -b 2048 -m PEM -C "test private key" -N "$pass" -f "$dir/$name"
  chmod 600 "$dir/$name"
}
ensure_keys() {
  command -v ssh-keygen >/dev/null 2>&1 || die "missing tool: ssh-keygen (apt-get install -y openssh-client)" 2
  mkdir -p "$ORACLE_KEYS_DIR"
  generate_key "$ORACLE_KEYS_DIR" id_rsa
  generate_key "$ORACLE_KEYS_DIR" id_rsa_passphrase testpassphrase123
}

# Copies the parts of legacy/functional-test/src/test/resources the compose file mounts (docker-compose.yml:41-57,
# 100, 110-112, 118-119) into .oracle/fixture with the same layout, then drops the keys into docker/compose/oss/keys.
prepare_fixture() {
  [ -f "$ORACLE_COMPOSE" ] || die "compose file not found: $ORACLE_COMPOSE" 2
  local compose_dir res_root
  compose_dir=$(cd "$(dirname "$ORACLE_COMPOSE")" && pwd)
  res_root=$(cd "$compose_dir/../../.." && pwd)
  [ -f "$res_root/tokens.properties" ] || die "unexpected fixture layout: $res_root/tokens.properties missing (ORACLE_COMPOSE must live in <resources>/docker/compose/oss/)" 2
  rm -rf "$FIXTURE"
  mkdir -p "$FIXTURE/docker/compose"
  cp -a "$compose_dir" "$FIXTURE/docker/compose/oss"
  cp -a "$res_root/tokens.properties" "$res_root/realm.properties" "$FIXTURE/"
  for d in resource-model test-files; do
    [ -d "$res_root/$d" ] && cp -a "$res_root/$d" "$FIXTURE/$d"
  done
  ensure_keys
  mkdir -p "$FIXTURE/docker/compose/oss/keys"
  cp "$ORACLE_KEYS_DIR"/id_rsa "$ORACLE_KEYS_DIR"/id_rsa.pub "$ORACLE_KEYS_DIR"/id_rsa_passphrase \
     "$ORACLE_KEYS_DIR"/id_rsa_passphrase.pub "$FIXTURE/docker/compose/oss/keys/"
  cp "$OVERLAY_SRC" "$FIXTURE/docker/compose/oss/"
}

# Prints the compose -f arguments to use. The overlay replaces the upstream file when the host has no IPv6.
COMPOSE_FILES=()
select_compose_files() {
  local main
  main="$FIXTURE/docker/compose/oss/$(basename "$ORACLE_COMPOSE")"
  if ! has_ipv6 || [ "${ORACLE_FORCE_OVERLAY:-0}" = "1" ]; then
    if [ "$(basename "$ORACLE_COMPOSE")" != "docker-compose.yml" ]; then
      die "no IPv6 on this host and the overlay only extends docker-compose.yml, not $(basename "$ORACLE_COMPOSE")" 2
    fi
    main="$FIXTURE/docker/compose/oss/$(basename "$OVERLAY_SRC")"
    log "no IPv6 on this host (/proc/net/if_inet6 absent): using the overlay compose file $(basename "$OVERLAY_SRC") (jdwp on 0.0.0.0:5005)"
  fi
  COMPOSE_FILES=(-f "$main")
  if [ "$ORACLE_PORT" != "4440" ]; then
    # `!override` (compose >= 2.24) replaces the fixture's fixed "4440:4440" mapping instead of appending to it.
    cat > "$ORACLE_DIR/ports.override.yml" <<EOF
services:
  rundeck:
    ports: !override
      - "${ORACLE_PORT}:4440"
EOF
    COMPOSE_FILES+=(-f "$ORACLE_DIR/ports.override.yml")
  fi
}

tools_image() {
  if [ -n "${ORACLE_TOOLS_IMAGE:-}" ]; then echo "$ORACLE_TOOLS_IMAGE"; return; fi
  if docker image inspect "$DEFAULT_TOOLS_IMAGE" >/dev/null 2>&1; then echo "$DEFAULT_TOOLS_IMAGE"; fi
}

# docker compose with the variables RdComposeContainer exports to the fixture (RdComposeContainer.groovy:56-67).
compose() {
  local tools
  tools=$(tools_image)
  env TEST_IMAGE="$ORACLE_IMAGE" \
      ${tools:+TEST_OSS_TOOLS_IMAGE="$tools"} \
      TEST_RUNDECK_GRAILS_URL="$(base_url)" \
      TEST_TARGET_PLATFORM="${TEST_TARGET_PLATFORM:-linux/amd64}" \
      TEST_RUNDECK_FEATURE_NAME="${TEST_RUNDECK_FEATURE_NAME:-placeholderFeatureName}" \
      docker compose -p "$PROJECT" "${COMPOSE_FILES[@]}" "$@"
}

probe() { # 0 when /api/60/system/info answers 200 with the token
  local code
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 -H "X-Rundeck-Auth-Token: $(read_token)" \
         -H 'Accept: application/json' "$(base_url)/api/60/system/info" 2>/dev/null || true)
  [ "$code" = "200" ]
}

wait_ready() {
  local deadline=$(( $(date +%s) + ORACLE_READY_TIMEOUT )) state
  log "waiting up to ${ORACLE_READY_TIMEOUT}s for 'Grails application running at' (RdComposeContainer.groovy:70) ..."
  while :; do
    state=$(compose ps --format '{{.Service}} {{.State}}' 2>/dev/null | awk '$1=="rundeck"{print $2}')
    if [ -n "$state" ] && [ "$state" != "running" ]; then
      compose logs --tail=60 rundeck >&2 || true
      die "the rundeck service is '$state' — see the log above (no IPv6? the overlay is selected automatically)"
    fi
    if compose logs --no-log-prefix rundeck 2>/dev/null | grep -q 'Grails application running at' && probe; then
      return 0
    fi
    [ "$(date +%s)" -lt "$deadline" ] || { compose logs --tail=60 rundeck >&2 || true; die "oracle not ready after ${ORACLE_READY_TIMEOUT}s"; }
    sleep 5
  done
}

cmd_prepare() {
  prepare_fixture
  select_compose_files
  printf '%s\n' "${COMPOSE_FILES[@]}" | awk 'NR%2==0'
}

cmd_up() {
  need_docker; need curl
  prepare_fixture
  select_compose_files
  local tools
  tools=$(tools_image)
  log "image $ORACLE_IMAGE, tools stage: ${tools:-built by the fixture (set ORACLE_TOOLS_IMAGE or run scripts/oracle/build-tools-image.sh)}"
  log "fixture copy: $FIXTURE"
  compose up -d --build
  wait_ready
  echo "ORACLE_URL=$(base_url)"
  echo "ORACLE_TOKEN=$(read_token)"
  log "ready. Try: curl -H 'X-Rundeck-Auth-Token: $(read_token)' $(base_url)/api/60/system/info"
}

cmd_down() {
  need_docker
  select_compose_files 2>/dev/null || COMPOSE_FILES=()
  if [ ${#COMPOSE_FILES[@]} -eq 0 ] || [ ! -f "${COMPOSE_FILES[1]}" ]; then
    # No fixture copy any more: remove by project name.
    docker compose -p "$PROJECT" down --remove-orphans --volumes 2>/dev/null \
      || log "nothing to remove for project $PROJECT"
    return
  fi
  compose down --remove-orphans --volumes
  log "fixture stopped (images kept)"
}

cmd_logs() {
  need_docker
  select_compose_files
  if [ $# -eq 0 ]; then compose logs --tail=200 rundeck; else compose logs "$@"; fi
}

# capture <name> <METHOD> <path> [json-body-file] → tests/golden/<name>.json
cmd_capture() {
  if [ $# -lt 3 ] || [ $# -gt 4 ]; then usage; exit 2; fi
  need curl; need python3
  local name=$1 method=$2 path=$3 body=${4:-}
  [[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ && "$name" != *..* ]] || die "golden name must match [A-Za-z0-9._/-]+ without '..': $name" 2
  [[ "$method" =~ ^[A-Z]+$ ]] || die "METHOD must be upper-case (GET, POST, PUT, DELETE ...): $method" 2
  [[ "$path" == /* ]] || die "path must start with '/' (e.g. /api/60/system/info): $path" 2
  [ -z "$body" ] || [ -r "$body" ] || die "body file not readable: $body" 2
  probe || die "no oracle answering at $(base_url) (run: scripts/oracle.sh up)"
  local accept=${ORACLE_ACCEPT:-application/json} ctype=${ORACLE_CONTENT_TYPE:-application/json}
  local tmp token url out
  tmp=$(mktemp -d); trap 'rm -rf "$tmp"' RETURN
  token=$(read_token); url="$(base_url)$path"
  local -a curl_args=(-sS --max-time 120 -X "$method" -D "$tmp/headers" -o "$tmp/body" -w '%{http_code}'
                      -H "X-Rundeck-Auth-Token: $token" -H "Accept: $accept")
  [ -n "$body" ] && curl_args+=(-H "Content-Type: $ctype" --data-binary "@$body")
  local status
  status=$(curl "${curl_args[@]}" "$url") || die "request failed: $method $url"
  out="$GOLDEN_DIR/$name.json"
  mkdir -p "$(dirname "$out")"
  python3 -I - "$out" "$name" "$method" "$path" "$status" "$tmp/headers" "$tmp/body" "$accept" \
    "${body:+$ctype}" "${body:-}" "$ORACLE_IMAGE" "$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)" <<'PY'
import datetime, json, re, sys
(out, name, method, path, status, hdr_file, body_file, accept, ctype, req_body_file, image, commit) = sys.argv[1:13]
# Volatile headers are dropped so two captures of the same request compare equal (tests/golden/README.md).
VOLATILE = re.compile(r"^(date|set-cookie|expires|connection|keep-alive|transfer-encoding|content-length|etag|"
                      r"last-modified|x-request-id|.*request-id|x-b3-.*|traceparent|tracestate)$")
headers = {}
with open(hdr_file, encoding="utf-8", errors="replace") as fh:
    for line in fh:
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip().lower()
        if VOLATILE.match(k):
            continue
        headers[k] = v.strip()
raw = open(body_file, "rb").read()
text = raw.decode("utf-8", errors="replace")
body, is_json = text, False
if "json" in headers.get("content-type", "") or (text[:1] in "{["):
    try:
        body, is_json = json.loads(text), True
    except ValueError:
        pass
req_body = None
if req_body_file:
    rb = open(req_body_file, "rb").read().decode("utf-8", errors="replace")
    try:
        req_body = json.loads(rb)
    except ValueError:
        req_body = rb
req_headers = {"accept": accept}
if ctype:
    req_headers["content-type"] = ctype
golden = {
    "schema": 1,
    "name": name,
    "captured": {"at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "oracle_image": image, "commit": commit, "tool": "scripts/oracle.sh capture"},
    "request": {"method": method, "path": path, "headers": req_headers, "body": req_body},
    "response": {"status": int(status), "headers": dict(sorted(headers.items())), "body_is_json": is_json, "body": body},
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(golden, fh, indent=2, ensure_ascii=False, sort_keys=False)
    fh.write("\n")
print(out)
PY
  log "captured $method $path -> HTTP $status"
}

main() {
  [ $# -ge 1 ] || { usage; exit 2; }
  local cmd=$1; shift
  case "$cmd" in
    up)      [ $# -eq 0 ] || { usage; exit 2; }; cmd_up ;;
    down)    [ $# -eq 0 ] || { usage; exit 2; }; cmd_down ;;
    logs)    cmd_logs "$@" ;;
    url)     [ $# -eq 0 ] || { usage; exit 2; }; base_url ;;
    token)   [ $# -eq 0 ] || { usage; exit 2; }; read_token ;;
    prepare) [ $# -eq 0 ] || { usage; exit 2; }; cmd_prepare ;;
    capture) cmd_capture "$@" ;;
    -h|--help|help) usage ;;
    *) usage; exit 2 ;;
  esac
}
main "$@"
