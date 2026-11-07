# `rdx-testkit`

shared test harness: temp projects, in-memory DB, fake nodes, golden files, oracle client

Test-only support shared by the other crates: temporary projects and framework directories, an
in-memory/SQLite database, fake nodes and executors, golden-file assertions and a client for the legacy oracle
(`scripts/oracle.sh`). Never a dependency of the `rdx` binary.

## Legacy references (ported in later phases)

- `legacy/functional-test/` (the oracle suite: `BaseContainer`, `RdClient`, compose files)
- `legacy/rundeckapp/src/test/groovy/` and `legacy/core/src/test/` (fixtures worth porting)

## Parity specs this crate targets

- supports every `specs/*.md`; the oracle runs go through `scripts/parity.sh`

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
