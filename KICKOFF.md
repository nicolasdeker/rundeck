# KICKOFF — run the rdx mission from an iPhone (Claude app + GitHub app), nothing else

Everything below is done from the phone: Safari for two one-time settings pages, the Claude app for sessions,
the GitHub app for supervision. No terminal, no VM.

## 0. One-time setup (≈10 minutes, Safari)

1. **GitHub App** — install the Claude GitHub App on the fork: https://github.com/apps/claude → *Install* → select
   `nicolasdeker/rundeck`. (Gives cloud sessions push access, Auto-fix, and GitHub-event triggers.)
2. **Cloud environment `rdx`** — https://claude.ai/code → environment settings → *New environment*:
   - Name: `rdx` · Network access: **Trusted** (default list is enough: GitHub, Docker Hub, crates.io, npm, Maven, Ubuntu apt).
   - Environment variables:
     ```
     BASH_DEFAULT_TIMEOUT_MS=600000
     BASH_MAX_TIMEOUT_MS=1800000
     CARGO_TERM_COLOR=never
     ```
   - Setup script: `bash scripts/cloud-setup.sh`
   The snapshot is taken the first time the environment is used (after the kit is merged); if a run reports that
   `scripts/cloud-setup.sh` changed, re-save the environment to refresh the snapshot.
3. **Usage** — a run every 2 hours ≈ 12 sessions/day on the subscription. Check https://claude.ai/settings/usage;
   turn on usage credits if the runs must continue past the plan's limit.

## 1. Bootstrap session (Claude app → **Code** tab → `nicolasdeker/rundeck` → environment `rdx` → paste PROMPT 1)

Model: the strongest available (Fable or Opus), effort high or max. Expected duration: 1–3 hours (Phase 0).

### PROMPT 1 — bootstrap
```
Bootstrap the rdx mission in this repository (nicolasdeker/rundeck).

1. Run: git fetch origin claude/rdx-kit && git merge --ff-only origin/claude/rdx-kit (if a fast-forward is impossible, merge normally). Then read CLAUDE.md and MISSION.md fully.
2. Execute MISSION.md §6 "Phase 0 — Bootstrap" completely, following §7 (take the autopilot-lock branch first, push to main after each commit, JOURNAL.md, PLAN.md). Pin legacy to tag v6.3.0 exactly as §6 describes.
3. Create the cloud scheduled task named "rdx-autopilot": prompt = the text under "PROMPT 2" in KICKOFF.md, schedule = custom cron "7 */2 * * *", repository = nicolasdeker/rundeck, environment = "rdx" (fall back to Default if "rdx" does not exist and say so). If you cannot create scheduled tasks from this session, write the exact settings in JOURNAL.md under "Owner action required" so the owner creates it at claude.ai/code/routines.
4. Release the lock. Finish with a JOURNAL.md entry and a short final message: what exists now, the first CI run URL, what the next scheduled run will do, and anything the owner must do from his phone.
```

## 2. Recurring work (scheduled task `rdx-autopilot`)

Created by the bootstrap session, or manually at https://claude.ai/code/routines → *New task*:
name `rdx-autopilot`, trigger *Schedule* → *Custom* → `7 */2 * * *`, repository `nicolasdeker/rundeck`,
environment `rdx`, model Fable/Opus with effort high, prompt = PROMPT 2.

### PROMPT 2 — scheduled run
```
You are a scheduled run of the rdx mission in nicolasdeker/rundeck. CLAUDE.md and MISSION.md in the repository are the contract: read them fully, then follow MISSION.md §7 (autonomy protocol) exactly.

1. Lock: git fetch origin autopilot-lock. If the branch exists, its tip commit message starts with "lock" and its committer date is younger than 3 hours, print "locked, skipping" and stop without changing anything. Otherwise take the lock exactly as §7 describes (a "lock <time> <run>" commit force-pushed to autopilot-lock).
2. Session ritual: tail -n 80 JOURNAL.md, the "← CURRENT" item of PLAN.md, open issues labeled decision/blocked (gh api repos/nicolasdeker/rundeck/issues?labels=decision&state=open — never gh issue/gh pr), latest CI runs (gh run list -L 5; gh run view <id> --log-failed on red), latest parity-report artifact, then make check.
3. Work the ← CURRENT item with the parity loop of MISSION.md §5 (spec → tests → code → oracle/Playwright → review → journal). Commit at every green step and push to main: git push origin HEAD:main. Never create or push any other branch. Never ask the owner anything: decide, record (ADR or DECISIONS-PENDING.md + decision issue), continue. Three failed attempts on one item → BLOCKED/<id>.md + blocked issue, next item.
4. After about 90 minutes of work, or when the item is done: JOURNAL.md entry (Done / Evidence with commit SHAs and CI URLs / Next / Risks), PLAN.md update, commit, push, release the lock (an "unlocked <time>" commit force-pushed to autopilot-lock).
5. If MISSION.md §9 is fully satisfied: write DONE at the repo root, commit, push, pause this scheduled task, open an issue titled "Release v0.1.0 ready".

Final message: item worked, commits (SHAs), CI status, next item, and anything the owner should look at (screenshots under docs/ui-review/, decision issues).
```

## 3. Daily supervision from the phone

- **GitHub app**: commits on `main` (each one is a green step), *Actions* (`ci`, `parity`, `nightly`), issues labeled
  `decision` (answer in a comment: the next run applies it and closes the issue) and `blocked`, screenshots under
  `docs/ui-review/<phase>/`, `JOURNAL.md` and `PARITY.md` for the big picture.
- **Claude app**: open any run from the task's *History* to read what happened, or send it a message to steer.
  To change direction durably: open a session on the repo and say *"Update MISSION.md: …"* — the next runs obey the
  new text. To pause: the task's on/off switch at claude.ai/code/routines.
- **Review UI work**: the screenshots gallery (`docs/ui-review/`) is updated at every phase gate; the journal links it.

## 4. Decisions already taken for you (reverse any of them with one message to a session)

- Backend contracts identical to Rundeck 6.3.0 (API v14–60, formats, DB schema on Postgres/MySQL, script plugins).
- Frontend rebuilt from scratch: Vue 3 + TypeScript + Vite + PrimeVue 4 + Tailwind 4, mobile-first, live execution
  view over SSE, legacy deep links redirected. (Alternative on file: React 19 — one line in ADR-0004.)
- Embedded DB: SQLite instead of H2 (JVM-only); migration tool provided.
- Java `.jar` plugins and legacy GSP-injected UI plugins: not supported in v1; script plugins unchanged; new WASM plugin ABI.
- Working name `rdx` (Rundeck is a PagerDuty trademark).
- Trunk-based: every run commits and pushes to `main`; phase tags `phase-N` (created via the GitHub API); one run at a
  time via the `autopilot-lock` branch.
