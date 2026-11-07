#!/usr/bin/env bash
# progress.sh — the owner's progress line: how much of Rundeck 6.3.0 is re-implemented, in percent.
#
# Two honest numbers, both computed from files in git (nothing is estimated):
#   parity %  = PARITY.md rows with status `done` or `deviated` / all rows  (deviated rows are decided by an ADR,
#               blocked and partial rows do not count; the oracle run behind every `done` is cited in the row);
#   phase     = checked / total items of the current phase in PLAN.md, and the number of closed phases (phase-N tags).
# Every scheduled run prints this line at the top of its final message and of its JOURNAL.md entry, and
# `scripts/progress.sh --update-readme` rewrites the status line of README.md between the PROGRESS markers.
# Usage: scripts/progress.sh [--update-readme] [--json]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

parity_rows() { grep -E '^\| [A-Z]+-[0-9]{3} \|' PARITY.md | sed 's/\\|/¦/g'; }  # escaped pipes inside cells are not separators
status_count() { parity_rows | awk -F'|' -v st="$1" '{ gsub(/^ +| +$/, "", $4); if ($4 == st) n++ } END { print n+0 }'; }
total=$(parity_rows | wc -l | tr -d ' ')
done_n=$(status_count done); dev_n=$(status_count deviated); part_n=$(status_count partial)
blk_n=$(status_count blocked); miss_n=$(status_count missing)
credit=$((done_n + dev_n))
pct=$(awk -v c="$credit" -v t="$total" 'BEGIN { printf "%.1f", (t > 0 ? 100.0 * c / t : 0) }')

# per-area breakdown (area prefix → done+deviated/total)
areas=$(parity_rows | awk -F'|' '{ id=$2; gsub(/ /, "", id); split(id, a, "-"); p=a[1]; gsub(/^ +| +$/, "", $4);
  t[p]++; if ($4 == "done" || $4 == "deviated") d[p]++ }
  END { for (p in t) printf "%s %d/%d ", p, d[p]+0, t[p] }' | sed 's/ $//')

# current phase (the heading that contains the ← CURRENT item, else the first heading with an unchecked item)
cur=$(awk '/^## Phase/ { ph=$3 } /← CURRENT/ { print ph; exit }' PLAN.md)
[ -z "$cur" ] && cur=$(awk '/^## Phase/ { ph=$3 } /^- \[ \]/ { print ph; exit }' PLAN.md)
cur=${cur:-0}
ph_total=$(awk -v ph="$cur" '/^## Phase/ { on=($3==ph) } on && /^- \[[ x]\]/ { n++ } END { print n+0 }' PLAN.md)
ph_done=$(awk -v ph="$cur" '/^## Phase/ { on=($3==ph) } on && /^- \[x\]/ { n++ } END { print n+0 }' PLAN.md)
closed=$(git tag -l 'phase-*' 2>/dev/null | wc -l | tr -d ' ')
# tags are created through the REST API and may not be fetched locally; fall back to the remote list when possible
if [ "$closed" = "0" ] && command -v gh >/dev/null 2>&1; then
  closed=$(gh api repos/nicolasdeker/rundeck/git/matching-refs/tags/phase- --jq 'length' 2>/dev/null || echo 0)
fi

line="Progress: parity ${pct}% (${credit}/${total} PARITY.md rows done or deviated; ${part_n} partial, ${blk_n} blocked, ${miss_n} missing) · phase ${cur}: ${ph_done}/${ph_total} items · phases closed: ${closed}/8 · areas: ${areas}"

if [ "${1:-}" = "--json" ]; then
  printf '{"parity_pct":%s,"done":%d,"deviated":%d,"partial":%d,"blocked":%d,"missing":%d,"total":%d,"phase":%s,"phase_done":%d,"phase_total":%d,"phases_closed":%d}\n' \
    "$pct" "$done_n" "$dev_n" "$part_n" "$blk_n" "$miss_n" "$total" "$cur" "$ph_done" "$ph_total" "$closed"
  exit 0
fi
echo "$line"
if [ "${1:-}" = "--update-readme" ]; then
  python3 - "$line" <<'PY'
import re, sys
line = sys.argv[1]; p = 'README.md'; s = open(p).read()
new = f"<!-- PROGRESS:BEGIN -->\n**{line}** (updated by `scripts/progress.sh` at the end of every run)\n<!-- PROGRESS:END -->"
if '<!-- PROGRESS:BEGIN -->' in s:
    s = re.sub(r'<!-- PROGRESS:BEGIN -->.*?<!-- PROGRESS:END -->', lambda m: new, s, flags=re.S)
else:
    s = s.replace("\n## Layout", "\n" + new + "\n\n## Layout", 1)
open(p, 'w').write(s)
PY
  echo "README.md status line updated"
fi
