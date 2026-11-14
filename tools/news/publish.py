#!/usr/bin/env python3
"""Step 4: build -> gate -> commit/push -> deploy -> live check -> X post + link reply -> ledger.

--dry-run (what QC reviews): runs the real build and the real gate on a temp dist, then PRINTS the git, wrangler,
curl, X and ledger steps instead of doing them. No push, no deploy, no X call of any kind, no ledger write.
Live: refuses to run unless $NAB_AUTOPOST_FLAG (/workspace/shared/nab-relaunch/autopost-live.flag) exists. That
file stays absent until Quality Checker passes the pipeline. Live must run from a clean checkout of origin/main.
Any failure: reason appended to autopost-issues.md (Chief of Staff relays it to Ryan) and a non-zero exit.
Usage  publish.py [--date YYYY-MM-DD] [--dry-run] [--at "YYYY-MM-DD HH:MM"  (dry-run only: timing as of then)]"""
import argparse, os, shlex, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nc

PROJECT = "nextaibreakout"
PY = sys.executable
XPY = "/workspace/.xvenv/bin/python"

def sh(cmd, cwd=nc.ROOT, env=None, show=True):
    if show: print("$ " + (cmd if isinstance(cmd, str) else " ".join(shlex.quote(c) for c in cmd)), flush=True)
    r = subprocess.run(cmd, cwd=cwd, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}, shell=isinstance(cmd, str), text=True, capture_output=True)
    return r.returncode, (r.stdout + r.stderr)

def fail(stage, why, date):
    print(f"STOP at {stage}: {why}"); nc.issue(stage, [why], date); print(f"logged to {nc.ISSUES}"); return 1

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=nc.today()); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--at")
    a = ap.parse_args(); d = a.date; dry = a.dry_run; mode = "DRY-RUN" if dry else "LIVE"
    if dry:  # a dry run must never raise a real alert for Ryan; its failures go to a separate file
        nc.ISSUES = os.environ["NAB_AUTOPOST_ISSUES"] = os.path.join(nc.STATE, "dryrun-issues.md")
    print(f"== publish {mode} {nc.slot(d)} at {nc.now():%Y-%m-%d %H:%M} MT, repo {nc.ROOT}")
    flag = os.path.exists(nc.LIVE_FLAG)
    print(f"[0] live flag {nc.LIVE_FLAG}: {'present' if flag else 'ABSENT'}")
    if not dry and not flag: print("STOP: live publishing is off (flag absent). Nothing done."); return 1
    if a.at and not dry: print("STOP: --at is for dry runs only"); return 1
    pay_p = nc.path("xpayload", d)
    try: pay = nc.load(pay_p)
    except Exception: return fail("inputs", f"no payload {pay_p}; run make_post.py first", d)
    url, slug = pay["url"], pay["slug"]
    # [1] duplicate check before anything else (also covers retries)
    row = nc.in_ledger(d)
    if row and row.get("reply_ids"): print(f"[1] ledger: {nc.slot(d)} already posted {row.get('url')}. Nothing to do."); return 0
    if row:
        print(f"[1] ledger: main post exists ({row.get('url')}) but no reply. Retrying the reply only.")
        if dry: print(f"    would run: {XPY} {nc.XNEWS} {pay_p}"); return 0
        rc, out = sh([XPY, nc.XNEWS, pay_p]); print(out); return 0 if rc == 0 else fail("x-reply-retry", out.strip()[-300:], d)
    print(f"[1] ledger: {nc.slot(d)} not in {nc.LEDGER}")
    # [2] git: live needs a clean origin/main checkout with only today's post files added
    files = [os.path.relpath(pay["post_md"], nc.ROOT), os.path.relpath(pay["og_image"], nc.ROOT)] + ([os.path.relpath(pay["entries_file"], nc.ROOT)] if pay.get("entries_file") else [])
    git_steps = ["git fetch origin", "git merge --ff-only origin/main", f"git add -- {' '.join(files)}",
                 f"git commit -m {shlex.quote('News: ' + nc.load(nc.path('spec', d))['title'])}"]
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
    print("[4] gate")
    gcmd = [PY, os.path.join(os.path.dirname(__file__), "gate.py"), "--dist", dist, "--date", d] + (["--at", a.at] if a.at else [])
    rc, out = sh(gcmd); print(out.rstrip())
    if rc: print("STOP: gate failed, nothing published (reasons logged by the gate)"); return 1
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
            print("    origin/main moved; rebased and pushed. Rebuilding on the new base before deploy.")
            for cmd in ([PY, "build.py"], [PY, "selfcheck.py", dist]):
                rc, out = sh(cmd, env={"NAB_DIST": dist})
                if rc: return fail("build", out[-200:], d)
            rc, out = sh(gcmd); print(out.rstrip())
            if rc: return fail("gate", "gate failed after rebase; the post is pushed but NOT deployed or posted", d)
    # [6] deploy (production)
    dep = ("set -a; . \"$HOME/.secrets/cloudflare.env\"; set +a; export CLOUDFLARE_ACCOUNT_ID=\"${CLOUDFLARE_ACCOUNT_ID:-fdc58fb4586f5e0eea17aaebad49c994}\"; "
           f"./node_modules/.bin/wrangler pages deploy {shlex.quote(dist)} --project-name {PROJECT} --branch main --commit-dirty=true")
    if dry: print("[6] deploy (printed only):\n    " + dep.replace(dist, "dist"))
    else:
        rc, out = sh(["bash", "-c", dep], show=False); print("    " + "\n    ".join(l for l in out.splitlines() if "pages.dev" in l or "Success" in l or "Deployment" in l))
        if rc: return fail("deploy", "wrangler deploy failed: " + out.strip().splitlines()[-1][:200], d)
    # [7] live check
    if dry: print(f"[7] live check (printed only): GET {url} must return 200 with the post title, and GET {nc.SITE}/images/news/{os.path.basename(pay['og_image'])} must return 200")
    else:
        ok = False
        for i in range(8):
            if nc.http_status(url) == 200 and nc.http_status(f"{nc.SITE}/images/news/{os.path.basename(pay['og_image'])}") == 200: ok = True; break
            time.sleep(15)
        if not ok: return fail("live-check", f"{url} did not return 200 after deploy; X post NOT sent", d)
        print(f"[7] live: {url} -> 200")
    # [8] X post + reply + ledger (xnews.py re-checks the ledger and timeline itself)
    print("[8] X post via xnews.py" + (" --dry-run (no network)" if dry else ""))
    rc, out = sh([XPY, nc.XNEWS, pay_p] + (["--dry-run"] if dry else [])); print(out.rstrip())
    if rc: return fail("x-post", out.strip()[-300:], d)
    print(f"== {mode} DONE: {url}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
