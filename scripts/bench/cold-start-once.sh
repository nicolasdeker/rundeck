#!/usr/bin/env bash
# scripts/bench/cold-start-once.sh — one cold start of the rdx binary, timed by hyperfine from scripts/bench/run.sh.
# Starts <binary> [args...], polls GET http://127.0.0.1:<port>/api/60/system/info until it answers (any HTTP status:
# the server is up), then stops the process. Exit 1 if the server does not answer within COLD_START_TIMEOUT (10 s).
# Usage: cold-start-once.sh <binary> <port> [args...]
set -euo pipefail
[ $# -ge 2 ] || { echo "usage: $0 <binary> <port> [args...]" >&2; exit 2; }
bin=$1 port=$2; shift 2
timeout_s=${COLD_START_TIMEOUT:-10}
"$bin" "$@" >/dev/null 2>&1 &
pid=$!
trap 'kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true' EXIT
deadline=$(( $(date +%s%N) / 1000000 + timeout_s * 1000 ))
while :; do
  if curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$port/api/60/system/info"; then exit 0; fi
  kill -0 "$pid" 2>/dev/null || { echo "server exited before answering" >&2; exit 1; }
  [ $(( $(date +%s%N) / 1000000 )) -lt "$deadline" ] || { echo "no answer within ${timeout_s}s" >&2; exit 1; }
  sleep 0.02
done
