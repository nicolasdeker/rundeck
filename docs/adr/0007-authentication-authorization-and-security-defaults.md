# ADR-0007 — Authentication, authorization and security defaults

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

Legacy authentication is JAAS. The property-file module `legacy/rundeckapp/src/main/java/org/rundeck/jaas/PropertyFileLoginModule.java`
(format `username: password [,role ...]`, `:42-46`) checks credentials with
`legacy/core/src/main/java/org/rundeck/jaas/PasswordCredential.java`, which accepts plain text, `MD5:` (base64 or
hex), `CRYPT:`, `BCRYPT:` and Jetty `OBF:` (`:34-37`, prefix parsing `:67-74`) and compares with `String.equals`
(`:100,108,112,121,139` — not constant-time). LDAP and PAM modules live under
`legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/jetty/jaas/` (`JettyCachingLdapLoginModule.java`, 1452 lines,
options `bindDn`, `userBaseDn`, `userObjectClass`, `roleBaseDn`, `roleMemberAttribute`, `roleNameAttribute`,
`supplementalRoles`, `nestedGroups`, `timeoutRead`, `cacheDurationMillis` at `:165-285`;
`JettyCombinedLdapLoginModule.java`) and `legacy/rundeckapp/src/main/groovy/org/rundeck/jaas/jetty/` (`JettyPamLoginModule.java`,
`ReloadablePropertyFileLoginModule.java`, ...), wired by `jaas-loginmodule.conf`
(`legacy/docker/official/remco/templates/jaas-loginmodule.conf:85-106`). Form login is `POST /j_security_check`
(`legacy/rundeckapp/grails-app/conf/application.groovy:175-177`); pre-authenticated mode uses
`rundeck.security.authorization.preauthenticated.*` (`legacy/rundeckapp/grails-app/conf/application.yml:240-245`).
API tokens: new tokens are stored as SHA-256 (`legacy/rundeckapp/grails-app/domain/rundeck/AuthToken.groovy:36`
default `AuthTokenMode.SECURED`, `:81-95` `encodeAsSHA256()`), but `LEGACY`/null rows hold the clear value, are
matched by plaintext equality (`legacy/rundeckapp/src/main/groovy/org/rundeck/app/data/providers/GormTokenDataProvider.groovy:194-215`)
and are returned in clear by the API when unmasked (`legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/tokens/Token.groovy:80-83`);
webhook tokens were already migrated to `SECURED` (`WebhookTokenSecureMigrationService.groovy:55-67`). Session
cookies: `http-only: true`, `same-site: "Lax"`, `secure` auto-enabled only when `grails.serverURL` is `https` and
not behind forwarded headers (`application.yml:397-405`; `legacy/rundeckapp/grails-app/init/rundeckapp/init/servlet/JettyServletContainerCustomizer.groovy:86-98`).
Security headers: enabled by default (`application.yml:247-258`) with CSP `script-src 'self' … 'unsafe-inline'
'unsafe-eval'`, `style-src 'self' 'unsafe-inline'`, `img-src * data:`, plus `X-Content-Type-Options: nosniff`,
`X-XSS-Protection: 0`, `X-Frame-Options: deny`, `Cache-Control: no-cache, no-store, max-age=0, must-revalidate`,
`Strict-Transport-Security: max-age=31536000; includeSubDomains`, `Permissions-Policy`, `Referrer-Policy`
(`legacy/grails-securityheaders/src/main/groovy/grails/securityheaders/SecurityheadersGrailsPlugin.groovy:50-102`,
`StrictTransportSecurityHeaderProvider.groovy:11`). CSRF: Spring's filter is off (`application.groovy:171`), legacy
uses HMAC request tokens for GSP forms (`application.yml:246`) and none on `/api/**` (`application.groovy:166`) while
session cookies may call the API (`application.yml:233-234`). Default credentials `admin:admin` ship in
`legacy/packaging/lib/common/etc/rundeck/realm.properties:25` and `legacy/rundeckapp/src/main/resources/WEB-INF/jaaslogin.properties:1`.
Files are created with the process umask `002` (`legacy/packaging/lib/common/etc/rundeck/profile:98`,
`legacy/docker/official/etc/profile:25`), i.e. `0664`. No login rate limiting exists (no rate-limit code under
`rundeckapp/grails-app` or `src/main`). Authorization is `rundeck-authz-core` evaluating `*.aclpolicy` YAML.

## Decision

### Authentication
1. **`realm.properties`**: same file, same line format, hot reload (file watch + mtime fallback). Every legacy
   credential format is accepted and verified identically: plain, `MD5:` (hex and base64), `CRYPT:`, `BCRYPT:`, `OBF:`.
   New format `ARGON2:` (PHC string `$argon2id$...`) is accepted in addition; any password **`rdx` itself writes**
   (`rdx realm hash`, future user management) is argon2id (m=64 MiB, t=3, p=1). `rdx doctor` warns on plain/`MD5:`/
   `CRYPT:`/`OBF:` entries. **C-002** (reason a). Legacy cannot read `ARGON2:` entries (documented).
2. **`jaas-loginmodule.conf` is parsed** (JAAS grammar: app name, module class, flag, options) and each class is
   mapped to a native provider: `PropertyFileLoginModule`/`ReloadablePropertyFileLoginModule`/
   `JettyAuthPropertyFileLoginModule`+`JettyRolePropertyFileLoginModule` → realm provider; `JettyCachingLdapLoginModule`
   and `JettyCombinedLdapLoginModule` → LDAP/LDAPS (`ldap3`) with the same option names and defaults
   (`userObjectClass=inetOrgPerson`, `roleMemberAttribute=uniqueMember`, `roleNameAttribute=roleName`,
   `supplementalRoles`, `nestedGroups`, `timeoutRead`, cache duration); `JettyPamLoginModule` → PAM (`pam` crate);
   flags `required`/`requisite`/`sufficient`/`optional` keep JAAS stacking semantics. Any other class is an error at
   `check-config` naming the class (**C-019**, reason c).
3. **Form login** stays `POST /j_security_check` (`j_username`, `j_password`), `/user/login`, `/user/logout`,
   `/user/loggedout`, `/user/error`, `/menu/home`. **Pre-authenticated mode** keeps the keys
   `rundeck.security.authorization.preauthenticated.{enabled,userNameHeader,userRolesHeader,attributeName,delimiter,
   redirectLogout,redirectUrl}` and the `RUNDECK_PREAUTH_*` variables (`README.md:208-214`); headers are honored
   only from trusted proxies (`server.useForwardHeaders`, ADR-0002).
4. **API tokens**: header `X-Rundeck-Auth-Token` and `authtoken` parameter; `/api/*/tokens` lifecycle, roles subset
   enforcement, expiry, `creator`, `rundeck.api.tokens.duration.max` as legacy. At rest: **SHA-256 in the legacy
   `auth_token.token` column with `token_mode = SECURED`** (same as legacy for new tokens, so legacy and `rdx` can
   alternate on one database). `rdx` never creates `LEGACY` rows; on boot it re-encodes existing `LEGACY`/null rows in
   place (the stored value is the clear token), exactly as legacy did for webhook tokens; the clear value is returned
   only in the creation response. Static tokens from `rundeck.tokens.file` (`RUNDECK_TOKENS_FILE`,
   `legacy/docker/official/remco/templates/framework.properties:28-29`) keep working. **C-001** (reason a); switch
   `rdx.compat.plaintext-tokens=true` skips the re-encoding.
5. **Sessions** are server-side rows (`rdx_session`, ADR-0005) so a cluster shares them and a restart keeps users
   logged in; idle timeout from `server.servlet.session.timeout` (docker default 3600 s,
   `legacy/docker/official/remco/templates/rundeck-config.properties:16`); new absolute lifetime
   `rdx.session.absolute_timeout` (default 24 h). Cookie name `JSESSIONID` is kept (sticky-session proxies key on
   it); flags `HttpOnly`, `SameSite=Lax` always, `Secure` whenever `grails.serverURL` is `https` **or** the request
   arrived over TLS or with a trusted `X-Forwarded-Proto: https`; `rdx.compat.insecure-session-cookie=true` forces
   `Secure` off (the legacy `server.servlet.session.cookie.secure=false` is honored the same way). **C-004**,
   **C-020** (reason a).
6. **CSRF**: `GET /ui-api/v1/session` returns a per-session token; cookie-authenticated requests to `/api/*` and
   `/ui-api/*` with a method other than `GET`/`HEAD`/`OPTIONS` must carry it in `X-RDX-CSRF` or arrive with
   `Sec-Fetch-Site: same-origin`/`none`; otherwise `403` with the legacy error envelope. Token-authenticated requests
   are exempt (as legacy). `rundeck.security.apiCookieAccess.enabled` keeps its meaning. **C-016** (reason a); switch
   `rdx.compat.cookie-api-no-csrf=true`.
7. **Rate limiting** on `/j_security_check` and `/api/*/tokens` creation: token bucket per client IP and per
   username (defaults 10/min burst 20); exceeded → `429` with `Retry-After`. **C-017** (reason a); switch
   `rdx.compat.unlimited-login-attempts=true`.
8. **Constant-time comparisons** (`subtle::ConstantTimeEq`) for every secret: passwords and hashes, token hashes,
   CSRF tokens, webhook secrets, pre-shared keys. DB lookups go by hash, never by clear value. **C-005** (reason a).
9. **No default credentials in packaged artifacts** (deb/rpm/container/Helm/binary). A first boot with no
   authenticatable user logs how to create one (`rdx realm hash`). `RDX_INSECURE_DEFAULT_ADMIN=1` (environment only,
   never a config key) creates `admin:admin` with roles `user,admin,architect,deploy,build` in memory for that run
   and prints a red warning on every start; the oracle fixture (`scripts/oracle.sh`, `parity.yml`) sets it so the
   upstream tests stay runnable. **C-007** (reason a).
10. **Audit events** for every authentication decision (success, failure, token use, logout, rate limit) go to the
    audit log (ADR-0008) with user, IP, method, outcome — never the secret.

### Security defaults
11. **Headers**: legacy's set is the floor and the legacy keys `rundeck.security.httpHeaders.*` still override.
    Defaults: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 0`,
    `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` as legacy,
    `Strict-Transport-Security: max-age=31536000; includeSubDomains` on TLS responses, `Cache-Control: no-store` on
    HTML and API responses, and a **strict CSP**: `default-src 'none'; script-src 'self' 'nonce-…'; style-src 'self';
    img-src 'self' data:; font-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; object-src
    'none'; base-uri 'self'` — no `unsafe-inline`/`unsafe-eval`, no analytics hosts. **C-003** (reason a); switch
    `rdx.compat.legacy-csp=true` serves the legacy policy.
12. **File modes**: files `rdx` creates (execution logs, `.rdlog`, server/audit logs, key storage, SQLite, exports)
    are `0600`, directories `0700`, independent of umask; `rdx.files.mode`/`rdx.files.dir_mode` widen them for log
    shippers. **C-006** (reason a); switch `rdx.compat.permissive-file-modes=true` restores umask behavior.
13. Secrets are `secrecy`/`zeroize` types, never `Debug`-printed, never in URLs, redacted in tracing (MISSION §4).

### Authorization
14. `rdx-authz` is a 1:1 port of `rundeck-authz-core` evaluation (`*.aclpolicy` YAML from `rundeck-authz-yaml`,
    `by`/`for`/`context`, `allow`/`deny` precedence, `match`/`equals`/`contains`/`subset`, wildcards) with the
    legacy test corpus (`legacy/rundeck-authz/**/src/test`) ported first; validation messages match where the oracle
    asserts them. System and project ACL files are read from the same locations with the same hot reload.
15. The semantics of the `RdAuthorize*` annotations become a typed policy layer on every handler; a test walks the
    router and fails on any handler without an explicit authorization check (MISSION §3.7). `/ui-api/v1` goes
    through the same layer.

## Consequences

Positive: all credential formats keep working; tokens are never stored or compared in clear; cookies, CSRF, headers
and file modes are secure by default while the oracle still runs; LDAP/PAM configurations migrate unchanged.

Negative: `ARGON2:` entries are one-way (legacy cannot read them); custom JAAS classes are unsupported; browser
scripts that called the API with a session cookie cross-site now need the CSRF header or the compat switch.

Risks: LDAP option parity across 1452 lines of legacy module — mitigated by the upstream `ldapTest` compose suite
(Phase 1 exit); CSP breaking a PrimeVue feature that needs inline styles — mitigated by a Playwright run with CSP
violation reporting enabled.

## Compatibility impact

Untouched: `realm.properties` formats, JAAS file syntax and option names for the standard modules, form login,
preauth keys, token header/param and lifecycle, `auth_token` schema, `JSESSIONID`, `rundeck.security.*` keys,
aclpolicy semantics. Deviations: **C-001, C-002, C-003, C-004, C-005, C-006, C-007, C-016, C-017, C-019, C-020**.

## Alternatives considered

- Argon2 for tokens — rejected: tokens are 256-bit random values (unsalted SHA-256 is adequate) and the legacy
  column/mode must stay readable by legacy during a rollback window.
- `__Host-` cookie prefix — rejected: changes the cookie name proxies depend on; `Secure`+`SameSite` reach the goal.
- Dropping `OBF:`/`MD5:` support — rejected by MISSION §2 (every legacy format accepted).
- Executing JAAS classes through a JVM — rejected (ADR-0001, no JVM).

## Migration / rollout

Nothing for realm/LDAP/PAM/preauth/token users. Packaged installs no longer log in as `admin:admin`: create a user
with `rdx realm hash` (or keep an existing `realm.properties`). Sites with custom JAAS classes need a native
equivalent (open a `decision` issue). Scripts calling the API cross-site with a session cookie add `X-RDX-CSRF` or
switch to tokens.

## References

- MISSION.md §1.1 (auth), §1.2 (`realm.properties`, `jaas-loginmodule.conf`), §2 (pre-approved deviations), §3.7.
- `legacy/core/src/main/java/org/rundeck/jaas/PasswordCredential.java:34-37,67-74,100,108,112,121,139`
- `legacy/rundeckapp/src/main/java/org/rundeck/jaas/PropertyFileLoginModule.java:42-46,133`
- `legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/jetty/jaas/JettyCachingLdapLoginModule.java:165-285`
- `legacy/rundeckapp/grails-app/domain/rundeck/AuthToken.groovy:36,81-95`;
  `legacy/rundeckapp/src/main/groovy/org/rundeck/app/data/providers/GormTokenDataProvider.groovy:194-215`;
  `legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/tokens/Token.groovy:80-83`;
  `legacy/rundeckapp/grails-app/services/rundeck/services/WebhookTokenSecureMigrationService.groovy:55-67`
- `legacy/rundeckapp/grails-app/conf/application.yml:233-258,397-405`; `application.groovy:166,171,175-183`
- `legacy/rundeckapp/grails-app/init/rundeckapp/init/servlet/JettyServletContainerCustomizer.groovy:86-98`
- `legacy/grails-securityheaders/src/main/groovy/grails/securityheaders/SecurityheadersGrailsPlugin.groovy:50-105`;
  `.../StrictTransportSecurityHeaderProvider.groovy:11`
- `legacy/packaging/lib/common/etc/rundeck/realm.properties:25`; `legacy/rundeckapp/src/main/resources/WEB-INF/jaaslogin.properties:1`
- `legacy/packaging/lib/common/etc/rundeck/profile:98`; `legacy/docker/official/etc/profile:25`
- `legacy/docker/official/remco/templates/jaas-loginmodule.conf:85-106`; `framework.properties:28-29`; `rundeck-config.properties:16`
