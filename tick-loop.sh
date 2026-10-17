#!/usr/bin/env bash
# STOPGAP scheduler (2026-10-17): the box was rebuilt at 04:58 MT without the cron package, so the */5 crontab is gone.
# Runs cron-tick.sh every 5 minutes (cron-tick only does a full refresh when the last success is >= 55 min old).
# Single instance via flock on data/tick-loop.lock. Start (survives the shell exiting):
#   setsid nohup ./tick-loop.sh >/dev/null 2>&1 < /dev/null &
# Stop: kill "$(cat data/tick-loop.pid)"
cd "$(dirname "$0")"
exec 8>data/tick-loop.lock
flock -n 8 || { echo "tick-loop already running (pid $(cat data/tick-loop.pid 2>/dev/null))"; exit 0; }
echo $$ > data/tick-loop.pid
echo "[tick-loop $(date -Is)] started pid $$" >> data/cron.log
while true; do
  PATH=/usr/local/bin:/usr/bin:/bin LABS=1 SEO2=1 DEPLOY=1 ./cron-tick.sh 9>&- 8>&- || echo "[tick-loop $(date -Is)] cron-tick exit $?" >> data/cron.log
  sleep $(( 300 - $(date +%s) % 300 ))   # align to :00, :05, :10 ...
done
