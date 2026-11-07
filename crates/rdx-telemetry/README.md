# `rdx-telemetry`

tracing, metrics (Prometheus registry → legacy Dropwizard JSON shape on /api/*/metrics), health

Observability (MISSION §3.9 / ADR-0008): `tracing` with execution/job/project/user fields and secret
redaction, a Prometheus registry at `/metrics` projected into the legacy Dropwizard JSON shape at
`/api/*/metrics/*`, optional OTLP export, and the legacy `/health` and `system/info` content.

## Legacy references (ported in later phases)

- `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy` (metrics and monitoring routes)
- `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/MonitoringController.groovy`
- `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/ApiController.groovy` (metrics, system info)
- `legacy/rundeckapp/grails-app/controllers/rundeck/interceptors/AA_TimerInterceptor.groovy`

## Parity specs this crate targets

- `specs/telemetry.md`
- upstream `api/system/MetricsSpec`, `api/system/SysInformationSpec`

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
