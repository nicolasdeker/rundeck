# Benchmarks — MISSION §4 performance gates

Legacy = `rundeck/rundeck:6.3.0` oracle fixture (`scripts/oracle.sh up`), `rdx` = release binary, both on the same
runner in the same session. Method, rules and scripts: `scripts/bench/README.md`. Raw outputs live under
`scripts/bench/results/<timestamp>-<label>/` (git-ignored); each filled row names its result directory and commit.
A row is filled only from a real run; until then it says **not measured yet**.

## API latency at 50 concurrent clients (p99, ms) — gate: rdx ≥ 5× better than legacy, or a documented reason

| endpoint | legacy p99 | rdx p99 | ratio | gate | evidence (results dir, commit, runner) | command that fills the row |
|---|---|---|---|---|---|---|
| `GET /api/60/project/$p/jobs` | not measured yet | not measured yet | – | open | – | `BASE_URL=<url> TOKEN=<token> PROJECT=<p> LABEL=legacy\|rdx scripts/bench/run.sh jobs-list` |
| `GET /api/60/execution/$id/output` | not measured yet | not measured yet | – | open | – | `BASE_URL=<url> TOKEN=<token> PROJECT=<p> EXEC_ID=<id> LABEL=legacy\|rdx scripts/bench/run.sh execution-output` |
| `POST /api/60/job/$id/run` | not measured yet | not measured yet | – | open | – | `BASE_URL=<url> TOKEN=<token> PROJECT=<p> JOB_ID=<uuid> LABEL=legacy\|rdx scripts/bench/run.sh job-run` |

## Executions and logs

| gate | legacy | rdx | gate | evidence | command that fills the row |
|---|---|---|---|---|---|
| 1,000 concurrent executions of a 5-step local job on 1 node — peak RSS (MB), gate rdx ≤ 1/4 legacy | not measured yet | not measured yet | open | – | `BASE_URL=... TOKEN=... scripts/bench/run.sh exec-load` (Phase 3) |
| … same run — executions failed (gate 0) | not measured yet | not measured yet | open | – | same run (`exec-load.json` → `failed`) |
| … same run — log lines expected vs read (gate: none lost) | not measured yet | not measured yet | open | – | same run (`exec-load.json` → `lines_expected`, `lines_read`) |
| log streaming: 100 MB execution log followed by 10 clients — RSS growth beyond buffers (gate: none) | not measured yet | not measured yet | open | – | `BASE_URL=... TOKEN=... scripts/bench/run.sh log-stream` (Phase 3) |

## Start-up and footprint

| gate | legacy | rdx | gate | evidence | command that fills the row |
|---|---|---|---|---|---|
| cold start to first request (median ms, gate rdx < 1,000) | not measured yet (wall clock of `scripts/oracle.sh up`) | not measured yet | open | – | `RDX_BIN=target/release/rdx scripts/bench/run.sh cold-start` |
| binary size including the UI (MB, gate rdx < 60) | n/a (WAR + JRE image 1.1 GB, informative) | not measured yet | open | – | `RDX_BIN=target/release/rdx scripts/bench/run.sh binary-size` |

## Scheduler and micro-benchmarks (criterion, `cargo bench`)

| gate | rdx | gate | evidence | command that fills the row |
|---|---|---|---|---|
| 10,000 scheduled jobs loaded + next-fire computed (gate < 2 s) | not measured yet | open | – | `cargo bench -p rdx-sched -- load_and_next_fire` (Phase 3) |
| cron evaluations per second (gate ≥ 1 M/s) | not measured yet | open | – | `cargo bench -p rdx-sched -- cron_eval` (Phase 3) |
| node filter matching | not measured yet | informative | – | `cargo bench -p rdx-nodes` |
| variable expansion | not measured yet | informative | – | `cargo bench -p rdx-workflow -- expand` |
| rdlog read/write | not measured yet | informative | – | `cargo bench -p rdx-logging` |
| aclpolicy evaluation | not measured yet | informative | – | `cargo bench -p rdx-authz` |

The nightly workflow (`.github/workflows/nightly.yml`, job `bench`) runs `cargo bench --workspace` once benches exist and
uploads the criterion reports as an artifact; it prints "no criterion benches yet" until then. The legacy-vs-rdx k6
comparison is run in-session (both servers on the same VM), not on the shared runner.

## How to fill a row

1. Start both servers on the same machine with the same data set (`scripts/oracle.sh up` for legacy; the rdx binary
   against the same MySQL and project export).
2. Run the command of the row for `LABEL=legacy`, then for `LABEL=rdx`; `run.sh` prints p99 / failed / reqs and the
   results directory.
3. Copy the numbers into the row, with `scripts/bench/results/<dir>` and the commit; set `gate` to pass/fail per MISSION §4
   (a fail needs an ADR or a `DECISIONS-PENDING.md` entry explaining why).
