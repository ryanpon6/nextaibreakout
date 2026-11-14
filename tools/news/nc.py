"""Shared paths and helpers for the daily Grok Bot news pipeline. No secrets live here.
Every path can be overridden with an env var so tests can run on copies."""
import datetime as dt, html, json, os, re, urllib.request, urllib.error
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

def issue(stage, reasons, date=None):
    """Append a failure to autopost-issues.md (Chief of Staff relays it to Ryan)."""
    os.makedirs(os.path.dirname(ISSUES), exist_ok=True)
    new = not os.path.exists(ISSUES)
    with open(ISSUES, "a", encoding="utf-8") as f:
        if new: f.write("# NAB news auto-post issues\nNewest at the bottom. Each entry blocked a publish. Chief of Staff: relay to Ryan.\n")
        f.write(f"\n## {now():%Y-%m-%d %H:%M} MT · {stage} · slot {slot(date or today())}\nALERT: news post NOT published.\n")
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

def syndication(pid):
    """Public, no-auth copy of one X post (the embed endpoint). Returns dict or None."""
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
