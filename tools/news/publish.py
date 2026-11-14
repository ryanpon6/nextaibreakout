#!/usr/bin/env python3
"""Step 4: build -> gate -> commit/push -> deploy -> live check -> timing re-check -> X post + link reply -> ledger.

--dry-run (what QC reviews): runs the real build and the real gate on a temp dist, then PRINTS the git, wrangler,
curl, X and ledger steps instead of doing them. No push, no deploy, no X call of any kind, no ledger write.
Dry-run alerts go to news/dryrun-issues.md, never to autopost-issues.md.
Live: refuses to run unless $NAB_AUTOPOST_FLAG (/workspace/shared/nab-relaunch/autopost-live.flag) exists.
  KILL SWITCH: delete that file. The next run stops at step 0 (and logs that it did).
Every failure path writes a dated alert to autopost-issues.md (Chief of Staff relays it; watch_issues.py notices it).
G12 hold: exit 20 (HELD). Draft goes to news/held-DATE.md plus an alert. Release by hand, after reading the draft:
  publish.py --release DATE            (needs the live flag; re-runs build and EVERY gate, only G12 is released)
  publish.py --release DATE --dry-run  (preview of the release)
Ledger rules (posted.jsonl, slot nab-news-DATE):
  complete row (main id + reply id)    -> nothing to do, exit 0
  main id, empty reply_ids             -> reply-only re-run allowed (xnews.py re-checks the timeline first)
  row marked unknown / reply_unknown   -> STOP, "unknown, check by hand"; never retried automatically
Usage  publish.py [--date YYYY-MM-DD] [--dry-run] [--release DATE] [--at "YYYY-MM-DD HH:MM" (dry-run only)]
Exit   0 done / nothing to do · 1 stopped (alert logged) · 20 held by G12"""
import argparse, html, os, shlex, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nc

PROJECT = "nextaibreakout"
PY = sys.executable
XPY = "/workspace/.xvenv/bin/python"
GATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate.py")

def sh(cmd, cwd=nc.ROOT, env=None, show=True):
    if show: print("$ " + (cmd if isinstance(cmd, str) else " ".join(shlex.quote(c) for c in cmd)), flush=True)
    r = subprocess.run(cmd, cwd=cwd, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}, shell=isinstance(cmd, str), text=True, capture_output=True)
    return r.returncode, (r.stdout + r.stderr)

def fail(stage, why, date):
    print(f"STOP at {stage}: {why}"); nc.issue(stage, [why], date); print(f"logged to {nc.ISSUES}"); return 1

def run_gate(dist, d, at=None, release=False):
    """Returns (rc, output). Any crash of the gate itself is a failure, never a pass."""
    cmd = [PY, GATE, "--dist", dist, "--date", d, "--no-log"] + (["--at", at] if at else []) + (["--release"] if release else [])
    try:
        rc, out = sh(cmd)
    except Exception as e:
        return 99, f"gate could not run: {e.__class__.__name__}: {e}"
    if rc not in (0, 1, nc.HELD): return 99, out + f"\ngate crashed (exit {rc})"
    return rc, out

def held(d, pay, spec, gate_out):
    p = os.path.join(nc.STATE, f"held-{d}.md")
    md = open(pay["post_md"], encoding="utf-8").read()
    with open(p, "w", encoding="utf-8") as f:
        f.write(f"# HELD news post {nc.slot(d)} ({nc.now():%Y-%m-%d %H:%M} MT)\n\nG12 held this post because it touches money, pricing, plans, usage limits, billing or policy.\n"
                f"Nothing was pushed, deployed or posted. To publish it as is, after reading it:\n\n    python3 tools/news/publish.py --release {d}\n\n"
                f"(needs the live flag; re-runs the build and every gate). To drop it, do nothing.\n\n"
                f"## Page URL (not live)\n{pay['url']}\n\n## X main post (card attached, no link)\n{pay['main']['text']}\n\n## X reply\n{pay['reply']['text']}\n\n"
                f"## Card files\n- OG / page: {pay['og_image']}\n- X card: {pay['x_card']}\n- alt: {pay['main']['alt']}\n\n## Gate output\n```\n{gate_out.strip()}\n```\n\n## Full page source (blog/posts)\n```markdown\n{md}```\n")
    nc.issue("held", [f"draft: {p}", f"release: python3 tools/news/publish.py --release {d}"], d,
             head=f"HELD: news post '{spec['title']}' waits for a manual release (G12 money/plans/policy hold).")
    print(f"HELD: draft written to {p}; alert logged to {nc.ISSUES}")
    return nc.HELD

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date"); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--at")
    ap.add_argument("--release", metavar="DATE", help="publish a G12-held post after a human read news/held-DATE.md")
    a = ap.parse_args(); dry = a.dry_run; rel = bool(a.release); d = a.release or a.date or nc.today()
    mode = ("DRY-RUN " if dry else "LIVE ") + ("RELEASE" if rel else "")
    if dry:  # a dry run must never raise a real alert for Ryan
        nc.ISSUES = os.environ["NAB_AUTOPOST_ISSUES"] = os.path.join(nc.STATE, "dryrun-issues.md"); os.environ["NAB_DRYRUN"] = "1"
    print(f"== publish {mode.strip()} {nc.slot(d)} at {nc.now():%Y-%m-%d %H:%M} MT, repo {nc.ROOT}")
    flag = os.path.exists(nc.LIVE_FLAG)
    print(f"[0] live flag {nc.LIVE_FLAG}: {'present' if flag else 'ABSENT'}")
    if not dry and not flag: return fail("live-flag", "live publishing is off (autopost-live.flag absent = kill switch); nothing done", d)
    if a.at and not dry: return fail("args", "--at is for dry runs only", d)
    if rel and not os.path.exists(os.path.join(nc.STATE, f"held-{d}.md")): return fail("release", f"no held draft news/held-{d}.md to release", d)
    pay_p = nc.path("xpayload", d)
    try: pay = nc.load(pay_p); spec = nc.load(nc.path("spec", d))
    except Exception as e: return fail("inputs", f"no payload/spec for {d} ({e.__class__.__name__}); run make_post.py first", d)
    url = pay["url"]
    # [1] ledger state (also governs every retry)
    row = nc.in_ledger(d)
    if row and row.get("reply_ids"): print(f"[1] ledger: {nc.slot(d)} already posted {row.get('url')}. Nothing to do."); return 0
    if row and (row.get("status") == "unknown" or row.get("reply_unknown") or not row.get("tweet_id")):
        return fail("ledger", f"{nc.slot(d)} has an UNKNOWN post state in posted.jsonl ({row.get('note', 'ambiguous X response')}); check @ryanpon by hand. Not retried.", d)
    if row:
        print(f"[1] ledger: main post exists ({row.get('url')}) with empty reply_ids -> reply-only re-run (allowed)")
        if dry: print(f"    would run: {XPY} {nc.XNEWS} {pay_p}"); return 0
        rc, out = sh([XPY, nc.XNEWS, pay_p]); print(out)
        return 0 if rc == 0 else fail("x-reply-retry", out.strip()[-300:], d)
    print(f"[1] ledger: {nc.slot(d)} not in {nc.LEDGER}")
    # [2] git
    files = [os.path.relpath(pay["post_md"], nc.ROOT), os.path.relpath(pay["og_image"], nc.ROOT)] + ([os.path.relpath(pay["entries_file"], nc.ROOT)] if pay.get("entries_file") else [])
    git_steps = ["git fetch origin", "git merge --ff-only origin/main", f"git add -- {' '.join(files)}", f"git commit -m {shlex.quote('News: ' + spec['title'])}"]
    if dry:
        print("[2] git (printed only):"); [print("    " + g) for g in git_steps]
    else:
        rc, out = sh("git fetch origin && git rev-parse --abbrev-ref HEAD && git status --porcelain")
        lines = out.strip().splitlines()
        if rc or lines[0] not in ("main", "autopost"): return fail("git", f"live run must be on main or the autopost branch that tracks origin/main (got {lines[:1]})", d)
        dirty = [l for l in lines[1:] if l[3:] not in files and not l[3:].startswith(("static/images/news/", "blog/posts/"))]
        if dirty: return fail("git", f"working tree not clean: {dirty[:5]}", d)
        rc, out = sh("git merge --ff-only origin/main")
        if rc: return fail("git", "cannot fast-forward to origin/main (conflict?) " + out[-200:], d)
    # [3] build + site self-checks
    dist = tempfile.mkdtemp(prefix="nab-news-dist-") if dry else os.path.join(nc.ROOT, "dist")
    print(f"[3] build -> {dist}")
    for cmd in ([PY, "build.py"], [PY, "selfcheck.py", dist], [PY, "cjkcheck.py", os.path.join(dist, "index.html")]):
        rc, out = sh(cmd, env={"NAB_DIST": dist})
        print("    " + (out.strip().splitlines() or [""])[-1])
        if rc: return fail("build", f"{cmd[1]} failed: {out.strip()[-200:]}", d)
    # [4] gate
    print("[4] gate" + (" (--release: G12 released, every other check runs)" if rel else ""))
    rc, out = run_gate(dist, d, a.at, rel); print(out.rstrip())
    if rc == nc.HELD: return held(d, pay, spec, out)
    if rc != 0:
        fl = [l for l in out.splitlines() if l.startswith("FAIL") or "crash" in l or "could not run" in l]
        return fail("gate", " | ".join(fl)[:900] or f"gate exit {rc}", d)
    # [5] commit + push, never force
    if dry:
        print("[5] push (printed only):\n    git push origin HEAD:main   (fast-forward only; on reject: fetch, rebase this one commit, rebuild, re-gate, push once more; never force)")
    else:
        for g in git_steps[2:]:
            rc, out = sh(g)
            if rc: return fail("git", out[-200:], d)
        rc, out = sh("git push origin HEAD:main")
        if rc:
            rc2, out2 = sh("git pull --rebase origin main && git push origin HEAD:main")
            if rc2: return fail("git-push", "push rejected twice; stopped without force. " + out2[-200:], d)
            for cmd in ([PY, "build.py"], [PY, "selfcheck.py", dist]):
                rc, out = sh(cmd, env={"NAB_DIST": dist})
                if rc: return fail("build", "rebuild after rebase failed; post is pushed but NOT deployed or posted. " + out[-200:], d)
            rc, out = run_gate(dist, d, None, rel); print(out.rstrip())
            if rc != 0: return fail("gate", "gate failed after rebase; the post is pushed but NOT deployed or posted", d)
    # [6] deploy (production)
    dep = ("set -a; . \"$HOME/.secrets/cloudflare.env\"; set +a; export CLOUDFLARE_ACCOUNT_ID=\"${CLOUDFLARE_ACCOUNT_ID:-fdc58fb4586f5e0eea17aaebad49c994}\"; "
           f"./node_modules/.bin/wrangler pages deploy {shlex.quote(dist)} --project-name {PROJECT} --branch main --commit-dirty=true")
    if dry: print("[6] deploy (printed only):\n    " + dep.replace(dist, "dist"))
    else:
        rc, out = sh(["bash", "-c", dep], show=False); print("    " + "\n    ".join(l for l in out.splitlines() if "pages.dev" in l or "Success" in l))
        if rc: return fail("deploy", "wrangler deploy failed: " + (out.strip().splitlines() or ["?"])[-1][:200], d)
    # [7] live check: 200 + the post's own title in the HTML + the card image
    img = f"{nc.SITE}/images/news/{os.path.basename(pay['og_image'])}"
    title_html = html.escape(spec["title"], quote=False)
    if dry: print(f"[7] live check (printed only): GET {url} -> 200 and the HTML contains the title '{title_html}'; GET {img} -> 200")
    else:
        ok = False
        for _ in range(8):
            if nc.http_status(img) == 200 and title_html in fetch_text(url): ok = True; break
            time.sleep(15)
        if not ok: return fail("live-check", f"{url} not live with its title after deploy; X post NOT sent", d)
        print(f"[7] live: {url} -> 200 with title")
    # [7b] timing re-check right before X (the deploy can take minutes)
    t = __import__("datetime").datetime.strptime(a.at, "%Y-%m-%d %H:%M").replace(tzinfo=nc.MT) if (dry and a.at) else nc.now()
    blocked, near = nc.tip_window(t)
    if blocked: return fail("timing", f"{t:%H:%M} MT is within {nc.SLOT_GAP_MIN} min of the {near:%-I:%M %p} MT tip slot; site post is live, X post NOT sent (rerun after the window)", d)
    print(f"[7b] timing re-check: {t:%H:%M} MT clear of tip slots")
    # [8] X post + reply + ledger (xnews.py re-checks the ledger and the timeline itself)
    print("[8] X post via xnews.py" + (" --dry-run (no network)" if dry else ""))
    env = {"NAB_RELEASED": "1"} if rel else {}
    rc, out = sh([XPY, nc.XNEWS, pay_p] + (["--dry-run"] if dry else []), env=env); print(out.rstrip())
    if rc: return fail("x-post", out.strip()[-300:], d)
    print(f"== {mode.strip()} DONE: {url}")
    return 0

def fetch_text(url):
    import urllib.request
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": nc.UA}), timeout=20) as r:
            return r.read().decode("utf-8", "replace") if r.status == 200 else ""
    except Exception: return ""

if __name__ == "__main__":
    sys.exit(main())
