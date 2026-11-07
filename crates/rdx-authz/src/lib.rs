//! `rdx-authz` — aclpolicy evaluation engine (port of rundeck-authz-core with its test corpus)
//!
//! A 1:1 port of the legacy authorization engine: policy loading, context matching
//! (project/system), `allow`/`deny` evaluation order, `by`/`notBy` subjects, resource matching with
//! regex/contains/subset rules, plus a typed policy layer for the `RdAuthorize*` annotation
//! semantics on every handler.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeck-authz/rundeck-authz-api/`
//! - `legacy/rundeck-authz/rundeck-authz-core/`
//! - `legacy/rundeck-authz/rundeck-authz-yaml/`
//! - test corpus: `legacy/rundeck-authz/rundeck-authz-yaml/src/test/`,
//!   `legacy/rundeck-authz/rundeck-authz-api/src/test/`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/authorization/`
//! - `legacy/rundeckapp/grails-app/controllers/rundeck/interceptors/AuthorizationInterceptor.groovy`
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
