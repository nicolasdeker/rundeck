//! `rdx-testkit` — shared test harness: temp projects, in-memory DB, fake nodes, golden files,
//! oracle client
//!
//! Test-only support shared by the other crates: temporary projects and framework directories, an
//! in-memory/SQLite database, fake nodes and executors, golden-file assertions and a client for the
//! legacy oracle (`scripts/oracle.sh`). Never a dependency of the `rdx` binary.
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/functional-test/` (the oracle suite: `BaseContainer`, `RdClient`, compose files)
//! - `legacy/rundeckapp/src/test/groovy/` and `legacy/core/src/test/` (fixtures worth porting)
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
