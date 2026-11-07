# `rdx-api`

axum router: API v14–60, auth middleware, error envelope, `OpenAPI` (utoipa), XML/JSON/YAML negotiation

The compatibility REST API (MISSION §1.1): every route of the legacy `UrlMappings.groovy` under
`/api/{version}`, API version checks (14–60), the legacy error envelope, XML/JSON/YAML negotiation, pagination
headers, auth middleware and the generated `OpenAPI` document.

## Legacy references (ported in later phases)

- `legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/ApiVersions.groovy`
- `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy`
- `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/*.groovy`
- `legacy/rundeckapp/grails-app/controllers/rundeck/interceptors/` (`ApiVersionInterceptor`, `AuthorizationInterceptor`)
- `legacy/rundeckapp/grails-app/services/rundeck/services/ApiService.groovy` (error envelope, rendering)

## Parity specs this crate targets

- `specs/api-*.md`
- upstream `api/**` (every spec; first `api/basic/BasicSpec`, `api/basic/BadVersionSpec`, `api/basic/UnauthorizedSpec`)

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
