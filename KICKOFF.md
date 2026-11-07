# KICKOFF — run the rdx mission from an iPhone, around the family's homework hours

Everything is done from the phone: Safari for two settings pages, the Claude app and the GitHub app for supervision.
No terminal, no VM, no API key.

## The budget model

The claude.ai subscription is one usage pool per account: a 5-hour session window that starts with the first message,
plus weekly limits, shared by chat, Claude Code, cloud sessions and scheduled tasks. Nothing lets you reserve part of
it for the kids, so the autopilot protects their hours by **not running when it would hurt**:

- Protected (Europe/Zurich): **Mon–Fri 16:00–22:00**, **Sat–Sun 09:00–19:00**.
- Buffer: a run never *starts* within 5 h (+ its own 75-minute cap) before a protected window, so the usage session the
  agent opened is over when the kids send their first message.
- Daily cap: `RDX_MAX_RUNS_PER_DAY` runs per day (default **2**) with a Sonnet-class model, to keep the weekly limit
  under control. The weekly limit is the one thing no calendar can protect: it is shared whatever the hour. You tune
  the cap from the usage page (see §3).

Everything above is enforced by `scripts/family-window.sh`, which every scheduled run executes first. Effective slots:
weeknights 01:37, 04:37, 07:37 (cap 2 → two of them), weekends 01:37 and 19:37, plus the Sunday 22:37 review.

## 1. One-time setup (≈10 minutes, Safari)

1. **GitHub App** — https://github.com/apps/claude → *Install* → select `nicolasdeker/rundeck` (push access for cloud
   sessions, Auto-fix). Then merge the kit: https://github.com/nicolasdeker/rundeck/compare/main...claude/rdx-kit →
   *Create pull request → Merge pull request*.
2. **Cloud environment `rdx`** — https://claude.ai/code → environments → *New environment*:
   - Name `rdx` · Network access **Trusted**.
   - Variables: `BASH_DEFAULT_TIMEOUT_MS=600000`, `BASH_MAX_TIMEOUT_MS=1800000`, `CARGO_TERM_COLOR=never`.
     Optional tuning: `RDX_MAX_RUNS_PER_DAY=2`, `RDX_RUN_MAX_MINUTES=75`.
   - Setup script: `if [ -d rundeck ]; then bash rundeck/scripts/cloud-setup.sh; fi` — the environment runs it from the
     parent of the checkout, not from the repository root (snapshot taken on first use; re-save the environment when a run reports
     that the script changed).
3. **Usage settings** — https://claude.ai/settings/usage : note the weekly reset day. Leave *usage credits / extra usage*
   **off** unless you want the plan to keep going on paid credits once the weekly limit is reached (that would protect
   the kids from being blocked, at a cost; the autopilot itself never enables anything).

## 2. Bootstrap (Phase 0) — Claude app → **Code** tab → `nicolasdeker/rundeck` → environment `rdx`

Start it in an allowed slot (a weeknight or before 10:45 on a weekday; before 03:45 or after 19:00 at the weekend), or
accept that this one supervised session spends daytime usage. Model: strongest available, effort high. Paste the content
of `scripts/prompts/bootstrap.md` (quoted at the end of this file). Expected: 1–3 hours. It merges nothing you have not
merged, moves the Java tree to `legacy/` pinned at v6.3.0, creates the workspace, CI, oracle scripts, `PARITY.md`, the
ADRs — and creates the two scheduled tasks:

- `rdx-autopilot` — `CRON_TZ=Europe/Zurich 37 1,4,7,10,13,16,19 * * *` (the guard filters the slots), Sonnet, effort high.
- `rdx-review` — `CRON_TZ=Europe/Zurich 37 22 * * 0` (Sunday night), strongest model.

Check them at https://claude.ai/code/routines (each has an on/off switch and a *Run now*). If the session could not
create them, its final message and `JOURNAL.md` ("Owner action required") give the exact settings to enter there:
prompt = content of `scripts/prompts/run.md` / `review.md`, repository, environment `rdx`, automatic approval.

## 3. Tuning after the first week

Open https://claude.ai/settings/usage on the reset day:
- weekly usage ≤ 50 % → raise `RDX_MAX_RUNS_PER_DAY` to 3 (environment variable), or switch `rdx-autopilot` to a
  stronger model;
- 50–80 % → leave as is;
- > 80 %, or the kids hit a limit once → lower the cap to 1 or pause `rdx-autopilot` for the week.
The protected windows themselves are a constant: to change them, edit the two lines in `scripts/family-window.sh`
(any ad-hoc session will do it for you: "move the weekday window to 15:30–22:30").

## 4. Daily supervision from the phone

- **Claude app**: *Code → Scheduled tasks* shows each run (blocked runs end in a few seconds with the guard's message —
  that is normal and costs nothing meaningful); open a run to read what happened; open an ad-hoc session to steer
  ("Update MISSION.md: …"). Ad-hoc sessions spend usage — keep them for real decisions, ideally in allowed slots.
- **GitHub app**: commits on `main`, *Actions* (`ci`, `parity`, `nightly`), issues labeled `decision` (answer in a
  comment: the next run applies it and closes the issue) and `blocked`, screenshots under `docs/ui-review/<phase>/`,
  `JOURNAL.md` and `PARITY.md` for the big picture.
- **Pause / resume**: the task switches at https://claude.ai/code/routines.

## 5. Opt-in alternative: buy throughput with API credits (Mode B)

If progress is too slow for your taste, the repository also carries `.github/workflows/autopilot.yml`, which runs the
same sessions on an API key with a hard per-run spend cap, outside the subscription entirely (Max/Ultra plans include
$100/$200 of monthly API credits that cover `claude -p` runs). It is inert until you set the repository variable
`AUTOPILOT_ENABLED=true`, the secrets `ANTHROPIC_API_KEY` and `AUTOPILOT_PAT` (fine-grained token: Contents, Issues,
Workflows read/write), and the variables `AUTOPILOT_MODEL`, `AUTOPILOT_RUN_BUDGET_USD`, `AUTOPILOT_REVIEW_MODEL`,
`AUTOPILOT_REVIEW_BUDGET_USD`. Pause the scheduled tasks while it is on, so the two never overlap.

## 6. Decisions already taken for you (reverse any of them with one message)

- Backend contracts identical to Rundeck 6.3.0 (API v14–60, formats, DB schema on Postgres/MySQL, script plugins).
- Frontend rebuilt from scratch: Vue 3 + TypeScript + Vite + PrimeVue 4 + Tailwind 4, mobile-first, live execution
  view over SSE, legacy deep links redirected. (Alternative on file: React 19 — one line in ADR-0004.)
- Embedded DB: SQLite instead of H2 (JVM-only); migration tool provided.
- Java `.jar` plugins and legacy GSP-injected UI plugins: not supported in v1; script plugins unchanged; new WASM plugin ABI.
- Working name `rdx` (Rundeck is a PagerDuty trademark).
- Trunk-based: every run commits and pushes to `main`; phase tags via the GitHub API; one run at a time via the
  `autopilot-lock` branch; Sonnet for routine work, strongest model for the Sunday review.

---

### Appendix — the bootstrap prompt (`scripts/prompts/bootstrap.md`)
```
Bootstrap the rdx mission in this repository (nicolasdeker/rundeck).

1. If the files CLAUDE.md, MISSION.md and KICKOFF.md are not yet the rdx kit (check for "rdx" in CLAUDE.md), run: git fetch origin claude/rdx-kit && git merge --ff-only origin/claude/rdx-kit (if a fast-forward is impossible, merge normally). Then read CLAUDE.md and MISSION.md fully.
2. Execute MISSION.md §6 "Phase 0 — Bootstrap" completely, following §7 (take the autopilot-lock branch first, push to main after each commit, JOURNAL.md, PLAN.md). Pin legacy to tag v6.3.0 exactly as §6 describes.
3. Recurring runs: create the cloud scheduled task "rdx-autopilot" with the prompt from scripts/prompts/run.md, cron "CRON_TZ=Europe/Zurich 37 1,4,7,10,13,16,19 * * *" (scripts/family-window.sh decides at run time whether a slot is allowed), repository nicolasdeker/rundeck, environment "rdx" (fall back to Default and say so). Also create "rdx-review" with scripts/prompts/review.md and cron "CRON_TZ=Europe/Zurich 37 22 * * 0" (Sunday 22:37). Both tasks: automatic approval; use the strongest model available for the review task and a Sonnet-class model for the work task when the tool lets you choose. If you cannot create scheduled tasks from this session, write the exact settings in JOURNAL.md under "Owner action required" so the owner creates them at claude.ai/code/routines. Do not enable the GitHub Actions autopilot workflow (it is the opt-in API-billed alternative).
4. Release the lock. Finish with a JOURNAL.md entry and a short final message: what exists now, the first CI run URL, what the next run will do, and anything the owner must do from his phone.
```
