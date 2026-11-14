#!/usr/bin/env python3
"""No-AI watcher for autopost-issues.md. Prints every line added since the last check and exits 1 when there is
something new; prints NOTHING and exits 0 when nothing changed (including when the file does not exist yet).
State (byte offset + file identity) lives in .issues-watch.json beside this script, so each alert is reported once.
A truncated or replaced file is re-read from the top.
Usage  watch_issues.py [--seed] [--file PATH] [--state PATH]
       --seed  mark the file's current content (or its absence) as already seen, print nothing, exit 0
       defaults: /workspace/shared/nab-relaunch/autopost-issues.md, <this script's folder>/.issues-watch.json
Exit   0 nothing new · 1 new lines printed · 2 watcher error"""
import argparse, json, os, sys

def save(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True); tmp = path + ".tmp"
    with open(tmp, "w") as f: json.dump(obj, f)
    os.replace(tmp, path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=os.getenv("NAB_AUTOPOST_ISSUES", "/workspace/shared/nab-relaunch/autopost-issues.md"))
    ap.add_argument("--state", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".issues-watch.json"))
    ap.add_argument("--seed", action="store_true")
    a = ap.parse_args()
    try:
        exists = os.path.exists(a.file)
        s = os.stat(a.file) if exists else None
        ident = [s.st_ino, s.st_dev] if s else None
        if a.seed: save(a.state, {"offset": s.st_size if s else 0, "ident": ident}); return 0
        if not exists: return 0
        try: st = json.load(open(a.state))
        except Exception: st = {}
        off = st.get("offset", 0)
        if st.get("ident") != ident or s.st_size < off: off = 0
        if s.st_size == off: return 0
        with open(a.file, "rb") as f: f.seek(off); new = f.read()
        sys.stdout.write(new.decode("utf-8", "replace"))
        save(a.state, {"offset": off + len(new), "ident": ident})
        return 1
    except Exception as e:
        print(f"watcher error: {e.__class__.__name__}: {e}", file=sys.stderr); return 2

if __name__ == "__main__":
    sys.exit(main())
