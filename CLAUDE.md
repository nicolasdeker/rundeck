# rdx — Rundeck rebuilt in Rust (identical backend contracts, new UI, cloud-only operation)

This repository is a fork of `rundeck/rundeck`. The mission is to re-implement Rundeck in Rust with **identical
external backend behavior** (API, file formats, plugin contracts, data) and a **brand-new web UI**. The full
mission brief is `MISSION.md`. **Read it at the start of every session, then `PLAN.md`, then the last 80 lines of
`JOURNAL.md`.** The owner supervises from a phone only (GitHub app + Claude app); nobody answers questions mid-run.

## Layout

- `legacy/` — the original Java/Groovy sources, pinned at upstream tag `v6.3.0` (commit `6ac5d092`). Read-only
  reference and black-box oracle (image `rundeck/rundeck:6.3.0`). Never edit it (exception: `legacy/README-LEGACY.md`).
- `crates/` — the Rust workspace (`rdx-*` crates). `Cargo.toml` at the root is the workspace.
- `ui/` — the new frontend (Vue 3 + TypeScript + Vite + PrimeVue 4 + Tailwind 4), built with `pnpm`, embedded in the binary.
- `specs/` — behavior specs written from the legacy code (`specs/<area>.md`, `specs/ui-journeys.md`), **before** the code.
- `docs/adr/` — Architecture Decision Records. `docs/COMPAT.md` — every externally visible deviation.
  `docs/ui-review/<phase>/` — screenshots for the owner.
- `PLAN.md` — phases, checklists, `← CURRENT` item. `PARITY.md` — contract matrix. `JOURNAL.md` — append-only session
  log. `DECISIONS-PENDING.md` — defaults taken (mirrored as GitHub issues labeled `decision`). `BLOCKED/` — one file per
  blocked item (mirrored as issues labeled `blocked`).
- `scripts/` — `family-window.sh` (calendar guard: may a run start now?), `prompts/{bootstrap,run,review}.md` (session
  prompts of the scheduled tasks), `cloud-setup.sh` (cloud environment setup script), `oracle.sh` (legacy Rundeck via
  Docker), `parity.sh` (upstream functional suite against the Rust binary), `bench/`.
  `.github/workflows/autopilot.yml` — opt-in API-billed alternative to the scheduled tasks (inert by default).

## Working rules (short form — MISSION.md is authoritative)

1. **Backend: parity before improvement.** External behavior matches legacy unless an ADR + `docs/COMPAT.md` entry says otherwise.
   **Frontend: rebuilt**, same user journeys, same deep links, nothing copied from the legacy UI as-is.
2. **Spec → tests → code.** No Rust module without its `specs/<area>.md` and ported tests; no UI page without its journey + Playwright test.
3. **Oracle, not opinion.** "Done" = the matching upstream functional tests pass against `rdx` (`scripts/parity.sh <filter>`)
   or the Playwright journey passes, and `PARITY.md` cites the run.
4. **Never fake green.** No skipped/deleted oracle tests, no stub endpoints returning 200, no `#[ignore]`/`test.skip` without a `BLOCKED/` file.
5. **Main is always green.** `make check` before every commit. Small conventional commits, pushed to `main` after each
   (`git push origin HEAD:main`). No force-push of `main`, no branches other than `main` and `autopilot-lock`.
6. **Family hours first, then one run at a time.** A scheduled run starts with `bash scripts/family-window.sh` and stops
   if it says blocked (never bypass it). Then take the `autopilot-lock` branch (skip the run if its tip says `lock …` and
   is younger than 3 h), release it at the end (`unlocked …` commit, force-pushed). Tags only via REST. See MISSION §7.
7. **Decide, record, continue.** Ambiguity → the parity-preserving option, an ADR or a `DECISIONS-PENDING.md` entry
   + `decision` issue, move on. Never ask.
8. **Stuck rule.** 3 failed attempts on one item → `BLOCKED/<id>.md` + `blocked` issue, take the next item.
9. **Context hygiene.** Never read large legacy files whole; grep, then read ranges. `legacy-analyst` subagent for
   exploration, `parity-reviewer` before closing an area or a phase gate.
10. **GitHub through REST only.** `gh api repos/nicolasdeker/rundeck/...`; `gh issue`/`gh pr` (GraphQL) are rejected here.
11. **No `unsafe`.** Workspace-wide `#![forbid(unsafe_code)]`.
12. **Every session ends within the guard's time budget with**: tests green, commit pushed to `main`, `JOURNAL.md` entry
    (done / evidence / next / risks, headed by the `scripts/progress.sh` line), `PLAN.md` updated, `README.md` status line
    refreshed (`scripts/progress.sh --update-readme`), lock released; the final message starts with the progress line.

## Commands

- `make check` — fast gate (fmt, clippy `-D warnings`, nextest, deny, audit, `pnpm lint`, `pnpm test`).
- `make oracle-up` / `make oracle-down` — legacy Rundeck 6.3.0 in Docker (`scripts/oracle.sh`).
- `make parity FILTER=<ApiSpecName>` — upstream Spock API tests against the Rust server.
- `make e2e` — Playwright journeys + screenshots into `docs/ui-review/`. `make bench`, `make fuzz TARGET=<name>`.

## Conventions

- Rust 2024 edition, stable toolchain pinned in `rust-toolchain.toml`. `cargo fmt` + `clippy::pedantic` (allow-list in `Cargo.toml`).
- Crate prefix `rdx-`. Binary `rdx`. Legacy config keys kept verbatim (`rundeck-config.properties`, `framework.properties`).
- Errors: `thiserror` in libraries, `anyhow` only in the binary. No `unwrap()`/`expect()` outside tests.
- Public items documented. Parsers get property tests (`proptest`) and a fuzz target.
- UI: `<script setup lang="ts">`, strict TS, no `any`, components ≤ 300 lines, i18n keys only (no hardcoded strings),
  `v-html` only through DOMPurify.
- Commit messages: `<type>(<area>): <summary>` — `feat|fix|spec|test|chore|docs|adr|perf|sec|ui`. Mention the parity spec or journey covered.

## Compaction note

When compacting, keep: the layout, the 12 working rules, the current `PLAN.md` item, and the last `JOURNAL.md` entry.
