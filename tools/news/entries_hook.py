"""Integration point with the tips-index branch (single source-of-truth entries list for the homepage
"latest 3" strips, /tips/ and the Claude tips index). make_post.py calls register() once per news post.

Rewire here only: set ENTRIES_FILE (or $NAB_ENTRIES) to the list tips-index lands, and adjust to_entry()
if its field names differ. Until that file exists, register() is a no-op (prints why); the post still shows on
/blog/, the homepage "Latest posts", sitemap, feed and llms.txt through blog.py.
Entry shape (from the tips-index brief): {date, title, url, kind: grok|claude, type: news|tip}. Idempotent by url."""
import json, os
import nc

ENTRIES_FILE = os.getenv("NAB_ENTRIES", os.path.join(nc.ROOT, "entries.json"))   # confirm the real path when tips-index lands

def to_entry(date, title, url, topic):
    return {"date": date, "title": title, "url": url, "kind": "claude" if topic == "claude" else "grok", "type": "news"}

def register(date, title, url, topic, dry=False):
    e = to_entry(date, title, url, topic)
    if not os.path.exists(ENTRIES_FILE):
        print(f"ENTRIES skipped: {ENTRIES_FILE} not present yet (tips-index not merged); would append {json.dumps(e)}"); return None
    data = json.load(open(ENTRIES_FILE, encoding="utf-8"))
    lst = data["entries"] if isinstance(data, dict) else data
    if any(x.get("url") == url for x in lst): print(f"ENTRIES already has {url}"); return ENTRIES_FILE
    if dry: print(f"ENTRIES dry-run: would append {json.dumps(e)} to {ENTRIES_FILE}"); return None
    lst.append(e); lst.sort(key=lambda x: x.get("date", ""), reverse=True)
    with open(ENTRIES_FILE, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False); f.write("\n")
    print(f"ENTRIES appended {url} to {ENTRIES_FILE}"); return ENTRIES_FILE
