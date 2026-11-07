# `rdx`

binary: CLI (`serve`, `migrate`, `check-config`, `export`, `import`, `keys`, `acl check`, `doctor`)

The single binary of the project (MISSION §3.1): one process, no JVM, no external scheduler or cache. It wires the
library crates together (`rdx-config` → `rdx-db` → services → `rdx-api`/`rdx-ui-api`/`rdx-web`) and embeds the
`ui/` build at release time. Error handling in this crate uses `anyhow`; libraries use `thiserror` (CLAUDE.md).

## What this build does

Phase 0 handles exactly one thing honestly:

- `rdx --version` / `rdx -V` prints `rdx <version>` on stdout and exits 0.
- Any other invocation prints a short usage on stderr saying the CLI arrives in Phase 1 and exits 2.

No argument parser yet (no dependency without a need). `tests/cli.rs` runs the built binary and asserts the exact
output and exit codes.

## Legacy references (ported in later phases)

- `legacy/rundeckapp/grails-app/init/` (application boot), `legacy/rundeckapp/grails-app/conf/application.groovy`
- `legacy/packaging/` and `legacy/docker/official/` (file locations, environment variable names — ADR-0009)
- `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy` (what `serve` must expose)

## Parity specs this crate targets

- `specs/cli.md` (Phase 1)
- end-to-end: every upstream `api/**` spec through `scripts/parity.sh --target rdx`

## Status

Phase 0: scaffold; `--version` only. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction
is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
