# ADR-0006 — Scheduler: Quartz-compatible cron, DB-persisted schedule, cluster lease

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

Legacy schedules jobs with Quartz. Its configuration is minimal: `legacy/rundeckapp/grails-app/conf/QuartzConfig.groovy:19-22`
sets `autoStartup = true` and `jdbcStore = false`, i.e. the in-memory `RAMJobStore`; schedules are rebuilt from
`scheduled_execution` rows at boot and cluster ownership is expressed by `server_nodeuuid` columns (ADR-0005), with
a takeover API. No misfire policy or thread count is configured in the application config (verified: no
`MisfireHandling`/`threadCount` settings under `grails-app/conf`, `grails-app/init` or `ScheduledExecutionService`),
so Quartz defaults apply — inferred from Quartz documentation, not from legacy code: `misfireThreshold` 60 s and
`MISFIRE_INSTRUCTION_SMART_POLICY`, which for cron triggers means "fire once now, then continue on schedule".
Legacy exposes Quartz gauges under `rundeck.scheduler.quartz.*` (`legacy/rundeckapp/grails-app/init/rundeckapp/BootStrap.groovy:462-468`:
`runningExecutions`, `threadPoolSize`, `scheduledJobs`) and a `quartz.scheduler.threadPool` health check (`:423-426`).
Job schedules use Quartz cron syntax (6–7 fields with seconds and optional year), stored in the job definition
(`crontabString` or the `seconds/minute/hour/dayOfMonth/month/dayOfWeek/year` fields of the job XML/YAML), with a
per-job time zone. MISSION §1.3 (scheduler bullet) and §3.6 fix the target.

## Decision

1. **`quartz-cron` is a standalone crate** (repo root) implementing the Quartz `CronExpression` grammar: 6 or 7
   fields (`seconds minutes hours day-of-month month day-of-week [year]`), `*`, `?`, ranges `a-b`, lists `a,b`,
   steps `a/n` and `*/n`, `L`, `LW`, `L-n`, `W`, `nW`, `#n` (`DOW#n`), day-of-week numbering **1 = SUN … 7 = SAT**
   and names `SUN`–`SAT`, month names `JAN`–`DEC`, case-insensitive names, the rule that exactly one of
   day-of-month/day-of-week is `?`, year range 1970–2099, and the same validity verdicts as `CronExpression.isValidExpression`
   (legacy job import and validation messages depend on them). Evaluation (`next_after(instant, tz)`) uses the job's
   IANA time zone with Quartz's DST behavior (skipped local times jump forward, repeated local times fire once).
2. The crate is **property-tested against a legacy-derived corpus**: `scripts/oracle.sh capture cron` records
   `(expression, timezone, from, next ×N)` tuples from the legacy container (`/api/*/job/{id}/forecast` and the
   scheduler's own `nextExecutionTime`) into `quartz-cron/tests/corpus/`; the forecast API of `rdx` must return the
   same instants. Fuzz target `cron_parse`; Criterion bench; gate ≥ 1M evaluations/s (MISSION §4).
3. **The schedule is persisted in the database** (`rdx_schedule` table via `rdx_migrations`, ADR-0005): job UUID,
   next fire time, owner server UUID, misfire policy, last fire, trigger kind (cron / `runAtTime` one-shot / retry).
   The `scheduled_execution` row stays the source of truth for the job's cron fields, `scheduleEnabled`,
   `executionEnabled`, time zone and `server_nodeuuid`; `rdx_schedule` is a derived index rebuilt on boot
   (schedule recovery) and after every job save/import/`scheduler/takeover`. Boot gate: 10,000 scheduled jobs loaded
   and next fire computed in < 2 s.
4. **Misfire policy matches Quartz defaults as legacy configures them**: a job whose next fire time is more than 60 s
   in the past when the scheduler looks at it fires **once** immediately, then continues on schedule; several missed
   occurrences never produce several executions. The threshold is `rdx.scheduler.misfire_threshold` (default 60 s).
5. **Cluster mode by database lease**: in cluster mode (`rundeck.clusterMode.enabled=true`, `rundeck.server.uuid`),
   each due trigger is claimed with `SELECT … FOR UPDATE SKIP LOCKED` (PostgreSQL, MySQL 8) on `rdx_schedule`, so
   exactly one server fires it; ownership (`server_nodeuuid`) is respected: a server only fires jobs it owns,
   except when `rundeck.scheduler.remoteExecution`-style policies (pinned by `specs/scheduler.md` from legacy)
   say otherwise. SQLite runs single-node and refuses `rundeck.clusterMode.enabled=true` at `check-config`.
6. **Takeover** keeps the legacy API (`PUT /api/*/scheduler/takeover` with the `server` / `project` / `job`
   selectors and the legacy response shape) and moves `server_nodeuuid` on `scheduled_execution` (and running
   executions where legacy does) in one transaction, then rebuilds the affected `rdx_schedule` rows. `GET
   /api/*/scheduler/jobs` and `/scheduler/server/{uuid}/jobs` keep their shapes.
7. **Execution mode** (`rundeck.executionMode`, `/api/*/system/executions/enable|disable`, project-level
   `project.disable.executions` / `project.disable.schedule`, `scheduleEnabled` / `executionEnabled` per job, the
   execution-mode timer of `legacy/grails-execution-mode-timer`) gates firing exactly as legacy does: a disabled
   schedule is not fired and not counted as misfired when re-enabled (next occurrence only).
8. **Thresholds**: `rundeck.scheduler.*` keys legacy honors (pinned in `specs/scheduler.md`, including the running
   executions limit and `rundeck.scheduler.threadPool.size`-style sizing) are read with the same names; the
   scheduler's concurrency is bounded (`rdx.scheduler.max_concurrent_fires`, default 2 × cores) and firing never
   blocks the tokio runtime (execution start is handed to `rdx-exec` supervisors, ADR-0002).
9. **Observability**: the legacy gauge names `rundeck.scheduler.quartz.runningExecutions`,
   `rundeck.scheduler.quartz.threadPoolSize`, `rundeck.scheduler.quartz.scheduledJobs` and the
   `quartz.scheduler.threadPool` health check keep their names in `/api/*/metrics/*` and `/monitoring/*` (ADR-0008),
   fed by the Rust scheduler.
10. **Retries, `runAtTime` and `retryDelay`** are one-shot triggers in the same table, so they survive a restart
    (legacy loses in-memory one-shots on restart — `jdbcStore = false`; this is an internal improvement with no
    contract change: the execution either runs once or is marked as legacy marks it, pinned by the oracle).

## Consequences

Positive: schedule state survives restarts and is shared by the cluster without a separate Quartz JDBC store or
external scheduler; next-fire computation is a pure, fuzzed, benchmarked function; cluster claims are race-free by
construction.

Negative: a second table (`rdx_schedule`) that must stay consistent with `scheduled_execution` (rebuilt on boot and
on every write, checked by `rdx doctor`); SQLite deployments cannot cluster.

Risks: Quartz DST corner cases and `L`/`W`/`#` semantics — covered by the corpus and property tests; MySQL `SKIP
LOCKED` requires 8.0+ (documented in `docs/MIGRATION.md`); misfire semantics subtly differ if legacy sites tuned
Quartz through `quartz.properties` (not found in 6.3.0 config; if a site did, `rdx.scheduler.misfire_threshold`
is the knob).

## Compatibility impact

Untouched: cron syntax and validation, job schedule fields, time zones, `scheduleEnabled`/`executionEnabled`,
forecast API, `server_nodeuuid` ownership, takeover and scheduler APIs, execution mode, metric names. No deviation
row: schedule persistence and restart-safe one-shots are internal. Additive: `rdx_schedule` table.

## Alternatives considered

- Port Quartz's JDBC job store schema — rejected: legacy does not use it (`jdbcStore = false`), so it is not a
  contract; its 11 tables are far more than the lease needs.
- An existing Rust cron crate (`cron`, `croner`) — rejected: none implements Quartz's `L`/`W`/`#`, 1 = SUN numbering
  and validity rules exactly; a wrong "next fire" is a silent contract break.
- Leader election (single scheduler node) — rejected: legacy semantics are per-job ownership plus takeover, not a
  single leader; per-trigger leases preserve them.
- Redis/etcd for leases — rejected: no external cache (MISSION §3.1).

## Migration / rollout

Nothing: schedules are read from the existing `scheduled_execution` rows on first boot and `rdx_schedule` is built
automatically. Cluster users keep `rundeck.server.uuid` and `rundeck.clusterMode.enabled`; MySQL must be 8.0+.

## References

- MISSION.md §1.3 (scheduler), §3.6, §4 (scheduler gates), §6 (Phase 3).
- `legacy/rundeckapp/grails-app/conf/QuartzConfig.groovy:19-22`
- `legacy/rundeckapp/grails-app/init/rundeckapp/BootStrap.groovy:423-426,462-468`
- `legacy/rundeckapp/grails-app/domain/rundeck/ScheduledExecution.groovy`, `Execution.groovy` (`serverNodeUUID`)
- `legacy/grails-execution-mode-timer`; `legacy/rundeckapp/grails-app/services/rundeck/services/ScheduledExecutionService.groovy`
- Related: ADR-0005 (`rdx_migrations`), ADR-0008 (metric names), `quartz-cron/`, `specs/scheduler.md`.
