# scripts/bench — performance gates (MISSION §4 "Performance")

Every number in `docs/BENCHMARKS.md` comes from this directory, measured on the **same runner**, legacy container vs
`rdx`, never from memory or extrapolation. A row that was not measured says "not measured yet". `run.sh` refuses to
invent values: when an input is missing (no job, no execution, no k6) it prints why and leaves the row empty.

## Method

| gate (MISSION §4) | tool | script / command | what is recorded |
|---|---|---|---|
| API p99 at 50 VUs: `GET /api/60/project/$p/jobs` | k6 | `k6/jobs-list.js` | `http_req_duration` p99 (ms), error rate, req/s |
| API p99 at 50 VUs: `GET /api/60/execution/$id/output` | k6 | `k6/execution-output.js` | same |
| API p99 at 50 VUs: `POST /api/60/job/$id/run` | k6 | `k6/job-run.js` | same (each VU runs the job; the job must be quick and idempotent) |
| 1,000 concurrent executions of a 5-step local job on 1 node: RSS ≤ 1/4 of legacy, no error, no lost log lines | k6 + `docker stats` / `ps -o rss` | `run.sh exec-load` (Phase 3: needs the rdx server; the sampler is the same for both) | peak RSS (MB), executions failed, log lines expected vs read |
| log streaming: 100 MB log followed by 10 clients, no growth beyond buffers | k6 + RSS sampler | `run.sh log-stream` (Phase 3) | RSS before/after (MB) |
| cold start to first request < 1 s | hyperfine | `run.sh cold-start` (needs `RDX_BIN`; legacy: measured by `scripts/oracle.sh up` wall clock) | median wall clock (ms) over 10 runs |
| binary < 60 MB including the UI | `stat` | `run.sh binary-size` (needs `RDX_BIN`) | bytes |
| scheduler: 10,000 jobs loaded + next-fire < 2 s; cron ≥ 1M evaluations/s | criterion | `cargo bench -p rdx-sched` (Phase 3) | criterion report |
| criterion benches: cron, node filter, variable expansion, rdlog, aclpolicy | criterion | `cargo bench --workspace` (nightly.yml `bench` job) | criterion report |

Rules of the method:

1. **Same runner, same minute.** Legacy and `rdx` are measured back to back on the same machine (CI: `ubuntu-latest`;
   in-session: the 4 vCPU cloud VM — note which in the row). Numbers from different machines are not compared.
2. **Legacy = the oracle fixture** (`scripts/oracle.sh up`, `rundeck/rundeck:6.3.0` with MySQL 8.4), nothing tuned.
   `rdx` = the release binary (`cargo build --release`) with the same database and the same project data.
3. **Warm-up excluded.** Every k6 script has a 15 s warm-up stage whose samples are dropped from the thresholds via
   the `main` scenario tag; hyperfine uses `--warmup 2`.
4. **Fixed data set.** `run.sh` requires a project (`PROJECT`), a job (`JOB_ID`, discovered as the first job of the
   project when unset) and a finished execution (`EXEC_ID`, discovered as the most recent execution when unset). The
   data set used for the recorded run is named in the row (`bench-project` from `scripts/bench/fixtures/` once Phase 3
   adds it).
5. **Record the raw output.** `run.sh` writes `scripts/bench/results/<UTC timestamp>-<label>/<scenario>.json`
   (k6 `--summary-export`) and `meta.json` (git commit, BASE_URL host, versions). The directory is git-ignored; the
   numbers go to `docs/BENCHMARKS.md` by hand with the result path and the commit.
6. **Thresholds are gates, not goals.** Each k6 script fails (exit 99) when `http_req_failed > 1 %` or p99 exceeds
   `P99_MS` (default 2000 ms for the legacy baseline — set it to the legacy p99 / 5 when gating `rdx`, MISSION §4
   "≥ 5× better").

## Usage

```
# against the legacy oracle (works today)
scripts/oracle.sh up
BASE_URL=http://localhost:4440 TOKEN=admintoken PROJECT=test scripts/bench/run.sh api         # three k6 scenarios
BASE_URL=... TOKEN=... scripts/bench/run.sh jobs-list|execution-output|job-run                 # one scenario
# against rdx (Phase 1+)
RDX_BIN=target/release/rdx scripts/bench/run.sh binary-size cold-start
BASE_URL=http://localhost:4440 TOKEN=admintoken LABEL=rdx scripts/bench/run.sh api
```

Environment: `BASE_URL` (required for API scenarios), `TOKEN` (required), `PROJECT` (default `test`), `JOB_ID`,
`EXEC_ID`, `VUS` (50), `DURATION` (60s), `P99_MS` (2000), `LABEL` (results directory suffix, default the BASE_URL host),
`RDX_BIN` (for `binary-size` and `cold-start`), `COLD_START_PORT` (4440).

Install: `k6` from https://grafana.com/docs/k6/latest/set-up/install-k6/ (`sudo gpg ... && apt-get install k6` or the
release tarball), `hyperfine` via `apt-get install hyperfine` (Ubuntu 24.04) or `cargo binstall hyperfine`. `run.sh`
checks for both and says which one is missing instead of silently skipping.
