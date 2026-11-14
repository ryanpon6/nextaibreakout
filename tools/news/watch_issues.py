#!/usr/bin/env python3
"""No-AI watcher for autopost-issues.md. Prints every line added since the last check and exits 1 when there is
something new; exits 0 (silent) when nothing changed. State (byte offset + file identity) is kept in a small JSON
file, so each new alert is reported once. A truncated or replaced file is re-read from the top.
Usage  watch_issues.py [--file PATH] [--state PATH]
       defaults: /workspace/shared/nab-relaunch/autopost-issues.md, /workspace/shared/nab-relaunch/news/.issues-watch.json
Exit   0 nothing new · 1 new lines printed · 2 watcher error"""
import argparse, json, os, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=os.getenv("NAB_AUTOPOST_ISSUES", "/workspace/shared/nab-relaunch/autopost-issues.md"))
    ap.add_argument("--state", default="/workspace/shared/nab-relaunch/news/.issues-watch.json")
    a = ap.parse_args()
    try: st = json.load(open(a.state))
    except Exception: st = {}
    if not os.path.exists(a.file): return 0
    s = os.stat(a.file); ident = [s.st_ino, s.st_dev]; off = st.get("offset", 0)
    if st.get("ident") != ident or s.st_size < off: off = 0
    if s.st_size == off: return 0
    with open(a.file, "rb") as f: f.seek(off); new = f.read()
    sys.stdout.write(new.decode("utf-8", "replace"))
    try:
        os.makedirs(os.path.dirname(a.state), exist_ok=True); tmp = a.state + ".tmp"
        json.dump({"offset": off + len(new), "ident": ident}, open(tmp, "w")); os.replace(tmp, a.state)
    except Exception as e:
        print(f"watcher: could not save state ({e.__class__.__name__})", file=sys.stderr); return 2
    return 1

if __name__ == "__main__":
    sys.exit(main())
