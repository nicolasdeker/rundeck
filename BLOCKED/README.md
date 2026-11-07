# BLOCKED/ — items stopped after three failed attempts (MISSION.md §7, rule 8)

One file per blocked item: `BLOCKED/<id>.md`, mirrored by a GitHub issue labeled `blocked`. `<id>` is the PLAN.md
item id (e.g. `P1-07`) or the PARITY.md row (e.g. `api-execution-output`). The weekly review session takes the
oldest file first and spends up to 45 minutes on it with a fresh approach.

Template:

```markdown
# <id> — <one-line title>
- Phase / item: <PLAN.md reference>   - Opened: <ISO date> run <id>   - Issue: #<n>
## Symptoms
What fails, exact commands and outputs (short), oracle spec names.
## Hypotheses tested
1. … (what was tried, result)
2. …
3. …
## What would unblock
Concrete: a legacy fact to confirm, a tool, an owner decision (then also a `decision` issue), an upstream fix.
## Impact
Which PARITY.md rows stay `blocked`, which phase gate it affects, workaround if any.
```

Removing a file (with the fix commit referenced in JOURNAL.md) closes the issue. Never delete a blocked upstream test
to get around a block (MISSION.md §8).
