//! `rdx-config` — properties/JAAS/project.properties parsing, env overrides, typed config, legacy
//! key names
//!
//! Parses `rundeck-config.properties`, `framework.properties`, `project.properties`, JAAS login
//! configuration and the `RUNDECK_*` environment overrides of the official container into a typed,
//! validated configuration. Legacy key names are kept verbatim (MISSION §1.2, CLAUDE.md
//! Conventions).
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeckapp/grails-app/conf/application.groovy` (defaults)
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/ConfigurationService.groovy`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/FrameworkService.groovy`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/common/Framework.java`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/utils/PropertyLookup.java`
//! - `legacy/docker/official/` (environment variable names, remco templates)
//! - `legacy/packaging/` (file locations)
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
