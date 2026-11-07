# `rdx-authn`

realm.properties, LDAP (ldap3), PAM, preauth headers, sessions, tokens, (later) OIDC

Authentication as described in MISSION §3.7 / ADR-0007: `realm.properties` with hot reload, LDAP/LDAPS with
the legacy JAAS configuration keys, PAM, pre-authenticated headers, API tokens hashed at rest, server-side
sessions, CSRF double-submit for the SPA and rate limiting on the login/token endpoints.

## Legacy references (ported in later phases)

- `legacy/rundeckapp/src/main/java/org/rundeck/jaas/PropertyFileLoginModule.java`
- `legacy/rundeckapp/src/main/groovy/org/rundeck/jaas/jetty/` (`ReloadablePropertyFileLoginModule`, `JettyRolePropertyFileLoginModule`, `JettyPamLoginModule`)
- `legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/jetty/jaas/` (`JettyCachingLdapLoginModule`, `JettyCombinedLdapLoginModule`, `JNDILoginModule`)
- `legacy/rundeckapp/grails-app/services/rundeck/services/ApiService.groovy` (token handling)
- `legacy/rundeckapp/grails-app/domain/rundeck/AuthToken.groovy`, `User.groovy`
- `legacy/rundeckapp/grails-app/services/rundeck/services/UserService.groovy`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/authentication/`

## Parity specs this crate targets

- `specs/authn.md`
- upstream `api/basic/UnauthorizedSpec`, `api/ldap/LdapRolesApiSpec` (gradle task `ldapTest`), `api/jdbc/JdbcRolesApiSpec`; `selenium/profile/TokenSpec`, `selenium/auth/BasicLoginSpec` inform the journeys

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
