# UI journeys — inventory of every user journey of the legacy UI (Rundeck 6.3.0)

Source of truth for the frontend contract of MISSION.md §1.6: every journey the legacy UI offers must exist
in the new UI, with the same deep links (old routes redirect) and a Playwright test. This file is the
inventory; the matching `PARITY.md` rows (area *Journeys*) carry the status and the evidence.

Built from three legacy sources (see `scripts/inventory/README.md` for the extraction commands):

1. the **57 Selenium specs** under `legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/selenium/`
   (55 `@SeleniumCoreTest`, `ldap/LdapLoginSpec` is `@LdapTest`, `project/ProjectsSpec` is `@UiModeFlag` only;
   241 feature methods in total — `python3 -I scripts/inventory/selenium_specs.py`);
2. the **260 GSP files** under `legacy/rundeckapp/grails-app/views/**` (233) and the Grails plugins (27) — the
   page templates (non-partial `*.gsp`) are listed in §3;
3. the **SPA page bundles** of `legacy/rundeckapp/grails-spa/packages/ui-trellis/src/app/pages/*` (the 30
   `pages/*` entries of `vue.config.app.js`; the only vue-router instance is `pages/repository/router.js`) — §4.

Conventions: `$p` = project name, `V` = `$api_version` (routes from `UrlMappings.groovy`, see `PARITY.md`),
`J-NNN` ids are stable, the Playwright file is `ui/e2e/j-NNN-<slug>.spec.ts`, phases follow MISSION.md §6
(1 foundations · 2 projects/nodes/storage · 3 jobs/executions/scheduler · 4 everything else in the API · 5 UI
completeness). Status values: `missing | partial | done | deviated | blocked` (MISSION §8: `done` only with a
recorded Playwright run; `deviated` needs an ADR + `docs/COMPAT.md`; `blocked` needs `BLOCKED/<id>.md`).
Selenium spec names are given relative to `.../functional/selenium/`; "no upstream test" means no Selenium spec
exercises the journey (the Playwright test is then the only oracle, written from the GSP/SPA behavior).

## 1. Journeys

| Id | Journey | Legacy entry points (deep links) | API endpoints used | Upstream Selenium spec(s) | Playwright test | Phase | Status |
|----|---------|----------------------------------|--------------------|---------------------------|-----------------|-------|--------|
| J-001 | Login shell: form login, wrong user / wrong or empty password errors, logout → logged-out page, help link | `/user/login`, `POST /j_security_check`, `/user/logout`, `/user/loggedout` | none (session cookie; `application.groovy:175-180`) | `login/BasicLoginSpec`, `ldap/LdapLoginSpec` | `ui/e2e/j-001-login-shell.spec.ts` | 1 | missing |
| J-002 | Deployment under a servlet context path: login and static assets resolve with a prefix | `/<ctx>/user/login`, `/<ctx>/static/**` | none | `contextPath/ContextPathLoginSpec` | `ui/e2e/j-002-context-path.spec.ts` | 1 | missing |
| J-003 | Top navigation: Jobs / Nodes / Commands / Activity / System Configuration links | `/menu/home`, `/project/$p/home`, `/project/$p/jobs`, `/project/$p/nodes`, `/project/$p/command/run`, `/project/$p/activity`, `/menu/systemConfig` | `/api/V/projects`, `/api/V/system/info` | `navigation/NavigationSpec` | `ui/e2e/j-003-top-navigation.spec.ts` | 1 | missing |
| J-004 | Main bar menus: system-configuration and user dropdowns on home, project home and project configuration | `/menu/home`, `/project/$p/home`, `/project/$p/configure` | `/api/V/projects` | `navigation/MainbarMenuSpec` | `ui/e2e/j-004-mainbar-menus.spec.ts` | 1 | missing |
| J-005 | User profile and API tokens: view profile, generate token (roles, expiry, default duration), delete token, remove expired | `/user/profile`, `/user/edit`, `/user/generateUserToken`, `/user/clearApiToken`, `/user/removeExpiredTokens` | `/api/V/tokens/$user?`, `/api/V/token/$tokenid`, `/api/V/tokens/$user/removeExpired`, `/api/V/user/info/$username?`, `/api/V/user/roles` | `profile/TokenSpec`, `login/BasicLoginSpec` (login as admin / as user) | `ui/e2e/j-005-profile-tokens.spec.ts` | 1 | missing |
| J-006 | UI language switch (fr_FR, ja_JP) from the profile, applied to all pages | `/user/profile` (language), `/user/edit` | `/api/V/user/info/$username?` | `jobs/JobsSpec` (change UI lang fr_FR / ja_JP and cancel job create) | `ui/e2e/j-006-language-switch.spec.ts` | 1 | missing |
| J-007 | Settings bar: theme selection and UI early-access toggle (persisted per user/browser) | utility bar on every page | none | `settings/SettingsBarSpec` | `ui/e2e/j-007-settings-theme.spec.ts` | 1 | missing |
| J-008 | Error pages: 404, 405, 500 and "execution unauthorized" | `404`/`405`/`500` mappings (`UrlMappings.groovy:370-372`), `views/common/execUnauthorized.gsp`, `views/common/error.gsp` | none | no upstream test | `ui/e2e/j-008-error-pages.spec.ts` | 1 | missing |
| J-009 | Home: project list with summary stats, create-project entry, per-project actions | `/`, `/menu/home`, `/menu/index` | `/api/V/projects`, `/api/V/home/summary`, `/api/V/project/$project/meta` | `project/ProjectsSpec`, `navigation/MainbarMenuSpec` | `ui/e2e/j-009-home-project-list.spec.ts` | 2 | missing |
| J-010 | Create project: name / label / description with validation (empty name, invalid characters) | `/resources/createProject` | `POST /api/V/projects` | `project/CreateProjectSpec` | `ui/e2e/j-010-create-project.spec.ts` | 2 | missing |
| J-011 | Project dashboard: execution and user counts, user details, readme/motd, authorization-dependent summary | `/project/$p/home` | `/api/V/project/$project`, `/api/V/project/$project/executions`, `/api/V/project/$project/history`, `/api/V/home/summary` | `project/ProjectDashboardSpec`, `project/ProjectDashboardAuthSpec` | `ui/e2e/j-011-project-dashboard.spec.ts` | 2 | missing |
| J-012 | Project sidebar: navigation links shown according to the user's authorizations (read-only users see no settings) | `/project/$p/home` (sidebar on every project page) | `/api/V/authorizations/project/$project/$kind`, `/api/V/authorizations/project/$project/$type/$specifier` | `project/NavSidebarSpec` | `ui/e2e/j-012-project-sidebar.spec.ts` | 2 | missing |
| J-013 | Project settings: add / change / delete description and label | `/project/$p/configure` | `GET /api/V/project/$project/config`, `PUT /api/V/project/$project/config/$keypath**` | `project/EditProjectSpec` | `ui/e2e/j-013-project-settings-basic.spec.ts` | 2 | missing |
| J-014 | Project settings: default node executor (SSH, SSHJ, local, script, stub, …) with plugin property forms | `/project/$p/configure` | `/api/V/project/$project/config`, `/api/V/plugin/list`, `/api/V/plugin/detail/$service/$provider` | `project/ExecutorSpec` | `ui/e2e/j-014-project-node-executor.spec.ts` | 2 | missing |
| J-015 | Project settings: default file copier (SCP, SSHJ-SCP, stub, script, WinRM, OpenSSH) with plugin property forms | `/project/$p/configure` | `/api/V/project/$project/config`, `/api/V/plugin/list`, `/api/V/plugin/detail/$service/$provider` | `project/DefaultFileCopierSpec` | `ui/e2e/j-015-project-file-copier.spec.ts` | 2 | missing |
| J-016 | Project settings: edit the raw project configuration and project files in an editor | `/resources/editProjectConfig?project=$p`, `/resources/editProjectFile?project=$p` (`UrlMappings.groovy:311`) | `GET/PUT /api/V/project/$project/config`, `/api/V/project/$project/readme.md`, `/api/V/project/$project/motd.md` | no upstream test | `ui/e2e/j-016-project-config-file.spec.ts` | 2 | missing |
| J-017 | Project readme: edit from settings, displayed on the project home | `/project/$p/configure` → readme editor, `/project/$p/home` | `GET/PUT/DELETE /api/V/project/$project/readme.md` | `project/ReadmeSpec` | `ui/e2e/j-017-project-readme.spec.ts` | 2 | missing |
| J-018 | Project message of the day: edit, choose where it shows (navbar / project home / project list) | `/project/$p/configure` → motd editor, `/project/$p/home`, `/menu/home` | `GET/PUT/DELETE /api/V/project/$project/motd.md`, `PUT /api/V/project/$project/config/$keypath**` (`project.gui.motd.display`) | `project/MotdSpec` | `ui/e2e/j-018-project-motd.spec.ts` | 2 | missing |
| J-019 | Node sources: list, add a source plugin, configure, save, help, writable-source marker | `/project/$p/nodes/sources`, `/project/$p/nodes/sources/edit`, `/project/$p/nodes/sources/storageaccess` | `/api/V/project/$project/sources`, `/api/V/project/$project/source/$index`, `/api/V/project/$project/configurable`, `POST /api/V/project/$project/plugins/save`, `/api/V/plugin/list` | `project/NodesSpec` | `ui/e2e/j-019-node-sources.spec.ts` | 2 | missing |
| J-020 | Edit a writable node source file (JSON/YAML/XML) in a code editor, save, see the nodes | `/project/$p/nodes/source/$index/edit`, `/project/$p/nodes/source/$index/save` | `GET/POST /api/V/project/$project/source/$index/resources` | `project/AceEditorSpec` | `ui/e2e/j-020-node-source-file-editor.spec.ts` | 2 | missing |
| J-021 | Node browser: filter language (`.*`, name, `tags:`, combined), filter from URL, attributes, expand node, save and reuse a filter | `/project/$p/nodes`, `/project/$p/nodes?filter=…` | `/api/V/project/$project/resources`, `/api/V/project/$project/resource/$name`, `/api/V/project/$project/nodes/tags` | `nodes/NodesSpec` | `ui/e2e/j-021-node-browser.spec.ts` | 2 | missing |
| J-022 | Key storage browser: browse folders, add / overwrite / delete / download keys and passwords | `/menu/storage`, `/menu/storage/$resourcePath**`, `/storage/upload/keys`, `/storage/delete/keys`, `/storage/download/keys`, `/storage/access/keys` | `GET/POST/PUT/DELETE /api/V/storage/keys`, `/api/V/storage/keys/$resourcePath**` | `appadmin/KeyStorageSpec` | `ui/e2e/j-022-key-storage.spec.ts` | 2 | missing |
| J-023 | System access control: upload / validate / create / edit / delete ACL policy files, duplicate-name warning | `/menu/acls`, `/menu/acls/create`, `/menu/acls/edit/$id**`, `/menu/acls/save`, `/menu/acls/delete/$id**` | `GET/POST/PUT/DELETE /api/V/system/acl/$path**` | `appadmin/AccessControlSpec` | `ui/e2e/j-023-system-acls.spec.ts` | 2 | missing |
| J-024 | Project access control: project-scoped ACL policy files | `/project/$p/admin/acls`, `/project/$p/admin/acls/create`, `/project/$p/admin/acls/edit/$id**`, `/project/$p/admin/acls/save`, `/project/$p/admin/acls/delete/$id**` | `GET/POST/PUT/DELETE /api/V/project/$project/acl/$path**` | no upstream test | `ui/e2e/j-024-project-acls.spec.ts` | 2 | missing |
| J-025 | Project export: choose components, export / download, promote to another instance, authorization-dependent options | `/project/$p/export`, `/project/$p/exportPrepare`, `/project/$p/exportWait/$token` | `/api/V/project/$project/export`, `/api/V/project/$project/export/async`, `/api/V/project/$project/export/status/$token`, `/api/V/project/$project/export/download/$token` | `project/ProjectExportSpec`, `project/ProjectExportAuthSpec` | `ui/e2e/j-025-project-export.spec.ts` | 2 | missing |
| J-026 | Project import: upload an archive with options, invalid archives rejected, status | `/project/$p/import`, `/project/$p/importArchive` | `PUT /api/V/project/$project/import`, `/api/V/project/$project/import/status` | `project/ImportProjectSpec` | `ui/e2e/j-026-project-import.spec.ts` | 2 | missing |
| J-027 | Project delete (confirmation, deferred deletion) | `/project/$p/admin/delete` | `DELETE /api/V/project/$project` | no upstream test | `ui/e2e/j-027-project-delete.spec.ts` | 2 | missing |
| J-028 | Job list: browse groups (expanded / collapsed per project setting), filter by name and group, job search, saved filters | `/project/$p/jobs`, `/project/$p/jobs/$groupPath**` | `/api/V/project/$project/jobs`, `/api/V/project/$project/jobs/browse`, `/api/V/job/$id/info` | `jobs/BasicJobsSpec` (view jobs list page, job filter …), `jobs/ExpandedJobGroupsSpec` | `ui/e2e/j-028-job-list.spec.ts` | 3 | missing |
| J-029 | Job list bulk actions: enable / disable executions and schedules, bulk delete | `/project/$p/jobs` (bulk edit mode) | `POST /api/V/jobs/execution/enable`, `/api/V/jobs/execution/disable`, `/api/V/jobs/schedule/enable`, `/api/V/jobs/schedule/disable`, `/api/V/jobs/delete` | `jobs/BulkJobActionsSpec` | `ui/e2e/j-029-job-bulk-actions.spec.ts` | 3 | missing |
| J-030 | Run job dialog: option inputs (incl. URL options, JSON list defaults), validation errors, editable node filter, run later, run from the job-list modal | `/project/$p/job/show/$id` (run form), job list run modal | `POST /api/V/job/$id/run`, `/api/V/job/$id/executions`, `/api/V/project/$project/jobs/validateOption`, `/api/V/job/$id/input/file/$optionName?` | `jobs/BasicJobsSpec` (run job modal …), `jobs/BulkJobActionsSpec` (job can be executed from the Job List Page modal), `jobs/JobsSpec` (Run job later, Url job options, Select all json list options by default, job execution with invalid option value) | `ui/e2e/j-030-run-job-dialog.spec.ts` | 3 | missing |
| J-031 | Job create: basic fields, empty name / empty workflow validation, first step, first option, cancel | `/project/$p/job/create` | `POST /api/V/project/$project/jobs/import`, `/api/V/incubating/jobs/components` | `jobs/BasicJobsSpec` (create job …) | `ui/e2e/j-031-job-create.spec.ts` | 3 | missing |
| J-032 | Job editor tabs: details, group picker modal, schedules, execution, other, notifications | `/project/$p/job/edit/$id` | `GET /api/V/job/$id`, `POST /api/V/project/$project/jobs/import` (`dupeOption=update`), `/api/V/incubating/job/$id/components` | `jobs/BasicJobsSpec` (edit job …), `jobs/JobNotificationSpec`, `jobs/JobTabsSpec` | `ui/e2e/j-032-job-editor-tabs.spec.ts` | 3 | missing |
| J-033 | Job editor workflow: add / edit / cancel / duplicate / remove / reorder steps, undo / redo / revert, step filter, node steps, error handlers, strategy, context-variable autocomplete | `/project/$p/job/edit/$id` (legacy ajax `/workflow/*`, `WorkflowController`) | `/api/V/plugin/list`, `/api/V/plugin/detail/$service/$provider`, `/api/V/job/$id/workflow` | `jobs/JobsSpec` (workflow features), `jobs/JobEditSpec` (add and remove steps) | `ui/e2e/j-033-job-editor-workflow.spec.ts` | 3 | missing |
| J-034 | Job editor options: create / duplicate / undo / redo / revert, option types incl. date, secure option without default | `/project/$p/job/edit/$id` (legacy ajax `/editOpts/*`, `EditOptsController`) | `/api/V/project/$project/jobs/validateOption` | `jobs/JobsSpec` (job option …, Create option form, Duplicate option create form), `jobs/DuplicateOptionsSpec` | `ui/e2e/j-034-job-editor-options.spec.ts` | 3 | missing |
| J-035 | Job editor nodes: dispatch to nodes, node filter preview while editing (single and combined values), orchestrator, thread count | `/project/$p/job/edit/$id` | `/api/V/project/$project/resources`, `/api/V/plugin/list` (Orchestrator) | `jobs/JobsSpec` (create job with dispatch to nodes, rename job with orchestrator), `jobs/JobEditSpec` (Filter nodes while editing …) | `ui/e2e/j-035-job-editor-nodes.spec.ts` | 3 | missing |
| J-036 | Log filters: global and per-step filters (highlight, key/value and multiline regex capture, replacement) and their rendering in the execution output | `/project/$p/job/edit/$id`, `/project/$p/execution/show/$id` | `/api/V/plugin/list` (LogFilter), `/api/V/execution/$id/output(.$format)?` | `jobs/JobsSpec` (add global log filters), `jobs/LogFilterSpec` | `ui/e2e/j-036-job-log-filters.spec.ts` | 3 | missing |
| J-037 | Job reference steps: by uuid / name / autocomplete / "choose a job" picker, import and pass options, node filter and thread-count override, run | `/project/$p/job/edit/$id`, `/menu/jobsPicker` | `/api/V/project/$project/jobs`, `POST /api/V/job/$id/run`, `/api/V/job/$id/executions` | `jobs/JobReferenceSpec` | `ui/e2e/j-037-job-reference-steps.spec.ts` | 3 | missing |
| J-038 | Job schedule: crontab editor, timezone, scheduled-job ACL warning, enable / disable schedule | `/project/$p/job/edit/$id`, `/project/$p/job/show/$id` | `POST /api/V/job/$id/schedule/enable`, `/api/V/job/$id/schedule/disable`, `/api/V/job/$id/forecast`, `/api/V/scheduler/jobs` | `jobs/ScheduledJobSpec`, `jobs/ScheduledJobExecutionAclWarningSpec` | `ui/e2e/j-038-job-schedule.spec.ts` | 3 | missing |
| J-039 | Job show page: definition, summary stats, action menu, nodes / log output / HTML output tabs, runbook | `/project/$p/job/show/$id`, `/project/$p/job/show/$id/$fullName**`, `/job/show/$id`, `/project/$p/job/runbook/$id` | `/api/V/job/$id`, `/api/V/job/$id/info`, `/api/V/job/$id/meta`, `/api/V/job/$id/executions`, `/api/V/job/$id/workflow` | `jobs/BasicJobsSpec` (showing the edited job), `jobs/JobSummarySpec`, `jobs/JobTabsSpec` | `ui/e2e/j-039-job-show.spec.ts` | 3 | missing |
| J-040 | Job execution and schedule toggles from the job page | `/project/$p/job/show/$id` | `POST /api/V/job/$id/execution/enable`, `/api/V/job/$id/execution/disable`, `/api/V/job/$id/schedule/enable`, `/api/V/job/$id/schedule/disable` | `jobs/JobsSpec` (job execution disable-enable), `jobs/ScheduledJobSpec` (disable-enable job schedule) | `ui/e2e/j-040-job-toggles.spec.ts` | 3 | missing |
| J-041 | Duplicate job: in the same project and into another project | `/project/$p/job/copy/$id` | `GET /api/V/job/$id`, `POST /api/V/project/$project/jobs/import` | `jobs/DuplicateJobSpec` | `ui/e2e/j-041-job-duplicate.spec.ts` | 3 | missing |
| J-042 | Delete job (confirmation, redirect to job list) | `/project/$p/job/delete/$id` | `DELETE /api/V/job/$id` | `jobs/JobDeleteSpec` | `ui/e2e/j-042-job-delete.spec.ts` | 3 | missing |
| J-043 | Job upload / import and export from the UI: file or pasted definition, format, `dupeOption` (skip message), export | `/project/$p/job/upload`, `/project/$p/jobs` (export) | `POST /api/V/project/$project/jobs/import`, `/api/V/project/$project/jobs/export`, `/api/V/job/$id?format=` | `jobs/ExportImportSpec` | `ui/e2e/j-043-job-upload-export.spec.ts` | 3 | missing |
| J-044 | Job audit fields: `lastModifiedBy` updated after an edit, shown on the job page | `/project/$p/job/show/$id` | `/api/V/job/$id/info`, `/api/V/job/$id/meta` | `jobs/JobAuditApiSpec` | `ui/e2e/j-044-job-audit.spec.ts` | 3 | missing |
| J-045 | Adhoc commands: run a command on the nodes matching a filter, abort, save as job, run from the node browser | `/project/$p/command/run`, `/project/$p/run/` | `POST /api/V/project/$project/run/command`, `/api/V/project/$project/run/script`, `/api/V/project/$project/run/url`, `/api/V/execution/$id/abort`, `/api/V/project/$project/resources` | `execution/CommandSpec`, `execution/CommandOnMultipleNodesSpec`, `nodes/NodesSpec` (a command can be ran from the nodes filter) | `ui/e2e/j-045-adhoc-command.spec.ts` | 3 | missing |
| J-046 | Live execution view: follow running output, nodes view ↔ output view, line wrap, line-number deep links and highlighting, refresh, auto-scroll, large-log warning, two-digit step numbers, node popover | `/project/$p/execution/show/$id`, `/execution/show/$id`, `/project/$p/execution/follow/$id` | `/api/V/execution/$id`, `/api/V/execution/$id/output(.$format)?`, `/api/V/execution/$id/output/state`, `/api/V/execution/$id/output/node/$nodename`, `/api/V/execution/$id/state`, `POST /api/V/execution/$id/abort` | `execution/ExecutionSpec`, `execution/CommandSpec` (nodes / output views, abort in show page), `jobs/LogViewerOutputSpec`, `jobs/steps/LogDataStepSpec` | `ui/e2e/j-046-execution-live-view.spec.ts` | 3 | missing |
| J-047 | Execution view: option values display and re-run with modified options while running | `/project/$p/execution/show/$id` | `/api/V/execution/$id`, `POST /api/V/job/$id/run`, `POST /api/V/job/$id/retry/$executionId` | `execution/ExecutionSpec` (check every option, change options while running) | `ui/e2e/j-047-execution-options-rerun.spec.ts` | 3 | missing |
| J-048 | Execution view: action menu according to authorizations (delete, re-run, …) and HTML-rendered output tab | `/project/$p/execution/show/$id` | `/api/V/authorizations/project/$project/$type/$specifier`, `DELETE /api/V/execution/$id` | `execution/ExecutionShowAuthSpec`, `jobs/JobTabsSpec` (job log html tab) | `ui/e2e/j-048-execution-actions-auth.spec.ts` | 3 | missing |
| J-049 | Activity page: execution list with max rows, filters, running executions, bulk delete according to authorizations | `/project/$p/activity`, `/project/$p/history`, `/project/$p/events/$action?/$id?` | `/api/V/project/$project/executions`, `/api/V/project/$project/executions/running`, `/api/V/project/$project/history`, `POST /api/V/executions/delete`, `/api/V/project/$project/executions/metrics` | `activity/ActivitySpec`, `jobs/ActivitySectionAuthSpec` | `ui/e2e/j-049-activity.spec.ts` | 3 | missing |
| J-050 | Job activity history reached from the job list and from the activity page | `/project/$p/jobs` (activity section), `/project/$p/activity?jobIdFilter=$id` | `/api/V/job/$id/executions`, `/api/V/project/$project/executions` | `jobs/JobActivityHistorySpec` | `ui/e2e/j-050-job-activity-history.spec.ts` | 3 | missing |
| J-051 | Execution history auto-cleanup configured in project settings and visible in the activity list | `/project/$p/configure` (execution history clean), `/project/$p/activity` | `PUT /api/V/project/$project/config/$keypath**`, `/api/V/project/$project/executions` | `execution/ExecutionSpec` (auto execution clean up) | `ui/e2e/j-051-execution-cleanup.spec.ts` | 3 | missing |
| J-052 | Job timeout: execution ends with `timedout` status and the step is marked failed | `/project/$p/execution/show/$id` | `/api/V/execution/$id`, `/api/V/execution/$id/state` | `jobs/JobsSpec` (job timeout should finish job with timeout status …) | `ui/e2e/j-052-job-timeout.spec.ts` | 3 | missing |
| J-053 | Project execution mode: disable executions / schedules at project level (and schedule the change), badges on job list, activity and dashboard | `/project/$p/configure`, `/project/$p/configure/executionLater`, `/project/$p/configure/executionLater/nextTime` | `PUT /api/V/project/$project/config/$keypath**`, `POST /api/V/project/$project/enable/later`, `POST /api/V/project/$project/disable/later` | `project/ExecutionModeSpec` | `ui/e2e/j-053-project-execution-mode.spec.ts` | 3 | missing |
| J-054 | Webhooks admin: enable, create, configure the event plugin, token, delete, inclusion in project export | `/webhook/admin`, `/webhook/admin/editorData/$project`, `/webhook/admin/save`, `/webhook/admin/delete/$id` | `/api/V/project/$project/webhooks`, `GET/POST/DELETE /api/V/project/$project/webhook/$id?`, `POST /api/V/webhook/$authtoken` | `webhook/WebhooksSpec` | `ui/e2e/j-054-webhooks.spec.ts` | 4 | missing |
| J-055 | SCM setup: configure export / import plugins, enable / disable, clean | `/project/$p/scm/$integration/setup`, `/project/$p/scm/$integration/index`, `/project/$p/scm/$integration/disable`, `/project/$p/scm/$integration/enable`, `/project/$p/scm/$integration/clean` | `/api/V/project/$project/scm/$integration/plugins`, `/api/V/project/$project/scm/$integration/plugin/$type/input`, `/api/V/project/$project/scm/$integration/plugin/$type/setup`, `/api/V/project/$project/scm/$integration/plugin/$type/enable`, `/api/V/project/$project/scm/$integration/plugin/$type/disable`, `/api/V/project/$project/scm/$integration/config`, `/api/V/project/$project/scm/$integration/status`, `/api/V/project/$project/scm/toggle` | `scm/ScmImportSpec`, `scm/ScmStatusBadgeSpec` | `ui/e2e/j-055-scm-setup.spec.ts` | 4 | missing |
| J-056 | SCM actions: import / export commits with action inputs, job diff | `/project/$p/scm/$integration/performAction`, `/project/$p/job/$id/scm/$integration/$action`, `/project/$p/scm/$integration/diff` | `/api/V/project/$project/scm/$integration/action/$actionId`, `/api/V/project/$project/scm/$integration/action/$actionId/input`, `/api/V/job/$id/scm/$integration/action/$actionId`, `/api/V/job/$id/scm/$integration/action/$actionId/input`, `/api/V/job/$id/scm/$integration/diff` | `scm/ScmImportSpec`, `scm/ScmStatusBadgeSpec` | `ui/e2e/j-056-scm-actions.spec.ts` | 4 | missing |
| J-057 | SCM status badges on the job page and job list actions | `/project/$p/job/show/$id`, `/project/$p/jobs` | `/api/V/job/$id/scm/$integration/status`, `/api/V/project/$project/scm/$integration/status` | `scm/ScmStatusBadgeSpec` | `ui/e2e/j-057-scm-status-badge.spec.ts` | 4 | missing |
| J-058 | Users list and user administration: create profile, edit, expand details (groups, NOT SET fields) | `/user/list`, `/user/register`, `/user/edit` | `/api/V/user/list`, `/api/V/user/info/$username?` | `users/UserListSpec` | `ui/e2e/j-058-user-list.spec.ts` | 4 | missing |
| J-059 | User summary: logged-in users, search by name | `/menu/userSummary` | `/api/V/user/list` | `users/UserSummarySpec` | `ui/e2e/j-059-user-summary.spec.ts` | 4 | missing |
| J-060 | System configuration and security configuration pages | `/menu/systemConfig`, `/menu/securityConfig` | `/api/V/system/info`, `/api/V/feature` | `navigation/NavigationSpec` (visits System Configuration) | `ui/e2e/j-060-system-config.spec.ts` | 4 | missing |
| J-061 | System report: system info, health and metrics | `/menu/systemInfo`, `/health`, `/monitoring/health`, `/monitoring/metrics`, `/monitoring/prometheus` | `/api/V/system/info`, `/api/V/metrics/$name**?`, `/api/V/monitoring/$name**?` | no upstream test | `ui/e2e/j-061-system-report.spec.ts` | 4 | missing |
| J-062 | Log storage: status, incomplete executions, resume | `/menu/logStorage` | `/api/V/system/logstorage`, `/api/V/system/logstorage/incomplete`, `POST /api/V/system/logstorage/incomplete/resume` | no upstream test | `ui/e2e/j-062-log-storage.spec.ts` | 4 | missing |
| J-063 | System execution mode: active / passive, schedule a mode change | `/menu/executionMode`, `/menu/executionMode/executionLater`, `/menu/executionMode/executionLater/nextTime` | `/api/V/system/executions/status`, `POST /api/V/system/executions/enable`, `/api/V/system/executions/disable`, `/api/V/system/executions/enable/later`, `/api/V/system/executions/disable/later` | no upstream test | `ui/e2e/j-063-system-execution-mode.spec.ts` | 4 | missing |
| J-064 | Scheduler / cluster view: jobs scheduled on this and other servers, takeover (new page; legacy exposes this through the API only) | none in the legacy UI | `/api/V/scheduler/jobs`, `/api/V/scheduler/server/$uuid/jobs`, `PUT /api/V/scheduler/takeover` | no upstream test | `ui/e2e/j-064-scheduler-cluster.spec.ts` | 4 | missing |
| J-065 | Plugins: installed plugin catalog, repository browse / search / upload / install / uninstall, plugin configuration | `/menu/plugins`, `/artifact/index/configurations`, `/artifact/index/upload`, `/repository/*`, `/plugin/list`, `/plugin/listByService`, `/plugin/providers/$service`, `/plugin/detail/$service/$provider`, `/plugin/validate/$service/$name`, `/plugin/icon/$service/$name`, `/plugin/i18n/$service/$name/$path**` | `/api/V/plugin/list`, `/api/V/plugin/detail/$service/$provider`, `/api/V/plugins/types`, `/api/V/plugins/list`, `/api/V/plugins/search`, `/api/V/plugins/upload`, `/api/V/plugins/install/$artifactId/$artifactVersion?`, `/api/V/plugins/uninstall/$artifactId`, `/api/V/repository/list`, `/api/V/repository/artifacts/list` (all 26 plugin-API rows `P-004`–`P-029` of `PARITY.md`) | no upstream test | `ui/e2e/j-065-plugins-catalog.spec.ts` | 4 | missing |
| J-066 | Project settings: plugin groups and per-project plugin configuration | `/project/$p/configure` (plugin groups) | `GET/POST /api/V/project/$project/configurable`, `POST /api/V/project/$project/plugins/save` | no upstream test | `ui/e2e/j-066-project-plugin-groups.spec.ts` | 4 | missing |
| J-067 | Password utility: encrypt a value with a `PasswordUtilityEncrypter` plugin | `/passwordUtility`, `/passwordUtility/encode` | `/api/V/plugin/list` (PasswordUtilityEncrypter) | no upstream test | `ui/e2e/j-067-password-utility.spec.ts` | 4 | missing |
| J-068 | Welcome / first-run page and licenses page | `/menu/welcome`, `/menu/licenses` | `/api/V/system/info` | no upstream test | `ui/e2e/j-068-welcome-licenses.spec.ts` | 5 | missing |
| J-069 | Community news, help links, version display, guided tours, plugin search (API shapes kept per MISSION §1.5) | `/community-news`, `/helplink/name`, `/tour/listAll`, `/tour/list/$loaderName`, `/tour/get/$loaderName/$tour`, `/search-plugins` | none beyond the UI routes listed | no upstream test | `ui/e2e/j-069-help-news-tours.spec.ts` | 5 | missing |
| J-070 | RSS activity feed | `/feed` | `/api/V/project/$project/history` | no upstream test | `ui/e2e/j-070-rss-feed.spec.ts` | 5 | missing |
| J-071 | Workflow graph page (standalone) → workflow graph inside job show / editor | `/workflowgraph/show` | `/api/V/job/$id/workflow` | no upstream test | `ui/e2e/j-071-workflow-graph.spec.ts` | 5 | missing |
| J-072 | Global search / command palette (new in rdx, MISSION §3.8) | none (new) | `/api/V/projects`, `/api/V/project/$project/jobs`, `/api/V/project/$project/resources` | no upstream test | `ui/e2e/j-072-command-palette.spec.ts` | 5 | missing |
| J-073 | Execution output download and rendered output (text / HTML, ANSI colors) | `/project/$p/execution/downloadOutput/$id`, `/project/$p/execution/renderOutput/$id` | `/api/V/execution/$id/output(.$format)?` | no upstream test | `ui/e2e/j-073-execution-output-download.spec.ts` | 3 | missing |

Totals: 73 journeys — phase 1: 8 · phase 2: 19 · phase 3: 27 · phase 4: 14 · phase 5: 5. Journeys with an upstream
Selenium spec: 56; without ("no upstream test"): 17. Every one of the 57 Selenium specs is referenced by at least one journey
(`scripts/inventory/README.md` has the check).

## 2. Deep links that must keep resolving (MISSION §1.6)

| Legacy route (`UrlMappings.groovy` line) | Journey |
|---|---|
| `/project/$p/job/show/$id` (302), `/project/$p/job/show/$id/$fullName**` (301), `/job/show/$id` (348) | J-039 |
| `/project/$p/execution/show/$id` (329), `/execution/show/$id` (349) | J-046 |
| `/project/$p/jobs` (300), `/project/$p/jobs/$groupPath**` (299) | J-028 |
| `/project/$p/nodes/` (292; the mapping carries a trailing slash), `/project/$p/run/` (293) | J-021 |
| `/project/$p/activity` (297), `/project/$p/history` (298) | J-049 |
| `/project/$p/home` (291) | J-011 |
| `/menu/*` (generic `/$controller/$action?/$id?` mapping, line 30, + `MenuController` actions) | J-003, J-009, J-022, J-023, J-059, J-060, J-061, J-062, J-063, J-065, J-068 |
| `/user/login` (line 30 + `UserController.login`, `application.groovy:178`) | J-001 |
| `/resources/*` (311; `/resources/createProject` 308) | J-010, J-016 |

## 3. GSP page templates (non-partial `*.gsp`) → journey

Partials (`_*.gsp`) are not listed; they are rendered inside these pages. Layouts: `layouts/base.gsp`, `layouts/main.gsp`.

| Directory | Page templates | Journey |
|---|---|---|
| `common/` | `error.gsp`, `execUnauthorized.gsp` | J-008 |
| `communityNews/` | `index.gsp` | J-069 |
| `execution/` | `show.gsp`, `showFragment.gsp`; `mailNotification/status.gsp` (email body) | J-046, J-047, J-048, J-073 (mail: behavior row notifications) |
| `feed/` | `index.gsp` | J-070 |
| `framework/` | `adhoc.gsp`, `adhocNext.gsp` | J-045 |
| `framework/` | `createProject.gsp` | J-010 |
| `framework/` | `editProject.gsp`, `editProjectConfig.gsp`, `editProjectFile.gsp` | J-013, J-014, J-015, J-016, J-017, J-018, J-053, J-066 |
| `framework/` | `nodes.gsp`, `projectSelect.gsp` | J-021, J-009 |
| `framework/` | `projectNodeSources.gsp`, `editProjectNodeSources.gsp`, `editProjectNodeSourceFile.gsp`, `createResourceModelConfig.gsp`, `viewResourceModelConfig.gsp` | J-019, J-020 |
| `menu/` | `home.gsp`, `home.next.gsp`, `projectHome.gsp`, `welcome.gsp`, `wait.gsp` | J-009, J-011, J-068 |
| `menu/` | `jobs.gsp`, `jobs.next.gsp`, `jobsFragment.gsp`, `jobsPicker.gsp` | J-028, J-029, J-037 |
| `menu/` | `acls.gsp`, `createSystemAclFile.gsp`, `editSystemAclFile.gsp` | J-023 |
| `menu/` | `projectAcls.gsp`, `createProjectAclFile.gsp`, `editProjectAclFile.gsp` | J-024 |
| `menu/` | `projectExport.gsp`, `projectImport.gsp`, `projectDelete.gsp` | J-025, J-026, J-027 |
| `menu/` | `storage.gsp` | J-022 |
| `menu/` | `executionMode.gsp`, `logStorage.gsp`, `systemConfig.gsp`, `systemInfo.gsp`, `licenses.gsp`, `plugins.gsp`, `userSummary.gsp` | J-063, J-062, J-060, J-061, J-068, J-065, J-059 |
| `passwordUtility/` | `index.gsp` | J-067 |
| `reports/` | `index.gsp` | J-049, J-050 |
| `scheduledExecution/` | `create.gsp`, `edit.gsp`, `show.gsp`, `delete.gsp`, `upload.gsp`, `runbook.gsp` | J-031, J-032–J-038, J-039, J-042, J-043 |
| `scm/` | `index.gsp`, `setup.gsp`, `performAction.gsp`, `diff.gsp` | J-055, J-056 |
| `searchPlugins/` | `index.gsp` | J-069 |
| `user/` | `login.gsp`, `loggedout.gsp`, `profile.gsp`, `edit.gsp`, `list.gsp`, `register.gsp` | J-001, J-005, J-006, J-058 |
| `workflow/` | `edit.gsp`, `editStepFilter.gsp` | J-033 |
| plugin `grails-webhooks/.../webhook/admin.gsp` | | J-054 |
| plugin `grails-repository/.../artifact/index.gsp` | | J-065 |
| plugin `grails-*/.../{index,error,notFound}.gsp`, `layouts/main.gsp` | scaffold pages of each Grails plugin, never served by `rdx` | — (deviated by construction; see `docs/COMPAT.md`) |

## 4. SPA page bundles (`vue.config.app.js` `pages/*`) → journey

| Bundle | Journey |
|---|---|
| `pages/login` | J-001 |
| `pages/home` | J-009 |
| `pages/project-dashboard` | J-011 |
| `pages/project-config` (plugin groups) | J-066 |
| `pages/project-nodes-config`, `pages/project-nodes-editor` | J-019, J-020 |
| `pages/nodes` | J-021 |
| `pages/storage` | J-022 |
| `pages/job/browse` | J-028, J-029, J-057 |
| `pages/job/editor` | J-031–J-038 |
| `pages/job/show`, `pages/job/head/scm-action-buttons`, `pages/job/head/scm-status-badge` | J-039, J-040, J-057 |
| `pages/job/upload` | J-043 |
| `pages/adhoc`, `pages/command` | J-045 |
| `pages/execution-show` | J-046, J-047, J-048 |
| `pages/project-activity` | J-049, J-050 |
| `pages/webhooks` | J-054 |
| `pages/user-list` | J-058 |
| `pages/user-summary` (entry `pages/menu/main.js`) | J-059 |
| `pages/repository` (vue-router: plugin repository, upload, configuration views) | J-065 |
| `pages/dynamic-form` | J-014, J-015, J-065 (plugin property forms) |
| `pages/community-news` | J-069 |
| `components/*` bundles (central, navbar, mainbar, motd, readme-motd, project-picker, theme, tour, version, first-run, server-identity, copybox, ko-paginator, uisockets, community-news-notification) | shell pieces of J-003, J-004, J-007, J-018, J-068, J-069 |
