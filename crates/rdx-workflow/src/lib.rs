//! `rdx-workflow` — workflow engine: strategies, rule engine, contexts, data/variable expansion,
//! log filters, orchestrators
//!
//! The workflow engine of MISSION §3.4: strategies (node-first, step-first, parallel, ruleset), the
//! rule engine, execution contexts, `${...}` data/variable expansion, log filters and
//! orchestrators. Each execution is a supervised task tree with cancellation.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/rules/`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/dispatcher/` (data context)
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/orchestrator/`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/WorkflowService.groovy`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/workflow/`
//! - `legacy/plugins/orchestrator-plugin/`, `flow-control-plugin/`, `job-state-plugin/`,
//!   `upvar-plugin/`
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
