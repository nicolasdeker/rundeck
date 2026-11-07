# oracle-scm-gitea-fixture — the two SCM specs fail on the legacy oracle itself
- Phase / item: Phase 0 P0-08 (oracle baseline) → affects Phase 4 (SCM rows `R-` `/project/$project/scm/*`)   - Opened: 2026-11-07 bootstrap session   - Issue: none yet (Issues are disabled on the fork; the owner must enable them)
## Symptoms
`org.rundeck.tests.functional.api.scm.ScmPluginSetupSpec` and `ScmPluginJobDiffSpec` fail at `initializationError` with
`java.lang.IllegalStateException: Failed to create repository: repoExample` / `repoExample4`
(`legacy/functional-test/src/test/groovy/org/rundeck/util/api/scm/gitea/GiteaApiRemoteRepo.groovy:60-79`), in both
baseline runs against `rundeck/rundeck:6.3.0`: in-session sequential (`tests/baselines/2026-11-07-legacy-6.3.0-in-session.json`)
and the CI matrix (`tests/baselines/2026-11-07-legacy-6.3.0-ci-run-42397663285.json`). All other 61 specs are green.
## Hypotheses tested
1. Environment-specific (cloud sandbox without IPv6, proxy CA)? No: the CI runner (IPv6, no proxy) fails identically.
2. Ordering dependency between specs? No: fails both when the package runs alone (CI) and in the full sequential run.
3. Not yet tested: the gitea fixture (`legacy/functional-test/src/test/resources/docker/compose/oss/gitea/`, image
   `gitea/gitea:28.0.0`, admin user created by `start.sh`) vs the test helper's API calls — the helper's own comment
   (`GiteaApiRemoteRepo.groovy:43-45`) records a `401 user does not exist [name: rundeckgitea]` failure mode when the
   admin user is not created before the tests reach the API; the exact HTTP response was not captured by the report.
## What would unblock
Capture the gitea response (run `ScmPluginSetupSpec` alone with `-i` and read `GiteaApiRemoteRepo` logs), check the
gitea container log for `start.sh` errors (admin user creation, token), compare with upstream CI (CircleCI config in
`legacy/.circleci/config.yml`, which may prebuild the gitea image or pin a different tag). If the fixture is broken on
tag v6.3.0 itself, the SCM rows get their oracle from differential tests against the legacy container instead.
## Impact
Oracle evidence for the 10 `/project/$project/scm/*` routes (PARITY `R-` rows mapped to `ScmPlugin*Spec`) is unavailable
until fixed; the two specs are excused for the `rdx` target in `tests/parity-skips.toml` (status `blocked`); Phase 4 exit
("full apiTest green except documented BLOCKED items") tolerates it. No workaround needed before Phase 4.
