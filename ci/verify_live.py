#!/usr/bin/env python3
"""Post-deploy check against the LIVE site (fresh, cache-busted fetches). Exit 1 on any failure.
Checks: data.json 'generated' equals the run just built (data/scored-seo2.json), homepage og:image/twitter:image are
/og-default.png and that file returns an image, /grok-bot/ returns 200, homepage shows the same run time.
Retries for up to ~2 min because Pages propagation takes a few seconds."""
import datetime as dt, json, os, re, sys, time, urllib.request
SITE = os.getenv("SITE", "https://nextaibreakout.com"); ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def get(p):
    r = urllib.request.urlopen(urllib.request.Request(f"{SITE}{p}{'&' if '?' in p else '?'}cb={time.time_ns()}", headers={"User-Agent": "nab-verify/1", "Cache-Control": "no-cache"}), timeout=20)
    return r.status, r.headers.get("content-type", ""), r.read()
want = os.getenv("EXPECT_GENERATED") or json.load(open(os.path.join(ROOT, "data", "scored-seo2.json")))["generated"]
for attempt in range(8):
    fails = []
    try:
        s, _, b = get("/data.json"); gen = json.loads(b).get("generated")
        if gen != want: fails.append(f"data.json generated {gen} != built {want}")
        s, _, h = get("/"); h = h.decode()
        for tag in ('property="og:image"', 'name="twitter:image"'):
            m = re.search(r'<meta ' + tag + r' content="([^"]+)"', h)
            if not m or not m.group(1).endswith("/og-default.png"): fails.append(f"homepage {tag} = {m.group(1) if m else None}")
        stamp = dt.datetime.fromisoformat(want).strftime("%b %d, %Y %H:%M UTC")
        if stamp not in h: fails.append(f"homepage does not show last run {stamp}")
        s, ct, b = get("/og-default.png")
        if s != 200 or not ct.startswith("image/") or len(b) < 5000: fails.append(f"og-default.png {s} {ct} {len(b)}B")
        s, _, g = get("/grok-bot/")
        if s != 200 or b"Grok Bot" not in g: fails.append(f"/grok-bot/ {s}")
    except Exception as e:
        fails.append(f"fetch error: {e}")
    if not fails: print(f"verify: OK (live run {want})"); sys.exit(0)
    print(f"verify attempt {attempt + 1}: " + "; ".join(fails)); time.sleep(15)
sys.exit(1)
