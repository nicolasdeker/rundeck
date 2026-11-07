//! `rdx-webhooks` — webhook endpoints + event plugins
//!
//! Inbound webhooks: the `/api/*/webhook/*` endpoints, webhook authentication, the webhook event
//! plugin service (run-job and log-events providers) and the project export/import of webhook
//! definitions.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/grails-webhooks/` (`Webhook.groovy` domain, `WebhookController.groovy`,
//!   `WebhookService.groovy`, `authenticator/`, `exporter/`, `importer/`)
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/webhook/`
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
