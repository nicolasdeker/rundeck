# ADR-0003 — Plugins: script plugins unchanged, built-ins native, WASM ABI, no in-process jars

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

Legacy loads two plugin kinds from `libext/`: Java jars
(`legacy/core/src/main/java/com/dtolabs/rundeck/core/plugins/JarPluginProviderLoader.java`) and script plugins —
a zip with a `plugin.yaml` descriptor and scripts
(`legacy/core/src/main/java/com/dtolabs/rundeck/core/plugins/ScriptPluginProviderLoader.java`,
`legacy/plugins/script-plugin`). Providers register against **35 service types**
(`legacy/core/src/main/java/com/dtolabs/rundeck/plugins/ServiceNameConstants.java:35-76`, from
`RemoteScriptNodeStep` to `PluginGroup`), including `UI` (`:63`, JavaScript injected into GSP pages through
`legacy/core/src/main/java/com/dtolabs/rundeck/plugins/rundeck/UIPlugin.java`) and `TourLoader` (`:66`). Fifteen
built-in modules ship under `legacy/plugins/`: `aes-gcm-encryption-plugin`, `audit-logging-plugin`,
`copyfile-plugin`, `flow-control-plugin`, `git-plugin`, `job-state-plugin`, `jsch-plugin`, `localexec-plugin`,
`object-store-plugin`, `orchestrator-plugin`, `script-node-step-plugin`, `script-plugin`, `source-refresh-plugin`,
`stub-plugin`, `upvar-plugin`. Loading jars requires a JVM (MISSION §1.5, reason c). MISSION §3.5 fixes four tiers.

## Decision

1. **Tier 1 — script plugins run unchanged.** Same zip layout, same `plugin.yaml` schema (metadata, `providers`,
   `service`, `plugin-type: script`, `script-file`, `script-args`, `script-interpreter`, `interpreter-args-quoted`,
   `config` property list, `use-original-extension`), same provider services the legacy loader accepts (pinned from
   `ScriptPluginProviderLoader.java` in `specs/plugins.md`), same environment/argument contract (`RD_*` variables,
   `RD_CONFIG_*`, data-context expansion), same output parsing (`^RUNDECK:DATA:` key/value lines and node-step
   result codes). Test: the upstream script-plugin fixtures and the `plugin` API spec pass against `rdx`; a corpus of
   existing community script plugins is executed unchanged in CI.
2. **Tier 2 — built-ins are native Rust providers with the legacy provider names**, because provider names are
   stored in job definitions and `project.properties` (`service.<Service>.default.provider=...`). In particular the
   SSH executor and SCP/SFTP copier keep the names `jsch-ssh`/`jsch-scp` and their configuration keys while being
   implemented on `russh`; `localexec`, `script`, `stub`, `copyfile`, `job-state`, `source-refresh`, `flow-control`,
   `aes-gcm` converter, `object-store` (S3-compatible), `orchestrator` providers, `git-export`/`git-import`,
   `audit-logging`, `upvar` likewise. Property descriptors are byte-equal to legacy where the oracle exposes them
   (`/api/*/plugin/detail`).
3. **Tier 3 — WASM Component Model ABI** (Phase 6, additive, off by default: `rdx.plugins.wasm.enabled=false`):
   `wit/rdx/*.wit` defines one world per service type, mirroring the 35 legacy services; host = `wasmtime` with
   WASI preview 2; capabilities are scoped per plugin by its descriptor (`capabilities: [fs:read:<path>, net:<host>,
   env:<name>]`) and default to none; one sample plugin per service type ships with the ABI (MISSION §6 Phase 6).
4. **Tier 4 — JVM sidecar over gRPC for jar plugins: design note only**, not built in v1 (MISSION §3.5).
5. **Jars are never loaded in-process.** At boot `rdx` scans `libext/*.jar`, reads the `Rundeck-Plugin-*` manifest
   attributes, logs one warning per jar with its name and the replacement status from `docs/PLUGINS.md`, and
   `rdx doctor` prints the same table. **C-009** (reason c). The plugin blocklist file contract stays for script
   plugins; jar-only entries are reported, not enforced.
6. **`UI` plugins are not supported** (JavaScript injected into GSP pages cannot exist without GSP). The new UI gets
   its own extension API in Phase 5 with its own ADR. **C-010** (reason c). `TourLoader`, `PluginGroup` and
   `PasswordUtilityEncrypter` have built-in implementations only in v1.
7. **Descriptors and discovery endpoints keep the legacy shapes**: `GET /api/*/plugin/list` and
   `GET /api/*/plugin/detail/{service}/{provider}` (service names as in `ServiceNameConstants`, property fields
   `name`, `title`, `desc`, `type`, `required`, `default`, `scope`, `renderingOptions`, `allowed`/`values`,
   `validator` outcome), plugin i18n via `resources/i18n/messages*.properties` inside the plugin zip, and the three
   configuration scopes (framework `framework.plugin.<Service>.<provider>.<prop>`, project
   `project.plugin.<Service>.<provider>.<prop>`, instance config in the job/step). Repository endpoints
   (`legacy/grails-repository`) install script and WASM plugins only.
8. Provider resolution is identical: default provider keys (`service.NodeExecutor.default.provider`,
   `service.FileCopier.default.provider`, node attributes `node-executor`/`file-copier`), fallbacks and error
   messages as the oracle shows them.

## Consequences

Positive: every script plugin in the wild keeps working; the built-ins become memory-safe native code; the WASM ABI
gives a sandboxed path for new plugins with explicit capabilities; no class-loader, no JVM.

Negative: community **jar** plugins stop working in-process (the largest compatibility cost of the mission); plugin
authors who want sandboxing must target WIT. `UI` plugins disappear until Phase 5.

Risks: subtle differences in script-plugin argument quoting and output parsing — mitigated by porting the legacy
unit tests of `ScriptPluginProviderLoader`/`ScriptPluginNodeStepExecutor` first and running the upstream `plugin`
API spec; descriptor drift — mitigated by golden files from the oracle for every built-in's `/plugin/detail`.

## Compatibility impact

Untouched: Tier 1 contract, provider names, descriptor shapes, `/plugin/list`, `/plugin/detail`, config scopes,
blocklist file for script plugins, repository endpoints for script plugins. Deviations: **C-009** jar plugins not
loaded (c), **C-010** `UI` plugins unsupported (c). Additive: WASM ABI (off by default), UI extension API (Phase 5).

## Alternatives considered

- Embedding a JVM (JNI/GraalVM polyglot) to load jars — rejected: reintroduces the JVM footprint and CVE surface;
  violates "no JVM" (MISSION §3.1).
- Running jar plugins through a `java -jar` wrapper per invocation — rejected: the plugin SPI is in-process Java
  interfaces with callbacks, not a CLI contract.
- Lua/JavaScript embedded scripting as the new plugin model — rejected: a third model with no legacy ABI; WIT
  mirrors the legacy service types instead.
- Making WASM the only new tier and dropping Tier 4 entirely — kept Tier 4 as a design note because popular jar
  plugins (`docs/PLUGINS.md`) may justify a sidecar later.

## Migration / rollout

Script plugins: nothing. Built-ins: nothing (same names, same keys). Jar plugins: `rdx doctor` lists them with
their status from `docs/PLUGINS.md` (ported natively, WASM sample available, no replacement); the operator removes or
replaces them. `UI` plugins: wait for the Phase 5 extension API.

## References

- MISSION.md §1.2 (script plugins), §1.5, §3.5, §6 (Phase 4 repository endpoints, Phase 6 WASM ABI).
- `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/ServiceNameConstants.java:35-76` (35 constants; `UI` :63,
  `TourLoader` :66, `PluginGroup` :76)
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/plugins/JarPluginProviderLoader.java`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/plugins/ScriptPluginProviderLoader.java`
- `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/rundeck/UIPlugin.java`
- `legacy/plugins/` (15 modules, listed in Context); `legacy/grails-repository`.
- Related: ADR-0004 (UI extension API, Phase 5), `docs/PLUGINS.md` (Phase 6), `specs/plugins.md`.
