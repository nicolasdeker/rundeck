//! `rdx-storage` — key storage: tree API, filesystem + DB backends, converters, AES-GCM encryption
//!
//! Key storage: the tree API (`keys/`), filesystem and database backends, storage converters and
//! the AES-GCM encryption converter, with the legacy on-disk/DB layout so existing installations
//! keep their keys.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeck-storage/` (`rundeck-storage-api`, `-conf`, `-data`, `-filesys`; see its
//!   `design.md`)
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/storage/`
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/StorageService.groovy`
//! - `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/StorageController.groovy`
//! - `legacy/rundeckapp/grails-app/domain/rundeck/Storage.groovy`
//! - `legacy/encryption-core/`, `legacy/plugins/aes-gcm-encryption-plugin/`
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
