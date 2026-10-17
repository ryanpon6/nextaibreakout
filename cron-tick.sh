#!/usr/bin/env bash
export GROKBOT=1  # /grok-bot/ live, approved by Ryan 2026-10-16
# Cron entry point, runs every 5 min. Catch-up: runs the full refresh only if the last
# successful run is >= 55 min old (so a run missed while the box was paused fires on the next tick).
# SEO2 is passed through unchanged (unset = production). With SEO2=1, run.sh exits 3 and skips the deploy if selfcheck fails.
# Lock: flock prevents overlapping runs. Staleness: logs loudly if the last success is > 90 min old.
set -uo pipefail
cd "$(dirname "$0")"
STAMP=data/last_success; LOG=data/cron.log; now=$(date +%s)
last=$(cat "$STAMP" 2>/dev/null || echo 0); age=$(( (now - last) / 60 ))
if (( age > 90 )); then
  echo "!!!!! STALE $(date -Is): last successful refresh was ${age} min ago ($(date -d @"$last" -Is 2>/dev/null || echo never)). Catching up now. !!!!!" | tee -a data/stale.log >> "$LOG"
fi
(( age < 55 )) && exit 0
exec 9>data/run.lock
flock -n 9 || { echo "[tick $(date -Is)] previous run still in progress; skipping" >> "$LOG"; exit 0; }
echo "===== run $(date -Is) (last success ${age} min ago) =====" >> "$LOG"
if LABS="${LABS:-1}" DEPLOY="${DEPLOY:-1}" SEO2="${SEO2:-0}" timeout 1500 ./run.sh >> "$LOG" 2>&1; then
  date +%s > "$STAMP"; echo "[tick $(date -Is)] OK" >> "$LOG"
else
  echo "!!!!! RUN FAILED $(date -Is) exit=$? !!!!!" | tee -a data/stale.log >> "$LOG"
fi
