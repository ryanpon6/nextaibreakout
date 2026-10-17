#!/usr/bin/env python3
"""Freshness gate shared by every runner (GitHub Actions now, box/Worker as fallbacks).
Reads the LIVE https://nextaibreakout.com/data.json 'generated' time, so it works no matter which runner deployed last.
  exit 0 + 'run=true'  -> site is >= MIN_AGE minutes old (or FORCE=1): do a full refresh
  exit 0 + 'run=false' -> fresh enough: skip (cheap no-op)
Also prints 'stale=true' when age > STALE_MIN (missed runs) so the workflow can raise an alarm after refreshing.
If data.json can't be read, it fails open (run=true)."""
import datetime as dt, json, os, sys, urllib.request
URL = os.getenv("LIVE_DATA", "https://nextaibreakout.com/data.json")
MIN_AGE = int(os.getenv("MIN_AGE", "50")); STALE_MIN = int(os.getenv("STALE_MIN", "100"))
try:
    req = urllib.request.Request(URL + "?cb=" + str(int(dt.datetime.now().timestamp())), headers={"User-Agent": "nab-gate/1", "Cache-Control": "no-cache"})
    gen = json.load(urllib.request.urlopen(req, timeout=20))["generated"]
    age = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(gen)).total_seconds() / 60
except Exception as e:
    print(f"gate: could not read live data.json ({e}); failing open", file=sys.stderr); gen, age = None, 10**6
run = os.getenv("FORCE") in ("1", "true") or age >= MIN_AGE
out = {"run": str(run).lower(), "stale": str(age > STALE_MIN).lower(), "age_min": f"{age:.0f}", "generated": gen or ""}
print(f"gate: live generated={gen} age={age:.0f} min -> run={out['run']} stale={out['stale']}", file=sys.stderr)
gh = os.getenv("GITHUB_OUTPUT")
with open(gh, "a") if gh else sys.stdout as f:
    for k, v in out.items(): f.write(f"{k}={v}\n")
