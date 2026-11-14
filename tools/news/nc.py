"""Shared paths and helpers for the daily Grok Bot news pipeline. No secrets live here.
Every path can be overridden with an env var so tests can run on copies."""
import datetime as dt, html, json, os, re, unicodedata, urllib.request, urllib.error
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
SHARED = os.getenv("NAB_SHARED", "/workspace/shared/nab-relaunch")
STATE = os.getenv("NAB_NEWS_STATE", os.path.join(SHARED, "news"))          # candidates, story, spec, run logs
TREND_LOG = os.getenv("NAB_TREND_LOG", os.path.join(SHARED, "trend-log.md"))
ISSUES = os.getenv("NAB_AUTOPOST_ISSUES", os.path.join(SHARED, "autopost-issues.md"))
LIVE_FLAG = os.getenv("NAB_AUTOPOST_FLAG", os.path.join(SHARED, "autopost-live.flag"))
LEDGER = os.getenv("NAB_LEDGER", "/workspace/nextaibreakout/posted.jsonl")
XNEWS = os.getenv("NAB_XNEWS", "/workspace/nextaibreakout/proposals/nab-news/xnews.py")
POSTS = os.path.join(ROOT, "blog", "posts")
NEWS_IMG = os.path.join(ROOT, "static", "images", "news")
SITE = "https://nextaibreakout.com"
MT = ZoneInfo("America/Edmonton")
AT = ZoneInfo("America/Halifax")
TIP_SLOTS_AT = (9, 13, 18)       # Days 2-14 tip series, Atlantic time
SLOT_GAP_MIN = 60                # no news post within this many minutes of a tip slot
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
QUIET = 10                       # exit code: nothing new, the AI should not run
HELD = 20                        # exit code: G12 per-post hold, draft written to news/held-DATE.md, waits for --release
CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def config():
    """tools/news/config.json. Missing file or key = safe default (hold ON). NAB_NEWS_CONFIG is honoured only
    in dry runs and selftests (NAB_DRYRUN=1), so a live run always reads the committed file."""
    p = os.getenv("NAB_NEWS_CONFIG") if os.getenv("NAB_DRYRUN") == "1" and os.getenv("NAB_NEWS_CONFIG") else CONFIG
    try: c = json.load(open(p, encoding="utf-8"))
    except Exception: c = {}
    return {"hold_money_policy": c.get("hold_money_policy", True) is not False, "_path": p}

def xweight(t):
    """twitter-text v3 weighting: these code point ranges count 1, everything else (CJK, emoji, '…', '•') counts 2."""
    n = 0
    for ch in unicodedata.normalize("NFC", t):
        o = ord(ch)
        n += 1 if (o <= 4351 or 8192 <= o <= 8205 or 8208 <= o <= 8223 or 8242 <= o <= 8247) else 2
    return n

def now():
    return dt.datetime.now(MT)

def today():
    return now().date().isoformat()

def slot(date):
    return f"nab-news-{date}"

def path(kind, date):
    return os.path.join(STATE, f"{kind}-{date}.json")

def load(p):
    with open(p, encoding="utf-8") as f: return json.load(f)

def save(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: json.dump(obj, f, indent=2, ensure_ascii=False); f.write("\n")

def issue(stage, reasons, date=None, head=None):
    """Append a failure to autopost-issues.md (Chief of Staff relays it to Ryan)."""
    os.makedirs(os.path.dirname(ISSUES), exist_ok=True)
    new = not os.path.exists(ISSUES)
    with open(ISSUES, "a", encoding="utf-8") as f:
        if new: f.write("# NAB news auto-post issues\nNewest at the bottom. Each entry blocked a publish. Chief of Staff: relay to Ryan.\n")
        f.write(f"\n## {now():%Y-%m-%d %H:%M} MT · {stage} · slot {slot(date or today())}\n{now():%Y-%m-%d %H:%M} MT {head or 'ALERT: news post NOT published (' + stage + ').'}\n")
        for r in reasons: f.write(f"- {r}\n")

def http_status(url, timeout=20, method="GET"):
    """Final status code after redirects, or 0 on network error. HTTPS only (http:// returns -1)."""
    if not url.startswith("https://"): return -1
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r: return r.status
    except urllib.error.HTTPError as e: return e.code
    except Exception: return 0

STATUS_RE = re.compile(r"https://(?:x|twitter)\.com/([A-Za-z0-9_]{1,15})/status/(\d{5,25})")

SYND_CALLS = 0   # embed-endpoint fetches made by this process (flushed into the run metrics)

def syndication(pid):
    """Public, no-auth copy of one X post (the embed endpoint). Returns dict or None. Counted in SYND_CALLS."""
    global SYND_CALLS
    SYND_CALLS += 1
    try:
        tok = _token(int(pid))
        req = urllib.request.Request(f"https://cdn.syndication.twimg.com/tweet-result?id={pid}&lang=en&token={tok}", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read().decode("utf-8"))
    except Exception:
        return None
    if d.get("__typename") != "Tweet": return None
    text = d.get("text", "")
    note = (((d.get("note_tweet") or {}).get("note_tweet_results") or {}).get("result") or {}).get("text")
    if note: text = note
    text = html.unescape(text)
    return {"id": d.get("id_str", str(pid)), "user": (d.get("user") or {}).get("screen_name"),
            "name": (d.get("user") or {}).get("name"), "created_at": d.get("created_at"), "text": text,
            "likes": d.get("favorite_count", 0), "replies": d.get("conversation_count", 0)}

def _token(n):
    # Same token the official embed script computes: ((id / 1e15) * pi) in base 36, zeros and dots removed.
    import math
    x = (n / 1e15) * math.pi
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"; ip = int(x); fp = x - ip; s = ""
    while ip: s = digits[ip % 36] + s; ip //= 36
    s = (s or "0") + "."
    for _ in range(8): fp *= 36; d = int(fp); s += digits[d]; fp -= d
    return s.replace("0", "").replace(".", "") or "a"

def norm(s):
    """Normalise for verbatim quote matching: curly quotes, dashes, whitespace, and t.co links."""
    s = unicodedata.normalize("NFKC", html.unescape(s))
    s = re.sub(r"https://t\.co/\S+", "", s)
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2014", "-").replace("\u2013", "-")
    return re.sub(r"\s+", " ", s).strip()

def tip_window(t):
    """Return (blocked, nearest_slot_MT) for the tip-slot buffer. Slots are 9 AM, 1 PM, 6 PM Atlantic."""
    t = t.astimezone(MT); best = None
    for dd in (-1, 0, 1):
        day = (t.astimezone(AT).date() + dt.timedelta(days=dd))
        for h in TIP_SLOTS_AT:
            s = dt.datetime(day.year, day.month, day.day, h, tzinfo=AT).astimezone(MT)
            gap = abs((t - s).total_seconds()) / 60
            if best is None or gap < best[0]: best = (gap, s)
    return best[0] < SLOT_GAP_MIN, best[1]

def ledger_rows():
    if not os.path.exists(LEDGER): return []
    rows = []
    for ln in open(LEDGER, encoding="utf-8"):
        try: rows.append(json.loads(ln))
        except Exception: pass
    return rows

def in_ledger(date):
    return next((r for r in ledger_rows() if r.get("slot") == slot(date)), None)

# ---- cost log (autopost-cost.jsonl) and per-run work metrics ----
import fcntl, time
from contextlib import contextmanager
COST = os.getenv("NAB_AUTOPOST_COST", os.path.join(SHARED, "autopost-cost.jsonl"))
XAPI_KEYS = ("users_me", "timeline_read", "media_upload", "media_metadata", "post", "reply")

def drydir(): return os.path.join(STATE, "dryrun")
def is_dry(): return os.getenv("NAB_DRYRUN") == "1"
def cost_path(dry=None): return os.path.join(drydir(), "autopost-cost.jsonl") if (is_dry() if dry is None else dry) else COST
def metrics_path(date, dry=None): return os.path.join(drydir() if (is_dry() if dry is None else dry) else STATE, f"metrics-{date}.json")

@contextmanager
def locked(path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try: yield
        finally: fcntl.flock(lk, fcntl.LOCK_UN)

def jsonl_append(path, row):
    """Append one row under an exclusive lock, written atomically (temp file + os.replace)."""
    with locked(path):
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        if old and not old.endswith("\n"): old += "\n"
        tmp = f"{path}.tmp{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f: f.write(old + json.dumps(row, ensure_ascii=False) + "\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)

def jsonl_rows(path):
    if not os.path.exists(path): return []
    out = []
    for ln in open(path, encoding="utf-8"):
        try: out.append(json.loads(ln))
        except Exception: pass
    return out

def metrics(date, dry=None):
    try: return load(metrics_path(date, dry))
    except Exception: return {}

def metrics_update(date, dry=None, reset=False, **kv):
    """kv values that are ints are added; others replace. reset=True starts a fresh run record."""
    p = metrics_path(date, dry)
    with locked(p):
        m = {} if reset else (load(p) if os.path.exists(p) else {})
        for k, v in kv.items():
            m[k] = (m.get(k) or 0) + v if isinstance(v, int) and not isinstance(v, bool) and k != "x_reads_agent" else v
        tmp = f"{p}.tmp{os.getpid()}"; save(tmp, m); os.replace(tmp, p)
    return m

def cost_row(date, outcome, *, x_post_id=None, reply_id=None, post_url=None, x_calls=None, ai_writing_step=False,
             gate_fix_retries=0, wall_seconds=None, note=None, dry=None):
    dry = is_dry() if dry is None else dry
    m = metrics(date, dry); calls = {k: int((x_calls or {}).get(k, 0)) for k in XAPI_KEYS}; calls["total"] = sum(calls.values())
    row = {"date": date, "run_at": now().isoformat(timespec="seconds"), "outcome": "dry-run" if dry else outcome, "posted": outcome == "posted" and not dry,
           "x_post_id": x_post_id, "reply_id": reply_id, "post_url": post_url,
           "x_reads_agent": m.get("x_reads_agent"), "syndication_fetches": int(m.get("syndication_fetches") or 0),
           "x_api_calls": calls, "ai_writing_step": bool(ai_writing_step), "gate_fix_retries": int(gate_fix_retries),
           "wall_seconds": wall_seconds if wall_seconds is not None else (round(time.time() - m["start_ts"], 1) if m.get("start_ts") else None)}
    if dry: row["dry_outcome"] = outcome   # what a live run would have logged; dry rows never count as posted
    if note: row["note"] = note
    jsonl_append(cost_path(dry), row)
    metrics_update(date, dry, reset=True, x_reads_agent=None, syndication_fetches=0, start_ts=time.time())  # next run in the day starts clean
    return row
