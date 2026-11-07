//! `rdx-logging` — execution log pipeline: streaming writers/readers, rdlog, log file storage
//! plugins, state tracking
//!
//! The execution log pipeline: streaming log writers and readers with bounded buffers, the `rdlog`
//! file format (shared codec in `rdx-formats`), log file storage plugins (upload/retrieve/partial),
//! and the execution state tracking that feeds the SSE fan-out.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/internal/RundeckLogFormat.java`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/logging/`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/LogFileStorageService.groovy`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/execution/logstorage/`
//! - `legacy/rundeckapp/grails-app/domain/rundeck/LogFileStorageRequest.groovy`
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
