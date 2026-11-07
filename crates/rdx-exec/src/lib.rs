//! `rdx-exec` — node executors (local, ssh via russh, script), file copiers (scp/sftp), process
//! supervision, pty/timeouts
//!
//! Node execution: the local, SSH (`russh`) and script node executors, scp/sftp file copiers,
//! process supervision with argv arrays (never a shell string), environment allow-lists, optional
//! PTY, timeouts and process-group kill on abort (MISSION §3.4).
//!
//! # Legacy references (ported in later phases)
//!
//! - `legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/` (`ExecutionContext.java`,
//!   `service/`, `impl/local/LocalNodeExecutor.java`, `script/`)
//! - `legacy/plugins/localexec-plugin/`, `script-plugin/`, `script-node-step-plugin/`,
//!   `copyfile-plugin/`, `jsch-plugin/`, `stub-plugin/`
//!
//! # Status
//!
//! Phase 0: scaffold, no code.

#![forbid(unsafe_code)]
