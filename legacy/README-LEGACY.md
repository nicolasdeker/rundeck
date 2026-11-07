# legacy/ — the original Rundeck sources, pinned (read-only)

This directory is the complete source tree of upstream `rundeck/rundeck` at tag **`v6.3.0`**
(commit `6ac5d092e6ccde3fd580ac61371487a300a0b6ca`, `version.number=6.3.0`), imported with
`git read-tree --prefix=legacy/ -u v6.3.0` during Phase 0 of the rdx mission (see `../MISSION.md`).

It is the **reference and oracle** for the Rust re-implementation in `../crates/`:

- Behavior specs in `../specs/` are written from this code (file:line references point here).
- The functional test suite in `functional-test/` (Spock, `@APITest` / `@SeleniumCoreTest`) is run unchanged
  against the published image `rundeck/rundeck:6.3.0` (baseline) and against the `rdx` binary (parity) by
  `../scripts/parity.sh`.
- Upstream's own agent knowledge base is under `.claude/docs/` and `.claude/rules/` (read `file-locations.md`).

**Rules** (MISSION.md §8): this tree is never edited — not the sources, not the tests. The only file that may change
here is this README. A legacy-specific or wrong upstream test is recorded in `../tests/parity-skips.toml` with a
justification; it is never modified or deleted. To update the pin, fetch the new tag from upstream and re-import the
tree in one commit, then update the tag and commit in this file, `MISSION.md`, and `CLAUDE.md`.

The submodule `packaging/packaging` (gitlink `1ab00442f024703d2c0b9f86719d3e8e171598a4`) is declared in the root
`.gitmodules`; it is not needed for the Rust build and CI checks it out with `submodules: false`.

Licensed under the Apache License 2.0 (see `LICENSE`). Rundeck is a trademark of PagerDuty, Inc.; this project is
not affiliated with or endorsed by PagerDuty (see `../NOTICE`).
