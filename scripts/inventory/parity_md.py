#!/usr/bin/env python3
"""Generate the Phase 0 inventory `PARITY.md` from the legacy tree (one-shot generator).

Usage:  python3 -I scripts/inventory/parity_md.py [--root <repo>] > PARITY.md

Every row starts as `missing`. The script is meant to be run ONCE at bootstrap: later sessions update the
status / oracle / last-run columns by hand, and re-running it would overwrite them (it prints a warning on
stderr when a `PARITY.md` with non-missing rows exists). The generated sections and their sources:

* API routes (main app / plugins): `routes.py` (UrlMappings.groovy) joined with `oracle_map.py`.
* Web routes / deep links: non-API mappings of `routes.py` plus the pages reached through the generic
  `/$controller/$action?/$id?` mapping (hand-verified controller actions, cited with file:line).
* Service types: the constants of `ServiceNameConstants.java`.
* Built-in plugins: `legacy/plugins/*/` with the `@Plugin(service=..., name=...)` annotations found in each
  (constant names are resolved to their literal values when they are defined in the same plugin or in core).
* Domain classes: `legacy/rundeckapp/grails-app/domain/**` + `legacy/grails-webhooks/.../domain/**`, with the
  table created for them by the Liquibase changelogs under `legacy/rundeckapp/grails-app/migrations/core/`.
* File formats and behaviors: the items of MISSION.md §1.2 / §1.3 with the legacy path of each (tables below,
  hand-verified against the tree on tag v6.3.0).
* Journeys: the table of `specs/ui-journeys.md`.
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oracle_map  # noqa: E402
import routes  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MAIN = "legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy"
API_SPECS = "legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/api"

# --------------------------------------------------------------------------------------------------------
# Hand-verified tables (paths relative to the repository root, checked on tag v6.3.0)
# --------------------------------------------------------------------------------------------------------

# Pages reached through the convention mapping `/$controller/$action?/$id?` (UrlMappings.groovy:30) or through
# the `/project/$project/job/$action?/$id?` (307), `/project/$project/execution/$action/$id` (330),
# `/project/$project/scm/$integration?/$action?` (295) and `/resources/$action?/$id?` (311) mappings.
# (pattern, methods, controller.action, evidence, note)
GENERIC_WEB_ROUTES = [
    ("/user/login", "GET", "user.login", "UrlMappings.groovy:30; UserController.groovy:108; conf/application.groovy:178 (loginFormUrl)", "deep link (MISSION §1.6)"),
    ("/j_security_check", "POST", "Spring Security form login", "conf/application.groovy:119,146,175 (filterProcessesUrl)", "form login endpoint (MISSION §1.1)"),
    ("/user/logout", "GET,POST", "Spring Security logout (UserController.logout:92 legacy)", "conf/application.groovy:179 (logout.filterProcessesUrl)", ""),
    ("/user/loggedout", "GET", "user.loggedout", "UrlMappings.groovy:30; UserController.groovy:97; conf/application.groovy:180 (afterLogoutUrl)", ""),
    ("/user/profile", "GET", "user.profile", "UrlMappings.groovy:30; UserController.groovy:131", ""),
    ("/user/edit", "GET", "user.edit", "UrlMappings.groovy:30; UserController.groovy:832", ""),
    ("/user/list", "GET", "user.list", "UrlMappings.groovy:30; UserController.groovy:127", ""),
    ("/user/register", "GET", "user.register", "UrlMappings.groovy:30; UserController.groovy:194", ""),
    ("/user/generateUserToken", "POST", "user.generateUserToken", "UrlMappings.groovy:30; UserController.groovy:839", "UI token creation"),
    ("/user/clearApiToken", "POST", "user.clearApiToken", "UrlMappings.groovy:30; UserController.groovy:1065", ""),
    ("/user/removeExpiredTokens", "POST", "user.removeExpiredTokens", "UrlMappings.groovy:30; UserController.groovy:992", ""),
    ("/menu/index", "GET", "menu.index", "UrlMappings.groovy:30; MenuController.groovy:199", "same as `/`"),
    ("/menu/home", "GET", "menu.home", "UrlMappings.groovy:30; MenuController.groovy:1830", "deep link `/menu/*`"),
    ("/menu/projectHome", "GET", "menu.projectHome", "UrlMappings.groovy:30; MenuController.groovy:1874", "also `/project/$project/home`"),
    ("/menu/jobs", "GET", "menu.jobs", "UrlMappings.groovy:30; MenuController.groovy:237", "also `/project/$project/jobs`"),
    ("/menu/jobsPicker", "GET", "menu.jobsPicker", "UrlMappings.groovy:30; MenuController.groovy:472", "job picker modal content"),
    ("/menu/acls", "GET", "menu.acls", "UrlMappings.groovy:30; MenuController.groovy:1317", "system ACL management"),
    ("/menu/executionMode", "GET", "menu.executionMode", "UrlMappings.groovy:30; MenuController.groovy:668", ""),
    ("/menu/storage", "GET", "menu.storage", "UrlMappings.groovy:30; MenuController.groovy:676", "also `/menu/storage/$resourcePath**`"),
    ("/menu/logStorage", "GET", "menu.logStorage", "UrlMappings.groovy:30; MenuController.groovy:747", ""),
    ("/menu/systemConfig", "GET", "menu.systemConfig", "UrlMappings.groovy:30; MenuController.groovy:912", ""),
    ("/menu/securityConfig", "GET", "menu.securityConfig", "UrlMappings.groovy:30; MenuController.groovy:921", ""),
    ("/menu/systemInfo", "GET", "menu.systemInfo", "UrlMappings.groovy:30; MenuController.groovy:1664", ""),
    ("/menu/licenses", "GET", "menu.licenses", "UrlMappings.groovy:30; MenuController.groovy:1822", ""),
    ("/menu/plugins", "GET", "menu.plugins", "UrlMappings.groovy:30; MenuController.groovy:1826", ""),
    ("/menu/welcome", "GET", "menu.welcome", "UrlMappings.groovy:30; MenuController.groovy:1881", "first-run page"),
    ("/menu/userSummary", "GET", "menu.userSummary", "UrlMappings.groovy:30; MenuController.groovy:3864", ""),
    ("/resources/nodes", "GET", "framework.nodes", "UrlMappings.groovy:311; FrameworkController.groovy:209", "deep link `/resources/*`; also `/project/$project/nodes/`"),
    ("/resources/adhoc", "GET", "framework.adhoc", "UrlMappings.groovy:311; FrameworkController.groovy:276", "also `/project/$project/command/run`"),
    ("/resources/editProject", "GET", "framework.editProject", "UrlMappings.groovy:311; FrameworkController.groovy:2538", "also `/project/$project/configure`"),
    ("/resources/editProjectFile", "GET,POST", "framework.editProjectFile", "UrlMappings.groovy:311; FrameworkController.groovy:2645", "readme.md / motd.md editor"),
    ("/resources/editProjectConfig", "GET,POST", "framework.editProjectConfig", "UrlMappings.groovy:311; FrameworkController.groovy:2735", "raw project.properties editor"),
    ("/resources/saveProject", "POST", "framework.saveProject", "UrlMappings.groovy:311; FrameworkController.groovy:1245", ""),
    ("/resources/saveProjectConfig", "POST", "framework.saveProjectConfig", "UrlMappings.groovy:311; FrameworkController.groovy:1012", ""),
    ("/resources/viewResourceModelConfig", "GET", "framework.viewResourceModelConfig", "UrlMappings.groovy:311; FrameworkController.groovy:2959", ""),
    ("/resources/editResourceModelConfig", "GET", "framework.editResourceModelConfig", "UrlMappings.groovy:311; FrameworkController.groovy:2923", ""),
    ("/resources/nodesFragment", "GET", "framework.nodesFragment", "UrlMappings.groovy:311; FrameworkController.groovy:659", "ajax fragment of the node browser"),
    ("/project/$project/job/create", "GET", "scheduledExecution.create", "UrlMappings.groovy:307; ScheduledExecutionController.groovy:2629", ""),
    ("/project/$project/job/edit/$id", "GET", "scheduledExecution.edit", "UrlMappings.groovy:307; ScheduledExecutionController.groovy:2396", ""),
    ("/project/$project/job/copy/$id", "GET", "scheduledExecution.copy", "UrlMappings.groovy:307; ScheduledExecutionController.groovy:2515", "duplicate job"),
    ("/project/$project/job/delete/$id", "GET,POST", "scheduledExecution.delete", "UrlMappings.groovy:307; ScheduledExecutionController.groovy:1533", ""),
    ("/project/$project/job/runbook/$id", "GET", "scheduledExecution.runbook", "UrlMappings.groovy:307; ScheduledExecutionController.groovy:652", ""),
    ("/project/$project/job/save", "POST", "scheduledExecution.save", "UrlMappings.groovy:307; ScheduledExecutionController.groovy:3076", "legacy form post of the job editor"),
    ("/project/$project/job/update", "POST", "scheduledExecution.update", "UrlMappings.groovy:307; ScheduledExecutionController.groovy:2439", "legacy form post of the job editor"),
    ("/project/$project/job/runAdhocInline", "POST", "scheduledExecution.runAdhocInline", "UrlMappings.groovy:307; ScheduledExecutionController.groovy:2813", "adhoc page submit (also `/api/*/project/$project/run/command/inline`)"),
    ("/project/$project/execution/follow/$id", "GET", "execution.follow", "UrlMappings.groovy:330; ExecutionController.groovy:126", "live view"),
    ("/project/$project/execution/downloadOutput/$id", "GET", "execution.downloadOutput", "UrlMappings.groovy:330; ExecutionController.groovy:702", ""),
    ("/project/$project/execution/renderOutput/$id", "GET", "execution.renderOutput", "UrlMappings.groovy:330; ExecutionController.groovy:769", "HTML rendered output"),
    ("/project/$project/execution/tailExecutionOutput/$id", "GET", "execution.tailExecutionOutput", "UrlMappings.groovy:330; ExecutionController.groovy:1538", "ajax log tail (UI-only)"),
    ("/project/$project/execution/ajaxExecState/$id", "GET", "execution.ajaxExecState", "UrlMappings.groovy:330; ExecutionController.groovy:375", "ajax state (UI-only)"),
    ("/project/$project/execution/cancelExecution/$id", "POST", "execution.cancelExecution", "UrlMappings.groovy:330; ExecutionController.groovy:573", "UI abort"),
    ("/project/$project/execution/delete/$id", "POST", "execution.delete", "UrlMappings.groovy:330; ExecutionController.groovy:326", ""),
    ("/project/$project/execution/bulkDelete", "POST", "execution.bulkDelete", "UrlMappings.groovy:30; ExecutionController.groovy:349", "activity page bulk delete"),
    ("/project/$project/scm/$integration/index", "GET", "scm.index", "UrlMappings.groovy:295; ScmController.groovy:270", ""),
    ("/project/$project/scm/$integration/setup", "GET,POST", "scm.setup / scm.saveSetup", "UrlMappings.groovy:295; ScmController.groovy:301,331", ""),
    ("/project/$project/scm/$integration/enable", "POST", "scm.enable", "UrlMappings.groovy:295; ScmController.groovy:868", ""),
    ("/project/$project/scm/$integration/disable", "POST", "scm.disable", "UrlMappings.groovy:295; ScmController.groovy:801", ""),
    ("/project/$project/scm/$integration/clean", "POST", "scm.clean", "UrlMappings.groovy:295; ScmController.groovy:834", ""),
    ("/project/$project/scm/$integration/performAction", "GET,POST", "scm.performAction / scm.performActionSubmit", "UrlMappings.groovy:295; ScmController.groovy:1643,1770", ""),
    ("/project/$project/scm/$integration/diff", "GET", "scm.diff", "UrlMappings.groovy:295; ScmController.groovy:2570", ""),
    ("/feed", "GET", "feed.index", "UrlMappings.groovy:30; FeedController.groovy:27", "RSS activity feed"),
    ("/health", "GET", "health.index", "UrlMappings.groovy:30; HealthController.groovy:5", ""),
    ("/passwordUtility", "GET", "passwordUtility.index", "UrlMappings.groovy:30; PasswordUtilityController.groovy:19", ""),
    ("/passwordUtility/encode", "POST", "passwordUtility.encode", "UrlMappings.groovy:30; PasswordUtilityController.groovy:33", ""),
    ("/workflow/$action", "GET,POST", "workflow.* (edit, copy, editStepFilter, saveStepFilter, validateStepFilter, removeStepFilter, renderItem, save, reorder, undo, redo, revert, renderUndo)", "UrlMappings.groovy:30; WorkflowController.groovy:91-744", "legacy job-editor ajax; the rebuilt editor does not need it (ADR-0004)"),
    ("/editOpts/$action", "GET,POST", "editOpts.* (index, edit, renderOpt, renderAll, renderSummary, save, remove, duplicate, reorder, renderUndo, undo, redo, revert)", "UrlMappings.groovy:30; EditOptsController.groovy:78-511", "legacy job-editor ajax; the rebuilt editor does not need it (ADR-0004)"),
]

# MISSION §1.2 items: (id slug, item, legacy paths, oracle evidence)
FILE_FORMATS = [
    ("Job definition XML (import/export, `dupeOption`/`uuidOption`, UUID handling)",
     "legacy/rundeckapp/grails-app/utils/rundeck/codecs/JobsXMLCodec.groovy; legacy/rundeckapp/src/main/groovy/org/rundeck/app/components/RundeckJobDefinitionManager.groovy; ScheduledExecutionController.groovy:3191 (dupeOption/uuidOption), ScheduledExecutionService.groovy:2053 (loadJobs)",
     "JobsImportSpec, JobsExportSpec, ConditionalWorkflowSpec (`format=xml`)"),
    ("Job definition YAML",
     "legacy/rundeckapp/grails-app/utils/rundeck/codecs/JobsYAMLCodec.groovy; RundeckJobDefinitionManager.groovy (`exportAs('yaml')`)",
     "JobsImportSpec, JobsExportSpec, JobsSpec, JobExecutionSpec, JobOptionValuesUrlGlobalsSpec, ConditionalWorkflowSpec (`format=yaml`)"),
    ("Job definition JSON (API shape)",
     "legacy/rundeckapp/src/main/groovy/org/rundeck/app/components/RundeckJobDefinitionManager.groovy (`exportAs('json')`); legacy/core/src/main/java/org/rundeck/app/components/jobs/JobFormat.java",
     "JobsImportSpec, JobsExportSpec, ConditionalWorkflowSpec (`format=json`)"),
    ("Node resources XML (`resources.xml`)",
     "legacy/core/src/main/java/com/dtolabs/rundeck/core/resources/format/ResourceXMLFormatParser.java, ResourceXMLFormatGenerator.java",
     "ConfigSpec, NodesSpec (`/project/$project/resources`)"),
    ("Node resources YAML (`resources.yaml`)",
     "legacy/core/src/main/java/com/dtolabs/rundeck/core/resources/format/ResourceYamlFormatParser.java, ResourceYamlFormatGenerator.java",
     "ConfigSpec (`/project/$project/resource/$name?format=yaml`)"),
    ("Node resources JSON (`resources.json`)",
     "legacy/core/src/main/java/com/dtolabs/rundeck/core/resources/format/json/ResourceJsonFormatParser.java, ResourceJsonFormatGenerator.java",
     "AnsibleResourceModelSpec, ConfigSpec (`/project/$project/resources`)"),
    ("Node filter language (node attributes, tags, regex, include/exclude)",
     "legacy/core/src/main/java/com/dtolabs/rundeck/core/utils/NodeSet.java; legacy/core/src/main/java/com/dtolabs/rundeck/core/common/NodeFilter.java",
     "NodesSpec, RunCommandSpec, ExecutionSpec, JobExecutionSpec (`filter=`)"),
    ("ACL policy YAML (`*.aclpolicy`) and evaluation semantics",
     "legacy/rundeck-authz/rundeck-authz-yaml; legacy/rundeck-authz/rundeck-authz-core; legacy/rundeckapp/grails-app/services/rundeck/services/AclFileManagerService.groovy",
     "SystemAclCreateSpec, ExecutionsQueryViewAuthSpec, ExecutionsQueryViewHistoryAuthSpec, AuthorizationsSpec"),
    ("`rundeck-config.properties`",
     "legacy/packaging/lib/common/etc/rundeck/rundeck-config.properties (template); legacy/rundeckapp/grails-app/services/rundeck/services/ConfigurationService.groovy; legacy/docker/official/remco/templates/rundeck-config.properties",
     "none"),
    ("`framework.properties`",
     "legacy/packaging/lib/common/etc/rundeck/framework.properties; legacy/core/src/main/java/com/dtolabs/rundeck/core/common/Framework.java, FrameworkFactory.java; legacy/core/src/main/java/com/dtolabs/rundeck/core/utils/PropertyLookup.java",
     "none"),
    ("`project.properties` (incl. `rundeck.server.uuid`, cluster mode keys)",
     "legacy/packaging/lib/common/etc/rundeck/project.properties; legacy/core/src/main/java/com/dtolabs/rundeck/core/common/FrameworkProjectConfig.java, FrameworkProject.java; legacy/rundeckapp/grails-app/services/rundeck/services/ProjectManagerService.groovy",
     "ConfigSpec (`/project/$project/config`)"),
    ("`realm.properties` (every credential format of `PropertyFileLoginModule`)",
     "legacy/packaging/lib/common/etc/rundeck/realm.properties; legacy/rundeckapp/src/main/java/org/rundeck/jaas/PropertyFileLoginModule.java; legacy/rundeckapp/src/main/groovy/org/rundeck/jaas/jetty/{ReloadablePropertyFileLoginModule,JettyAuthPropertyFileLoginModule,JettyRolePropertyFileLoginModule}.java",
     "BasicSpec, UnauthorizedSpec (login with the default realm); Selenium login/BasicLoginSpec"),
    ("`jaas-loginmodule.conf` (JAAS syntax; modules PropertyFile, LDAP, LDAP combined, PAM, JNDI)",
     "legacy/packaging/lib/common/etc/rundeck/jaas-loginmodule.conf; legacy/docker/official/remco/templates/jaas-loginmodule.conf; legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/jetty/jaas/{JettyCachingLdapLoginModule,JettyCombinedLdapLoginModule,JNDILoginModule}.java; legacy/rundeckapp/src/main/groovy/org/rundeck/jaas/jetty/JettyPamLoginModule.java",
     "LdapRolesApiSpec (@LdapTest), JdbcRolesApiSpec (@JdbcTest)"),
    ("`log4j2.properties` (accepted; mapped to `tracing`)",
     "legacy/packaging/lib/common/etc/rundeck/log4j2.properties; legacy/docker/official/remco/templates/log4j2.properties",
     "none"),
    ("Execution log `.rdlog` format (`text/x-rundeck-log-v2.0`)",
     "legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/internal/RundeckLogFormat.java:44-56 (FORMAT_MIME, LOG_FILE_FILETYPE); legacy/rundeckapp/grails-app/services/rundeck/services/LoggingService.groovy, logging/ExecutionLogReader.groovy",
     "ExecutionOutputSpec (@APIExecOutputTest), ExecutionSpec, JobExecutionSpec (`/execution/$id/output`)"),
    ("Key storage layout: filesystem backend (path + metadata files) and DB backend (`storage` table)",
     "legacy/rundeck-storage/rundeck-storage-filesys/src/main/java/org/rundeck/storage/data/file/{FileTree,DirectFilepathMapper,MetadataMapper}.java; legacy/rundeck-storage/rundeck-storage-conf; legacy/rundeckapp/grails-app/services/rundeck/services/DbStorageService.groovy; legacy/rundeckapp/grails-app/domain/rundeck/Storage.groovy",
     "PrivateKeySpec, PublicKeySpec (`/storage/keys`)"),
    ("Storage converter semantics (AES-GCM encryption, jasypt alias, timestamper)",
     "legacy/core/src/main/java/com/dtolabs/rundeck/core/storage/{StorageConverterPluginAdapter,StorageTimestamperConverter,TreeStorageManager}.java; legacy/plugins/aes-gcm-encryption-plugin; legacy/encryption-core",
     "EncryptionBackwardCompatSpec"),
    ("Project archive zip (export/import: jobs, executions, configs, ACLs, readme/motd, scm, webhooks)",
     "legacy/rundeckapp/grails-app/services/rundeck/services/ProjectService.groovy:794 (exportProjectToOutputStream), :1120 (importToProject), :514 (exportProjectToFileAsync), :2122 (handleApiImport); services/asyncimport/AsyncImportService.groovy",
     "ExportSpec, ExecExportSpec, ImportSpec"),
    ("Script plugin zip + `plugin.yaml` contract (providers NodeExecutor, FileCopier, ResourceModelSource, WorkflowStep, WorkflowNodeStep, Notification, …)",
     "legacy/core/src/main/java/com/dtolabs/rundeck/core/plugins/{ScriptPluginProviderLoader,ScriptPluginProvider,ScriptPluginProviderImpl,ScriptPluginScanner,PluginMetadata,ZipResourceLoader}.java; legacy/core/src/main/java/com/dtolabs/rundeck/core/resources/ScriptPluginResourceModelSource.java; legacy/plugins/script-plugin",
     "PluginSpec (`/plugin/list`); the Phase 3 script-plugin fixture is the oracle for the loader"),
    ("Execution state file (`state.json`) and output-state endpoint",
     "legacy/rundeckapp/grails-app/services/rundeck/services/workflow/{DefaultStateExecutionFileProducer,DefaultWorkflowStateDataLoader,StateMapping}.groovy; services/logging/WorkflowStateFileLoader.groovy",
     "ExecutionSpec, JobExecutionSpec (`/execution/$id/state`)"),
]

# MISSION §1.1 + §1.3 behaviors, split into named sub-items: (item, legacy paths, oracle evidence)
BEHAVIORS = [
    # §1.1 contracts that are behaviors of every endpoint
    ("API version negotiation 14→60 (`X-Rundeck-API-Version`, `api.error.api-version.unsupported`, per-version switches)",
     "legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/api/ApiVersions.groovy:60,68,69; legacy/rundeckapp/grails-app/services/rundeck/services/ApiService.groovy:1111-1128 (requireApi/requireVersion)",
     "BadVersionSpec, BasicSpec, SysInformationSpec"),
    ("Error envelope JSON/XML (`{error,apiversion,errorCode,message}`, `<result error=\"true\">`) and content negotiation",
     "ApiService.groovy:1023 (renderErrorFormat), :1033 (renderErrorJson), :1060 (renderErrorXml); catch-all `UrlMappings.groovy:288` → `ApiController.invalid`",
     "UnauthorizedSpec, BadVersionSpec, JobImportSpec, JobOptionValidationSpec, ConfigSpec (`api.error.*`)"),
    ("Authentication modes: API token header/param, session cookie after form login, pre-authenticated headers; token roles/expiry",
     "legacy/rundeckapp/grails-app/conf/application.groovy:119-180; legacy/rundeckapp/src/main/groovy/org/rundeck/security/RundeckPreauthSuccessEventHandler.groovy (`rundeck.security.authorization.preauthenticated.{enabled,userNameHeader,userRolesHeader,attributeName,delimiter}`); services/RundeckAuthTokenManagerService.groovy; domain AuthToken.groovy",
     "UnauthorizedSpec (`authtoken`/`X-Rundeck-Auth-Token`), ExecutionsQueryViewAuthSpec, ExecutionsQueryViewHistoryAuthSpec (`/tokens/$user`)"),
    # workflow engine
    ("Workflow strategy `sequential`", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/SequentialWorkflowStrategy.java, SequentialStrategyProfile.java, BaseWorkflowExecutor.java", "JobExecutionSpec, JobsImportSpec, JobImportSpec, ExecuteScriptSpec (`strategy`)"),
    ("Workflow strategy `parallel`", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/ParallelWorkflowStrategy.java", "none (keyword `parallel` not asserted by an API spec)"),
    ("Workflow strategy `node-first`", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/NodeFirstWorkflowStrategy.java, NodeFirstWorkflowExecutor.java", "JobExecutionOnMultipleNodesSpec (node dispatch); keyword not asserted"),
    ("Rule-engine workflow executor (`ruleset` strategy, conditions, state)", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/EngineWorkflowExecutor.java; legacy/core/src/main/java/com/dtolabs/rundeck/core/rules/{WorkflowEngine,WorkflowEngineBuilder,Rules,StateWorkflowSystem,Condition}.java", "ConditionalWorkflowSpec"),
    ("Step error handlers (`errorhandler`, `keepgoingOnSuccess`)", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/{HandlerExecutionItem,HasFailureHandler}.java; workflow/BaseWorkflowExecutor.java, WorkflowItemErrorHandlerContext.java", "JobErrorHandler, JobExecutionSpec"),
    ("`keepgoing` (workflow and node dispatch)", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/BaseWorkflowExecutor.java; legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/support/ExecutionContext.groovy:47 (nodeKeepgoing)", "JobExecutionSpec, JobExecutionStatusSpec, ConditionalWorkflowSpec, ScheduleSpec (`keepgoing`)"),
    ("Step / node contexts and shared data context (`${data.x*}`, `${export.*}`)", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/{StepExecutionContext,StepNodeContext,WFSharedContext,SharedOutputContext,ContextStack}.java; legacy/plugins/upvar-plugin", "StepExecutionContextSpec, FileUrlScriptStepSpec"),
    ("Variable expansion `${option.x}`, `${node.name}`, `${job.*}`, `${globals.*}`, `${data.*}`", "legacy/core/src/main/java/com/dtolabs/rundeck/core/dispatcher/DataContextUtils.java, ContextView.java", "JobOptionValuesUrlGlobalsSpec (`globals`), StepExecutionContextSpec, JobExecutionSpec"),
    ("`@option.x@` token replacement in inline scripts", "legacy/core/src/main/java/com/dtolabs/rundeck/core/dispatcher/DataContextUtils.java (replaceTokensInScript), ReplaceTokenReader.java", "JobExecutionSpec, OptionInputValidationSpec (`@option`)"),
    ("Secure option handling (secure / secureExposed, not persisted, masked in logs)", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/workflow/BaseWorkflowExecutor.java; legacy/rundeckapp/grails-app/domain/rundeck/Option.groovy; services/ExecutionService.groovy", "SecureInputSpec (@APISecureInputTest), JobOptionValidationSpec"),
    ("Log filters (global and per step, `LogFilter` plugins)", "legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/{PluginFilteredStreamingLogWriter,LoggingManagerImpl,PluginLoggingManager}.java; legacy/core/src/main/java/com/dtolabs/rundeck/plugins/logging/LogFilterPlugin.java", "none in the API suite (Selenium jobs/LogFilterSpec)"),
    ("Job references: import options, node intersect, child failure propagation, `failOnDisable`, `childNodes`", "legacy/rundeckapp/grails-app/services/rundeck/services/ExecutionService.groovy:1743 (childNodes), :3992-4113 (nodeIntersect, importOptions); legacy/core/src/main/java/com/dtolabs/rundeck/core/jobs/{JobExecutionItem,JobRefCommand}.java", "JobExecutionSpec, JobsImportSpec (`jobref`)"),
    ("Orchestrators (`Orchestrator` plugins: maxPercentage, subset, rankTiered)", "legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/orchestrator/OrchestratorService.java; legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/dispatch/{OrchestratorNodeDispatcher,OrchestratorNodeProcessor}.java; legacy/plugins/orchestrator-plugin", "none"),
    ("Node dispatch options `threadcount`, `rankAttribute`, `rankOrder`, `keepgoing`, `nodesSelectedByDefault`, `excludeFilterUncheck`", "legacy/rundeckapp/grails-app/domain/rundeck/ScheduledExecution.groovy:83,115,340-358; ExecutionContext.groovy:47-51; legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/dispatch/{ParallelNodeDispatcher,SequentialNodeDispatcher,NodeDispatcherService}.java", "JobExecutionOnMultipleNodesSpec, JobExecutionSpec (`nodesSelectedByDefault`, `threadcount`), ExecExportSpec, ScheduleSpec"),
    ("Retries (`retry`, `retryDelay`) incl. retry counter in the execution", "ExecutionContext.groovy:33-34; legacy/rundeckapp/grails-app/services/rundeck/services/ExecutionService.groovy (retry scheduling); domain Execution.groovy", "ExecutionSpec, JobExecutionSpec, JobExecutionStatusSpec (`retry`)"),
    ("Timeouts (`timeout`, `timedout` status)", "ExecutionContext.groovy:32; legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/WorkflowExecutionServiceThread.java; services/ExecutionService.groovy", "JobExecutionSpec, JobExecutionStatusSpec (`timeout`)"),
    ("`multipleExecutions` / `maxMultipleExecutions` (409 on conflict)", "legacy/rundeckapp/grails-app/domain/rundeck/ScheduledExecution.groovy:104,121; services/ExecutionService.groovy", "JobExecutionSpec (`multipleExecutions`)"),
    ("`loglevel` (DEBUG/VERBOSE/INFO/WARN/ERROR) of jobs and adhoc runs", "ExecutionContext.groovy:30; services/logging/LoglevelThresholdLogWriter.groovy", "JobExecutionSpec, ExecuteScriptSpec, StepExecutionContextSpec and others (`loglevel` in job definitions)"),
    ("`defaultTab` of a job", "legacy/rundeckapp/grails-app/domain/rundeck/ScheduledExecution.groovy:119", "none (UI behavior; Selenium jobs/JobTabsSpec)"),
    # executions
    ("Run job: options, node filter override, `asUser`, `runAtTime`, `filter`", "ScheduledExecutionController.groovy (apiJobRun, UrlMappings.groovy:88,95); services/ExecutionService.groovy, ScheduledExecutionService.groovy", "JobExecutionSpec, CopyfileSpec, JschNodeExecutorSpec (`/job/$id/run`); `asUser`/`runAtTime` not asserted by an API spec"),
    ("Abort execution (`asUser`, `forceIncomplete`)", "ExecutionController.groovy (apiExecutionAbort); services/ExecutionService.groovy:1999,2039 (abortExecution)", "AbortSpec, JobExecutionSpec (`/execution/$id/abort`); `forceIncomplete` not asserted"),
    ("Retry a job from a failed execution (`/job/$id/retry/$executionId`)", "ScheduledExecutionController.groovy (apiJobRetry, UrlMappings.groovy:89)", "none"),
    ("Follow output: `offset`, `lastlines`, `lastmod`, `maxlines`, `compacted`, `.text/.json/.xml` formats, per node/step", "ExecutionController.groovy (apiExecutionOutput, apiExecutionOutputNodeFilter, apiExecutionOutputStepFilter, tailExecutionOutput:1538); services/logging/ExecutionLogReader.groovy", "ExecutionOutputSpec (@APIExecOutputTest), ExecutionSpec, JobExecutionSpec, ConditionalWorkflowSpec, CopyfileSpec"),
    ("Execution state (`/execution/$id/state`, `/output/state`)", "ExecutionController.groovy (apiExecutionState, apiExecutionStateOutput); services/workflow/*.groovy", "ExecutionSpec, JobExecutionSpec"),
    ("Bulk delete executions (`/executions/delete`)", "ExecutionController.groovy (apiExecutionDeleteBulk, UrlMappings.groovy:53)", "none"),
    ("Execution metrics (`/executions/metrics`, per project)", "ExecutionController.groovy (apiExecutionMetrics, UrlMappings.groovy:123-124); services/MicrometerExecutionMetricsService.groovy", "none"),
    ("Running executions (`/project/$project/executions/running`, cluster-wide option)", "MenuController.groovy (apiExecutionsRunningv14, UrlMappings.groovy:126)", "ExecutionSpec"),
    ("Execution mode passive/active (system) and scheduled mode change (execution-mode-timer plugin)", "ExecutionController.groovy (apiExecutionModeStatus/Active/Passive, UrlMappings.groovy:223-225); legacy/grails-execution-mode-timer", "ExecutionModeSpec (`/system/executions/enable|disable`)"),
    ("`rundeck.execution.logs.fileStorage*` rules (plugin, checkpoints, retries, concurrency, `generateExecutionXml`, `cancelOnStorageFailure`)", "legacy/rundeckapp/grails-app/services/rundeck/services/LogFileStorageService.groovy; ConfigurationService.groovy; conf/application.groovy (17 keys measured: `rundeck.execution.logs.fileStoragePlugin`, `...fileStorage.{cancelOnStorageFailure,checkpoint.fileSize.increment,checkpoint.fileSize.minimum,checkpoint.time.interval,checkpoint.time.minimum,forcePartialChecking,generateExecutionXml,remotePendingDelay,removeTasks.poolSize,retrievalRetryCount,retrievalRetryDelay,retrievalTasks.concurrencyLimit,scheduledTasks.poolSize,storageRetryCount,storageRetryDelay,storageTasks.concurrencyLimit}`)", "none"),
    ("Execution history auto-cleanup (`project.execution.history.cleanup.*` scheduled job)", "legacy/rundeckapp/grails-app/services/rundeck/services/ScheduledExecutionService.groovy, FrameworkService.groovy (ExecutionsCleanUp job)", "none in the API suite (Selenium execution/ExecutionSpec `auto execution clean up`)"),
    # scheduler
    ("Quartz cron syntax (6–7 fields, seconds, `?`, `L`, `W`, `#`, day-of-week numbering) and `crontabString`", "legacy/rundeckapp/grails-app/domain/rundeck/ScheduledExecution.groovy:66 (crontabString), generateCrontabExression; services/ScheduledExecutionService.groovy (org.quartz CronExpression); `quartz-cron/` crate in this repo", "JobScheduledSpec, ScheduleSpec, ScmPluginImportScheduledJobSpec (`crontab`)"),
    ("Schedule timezone (`timeZone`)", "ScheduledExecution.groovy:110", "JobScheduledSpec, JobExecutionSpec (`timeZone`)"),
    ("`scheduleEnabled` / `executionEnabled` at job, project (`project.disable.schedule|executions`) and system level", "ScheduledExecution.groovy:112-113; ScheduledExecutionController.groovy (apiFlipScheduleEnabled, apiFlipExecutionEnabled, bulk variants, UrlMappings.groovy:70-86,107-118)", "JobScheduledSpec, ScheduleSpec, JobSpec, ExecuteScriptSpec"),
    ("Forecast API (`/job/$id/forecast`, `/scheduler/jobs`)", "MenuController.groovy (apiJobForecast, apiSchedulerListJobs, UrlMappings.groovy:67,211,214)", "none (`forecast` keyword only in ExecutionSpec)"),
    ("Cluster ownership of schedules (`serverNodeUUID`, `rundeck.server.uuid`, remote assignment)", "ScheduledExecution.groovy:106; services/ScheduledExecutionService.groovy:1531 (scheduleJob forceLocal/remoteAssigned); services/JobSchedulerService.groovy, JobSchedulesService.groovy", "none"),
    ("Takeover API (`/scheduler/takeover`)", "ScheduledExecutionController.groovy (apiJobClusterTakeoverSchedule, UrlMappings.groovy:217); ScheduledExecutionService.groovy:1097 (reclaimAndScheduleJobs)", "none"),
    ("Schedule recovery after restart (reschedule jobs, clean up running executions of this server)", "ScheduledExecutionService.groovy:970,981 (rescheduleJobsAsync/rescheduleJobs); ExecutionService.groovy:923,966 (cleanupRunningJobs)", "none"),
    ("Scheduler thresholds and quartz pass-through (`rundeck.scheduler.quartz.*`)", "legacy/rundeckapp/grails-app (only `rundeck.scheduler.quartz.*` is referenced as a literal key); legacy/rundeckapp/grails-app/conf/application.groovy (quartz block)", "none"),
    # projects, nodes, sources
    ("Projects CRUD, list, meta, deferred delete", "ProjectController.groovy (apiProjectList/Create/Get/Delete/Meta, UrlMappings.groovy:131,135,208); services/ProjectManagerService.groovy, FrameworkService.groovy", "ProjectsSpec, ProjectSpec, ConfigSpec"),
    ("Node sources: file / url / script / directory / plugin providers, refresh, caching", "legacy/core/src/main/java/com/dtolabs/rundeck/core/resources/{FileResourceModelSource,URLResourceModelSource,ScriptResourceModelSource,DirectoryResourceModelSource,ScriptPluginResourceModelSource,CachingResourceModelSource}*.java; services/NodeService.groovy, nodes/CachedProjectNodes.groovy; FrameworkController.groovy (apiSourcesList, apiSourceGet)", "ConfigSpec (`/sources`, `/source/$index`), NodesSpec, AnsibleResourceModelSpec"),
    ("Per-source editable nodes (writeable sources, `/source/$index/resources`)", "FrameworkController.groovy (apiSourceGetContent, apiSourceWriteContent, UrlMappings.groovy:178)", "ConfigSpec"),
    ("Project readme / motd files", "ProjectController.groovy (apiProjectFileGet/Put/Delete, UrlMappings.groovy:143,150)", "ImportSpec"),
    ("Project configuration keys (`/config`, `/config/$keypath`, properties/json/text content types)", "ProjectController.groovy (apiProjectConfigGet/Put/KeyGet/KeyPut/KeyDelete, UrlMappings.groovy:136-142)", "ConfigSpec"),
    ("Per-project plugin configuration and plugin groups (`/configurable`, `/plugins/save`)", "FrameworkController.groovy (getProjectConfigurable, saveProjectConfigurable, saveProjectPlugins, UrlMappings.groovy:147,158); services/PluginConfigService.groovy", "none"),
    ("ACL files: system (`/system/acl/*`) and project (`/project/$project/acl/*`) with validation messages", "FrameworkController.groovy (apiSystemAcls, UrlMappings.groovy:226); ProjectController.groovy (apiProjectAcls, :154); services/AclFileManagerService.groovy", "SystemAclCreateSpec (system); none (project)"),
    ("Feature flags endpoint (`/feature`, `/feature/$featureName`, `rundeck.feature.*.enabled`)", "ApiController.groovy (featureQueryAll, featureQuery, UrlMappings.groovy:257-268); services/feature/FeatureService.groovy", "none"),
    # other
    ("Notifications: email, webhook, plugin; triggers onsuccess/onfailure/onstart/onavgduration/onretryablefailure", "legacy/rundeckapp/grails-app/services/rundeck/services/NotificationService.groovy; domain Notification.groovy; views/execution/mailNotification/status.gsp", "JobExecutionSpec (`notification`); Selenium jobs/JobNotificationSpec"),
    ("Webhooks: receive (`/webhook/$authtoken`), CRUD, `WebhookEvent` plugins, token handling and secure migration", "legacy/grails-webhooks/grails-app/services/webhooks/WebhookService.groovy:71 (processWebhook), :196,202,400; controllers/webhooks/WebhookController.groovy; legacy/core/src/main/java/com/dtolabs/rundeck/plugins/webhook/WebhookEventPlugin.java; services/WebhookTokenSecureMigrationService.groovy", "none in the API suite (Selenium webhook/WebhooksSpec)"),
    ("SCM export/import with git (setup, status, actions, diff, job import/export, scheduled import)", "legacy/rundeckapp/grails-app/services/rundeck/services/ScmService.groovy, services/scm/*.groovy; ScmController.groovy; legacy/plugins/git-plugin", "ScmPluginSetupSpec, ScmPluginStatusSpec, ScmPluginInputsSpec, ScmPluginActionsSpec, ScmPluginJobStatusSpec, ScmPluginJobDiffSpec, ScmPluginJobActionInputSpec, ScmPluginJobActionsPerformSpec, ScmPluginImportScheduledJobSpec (through helper GitScmApiClient)"),
    ("Log file storage plugins (`LogFileStorage`/`ExecutionFileStorage`), incomplete-storage listing and resume", "services/LogFileStorageService.groovy; domain LogFileStorageRequest.groovy; MenuController.groovy (apiLogstorageInfo, apiLogstorageListIncompleteExecutions, apiResumeIncompleteLogstorage, UrlMappings.groovy:220-222)", "none"),
    ("File uploads for job options (`FileUpload` plugin, `JobFileRecord`, `/job/$id/input/file`, `/jobs/file/$id`)", "services/FileUploadService.groovy; domain JobFileRecord.groovy; ScheduledExecutionController.groovy (apiJobFileUpload, apiJobFilesList, apiJobFileInfo, UrlMappings.groovy:90-94,119)", "none"),
    ("Remote option values (`valuesUrl`, `OptionValues` plugins, globals in URLs)", "services/optionvalues/OptionValuesService.groovy; services/ScheduledExecutionService.groovy (remote option loading); legacy/core/src/main/java/com/dtolabs/rundeck/plugins/option/OptionValuesPlugin.java", "JobOptionValuesUrlGlobalsSpec"),
    ("`NodeEnhancer` plugins applied to project nodes", "legacy/core/src/main/java/com/dtolabs/rundeck/plugins/nodes/NodeEnhancerPlugin.java; services/NodeService.groovy", "none"),
    ("`UserGroupSource` plugins (extra roles at login)", "legacy/core/src/main/java/com/dtolabs/rundeck/plugins/user/groups/UserGroupSourcePlugin.java; legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/service/ScriptUserGroupSource.java", "none"),
    ("Execution and job lifecycle plugins (`ExecutionLifecycle`, `JobLifecycle`)", "legacy/core/src/main/java/com/dtolabs/rundeck/plugins/jobs/ExecutionLifecyclePlugin.java; legacy/core/src/main/java/com/dtolabs/rundeck/plugins/project/JobLifecyclePlugin.java; legacy/core/src/main/java/com/dtolabs/rundeck/core/execution/ExecutionLifecycle{Component,Plugin}Exception.java", "none"),
    ("Audit events (`AuditEventListener`, login/logout/project/job events)", "legacy/core/src/main/java/com/dtolabs/rundeck/core/audit/{AuditEvent,ActionTypes,ResourceTypes,RequestInfo,UserInfo}.java; legacy/core/src/main/java/com/dtolabs/rundeck/plugins/audit/AuditEventListenerPlugin.java; legacy/plugins/audit-logging-plugin", "none in the API suite (Selenium jobs/JobAuditApiSpec checks `lastModifiedBy`)"),
]

# Oracle evidence per service type (spec names that literally denote the service, or keyword hits in the
# API specs; see scripts/inventory/README.md). Anything not listed is "none".
SERVICE_TYPE_ORACLE = {
    "NodeExecutor": "JschNodeExecutorSpec, OpenSshNodeExecutorSpec, SshjNodeExecutorSpec, JobExecSudoSpec",
    "FileCopier": "none in the API suite (Selenium project/DefaultFileCopierSpec)",
    "WorkflowNodeStep": "CopyfileSpec (copyfile node step), StepExecutionContextSpec",
    "WorkflowStep": "FileUrlScriptStepSpec, StepExecutionContextSpec, ConditionalWorkflowSpec",
    "WorkflowStrategy": "ConditionalWorkflowSpec (`strategy`)",
    "ResourceModelSource": "AnsibleResourceModelSpec, ConfigSpec (`/sources`)",
    "ResourceFormatParser": "ConfigSpec, NodesSpec (`/resources?format=`)",
    "ResourceFormatGenerator": "ConfigSpec (`/resource/$name?format=yaml`)",
    "Notification": "JobExecutionSpec (`notification`)",
    "Storage": "PrivateKeySpec, PublicKeySpec",
    "StorageConverter": "EncryptionBackwardCompatSpec",
    "ScmExport": "ScmPluginSetupSpec, ScmPluginActionsSpec, ScmPluginJobStatusSpec (git-export)",
    "ScmImport": "ScmPluginImportScheduledJobSpec, ScmPluginJobDiffSpec, ScmPluginJobActionsPerformSpec (git-import)",
    "OptionValues": "none (JobOptionValuesUrlGlobalsSpec covers remote URL values, not the plugin)",
}


def read(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as fh:
        return fh.read()


def service_types() -> list[tuple[str, int]]:
    out = []
    for no, line in enumerate(read("legacy/core/src/main/java/com/dtolabs/rundeck/plugins/ServiceNameConstants.java").splitlines(), 1):
        m = re.match(r"\s*public static final String (\w+)\s*=", line)
        if m:
            out.append((m.group(1), no))
    return out


def resolve_constant(expr: str, annotated_file: str, search_dirs: list[str]) -> str:
    """Literal value of a `@Plugin(name = ...)` expression.

    Order: the class the expression names (`Foo.CONST` → `Foo.java`/`Foo.groovy` of the module), then the
    annotated file itself, then the module, then core — so sibling classes sharing a constant name
    (`PROVIDER_NAME`, `SERVICE_PROVIDER_TYPE`) resolve to their own value.
    """
    expr = expr.strip()
    if re.fullmatch(r"\"[^\"]*\"|'[^']*'", expr):
        return expr[1:-1]
    parts = expr.split(".")
    const = parts[-1]
    rx = re.compile(r"\b" + re.escape(const) + r"\s*=\s*[\"']([^\"']+)[\"']")
    candidates: list[str] = []
    for d in search_dirs:
        for dp, _, fns in os.walk(os.path.join(ROOT, d)):
            for fn in fns:
                if fn.endswith((".java", ".groovy")):
                    candidates.append(os.path.relpath(os.path.join(dp, fn), ROOT))
    ordered = []
    if len(parts) > 1:
        ordered += [c for c in candidates if os.path.basename(c).rsplit(".", 1)[0] == parts[-2]]
    ordered.append(annotated_file)
    ordered += [c for c in candidates if c not in ordered]
    for c in ordered:
        m = rx.search(read(c))
        if m:
            return m.group(1)
    return f"?{expr}"


def builtin_plugins() -> list[tuple[str, list[tuple[str, str, str]]]]:
    """[(dir, [(service, provider, file)])] from the @Plugin annotations of each plugin module."""
    result = []
    base = os.path.join(ROOT, "legacy/plugins")
    for d in sorted(os.listdir(base)):
        full = os.path.join(base, d)
        if not os.path.isdir(full):
            continue
        providers = []
        for dp, _, fns in os.walk(full):
            if "/test/" in dp + "/" or "/build/" in dp + "/":
                continue
            for fn in sorted(fns):
                if not fn.endswith((".java", ".groovy")):
                    continue
                rel = os.path.relpath(os.path.join(dp, fn), ROOT)
                src = read(rel)
                for m in re.finditer(r"@Plugin\s*\(", src):
                    end = routes.balanced(src, m.end() - 1, "(", ")")
                    args = src[m.end() : end - 1]
                    svc = re.search(r"service\s*=\s*(?:ServiceNameConstants\.)?[\"']?(\w+)[\"']?", args)
                    name = re.search(r"name\s*=\s*([^,\n]+)", args)
                    if not svc or not name:
                        continue
                    provider = resolve_constant(name.group(1), rel, [f"legacy/plugins/{d}", "legacy/core/src/main/java"])
                    providers.append((svc.group(1), provider, rel))
        result.append((d, providers))
    return result


def domain_classes() -> list[tuple[str, str, str]]:
    """[(class, file, table evidence)] for the 22 rundeckapp domain classes + Webhook."""
    files = []
    for base in ("legacy/rundeckapp/grails-app/domain", "legacy/grails-webhooks/grails-app/domain"):
        for dp, _, fns in os.walk(os.path.join(ROOT, base)):
            files += [os.path.relpath(os.path.join(dp, f), ROOT) for f in fns if f.endswith(".groovy")]
    tables: dict[str, str] = {}
    mig = "legacy/rundeckapp/grails-app/migrations/core"
    for fn in sorted(os.listdir(os.path.join(ROOT, mig))):
        for no, line in enumerate(read(f"{mig}/{fn}").splitlines(), 1):
            m = re.search(r"createTable\s*\(\s*tableName:\s*\"([a-z_]+)\"", line)
            if m:
                tables.setdefault(m.group(1), f"{mig}/{fn}:{no}")
    out = []
    for f in sorted(files, key=lambda p: os.path.basename(p)):
        src = read(f)
        m = re.search(r"^(?:public\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?", src, re.M)
        cls, parent = m.group(1), m.group(2)
        explicit = re.search(r"^\s*table\s+[\"'](\w+)[\"']", src, re.M)
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", cls).lower()
        table = explicit.group(1) if explicit else snake
        if table in tables:
            mapping_note = '; `mapping { table "' + table + '" }` in the domain class' if explicit else ""
            ev = f"`{table}` ({tables[table]}{mapping_note})"
        elif parent and re.sub(r"(?<!^)(?=[A-Z])", "_", parent).lower() in tables:
            pt = re.sub(r"(?<!^)(?=[A-Z])", "_", parent).lower()
            ev = f"`{pt}` (subclass of {parent}, single-table; {tables[pt]})"
        else:
            ev = "no `createTable` found in migrations (check Phase 1 schema capture)"
        out.append((cls, f, ev))
    return out


def journeys() -> list[list[str]]:
    rows = []
    for line in read("specs/ui-journeys.md").splitlines():
        if re.match(r"\|\s*J-\d{3}\s*\|", line):
            cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
            rows.append(cells)
    return rows


def md(cells: list[str]) -> str:
    return "| " + " | ".join(c.replace("|", "\\|") if i not in (0,) else c for i, c in enumerate(cells)) + " |"


def main(argv: list[str]) -> int:
    global ROOT
    if len(argv) > 2 and argv[1] == "--root":
        ROOT = argv[2]
    existing = os.path.join(ROOT, "PARITY.md")
    if os.path.exists(existing):
        with open(existing, encoding="utf-8") as fh:
            if re.search(r"^\| \w+-\d+ \|.*\| (partial|done|deviated|blocked) \|", fh.read(), re.M):
                print("WARNING: PARITY.md already carries non-missing statuses; regenerating would discard them", file=sys.stderr)

    all_routes = []
    for f in routes.FILES:
        all_routes += routes.extract(f, ROOT)
    # oracle mapping for API routes
    sources = {}
    for group, rel in (("specs", oracle_map.SPEC_DIR), ("helpers", oracle_map.HELPER_DIR)):
        for f in oracle_map.groovy_files(ROOT, rel):
            with open(f, encoding="utf-8", errors="replace") as fh:
                sources[f] = (group, fh.read().splitlines())

    def oracle_for(pattern: str) -> str:
        rx = oracle_map.pattern_regex(pattern)
        if rx is None:
            return "none (catch-all; not path-mappable)"
        specs, helpers = set(), set()
        for f, (group, lines) in sources.items():
            if any(rx.search(t) for t in lines):
                (specs if group == "specs" else helpers).add(os.path.basename(f)[:-7])
        if specs:
            return ", ".join(sorted(specs))
        if helpers:
            return "none (indirect via helper " + ", ".join(sorted(helpers)) + ")"
        return "none"

    sections: dict[str, list[list[str]]] = {}
    status, last = "missing", "—"

    api_main = [r for r in all_routes if r["kind"] == "api" and r["file"] == MAIN]
    sections["API routes (main app)"] = [
        [f"R-{i:03d}", f"`{r['methods']}` `{r['pattern']}` → {r['controller']}.{r['action']}" + (f" ({r['extras']})" if r["extras"] != "-" else ""), status, oracle_for(r["pattern"]), last, f"`UrlMappings.groovy:{r['line']}`"]
        for i, r in enumerate(api_main, 1)
    ]
    api_plug = [r for r in all_routes if r["kind"] == "api" and r["file"] != MAIN]
    sections["API routes (plugins)"] = [
        [f"P-{i:03d}", f"`{r['methods']}` `{r['pattern']}` → {r['controller']}.{r['action']}" + (f" (flag `{r['condition']}`)" if r["condition"] != "-" else ""), status, oracle_for(r["pattern"]), last, f"`{r['file'].split('/')[1]}` `UrlMappings.groovy:{r['line']}`"]
        for i, r in enumerate(api_plug, 1)
    ]
    web_rows = []
    for r in all_routes:
        if r["kind"] == "api":
            continue
        plugin = r["file"].split("/")[1]
        if r["file"] != MAIN and r["kind"] in ("view", "generic"):
            continue  # plugin scaffold mappings, summarised below
        label = f"`{r['methods']}` `{r['pattern']}` → {r['controller']}.{r['action']}" if r["kind"] in ("web", "generic") else f"`{r['pattern']}` → {r['action']}"
        if r["condition"] != "-":
            label += f" (flag `{r['condition']}`)"
        note = {"generic": "convention mapping; resolves `/menu/*`, `/user/*`, `/framework/*`, … (rows below)", "redirect": "redirect", "status": "error handler"}.get(r["kind"], "")
        web_rows.append([label, f"`{plugin}` `UrlMappings.groovy:{r['line']}`" if r["file"] != MAIN else f"`UrlMappings.groovy:{r['line']}`", note])
    for pattern, methods, ctrl, ev, note in GENERIC_WEB_ROUTES:
        web_rows.append([f"`{methods}` `{pattern}` → {ctrl}", "`" + ev.replace("; ", "`; `") + "`", note])
    for plugin in ("grails-metricsweb", "grails-repository", "grails-rundeck-data-shared", "grails-execution-mode-timer", "grails-job-kill-handler", "grails-persistlocale", "grails-securityheaders"):
        scaf = [r for r in all_routes if r["file"].split("/")[1] == plugin and r["kind"] in ("view", "generic")]
        if scaf:
            web_rows.append([f"`{plugin}` scaffold mappings: " + ", ".join(f"`{r['pattern']}`" for r in scaf), f"`{plugin}` `UrlMappings.groovy:{','.join(r['line'] for r in scaf)}`", "Grails plugin scaffold (`/`→view, 404/500 views, generic); never served by rdx"])
    sections["Web routes / deep links"] = [[f"W-{i:03d}", row[0], status, "Playwright (journeys) / redirect test", last, row[1] + ((" — " + row[2]) if row[2] else "")] for i, row in enumerate(web_rows, 1)]

    sections["Service types"] = [
        [f"S-{i:03d}", f"`{name}`", status, SERVICE_TYPE_ORACLE.get(name, "none"), last, f"`ServiceNameConstants.java:{no}`"]
        for i, (name, no) in enumerate(service_types(), 1)
    ]
    sections["Built-in plugins"] = []
    for i, (d, provs) in enumerate(builtin_plugins(), 1):
        desc = "; ".join(f"{svc} `{prov}`" for svc, prov, _ in provs) or "no `@Plugin` annotation found"
        files = sorted({os.path.basename(f) for _, _, f in provs})
        sections["Built-in plugins"].append([f"BP-{i:03d}", f"`legacy/plugins/{d}` — {desc}", status, "none (see the matching Service types / Behavior rows)", last, "`" + "`, `".join(files) + "`" if files else "—"])
    sections["Domain classes"] = [
        [f"D-{i:03d}", f"`{cls}` → {ev}", status, "none (Phase 1 schema capture from a 6.3.0-initialised Postgres)", last, f"`{f}`"]
        for i, (cls, f, ev) in enumerate(domain_classes(), 1)
    ]
    sections["File formats"] = [[f"F-{i:03d}", item, status, oracle, last, "`" + paths.replace("; ", "`; `") + "`"] for i, (item, paths, oracle) in enumerate(FILE_FORMATS, 1)]
    sections["Behavior"] = [[f"B-{i:03d}", item, status, oracle, last, "`" + paths.replace("; ", "`; `") + "`"] for i, (item, paths, oracle) in enumerate(BEHAVIORS, 1)]
    sections["Journeys"] = []
    for cells in journeys():
        jid, name, entry, api, sel, pw, phase, st = cells[:8]
        sections["Journeys"].append([jid, f"{name} (phase {phase})", st, f"Playwright {pw}; upstream: {sel}", last, f"entry: {entry}; API: {api}"])

    # ---------------------------------------------------------------- output
    out = []
    out.append("# PARITY.md — contract matrix of rdx against Rundeck 6.3.0 (tag `v6.3.0`, commit `6ac5d092`)")
    out.append("")
    out.append("Generated at Phase 0 by `python3 -I scripts/inventory/parity_md.py` (see `scripts/inventory/README.md` for the")
    out.append("extraction method and the verification commands). From Phase 1 on this file is maintained by hand: rows change")
    out.append("status and gain evidence, rows are never deleted. One row per contract item; one line per row.")
    out.append("")
    out.append("## Columns")
    out.append("")
    out.append("| Column | Meaning |")
    out.append("|---|---|")
    out.append("| id | stable row id (`R` main-app API route, `P` plugin API route, `W` web route / deep link, `S` service type, `BP` built-in plugin, `D` domain class, `F` file format, `B` behavior, `J` journey) |")
    out.append("| item | the contract item: route (`methods` `pattern` → controller.action), type, class, format, behavior or journey |")
    out.append("| status | `missing` (not implemented) · `partial` (implemented, oracle not fully green) · `done` (oracle/Playwright run recorded in *last run*) · `deviated` (intentional difference: ADR + `docs/COMPAT.md` line required) · `blocked` (`BLOCKED/<id>.md` + `blocked` issue required) |")
    out.append("| oracle spec | the upstream functional spec class(es) under `legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/api/**` whose source addresses the item (route rows: literal path match, see README), the Playwright test for journeys, or `none` when no upstream test exercises it (a coverage gap: a differential test against the legacy container is then required before `done`) |")
    out.append("| last run | `<date> <pass>/<total> <commit> <CI url>` of the run that justifies the status; `—` until then |")
    out.append("| legacy reference | file:line in `legacy/` (paths relative to `legacy/rundeckapp/grails-app/controllers/rundeckapp/` for `UrlMappings.groovy`, to `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/` for `*Controller.groovy`, to `legacy/rundeckapp/grails-app/services/rundeck/services/` for `*Service.groovy`, to `legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/support/` for `ExecutionContext.groovy`, otherwise from the repository root) |")
    out.append("")
    out.append("## Rules (MISSION.md §8)")
    out.append("")
    out.append("- Never `done` without an oracle run (API) or a Playwright run (UI) recorded in *last run* on the commit being judged.")
    out.append("- `deviated` requires an ADR under `docs/adr/` and a line in `docs/COMPAT.md`; `blocked` requires `BLOCKED/<id>.md` and a `blocked` issue.")
    out.append("- Unimplemented endpoints answer `501` with the legacy error envelope (`api.error.not-implemented`) and stay `missing`.")
    out.append("- Oracle specs are never edited or skipped to turn a row green; a legacy-specific or wrong test goes to `tests/parity-skips.toml` and the row stays `deviated`/`blocked`.")
    out.append("- `V` stands for `$api_version` (14–60); route patterns are quoted verbatim from `UrlMappings.groovy` (Grails syntax: `$x` one segment, `$x?` optional, `$x**` rest of path, `(.$format)?` optional extension).")
    out.append("")
    out.append("## Totals")
    out.append("")
    statuses = ["missing", "partial", "done", "deviated", "blocked"]
    out.append("| area | rows | " + " | ".join(statuses) + " |")
    out.append("|---|---|" + "|".join("---" for _ in statuses) + "|")
    grand = {s: 0 for s in statuses}
    total = 0
    for area, rows in sections.items():
        counts = {s: sum(1 for r in rows if r[2] == s) for s in statuses}
        for s in statuses:
            grand[s] += counts[s]
        total += len(rows)
        out.append(f"| {area} | {len(rows)} | " + " | ".join(str(counts[s]) for s in statuses) + " |")
    out.append(f"| **all** | **{total}** | " + " | ".join(f"**{grand[s]}**" for s in statuses) + " |")
    out.append("")
    for area, rows in sections.items():
        out.append(f"## {area}")
        out.append("")
        if area == "API routes (main app)":
            out.append(f"{len(rows)} `/api/$api_version/...` patterns in `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy` (measured; MISSION.md Appendix B says 120). Methods `*` = any method accepted by the mapping (the controller's `allowedMethods` decides).")
        elif area == "API routes (plugins)":
            out.append(f"{len(rows)} patterns contributed by the Grails plugins: `grails-webhooks` (3, behind `rundeck.feature.webhooks.enabled`), `grails-repository` (26, 25 of them behind `rundeck.feature.repository.enabled`), `grails-execution-mode-timer` (4). `grails-metricsweb`, `grails-rundeck-data-shared`, `grails-job-kill-handler`, `grails-persistlocale` and `grails-securityheaders` contribute no API route (`grails-metricsweb` adds the four legacy `/metrics/*` web routes listed in the next section).")
        elif area == "Web routes / deep links":
            out.append("Non-API mappings of the main app and the plugins, plus the pages reached through the convention mapping `/$controller/$action?/$id?` (the `/menu/*`, `/user/*`, `/resources/*` deep links of MISSION.md §1.6). New routes may differ; these must redirect (ADR-0004). Legacy ajax endpoints of the GSP pages are inventoried so that nothing is forgotten, and will be closed as `deviated` when the rebuilt UI replaces them.")
        elif area == "Service types":
            out.append(f"{len(rows)} constants in `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/ServiceNameConstants.java` (measured; MISSION.md Appendix B says 36). Jar plugins are out of scope (§1.5); each type must be served by built-ins, script plugins and the WASM ABI (ADR-0003).")
        elif area == "Built-in plugins":
            out.append(f"{len(rows)} modules under `legacy/plugins/` with the providers their `@Plugin(service, name)` annotations register (names resolved from the constants of the module or of `core`).")
        elif area == "Domain classes":
            out.append(f"{len(rows)} GORM domain classes (22 under `legacy/rundeckapp/grails-app/domain/rundeck/`, plus `legacy/grails-webhooks/grails-app/domain/webhooks/Webhook.groovy`) with the table the Liquibase changelogs create for them (`legacy/rundeckapp/grails-app/migrations/core/*.groovy`; `rdoption_values` and `workflow_workflow_step` are the two extra collection/join tables).")
        elif area == "File formats":
            out.append("One row per item of MISSION.md §1.2 (job definitions and node resources split per format).")
        elif area == "Behavior":
            out.append("One row per named sub-item of MISSION.md §1.3 (plus the three §1.1 cross-cutting contracts). *oracle spec* names the API specs that literally mention the behavior (keyword or path evidence, see README); `none` means the behavior must get a differential test against the legacy container.")
        elif area == "Journeys":
            out.append(f"{len(rows)} journeys from `specs/ui-journeys.md` (57 Selenium specs, 260 GSP files, 30 SPA page bundles). The oracle is the Playwright test; the upstream Selenium spec is the reference behavior.")
        out.append("")
        out.append("| id | item | status | oracle spec | last run | legacy reference |")
        out.append("|---|---|---|---|---|---|")
        for r in rows:
            out.append(md(r))
        out.append("")
    out.append("## Oracle baseline (legacy 6.3.0)")
    out.append("")
    out.append("pending: filled by the Phase 0 baseline run")
    out.append("")
    sys.stdout.write("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
