# rdx kit — mission files for the Rust rebuild of Rundeck (cloud-only, phone-supervised, API-billed)

| File | Purpose |
|------|---------|
| `KICKOFF.md` | **Start here.** The iPhone runbook: budget model, one-time settings, bootstrap, recurring runs, daily supervision. |
| `CLAUDE.md` | Permanent project rules loaded by every Claude Code session (short; points to MISSION.md). |
| `MISSION.md` | The mission brief: parity contract, UI rebuild, governance of deviations, architecture, gates, phases, autonomy protocol, prohibitions, definition of done. |
| `.github/workflows/autopilot.yml` | The unattended loop: nightly work sessions + weekly review, billed to the API key with hard spend caps, results posted to the "Autopilot runs" issue. |
| `scripts/prompts/{bootstrap,run,review}.md` | The three session prompts (single source for the workflow and for the Claude app). |
| `.claude/agents/legacy-analyst.md` | Read-only subagent that mines `legacy/` and writes behavior specs. |
| `.claude/agents/parity-reviewer.md` | Independent reviewer run before closing an area / phase gate. |
| `scripts/cloud-setup.sh` | Setup script of the `rdx` cloud environment (Mode B / ad-hoc sessions). |

These files live on the branch `claude/rdx-kit` of `nicolasdeker/rundeck`; merge it into `main` first (KICKOFF §1.4).
