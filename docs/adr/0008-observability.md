# ADR-0008 — Observability: tracing, metrics projection, health, logs

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

Legacy 6.3.0 exposes three metric surfaces. (1) The API: `GET /api/$api_version/metrics/$name**?`
(`legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy:270`, `ApiController.apiMetrics`) returns
the Dropwizard JSON shape (`gauges`, `counters`, `histograms`, `meters`, `timers`) and `/api/$api_version/system/info`
(`:219`) carries the system report. (2) `/monitoring/metrics`, `/monitoring/prometheus`, `/monitoring/health`,
`/monitoring/health/readiness` (`UrlMappings.groovy:22-26`, `MonitoringController.groovy`), `permitAll`
(`legacy/rundeckapp/grails-app/conf/application.groovy:138`), disabled with `rundeck.metrics.monitoring.enabled=false`
(`MonitoringController.groovy:15,191`) — so **Prometheus exposition already exists in legacy**. (3) The legacy
Dropwizard servlets `/metrics/metrics`, `/metrics/ping`, `/metrics/healthcheck`, `/metrics/threads`
(`legacy/grails-metricsweb/grails-app/controllers/metricsweb/UrlMappings.groovy:21-27`): "deprecated, opt-in only",
404 unless `rundeck.metrics.legacy.enabled=true`, "will be removed in Rundeck 7.0"; the admin servlet is gated by
`rundeck.metrics.enabled` and `rundeck.metrics.api.enabled` (`DisablingAdminServlet.groovy:98-99`). Spring Boot
actuator web exposure is excluded entirely (`application.yml:81` `exclude: '*'`). Gauge names include
`rundeck.scheduler.quartz.*` (`BootStrap.groovy:462-468`). Logging is Log4j2 (`legacy/packaging/lib/common/etc/rundeck/log4j2.properties`,
`legacy/docker/official/remco/templates/log4j2.properties`) driven by `RUNDECK_LOGGING_STRATEGY`,
`RUNDECK_LOGGING_AUDIT_ENABLED`, `RUNDECK_LOGGING_LEVEL_*` (`legacy/docker/official/README.md:163-174`). MISSION §3.9
asks for `tracing`, optional OTLP, a Prometheus registry "exposed at `/metrics` (new)" and projected into the legacy
JSON, `/api/*/system/info` and `/health` unchanged, structured JSON logs with redaction.

## Decision

1. **`tracing` everywhere.** Every request span carries `request_id`, `method`, `route`, `status`, `user`,
   `auth_method`; every execution span carries `execution_id`, `job_id`, `project`, `user`, and step/node spans nest
   under it (ADR-0002 task tree). Field names are stable and documented in `crates/rdx-telemetry/README.md`.
2. **Log output**: human-readable in a TTY, **structured JSON** otherwise (`rdx.logging.format=json|text`), one line
   per event, UTC timestamps, level, target, span fields. Secret redaction is a `tracing` layer: values of fields
   named `password`, `token`, `secret`, `authorization`, `cookie` and any `secrecy` type render as `[REDACTED]`; a
   test greps a synthetic log for planted secrets.
3. **`log4j2.properties` is accepted** and mapped to the `tracing` filter: logger-level settings (`logger.<name>.level`)
   become `EnvFilter` directives on the matching Rust targets (mapping table in `rdx-telemetry`), appenders become
   `console`/`file`; unmappable Log4j2 features are logged once as ignored. The `RUNDECK_LOGGING_STRATEGY`,
   `RUNDECK_LOGGING_AUDIT_ENABLED`, `RUNDECK_LOGGING_LEVEL_*` variables keep their meaning (ADR-0009).
4. **Audit log** (`rundeck.audit.*`, `audit-logging` built-in, ADR-0003) receives the auth events of ADR-0007 and the
   legacy audit events (project/job/ACL changes) with the legacy event names.
5. **One Prometheus registry** (`prometheus-client`) is the single metrics store. It is **projected** to the legacy
   Dropwizard JSON at `/api/*/metrics/*` with the legacy metric names and types (gauges/counters/meters/timers;
   timers carry the same percentile keys; `name` filtering as legacy), fed by the same instrumentation.
6. **Prometheus exposition keeps the legacy path `/monitoring/prometheus`** (text format 0.0.4 / OpenMetrics by
   `Accept`), with `/monitoring/metrics`, `/monitoring/health` and `/monitoring/health/readiness` kept, gated by the
   legacy key `rundeck.metrics.monitoring.enabled`, unauthenticated as legacy (`permitAll`) — these are contracts.
   **No additional `/metrics` path is added**: `/metrics/*` is the legacy Dropwizard namespace (C-011) and adding a
   second Prometheus endpoint there would be a conflicting, non-contract route. This refines MISSION §3.9 ("exposed
   at `/metrics` (new)") per MISSION §0 (the legacy code wins); the deviation from the MISSION wording is recorded in
   `docs/COMPAT.md` **C-014**. Metric names for `rdx`-specific series are prefixed `rdx_`; legacy-named series keep
   their names.
7. **`/api/*/system/info` keeps the legacy content** (version fields, OS, JVM block replaced by a `runtime` block with
   identical keys where tests assert them — pinned by `specs/system.md` against the oracle), and `/health`
   (listed as filter-exempt at `application.groovy:161`) is served with the legacy body if the oracle shows one
   (Phase 1 verifies; otherwise it aliases `/monitoring/health`).
8. **Legacy Dropwizard servlets and admin HTML pages are not served**: `/metrics/metrics|ping|healthcheck|threads`
   return 404 regardless of `rundeck.metrics.legacy.enabled` (legacy's own default), and the admin servlet pages
   (`grails-metricsweb`) do not exist. **C-011** (reason c, and upstream-deprecated).
9. **OpenTelemetry**: OTLP export of traces and metrics (`rdx.otel.endpoint`), **off by default**, additive (Phase 6).
10. **Health model**: `/monitoring/health` aggregates database connectivity, scheduler liveness (ADR-0006), log
    storage writability and plugin registry; `readiness` fails until migrations are applied and the scheduler has
    recovered; both are the probes used by the Helm chart (ADR-0009).
11. **Gauges with legacy names** are kept: `rundeck.scheduler.quartz.runningExecutions`, `threadPoolSize`,
    `scheduledJobs`, the `quartz.scheduler.threadPool` health check name, and the execution/job/HTTP meters legacy
    registers (inventoried in `specs/metrics.md` from `BootStrap.groovy` and `MetricService`).

## Consequences

Positive: one instrumentation layer feeds logs, legacy JSON, Prometheus and (optionally) OTLP; secrets cannot leak
through logs by construction; existing Prometheus scrapes of `/monitoring/prometheus` keep working.

Negative: the Log4j2 mapping is lossy for exotic appenders (documented); legacy Dropwizard servlets are gone for
the few sites that opted in.

Risks: Dropwizard timer percentile semantics vs Prometheus histograms — the projection computes the legacy keys
from an HDR-style summary so the JSON shape and keys match; `/health` legacy body unknown until the oracle run.

## Compatibility impact

Untouched: `/api/*/metrics/*` JSON, `/api/*/system/info`, `/monitoring/*` paths and gating key, legacy metric names,
`RUNDECK_LOGGING_*` variables, `log4j2.properties` acceptance. Deviations: **C-011** legacy `/metrics/*` and admin
pages dropped (c), **C-014** Prometheus exposition stays at `/monitoring/prometheus` (refines MISSION §3.9; no new
path). Additive: structured JSON logs, OTLP (off), `rdx_*` series.

## Alternatives considered

- Add `/metrics` as MISSION §3.9 literally says — rejected: collides with the legacy `/metrics/*` namespace and
  duplicates an endpoint legacy already has at `/monitoring/prometheus`.
- `metrics` crate façade + exporters — rejected: one registry with one projection is simpler to keep name-stable.
- Keep Log4j2 syntax unsupported — rejected: `log4j2.properties` is a file operators ship (MISSION §1.2).
- Serve the Dropwizard admin HTML pages — rejected: upstream disabled them by default and scheduled removal;
  JVM thread dumps (`/metrics/threads`) have no meaning.

## Migration / rollout

Nothing for API metrics, `/monitoring/*` scrapes and logging variables. Sites that enabled
`rundeck.metrics.legacy.enabled=true` switch scrapes to `/monitoring/prometheus` or `/api/*/metrics/metrics`.

## References

- MISSION.md §1.5 (metricsweb), §3.9, §4 (secrets), §6 (Phase 4 `/metrics/*`, `/monitoring/*`).
- `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy:22-26,219,270`
- `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/MonitoringController.groovy:15,191`
- `legacy/rundeckapp/grails-app/conf/application.groovy:138,161`; `application.yml:76-82`
- `legacy/grails-metricsweb/grails-app/controllers/metricsweb/UrlMappings.groovy:21-27`;
  `legacy/grails-metricsweb/src/main/groovy/org/grails/plugins/metricsweb/DisablingAdminServlet.groovy:98-99`
- `legacy/rundeckapp/grails-app/init/rundeckapp/BootStrap.groovy:423-426,462-468`
- `legacy/packaging/lib/common/etc/rundeck/log4j2.properties`; `legacy/docker/official/remco/templates/log4j2.properties`;
  `legacy/docker/official/README.md:163-174`
- Related: ADR-0002 (spans), ADR-0006 (gauges), ADR-0007 (audit), ADR-0009 (probes).
