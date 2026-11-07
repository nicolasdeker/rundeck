#!/usr/bin/env bash
# family-window.sh — may an autopilot run start now? exit 0 = yes, exit 3 = no (reason printed).
#
# The family uses the same claude.ai subscription for homework. Protected windows (Europe/Zurich):
#   Mon–Fri 16:00–22:00, Sat–Sun 09:00–19:00.
# A plan "session" is a 5-hour usage window that starts with the first message, so an autopilot run must
# START at least 5 hours (+ its own max duration) before a protected window opens, and never during one.
# A daily cap keeps the weekly limit under control; tune it from the usage page (see KICKOFF.md).
#
# Env knobs: RDX_RUN_MAX_MINUTES (default 75), RDX_MAX_RUNS_PER_DAY (default 2), RDX_FORCE=1 to bypass (ad-hoc only),
# RDX_NOW="YYYY-MM-DD HH:MM" (local time) to test the calendar logic.
set -u
export TZ=Europe/Zurich
[ "${RDX_FORCE:-0}" = "1" ] && { echo "ok: forced"; exit 0; }

at=${RDX_NOW:-now}                                # RDX_NOW="2026-11-09 07:37" (local) for tests
dow=$(date -d "$at" +%u)                          # 1=Mon … 7=Sun
now=$(( 10#$(date -d "$at" +%H) * 60 + 10#$(date -d "$at" +%M) ))   # minutes since midnight, local
run_max=${RDX_RUN_MAX_MINUTES:-75}
buffer=300                                        # the plan's 5-hour usage session

if [ "$dow" -ge 6 ]; then ps=$((9*60));  pe=$((19*60)); label="weekend 09:00–19:00"
else                      ps=$((16*60)); pe=$((22*60)); label="weekday 16:00–22:00"; fi

if [ "$now" -ge $(( ps - buffer - run_max )) ] && [ "$now" -lt "$pe" ]; then
  echo "blocked: family window ($label) or its 5h buffer — now $(date -d "$at" "+%a %H:%M %Z")"; exit 3
fi

today=$(date -u -d "$at" +%F)                     # JOURNAL headings use ISO-8601 UTC dates
runs_today=$(grep -c "^## ${today}" JOURNAL.md 2>/dev/null || true)
runs_today=${runs_today:-0}
cap=${RDX_MAX_RUNS_PER_DAY:-2}
if [ "$runs_today" -ge "$cap" ]; then
  echo "blocked: daily cap reached ($runs_today/$cap runs journaled today)"; exit 3
fi

echo "ok: $(date -d "$at" '+%a %H:%M %Z'), runs today $runs_today/$cap, max run ${run_max} min, must finish by $(printf %02d:%02d $(( (ps - buffer) / 60 )) $(( (ps - buffer) % 60 )))"
exit 0
