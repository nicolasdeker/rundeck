//! `rdx-db` — `sqlx` (Postgres, `MySQL`, `SQLite`), repositories, legacy-compatible schema,
//! `rdx_migrations`
//!
//! Persistence behind one repository trait per aggregate (MISSION §3.3): `sqlx` for Postgres,
//! `MySQL` and `SQLite`, explicit transactions, the legacy Postgres/MySQL schema checked in and
//! diffed in CI against a fresh legacy init, and the `rdx_migrations` table for rdx-owned changes.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/rundeckapp/grails-app/migrations/` (Liquibase changelogs = the schema contract)
//! - `legacy/rundeckapp/grails-app/domain/rundeck/*.groovy` (GORM mappings, column names)
//! - `legacy/rundeckapp/grails-app/services/rundeck/services/data/`
//! - `legacy/rundeckapp/grails-app/conf/application.groovy` (`dataSource` keys)
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
