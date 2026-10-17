"""Frontier Labs: fetch latest releases per lab from labs_sources.json -> data/labs.json.
Parser hooks: add a function to PARSERS keyed by source 'type'. Never synthesizes items."""
import datetime as dt, email.utils, json, os, re, sys, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from common import DATA, ROOT, UA
CFG = os.path.join(ROOT, "labs_sources.json"); OUT = os.path.join(DATA, "labs.json")
MAX = 10
# General editorial rules (apply to every lab; per-source config can add more)
MAX_AGE_DAYS = 90            # releases older than this are dropped
STORY_RE = re.compile(r"(^how (?!meta\b|openai\b|anthropic\b|google\b|xai\b|deepmind\b|we\b).+ (is |are )?(using|uses|built|builds|building|scal\w+|runs|cuts|turns|brings|puts|takes)\b|\b(scales|deploys|adopts|chooses|rolls out) (claude|chatgpt|gemini|grok|codex|openai)\b|\bcase study\b|\bcustomer (story|support)\b|\bloose on\b|\bcuts .+ (costs?|time)\b|\bwith (openai|chatgpt|codex|grok|claude|gemini)\b.*$)", re.I)
PROMO_RE = re.compile(r"(\bsubscription\b|\bpricing\b|\bnews we announced in\b|\b(weekly|monthly) (recap|roundup|round-up)\b|^the latest ai news\b|\brecap$)", re.I)
VERSION_RE = re.compile(r"^(rust-)?v?\d+(\.\d+)+\S*$", re.I)
def norm(t): return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"})
    with urllib.request.urlopen(req, timeout=25) as r: return r.read()
def pdate(s):
    if not s: return None
    s = s.strip()
    try: d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try: d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception: return None
    if d.tzinfo is None: d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(dt.timezone.utc).isoformat()
def sday(s):
    """Calendar day exactly as the source states it (its own timezone), so dates never shift a day on conversion."""
    if not s: return None
    s = s.strip()
    try: return email.utils.parsedate_to_datetime(s).date().isoformat()
    except Exception:
        try: return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
        except Exception: return None
def txt(s): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()
def rss_loose(raw):
    """Fallback for feeds that are occasionally not well-formed XML: regex out <item> blocks."""
    x = raw.decode("utf-8", "replace"); out = []
    g = lambda b, t: (re.search(r"<%s[^>]*>(.*?)</%s>" % (t, t), b, re.S) or [None, ""])[1].replace("<![CDATA[", "").replace("]]>", "")
    for b in re.findall(r"<item\b.*?</item>", x, re.S):
        out.append(dict(title=txt(g(b, "title")), url=txt(g(b, "link")), date=pdate(txt(g(b, "pubDate"))), day=sday(txt(g(b, "pubDate"))), summary=txt(g(b, "description"))[:240],
                        categories=[txt(c.replace("<![CDATA[", "").replace("]]>", "")) for c in re.findall(r"<category[^>]*>(.*?)</category>", b, re.S)]))
    return out
def rss(src):
    raw = fetch(src["url"])
    try: root = ET.fromstring(raw)
    except ET.ParseError: return rss_loose(raw)
    if root.tag.endswith("feed"): return atom(src, root)
    return [dict(title=txt(i.findtext("title")), url=(i.findtext("link") or "").strip(), date=pdate(i.findtext("pubDate")), day=sday(i.findtext("pubDate")),
                 summary=txt(i.findtext("description"))[:240], categories=[txt(c.text) for c in i.findall("category")]) for i in root.iter("item")]
def atom(src, root=None):
    ns = "{http://www.w3.org/2005/Atom}"; root = root if root is not None else ET.fromstring(fetch(src["url"]))
    out = []
    for en in root.iter(ns + "entry"):
        link = next((l.get("href") for l in en.findall(ns + "link") if l.get("rel") in (None, "alternate")), "")
        out.append(dict(title=txt(en.findtext(ns + "title")), url=link, date=pdate(en.findtext(ns + "published") or en.findtext(ns + "updated")), day=sday(en.findtext(ns + "published") or en.findtext(ns + "updated")),
                        summary=txt(en.findtext(ns + "summary"))[:240]))
    return out
DATE_RE = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}, 20\d\d"
def html(src):
    """Light listing-page scraper (one GET per run) for labs without a feed. Config: base, link_prefix.
    Keeps only cards that carry both a title and a visible date; never guesses a date."""
    import html as H
    x = fetch(src["url"]).decode("utf-8", "replace"); out, seen = [], set()
    for m in re.finditer(r'<a\b[^>]*href="(%s[^"#?]+)"[^>]*>(.*?)</a>' % re.escape(src["link_prefix"]), x, re.S):
        href, inner = m.group(1), m.group(2); d = re.search(DATE_RE, inner)
        if not d or href in seen: continue
        cands = [g[1] for g in re.findall(r'<(h[1-6])\b[^>]*>(.*?)</\1>', inner, re.S)] + re.findall(r'class="[^"]*title[^"]*"[^>]*>(.*?)</', inner, re.S)
        cands += re.findall(r">([^<>]{8,})<", inner)
        title = next((t for t in (txt(H.unescape(c)) for c in cands) if len(t) > 5 and not re.fullmatch(DATE_RE, t)), None)
        if not title: continue
        seen.add(href); dd = dt.datetime.strptime(re.sub(r"^(\w{3})\w*\.?", r"\1", d.group(0)), "%b %d, %Y").replace(hour=12, tzinfo=dt.timezone.utc)  # page shows a date only; noon UTC keeps the same calendar day in MT
        out.append(dict(title=title[:160], url=(src.get("base", "") + href) if href.startswith("/") else href, date=dd.isoformat(), day=dd.date().isoformat(), summary=""))
    return out
PARSERS = {"rss": rss, "atom": atom, "html": html}
def run():
    cfg = json.load(open(CFG)); prev = json.load(open(OUT)) if os.path.exists(OUT) else {"labs": {}}
    now = dt.datetime.now(dt.timezone.utc); res = {"generated": now.isoformat(), "labs": {}}
    for lab in cfg["labs"]:
        items, status = [], []
        kw = [k.lower() for k in lab.get("include_keywords", [])]
        for s in lab["sources"]:
            if s.get("status") == "disabled": status.append(dict(name=s["name"], url=s["url"], status="disabled", ok=False, error=s.get("note", ""))); continue
            st = dict(name=s["name"], url=s["url"], status=s.get("status", "provisional"), ok=False)
            if s.get("status") == "placeholder": st["error"] = s.get("note", "placeholder"); status.append(st); continue
            try:
                raw = PARSERS[s["type"]](s)
                if not raw: raise ValueError("feed returned 0 items")
                got = [dict(i, source=s.get("label", s["name"]), unofficial=bool(s.get("unofficial"))) for i in raw if i["title"] and i["url"].startswith("http")]
                if s.get("include_categories"): got = [i for i in got if set(i.get("categories") or []) & set(s["include_categories"])]
                if s.get("exclude_url_patterns"): got = [i for i in got if not any(re.search(p, i["url"]) for p in s["exclude_url_patterns"])]
                k2 = [k.lower() for k in s.get("include_keywords", [])] or kw
                if k2: got = [i for i in got if any(re.search(r"\b" + re.escape(k) + r"\b", (i["title"] + ("" if s.get("keywords_title_only") else " " + i["summary"])).lower()) for k in k2)]
                if s.get("exclude_keywords"): got = [i for i in got if not any(k.lower() in i["title"].lower() for k in s["exclude_keywords"])]
                if s.get("exclude_title_patterns"):  # never drop real releases: titles with a version number or "release notes" always stay
                    keep_re = re.compile(s.get("protect_title_pattern", r"\bv?\d+\.\d+(\.\d+)*\b|release notes"), re.I)
                    got = [i for i in got if keep_re.search(i["title"]) or not any(re.search(p, i["title"], re.I) for p in s["exclude_title_patterns"])]
                if s.get("require_title_keywords"): got = [i for i in got if any(re.search(r"\b" + re.escape(k) + r"\b", i["title"], re.I) for k in s["require_title_keywords"])]
                cut = (now - dt.timedelta(days=s.get("max_age_days", lab.get("max_age_days", MAX_AGE_DAYS)))).isoformat()
                got = [i for i in got if i["date"] and i["date"] >= cut]
                if not s.get("allow_stories"): got = [i for i in got if not STORY_RE.search(i["title"]) and not PROMO_RE.search(i["title"])]
                for i in got:
                    if VERSION_RE.match(i["title"]) and s.get("product"): i["title"] = f'{s["product"]} {re.sub(r"^rust-", "", i["title"])}'
                if s["type"] == "atom" and "github.com" in s["url"]: s.setdefault("max", 1)
                got = sorted(got, key=lambda i: i["date"] or "", reverse=True)[: s.get("max", MAX)]
                for i in got: i["prio"] = lab["sources"].index(s)
                items += got; st.update(ok=True, count=len(got), raw=len(raw))
            except Exception as ex:
                st["error"] = f"{type(ex).__name__}: {ex}"[:200]
                keep = [i for i in prev["labs"].get(lab["slug"], {}).get("items", []) if i["source"] == s.get("label", s["name"])]
                if keep: items += keep; st["stale_kept"] = len(keep)  # reuse this source's last real fetch
            status.append(st)
        items.sort(key=lambda i: i["date"] or "", reverse=True)
        best = {}  # cross-posted copies: same normalized title on different domains -> keep the higher-priority source (config order)
        dom = lambda u: re.sub(r"^www\.", "", urllib.parse.urlparse(u).netloc.lower())
        for i in items:
            k = norm(i["title"]); b = best.get(k)
            if b is None or (dom(b["url"]) != dom(i["url"]) and i.get("prio", 99) < b.get("prio", 99)): best[k] = i
        items = [i for i in items if best[norm(i["title"])] is i or dom(best[norm(i["title"])]["url"]) == dom(i["url"]) and i["url"] != best[norm(i["title"])]["url"]]
        if not items and any(s.get("error") and s["status"] != "placeholder" for s in status):  # transient failure: keep last real fetch
            old = prev["labs"].get(lab["slug"], {}); items = old.get("items", []); fetched = old.get("fetched")
        else: fetched = now.isoformat() if items else None
        res["labs"][lab["slug"]] = dict(items=items[:MAX], sources=status, fetched=fetched)
        print(f"[labs] {lab['slug']}: {len(items[:MAX])} items", "; ".join(f"{x['name']}={'ok' if x['ok'] else x.get('error','')[:60]}" for x in status))
    json.dump(res, open(OUT, "w"), indent=1)
if __name__ == "__main__": run()
