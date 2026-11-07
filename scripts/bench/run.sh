#!/usr/bin/env bash
# scripts/bench/run.sh — run the performance scenarios of MISSION §4 against whatever answers at BASE_URL
# (today: the legacy oracle from scripts/oracle.sh up; later: rdx) and write raw results under scripts/bench/results/.
# Method and rules: scripts/bench/README.md. Never invents a number: a scenario whose inputs are missing is reported
# as "not measured" with the reason, and the exit code is non-zero.
#
# Usage: scripts/bench/run.sh <scenario>... | all
#   api               = jobs-list execution-output job-run (k6, 50 VUs by default)
#   jobs-list         GET  /api/60/project/$PROJECT/jobs
#   execution-output  GET  /api/60/execution/$EXEC_ID/output
#   job-run           POST /api/60/job/$JOB_ID/run
#   binary-size       size of $RDX_BIN (MISSION §4: < 60 MB including the UI)
#   cold-start        hyperfine: start $RDX_BIN until GET /api/60/system/info answers (MISSION §4: < 1 s)
#   exec-load, log-stream   Phase 3 (need the rdx execution engine) — reported as not implemented, exit 4
# Env: BASE_URL, TOKEN (API scenarios), PROJECT (test), JOB_ID / EXEC_ID (discovered from the API when unset), VUS (50),
#      DURATION (60s), P99_MS (2000), LABEL (results suffix, default BASE_URL host), RDX_BIN, COLD_START_PORT (4440),
#      RDX_ARGS (extra arguments for the cold-start command).
# Exit codes: 0 every requested scenario measured and within thresholds; 2 usage / missing tool; 3 a scenario could not
#             be measured (missing input, discovery found nothing); 4 scenario not implemented yet; 99 a k6 threshold failed.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
RESULTS_ROOT=$HERE/results
VUS=${VUS:-50}
DURATION=${DURATION:-60s}
P99_MS=${P99_MS:-2000}
PROJECT=${PROJECT:-test}
API=/api/60

log() { echo "[bench] $*" >&2; }
die() { log "error: $1"; exit "${2:-1}"; }
usage() { sed -n '/^# Usage:/,/^# Exit codes:/p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }
need() { command -v "$1" >/dev/null 2>&1 || die "missing tool: $1 — see scripts/bench/README.md (Install)" 2; }

[ $# -ge 1 ] || { usage; exit 2; }
SCENARIOS=()
for s in "$@"; do
  case "$s" in
    all) SCENARIOS+=(jobs-list execution-output job-run binary-size cold-start) ;;
    api) SCENARIOS+=(jobs-list execution-output job-run) ;;
    jobs-list|execution-output|job-run|binary-size|cold-start|exec-load|log-stream) SCENARIOS+=("$s") ;;
    -h|--help) usage; exit 0 ;;
    *) log "unknown scenario: $s"; usage; exit 2 ;;
  esac
done

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
LABEL=${LABEL:-}
if [ -z "$LABEL" ] && [ -n "${BASE_URL:-}" ]; then LABEL=$(echo "$BASE_URL" | sed -E 's#^[a-z]+://##; s#[^A-Za-z0-9._-]+#_#g'); fi
OUT_DIR=$RESULTS_ROOT/$STAMP-${LABEL:-local}
mkdir -p "$OUT_DIR"
STATUS=0
NOT_MEASURED=()

api_get() { curl -sS --max-time 30 -H "X-Rundeck-Auth-Token: $TOKEN" -H 'Accept: application/json' "$BASE_URL$API$1"; }

require_api() {
  [ -n "${BASE_URL:-}" ] || die "BASE_URL is required for API scenarios (e.g. http://localhost:4440)" 2
  [ -n "${TOKEN:-}" ] || die "TOKEN is required (legacy oracle: admintoken)" 2
  need curl; need k6; need jq
  BASE_URL=${BASE_URL%/}
  local code
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 -H "X-Rundeck-Auth-Token: $TOKEN" "$BASE_URL$API/system/info" || true)
  [ "$code" = "200" ] || die "no server answered 200 at $BASE_URL$API/system/info (got '${code:-none}')" 3
}

# Discovery never guesses: it takes real ids from the API or reports the scenario as not measurable.
discover_job() {
  [ -n "${JOB_ID:-}" ] && return 0
  JOB_ID=$(api_get "/project/$PROJECT/jobs?max=1" | jq -r '.[0].id // empty')
  [ -n "$JOB_ID" ] || { NOT_MEASURED+=("job-run: project '$PROJECT' has no job (set JOB_ID or import one)"); return 1; }
  log "JOB_ID=$JOB_ID (first job of project $PROJECT)"
}
discover_exec() {
  [ -n "${EXEC_ID:-}" ] && return 0
  EXEC_ID=$(api_get "/project/$PROJECT/executions?max=1&statusFilter=succeeded" | jq -r '.executions[0].id // empty')
  [ -n "$EXEC_ID" ] || { NOT_MEASURED+=("execution-output: project '$PROJECT' has no succeeded execution (set EXEC_ID or run a job)"); return 1; }
  log "EXEC_ID=$EXEC_ID (latest succeeded execution of project $PROJECT)"
}

run_k6() { # <scenario> <script> [extra env k=v ...]
  local scenario=$1 script=$2; shift 2
  log "k6 $scenario: VUS=$VUS DURATION=$DURATION P99_MS=$P99_MS -> $OUT_DIR/$scenario.json"
  set +e
  env BASE_URL="$BASE_URL" TOKEN="$TOKEN" PROJECT="$PROJECT" VUS="$VUS" DURATION="$DURATION" P99_MS="$P99_MS" "$@" \
    k6 run --quiet --summary-export "$OUT_DIR/$scenario.json" "$HERE/k6/$script" 2>&1 | tee "$OUT_DIR/$scenario.log" >&2
  local rc=${PIPESTATUS[0]}
  set -e
  if [ -f "$OUT_DIR/$scenario.json" ]; then
    jq -r --arg s "$scenario" '"\($s): p99=\(.metrics.http_req_duration["p(99)"] // .metrics.http_req_duration.values["p(99)"] | tostring) ms, failed=\(.metrics.http_req_failed.value // .metrics.http_req_failed.values.rate | tostring), reqs=\(.metrics.http_reqs.count // .metrics.http_reqs.values.count | tostring)"' "$OUT_DIR/$scenario.json" >&2 || true
  fi
  if [ "$rc" -eq 99 ]; then log "$scenario: a k6 threshold failed (see thresholds in k6/$script)"; STATUS=99
  elif [ "$rc" -ne 0 ]; then die "k6 exited with $rc for $scenario" "$rc"; fi
}

write_meta() {
  need jq
  jq -n --arg commit "$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || echo unknown)" --arg base "${BASE_URL:-}" \
        --arg label "${LABEL:-local}" --arg stamp "$STAMP" --arg k6 "$(k6 version 2>/dev/null | head -1 || echo n/a)" \
        --arg hyperfine "$(hyperfine --version 2>/dev/null || echo n/a)" --arg host "$(uname -srm)" \
        --arg cpus "$(nproc 2>/dev/null || echo n/a)" --argjson vus "$VUS" --arg duration "$DURATION" --argjson p99 "$P99_MS" \
        '{commit:$commit, base_url:$base, label:$label, started:$stamp, k6:$k6, hyperfine:$hyperfine, host:$host, cpus:$cpus, vus:$vus, duration:$duration, p99_ms_threshold:$p99}' \
        > "$OUT_DIR/meta.json"
}

scenario_binary_size() {
  if [ -z "${RDX_BIN:-}" ] || [ ! -f "$RDX_BIN" ]; then NOT_MEASURED+=("binary-size: RDX_BIN is not set or not a file (the rdx binary lands in Phase 1)"); return; fi
  local bytes; bytes=$(stat -c %s "$RDX_BIN")
  jq -n --arg bin "$RDX_BIN" --argjson bytes "$bytes" '{binary:$bin, bytes:$bytes, mb:(($bytes/1048576*100|floor)/100), limit_mb:60, ok:($bytes < 60*1048576)}' > "$OUT_DIR/binary-size.json"
  log "binary-size: $bytes bytes ($(( bytes / 1048576 )) MB) -> $OUT_DIR/binary-size.json"
}

# Cold start = wall clock from process start until GET /api/60/system/info answers (MISSION §4: < 1 s).
scenario_cold_start() {
  if [ -z "${RDX_BIN:-}" ] || [ ! -x "$RDX_BIN" ]; then NOT_MEASURED+=("cold-start: RDX_BIN is not set or not executable (the rdx binary lands in Phase 1)"); return; fi
  need hyperfine; need curl
  local port=${COLD_START_PORT:-4440}
  local cmd="$HERE/cold-start-once.sh '$RDX_BIN' $port ${RDX_ARGS:-}"
  hyperfine --warmup 2 --runs 10 --export-json "$OUT_DIR/cold-start.json" "$cmd" >&2
  jq -r '.results[0] | "cold-start: median \(.median*1000|floor) ms, min \(.min*1000|floor) ms, max \(.max*1000|floor) ms"' "$OUT_DIR/cold-start.json" >&2
}

for s in "${SCENARIOS[@]}"; do
  case "$s" in
    jobs-list)        require_api; write_meta; run_k6 jobs-list jobs-list.js ;;
    execution-output) require_api; write_meta; discover_exec && run_k6 execution-output execution-output.js EXEC_ID="$EXEC_ID" ;;
    job-run)          require_api; write_meta; discover_job && run_k6 job-run job-run.js JOB_ID="$JOB_ID" ;;
    binary-size)      scenario_binary_size ;;
    cold-start)       scenario_cold_start ;;
    exec-load|log-stream)
      log "$s: not implemented yet — needs the rdx execution engine (Phase 3); the RSS sampler and the k6 script are added with it"
      NOT_MEASURED+=("$s: not implemented (Phase 3)"); STATUS=4 ;;
  esac
done

log "results: $OUT_DIR"
if [ ${#NOT_MEASURED[@]} -gt 0 ]; then
  printf '%s\n' "${NOT_MEASURED[@]}" > "$OUT_DIR/not-measured.txt"
  for n in "${NOT_MEASURED[@]}"; do log "NOT MEASURED — $n"; done
  [ "$STATUS" -ne 0 ] || STATUS=3
fi
exit "$STATUS"
