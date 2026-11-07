#!/usr/bin/env bash
# cloud-setup.sh — setup script of the "rdx" Claude Code cloud environment.
# Runs as root, from the repository root, on a fresh Ubuntu 24.04 VM (4 vCPU / 16 GB / 30 GB, Docker available).
# It must finish in < ~5 minutes so the environment snapshot is cached; everything heavy runs in parallel and
# is best-effort (a failed step never fails the script). Keep it idempotent. Agent: keep this file current.
set -uo pipefail
export DEBIAN_FRONTEND=noninteractive
log() { echo "[cloud-setup] $*"; }
budget() { timeout --signal=TERM "$1" bash -c "$2" || log "step timed out or failed (non-fatal): ${2:0:60}"; }

# 1) System packages: JDK 17 for the legacy functional-test build (Gradle 8.14), PAM/SSL headers for rdx crates.
budget 200 'apt-get update -qq >/dev/null && apt-get install -y -qq --no-install-recommends \
  openjdk-17-jdk-headless libpam0g-dev libssl-dev pkg-config clang lld jq bc unzip >/dev/null' &

# 2) Docker images for the oracle and DB fixtures (cached by the snapshot; containers are started per session).
budget 270 'docker pull -q rundeck/rundeck:6.3.0 >/dev/null' &
budget 120 'docker pull -q postgres:16 >/dev/null' &
budget 120 'docker pull -q mysql:8 >/dev/null' &

# 3) Rust toolchain + prebuilt cargo tools (cargo-binstall avoids compiling the tools).
# shellcheck disable=SC1091
source "$HOME/.cargo/env" 2>/dev/null || true
budget 240 '
  rustup show >/dev/null 2>&1 || true                      # installs the toolchain pinned by rust-toolchain.toml
  rustup component add clippy rustfmt llvm-tools-preview >/dev/null 2>&1 || true
  command -v cargo-binstall >/dev/null || curl -fsSL https://raw.githubusercontent.com/cargo-bins/cargo-binstall/main/install-from-binstall-release.sh | bash >/dev/null 2>&1
  cargo binstall -y --no-confirm cargo-nextest cargo-deny cargo-audit cargo-llvm-cov cargo-cyclonedx >/dev/null 2>&1 || true
  [ -f Cargo.lock ] && cargo fetch >/dev/null 2>&1 || true
' &

# 4) Frontend toolchain (pnpm) + Playwright browser (best effort; chromedriver/chrome are preinstalled as fallback).
budget 240 '
  command -v pnpm >/dev/null || npm install -g pnpm >/dev/null 2>&1 || true
  if [ -f ui/pnpm-lock.yaml ]; then (cd ui && pnpm install --frozen-lockfile >/dev/null 2>&1) || true; fi
  if [ -f ui/package.json ]; then (cd ui && pnpm exec playwright install chromium >/dev/null 2>&1) || true; fi
' &

# 5) Gradle warm-up for the legacy functional tests (downloads wrapper + dependencies once).
budget 240 '[ -x legacy/gradlew ] && cd legacy && JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew -q --no-daemon :functional-test:compileTestGroovy >/dev/null 2>&1' &

wait
log "done (JDK: $(javac -version 2>&1 | head -1); rust: $(rustc --version 2>/dev/null || echo n/a); docker images: $(docker images -q 2>/dev/null | wc -l))"
