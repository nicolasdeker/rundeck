# rdx kit — mission files for the Rust rebuild of Rundeck (cloud-only, phone-supervised, homework-hours aware)

| File | Purpose |
|------|---------|
| `KICKOFF.md` | **Start here.** The iPhone runbook: budget model (family windows), one-time settings, bootstrap, tuning, supervision. |
| `CLAUDE.md` | Permanent project rules loaded by every Claude Code session (short; points to MISSION.md). |
| `MISSION.md` | The mission brief: parity contract, UI rebuild, governance of deviations, architecture, gates, phases, autonomy protocol, prohibitions, definition of done. |
| `scripts/family-window.sh` | Calendar guard run first by every scheduled session: blocks homework hours (Mon–Fri 16–22, Sat–Sun 9–19), the 5 h buffer before them, and the daily cap. |
| `scripts/prompts/{bootstrap,run,review}.md` | The three session prompts (bootstrap session, `rdx-autopilot` task, `rdx-review` task). |
| `.claude/agents/legacy-analyst.md` | Read-only subagent that mines `legacy/` and writes behavior specs. |
| `.claude/agents/parity-reviewer.md` | Independent reviewer run before closing an area / phase gate. |
| `scripts/cloud-setup.sh` | Setup script of the `rdx` cloud environment (< 5 min, cached). |
| `.github/workflows/autopilot.yml` | Opt-in alternative on API billing (inert until `AUTOPILOT_ENABLED=true`). |

These files live on the branch `claude/rdx-kit` of `nicolasdeker/rundeck`; merge it into `main` first (KICKOFF §1).
