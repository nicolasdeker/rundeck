#!/usr/bin/env bash
# cloud-setup.sh — setup script of the "rdx" Claude Code cloud environment.
#
# The environment runs its setup script as root from the directory that holds the repository checkouts
# (the PARENT of this repository), not from the repository root. The environment's setup-script line is therefore:
#     if [ -d rundeck ]; then bash rundeck/scripts/cloud-setup.sh; fi
# This script changes to its own repository root first, so it also works when run from inside the checkout.
# Fresh Ubuntu 24.04 VM (4 vCPU / 16 GB / 30 GB, Docker available). It must finish in < ~5 minutes so the
# environment snapshot is cached; everything heavy runs in parallel and is best-effort (a failed step never fails
# the script). Keep it idempotent. Agent: keep this file current, and note in JOURNAL.md when it changes so the
# owner re-saves the environment (the snapshot is taken when the environment is first used).
# CLOUD_SETUP_DRY_RUN=1 prints the resolved repository root and the steps without running them.
set -uo pipefail
export DEBIAN_FRONTEND=noninteractive
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 0
log() { echo "[cloud-setup] $*"; }
log "repository root: $PWD"
if [ "${CLOUD_SETUP_DRY_RUN:-0}" = "1" ]; then
  log "dry run: apt packages, docker pulls (rundeck/rundeck:6.3.0, mysql:8.4.11, postgres:16), rust tools, pnpm/ui deps, gradle warm-up"
  exit 0
fi
budget() { timeout --signal=TERM "$1" bash -c "$2" || log "step timed out or failed (non-fatal): ${2:0:60}"; }
pull() { # Docker Hub answers 429 to anonymous pulls from shared egress IPs: retry a few times, never fail.
  for i in 1 2 3; do docker pull -q "$1" >/dev/null 2>&1 && return 0; sleep $((20 * i)); done
  log "could not pull $1 (non-fatal; sessions pull it on demand)"
}

# 1) System packages: JDK 17 for the legacy functional-test build (Gradle 8.14), PAM/SSL headers for rdx crates,
#    shellcheck for scripts, k6/hyperfine come later via scripts/bench.
budget 200 'apt-get update -qq >/dev/null && apt-get install -y -qq --no-install-recommends \
  openjdk-17-jdk-headless libpam0g-dev libssl-dev pkg-config clang lld jq bc unzip shellcheck openssh-client >/dev/null' &

# 2) Docker images for the oracle and DB fixtures (cached by the snapshot; containers are started per session).
#    mysql:8.4.11 is the version pinned by legacy/functional-test/src/test/resources/docker/compose/oss/docker-compose.yml.
budget 270 "$(declare -f log pull); pull rundeck/rundeck:6.3.0" &
budget 120 "$(declare -f log pull); pull mysql:8.4.11" &
budget 120 "$(declare -f log pull); pull postgres:16" &

# 3) Rust toolchain + prebuilt cargo tools (cargo-binstall avoids compiling the tools).
# shellcheck disable=SC1091
source "$HOME/.cargo/env" 2>/dev/null || true
budget 600 '
  # The toolchain pinned by rust-toolchain.toml (1.97.0, minimal profile + the three components); `rustup show` alone
  # would download it on the first cargo call of every session instead of once into the snapshot.
  rustup toolchain install 1.97.0 --profile minimal -c clippy -c rustfmt -c llvm-tools-preview >/dev/null 2>&1 || true
  rustup show >/dev/null 2>&1 || true
  command -v cargo-binstall >/dev/null || curl -fsSL https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.sh | bash >/dev/null 2>&1
  # binstall fetches prebuilt binaries (GitHub release assets are blocked by the proxy for some crates, quickinstall
  # works for most); whatever is still missing is built from source with --locked (nextest refuses unlocked builds).
  cargo binstall --no-confirm cargo-nextest cargo-deny cargo-audit cargo-llvm-cov cargo-cyclonedx >/dev/null 2>&1 || true
  for t in cargo-nextest cargo-deny cargo-audit; do command -v $t >/dev/null || cargo install --locked $t >/dev/null 2>&1 || true; done
  [ -f Cargo.lock ] && cargo fetch >/dev/null 2>&1 || true
' &

# 4) Frontend dependencies (pnpm is preinstalled with Node 22; Playwright + chromium are preinstalled under
#    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers, so no browser download here).
budget 240 '
  command -v pnpm >/dev/null || npm install -g pnpm >/dev/null 2>&1 || true
  if [ -f ui/pnpm-lock.yaml ]; then (cd ui && pnpm install --frozen-lockfile >/dev/null 2>&1) || true; fi
' &

# 5) Gradle warm-up for the legacy functional tests (downloads wrapper + dependencies once, compiles the specs).
#    Maven Central rate-limits the shared egress IP (429): the init script redirects it to Google's mirror.
mkdir -p "$HOME/.gradle/init.d" && cp scripts/gradle-init.d/*.gradle "$HOME/.gradle/init.d/" 2>/dev/null || true
budget 280 '[ -x legacy/gradlew ] && cd legacy && for i in 1 2 3; do JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew -q --no-daemon -Dorg.gradle.internal.repository.max.retries=8 -Dorg.gradle.internal.repository.initial.backoff=3000 :functional-test:compileTestGroovy >/dev/null 2>&1 && break; sleep 30; done' &

wait
log "done (JDK 17: $(/usr/lib/jvm/java-17-openjdk-amd64/bin/javac -version 2>&1 | tail -1); rust: $(rustc --version 2>/dev/null || echo n/a); docker images: $(docker images -q 2>/dev/null | wc -l))"
