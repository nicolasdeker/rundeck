# rdx kit — mission files for the Rust rebuild of Rundeck (cloud-only, phone-supervised)

| File | Purpose |
|------|---------|
| `KICKOFF.md` | **Start here.** The iPhone runbook: one-time settings, the bootstrap prompt, the scheduled-task prompt, daily supervision. |
| `CLAUDE.md` | Permanent project rules loaded by every Claude Code session (short; points to MISSION.md). |
| `MISSION.md` | The mission brief: parity contract, UI rebuild, governance of deviations, architecture, gates, phases, autonomy protocol, prohibitions, definition of done. |
| `.claude/agents/legacy-analyst.md` | Read-only subagent that mines `legacy/` and writes behavior specs. |
| `.claude/agents/parity-reviewer.md` | Independent reviewer run before closing an area / phase gate. |
| `scripts/cloud-setup.sh` | Setup script of the `rdx` cloud environment (JDK 17, cargo tools, Docker images, pnpm, Gradle warm-up; < 5 min, cached). |

These files live on the branch `claude/rdx-kit` of `nicolasdeker/rundeck`; the bootstrap session merges them into `main`.
