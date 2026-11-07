//! `rdx-sched` — Quartz-compatible cron, scheduler, cluster ownership, takeover, execution mode
//!
//! The scheduler of MISSION §3.6 / ADR-0006: Quartz-compatible triggers (via the `quartz-cron`
//! crate), persisted next-fire times and misfire policy, cluster ownership by DB lease, the
//! takeover endpoint and the active/passive execution mode.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/ScheduledExecutionService.groovy`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/JobSchedulerService.groovy`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/JobSchedulesService.groovy`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/schedule/`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/cluster/`
//! - `legacy/rundeckapp/grails-app/conf/application.groovy` (quartz keys)
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
