//! `rdx-scm` — git export/import (gix or git2), SCM API
//!
//! SCM integration: the git export and import plugins (status, actions, inputs, diff, job tracking)
//! and the SCM API endpoints with their legacy shapes.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/ScmService.groovy`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/scm/`
//! - `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/ScmController.groovy`
//! - `legacy/plugins/git-plugin/`
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
