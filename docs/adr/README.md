# Architecture Decision Records — rdx

ADRs record the decisions that shape `rdx` (MISSION.md §2, §3). MISSION.md §3 holds the decisions already taken by
the owner; an ADR refines one of them with testable statements, consequences, compatibility impact and a migration
path. ADRs are immutable once `Accepted`: a change is a new ADR that supersedes the old one (status `Superseded by
ADR-NNNN`).

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](0001-rust-rebuild-with-identical-contracts-and-workspace.md) | Rust rebuild with identical contracts, one binary, one workspace | Accepted | 2026-11-07 |
| [0002](0002-runtime-http-and-execution-model.md) | Runtime, HTTP stack and execution model | Accepted | 2026-11-07 |
| [0003](0003-plugins.md) | Plugins: script plugins unchanged, built-ins native, WASM ABI, no in-process jars | Accepted | 2026-11-07 |
| [0004](0004-frontend-rebuilt.md) | Frontend rebuilt: Vue 3 stack, salvage policy, UI-only API, review channel | Accepted | 2026-11-07 |
| [0005](0005-data-legacy-schema-and-sqlite.md) | Data: legacy Postgres/MySQL schema kept, `rdx_migrations`, SQLite default, H2 unsupported | Accepted | 2026-11-07 |
| [0006](0006-scheduler-quartz-compatible.md) | Scheduler: Quartz-compatible cron, DB-persisted schedule, cluster lease | Accepted | 2026-11-07 |
| [0007](0007-authentication-authorization-and-security-defaults.md) | Authentication, authorization and security defaults | Accepted | 2026-11-07 |
| [0008](0008-observability.md) | Observability: tracing, metrics projection, health, logs | Accepted | 2026-11-07 |
| [0009](0009-packaging-and-distribution.md) | Packaging and distribution | Accepted | 2026-11-07 |

Statuses: `Proposed` → `Accepted` → (`Deprecated` | `Superseded by ADR-NNNN`). Numbers are never reused.

## Rules (MISSION.md §2)

1. **Every externally visible deviation from legacy 6.3.0 behavior needs an ADR and a line in
   [`docs/COMPAT.md`](../COMPAT.md).** "Externally visible" means anything an API client, a file on disk, a database
   row, a plugin, a browser, a reverse proxy or an operator can observe. When unsure whether something is a contract,
   it is (MISSION §2): preserve it and record the doubt in `DECISIONS-PENDING.md`.
2. A deviation is allowed only for one of three reasons: **(a)** it fixes a security weakness, **(b)** the legacy
   behavior is a bug confirmed by legacy tests or docs, **(c)** the legacy feature is JVM-bound. The ADR names the
   reason and the `COMPAT.md` row cites the legacy code (`path:line`) that defines the behavior being changed.
3. Where feasible the deviation ships with a compatibility switch `rdx.compat.<name>=true` that restores the legacy
   behavior. **Switches default to the secure behavior.** Only the oracle fixture (`scripts/oracle.sh`, the `parity`
   workflow) may enable them, and only the ones its `COMPAT.md` row names. Never weaken a default to pass a test
   (MISSION §8).
4. Additive features (OIDC, OpenTelemetry, WASM ABI, UI extension API, `/ui-api/v1`) are documented in an ADR, land
   after their phase gate, default to off, and never alter a legacy contract.
5. Internals are free (MISSION §2): a decision that changes nothing observable needs no ADR, only a crate `README.md`
   or `docs/ARCHITECTURE.md` entry.
6. Every legacy fact in an ADR is cited as `legacy/<path>:<line>` and was verified by grep at the time of writing;
   statements that are inferred rather than read say so.

## Template

```markdown
# ADR-NNNN — <title>

- Status: Proposed | Accepted | Deprecated | Superseded by ADR-MMMM
- Date: YYYY-MM-DD
- Phase: N
- Deciders: owner via MISSION.md, autopilot

## Context
What forces are at play; which MISSION sections apply; which legacy behavior (path:line) is concerned.

## Decision
Numbered, specific, testable statements. Each one can be checked by a test, a CI job or a reviewer.

## Consequences
Positive. Negative. Risks (and how they are watched).

## Compatibility impact
Which legacy contracts are untouched. Which deviate, each with its `docs/COMPAT.md` id (C-NNN) and reason (a/b/c).

## Alternatives considered
Short, each with why it was rejected.

## Migration / rollout
What an existing Rundeck user must do: nothing, or exactly what.

## References
Legacy paths with line numbers (verified), MISSION.md sections, related ADRs and specs.
```

## Writing an ADR

- File name `NNNN-<slug>.md`, four digits, lowercase slug. Add the row to the index above in the same commit.
- 80–180 lines, dense. No filler, no restating MISSION.md: cite it.
- Commit type `adr(<area>): ...` (CLAUDE.md conventions).
- When an ADR introduces a `rdx.compat.<name>` switch, the same commit adds the `COMPAT.md` row with status `planned`;
  the implementing commit flips it to `implemented`; the first green oracle run that exercises it flips it to
  `verified` with the run reference.
