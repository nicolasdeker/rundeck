//! `rdx-notify` — email, webhook, notification plugins
//!
//! Job notifications: the `onsuccess`/`onfailure`/`onstart`/`onavgduration`/`onretryablefailure`
//! triggers, email and webhook (HTTP) notifications with the legacy payloads and templates, and the
//! notification plugin service.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/NotificationService.groovy`
//! - `legacy/rundeckapp/grails-app/domain/rundeck/Notification.groovy`
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/notification/`
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
