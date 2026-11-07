# `rdx-plugin`

plugin registry, descriptors/properties, script plugin host, WASM host (wasmtime), built-in providers

Plugins as described in MISSION §3.5 / ADR-0003: the provider registry keyed by the legacy service types,
plugin descriptors and property schemas, the script plugin host (zip + `plugin.yaml`, same env/argument
contract), the WASM Component Model host and the natively ported built-in providers.

## Legacy references (ported in later phases)

- `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/` (SPI; `ServiceNameConstants.java` lists the service types)
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/plugins/` (loader, descriptors, script plugin host)
- `legacy/rundeckapp/grails-app/services/rundeck/services/PluginService.groovy`
- `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/PluginController.groovy`
- `legacy/plugins/*` (15 built-in plugins)

## Parity specs this crate targets

- `specs/plugins.md`
- upstream `api/plugin/PluginSpec`, `integration/BlocklistSpec` (gradle task `pluginBlocklistTest`)

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
