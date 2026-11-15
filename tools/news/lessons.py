#!/usr/bin/env python3
"""Lessons-we-learned queue for the daily news pipeline.

Queue   $NAB_NEWS_STATE/lessons/LESSON-SLUG.json
Posted  $NAB_NEWS_STATE/lessons/posted/   (moved here after a successful post)

Each item uses the same keys as spec-DATE.json, plus:
  source:    "lesson"
  qc:        {"verdict": "PASS", "by": "Quality Checker", "at": ISO time, "sha256": content_hash(item)}
             sha256 binds the PASS to the exact content (rule 23): any edit after the PASS, to any key
             except "qc" and "priority", changes the hash and the item is skipped / fails G7 until QC
             re-passes it. Print the hash with: python3 tools/news/lessons.py hash FILE
  evidence:  [paths to our own files the before/after examples are quoted from]
  priority:  optional bool — a priority item is posted ahead of an X story
             (the X story is not logged as covered, so the next run can pick it if it is still inside the 24h window; still one nab-news-DATE slot)
  kind:      optional "claude" or "grok" (default grok)

fetch.py picks at most one item a day. Exit 10 only when the X scan is quiet
and this queue has no qc-PASS item. The written spec-DATE.json is already
Quality Checker passed: the routine must not rewrite it.
"""
import glob, hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nc

HASH_SKIP = ("qc", "priority")   # scheduling + the PASS block itself; everything else is bound by the hash

def content_hash(obj):
    """sha256 of the item's content, canonical JSON, without the qc block and priority flag."""
    body = {k: v for k, v in (obj or {}).items() if k not in HASH_SKIP}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()

def hash_problem(obj, qc=None):
    """'' if the qc block's sha256 matches the content, else the reason (fail closed)."""
    qc = qc if isinstance(qc, dict) else (obj.get("qc") if isinstance(obj.get("qc"), dict) else {})
    want = str(qc.get("sha256") or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{64}", want): return "qc block has no sha256 content hash (rule 23)"
    if want != content_hash(obj): return "content changed after the qc PASS (sha256 mismatch, rule 23: needs a fresh QC pass)"
    return ""

def already_posted(obj):
    """Reason string if this lesson's slug already has a site post or a ledger row (double-post guard)."""
    slug = clean_slug(obj)
    hits = glob.glob(os.path.join(nc.POSTS, f"*-{slug}.md"))
    if hits: return f"slug '{slug}' already has a site post ({os.path.basename(hits[0])})"
    url = f"{nc.SITE}/blog/{slug}/"
    try:
        for r in nc.ledger_rows():
            if str(r.get("story_url") or r.get("url") or "").rstrip("/") == url.rstrip("/"): return f"slug '{slug}' already in the ledger ({r.get('slot')})"
    except Exception as e:
        return f"ledger unreadable ({e.__class__.__name__}); fail closed"
    return ""

def clean_slug(obj, path=""):
    return re.sub(r"[^a-z0-9-]", "", str(obj.get("slug") or os.path.splitext(os.path.basename(path))[0]).lower()).strip("-")[:70] or "lesson"

REQ = ("slug", "title", "description", "body_md", "related_tips", "x_main",
       "card_headline", "card_points", "image_alt", "note")

def queue_dir():
    return os.path.join(nc.STATE, "lessons")

def posted_dir():
    return os.path.join(nc.STATE, "lessons", "posted")

def evidence_paths(obj):
    out = []
    for e in obj.get("evidence") or []:
        p = e if isinstance(e, str) else (e or {}).get("file") or (e or {}).get("path")
        if p: out.append(p)
    return out

def is_claude(obj):
    if str(obj.get("kind") or "").strip().lower() == "claude": return True
    if str(obj.get("topic") or "").strip().lower() == "claude": return True
    return bool(re.search(r"\bclaude\b", str(obj.get("slug") or "") + " " + str(obj.get("title") or ""), re.I))

def qc_pass(obj):
    qc = obj.get("qc") if isinstance(obj.get("qc"), dict) else {}
    return str(qc.get("verdict") or "").strip().upper() == "PASS"

def sort_key(item):
    path, obj = item
    qc = obj.get("qc") if isinstance(obj.get("qc"), dict) else {}
    raw = str(qc.get("at") or "").strip()
    import datetime as dt
    try:
        at = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if at.tzinfo is None: at = at.replace(tzinfo=dt.timezone.utc)
        stamp = at.timestamp()
    except Exception:
        stamp = os.path.getmtime(path) if os.path.exists(path) else 0
    return (stamp, path)

def oldest(items):
    return min(items, key=sort_key)

def valid(obj, path=""):
    """Return a reason string if the item cannot be posted, or '' if it can."""
    if not isinstance(obj, dict): return "not a JSON object"
    if str(obj.get("source") or "").strip().lower() != "lesson": return "source is not 'lesson'"
    if not qc_pass(obj): return "no qc PASS block"
    qc = obj.get("qc") or {}
    if not str(qc.get("by") or "").strip(): return "qc block is missing 'by'"
    if not str(qc.get("at") or "").strip(): return "qc block is missing 'at'"
    miss = [k for k in REQ if not obj.get(k)]
    if miss: return "missing spec fields: " + ", ".join(miss)
    if not evidence_paths(obj): return "no evidence files"
    why = hash_problem(obj)
    if why: return why
    why = already_posted(obj)
    if why: return why
    return ""

def load_queue(log=None):
    """Return [(path, obj), ...] for qc-PASS items sitting in lessons/ (not posted/)."""
    d = queue_dir(); items = []
    if not os.path.isdir(d): return items
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"): continue
        path = os.path.join(d, name)
        if not os.path.isfile(path): continue
        try: obj = nc.load(path)
        except Exception as e:
            if log is not None: log.append(f"skip lesson {name}: unreadable ({e.__class__.__name__})")
            continue
        why = valid(obj, path)
        if why:
            if log is not None: log.append(f"skip lesson {name}: {why}")
            continue
        items.append((path, obj))
    return items

def choose(picked_x, queue):
    """Pick today's source. A priority lesson beats an X story (X waits until tomorrow).
    Returns ("lesson", (path, obj)) | ("x", None) | ("quiet", None)."""
    pri = [(p, o) for p, o in queue if o.get("priority") is True or str(o.get("priority")).lower() == "true"]
    if pri: return "lesson", oldest(pri)
    if picked_x: return "x", None
    if queue: return "lesson", oldest(queue)
    return "quiet", None

def emit(date, path, obj):
    """Write story-DATE.json and spec-DATE.json from a queue item. Returns those paths."""
    spec = dict(obj)
    kind = "claude" if is_claude(obj) else "grok"
    slug = clean_slug(obj, path)
    story = {
        "key": slug, "topic": "lesson", "kind": kind, "source": "lesson",
        "headline": str(obj.get("title") or obj.get("card_headline") or "")[:200],
        "posts": [], "evidence": evidence_paths(obj), "qc": obj.get("qc") or {},
        "priority": bool(obj.get("priority") is True or str(obj.get("priority")).lower() == "true"),
        "lesson_file": path, "date": date, "picked_at": nc.now().isoformat(),
    }
    sp, stp = nc.path("spec", date), nc.path("story", date)
    nc.save(stp, story); nc.save(sp, spec)
    return stp, sp

def archive(story, dry=False):
    """Move the queue item to lessons/posted/ after a successful post. Dry runs only print."""
    if not story or not (story.get("source") == "lesson" or story.get("topic") == "lesson"):
        return None
    src = story.get("lesson_file")
    if not src:
        return None
    dest_dir = posted_dir()
    dest = os.path.join(dest_dir, os.path.basename(src))
    if dry:
        print(f"[8b] lesson archive (printed only): mv {src} {dest}")
        return dest
    if not os.path.isfile(src):
        print(f"[8b] lesson already archived or missing: {src}")
        return None
    os.makedirs(dest_dir, exist_ok=True)
    if os.path.exists(dest):
        base, ext = os.path.splitext(os.path.basename(src))
        dest = os.path.join(dest_dir, f"{base}-{story.get('date') or nc.today()}{ext}")
    os.rename(src, dest)
    print(f"[8b] lesson archived: {dest}")
    return dest

if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "hash":
    print(content_hash(nc.load(sys.argv[2])))
