//! `quartz-cron` — standalone crate: Quartz cron parser/evaluator (property-tested against a
//! legacy-derived corpus)
//!
//! A standalone, dependency-light implementation of the Quartz `CronExpression` grammar used by
//! legacy job schedules: seven fields (seconds to optional year), `*`, `?`, `-`, `,`, `/`, `L`,
//! `W`, `#`, month and day-of-week names, and `next_fire_after(instant)` with Quartz's semantics.
//! Property-tested against a corpus derived from the legacy container; fuzzed (MISSION §4).
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/ScheduledExecutionService.groovy` (how
//!   `CronExpression` is built and validated)
//! - `legacy/rundeckapp/src/test/groovy/rundeck/services/ScheduledExecutionServiceSpec.groovy`
//!   (cron cases)
//! - Quartz itself is an external library in legacy (`org.quartz.CronExpression`); the behavioral
//!   reference is its documented grammar plus the derived corpus
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
