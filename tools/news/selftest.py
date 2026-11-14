#!/usr/bin/env python3
"""Negative tests for gate.py: each case breaks one thing on a COPY of a passing build and expects that
check to FAIL. Nothing here touches the real post, ledger, issues file, site or X.
Usage  selftest.py --dist DIR --date YYYY-MM-DD   (DIR and the state files must pass the gate first)"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import nc

def run(dist, state, date, ledger, extra=()):
    env = {**os.environ, "NAB_NEWS_STATE": state, "NAB_LEDGER": ledger, "NAB_AUTOPOST_ISSUES": os.path.join(state, "issues.md"), "PYTHONDONTWRITEBYTECODE": "1"}
    r = subprocess.run([sys.executable, os.path.join(HERE, "gate.py"), "--dist", dist, "--date", date, "--at", f"{date} 17:30", *extra], env=env, text=True, capture_output=True)
    return r.returncode, r.stdout

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dist", required=True); ap.add_argument("--date", required=True); a = ap.parse_args()
    pay0 = nc.load(nc.path("xpayload", a.date)); slug = pay0["slug"]
    cases = [
        ("G3", "rule 19 text", "page", lambda h: h.replace("</article>", "<p>Example coming soon</p></article>")),
        ("G3", "empty img alt", "page", lambda h: re.sub(r'(<img src="/images/news/[^"]+" )alt="[^"]*"', r'\1alt=""', h)),
        ("G4", "retired teal", "page", lambda h: h.replace("</article>", '<p style="color:#274043">x y</p></article>')),
        ("G4", "purple colour", "page", lambda h: h.replace("</article>", '<p style="background:#9B30FF">x y</p></article>')),
        ("G4", "red text", "page", lambda h: h.replace("</article>", '<p style="color:#FF4B2B">x y</p></article>')),
        ("G4", "token drift", "css", lambda c: c.replace("--red:#FF4B2B", "--red:#FF0000", 1)),
        ("G5", "broken internal link", "page", lambda h: h.replace("</article>", '<p><a href="/tips/not-a-real-tip/">x</a></p></article>')),
        ("G5", "http link", "page", lambda h: h.replace("</article>", '<p><a href="http://example.org/">x</a></p></article>')),
        ("G6", "card not in build", "rmimg", None),
        ("G7", "edited quote", "page", lambda h: re.sub(r"(<blockquote><p>)You should get ~7%", r"\1You should get ~20%", h, count=1)),
        ("G7", "invented figure", "pay", lambda p: {**p, "main": {**p["main"], "text": p["main"]["text"] + " Usage is up 40%."}}),
        ("G7", "unverified post link", "page", lambda h: h.replace("</article>", '<p><a href="https://x.com/someone/status/1234567890123">x</a></p></article>')),
        ("G8", "token in page", "page", lambda h: h.replace("</article>", "<p>ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5 z</p></article>")),
        ("G10", "link in main post", "pay", lambda p: {**p, "main": {**p["main"], "text": p["main"]["text"] + " nextaibreakout.com"}}),
        ("G11", "personal name", "page", lambda h: h.replace("</article>", "<p>Thanks Gavin</p></article>")),
        ("G1", "already posted", "ledger", None),
        ("G2", "tip slot window", "at", None),
    ]
    bad = 0
    for want, name, kind, fn in cases:
        t = tempfile.mkdtemp(prefix="nab-gate-test-"); dist = os.path.join(t, "dist"); state = os.path.join(t, "state")
        shutil.copytree(a.dist, dist); shutil.copytree(nc.STATE, state, ignore=shutil.ignore_patterns("*issues*"))
        ledger = os.path.join(t, "posted.jsonl"); shutil.copy(nc.LEDGER, ledger)
        pay = dict(pay0); md = os.path.join(t, os.path.basename(pay["post_md"])); shutil.copy(pay["post_md"], md); pay["post_md"] = md
        pp = os.path.join(dist, "blog", slug, "index.html"); extra = []
        if kind == "page": new = fn(open(pp).read()); open(pp, "w").write(new)
        elif kind == "css": cp = os.path.join(dist, "style.css"); new = fn(open(cp).read()); open(cp, "w").write(new)
        elif kind == "rmimg": os.remove(os.path.join(dist, "images", "news", os.path.basename(pay["og_image"])))
        elif kind == "pay": pay = fn(pay)
        elif kind == "ledger": open(ledger, "a").write(json.dumps({"date": a.date, "slot": nc.slot(a.date), "url": "https://x.com/ryanpon/status/1"}) + "\n")
        nc.save(os.path.join(state, f"xpayload-{a.date}.json"), pay)
        if kind == "at": extra = ["--at", f"{a.date} 06:30"]
        rc, out = run(dist, state, a.date, ledger, extra if kind == "at" else ["--skip-net"] if want != "G5" or "http" in name else [])
        if kind == "at": rc, out = (lambda r: (r.returncode, r.stdout))(subprocess.run([sys.executable, os.path.join(HERE, "gate.py"), "--dist", dist, "--date", a.date, "--skip-net", "--at", f"{a.date} 06:30"], env={**os.environ, "NAB_NEWS_STATE": state, "NAB_LEDGER": ledger, "NAB_AUTOPOST_ISSUES": os.path.join(state, "issues.md")}, text=True, capture_output=True))
        failed = [l for l in out.splitlines() if l.startswith("FAIL")]
        ok = rc == 1 and any(l.startswith(f"FAIL {want} ") for l in failed)
        bad += not ok
        print(f"{'ok  ' if ok else 'MISS'} {want:4} {name:22} -> {(failed[0][:110] if failed else 'no FAIL line')}")
        shutil.rmtree(t, ignore_errors=True)
    print(f"selftest: {len(cases) - bad}/{len(cases)} broken builds caught"); return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
