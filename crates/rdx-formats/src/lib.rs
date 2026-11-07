//! `rdx-formats` — job XML/YAML/JSON codecs, resources xml/yaml/json, aclpolicy YAML, rdlog,
//! project archive
//!
//! Every externally visible file format of MISSION §1.2: job definitions (XML/YAML/JSON), resource
//! model documents, `.aclpolicy` YAML, the `rdlog` execution log format and the project archive
//! (`.zip`/`.jar`). Round-trip byte-stable where the legacy codecs are, semantically identical
//! otherwise. Every parser gets property tests and a fuzz target (MISSION §4).
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeckapp/grails-app/utils/rundeck/codecs/JobsXMLCodec.groovy`
//! - `legacy/rundeckapp/grails-app/utils/rundeck/codecs/JobsYAMLCodec.groovy`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/resources/format/`
//! - `legacy/rundeck-authz/rundeck-authz-yaml/`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/internal/RundeckLogFormat.java`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/ProjectService.groovy` (archive
//!   export/import)
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
