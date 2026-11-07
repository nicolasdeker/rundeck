# scripts/inventory — reproducible extraction of the legacy inventory (Rundeck 6.3.0)

Small Python 3 (stdlib only, run with `python3 -I`) scripts that read the pinned legacy tree under `legacy/`
and print the facts that `PARITY.md` and `specs/ui-journeys.md` are built from. They never write into
`legacy/`. All counts below were measured on tag `v6.3.0` (commit `6ac5d092`) with Python 3.13.

| Script | What it extracts | Output |
|---|---|---|
| `routes.py` | every mapping of the 9 `UrlMappings.groovy` files (main app + 8 Grails plugins): file, line, kind (`api`/`web`/`generic`/`redirect`/`view`/`status`), pattern, HTTP methods, controller, action, fixed params, feature flag | TSV on stdout + `# ...` count lines |
| `oracle_map.py` | for each `api` route of `routes.py`, the upstream functional specs (`legacy/functional-test/.../functional/api/**`) whose source contains the route's path, and the shared helpers (`.../org/rundeck/util/**`) that do | TSV on stdout; `--evidence` adds `# file:line: text` lines |
| `selenium_specs.py` | the 57 Selenium specs: class, annotations, page objects imported, feature methods | TSV on stdout |
| `parity_md.py` | the Phase 0 `PARITY.md` (routes + oracle mapping + service types + built-in plugins + domain classes/tables + the hand-verified §1.2/§1.3 tables + the journeys of `specs/ui-journeys.md`) | Markdown on stdout — **one-shot**: from Phase 1 on `PARITY.md` is edited by hand |

## Commands

```sh
cd <repo>
python3 -I scripts/inventory/routes.py > /tmp/routes.tsv            # 276 mappings; 152 api patterns (119 main app + 33 plugins)
python3 -I scripts/inventory/oracle_map.py /tmp/routes.tsv --evidence  # 152 api routes: 53 with spec, 12 helpers only, 87 none
python3 -I scripts/inventory/selenium_specs.py                       # 57 specs, 241 feature methods
python3 -I scripts/inventory/parity_md.py > PARITY.md                # only at bootstrap (warns if statuses were already edited)
```

## Method and limits (so nobody over-reads the mapping)

* **Route parsing.** Comments are stripped outside string literals before matching, so the two commented-out
  mappings of the main file (`resources/refresh`, `exportDownload`) and the commented `uninstall` of
  `grails-repository` are not counted. A mapping is `"<pattern>"(<args>) { <block> }`, `verb "<pattern>"(...)`,
  `name x: "<pattern>" { ... }` or `"<pattern>" { ... }`. `${project}` is normalised to `$project`. Methods come
  from an `action = [GET: ..., POST: ...]` map or a `post` verb prefix; `*` means the mapping accepts any method
  and the controller's `allowedMethods` decides (the specs below are the oracle for that).
* **Oracle mapping is a literal path match, not a semantic one.** The route path (after `/api/$api_version`)
  becomes a regex where `$x` matches one segment (Groovy `${expr}` included), `$x**` the rest, optional parts are
  optional, the match must start after a quote or `/api/<x>` and end at a quote, `?`, whitespace or end of line
  (`RdClient` prefixes `/api/<version>` itself: `legacy/functional-test/src/test/groovy/org/rundeck/util/container/RdClient.groovy:153,183`).
  A spec listed for a route therefore *mentions* that path; it may not assert every method or behavior of the
  route. A route marked `none` may still be reached through a helper class (reported separately as `helpers`),
  through a URL built from variables, or not at all — the three cases are not distinguished and the row stays
  a coverage gap until a differential test exists. The catch-all `/api/$api_version/$other/$extra**?` is not
  mapped (it would match every path).
* **Behavior / format / service-type oracle columns** in `PARITY.md` were filled from keyword greps over the API
  specs (`grep -rli <keyword> legacy/functional-test/.../functional/api`) and from spec names that literally
  denote the item (e.g. `JschNodeExecutorSpec` for `NodeExecutor`); the keyword is quoted in the cell. "Mentions"
  again, not "asserts".
* **Built-in plugin providers** come from `@Plugin(service = ..., name = ...)`; a `name` given as a constant is
  resolved by grepping the plugin module and then `legacy/core/src/main/java` for `CONST = "..."`; an unresolved
  name is printed as `?<expr>` (none remained on v6.3.0).
* **Domain tables** come from `createTable(tableName: "...")` in `legacy/rundeckapp/grails-app/migrations/core/*.groovy`
  (the actual schema), cross-checked with the two explicit `mapping { table ... }` blocks (`Option` → `rdoption`,
  `User` → `rduser`). Subclasses without their own table (`ExecReport`, `CommandExec`, `JobExec`, `PluginStep`) are
  reported on their parent's table.
* **Journeys** are hand-written in `specs/ui-journeys.md` from `selenium_specs.py`, the GSP page templates
  (`find legacy/rundeckapp/grails-app/views -name '*.gsp'`, 233 + 27 in the plugins = 260) and the SPA page
  bundles of `legacy/rundeckapp/grails-spa/packages/ui-trellis/vue.config.app.js`.

## Verification used at Phase 0

```sh
# totals table == row counts per id prefix
for p in R P W S BP D F B J; do printf '%s\t' $p; grep -cE "^\| $p-[0-9]{3} \|" PARITY.md; done
# every Selenium spec is cited by a journey
for f in $(find legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/selenium -name '*Spec.groovy'); do
  c=$(basename $f .groovy); d=$(basename $(dirname $f)); grep -qE "$d/$c\b" specs/ui-journeys.md || echo "NOT REFERENCED: $d/$c"; done
# spot-check: the line cited by a route row holds that pattern
grep -E '^\| R-040 ' PARITY.md; sed -n 102p legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy
```

## Measured counts vs MISSION.md Appendix B (legacy code wins)

| Item | MISSION.md | Measured | Evidence |
|---|---|---|---|
| `/api/$api_version/...` patterns, main app | 120 | **119** | `routes.py` (`# ... UrlMappings.groovy: api=119`); manual count of lines 40–288 |
| Plugin API patterns | "plus plugin routes" | 33 (webhooks 3, repository 26, execution-mode-timer 4) | `routes.py` |
| Service types (`ServiceNameConstants.java`) | 36 | **35** | `grep -c 'public static final String' legacy/core/src/main/java/com/dtolabs/rundeck/plugins/ServiceNameConstants.java` → 35 (lines 35–76) |
| Built-in plugin modules | 15 | 15 | `ls -d legacy/plugins/*/` |
| Domain classes | 23 | 23 (22 + `grails-webhooks/.../Webhook.groovy`) | `find ... grails-app/domain -name '*.groovy'` |
| Controllers | 27 | **26** `*Controller.groovy` (28 files in `controllers/rundeck/controllers/`, `ControllerBase.groovy` and `ParamsUtil.groovy` are not controllers) | `find legacy/rundeckapp/grails-app/controllers -name '*Controller.groovy' \| wc -l` |
| Services | 66 | **65** `*Service.groovy` under `legacy/rundeckapp/grails-app/services` (115 `.groovy` files in total) | `find legacy/rundeckapp/grails-app/services -name '*Service.groovy' \| wc -l` |
| API functional specs | 64 `@APITest` | **63** files carry `@APITest` (62 under `functional/api/**` + `functional/util/WaitUtilsSpec.groovy`); the `api/**` tree holds 66 `.groovy` files: 62 `@APITest`, 1 `@APIExecOutputTest` (`ExecutionOutputSpec`), 1 `@APISecureInputTest` (`SecureInputSpec`), 1 `@JdbcTest`, 1 `@LdapTest`, and `scm/ScmBaseContainer.groovy` (base class) | `grep -rl '@APITest' legacy/functional-test/src/test/groovy \| wc -l` |
| Selenium specs | 57 | 57 (55 `@SeleniumCoreTest`, `LdapLoginSpec` `@LdapTest`, `ProjectsSpec` `@UiModeFlag`) | `selenium_specs.py` |
| GSP files | 260 | 260 (233 in `rundeckapp`, 27 in the Grails plugins) | `find legacy -name '*.gsp' \| wc -l` |
| API versions | 14 → 60, deprecation 17 | same | `ApiVersions.groovy:60,68,69` |
