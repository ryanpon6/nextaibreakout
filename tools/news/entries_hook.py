"""Integration point with tips-index: catalog.json at the repo root ({"entries": [...]}) is the single source of
truth for the homepage "latest 3" strips, the dated /tips/ list and the Claude tips index.
make_post.py calls register() once per news post.

Entry: id (the URL slug), date, title, url (site path), kind grok|claude, type news, source (the cited X posts).
seq is left to catalog.append(). A missing id fails the tips-index build, so id is always set.
When catalog.py is in the repo, its append() is used (it validates and writes atomically). Otherwise the same
add-or-replace-by-id is done here. While catalog.json is absent (this branch, until tips-index merges),
register() is a no-op and says so. Rewire only here: ENTRIES_FILE / $NAB_ENTRIES and to_entry()."""
import json, os, sys
import nc

ENTRIES_FILE = os.getenv("NAB_ENTRIES", os.path.join(nc.ROOT, "catalog.json"))

def to_entry(date, title, slug, topic, sources=()):
    e = {"id": slug, "date": date, "title": title, "url": f"/blog/{slug}/", "kind": "claude" if topic == "claude" else "grok", "type": "news"}
    if sources: e["source"] = "News post from the daily pipeline. Cited X posts: " + ", ".join(sources)
    return e

def register(date, title, slug, topic, sources=()):
    e = to_entry(date, title, slug, topic, sources)
    if not os.path.exists(ENTRIES_FILE):
        print(f"ENTRIES skipped: {ENTRIES_FILE} not present (tips-index not merged); would add {json.dumps(e)}"); return None
    if os.path.exists(os.path.join(nc.ROOT, "catalog.py")) and os.path.abspath(ENTRIES_FILE) == os.path.join(nc.ROOT, "catalog.json"):
        if nc.ROOT not in sys.path: sys.path.insert(0, nc.ROOT)
        import catalog
        catalog.append(e, ENTRIES_FILE); print(f"ENTRIES catalog.append({e['id']}) -> {ENTRIES_FILE}"); return ENTRIES_FILE
    data = json.load(open(ENTRIES_FILE, encoding="utf-8")); rows = data["entries"]
    ids = [r.get("id") for r in rows]
    if e["id"] in ids: rows[ids.index(e["id"])] = {**rows[ids.index(e["id"])], **e}
    else: rows.append(e)
    tmp = ENTRIES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False); f.write("\n")
    os.replace(tmp, ENTRIES_FILE); print(f"ENTRIES added {e['id']} to {ENTRIES_FILE}"); return ENTRIES_FILE
