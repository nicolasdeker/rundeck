# ADR-0001 — Rust rebuild with identical contracts, one binary, one workspace

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

Rundeck OSS `v6.3.0` (commit `6ac5d092`, Apache-2.0) is a Grails/Spring application: ~370k lines of Groovy and
~147k lines of Java (MISSION Appendix B). Its external surface is large and is what its users depend on: REST API
versions 14 → 60 (`legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/ApiVersions.groovy:60,68,69`:
`API_CURRENT_VERSION = V60`, `API_EARLIEST_VERSION = V14`, `API_DEPRECATION_VERSION = V17`), 120 `/api/$api_version`
route patterns in `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy` plus plugin-contributed
routes, a JSON error envelope built in `legacy/rundeckapp/grails-app/services/rundeck/services/ApiService.groovy:1033-1046`
(`error: true`, `apiversion`, `errorCode` defaulting to `api.error.unknown`, `message`), 23 domain classes
(22 under `legacy/rundeckapp/grails-app/domain/rundeck/` plus `legacy/grails-webhooks/grails-app/domain/webhooks/Webhook.groovy`),
35 plugin service types (`legacy/core/src/main/java/com/dtolabs/rundeck/plugins/ServiceNameConstants.java:35-76`),
15 built-in plugin modules (`legacy/plugins/*`), and 260 GSP pages across the Grails modules.

The owner wants a drop-in replacement that is measurably faster, smaller and more secure (MISSION §0, §4), built and
operated unattended from a phone (MISSION §7). The legacy stack cannot reach the §4 gates (cold start < 1 s, binary
< 60 MB, RSS ≤ 1/4 under 1,000 concurrent executions) and its UI is server-rendered GSP plus a Vue SPA bolted on.

## Decision

1. `rdx` is a from-scratch Rust implementation whose **backend behavior is identical** to legacy 6.3.0 for everything
   enumerated in MISSION §1 (API, file formats, data, behavior). "Identical" is defined by the oracle: the upstream
   functional suite (`legacy/functional-test`, 64 `@APITest` specs, driven by `TEST_RUNDECK_URL` /
   `TEST_RUNDECK_TOKEN` — `legacy/functional-test/readme.md:32,34`) must pass against the `rdx` binary, and
   differential golden files are captured from the `rundeck/rundeck:6.3.0` image (`scripts/oracle.sh`).
2. The **frontend is rebuilt** (ADR-0004): same user journeys and deep links, no legacy markup. Two standards, one
   product.
3. Working name **`rdx`**: binary `rdx`, crates `rdx-*`, repository `nicolasdeker/rundeck`. The product is not called
   Rundeck ("Rundeck" is a trademark of PagerDuty, Inc.). `NOTICE` keeps the Apache-2.0 attribution and a "not
   affiliated with PagerDuty, Inc." statement. Everything that is a contract keeps its legacy name verbatim even when
   it contains `rundeck`: config files (`rundeck-config.properties`, `framework.properties`, `realm.properties`),
   config keys (`rundeck.*`, `framework.*`, `dataSource.*`), HTTP headers (`X-Rundeck-Auth-Token`,
   `X-Rundeck-API-Version`), environment variables of the official image (`RUNDECK_*`,
   `legacy/docker/official/README.md:110-218`), filesystem paths (ADR-0009).
4. One Cargo workspace (`Cargo.toml`: resolver 3, edition 2024, `rust-version = "1.97"`, `unsafe_code = "forbid"`,
   `missing_docs = "deny"`, `clippy::pedantic` with an explicit allow-list, `unwrap_used`/`expect_used`/`todo` denied).
   Crates and roles (MISSION §3.1; dependency direction in `docs/ARCHITECTURE.md`, downwards only):

   | Layer | Crates |
   |---|---|
   | binary | `rdx` (CLI `serve`, `migrate`, `check-config`, `export`, `import`, `keys`, `acl check`, `doctor`; embeds `ui/`) |
   | edge | `rdx-api` (API v14–60), `rdx-ui-api` (`/ui-api/v1`), `rdx-web` (SPA, headers, redirects), `rdx-webhooks` |
   | service | `rdx-sched`, `rdx-workflow`, `rdx-exec`, `rdx-logging`, `rdx-notify`, `rdx-scm`, `rdx-nodes`, `rdx-storage`, `rdx-authn`, `rdx-authz`, `rdx-plugin` |
   | cross-cutting | `rdx-telemetry` |
   | infrastructure | `rdx-db` |
   | foundation | `rdx-formats`, `rdx-config`, `rdx-model`, `quartz-cron` (standalone, repo root) |
   | test support | `rdx-testkit` |

5. **One binary, no JVM, no external scheduler, no external cache.** Everything async on `tokio`; blocking work
   (process I/O, git, file copies) goes through `spawn_blocking` or dedicated threads with bounded queues (ADR-0002).
6. Every dependency carries a one-line justification in the crate's `Cargo.toml`; `cargo deny` (licenses, duplicate
   majors, crates.io only) and `cargo audit` stay clean (MISSION §4, §8).
7. The legacy tree lives read-only under `legacy/` at tag `v6.3.0`; it is the reference and the black-box oracle,
   never a dependency. Nothing under `legacy/` is edited except `legacy/README-LEGACY.md`.
8. Unimplemented endpoints return `501` with the legacy envelope and `errorCode: "api.error.not-implemented"`
   (MISSION §8); they stay `missing` in `PARITY.md`. No stub returns `200`.
9. Quality gates are code, not prose: coverage ≥ 80 % on library crates, no file > 800 lines, no function > 80 lines,
   cyclomatic complexity ≤ 25, every parser fuzzed (MISSION §4).

## Consequences

Positive: a single static-ish binary (ADR-0009) with sub-second start, memory safety without a GC, no JVM CVE
surface, predictable latency for log streaming, a modern UI that works on a phone, and a test oracle that makes
"done" objective.

Negative: ~500k lines of behavior to re-derive; two codebases to read during the whole mission; the Java plugin
ecosystem cannot be loaded in-process (ADR-0003); compile times on 4 vCPU runners demand the resource discipline of
MISSION §7.

Risks: silent behavior drift in rarely tested corners (mitigated by spec-first, golden files, and `PARITY.md` rows
that stay `missing` until an oracle run proves them); MISSION inventory numbers that disagree with the code
(this ADR cites the code; MISSION is corrected by commit when they disagree, MISSION §0).

## Compatibility impact

Untouched: every contract in MISSION §1.1–§1.5 (API, formats, behavior, data, script plugins). Deviations are owned
by the ADRs that introduce them and listed in `docs/COMPAT.md`: H2/SQLite (C-008, ADR-0005), jar and UI plugins
(C-009, C-010, ADR-0003), legacy Dropwizard pages (C-011, ADR-0008), the UI (C-012, C-013, C-015, C-021, ADR-0004),
security defaults (C-001…C-007, C-016, C-017, C-020, ADR-0007), TLS keystores and JAAS classes (C-018, C-019,
ADR-0002/0007). The product name is not a deviation: no contract carries the word "Rundeck" as a value except
where kept verbatim (statement 3).

## Alternatives considered

- Modernize the Java code base in place — rejected: cannot meet §4 (JVM footprint, cold start), keeps GSP.
- Go — rejected: the owner fixed the stack in MISSION §3; the needed ecosystem (`wasmtime`, `russh`, `sqlx`,
  `rustls`) and GC-free streaming favor Rust.
- GraalVM native image of the legacy app — rejected: Grails' reflection-heavy runtime makes it impractical and jar
  plugins would still not load dynamically.
- Hybrid (Rust API in front of the Java engine) — rejected: two runtimes, none of the §4 gains, double maintenance.

## Migration / rollout

An existing user on PostgreSQL or MySQL stops the Java server, installs `rdx` (ADR-0009), points it at the same
`/etc/rundeck` and the same database, and starts it; API clients, jobs, ACLs, node sources, script plugins and key
storage keep working. H2 users run `rdx migrate --from-h2` first (ADR-0005). Jar plugins are inventoried by
`rdx doctor` and matched against `docs/PLUGINS.md` (ADR-0003).

## References

- MISSION.md §0, §1, §2, §3.1, §4, §8; `docs/ARCHITECTURE.md`; `Cargo.toml`.
- `legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/ApiVersions.groovy:60,68,69`
- `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy` (120 `"/api/$api_version` patterns)
- `legacy/rundeckapp/grails-app/services/rundeck/services/ApiService.groovy:1033-1046`
- `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/ServiceNameConstants.java:35-76`
- `legacy/grails-webhooks/grails-app/domain/webhooks/Webhook.groovy`; `legacy/plugins/*` (15 directories)
- `legacy/functional-test/readme.md:32,34`; `legacy/docker/official/README.md:110-218`
