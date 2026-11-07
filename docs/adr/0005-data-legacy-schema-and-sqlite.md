# ADR-0005 — Data: legacy Postgres/MySQL schema kept, `rdx_migrations`, SQLite default, H2 unsupported

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

Legacy persists 23 GORM domain classes (22 in `legacy/rundeckapp/grails-app/domain/rundeck/`:
`AuthToken`, `BaseReport`, `CommandExec`, `ExecReport`, `Execution`, `JobExec`, `JobFileRecord`,
`LogFileStorageRequest`, `Notification`, `Option`, `Orchestrator`, `PluginMeta`, `PluginStep`, `Project`,
`ReferencedExecution`, `ScheduledExecution`, `ScheduledExecutionStats`, `StoredEvent`, `Storage`, `User`,
`Workflow`, `WorkflowStep`; plus `legacy/grails-webhooks/grails-app/domain/webhooks/Webhook.groovy`). The schema is
managed by Liquibase: `legacy/rundeckapp/grails-app/migrations/changelog.groovy` includes one changelog per
aggregate under `migrations/core/` (`:87-91` and following, e.g. `core/AuthToken.groovy`, `core/Execution.groovy`).
The default development/embedded database is H2 (`legacy/rundeckapp/grails-app/conf/DataSource.groovy:4`
`org.h2.Driver`, `:29` `jdbc:h2:file:db/devDb`), which exists only on the JVM. MISSION §1.4 and §3.3 require `rdx`
to start against a database initialized by legacy 6.3.0 on PostgreSQL and MySQL and to make SQLite the embedded
default.

## Decision

1. **The PostgreSQL and MySQL schema is the legacy schema**: same table and column names, types, indexes,
   sequences/auto-increment and foreign keys for all 23 aggregates, so that `rdx` boots on a database that legacy
   6.3.0 created and that legacy 6.3.0 could boot on afterwards. The DDL is generated **once** from a
   legacy-initialized database (the `rundeck/rundeck:6.3.0` image against `postgres:16` and `mysql:8`), checked in
   under `crates/rdx-db/migrations/{postgres,mysql}/0001_legacy_6_3_0.sql`, and diffed in CI against a fresh legacy
   init on every push (`parity.yml`). Any diff fails the build.
2. **`rdx` never writes to Liquibase's tables** (`DATABASECHANGELOG`, `DATABASECHANGELOGLOCK`); they are left intact
   so the legacy server stays able to start on the same database during a rollback window. `rdx`'s own additive
   changes (new tables/columns/indexes only; never renaming or dropping legacy objects in v1) live in
   `rdx_migrations` with a checksum per migration; `rdx migrate` applies them, `rdx serve` refuses to start on a
   pending migration unless `rdx.db.migrate_on_start=true` (the legacy `RUNDECK_DATABASE_MIGRATE_ONSTART`
   environment variable, `legacy/docker/official/README.md:158`, maps to it).
3. **Connection configuration keeps the legacy keys**: `dataSource.url`, `dataSource.username`,
   `dataSource.password`, `dataSource.driverClassName`, `dataSource.properties.*` (pool sizing: `maximumPoolSize`,
   `connectionTimeout`, `idleTimeout`, `maxLifetime`, `validationTimeout` mapped to the `sqlx` pool; unknown
   JDBC-specific properties are ignored with a warning). A `jdbc:postgresql://`/`jdbc:mysql://`/`jdbc:mariadb://`
   URL is translated to the native URL. A `jdbc:h2:` URL is rejected at `check-config`/`serve` with a message that
   names `rdx migrate --from-h2` (**C-008**, reason c).
4. **SQLite is the embedded default** (`dataSource.url` absent → `${rdeck.base}/data/rdx.sqlite`, WAL mode, foreign
   keys on, single writer, `busy_timeout` 5 s). Its schema is the legacy schema translated to SQLite types, checked in
   under `crates/rdx-db/migrations/sqlite/`, with the same column names so repositories share SQL where dialects
   allow. SQLite is single-node only (ADR-0006).
5. **`rdx migrate --from-h2`** consumes (a) a legacy project archive per project (jobs, executions, configs, ACLs,
   readme/motd, SCM — MISSION §1.2) and (b) a CSV dump of the H2 tables produced by a documented procedure run in
   the legacy container (JDBC `CSVWRITE` per table, documented in `docs/MIGRATION.md`), and loads them into the target
   backend (SQLite by default, or Postgres/MySQL). Verified in CI with a seeded legacy H2 instance; row counts and
   a sample of API responses (`/api/*/project/*/jobs`, `/api/*/execution/*`) must match the legacy source.
6. **Data access**: `sqlx` with runtime-checked queries per backend behind one repository trait per aggregate
   (`ProjectRepo`, `JobRepo`, `ExecutionRepo`, `TokenRepo`, ...), explicit transactions for multi-row writes
   (job import, execution finalize, project delete), statement timeouts from `rdx.db.statement_timeout` (default
   30 s), no N+1 on hot paths (tests assert query counts for job list, execution list, node sources).
7. **Semantics of legacy columns are preserved**, including the ones that encode behavior: `auth_token.token_mode`
   (`SECURED`/`LEGACY`/null, ADR-0007), `execution.status`/`abortedby`/`server_nodeuuid`
   (cluster ownership, ADR-0006), `scheduled_execution.server_nodeuuid`, `log_file_storage_request` states
   (incomplete-storage resume), `stored_event` (audit/webhook events), `base_report`/`exec_report` (activity), text
   columns that hold the legacy XML/YAML/JSON serializations (`workflow_step.json_data`, option values) are read and
   written with `rdx-formats` codecs that round-trip byte-stable where legacy is.
8. **Identifiers and sequences**: `rdx` uses the same primary key generation strategy as legacy per backend
   (sequences/identity columns created by the legacy DDL) so legacy and `rdx` can alternate on the same database.

## Consequences

Positive: zero-downtime adoption for Postgres/MySQL users and a rollback path (start the Java server again); an
embedded default that needs no JVM; schema drift caught by CI against the real legacy initializer.

Negative: the legacy schema carries GORM artifacts (`version` columns, `class` discriminators, wide text columns)
that `rdx` must honor; additive-only evolution until a post-v1 ADR allows schema cleanup; SQLite limits a node to
single-server mode.

Risks: type mapping subtleties (MySQL `TINYINT(1)` booleans, timestamp time zones, Postgres `bytea` vs MySQL
`blob`) — covered by round-trip tests on all three backends in CI; H2 CSV export edge cases (CLOBs with newlines) —
covered by the CI migration fixture.

## Compatibility impact

Untouched: Postgres/MySQL schema and data, `dataSource.*` keys, project archive format, `rundeck.server.uuid`
cluster semantics. Deviation: **C-008** H2 unsupported / SQLite default (reason c). Additive: `rdx_migrations`
table, `rdx migrate`, SQLite backend.

## Alternatives considered

- A new clean schema with a one-way migration — rejected: breaks the drop-in promise and the rollback window
  (MISSION §0, §1.4).
- Diesel or SeaORM — rejected: `sqlx` runtime-checked queries fit three dialects over one hand-written legacy schema.
- Keep H2 through a JVM helper process — rejected: no JVM (ADR-0001); `migrate --from-h2` covers the need once.
- Embedded Postgres instead of SQLite — rejected: binary size, startup time, operational weight for the single-node case.

## Migration / rollout

Postgres/MySQL: nothing — stop legacy, start `rdx` on the same `dataSource.*`; `rdx migrate` adds the
`rdx_migrations` table on first start. H2: run the documented export in the legacy container, then
`rdx migrate --from-h2 --archives <dir> --csv <dir>`; the default target is SQLite under `${rdeck.base}/data/`.

## References

- MISSION.md §1.4, §3.3, §6 (Phase 1 exit: legacy-initialized Postgres boots `rdx`; Phase 6 `rdx migrate`).
- `legacy/rundeckapp/grails-app/domain/rundeck/*.groovy` (22 files), `legacy/grails-webhooks/grails-app/domain/webhooks/Webhook.groovy`
- `legacy/rundeckapp/grails-app/migrations/changelog.groovy:87-91` (includes of `core/*.groovy`)
- `legacy/rundeckapp/grails-app/conf/DataSource.groovy:4,29` (H2 default)
- `legacy/docker/official/README.md:142-158` (`RUNDECK_DATABASE_*`)
- Related: ADR-0006 (cluster lease), ADR-0007 (`auth_token.token_mode`), `docs/MIGRATION.md` (Phase 6).
