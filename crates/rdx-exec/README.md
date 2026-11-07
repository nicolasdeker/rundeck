# `rdx-exec`

node executors (local, ssh via russh, script), file copiers (scp/sftp), process supervision, pty/timeouts

Node execution: the local, SSH (`russh`) and script node executors, scp/sftp file copiers, process supervision
with argv arrays (never a shell string), environment allow-lists, optional PTY, timeouts and process-group
kill on abort (MISSION §3.4).

## Legacy references (ported in later phases)

- `legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/` (`ExecutionContext.java`, `service/`, `impl/local/LocalNodeExecutor.java`, `script/`)
- `legacy/plugins/localexec-plugin/`, `script-plugin/`, `script-node-step-plugin/`, `copyfile-plugin/`, `jsch-plugin/`, `stub-plugin/`

## Parity specs this crate targets

- `specs/exec.md`
- upstream `api/executor/JschNodeExecutorSpec`, `api/executor/OpenSshNodeExecutorSpec`, `api/executor/SshjNodeExecutorSpec`, `api/filecopy/CopyfileSpec`, `api/project/RunCommandSpec`, `api/project/ExecuteScriptSpec`, `api/project/RunUrlSpec`

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
