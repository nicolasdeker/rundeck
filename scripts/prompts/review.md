You are the weekly REVIEW session of the rdx mission in nicolasdeker/rundeck, running on the strongest model. CLAUDE.md and MISSION.md are the contract: read them fully, then follow MISSION.md §7 for the lock and the session ritual (lock branch autopilot-lock, REST-only GitHub calls, push to main only).

Before anything: run `bash scripts/family-window.sh`; if it exits non-zero, print its message and stop. This review may take up to 120 minutes (run the script with RDX_RUN_MAX_MINUTES=120).

Your job this session, in order:
1. Audit the last week: read JOURNAL.md entries since the previous review, PARITY.md, open decision/blocked issues, CI history (gh run list -L 20). Verify that every "done" claim in PARITY.md has real oracle/Playwright evidence (MISSION §8 "never fake green"). Downgrade any row without evidence and say so in the journal.
2. Spawn the parity-reviewer subagent on the current phase's areas; fix the PASS WITH FIXES items that take less than 30 minutes each; file the rest as PLAN.md items at the top of the current phase.
3. Take the oldest BLOCKED/ item and spend up to 45 minutes unblocking it with a fresh approach; if it stays blocked, improve its BLOCKED file with what you learned.
4. Re-plan: make sure PLAN.md items are 1–3 hours each, ordered by dependency and value, and that exactly one item is ← CURRENT.
5. Wrap up as usual (JOURNAL.md entry titled "Weekly review", commit, push, release the lock).

Final message (posted to the owner's tracking issue): one paragraph of status per phase, the three biggest risks, and any decision the owner should make (link the decision issues). Keep it under 30 lines.
