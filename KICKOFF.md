# KICKOFF — run the rdx mission from an iPhone, without touching the family's Claude usage

Everything is done from the phone: Safari for a few settings pages, the GitHub app and the Claude app for
supervision. No terminal, no VM.

## Budget — why Mode A

The claude.ai subscription has one usage pool per account (5-hour windows + weekly limits), shared by chat, Claude Code,
cloud sessions and scheduled tasks. There is no way to reserve part of it for homework. So the autopilot runs on
**API billing instead** (Mode A): API usage is a separate budget with a hard monthly cap, it never counts against the
plan, and Max/Ultra plans include **$100/month of API credits** (Max) / **$200** (Ultra) that cover exactly this kind of
`claude -p` run. Rules of thumb: a one-hour Sonnet session costs a few dollars; an Opus/Fable session several times
more. The defaults below (2 Sonnet sessions per night at $8 cap + 1 Opus review per week at $30) land around
$150/month, i.e. the included credits plus about $50 — set the Console spend limit to what you accept, and the loop
simply pauses when it is reached.

Mode B (subscription, cloud scheduled task, nights only, Sonnet) is kept as a fallback in §5; it is free but it does
eat into the weekly limit the kids rely on.

## 1. One-time setup for Mode A (≈20 minutes, Safari)

1. **Claude Console** — https://platform.claude.com : sign in with the same account, create an organization if asked.
   - On https://claude.ai → *Settings → Billing → API credits → Link organization*: claims the included monthly credits
     (plan held ≥ 7 days; Max/Ultra only).
   - *API keys → Create key*: name `rdx-autopilot`, copy it once.
   - *Billing / Limits*: set a **monthly spend limit** (e.g. 150 USD). With no payment method on file the runs stop
     when the included credits are used up — the strictest protection.
2. **GitHub personal access token** — https://github.com/settings/personal-access-tokens → *Fine-grained → Generate*:
   repository access `nicolasdeker/rundeck` only; permissions **Contents: Read and write**, **Issues: Read and write**,
   **Workflows: Read and write**, **Actions: Read**. Expiry 90 days (put a reminder). Copy it once.
3. **Repository settings** — https://github.com/nicolasdeker/rundeck/settings/secrets/actions (desktop site if the
   mobile layout hides the menu):
   - Secrets: `ANTHROPIC_API_KEY` = the Console key · `AUTOPILOT_PAT` = the token from step 2.
   - Variables (tab *Variables*): `AUTOPILOT_ENABLED=true` · `AUTOPILOT_MODEL=sonnet` · `AUTOPILOT_EFFORT=high` ·
     `AUTOPILOT_RUN_BUDGET_USD=8` · `AUTOPILOT_REVIEW_MODEL=opus` · `AUTOPILOT_REVIEW_BUDGET_USD=30`.
   - *Settings → Actions → General*: workflow permissions **Read and write**, and allow GitHub Actions to create issues.
4. **Merge the kit (required: Actions only lists workflows that exist on `main`)** —
   https://github.com/nicolasdeker/rundeck/compare/main...claude/rdx-kit → *Create pull request → Merge pull request*.
5. **GitHub App** (optional but recommended, for ad-hoc sessions and Auto-fix): https://github.com/apps/claude → *Install*
   → select `nicolasdeker/rundeck`.

## 2. Bootstrap (Phase 0)

GitHub app or Safari → *Actions → autopilot → Run workflow* → mode `bootstrap`, budget `20` → *Run workflow*.
Expected: 1–3 hours. Follow it in the workflow log; the result is posted as the first comment of the issue
**"Autopilot runs"** (created automatically). If something is missing (secret, permission), the comment says so.
If the run fails at startup with a model/effort error, change `AUTOPILOT_MODEL` / `AUTOPILOT_EFFORT` (e.g. `medium`)
and run again.

Alternative (uses subscription usage once, but gives you a readable transcript): Claude app → **Code** tab →
`nicolasdeker/rundeck` → paste the content of `scripts/prompts/bootstrap.md` (also quoted at the end of this file).

## 3. Recurring runs

Nothing to create: the `autopilot` workflow fires at 01:07 and 04:07 (Europe/Zurich, winter) every night with the
work model, and on Sunday 03:07 with the review model. Each run: locks `autopilot-lock`, works the `← CURRENT` item of
`PLAN.md`, commits and pushes to `main`, writes `JOURNAL.md`, posts cost + summary to the "Autopilot runs" issue.

- **Pause / resume**: variable `AUTOPILOT_ENABLED=false` / `true`.
- **Faster / slower**: edit the two cron lines in `.github/workflows/autopilot.yml` (any run can do it for you:
  comment on a `decision` issue or open an ad-hoc session and say "add a 10:07 weekday run").
- **Stronger model for work runs**: `AUTOPILOT_MODEL=opus` (raise `AUTOPILOT_RUN_BUDGET_USD` accordingly).
- **Manual run now**: *Actions → autopilot → Run workflow* (mode `run` or `review`, optional budget override).

## 4. Daily supervision from the phone

- **GitHub app**: issue **"Autopilot runs"** (one comment per session with cost and summary), commits on `main`,
  *Actions* (`autopilot`, `ci`, `parity`, `nightly`), issues labeled `decision` (answer in a comment: the next run
  applies it and closes the issue) and `blocked`, screenshots under `docs/ui-review/<phase>/`, `JOURNAL.md` and
  `PARITY.md` for the big picture.
- **Claude app**: open an ad-hoc cloud session on the repo to steer ("Update MISSION.md: …", "show me the execution
  page screenshots and explain the choices"); it uses subscription usage, so keep it for real decisions.
- **Console**: https://platform.claude.com → Billing shows the month's API spend and the remaining credits.

## 5. Mode B — subscription instead of API (fallback)

Create the cloud environment `rdx` (https://claude.ai/code → environments → *New*: name `rdx`, network **Trusted**,
variables `BASH_DEFAULT_TIMEOUT_MS=600000`, `BASH_MAX_TIMEOUT_MS=1800000`, `CARGO_TERM_COLOR=never`, setup script
`bash scripts/cloud-setup.sh`), then at https://claude.ai/code/routines → *New task*: name `rdx-autopilot`, trigger
*Schedule → Custom* `7 0,3 * * *`, repository `nicolasdeker/rundeck`, environment `rdx`, model Sonnet / effort high,
prompt = content of `scripts/prompts/run.md`. Set `AUTOPILOT_ENABLED=false` on GitHub so the two modes never overlap.
Expect the weekly limit to be shared with homework use; keep the cadence to nights.

## 6. Decisions already taken for you (reverse any of them with one message)

- Backend contracts identical to Rundeck 6.3.0 (API v14–60, formats, DB schema on Postgres/MySQL, script plugins).
- Frontend rebuilt from scratch: Vue 3 + TypeScript + Vite + PrimeVue 4 + Tailwind 4, mobile-first, live execution
  view over SSE, legacy deep links redirected. (Alternative on file: React 19 — one line in ADR-0004.)
- Embedded DB: SQLite instead of H2 (JVM-only); migration tool provided.
- Java `.jar` plugins and legacy GSP-injected UI plugins: not supported in v1; script plugins unchanged; new WASM plugin ABI.
- Working name `rdx` (Rundeck is a PagerDuty trademark).
- Trunk-based: every run commits and pushes to `main`; phase tags via the GitHub API; one run at a time via the
  `autopilot-lock` branch; Sonnet for routine work, Opus for the weekly review.

---

### Appendix — the bootstrap prompt (`scripts/prompts/bootstrap.md`), for the Claude-app variant
```
Bootstrap the rdx mission in this repository (nicolasdeker/rundeck).

1. If the files CLAUDE.md, MISSION.md and KICKOFF.md are not yet the rdx kit (check for "rdx" in CLAUDE.md), run: git fetch origin claude/rdx-kit && git merge --ff-only origin/claude/rdx-kit (if a fast-forward is impossible, merge normally). Then read CLAUDE.md and MISSION.md fully.
2. Execute MISSION.md §6 "Phase 0 — Bootstrap" completely, following §7 (take the autopilot-lock branch first, push to main after each commit, JOURNAL.md, PLAN.md). Pin legacy to tag v6.3.0 exactly as §6 describes.
3. Operating mode: read KICKOFF.md §"Budget". If this session runs inside GitHub Actions (the GITHUB_ACTIONS environment variable is set), the recurring runs are the autopilot workflow already present in .github/workflows/autopilot.yml — do not create a cloud scheduled task; make sure the workflow's prerequisites are documented in JOURNAL.md under "Owner action required" (secrets ANTHROPIC_API_KEY and AUTOPILOT_PAT, repository variables). If this session runs in a Claude Code cloud session instead, create the cloud scheduled task "rdx-autopilot" with the prompt from scripts/prompts/run.md, schedule custom cron "7 0,3 * * *" (UTC), repository nicolasdeker/rundeck, environment "rdx" (fall back to Default and say so); if you cannot create scheduled tasks from here, write the exact settings in JOURNAL.md under "Owner action required".
4. Release the lock. Finish with a JOURNAL.md entry and a short final message: what exists now, the first CI run URL, what the next run will do, and anything the owner must do from his phone.
```
