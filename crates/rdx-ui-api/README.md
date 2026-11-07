# `rdx-ui-api`

UI-only API (`/ui-api/v1`): SSE streams, aggregated views, session/CSRF — not a compatibility contract

The UI-only API consumed by the new frontend (MISSION §3.8): SSE streams of execution events, aggregated
dashboard views, session and CSRF endpoints. Versioned, documented as non-contract, and authorized through
`rdx-authz` like every other handler.

## Legacy references (ported in later phases)

- No 1:1 port. Informed by `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/MenuController.groovy` (dashboard aggregates), `ExecutionController.groovy` (`tailExecutionOutput`) and the legacy SPA's service calls in `legacy/rundeckapp/grails-spa/packages/ui-trellis/src/library/services/`

## Parity specs this crate targets

- `specs/ui-api.md`, `specs/ui-journeys.md`
- Playwright journeys (`ui/e2e`), not the upstream oracle

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
