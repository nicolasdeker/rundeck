# MISSION — Rebuild Rundeck as `rdx`: Rust backend with identical contracts, new frontend, cloud-only operation

You are the sole engineer on this project. The owner (Nico) supervises **from an iPhone only**, through
the Claude app and the GitHub app. He never has a terminal. You never ask him anything mid-run: you decide,
record, continue. This file is the contract between you and the owner. Read it fully at every session start.

Upstream reference: `rundeck/rundeck` tag **`v6.3.0`** (commit `6ac5d092e6ccde3fd580ac61371487a300a0b6ca`,
`version.number=6.3.0`), Apache-2.0. The matching release artifacts (`rundeck/rundeck:6.3.0` Docker image) are the
black-box oracle. Measured facts about that tag are in Appendix B; where this file and the legacy code disagree,
**the legacy code wins** — fix this file via a commit.

---

## 0. Prime directive

Build `rdx`: a Rust re-implementation of Rundeck OSS with a brand-new web UI, that an existing Rundeck user can
drop in place of their Java server **without changing their jobs, node sources, ACLs, config files, API clients,
script plugins, or Postgres/MySQL database**, and that is measurably faster, smaller, more secure, and far better to
use (including on a phone) than the original.

Two different standards apply:
- **Backend contracts (§1): identical.** API, file formats, data, behavior. This is what makes `rdx` a replacement.
- **Frontend (§1.6, §3.8): rebuilt.** Same user journeys and same deep links, modern stack, no legacy markup kept.

"Improved" is defined by the measurable gates in §4. Anything not measurable is not a goal.

The product is not called Rundeck ("Rundeck" is a trademark of PagerDuty, Inc.). Working name: **rdx**
(binary `rdx`, crates `rdx-*`). Keep `NOTICE` with the Apache-2.0 attribution and a "not affiliated with PagerDuty"
statement. Legacy config keys that contain the word `rundeck` are kept verbatim for compatibility.

**Operating model (non-negotiable):** unattended sessions run as Claude Code **cloud scheduled tasks** on the owner's
subscription, only outside the family's homework hours — Europe/Zurich **Mon–Fri 16:00–22:00 and Sat–Sun 09:00–19:00**
are protected, plus the 5-hour usage-session buffer before each window — as enforced by `scripts/family-window.sh`,
which every scheduled run executes first and never bypasses. A daily run cap keeps the weekly limit under control.
An API-billed GitHub Actions alternative exists but is opt-in. State lives in git. Progress is reviewable from the
GitHub app and the Claude app. Details in §7.

---

## 1. The parity contract — what must be identical

Everything below is verified by the oracle: the **upstream functional test suite** in `legacy/functional-test`
(Spock, 64 `@APITest` specs) run against the Rust binary via `TEST_RUNDECK_URL` / `TEST_RUNDECK_TOKEN`
(see `legacy/functional-test/readme.md`), plus differential tests you write against a running legacy container
(`scripts/oracle.sh`, image `rundeck/rundeck:6.3.0`).

### 1.1 REST API
- Versions **14 → 60** (`legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/ApiVersions.groovy`:
  `API_EARLIEST_VERSION = 14`, `API_DEPRECATION_VERSION = 17`, `API_CURRENT_VERSION = 60`).
  Same version negotiation, same `X-Rundeck-API-Version` response header, same error envelope
  (`{"error":true,"apiversion":60,"errorCode":"...","message":"..."}` — `ApiService.renderErrorJson`, and the XML
  equivalent `<result error="true" apiversion="60">`), same per-version behavior switches where the legacy code
  branches on `request.api_version`.
- All **120 route patterns** in `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy`
  (`/api/$api_version/...`) plus the routes contributed by the Grails plugins
  (`legacy/grails-webhooks`, `grails-metricsweb`, `grails-repository`, `grails-rundeck-data-shared`,
  `grails-execution-mode-timer`, `grails-job-kill-handler`). Same methods, status codes, JSON shapes, XML shapes where
  XML is still supported, pagination params (`offset`, `max`), filters, and `Content-Type` handling
  (`application/json`, `application/xml`, `application/yaml`, `text/plain`, multipart).
- Authentication: API tokens (`X-Rundeck-Auth-Token` header and `authtoken` param), session cookie after form login
  (`/j_security_check`), pre-authenticated mode (`rundeck.security.authorization.preauthenticated.*` headers from a
  reverse proxy). Token roles, expiry, `/api/*/tokens` lifecycle.
- The generated OpenAPI documents (`META-INF/swagger/api-*.yml` produced by `legacy/gradle/grailsopenapispec.gradle`)
  are a secondary oracle: your `utoipa` spec must be a superset at the path/operation level; diff it in CI.

### 1.2 File formats (round-trip byte-stable where legacy is, semantically identical otherwise)
- Job definitions: XML, YAML, JSON — `legacy/rundeckapp/grails-app/utils/rundeck/codecs/JobsXMLCodec.groovy`,
  `JobsYAMLCodec.groovy`, and the JSON shape used by the API. Import with `dupeOption` semantics, UUID handling, export.
- Node resources: `resources.xml` / `.yaml` / `.json`, node attributes, tags, the **node filter language**
  (`legacy/core/src/main/java/com/dtolabs/rundeck/core/utils/NodeSet.java`, `common/NodeFilter.java`).
- ACL policies: `*.aclpolicy` YAML (`legacy/rundeck-authz/rundeck-authz-yaml`), same evaluation semantics
  (`rundeck-authz-core`), same validation messages where tests assert them.
- Config: `rundeck-config.properties`, `framework.properties`, `project.properties` (incl. `rundeck.server.uuid`,
  cluster mode), `realm.properties` (every credential format legacy's `PropertyFileLoginModule` accepts — verify in
  `legacy/rundeckapp/src/main/java/.../jaas/`), `jaas-loginmodule.conf` (parse the JAAS format, map modules to native
  auth providers: property file, LDAP, LDAP combined, PAM; see §3.7), `log4j2.properties` (accept; map to `tracing`).
- Execution logs: the `.rdlog` format (`legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/internal/RundeckLogFormat.java`)
  so existing log archives remain readable and `output` endpoints return identical entries.
- Key storage layout (filesystem backend path layout + metadata, DB backend table), converter plugin semantics
  (`legacy/rundeck-storage`, `legacy/plugins/aes-gcm-encryption-plugin`).
- Project archives (export/import zip: jobs, executions, configs, ACLs, readme/motd, scm).
- Script plugins: zip + `plugin.yaml` contract (`legacy/core/src/main/java/com/dtolabs/rundeck/core/plugins/ScriptPlugin*`,
  `legacy/plugins/script-plugin`), providers for NodeExecutor, FileCopier, ResourceModelSource, WorkflowStep,
  WorkflowNodeStep, Notification, etc. **Existing script plugins must run unchanged.**

### 1.3 Behavior
- Workflow engine: strategies `sequential`, `parallel`, `node-first`, the rule-engine executor
  (`legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/`, `rules/`), error handlers, `keepgoing`,
  step/node contexts, shared data context and variable expansion (`${option.x}`, `@option.x@`, `${node.name}`,
  `${data.x*}`, `${globals.*}`, `${job.*}`, secure option handling), log filters, job references (import options,
  node intersect, child failure propagation), orchestrators, node dispatch (`threadcount`, `rankAttribute`,
  `rankOrder`, `keepgoing`, `nodesSelectedByDefault`, `excludeFilterUncheck`), retries (`retry`, `retryDelay`),
  timeouts, `multipleExecutions`, `loglevel`, `defaultTab`.
- Executions: run (node filter/options/`asUser`/`runAtTime`), abort (`asUser`, `forceIncomplete`), retry from
  execution, follow output (offset/lastlines/`lastmod`, `compacted`), state, bulk delete, metrics, `executions/running`,
  execution mode (passive/active), `rundeck.execution.logs.*` rules.
- Scheduler: **Quartz cron syntax** (6–7 fields, seconds, `?`, `L`, `W`, `#`, day-of-week numbering), timezone,
  `scheduleEnabled`/`executionEnabled`, forecast API, cluster ownership (`serverNodeUUID`), takeover API, schedule
  recovery after restart, `rundeck.scheduler.*` thresholds.
- Projects, nodes, sources (file/url/script/plugin, refresh, caching, per-source editable nodes), readme/motd, config
  keys, per-project plugin config, ACL files (system + project), feature flags endpoint.
- Notifications (email, webhook, plugin), webhooks (incl. `WebhookEvent` plugins and token handling), SCM export/import
  with git (`legacy/plugins/git-plugin`), log file storage plugins and incomplete-storage resume, file uploads for
  options, remote option values (`OptionValues`), `NodeEnhancer`, `UserGroupSource`, execution/job lifecycle plugins,
  audit events.

### 1.4 Data
- On PostgreSQL and MySQL, `rdx` **starts against a database initialized by legacy 6.3.0** and keeps working on it:
  same table/column names and types for the 23 domain classes (`legacy/rundeckapp/grails-app/domain/`, Liquibase
  changelogs in `legacy/rundeckapp/grails-app/migrations/`). Any additive schema change goes in `rdx`'s own migration
  table (`rdx_migrations`), never in Liquibase's. A CI job initializes Postgres with the legacy image, boots `rdx` on
  it and runs the parity suite.
- H2 is JVM-only and cannot be supported. Embedded default becomes **SQLite**. Ship `rdx migrate --from-h2` that
  consumes a legacy project export + a dump produced by a documented procedure (JDBC → CSV via the legacy
  container), and verify it in CI.

### 1.5 Out of scope for v1 (document, do not build)
- Loading **Java `.jar` plugins** in-process. Replacement contracts in §3.5. Record popular community jar plugins and
  their replacement status in `docs/PLUGINS.md`.
- Legacy **`UI` plugins** (JS injected into GSP pages). Deviated: the new UI exposes its own extension API in Phase 5
  (ADR). PagerDuty Process Automation / Enterprise features. The Dropwizard admin HTML pages (`grails-metricsweb`);
  the JSON endpoints under `/api/*/metrics/*` are kept. Guided Tours (`TourController`): keep the API shapes.

### 1.6 User journeys (the UI contract — behavior, not markup)
- Every user journey the legacy UI offers exists in the new UI: inventory it in `specs/ui-journeys.md` from the
  57 Selenium specs (`legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/selenium`), the 260 GSP pages
  (`legacy/rundeckapp/grails-app/views/**/*.gsp`) and the SPA routes/components
  (`legacy/rundeckapp/grails-spa/packages/ui-trellis/src`). Each journey gets a Playwright test in `ui/e2e/`.
- **Deep links keep resolving** (bookmarks, emails, webhooks and notifications carry them): `/project/$p/job/show/$id`,
  `/project/$p/execution/show/$id`, `/project/$p/jobs`, `/project/$p/nodes`, `/project/$p/activity`, `/project/$p/home`,
  `/menu/*`, `/user/login`, `/resources/*` — new routes may differ, old ones redirect.
- i18n: every message key of `legacy/rundeckapp/grails-app/i18n/` and ui-trellis bundles that the new UI needs is
  carried over (converted), languages kept.
- The UI only talks to the legacy API (§1.1) plus the UI-only API of §3.8; no second backend contract.

---

## 2. Improvements and deviations — governance

- **Internals are free.** Rewrite everything behind the contracts in §1. Do not port Grails/Spring/GORM idioms;
  port behavior.
- **External deviations need an ADR** in `docs/adr/NNNN-*.md` (status, context, decision, consequences, migration)
  **and** a line in `docs/COMPAT.md`. They are allowed only when (a) they fix a security weakness, (b) legacy behavior
  is a bug confirmed by legacy tests or docs, or (c) the legacy feature is JVM-bound (H2, jar plugins, JAAS classes,
  GSP-injected UI plugins). Where feasible keep a compatibility switch (`rdx.compat.<name>=true`) defaulting to the
  secure behavior.
- **Pre-approved deviations** (write the ADRs in Phase 0): API tokens stored hashed; new local passwords hashed with
  argon2id while all legacy `realm.properties` formats remain accepted; stricter default security headers/CSP (legacy
  `grails-securityheaders` is the floor); session cookies `Secure`/`HttpOnly`/`SameSite=Lax`; constant-time
  comparisons; log files `0600`; no default `admin/admin` credentials in packaged artifacts unless
  `RDX_INSECURE_DEFAULT_ADMIN=1` (the oracle fixture sets it so the upstream tests stay runnable); the whole UI (§3.8).
- **Additive features are allowed only after their phase gate** and off by default: OIDC/OAuth2 login, Prometheus
  exposition, OpenTelemetry traces, WASM plugin ABI, UI extension API. They never alter a legacy contract.
- When unsure whether something is a contract: **it is**. Preserve it, note it in `DECISIONS-PENDING.md`.

---

## 3. Target architecture (decisions already taken — refine via ADR, do not re-litigate)

### 3.1 Workspace
```
crates/
  rdx            binary: CLI (`serve`, `migrate`, `check-config`, `export`, `import`, `keys`, `acl check`, `doctor`)
  rdx-config     properties/JAAS/project.properties parsing, env overrides, typed config, legacy key names
  rdx-model      domain types (Job, Workflow, Option, Execution, Node, Project, Token, User, Webhook...), serde codecs
  rdx-formats    job XML/YAML/JSON codecs, resources xml/yaml/json, aclpolicy YAML, rdlog, project archive
  rdx-db         sqlx (Postgres, MySQL, SQLite), repositories, legacy-compatible schema, rdx_migrations
  rdx-authn      realm.properties, LDAP (ldap3), PAM, preauth headers, sessions, tokens, (later) OIDC
  rdx-authz      aclpolicy evaluation engine (port of rundeck-authz-core with its test corpus)
  rdx-storage    key storage: tree API, filesystem + DB backends, converters, AES-GCM encryption
  rdx-nodes      node model, node filter language, resource model sources, caching, node enhancers
  rdx-workflow   workflow engine: strategies, rule engine, contexts, data/variable expansion, log filters, orchestrators
  rdx-exec       node executors (local, ssh via russh, script), file copiers (scp/sftp), process supervision, pty/timeouts
  rdx-logging    execution log pipeline: streaming writers/readers, rdlog, log file storage plugins, state tracking
  rdx-sched      Quartz-compatible cron, scheduler, cluster ownership, takeover, execution mode
  rdx-plugin     plugin registry, descriptors/properties, script plugin host, WASM host (wasmtime), built-in providers
  rdx-scm        git export/import (gix or git2), SCM API
  rdx-notify     email, webhook, notification plugins
  rdx-webhooks   webhook endpoints + event plugins
  rdx-api        axum router: API v14–60, auth middleware, error envelope, OpenAPI (utoipa), XML/JSON/YAML negotiation
  rdx-ui-api     UI-only API (`/ui-api/v1`): SSE streams, aggregated views, session/CSRF — not a compatibility contract
  rdx-web        embedded SPA (rust-embed), security headers, legacy deep-link redirects
  rdx-telemetry  tracing, metrics (Prometheus registry → legacy Dropwizard JSON shape on /api/*/metrics), health
  rdx-testkit    shared test harness: temp projects, in-memory DB, fake nodes, golden files, oracle client
quartz-cron      standalone crate: Quartz cron parser/evaluator (property-tested against a legacy-derived corpus)
ui/              the new frontend (§3.8), built by `pnpm`, embedded into `rdx` at release build
```
One binary, no JVM, no external scheduler, no external cache. Everything async on `tokio`; blocking work
(process spawn I/O, git, file copies) through `spawn_blocking` or dedicated threads with bounded queues.

### 3.2 Runtime & HTTP
`tokio` multi-thread, `axum` + `tower` (timeouts, concurrency limits, request-id, compression, body limits),
`hyper` 1.x, `rustls` only (no OpenSSL), HTTP/1.1 + HTTP/2, graceful shutdown with execution drain and in-flight
log flush. Streaming endpoints (`execution output`, SSE) use bounded channels with backpressure; never buffer a whole
log in memory.

### 3.3 Data
`sqlx` with runtime-checked queries per backend behind a repository trait per aggregate; explicit transactions;
migrations in `crates/rdx-db/migrations/{postgres,mysql,sqlite}`; the Postgres/MySQL schema is the legacy schema
(generated once from a legacy-initialized DB, checked in, diffed in CI against a fresh legacy init). Pool sized from
config, statement timeouts, no N+1 (tests assert query counts on hot paths).

### 3.4 Execution model
Each execution is a supervised task tree: workflow task → step tasks → node tasks, with cancellation tokens,
structured concurrency, per-execution resource limits (threadcount, max log bytes, timeouts), and an append-only
event stream feeding the log writers, the state machine, and the SSE fan-out. Child processes run with argv arrays
(no shell interpolation), env allow-lists, working dir, optional PTY, process-group kill on abort, zombie reaping.

### 3.5 Plugins (ADR-0003)
Tier 1: **script plugins** unchanged (zip + `plugin.yaml`, same provider types, env/argument contract, output parsing).
Tier 2: **built-in providers** ported natively in Rust (everything in `legacy/plugins/*`: localexec, script,
script-node-step, stub, copyfile, job-state, source-refresh, flow-control, aes-gcm-encryption, object-store
(S3-compatible), orchestrator, git, audit-logging, upvar, jsch→russh). Tier 3: a **WASM Component Model ABI**
(`wit/` definitions mirroring the 36 service types in `legacy/core/.../ServiceNameConstants.java`), hosted by
`wasmtime` with capability-scoped WASI. Tier 4 (not v1): a JVM sidecar over gRPC for jar plugins — design note only.
Plugin descriptors, property schemas, `/plugin/list` and `/plugin/detail` keep the legacy shapes.

### 3.6 Scheduler (ADR-0006)
Own Quartz-compatible cron crate; scheduler persisted in DB (next fire time, owner UUID, misfire policy matching
Quartz defaults as legacy configures them); cluster mode by DB lease (`SELECT ... FOR UPDATE SKIP LOCKED` on
Postgres/MySQL, single-node on SQLite); takeover endpoint moves ownership; recover schedules on boot.

### 3.7 Auth (ADR-0007)
`realm.properties` + roles with hot reload; LDAP/LDAPS with the same config keys as the legacy JAAS modules (bind DN,
user/role base, filters, role name attribute, nested groups, `supplementalRoles`); PAM via the `pam` crate;
preauthenticated headers; API tokens (hashed at rest, roles subset enforcement, expiry, `creator`); server-side
sessions in DB with absolute + idle timeouts; CSRF double-submit for the SPA; rate limiting on login and token
endpoints; audit events for every auth decision. Authorization: port `rundeck-authz-core` 1:1 with its test corpus
(`legacy/rundeck-authz/**/src/test`), then the `RdAuthorize*` annotations' semantics as a typed policy layer on every
handler (a test walks the router and fails on any handler without an explicit auth check).

### 3.8 Frontend — rebuilt (ADR-0004)
- **Stack:** Vue 3.5 (`<script setup>`, Composition API, TypeScript `strict`), Vite, Pinia, vue-router, TanStack Query
  (Vue), PrimeVue 4 (Aura preset) + Tailwind 4 for layout/tokens, CodeMirror 6 (job scripts, YAML/JSON editors),
  vue-flow (workflow graph), date-fns + `@internationalized/date`, vue-i18n with the converted legacy bundles,
  `openapi-typescript` + `openapi-fetch` client generated from `rdx`'s OpenAPI document, Vitest + Testing Library,
  Playwright for e2e, Storybook for the component library, `pnpm`, ESLint flat config + Prettier.
  *Alternative considered: React 19 + TanStack Router/Query + shadcn/ui. Rejected for v1 to keep the i18n bundles,
  domain types and the upstream community's Vue direction salvageable. One-line change in ADR-0004 if the owner
  reverses it.*
- **Salvage policy:** nothing from `legacy/rundeckapp/grails-spa` is copied as-is. Domain TypeScript types
  (`JobDefinition.ts` etc.), i18n bundles and pure utility functions may be ported after review and typing; every
  component is rewritten. No GSP, no server-rendered HTML except the SPA shell.
- **Product requirements:** mobile-first (the owner reviews on a 375 px-wide screen; every core journey works there),
  dark/light themes, keyboard navigation and WCAG 2.2 AA, instant navigation (route-level code splitting, optimistic
  updates), **live execution view** (SSE from `/ui-api/v1/executions/{id}/events`: log lines, step/node state,
  progress), job editor with workflow graph + YAML/JSON round-trip, node browser with the legacy filter language and
  autocomplete, activity timeline, key storage browser, ACL editor with live `rdx acl check` validation, project
  settings, plugin configuration forms generated from plugin property descriptors, global search / command palette.
- **UI-only API** (`/ui-api/v1`, `rdx-ui-api`): SSE streams, aggregated dashboards, session/CSRF endpoints. Documented as
  non-contract; versioned; every endpoint authorized through the same `rdx-authz` layer.
- **Delivery:** `ui/` builds to static assets embedded with `rust-embed`, served with hashed immutable caching; the
  dev loop is `pnpm dev` proxying to `rdx serve`.
- **Review channel for the owner:** `pnpm e2e` writes screenshots (375 px and 1280 px, light and dark) of every
  journey into `docs/ui-review/<phase>/`; the gate summary in `JOURNAL.md` links them so they can be viewed in the
  GitHub app.

### 3.9 Observability (ADR-0008)
`tracing` everywhere with execution/job/project/user fields; OpenTelemetry OTLP export optional; a Prometheus
registry exposed at `/metrics` (new) and projected into the legacy Dropwizard JSON shape at `/api/*/metrics/*`;
`/api/*/system/info` and `/health` keep legacy content; structured JSON logs with secret redaction.

### 3.10 Packaging (ADR-0009)
Static-ish Linux binaries (x86_64, aarch64; musl where PAM allows, else glibc), distroless container as non-root with
read-only root FS, deb/rpm mirroring `legacy/packaging` paths (`/etc/rundeck`, `/var/lib/rundeck`, `/var/log/rundeck`,
systemd unit, env variable names of `legacy/docker/official`), a Helm chart, SBOM (CycloneDX via `cargo-cyclonedx`),
signed releases (`cosign`), reproducible-build flag.

---

## 4. Non-functional gates (measured in CI; a phase cannot close with a red gate)

**Security**
- `#![forbid(unsafe_code)]` workspace-wide; `cargo deny` (licenses: Apache-2.0, MIT, BSD-2/3, ISC, Zlib, MPL-2.0 case
  by case; bans duplicate majors; crates.io only); `cargo audit` clean or documented waivers with expiry.
- Fuzz targets (`cargo-fuzz`) for every parser: job XML/YAML/JSON, resources formats, aclpolicy, node filter, Quartz
  cron, rdlog, properties/JAAS, project archive. ≥ 60 s each in the nightly workflow, corpora checked in.
- Threat model (`docs/THREAT-MODEL.md`, STRIDE per trust boundary) and an abuse-case suite: path traversal in key
  storage/log/project paths, command injection in node steps and script plugins, SSRF in URL sources/webhooks/
  notifications, XXE off, YAML tags off, zip-slip in imports, token/credential leakage in logs, authz bypass via API
  version, mass assignment, DoS via unbounded bodies/logs/option values, CSRF on the SPA, XSS in log rendering.
- Secrets: `zeroize`/`secrecy` types, never `Debug`-printable, never in URLs, redaction in tracing. Supply chain:
  pinned lockfiles (Cargo and pnpm), `pnpm audit` clean or waived, SBOMs per release, provenance attestations.

**Performance** (vs the legacy container on the same runner; `scripts/bench/` with `k6` + `hyperfine`;
numbers recorded in `docs/BENCHMARKS.md` per phase)
- API p99 for `GET /api/60/project/$p/jobs`, `GET /api/60/execution/$id/output`, `POST /api/60/job/$id/run` at 50
  concurrent clients ≥ **5× better** than legacy, or a documented reason.
- 1,000 concurrent executions of a 5-step local job on 1 node: RSS ≤ **1/4** of legacy, no error, no lost log lines.
- Log streaming: 100 MB execution log followed by 10 clients with no memory growth beyond buffers.
- Cold start to first request **< 1 s**; binary **< 60 MB** including the UI.
- Scheduler: 10,000 scheduled jobs loaded and next-fire computed in **< 2 s**; cron ≥ 1M evaluations/s.
- Criterion benches for: cron, node filter, variable expansion, rdlog read/write, aclpolicy evaluation.

**Frontend**
- Lighthouse (mobile preset) ≥ 90 performance / ≥ 95 accessibility / ≥ 95 best practices on: login, project home,
  job list, job edit, execution view, nodes, activity. Initial JS ≤ 250 kB gzip; route chunks ≤ 150 kB gzip.
- `axe` (via Playwright) zero serious/critical violations on every journey; keyboard-only completion of the top-10
  journeys; all journeys pass at 375×812 and 1280×800, light and dark.
- Live execution view renders a 100k-line log with virtualized rendering at 60 fps scroll; SSE reconnect with resume.
- Vitest coverage ≥ 80 % on `ui/src/lib` and stores; every journey has a Playwright test.

**Quality**
- Coverage ≥ 80 % lines on library crates (`cargo llvm-cov`); every legacy Spock test for a ported area has a Rust
  counterpart or a written justification in the spec.
- No file > 800 lines, no function > 80 lines (clippy `too_many_lines`), cyclomatic complexity ≤ 25 (as upstream).
- Docs: every crate has a `README.md`; `docs/ARCHITECTURE.md` with the execution and request diagrams; `docs/MIGRATION.md`.

---

## 5. Method — the parity loop (repeat per feature, smallest vertical slice first)

1. **Locate** the legacy behavior: controllers → services → core → plugins, plus tests (`*Spec.groovy`, `*Test.groovy`)
   and docs (`legacy/.claude/docs/file-locations.md` is a good map). Use the `legacy-analyst` subagent; never read
   files > 500 lines whole.
2. **Spec** it in `specs/<area>.md`: endpoints/formats, inputs, outputs, status codes, error codes, edge cases,
   per-API-version differences, security-relevant checks, references to legacy file:line, open questions resolved
   with the parity default. A spec is a contract you can test; vague sentences are not allowed.
3. **Port tests first**: unit/property tests from the legacy Spock specs; golden files captured from the oracle
   (`scripts/oracle.sh capture <name>` records request/response pairs into `tests/golden/`).
4. **Implement** the thinnest slice that makes those tests pass, then the next.
5. **Oracle**: `scripts/parity.sh <SpecClass or filter>` runs the upstream functional tests against `rdx`. Record the
   result (pass counts, run id, commit) in `PARITY.md`.
6. **UI slice**: when the area has user journeys, add the pages/components and their Playwright tests in the same
   phase (§6), screenshots into `docs/ui-review/`.
7. **Review**: before closing an area, spawn `parity-reviewer`; address findings; commit.
8. **Journal**: append to `JOURNAL.md` (what, evidence, next, risks). Update `PLAN.md`.

Order of slices inside an area: happy path for the current API version → error paths → older API versions → XML
responses → UI journey → performance/security hardening.

---

## 6. Phases and exit gates

Each phase ends with: all its oracle specs green, `make check` green, benches recorded, ADRs merged, screenshots
updated, a tag `phase-N` (created via REST, see §7), and a `JOURNAL.md` summary. If a gate cannot be reached because of a blocked item,
close the phase with the item listed in `BLOCKED/` and in `PARITY.md` as `missing`, and continue.

**Phase 0 — Bootstrap (no product code)**
- Repo surgery in one commit: `git rm -r` the root Java tree (keep this kit's files), then
  `git read-tree --prefix=legacy/ -u v6.3.0` (fetch the tag first: `git fetch origin tag v6.3.0`). Add
  `legacy/README-LEGACY.md` stating the pinned tag and that the tree is read-only. The `ui/` directory starts empty
  (the legacy SPA stays under `legacy/` for reference only).
- Root: `Cargo.toml` workspace, `rust-toolchain.toml`, `Makefile`, `deny.toml`, `.github/workflows/{ci,parity,nightly,release}.yml`,
  `scripts/cloud-setup.sh` (kept current: it is the cloud environment's setup script), `scripts/oracle.sh`
  (`docker compose` with `rundeck/rundeck:6.3.0`, `RUNDECK_TOKENS_FILE` with `admintoken`), `scripts/parity.sh`,
  `scripts/bench/`, `ui/` scaffold (§3.8) with lint/test/e2e wiring.
- Generate `PARITY.md` from `UrlMappings.groovy` (all routes), `ServiceNameConstants.java` (36 service types),
  `legacy/plugins/*` (15 built-ins), domain classes (23), file formats (§1.2), journeys (§1.6): one row each, `missing`.
- Write ADR-0001..0009 and the pre-approved deviations of §2 into `docs/COMPAT.md`.
- Prove the oracle: run `legacy/functional-test` `apiTest` against `rundeck/rundeck:6.3.0` (in-session with Docker,
  and in the `parity` workflow); store the baseline pass list in `PARITY.md` (tests failing on legacy are excluded
  from gates and listed).
- Recurring runs: create the cloud scheduled tasks `rdx-autopilot` and `rdx-review` (§7) if they do not exist yet;
  document anything the owner must set (environment `rdx`, model choice) in `JOURNAL.md` under "Owner action required".
- Exit: CI green on the empty workspace; `scripts/parity.sh` can target legacy or `rdx` by env; first UI screenshots
  (login shell) in `docs/ui-review/phase-0/`.

**Phase 1 — Foundations (backend + UI foundation)**
- `rdx-config`, `rdx-db` (schema from legacy Postgres init, three backends, repositories for Project/User/AuthToken/
  StoredEvent), `rdx-authn`, `rdx-authz` (full port + corpus), `rdx-api` skeleton (version negotiation, error
  envelope, content negotiation, `/system/info`, `/tokens`, `/user/*`, `/system/acl/*`, `/authorizations/*`,
  `/feature/*`), `rdx-web` (shell + redirects), `rdx-telemetry`, `rdx-ui-api` (session, CSRF).
- UI foundation: design system (tokens, PrimeVue preset, dark mode), app shell/navigation, login, user profile,
  tokens management, generated API client, i18n pipeline, Storybook, Playwright harness, screenshot pipeline.
- Exit: upstream specs `basic`, `acl`, `authorizations`, `system` (non-execution parts) green; `ldapTest` green with the
  upstream LDAP compose; legacy-initialized Postgres boots `rdx`; UI journeys: login/logout, tokens, profile.

**Phase 2 — Projects, nodes, storage**
- Projects CRUD/config/ACLs/readme/motd/export-import (incl. async), resource model sources + formats + node filter,
  `/resources`, `/sources`, `/nodes/tags`, key storage (`/storage/keys/*`, fs + DB + converters + AES-GCM), config storage.
- UI: project list/home/settings, ACL editor, node browser with filter autocomplete, key storage browser,
  readme/motd.
- Exit: `project`, `nodes`, `resourceModel`, `storage`, `export_import` green; fuzz targets for every parser in scope;
  journeys green.

**Phase 3 — Jobs, workflow, executions, scheduler**
- Job model + codecs, import/export/browse/validateOption/meta/info/forecast/workflow, options incl. secure/file/
  remote, `rdx-workflow`, `rdx-exec` (local, ssh/scp/sftp via russh, script plugins), `rdx-logging`, executions API
  (run/abort/retry/output/state/delete/metrics/running/input files), `rdx-sched` + cluster + takeover, notifications,
  execution-mode timer, job kill handler, SSE event stream.
- UI: job list/groups/search, job editor (workflow graph, steps, options, notifications, schedule with cron helper,
  YAML/JSON view), run dialog, live execution view, activity timeline, adhoc commands.
- Exit: `job`, `execution`, `executor`, `filecopy`, `workflow`, `workflowSteps`, `schedule`, `plugin` green;
  `apiTestNodeExecutorSecureInput` green; performance gates for API/executions/log streaming measured; journeys green.

**Phase 4 — Everything else in the API**
- Webhooks, SCM (git), log file storage plugins + incomplete resume, `/plugin/*`, `/metrics/*`, `/monitoring/*`,
  `/scheduler/*`, incubating endpoints, home summary, repository endpoints (script/WASM plugin install), `jdbcTest`
  (Postgres/MySQL compose).
- UI: webhooks, SCM pages, plugin catalog/config forms, system report, log storage status, scheduler/cluster view.
- Exit: full `apiTest` green except documented `BLOCKED/` items (≥ 98 % of baseline); OpenAPI superset diff green.

**Phase 5 — UI completeness, extension API, polish**
- Close every row of `specs/ui-journeys.md`; command palette; UI extension API (replacing legacy `UI` plugins) with
  one sample; Lighthouse/axe gates on all pages; i18n parity check; `docs/ui-review/phase-5/` full gallery.
- Exit: every journey has a green Playwright test; all §4 frontend gates green.

**Phase 6 — Hardening, performance, packaging, migration**
- Threat model + abuse tests, nightly fuzzing, benches vs legacy with tuning, packaging (§3.10), `rdx migrate`,
  `docs/MIGRATION.md` (from 5.x/6.x on Postgres/MySQL/H2), `docs/PLUGINS.md`, WASM ABI v1 with one sample plugin per
  service type, OIDC (off by default).
- Exit: all §4 gates green; `v0.1.0` release workflow produces binaries, images, deb/rpm, SBOM, signatures.

**Phase 7 — Release**
- Changelog, upgrade guide, `SECURITY.md`, issue templates, final `PARITY.md`, then write the `DONE` file at the repo
  root and pause the scheduled task (see §7).

---

## 7. Autonomy protocol (cloud-only)

**Where things run**
- **Work sessions — Mode A (default): the cloud scheduled task `rdx-autopilot`** (cron `CRON_TZ=Europe/Zurich 37 1,4,7,10,13,16,19 * * *`,
  repository `nicolasdeker/rundeck`, environment `rdx` whose setup script is `if [ -d rundeck ]; then bash rundeck/scripts/cloud-setup.sh; fi` (it runs from the parent of the checkout) and whose
  variables include `BASH_DEFAULT_TIMEOUT_MS=600000`, `BASH_MAX_TIMEOUT_MS=1800000`, automatic approval, Sonnet-class
  model, effort high). Each firing is a fresh VM with the repo cloned at `main`; the first thing it does is
  `bash scripts/family-window.sh`, which blocks the run inside the family's homework windows, inside the 5-hour buffer
  before them, and beyond `RDX_MAX_RUNS_PER_DAY` runs per day (default 2; the owner tunes it from the usage page).
  Allowed slots in practice: weeknights 01:37 / 04:37 / 07:37, weekend 01:37 and 19:37.
- **Review session — the cloud scheduled task `rdx-review`** (cron `CRON_TZ=Europe/Zurich 37 22 * * 0`, Sunday 22:37,
  strongest model) running `scripts/prompts/review.md`: audits the week's evidence, runs `parity-reviewer`, attacks the
  oldest blocked item, re-plans.
- **Mode B (opt-in, API-billed)**: the `autopilot` GitHub Actions workflow (`.github/workflows/autopilot.yml`), inert until
  the owner sets `AUTOPILOT_ENABLED=true` and the secrets. Used only if the owner decides to buy throughput with API
  credits instead of subscription usage; then the scheduled tasks are paused so the two never overlap.
- **Ad-hoc sessions**: the owner can open a cloud session from the Claude app (**Code** tab) at any time to steer or run
  something urgent; the same rules and the same lock apply (an ad-hoc session may set `RDX_FORCE=1` for the calendar
  guard — the owner is choosing to spend usage).
- **Heavy verification**: GitHub Actions on the public fork (free standard runners, Docker, services). `parity.yml`
  runs the full oracle suite on every push to `main` and uploads `parity-report.json`; `nightly.yml` runs fuzzing,
  benches, Lighthouse; `ci.yml` is the fast gate (fmt, clippy, tests, deny, audit, ui lint/test). Pushes from cloud
  sessions trigger these workflows normally.
- **Owner interface**: GitHub app (commits, Actions, issues) and Claude app (task run history, ad-hoc sessions).
  Nothing requires a terminal.

**State lives in files, not in your context.** A fresh session must resume in under five minutes.
- `PLAN.md`: phases as checklists; exactly one item marked `← CURRENT`. Granularity: 1–3 hours of work.
- `JOURNAL.md`: append-only. Entry template: `## <ISO date> run <id> — phase <N> / <item>` then `Done:`, `Evidence:`
  (commands + pass counts + commit SHAs + CI run URLs), `Next:`, `Risks/Decisions:`. Never rewrite old entries.
- `PARITY.md`: one row per contract item: `area | item | status (missing|partial|done|deviated|blocked) | oracle spec | last run (date, pass/total, commit, CI url)`.
- `DECISIONS-PENDING.md` + a GitHub issue labeled `decision` for each entry: the question, the default you took, why.
  The owner answers in the issue from his phone; at session start read open `decision` issues
  (`gh api 'repos/nicolasdeker/rundeck/issues?labels=decision&state=open'` — `gh issue`/`gh pr` use GraphQL and are
  rejected by the cloud GitHub proxy; always use `gh api` REST calls), apply answered ones (close the issue with a
  comment citing the commit), never block on unanswered ones.
- `BLOCKED/<id>.md` + a GitHub issue labeled `blocked` after three failed attempts on one item: symptoms, hypotheses
  tested, what would unblock, estimated impact.
- `docs/ui-review/<phase>/`: screenshots for the owner (see §3.8).

**Session ritual**
1. **Lock** (one run at a time) — the cloud GitHub proxy only accepts pushes to branches and refuses deletions, so the
   lock is the branch `autopilot-lock` whose tip commit message carries the state:
   `git fetch origin autopilot-lock` → if the tip's message starts with `lock` and its committer date is younger than
   3 h, log `locked, skipping` and exit without changes. Otherwise take it:
   `sha=$(git commit-tree HEAD^{tree} -m "lock $(date -u +%FT%TZ) <run id>") && git push -f origin $sha:refs/heads/autopilot-lock`.
   Release at the end with a commit whose message is `unlocked <ISO time>` force-pushed the same way. CI workflows
   ignore this branch (`on.push.branches: [main]`). Ad-hoc sessions follow the same protocol.
2. Read `CLAUDE.md`, `MISSION.md`, `tail -n 80 JOURNAL.md`, `grep -n "CURRENT" PLAN.md`, `git log --oneline -8`,
   open `decision`/`blocked` issues (REST, see above), latest CI results (`gh run list -L 5`,
   `gh run view <id> --log-failed` on red), latest `parity-report.json` (`gh run download -n parity-report`) →
   update `PARITY.md` if it carries new evidence.
3. `make check`. If red and not caused by you: fixing it is the current item.
4. Work the current item with the §5 loop. Commit at every green step (conventional messages), **push to `main`**
   after each commit (`git push origin HEAD:main`; never force). The scheduled task's default `claude/` branch
   behavior is overridden by this instruction.
5. Stop after ~60 minutes of work or when the item is done — always within the guard's "max run" and before its
   "must finish by" time: `JOURNAL.md` entry, `PLAN.md` update, commit, push, release the lock. The next run continues.
6. When a phase gate is met: create the tag `phase-N` through the REST API (git pushes of tags are refused by the proxy):
   `gh api repos/nicolasdeker/rundeck/git/refs -f ref=refs/tags/phase-N -f sha=$(git rev-parse HEAD)`; journal
   summary with screenshot links; move `← CURRENT` to the next phase.
7. If `MISSION.md` §9 is satisfied: write `DONE`, commit, push, pause the scheduled task (`/schedule` or the
   scheduling tool) and open a GitHub issue `Release v0.1.0 ready` for the owner.

**Resource discipline (4 vCPU / 16 GB / 30 GB, fresh VM every run)**
- Build fast: `cargo check` first, tests per crate (`cargo nextest run -p <crate>`), `CARGO_INCREMENTAL=0` in CI only,
  `profile.dev` with `opt-level=1` for dependencies, lean dependency tree (every new crate justified in `Cargo.toml`).
- Keep `scripts/cloud-setup.sh` under five minutes so the environment snapshot caches toolchains, `cargo fetch`,
  pre-pulled `rundeck/rundeck:6.3.0` and `postgres:16` images; it must stay idempotent and tolerant (`|| true` on
  optional parts). When it changes, note it in `JOURNAL.md` so the owner can re-save the environment (the snapshot is
  taken when the environment is first used).
- Run the full Selenium/Playwright suites in CI, not in-session; in-session use filtered runs.
- Disk: `cargo clean -p` old artifacts if `df` shows < 5 GB; never commit `target/`, `node_modules/`, oracle data.

**Budget**: runs draw on the family's subscription, so the calendar guard and the daily cap are the budget — never work
around them. End every run within the "max run" minutes the guard printed (wrap-up included) and before its "must
finish by" time. Do not spawn parallel sessions; one lock, one run. Prefer `legacy-analyst` (sonnet) for exploration;
use subagents sparingly. Never run the same failing command more than twice in a row. Expensive work (engine design,
phase reviews, unblocking) belongs to the Sunday review session.

---

## 8. Hard prohibitions

- Never edit `legacy/` (except `legacy/README-LEGACY.md`); never edit the upstream functional tests to make them pass.
  A legacy-specific or wrong test goes in `tests/parity-skips.toml` with a justification and stays `deviated`/`blocked`
  in `PARITY.md`.
- Never mark an item done without an oracle run (API) or a Playwright run (UI) recorded in `PARITY.md`.
- Never return success for unimplemented behavior. Unimplemented endpoints return `501` with the legacy error envelope
  and `errorCode: "api.error.not-implemented"`; they stay `missing` in `PARITY.md`.
- Never weaken a security default to pass a test; add the compat switch, enable it only in the oracle fixture.
- Never introduce a dependency (Cargo or pnpm) without a one-line justification and clean `cargo deny` / `pnpm audit`.
- Never use `unsafe`, `unwrap()`/`expect()` in non-test code, `std::process::Command` with a shell string, YAML tag
  resolution, XML external entities, `v-html` without DOMPurify, or `tokio::spawn` without a cancellation path.
- Never force-push `main`, rewrite history, delete branches/tags, or push to any branch other than `main` and the
  `autopilot-lock` lock branch. Tags only through the REST API at phase gates.
- Never run a second session while the lock is held. Never ask the owner anything; decide, record, continue.

---

## 9. Definition of done (writes `DONE`)

- All phase gates closed; `PARITY.md` shows ≥ 98 % `done` across API/formats/behavior/journeys rows, each with an oracle
  or Playwright run dated within the last week on the final commit; remaining rows are `blocked`/`deviated` with ADR
  or `BLOCKED/` references.
- All §4 gates green on the final commit, benches recorded in `docs/BENCHMARKS.md` with the legacy comparison.
- `v0.1.0` release artifacts produced by CI and smoke-tested: a legacy 6.3.0 Postgres database + project exports
  migrated, jobs run, logs readable, ACLs enforced, script plugins executed, the new UI usable on a phone.

---

## Appendix A — Legacy map (paths relative to `legacy/`, tag v6.3.0)

- API versions: `rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/ApiVersions.groovy`
- Routes: `rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy` (+ `grails-*/grails-app/controllers/**/UrlMappings.groovy`)
- Controllers: `rundeckapp/grails-app/controllers/rundeck/controllers/*.groovy` (`ApiController`, `ExecutionController`,
  `ScheduledExecutionController`, `ProjectController`, `FrameworkController`, `StorageController`, `ScmController`, `PluginController`, ...)
- Services: `rundeckapp/grails-app/services/rundeck/services/` (66)
- Domain + schema: `rundeckapp/grails-app/domain/rundeck/*.groovy`, `webhooks/Webhook.groovy`; `rundeckapp/grails-app/migrations/`
- Core engine: `core/src/main/java/com/dtolabs/rundeck/core/{execution,dispatcher,jobs,nodes,resources,rules,schedule,storage,logging,authorization,authentication,cluster,plugins,utils}`
- Plugin SPI: `core/src/main/java/com/dtolabs/rundeck/plugins/` (36 service types in `ServiceNameConstants.java`)
- Built-in plugins: `plugins/*` (15)
- AuthZ: `rundeck-authz/{rundeck-authz-api,rundeck-authz-core,rundeck-authz-yaml}`; key storage: `rundeck-storage/*`; crypto: `encryption-core/`
- Job codecs: `rundeckapp/grails-app/utils/rundeck/codecs/{JobsXMLCodec,JobsYAMLCodec}.groovy`
- Node filter: `core/src/main/java/com/dtolabs/rundeck/core/utils/NodeSet.java`, `core/.../common/NodeFilter.java`
- Log format: `core/src/main/java/com/dtolabs/rundeck/core/logging/internal/RundeckLogFormat.java`
- JAAS modules: `rundeckapp/src/main/java/**/jaas/` (`PropertyFileLoginModule`, `JettyCachingLdapLoginModule`,
  `JettyCombinedLdapLoginModule`, `JettyPamLoginModule`, ...)
- Legacy frontend (reference only): `rundeckapp/grails-spa/packages/ui-trellis/`, `rundeckapp/grails-app/views/**/*.gsp`,
  `rundeckapp/grails-app/i18n/`
- Oracle: `functional-test/` (tasks `apiTest`, `seleniumCoreTest`, `ldapTest`, `jdbcTest`, `pluginBlocklistTest`,
  `apiTestNodeExecutorSecureInput`; env `TEST_RUNDECK_URL`, `TEST_RUNDECK_TOKEN`, `RUNDECK_TEST_USER/PASS`;
  compose files under `functional-test/src/test/resources/docker/`)
- Packaging: `packaging/`, `docker/official/` (env variable names, remco templates)
- Upstream's own agent knowledge base: `.claude/docs/*.md`, `.claude/rules/*.md` — read `file-locations.md`,
  `testing-guidelines.md`, `api-guidelines.md`.

## Appendix B — Inventory (measured on tag v6.3.0)

- Backend: ~370k lines Groovy + ~147k lines Java. Legacy frontend: ~46k TS, ~49k Vue, ~81k JS; 260 GSP files.
- API: versions 14–60, 120 route patterns in the main app + plugin routes; 27 controllers; 66 services; 23 domain classes.
- Plugin service types: 36. Built-in plugin modules: 15. Functional specs: 64 API, 57 Selenium.
- Legacy build (only if ever needed): Java 17 + Node, `./gradlew build -x check` ≈ 4–8 min on a laptop; prefer the
  published `rundeck/rundeck:6.3.0` image as oracle.
