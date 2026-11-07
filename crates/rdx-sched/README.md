# `rdx-sched`

Quartz-compatible cron, scheduler, cluster ownership, takeover, execution mode

The scheduler of MISSION §3.6 / ADR-0006: Quartz-compatible triggers (via the `quartz-cron` crate), persisted
next-fire times and misfire policy, cluster ownership by DB lease, the takeover endpoint and the
active/passive execution mode.

## Legacy references (ported in later phases)

- `legacy/rundeckapp/grails-app/services/rundeck/services/ScheduledExecutionService.groovy`
- `legacy/rundeckapp/grails-app/services/rundeck/services/JobSchedulerService.groovy`
- `legacy/rundeckapp/grails-app/services/rundeck/services/JobSchedulesService.groovy`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/schedule/`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/cluster/`
- `legacy/rundeckapp/grails-app/conf/application.groovy` (quartz keys)

## Parity specs this crate targets

- `specs/scheduler.md`
- upstream `api/schedule/ScheduleSpec`, `api/job/JobScheduledSpec`, `api/execution/ExecutionModeSpec`

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
