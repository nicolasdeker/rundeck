# rdx — Rundeck, rebuilt in Rust

**rdx** is a from-scratch re-implementation of [Rundeck OSS](https://github.com/rundeck/rundeck) (tag `v6.3.0`) as a
single Rust binary with a new web UI. An existing Rundeck user can drop it in place of the Java server **without
changing jobs, node sources, ACLs, config files, API clients, script plugins, or the Postgres/MySQL database**.

| | Legacy Rundeck 6.3.0 | rdx |
|---|---|---|
| REST API v14–60, file formats, DB schema, script plugins | contract | **identical** (verified by the upstream functional suite) |
| Web UI | Grails GSP + Vue 2/3 mix | **rebuilt**: Vue 3 + TypeScript + PrimeVue 4 + Tailwind 4, mobile-first, live execution view |
| Runtime | JVM, H2/Postgres/MySQL, Quartz | one static binary, SQLite/Postgres/MySQL, own Quartz-compatible scheduler |

Status: **Phase 0 (bootstrap)** — no product code yet. Progress is tracked in `PLAN.md` (phases), `PARITY.md` (the
contract matrix with oracle evidence) and `JOURNAL.md` (append-only session log). The project is developed
autonomously by scheduled Claude Code sessions; `MISSION.md` is the contract, `KICKOFF.md` the owner's runbook.

<!-- PROGRESS:BEGIN -->
**Progress: parity 0.0% (0/548 PARITY.md rows done or deviated; 0 partial, 0 blocked, 548 missing) · phase 0: 9/10 items · phases closed: 0/8 · areas: B 0/59 BP 0/15 P 0/33 D 0/23 W 0/171 J 0/73 S 0/35 R 0/119 F 0/20** (updated by `scripts/progress.sh` at the end of every run)
<!-- PROGRESS:END -->

## Layout

- `crates/` — the Rust workspace (`rdx-*` crates, binary `rdx`); `quartz-cron/` — standalone Quartz cron crate.
- `ui/` — the new frontend (pnpm), embedded into the binary at release build.
- `legacy/` — upstream sources at `v6.3.0`, read-only reference and test oracle (`legacy/README-LEGACY.md`).
- `specs/` — behavior specs written from the legacy code before the Rust code. `docs/adr/` — decision records;
  `docs/COMPAT.md` — every externally visible deviation; `docs/ui-review/` — screenshots per phase.
- `scripts/` — `oracle.sh` (legacy Rundeck in Docker), `parity.sh` (upstream functional tests against `rdx` or the
  legacy image), `bench/`, `cloud-setup.sh`, `family-window.sh`, `prompts/`.

## Commands

```sh
make check                 # fmt, clippy -D warnings, nextest, cargo-deny, cargo-audit, ui lint + unit tests
make oracle-up             # legacy Rundeck 6.3.0 + fixtures via docker compose (admin token: admintoken)
make parity FILTER=basic   # upstream API specs (package or class) against rdx (PARITY_TARGET=legacy for the baseline)
make e2e                   # Playwright journeys + screenshots into docs/ui-review/
```

## License and trademark

Apache License 2.0 (`LICENSE`, `NOTICE`). "Rundeck" is a trademark of PagerDuty, Inc.; rdx is not affiliated with or
endorsed by PagerDuty. Legacy configuration keys containing `rundeck` are kept verbatim for compatibility.
