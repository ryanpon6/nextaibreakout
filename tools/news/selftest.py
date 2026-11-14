#!/usr/bin/env python3
"""Negative tests for gate.py: each case breaks one thing on a COPY of a passing build and expects that check to
FAIL (or G12 to HOLD). Nothing here touches the real post, ledger, issues file, site or X. G7 re-fetches the cited
posts from X's public embed endpoint in every case, so this needs network.
Usage  selftest.py --dist DIR --date YYYY-MM-DD   (the copy must pass the gate with G12 off)"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nc

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dist", required=True); ap.add_argument("--date", required=True)
    ap.add_argument("--show-cost-row", action="store_true", help="print the simulated posting-day cost row"); a = ap.parse_args()
    pay0 = nc.load(nc.path("xpayload", a.date)); slug = pay0["slug"]; d = a.date
    end = lambda extra: (lambda h: h.replace("</article>", extra + "</article>"))
    def tamper_story(s):
        p = s["posts"][[x["id"] for x in s["posts"]].index("2121303079803089179")] if any(x["id"] == "2121303079803089179" for x in s["posts"]) else s["posts"][0]
        p["text"] = p["text"].replace("~7%", "~20%"); return s
    cases = [  # (expect, name, target, mutate, extra gate args, G12 on?)
        ("PASS", "control: unmodified copy", None, None, [], False),
        ("HELD", "G12 on: money/plans story", None, None, [], True),
        ("PASS", "G12 on + --release", None, None, ["--release"], True),
        ("HELD", "G12 story flag sensitive", "story", lambda s: {**s, "sensitive": True}, [], True),
        ("G3", "rule 19 text", "page", end("<p>Example coming soon</p>"), [], False),
        ("G3", "empty img alt", "page", lambda h: re.sub(r'(<img src="/images/news/[^"]+" )alt="[^"]*"', r'\1alt=""', h), [], False),
        ("G4", "retired teal", "page", end('<p style="color:#274043">x y</p>'), [], False),
        ("G4", "purple colour", "page", end('<p style="background:#9B30FF">x y</p>'), [], False),
        ("G4", "red text", "page", end('<p style="color:#FF4B2B">x y</p>'), [], False),
        ("G4", "token drift", "css", lambda c: c.replace("--red:#FF4B2B", "--red:#FF0000", 1), [], False),
        ("G5", "broken internal link", "page", end('<p><a href="/tips/not-a-real-tip/">x</a></p>'), [], False),
        ("G5", "http link", "page", end('<p><a href="http://example.org/">x</a></p>'), [], False),
        ("G6", "card not in build", "rmimg", None, [], False),
        ("G7", "edited quote", "page", lambda h: re.sub(r"(<blockquote><p>)You should get ~7%", r"\1You should get ~20%", h, count=1), [], False),
        ("G7", "tampered story file", "story", tamper_story, [], False),
        ("G7", "tampered story + page", "both", None, [], False),
        ("G7", "invented figure", "pay", lambda p: {**p, "main": {**p["main"], "text": p["main"]["text"] + " Usage is up 40%."}}, [], False),
        ("G7", "dropped qualifier", "spec", lambda s: {**s, "description": s["description"].replace("up to about 15%", "up to 15%")}, [], False),
        ("G7", "SEO title drops 'up to'", "spec", lambda s: {**s, "seo_title": s["seo_title"].replace("up to ~15%", "~15%")}, [], False),
        ("G7", "page meta drops 'up to'", "page", lambda h: h.replace("up to about 15%", "about 15%", 1), [], False),
        ("G7", "'team says', not TEAM", "team", None, [], False),
        ("G7", "X post without quote", "pay", lambda p: {**p, "main": {**p["main"], "text": "Grok Bot plans got about 7% more room, the team says."}}, [], False),
        ("G7", "unverified post link", "page", end('<p><a href="https://x.com/someone/status/1234567890123">x</a></p>'), [], False),
        ("G8", "token in page", "page", end("<p>ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5 z</p>"), [], False),
        ("G10", "link in main post", "pay", lambda p: {**p, "main": {**p["main"], "text": p["main"]["text"] + " nextaibreakout.com"}}, [], False),
        ("G10", "twitter-text weight", "pay", lambda p: {**p, "main": {**p["main"], "text": p["main"]["text"] + " " + "…" * (280 - len(p["main"]["text"]) - 1)}}, [], False),
        ("G11", "personal name", "page", end("<p>Thanks Gavin</p>"), [], False),
        ("G1", "already posted", "ledger", None, [], False),
        ("G2", "tip slot window", None, None, ["--at", f"{d} 06:30"], False),
    ]
    bad = 0
    for want, name, kind, fn, extra, hold in cases:
        t = tempfile.mkdtemp(prefix="nab-gate-test-"); dist = os.path.join(t, "dist"); state = os.path.join(t, "state")
        shutil.copytree(a.dist, dist); shutil.copytree(nc.STATE, state, ignore=shutil.ignore_patterns("*issues*", "held-*"))
        ledger = os.path.join(t, "posted.jsonl"); shutil.copy(nc.LEDGER, ledger)
        cfg = os.path.join(t, "config.json"); json.dump({"hold_money_policy": hold}, open(cfg, "w"))
        pay = dict(pay0); md = os.path.join(t, os.path.basename(pay["post_md"])); shutil.copy(pay["post_md"], md); pay["post_md"] = md
        pp = os.path.join(dist, "blog", slug, "index.html")
        sp, stp = os.path.join(state, f"spec-{d}.json"), os.path.join(state, f"story-{d}.json")
        if kind == "page": new = fn(open(pp).read()); open(pp, "w").write(new)
        elif kind == "css": cp = os.path.join(dist, "style.css"); new = fn(open(cp).read()); open(cp, "w").write(new)
        elif kind == "rmimg": os.remove(os.path.join(dist, "images", "news", os.path.basename(pay["og_image"])))
        elif kind == "pay": pay = fn(pay)
        elif kind == "spec": nc.save(sp, fn(nc.load(sp)))
        elif kind == "story": nc.save(stp, fn(nc.load(stp)))
        elif kind == "both":  # forger edits the story file AND the page consistently; only the re-fetch can catch it
            nc.save(stp, tamper_story(nc.load(stp))); h = open(pp).read(); open(pp, "w").write(re.sub(r"(<blockquote><p>)You should get ~7%", r"\1You should get ~20%", h, count=1))
        elif kind == "ledger": open(ledger, "a").write(json.dumps({"date": d, "slot": nc.slot(d), "url": "https://x.com/ryanpon/status/1"}) + "\n")
        nc.save(os.path.join(state, f"xpayload-{d}.json"), pay)
        env = {**os.environ, "NAB_NEWS_STATE": state, "NAB_LEDGER": ledger, "NAB_AUTOPOST_ISSUES": os.path.join(t, "issues.md"),
               "NAB_DRYRUN": "1", "NAB_NEWS_CONFIG": cfg, "PYTHONDONTWRITEBYTECODE": "1"}
        if kind == "team": env["NAB_NEWS_TEAM"] = "elonmusk"   # Sam and Matt treated as outsiders: "the team says" must now fail
        args = (extra or ["--at", f"{d} 17:30"]) + (["--at", f"{d} 17:30"] if extra and "--at" not in extra else [])
        if want != "G5" or "http" in name: args += ["--skip-net"]
        r = subprocess.run([sys.executable, os.path.join(HERE, "gate.py"), "--dist", dist, "--date", d, "--no-log", *args], env=env, text=True, capture_output=True)
        out = r.stdout; failed = [l for l in out.splitlines() if l.startswith(("FAIL", "HOLD"))]
        if want == "PASS": ok = r.returncode == 0 and not failed
        elif want == "HELD": ok = r.returncode == nc.HELD and any(l.startswith("HOLD G12") for l in failed) and not any(l.startswith("FAIL") for l in failed)
        else: ok = r.returncode == 1 and any(l.startswith(f"FAIL {want} ") for l in failed)
        bad += not ok
        shown = next((l for l in failed if l.startswith(("FAIL " + want, "HOLD"))), failed[0] if failed else out.strip().splitlines()[-1])
        print(f"{'ok  ' if ok else 'MISS'} {want:4} {name:28} exit {r.returncode:<2} -> {shown[:120]}")
        shutil.rmtree(t, ignore_errors=True)
    cbad, cn = cost_cases(d, a.show_cost_row)
    print(f"selftest: {len(cases) - bad}/{len(cases)} gate cases, {cn - cbad}/{cn} cost-log cases behaved as expected"); return 1 if bad or cbad else 0

POSTED_SIM = r"""
import json, os, sys, time
sys.path.insert(0, sys.argv[1]); import nc, publish
d = sys.argv[2]
nc.metrics_update(d, reset=True, start_ts=time.time() - 42, x_reads_agent=9, syndication_fetches=5)
xm = nc.metrics_path(d) + ".xcalls"   # what xnews.py writes via NAB_XNEWS_METRICS
json.dump({"users_me": 1, "timeline_read": 1, "media_upload": 3, "media_metadata": 1, "post": 1, "reply": 1}, open(xm, "w"))
publish.RUN.update(outcome="posted", ai=True, url="https://nextaibreakout.com/blog/x/", x_calls=publish.xcalls(xm))
publish.record(d, 0)
"""

def cost_cases(d, show):
    """Cost log: quiet, failed and posted rows land in $NAB_AUTOPOST_COST with the right fields; dry runs go to dryrun/;
    cost_report totals them and prints nothing for a missing file. No network, no X calls."""
    t = tempfile.mkdtemp(prefix="nab-cost-test-"); state = os.path.join(t, "state"); os.makedirs(state)
    cost, ledger = os.path.join(t, "autopost-cost.jsonl"), os.path.join(t, "posted.jsonl")
    open(ledger, "w").write(json.dumps({"date": d, "slot": nc.slot(d), "tweet_id": "100", "reply_ids": ["101"], "url": "https://x.com/ryanpon/status/100"}) + "\n")
    env = {**os.environ, "NAB_NEWS_STATE": state, "NAB_AUTOPOST_COST": cost, "NAB_LEDGER": ledger, "NAB_AUTOPOST_ISSUES": os.path.join(t, "issues.md"),
           "NAB_AUTOPOST_FLAG": os.path.join(t, "no-such.flag"), "PYTHONDONTWRITEBYTECODE": "1"}
    env.pop("NAB_DRYRUN", None)
    cand = os.path.join(t, "cand.json"); json.dump({"date": d, "x_reads": 6, "stories": []}, open(cand, "w"))
    run = lambda argv, e=env: subprocess.run([sys.executable, *argv], env=e, text=True, capture_output=True)
    last = lambda: (nc.jsonl_rows(cost) or [{}])[-1]
    res = []
    def check(name, ok, info=""):
        res.append(ok); print(f"{'ok  ' if ok else 'MISS'} COST {name:28} {info}"[:170])
    open(ledger + ".q", "w").close()
    r = run([os.path.join(HERE, "fetch.py"), "--date", d, "--candidates", cand], {**env, "NAB_LEDGER": ledger + ".q"}); row = last()
    check("quiet day row", r.returncode == nc.QUIET and row.get("outcome") == "quiet" and row.get("posted") is False and row.get("x_reads_agent") == 6
          and row["x_api_calls"]["total"] == 0 and row.get("ai_writing_step") is False, f"exit {r.returncode} -> {row.get('outcome')}, x_reads {row.get('x_reads_agent')}")
    n0 = len(nc.jsonl_rows(cost))
    r = run([os.path.join(HERE, "fetch.py"), "--date", d, "--candidates", cand, "--dry-run", "--x-reads", "3"], {**env, "NAB_LEDGER": ledger + ".q"})
    dr = nc.jsonl_rows(os.path.join(state, "dryrun", "autopost-cost.jsonl"))
    check("dry run goes to dryrun/", r.returncode == nc.QUIET and len(nc.jsonl_rows(cost)) == n0 and dr and dr[-1].get("x_reads_agent") == 3 and dr[-1].get("outcome") == "dry-run" and dr[-1].get("dry_outcome") == "quiet" and dr[-1].get("posted") is False, f"real rows {len(nc.jsonl_rows(cost))}, dryrun rows {len(dr)}")
    r = run([os.path.join(HERE, "publish.py"), "--date", d]); row = last()
    check("failed row (flag absent)", r.returncode == 1 and row.get("outcome") == "failed:live-flag" and row.get("posted") is False
          and row["x_api_calls"]["total"] == 0 and row.get("ai_writing_step") is False, f"exit {r.returncode} -> {row.get('outcome')}")
    nc.jsonl_append(cost, {"date": d, "run_at": "x", "outcome": "failed:gate", "posted": False, "x_api_calls": {}, "ai_writing_step": True})
    r = run(["-c", POSTED_SIM, HERE, d]); row = last()
    ok = (r.returncode == 0 and row.get("outcome") == "posted" and row.get("posted") is True and row.get("x_post_id") == "100" and row.get("reply_id") == "101"
          and row["x_api_calls"] == {"users_me": 1, "timeline_read": 1, "media_upload": 3, "media_metadata": 1, "post": 1, "reply": 1, "total": 8}
          and row.get("gate_fix_retries") == 1 and row.get("ai_writing_step") is True and row.get("x_reads_agent") == 9 and row.get("syndication_fetches") == 5
          and 40 <= (row.get("wall_seconds") or 0) <= 60 and not os.path.exists(os.path.join(state, f"metrics-{d}.json.xcalls")))
    check("posted row (simulated xnews)", ok, f"-> {row.get('outcome')}, ids {row.get('x_post_id')}/{row.get('reply_id')}, X calls {row.get('x_api_calls', {}).get('total')}" + ("" if r.returncode == 0 else r.stderr[-200:]))
    if show: print(json.dumps(row, indent=1))
    rep = os.path.join(HERE, "cost_report.py")
    r = run([rep, "--file", cost, "--json"]); j = json.loads(r.stdout or "{}").get(d[:7], {})
    check("cost_report totals", j.get("runs") == 4 and j.get("quiet") == 1 and j.get("posted") == 1 and j.get("failed") == 2 and j["x_api_calls"]["total"] == 8
          and j.get("ai_writing_runs") == 2 and j.get("x_reads_agent") == 15, f"runs {j.get('runs')}, quiet {j.get('quiet')}, posted {j.get('posted')}, failed {j.get('failed')}")
    r1 = run([rep, "--file", os.path.join(t, "missing.jsonl")]); r2 = run([rep, "--file", cost, "--month", "1999-01"])
    check("cost_report silent when empty", r1.returncode == 0 and r1.stdout == "" and r2.returncode == 0 and r2.stdout == "", "")
    shutil.rmtree(t, ignore_errors=True)
    return res.count(False), len(res)

if __name__ == "__main__":
    sys.exit(main())
