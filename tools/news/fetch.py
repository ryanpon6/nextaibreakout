#!/usr/bin/env python3
"""Step 1 (no AI): verify, dedupe and pick today's news story.

Input  candidates-YYYY-MM-DD.json in $NAB_NEWS_STATE, written by the routine's agent from Grok Bot's public X
       read tools (namespace "x": search_news, search_posts_all, get_posts_by_ids). Format: see README.md.
Work   re-reads every post from X's public embed endpoint (no login, no X API spend), keeps posts it could
       verify, drops anything already in trend-log.md or an existing site post, applies the 24h window and a
       notability bar, and ranks Grok Bot stories above Claude stories.
Output story-YYYY-MM-DD.json with the picked story and the verified post text the gate checks quotes against.
Exit   0 = a story was picked (AI writes the post) · 10 = quiet day (stop, no AI) · 2 = bad input.
Cost   every run starts a fresh run record (news/metrics-DATE.json) with the agent's X read count
       (--x-reads N, or "x_reads" in the candidates file) and this script's embed fetches. A quiet day or bad
       input also appends its row to autopost-cost.jsonl here (dry runs: news/dryrun/).
Usage  fetch.py [--date YYYY-MM-DD] [--candidates PATH] [--log-trends] [--x-reads N] [--dry-run]"""
import argparse, datetime as dt, glob, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nc

TEAM = {"elonmusk", "xai", "grok", "bot", "samsokolin", "mattyp", "poteto", "romanugarte_"}  # Elon + Grok Bot team accounts seen in real posts
MIN_LIKES = 500          # biggest verified post in the story must clear this, unless a team account posted it
MIN_TEAM_LIKES = 200
WINDOW_H = 24
TOPIC_RANK = {"grokbot": 0, "claude": 1}

def seen_ids():
    ids, keys = set(), set()
    if os.path.exists(nc.TREND_LOG):
        ids |= set(re.findall(r"/status/(\d+)", open(nc.TREND_LOG, encoding="utf-8").read()))
    for p in glob.glob(os.path.join(nc.POSTS, "*.md")):
        s = open(p, encoding="utf-8").read()
        ids |= set(re.findall(r"/status/(\d+)", s))
        m = re.search(r"^story_key:\s*\"?([\w-]+)", s, re.M)
        if m: keys.add(m.group(1))
    return ids, keys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=nc.today()); ap.add_argument("--candidates")
    ap.add_argument("--log-trends", action="store_true", help="append today's scan to trend-log.md")
    ap.add_argument("--x-reads", type=int, help="X tool reads the routine agent made (else candidates 'x_reads')")
    ap.add_argument("--dry-run", action="store_true", help="cost row and run record go to news/dryrun/")
    a = ap.parse_args()
    if a.dry_run: os.environ["NAB_DRYRUN"] = "1"
    rc = run(a); return rc

def run(a):
    t0 = time.time()
    def done(rc, outcome=None, note=None):
        reads = a.x_reads if a.x_reads is not None else xr
        nc.metrics_update(a.date, x_reads_agent=reads, syndication_fetches=nc.SYND_CALLS)
        if outcome: nc.cost_row(a.date, outcome, wall_seconds=round(time.time() - t0, 1), note=note)
        return rc
    xr = None
    nc.metrics_update(a.date, reset=True, start_ts=t0, x_reads_agent=a.x_reads, syndication_fetches=0)
    src = a.candidates or nc.path("candidates", a.date)
    try:
        c = nc.load(src); stories = c["stories"]; assert isinstance(stories, list)
        xr = c.get("x_reads") if isinstance(c.get("x_reads"), int) else None
    except Exception as e:
        print(f"BAD INPUT {src}: {e.__class__.__name__}"); return done(2, "failed:fetch", f"bad input {e.__class__.__name__}")
    if nc.in_ledger(a.date):
        print(f"QUIET: slot {nc.slot(a.date)} already posted"); return done(nc.QUIET, "quiet", "slot already posted")
    ids, keys = seen_ids()
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=WINDOW_H)
    picked, log = [], []
    for s in stories:
        key = re.sub(r"[^a-z0-9-]", "", str(s.get("key", "")).lower())[:60]
        topic = s.get("topic") if s.get("topic") in TOPIC_RANK else None
        if not key or not topic: log.append(f"skip story with bad key/topic: {s.get('key')!r}"); continue
        posts = []
        for pid in dict.fromkeys(str(i) for i in s.get("post_ids", [])):
            if not pid.isdigit(): continue
            v = nc.syndication(pid)
            if not v or not v["user"]: log.append(f"{key}: {pid} not verifiable on the public embed endpoint, dropped"); continue
            v["url"] = f"https://x.com/{v['user']}/status/{v['id']}"
            v["team"] = v["user"].lower() in TEAM
            posts.append(v)
        if not posts: log.append(f"{key}: no verified posts"); continue
        posts.sort(key=lambda p: (-p["team"], -p["likes"]))
        newest = max(dt.datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")) for p in posts)
        top = max(posts, key=lambda p: p["likes"])
        dup = key in keys or top["id"] in ids or posts[0]["id"] in ids
        team_likes = max([p["likes"] for p in posts if p["team"]] or [0])
        notable = top["likes"] >= MIN_LIKES or team_likes >= MIN_TEAM_LIKES
        why = ("already covered (trend-log or site post)" if dup else "older than 24h" if newest < cutoff
               else f"not notable (top {top['likes']} likes)" if not notable else "")
        log.append(f"{key} [{topic}]: {len(posts)} verified, top @{top['user']} {top['likes']} likes" + (f" -> skip: {why}" if why else " -> eligible"))
        if why: continue
        picked.append({"key": key, "topic": topic, "headline": str(s.get("headline", ""))[:200], "sensitive": bool(s.get("sensitive")),
                       "news_url": s.get("news_url") if str(s.get("news_url", "")).startswith("https://x.com/") else None,
                       "score": sum(p["likes"] for p in posts), "posts": posts})
    for ln in log: print("  " + ln)
    if a.log_trends: append_trends(a.date, log, picked)
    if not picked:
        print("QUIET: no new notable Grok Bot or Claude story in the last 24h"); return done(nc.QUIET, "quiet")
    picked.sort(key=lambda s: (TOPIC_RANK[s["topic"]], -s["score"]))
    best = picked[0]; best.update(date=a.date, picked_at=nc.now().isoformat(), candidates_file=src)
    out = nc.path("story", a.date); nc.save(out, best)
    print(f"STORY {best['key']} ({best['topic']}, {len(best['posts'])} verified posts) -> {out}")
    return done(0)

def append_trends(date, log, picked):
    with open(nc.TREND_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n## {date} — news scan {nc.now():%-I:%M %p} MT (tools/news/fetch.py)\n")
        for s in picked:
            for p in s["posts"][:3]: f.write(f"- {s['key']}: @{p['user']} {p['url']} ({p['likes']} likes)\n")
        for ln in log:
            if "skip" in ln: f.write(f"- seen, not used: {ln}\n")

if __name__ == "__main__":
    sys.exit(main())
