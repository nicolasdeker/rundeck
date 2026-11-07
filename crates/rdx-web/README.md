# `rdx-web`

embedded SPA (rust-embed), security headers, legacy deep-link redirects

Serves the embedded SPA with hashed immutable caching, sets the security headers, and redirects the legacy
deep links (MISSION §1.6) to the new routes.

## Legacy references (ported in later phases)

- `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy` (non-API routes = the deep links to keep)
- `legacy/rundeckapp/grails-app/views/` (which pages exist; reference only, nothing is copied)
- `legacy/rundeckapp/grails-app/conf/application.groovy` (security header keys)

## Parity specs this crate targets

- `specs/web.md`, `specs/ui-journeys.md` (deep links)
- Playwright journeys (`ui/e2e`)

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
