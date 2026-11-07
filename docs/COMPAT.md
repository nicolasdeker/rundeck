# COMPAT — register of externally visible deviations from Rundeck 6.3.0

`rdx` is a drop-in replacement for Rundeck OSS `v6.3.0` (commit `6ac5d092`): backend contracts are identical
(MISSION.md §1) unless a row below says otherwise. This file is the single list of everything an API client, a file on
disk, a database row, a plugin, a browser, a reverse proxy or an operator can observe to be different.

## Governance (MISSION.md §2)

1. **A deviation exists only if it has an ADR and a row here.** No row, no deviation: code that behaves differently
   from legacy without a row is a parity bug.
2. **Allowed reasons**: **(a)** fixes a security weakness; **(b)** legacy behavior is a bug confirmed by legacy tests
   or docs; **(c)** the legacy feature is JVM-bound. Pre-approved by the owner in MISSION §2: hashed tokens, argon2id
   for new local passwords, stricter headers/CSP, cookie flags, constant-time comparisons, `0600` files, no default
   admin, the whole UI. Additive features (§2) are listed too, marked `additive`; they never alter a legacy contract.
3. **Every row cites the legacy code** (`legacy/<path>:<line>`, verified by grep when written) that defines the
   behavior being changed, and names how the upstream oracle suite still passes.
4. **Compatibility switches** are `rdx.compat.<name>=true` in `rundeck-config.properties` (or `RDX_COMPAT_<NAME>=1`).
   **They default to the secure behavior.** Only the oracle fixture (`scripts/oracle.sh`, `.github/workflows/parity.yml`)
   may turn one on, and only when its row's "oracle impact" says so. Never weaken a default to pass a test (MISSION §8).
   `RDX_INSECURE_DEFAULT_ADMIN=1` is deliberately an environment variable, not a config key, so it cannot be left in a
   config file by accident.
5. **Status** moves `planned` → `implemented` (the commit that ships it) → `verified` (first green oracle run that
   exercises it, with the `PARITY.md` run reference). All rows are `planned` in Phase 0.
6. Transitional behavior is not a deviation: unimplemented endpoints return `501` with the legacy envelope and
   `errorCode: "api.error.not-implemented"` and stay `missing` in `PARITY.md` (MISSION §8).
7. Removing a row requires a superseding ADR.

## Register

| id | area | legacy behavior (path:line) | rdx behavior | reason | compat switch | ADR | status | oracle impact |
|---|---|---|---|---|---|---|---|---|
| C-001 | API tokens | New tokens stored SHA-256 (`AuthToken.groovy:36` default `SECURED`, `:81-95`); `LEGACY`/null rows hold the clear token, are matched by plaintext equality (`GormTokenDataProvider.groovy:194-215`) and returned in clear when unmasked (`api/tokens/Token.groovy:80-83`) | Never creates `LEGACY` rows; re-encodes existing `LEGACY`/null rows to `SECURED` in place at boot (same column, same mode legacy reads); clear value only in the creation response; `rundeck.tokens.file` static tokens unchanged | a | `rdx.compat.plaintext-tokens` (default `false`) | 0007 | planned | Tests create tokens via API and use the returned clear value; `admintoken` from `RUNDECK_TOKENS_FILE` keeps working. Unaffected |
| C-002 | Local passwords | `PasswordCredential.java:34-37,67-74` accepts plain, `MD5:`, `CRYPT:`, `BCRYPT:`, `OBF:`; nothing writes argon2 | All legacy formats still accepted and verified identically; new `ARGON2:` (argon2id PHC) format accepted; every password `rdx` writes (`rdx realm hash`) is argon2id; `rdx doctor` warns on plain/`MD5:`/`CRYPT:`/`OBF:` | a | none (additive accept; `ARGON2:` is one-way for legacy) | 0007 | planned | Fixtures use plaintext `admin:admin` — accepted. Unaffected |
| C-003 | Security headers / CSP | Headers on by default (`application.yml:247-258`) with CSP `script-src 'self' … 'unsafe-inline' 'unsafe-eval'`, `style-src 'unsafe-inline'`, `img-src * data:`; set defined in `SecurityheadersGrailsPlugin.groovy:50-102`, HSTS `StrictTransportSecurityHeaderProvider.groovy:11` | Legacy set is the floor; strict nonce-based CSP without `unsafe-*` or analytics hosts, `frame-ancestors 'none'`, `object-src 'none'`, `base-uri 'self'`; `rundeck.security.httpHeaders.*` overrides still honored | a | `rdx.compat.legacy-csp` (default `false`) | 0007 | planned | No header assertions in `legacy/functional-test` (grep `X-Frame-Options|Content-Security-Policy|Set-Cookie`: none). Unaffected |
| C-004 | Session cookie flags | `http-only: true`, `same-site: Lax`, `secure` unset — auto-enabled only when `grails.serverURL` is https and not behind forwarded headers (`application.yml:397-405`; `JettyServletContainerCustomizer.groovy:86-98`) | `HttpOnly` + `SameSite=Lax` always; `Secure` when serverURL is https **or** the request is TLS / trusted `X-Forwarded-Proto: https`; name `JSESSIONID` kept | a | `rdx.compat.insecure-session-cookie` (default `false`; legacy `server.servlet.session.cookie.secure=false` honored too) | 0007 | planned | Oracle runs over plain HTTP → `Secure` not set. Unaffected |
| C-005 | Secret comparison | `String.equals` on passwords/hashes (`PasswordCredential.java:100,108,112,121,139`) | `subtle::ConstantTimeEq` for passwords, hashes, tokens, CSRF, webhook secrets; DB lookups by hash only | a | none | 0007 | planned | None |
| C-006 | File permissions | Files created with process umask `002` → `0664` (`packaging/lib/common/etc/rundeck/profile:98`, `docker/official/etc/profile:25`); no explicit mode handling in logging code | Execution logs, `.rdlog`, server/audit logs, key storage, SQLite, exports `0600`; directories `0700`; `rdx.files.mode`/`dir_mode` widen | a | `rdx.compat.permissive-file-modes` (default `false`) | 0007 | planned | Tests read logs through the API. Unaffected |
| C-007 | Default credentials | `admin:admin` shipped (`packaging/lib/common/etc/rundeck/realm.properties:25`; `rundeckapp/src/main/resources/WEB-INF/jaaslogin.properties:1`; docker `README.md:65`) | No credentials in any packaged artifact; first boot prints how to create a user; `RDX_INSECURE_DEFAULT_ADMIN=1` creates in-memory `admin:admin` (roles `user,admin,architect,deploy,build`) with a loud warning | a | env `RDX_INSECURE_DEFAULT_ADMIN=1` only | 0007 | planned | The oracle fixture sets `RDX_INSECURE_DEFAULT_ADMIN=1` so `RUNDECK_TEST_USER/PASS` and token bootstrap work |
| C-008 | Embedded database | H2 default (`DataSource.groovy:4` `org.h2.Driver`, `:29` `jdbc:h2:file:...`) | H2 unsupported (`jdbc:h2:` URL rejected at `check-config`/`serve`); SQLite embedded default at `${rdeck.base}/data/rdx.sqlite`; Postgres/MySQL identical legacy schema; `rdx migrate --from-h2` (archives + documented CSV dump) | c | none | 0005 | planned | Parity suite runs on SQLite default and on legacy-initialized Postgres (`parity.yml`); `jdbcTest` on Postgres/MySQL compose |
| C-009 | Jar plugins | `JarPluginProviderLoader.java` loads `libext/*.jar` in-process | Jars are inventoried (manifest read, warning + `docs/PLUGINS.md` status) and never loaded; script plugins and the 15 built-ins (native, same provider names) unchanged; WASM ABI (Phase 6, off by default) | c | none | 0003 | planned | API specs use built-in/script providers; the upstream `pluginBlocklistTest` task targets jars → listed `deviated` in `PARITY.md` |
| C-010 | `UI` plugins | `UI` service type (`ServiceNameConstants.java:63`, `UIPlugin.java`) injects JS into GSP pages | Not supported; UI extension API in Phase 5 (own ADR) | c | none | 0003, 0004 | planned | No API spec depends on UI plugins; Selenium suite is not an oracle for the new UI |
| C-011 | Dropwizard servlets / admin pages | `/metrics/metrics|ping|healthcheck|threads` 404 by default, opt-in `rundeck.metrics.legacy.enabled=true`, removal planned 7.0 (`grails-metricsweb/.../UrlMappings.groovy:21-27`); admin servlet gated (`DisablingAdminServlet.groovy:98-99`) | Never served (404 regardless of the key); `/api/*/metrics/*` Dropwizard JSON and `/monitoring/*` kept | c (+ upstream-deprecated) | none | 0008 | planned | API tests hit `/api/*/metrics/*` (`UrlMappings.groovy:270`), which is kept |
| C-012 | Guided tours | `/tour/listAll`, `/tour/list/$loaderName`, `/tour/get/$loaderName/$tour` (`UrlMappings.groovy:359-361`, `TourController.groovy`); tours rendered by GSP/ui-trellis | API shapes and `TourLoader` service kept; presentation redone in the new UI (Phase 5) | UI (§3.8) | none | 0004 | planned | API shapes unchanged |
| C-013 | Web UI | GSP pages (260) + `ui-trellis` SPA | Whole UI rebuilt (Vue 3, mobile-first); same journeys; legacy deep links served or 302-redirected; same login form contract (`/j_security_check`, `application.groovy:175-177`) | UI (§3.8, pre-approved) | none | 0004 | planned | 57 Selenium specs are not an oracle for the new UI; Playwright journeys in `ui/e2e/` replace them (MISSION §1.6) |
| C-014 | Prometheus exposition | Already exposed at `/monitoring/prometheus` with `/monitoring/metrics`, `/monitoring/health[/readiness]` (`UrlMappings.groovy:22-26`, `MonitoringController.groovy:15,191`, `permitAll` `application.groovy:138`) | Same paths, same gating key, same format; **no new `/metrics` path** (MISSION §3.9 wording refined: `/metrics/*` is the legacy Dropwizard namespace); `rdx_*` series additive | none (parity; corrects MISSION §3.9) | none | 0008 | planned | Unaffected |
| C-015 | UI-only API | none | `/ui-api/v1` (SSE, aggregated views, session/CSRF): non-contract, versioned, same authz layer, no domain mutations outside `/api/*` | additive (§3.8) | none | 0004, 0007 | planned | Unaffected |
| C-016 | CSRF on cookie-authenticated API calls | Session cookies may call `/api/*` (`application.yml:233-234` `apiCookieAccess.enabled: true`) with no CSRF check on `/api/**` (`application.groovy:166`); HMAC tokens only for GSP forms (`application.yml:246`) | Cookie-authenticated non-safe methods on `/api/*` and `/ui-api/*` need `X-RDX-CSRF` (from `/ui-api/v1/session`) or `Sec-Fetch-Site: same-origin|none`, else 403; token auth exempt | a | `rdx.compat.cookie-api-no-csrf` (default `false`) | 0007 | planned | API specs authenticate with tokens. Unaffected |
| C-017 | Login / token rate limiting | None (no rate-limit code under `rundeckapp/grails-app`, `src/main`) | Token bucket per IP and per user on `/j_security_check` and token creation (10/min, burst 20) → 429 + `Retry-After` | a | `rdx.compat.unlimited-login-attempts` (default `false`) | 0007 | planned | Limits sized above test rates; if a spec trips them the fixture enables the switch and the row says so |
| C-018 | TLS keystore | JKS keystore via `ssl.properties` (`packaging/lib/common/etc/rundeck/ssl/ssl.properties:1-2`) | PEM (`rdx.tls.cert/key`) or PKCS#12; JKS not read; `rdx doctor` prints the `keytool` conversion | c | none | 0002 | planned | Oracle runs over HTTP. Unaffected |
| C-019 | Custom JAAS classes | Any class named in `jaas-loginmodule.conf` is loaded by the JVM (`docker/official/remco/templates/jaas-loginmodule.conf:85-106`) | Standard modules mapped to native providers (property file, LDAP, combined LDAP, PAM, same options); any other class is a `check-config` error | c | none | 0007 | planned | Fixtures use `PropertyFileLoginModule`; `ldapTest` uses `JettyCachingLdapLoginModule`. Unaffected |
| C-020 | Session lifetime | In-memory Jetty sessions (`application.yml:398` `persistent: false`), idle timeout `server.servlet.session.timeout` (docker default 3600, `remco/templates/rundeck-config.properties:16`), no absolute limit | DB-backed sessions (survive restart, shared in cluster); same idle key; new absolute lifetime `rdx.session.absolute_timeout` (default 24 h) | a | none (`rdx.session.absolute_timeout=0` disables) | 0007 | planned | Test sessions are short. Unaffected |
| C-021 | Static asset caching | `Cache-Control: no-cache, no-store, max-age=0, must-revalidate` on all responses (`SecurityheadersGrailsPlugin.groovy:85-88`) | Hashed immutable assets `public, max-age=31536000, immutable`; HTML shell and API `no-store` | UI (§3.8) | none | 0004 | planned | API responses keep `no-store`. Unaffected |

Paths in the table are relative to `legacy/`; `application.yml`/`application.groovy` are
`legacy/rundeckapp/grails-app/conf/`, `UrlMappings.groovy` is `legacy/rundeckapp/grails-app/controllers/rundeckapp/`
unless prefixed.

## Not deviations (recorded to stop the question coming back)

- Product name `rdx` and the `NOTICE` trademark statement: no contract carries "Rundeck" as a value except the keys,
  headers, paths and variables kept verbatim (ADR-0001).
- `rdx_migrations`, `rdx_schedule`, `rdx_session` tables: additive schema in `rdx`'s own migration table; Liquibase
  tables untouched (ADR-0005, ADR-0006, ADR-0007).
- Scheduler persistence and restart-safe one-shots (ADR-0006), structured JSON logs and OTLP (ADR-0008), HTTP/2,
  `X-Request-Id` (ADR-0002), systemd `rdx.service` with `Alias=rundeckd.service`, Helm chart, SBOM/signatures
  (ADR-0009): internal or additive.
