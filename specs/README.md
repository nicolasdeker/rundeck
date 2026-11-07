# specs/ — behavior specifications written from the legacy code, before the code

MISSION.md §5 step 2: no Rust module without its `specs/<area>.md`, no UI page without its journey in
`specs/ui-journeys.md` and a Playwright test. A spec is a contract you can test; vague sentences are not allowed.
Specs are written from `legacy/` (grep, then read ranges — never a file over 500 lines whole) and from the
upstream functional tests, which are the oracle (`scripts/parity.sh <SpecClass>`).

Files in this directory at Phase 0:

- `README.md` — this file: the template and the plan of spec files per phase.
- `ui-journeys.md` — the inventory of the 73 user journeys (MISSION §1.6), with deep links, API endpoints,
  upstream Selenium specs and Playwright files. Rows mirror the *Journeys* section of `PARITY.md`.

## Spec template (`specs/<area>.md`)

```markdown
# <area> — <one-line scope>

Legacy references: <file:line list — controllers → services → core → plugins, and the Spock specs>
Upstream oracle specs: <functional spec classes under legacy/functional-test/.../functional/api/**, or "none" + the differential test to write>
PARITY.md rows: <ids, e.g. R-040..R-049, B-025>
Status: draft | reviewed (parity-reviewer) | implemented

## 1. Endpoints / formats
For each endpoint: method, pattern (verbatim from UrlMappings.groovy), controller.action, authorization
(resource type + actions checked, legacy `AuthConstants`), request parameters/body per content type
(`application/json`, `application/xml`, `application/yaml`, `text/plain`, multipart), pagination (`offset`, `max`),
filters, response shape per format with an example captured from the oracle (`tests/golden/<name>`), status codes.

## 2. Error cases
errorCode, HTTP status, message key (`legacy/rundeckapp/grails-app/i18n/messages.properties`), per format
(JSON envelope `{"error":true,"apiversion":N,"errorCode":"...","message":"..."}`, XML `<result error="true" apiversion="N">`).

## 3. Per-API-version differences
Every `request.api_version` branch in the legacy code, with the version threshold and both behaviors.

## 4. Behavior and edge cases
Ordering, defaults, limits, empty inputs, concurrency, idempotency, time zones, encoding, size limits —
each with the legacy file:line that defines it.

## 5. Security-relevant checks
AuthN/AuthZ decisions, input validation, path traversal, secrets handling, rate/size limits, CSRF/session rules.

## 6. Data
Tables/columns read or written (legacy names), transactions, cascade rules, migration notes (`rdx_migrations`).

## 7. Open questions resolved with the parity default
Each ambiguity, the legacy behavior kept, and the DECISIONS-PENDING.md / ADR reference if any.

## 8. Test plan
Ported unit/property tests (from which legacy Spock specs), golden files, fuzz target (for parsers),
oracle command (`make parity FILTER=<SpecClass>`), Playwright journeys touched.
```

## Planned spec files per phase (one per area; legacy references are the starting points)

Phase 1 — foundations
| Spec | Covers (PARITY.md rows) | Legacy references |
|---|---|---|
| `specs/config.md` | `rundeck-config.properties`, `framework.properties`, `project.properties`, env overrides (F-009..F-011) | `legacy/core/.../common/{Framework,FrameworkFactory,FrameworkProjectConfig}.java`, `legacy/core/.../utils/PropertyLookup.java`, `legacy/rundeckapp/grails-app/services/rundeck/services/ConfigurationService.groovy`, `legacy/packaging/lib/common/etc/rundeck/*.properties`, `legacy/docker/official/remco/templates/*` |
| `specs/db-schema.md` | the 23 domain classes / tables (D-001..D-023), `rdx_migrations` | `legacy/rundeckapp/grails-app/domain/**`, `legacy/grails-webhooks/grails-app/domain/webhooks/Webhook.groovy`, `legacy/rundeckapp/grails-app/migrations/core/*.groovy` |
| `specs/api-envelope.md` | version negotiation, error envelope, content negotiation, `/api/V/system/info`, catch-all 404, 501 for unimplemented (B-001, B-002, R-079..R-081, R-113, R-119) | `legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/ApiVersions.groovy`, `.../services/ApiService.groovy:1023-1128`, `.../controllers/ApiController.groovy`, `legacy/gradle/grailsopenapispec.gradle` (OpenAPI secondary oracle) |
| `specs/authn.md` | `realm.properties`, `jaas-loginmodule.conf`, tokens, sessions, `/j_security_check`, pre-auth headers (F-012, F-013, B-003, R-090..R-092) | `legacy/rundeckapp/src/main/java/org/rundeck/jaas/PropertyFileLoginModule.java`, `legacy/rundeckapp/src/main/groovy/{org/rundeck/jaas,com/dtolabs/rundeck/jetty/jaas}/**`, `legacy/rundeckapp/grails-app/conf/application.groovy:119-190`, `.../services/RundeckAuthTokenManagerService.groovy` |
| `specs/authz.md` | `*.aclpolicy`, evaluation, `/system/acl/*`, `/project/*/acl/*`, `/authorizations/*` (F-008, B-046, R-085, R-040, R-114..R-118) | `legacy/rundeck-authz/{rundeck-authz-api,rundeck-authz-core,rundeck-authz-yaml}`, `.../services/{AuthorizationService,AclFileManagerService}.groovy`, `.../controllers/AuthorizationsController.groovy` |
| `specs/users-tokens-features.md` | `/tokens/*`, `/token/*`, `/user/*`, `/feature/*` (R-090..R-098, R-107..R-108) | `.../controllers/{ApiController,UserController}.groovy`, `.../services/feature/FeatureService.groovy` |
| `specs/web-shell.md` | legacy deep-link redirects, SPA shell, `/ui-api/v1` session/CSRF, health (W-*) | `UrlMappings.groovy:291-368`, `MenuController`, `UserController`, `conf/application.groovy` |

Phase 2 — projects, nodes, storage
| Spec | Covers | Legacy references |
|---|---|---|
| `specs/projects.md` | projects CRUD/config/readme/motd/meta/export-import incl. async, archive format (R-046..R-065, F-018, B-040..B-046) | `.../controllers/ProjectController.groovy`, `.../services/{ProjectService,ProjectManagerService}.groovy`, `.../services/asyncimport/*` |
| `specs/nodes.md` | resources formats, node filter language, sources, writable sources, `/nodes/tags`, caching, `NodeEnhancer` (F-004..F-007, R-066..R-072, B-041, B-042, B-055) | `legacy/core/.../resources/**`, `legacy/core/.../utils/NodeSet.java`, `legacy/core/.../common/NodeFilter.java`, `.../controllers/FrameworkController.groovy`, `.../services/NodeService.groovy` |
| `specs/storage.md` | key storage API, fs + DB layouts, converters, AES-GCM, incubator storage (R-093..R-095, F-016, F-017) | `legacy/rundeck-storage/**`, `legacy/core/.../storage/**`, `.../services/{StorageService,DbStorageService,ConfigStorageService}.groovy`, `legacy/plugins/aes-gcm-encryption-plugin`, `legacy/encryption-core` |

Phase 3 — jobs, workflow, executions, scheduler
| Spec | Covers | Legacy references |
|---|---|---|
| `specs/jobs.md` | job model, XML/YAML/JSON codecs, import/export/browse/validateOption/meta/info/workflow/components, file uploads, remote options (R-013..R-039, R-043..R-045, F-001..F-003, B-053, B-054) | `legacy/rundeckapp/grails-app/utils/rundeck/codecs/{JobsXMLCodec,JobsYAMLCodec}.groovy`, `legacy/rundeckapp/src/main/groovy/org/rundeck/app/components/RundeckJobDefinitionManager.groovy`, `.../controllers/{ScheduledExecutionController,EditOptsController,MenuController}.groovy`, `.../services/{ScheduledExecutionService,FileUploadService,JobMetadataService}.groovy`, `.../services/optionvalues/OptionValuesService.groovy` |
| `specs/workflow.md` | strategies, rule engine, error handlers, keepgoing, contexts, expansion, secure options, log filters, job references, orchestrators, node dispatch (B-004..B-021) | `legacy/core/.../execution/workflow/**`, `legacy/core/.../rules/**`, `legacy/core/.../dispatcher/DataContextUtils.java`, `legacy/core/.../execution/dispatch/**`, `legacy/core/.../execution/orchestrator/**`, `.../services/ExecutionService.groovy` |
| `specs/executions.md` | run/abort/retry/output/state/delete/metrics/running/input files, execution mode, `.rdlog`, log storage rules, cleanup (R-001..R-012, R-041..R-042, R-082..R-084, F-015, F-020, B-022..B-032) | `.../controllers/{ExecutionController,RdExecutionController}.groovy`, `.../services/{ExecutionService,LoggingService,LogFileStorageService,ExecutionUtilService}.groovy`, `legacy/core/.../logging/internal/RundeckLogFormat.java`, `legacy/grails-execution-mode-timer` |
| `specs/scheduler.md` | Quartz cron, timezone, enable flags, forecast, cluster ownership, takeover, recovery, thresholds (R-076..R-078, B-033..B-040) | `.../services/{ScheduledExecutionService,JobSchedulerService,JobSchedulesService}.groovy`, `legacy/rundeckapp/grails-app/domain/rundeck/ScheduledExecution.groovy`, `legacy/core/.../schedule/**`, `quartz-cron/` |
| `specs/executors.md` | NodeExecutor/FileCopier contracts (local, ssh/scp/sftp, script plugins, stub), script plugin zip + `plugin.yaml` (S-006, S-007, F-019, BP-*) | `legacy/core/.../execution/service/**`, `legacy/core/.../plugins/ScriptPlugin*.java`, `legacy/plugins/{jsch-plugin,script-plugin,localexec-plugin,copyfile-plugin,stub-plugin,script-node-step-plugin}` |
| `specs/notifications.md` | email/webhook/plugin notifications (B-047) | `.../services/NotificationService.groovy`, `legacy/rundeckapp/grails-app/domain/rundeck/Notification.groovy`, `views/execution/mailNotification/status.gsp` |

Phase 4 — everything else in the API
| Spec | Covers | Legacy references |
|---|---|---|
| `specs/webhooks.md` | `/webhook/*`, `WebhookEvent` plugins, tokens (P-001..P-003, B-048) | `legacy/grails-webhooks/**` |
| `specs/scm.md` | SCM export/import with git, all `/scm/*` routes (R-029..R-032, R-073..R-075, B-049) | `.../controllers/ScmController.groovy`, `.../services/ScmService.groovy`, `.../services/scm/*`, `legacy/plugins/git-plugin` |
| `specs/plugins.md` | `/plugin/*`, `/plugins/*`, `/repository/*`, plugin descriptors and property forms, service types (R-111..R-112, P-004..P-029, S-*) | `.../controllers/PluginController.groovy`, `.../services/{PluginService,PluginApiService,UiPluginService}.groovy`, `legacy/grails-repository/**`, `legacy/core/.../plugins/**` |
| `specs/system.md` | `/system/*` (info, logstorage, executions mode), `/metrics/*`, `/monitoring/*`, `/home/summary`, `/scheduler/*`, incubating endpoints (R-079..R-089, R-109..R-110, R-017, P-030..P-033) | `.../controllers/{ApiController,MenuController,MonitoringController}.groovy`, `legacy/grails-metricsweb`, `.../services/{DropwizardMicrometerBridgeService,MicrometerExecutionMetricsService}.groovy` |
| `specs/lifecycle-audit.md` | execution/job lifecycle plugins, `UserGroupSource`, audit events (B-056..B-058) | `legacy/core/.../plugins/{jobs,project,user,audit}/**`, `legacy/core/.../audit/**`, `legacy/plugins/audit-logging-plugin` |

Phase 5 — UI completeness: no new backend spec; every row of `specs/ui-journeys.md` gets its Playwright test and
`docs/ui-review/phase-5/` gallery. Phase 6 — `specs/migration.md` (`rdx migrate --from-h2`, legacy Postgres/MySQL
boot), `specs/packaging.md` (env variable names and templates of `legacy/docker/official`, `legacy/packaging`).

Row ids above refer to `PARITY.md` as generated at Phase 0; when a range is cited, check the ids in the file
before using them in a spec header (rows are never renumbered, but a cited range may need a comma-separated list).
