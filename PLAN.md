# PLAN — rdx phases as checklists (MISSION.md §6). Exactly one item is marked `← CURRENT`.

Granularity: 1–3 hours per item. Ids are stable (`P<phase>-<nn>`); JOURNAL.md entries and BLOCKED/ files cite them.
A phase closes when its exit gate is met (oracle specs green, `make check` green, benches recorded, ADRs merged,
screenshots updated, tag `phase-N` via REST, journal summary).

## Phase 0 — Bootstrap (no product code)

- [x] P0-01 Repo surgery: Java tree → `legacy/` pinned at `v6.3.0`, kit at the root, `NOTICE`, `.gitmodules`, `.gitignore` (commit 513185b)
- [x] P0-02 Cloud environment: setup script runs from the checkout's parent (`scripts/cloud-setup.sh`, env `RDX` re-saved), Maven mirror init script, oracle tools image (commit c7f6353 + follow-ups)
- [x] P0-03 Rust workspace scaffold: `Cargo.toml`, 22 `rdx-*` crates + `quartz-cron`, toolchain/fmt/clippy/deny, `Makefile`, `docs/ARCHITECTURE.md`
- [x] P0-04 `ui/` scaffold (Vue 3 + Vite + PrimeVue 4 + Tailwind 4) with lint/test/e2e; login shell; screenshots in `docs/ui-review/phase-0/`
- [ ] P0-05 CI: `ci.yml`, `parity.yml`, `nightly.yml`, `release.yml`; `scripts/oracle.sh`, `scripts/parity.sh`, `scripts/parity-report.py`, `scripts/bench/`, `tests/parity-skips.toml`
- [ ] P0-06 `PARITY.md` inventory (routes, service types, plugins, domain classes, formats, behavior, journeys) + `specs/ui-journeys.md` + `specs/README.md`
- [x] P0-07 ADR-0001..0009 + `docs/COMPAT.md` (commit: adr, 21 COMPAT rows, 87 verified legacy citations)
- [ ] P0-08 Oracle proven: `legacy/functional-test` `apiTest` against `rundeck/rundeck:6.3.0` in-session and in `parity.yml`; baseline recorded in `PARITY.md`
- [ ] P0-09 Scheduled tasks `rdx-autopilot` and `rdx-review` created; owner actions journaled
- [ ] P0-10 Exit gate: `ci.yml` green on `main`, journal summary, tag `phase-0`

## Phase 1 — Foundations (backend + UI foundation)

- [ ] P1-01 `specs/config.md` + `rdx-config`: `rundeck-config.properties`, `framework.properties`, `project.properties`, env overrides, typed config (legacy `PropertyLookup`, `Framework` init) ← CURRENT-NEXT
- [ ] P1-02 `specs/db-schema.md` + `rdx-db`: legacy Postgres schema captured from a 6.3.0-initialized DB, `rdx_migrations`, SQLite/MySQL/Postgres pools, repositories Project/User/AuthToken/StoredEvent
- [ ] P1-03 `specs/api-envelope.md` + `rdx-api` skeleton: version negotiation 14–60, error envelope JSON/XML, content negotiation, `/api/*/system/info`, 501 `api.error.not-implemented` for everything else
- [ ] P1-04 `specs/authn.md` + `rdx-authn`: `realm.properties` (all formats), tokens (hashed at rest, roles, expiry), sessions, `/j_security_check`, preauth headers
- [ ] P1-05 `specs/authz.md` + `rdx-authz`: port of `rundeck-authz-core` with its test corpus; `.aclpolicy` YAML; `/api/*/system/acl/*`, `/api/*/project/*/acl/*`
- [ ] P1-06 `/tokens`, `/user/*`, `/authorizations/*`, `/feature/*` endpoints; `scripts/parity.sh --target rdx` wiring; `PARITY_RDX_ENABLED=true`
- [ ] P1-07 `rdx-web` shell + legacy deep-link redirects; `rdx-ui-api` session/CSRF; `rdx-telemetry` tracing + `/health`
- [ ] P1-08 UI foundation: design tokens, PrimeVue preset, app shell/navigation, login against `rdx`, profile, tokens management, generated API client, i18n pipeline, Storybook
- [ ] P1-09 `ldapTest` compose green; legacy-initialized Postgres boots `rdx` (CI job)
- [ ] P1-10 Exit gate: upstream `basic`, `acl`, `authorizations`, `system` (non-execution) green; journeys login/logout, tokens, profile; tag `phase-1`

## Phase 2 — Projects, nodes, storage
- [ ] P2-01 … (planned by the Phase 1 closing review; see MISSION.md §6)

## Phase 3 — Jobs, workflow, executions, scheduler
- [ ] P3-01 …

## Phase 4 — Everything else in the API
- [ ] P4-01 …

## Phase 5 — UI completeness, extension API, polish
- [ ] P5-01 …

## Phase 6 — Hardening, performance, packaging, migration
- [ ] P6-01 …

## Phase 7 — Release
- [ ] P7-01 …
