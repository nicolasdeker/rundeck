# DECISIONS-PENDING — defaults the autopilot took without the owner (MISSION.md §7)

Each entry is mirrored by a GitHub issue labeled `decision`. The owner answers in the issue from the phone; the next run
applies the answer, cites the commit in a closing comment, and moves the entry to the "Resolved" section below.
Rule: ambiguity → the parity-preserving (or more secure) option, recorded here, never a question mid-run.

| id | date | question | default taken | why | issue |
|----|------|----------|---------------|-----|-------|
| D-001 | 2026-11-07 | Where does the legacy functional suite's Maven traffic go from the cloud? Maven Central answers 429 to the shared egress IP. | A Gradle init script (`scripts/gradle-init.d/central-mirror.gradle`, installed by `scripts/cloud-setup.sh`) redirects Maven Central to Google's read-only mirror; `legacy/` is untouched. | Same artifacts, no rate limit, no edit of the oracle. Reverse by deleting the init script. | pending: Issues are disabled on the fork and the cloud GitHub proxy refuses repository-settings writes; the owner enables Issues (GitHub → Settings → General → Features), then the next run opens the issue |
| D-002 | 2026-11-07 | The oracle fixture's `tools` Docker stage runs `pip install` behind the cloud proxy, whose CA pip rejects. | `scripts/oracle/tools.Dockerfile` reproduces the upstream stage and can bake an extra CA (`ORACLE_EXTRA_CA`); the fixture is pointed at it with `TEST_OSS_TOOLS_IMAGE` (an upstream-supported variable). CI builds the upstream stage unchanged. | Keeps `legacy/` read-only; the resulting container is identical except for the trusted CA list. | pending: Issues are disabled on the fork and the cloud GitHub proxy refuses repository-settings writes; the owner enables Issues (GitHub → Settings → General → Features), then the next run opens the issue |
| D-003 | 2026-11-07 | Which parity runs gate CI while `rdx` cannot serve yet (Phase 0)? | `parity.yml` runs the legacy baseline matrix; the `rdx` target job is gated on the repository variable `PARITY_RDX_ENABLED=true`, skipped (visibly) until the Phase 1 API skeleton serves `/api/*/system/info`. | A failing or stubbed rdx job would be fake red/fake green; a skipped job claims nothing. | pending: Issues are disabled on the fork and the cloud GitHub proxy refuses repository-settings writes; the owner enables Issues (GitHub → Settings → General → Features), then the next run opens the issue |
| D-004 | 2026-11-07 | Which frontend libraries belong to the Phase 0 scaffold? | Core only (Vue 3.5, Vite, vue-router, Pinia, vue-i18n, PrimeVue 4 Aura, Tailwind 4, Vitest, Playwright, ESLint/Prettier). TanStack Query, CodeMirror, vue-flow, openapi-typescript, Storybook, DOMPurify arrive with their first use in Phase 1. | Every dependency needs a justification (MISSION §8); none of these has a consumer yet. | pending: Issues are disabled on the fork and the cloud GitHub proxy refuses repository-settings writes; the owner enables Issues (GitHub → Settings → General → Features), then the next run opens the issue |

## Resolved

(none yet)
