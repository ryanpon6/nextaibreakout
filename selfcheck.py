"""Self-check for a built site dir (default dist-seo2). Exit 1 on any failure.
Usage: python3 selfcheck.py [dist_dir]"""
import glob, html, json, os, re, sys
from urllib.parse import urlparse, unquote
HERE = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "dist-seo2")
SITE = "https://nextaibreakout.com"
fails = []
def F(rel, msg): fails.append(f"{rel}: {msg}")
def resolve(u):
    """True if an internal path exists in dist (Pages rules: /x -> x.html, /x/ -> x/index.html, plus _redirects)."""
    p = unquote(urlparse(u).path)
    if p in REDIR: return True
    c = [p.lstrip("/")]
    if p.endswith("/"): c.append(p.lstrip("/") + "index.html")
    else: c += [p.lstrip("/") + ".html", p.lstrip("/") + "/index.html"]
    return any(os.path.isfile(os.path.join(D, x)) for x in c if x != "") or p == "/" and os.path.isfile(os.path.join(D, "index.html"))
REDIR = set()
rp = os.path.join(D, "_redirects")
if os.path.exists(rp):
    for ln in open(rp):
        if ln.strip() and not ln.startswith("#"): REDIR.add(ln.split()[0])
# days of data recorded (for 'week' wording)
ndays = len(glob.glob(os.path.join(HERE, "data", "archive", "daily", "*.json")))
files = [f for f in glob.glob(os.path.join(D, "**", "*"), recursive=True) if f.endswith((".html", ".xml", ".txt"))]
def visible_desc(raw):
    m = re.search(r'<h1>.*?</h1><p class="dim">(.*?)</p>', raw, re.S); return html.unescape(m.group(1)).strip() if m else None
for f in files:
    raw = open(f, encoding="utf-8").read(); rel = os.path.relpath(f, D)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", raw))  # JSON-LD scripts are kept: their text is checked too
    for pat in ("pace right now", "/day now"):
        for m in re.finditer(re.escape(pat), txt): F(rel, f"{pat!r} …{txt[max(0,m.start()-50):m.end()+10]!r}")
    for a, b in re.findall(r"\b(\d+) of (\d+) (?:hourly )?runs?\b", txt):
        if int(a) > int(b): F(rel, f"run count {a} of {b}")
    for m in re.finditer(r'"description":\s*"(static|gradio|streamlit|docker)"|<p class="(?:what|dim)">\s*(static|gradio|streamlit|docker)\s*</p>|<description>(static|gradio|streamlit|docker)\b', raw, re.I):
        F(rel, f"bare SDK description {m.group(0)[:60]!r}")
    for m in re.finditer(r'<p class="(?:what|dim)">\s*</p>', raw): F(rel, "empty description")
    for m in re.finditer(r"-[\d.,]+[KM]? downloads|\b0 downloads/day", txt): F(rel, f"bad downloads figure {m.group(0)!r}")
    for m in re.finditer(r"\+[\d.,]+[KM]? [a-z/]+ total\b", txt): F(rel, f"plus sign on a total {m.group(0)!r}")
    if ndays < 7:
        for m in re.finditer(r"\b(this|last) week\b|\bweekly\b|week's", txt, re.I): F(rel, f"'week' wording with only {ndays} days of data: {txt[max(0,m.start()-40):m.end()+20]!r}")
    # JSON-LD parses, and item pages' description matches the visible one
    for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', raw, re.S):
        try: j = json.loads(blob)
        except Exception as ex: F(rel, f"JSON-LD does not parse: {ex}"); continue
        s = json.dumps(j)
        for u in re.findall(r'"(?:url|item|@id)": "(https://nextaibreakout\.com[^"#]*)', s):
            if not resolve(u): F(rel, f"JSON-LD link does not resolve: {u}")
        if rel.startswith("item/"):
            for g in j.get("@graph", []):
                me = g.get("mainEntity") if isinstance(g, dict) else None
                if isinstance(me, dict) and "description" in me and me["description"] != visible_desc(raw):
                    F(rel, f"JSON-LD description {me['description']!r} != visible {visible_desc(raw)!r}")
    # internal links
    links = re.findall(r'(?:href|src)="(/[^"]*|https://nextaibreakout\.com[^"]*)"', raw) if f.endswith(".html") else []
    if rel == "feed.xml": links = re.findall(r"<link>(https://nextaibreakout\.com[^<]*)</link>", raw)
    if rel in ("sitemap.xml",): links = re.findall(r"<loc>([^<]+)</loc>", raw)
    if rel == "llms.txt": links = re.findall(r"https://nextaibreakout\.com[^\s)\]>]*", raw) + re.findall(r"\]\((/[^)]*)\)", raw)
    for u in links:
        if u.startswith("//") or u.endswith((".xml",)) and resolve(u): continue
        if not resolve(u): F(rel, f"link does not resolve: {u}")
    if rel == "feed.xml":
        if raw.count("<item>") > 10: F(rel, "more than 10 items")
        for t_ in re.findall(r"<item><title>(.*?)</title>", raw):
            if re.match(r"\d+\. ", t_): F(rel, f"numbered feed title {t_!r}")
# top-10 coverage: every current top-10 item has an item page, a daily entry and a /breakouts/ entry, and the homepage/feed link on-site
sys.path.insert(0, HERE)
import archive as A
SCF = "scored-seo2.json" if os.getenv("SEO2") == "1" or os.path.basename(os.path.normpath(D)) == "dist-seo2" else "scored.json"
sc = json.load(open(os.path.join(HERE, "data", SCF)))
home = open(os.path.join(D, "index.html")).read(); feed = open(os.path.join(D, "feed.xml")).read() if os.path.exists(os.path.join(D, "feed.xml")) else ""
daily = open(os.path.join(D, "daily", sc["generated"][:10], "index.html")).read() if os.path.exists(os.path.join(D, "daily", sc["generated"][:10], "index.html")) else ""
brk = open(os.path.join(D, "breakouts", "index.html")).read() if os.path.exists(os.path.join(D, "breakouts", "index.html")) else ""
for i in sc["top"]:
    sl = A.slug(i); p = f"/item/{i['source']}/{sl.split('-', 1)[1].strip('-')}/"
    if not resolve(p): F("top10", f"no item page for {i['id']} ({p})")
    for nm, doc in (("homepage", home), ("daily", daily), ("breakouts", brk)):
        if f'href="{p}"' not in doc: F("top10", f"{i['id']} not linked on {nm}")
    if SITE + p not in feed: F("top10", f"{i['id']} not linked in feed")
    if f'"url": "{SITE}{p}"' not in home: F("top10", f"{i['id']} not in homepage ItemList with its item page")
# build stale vs scored file: homepage rows, homepage ItemList and feed must be exactly the scored top 10, in order, from the same run
exp = [f"/item/{i['source']}/{A.slug(i).split('-', 1)[1].strip('-')}/" for i in sc["top"]]
tb = re.search(r"<tbody>(.*?)</tbody>", home, re.S)
rows = re.findall(r'<a class="title" href="([^"]+)"', tb.group(1)) if tb else []
il = []
for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', home, re.S):
    for g in json.loads(blob).get("@graph", []):
        if g.get("@type") == "ItemList": il = [x["url"].replace(SITE, "") for x in g["itemListElement"]]
fl = [u.replace(SITE, "") for u in re.findall(r"<item><title>.*?</title><link>([^<]+)</link>", feed)]
for nm, got in (("homepage rows", rows), ("homepage ItemList", il), ("feed", fl)):
    if got != exp:
        bad = [f"#{k+1} {sc['top'][k]['id'] if k < len(sc['top']) else '-'} expected {exp[k] if k < len(exp) else '-'} got {got[k] if k < len(got) else '-'}" for k in range(max(len(got), len(exp))) if (got[k:k+1] or [None]) != (exp[k:k+1] or [None])]
        F("stale", f"build stale vs scored file ({SCF}): {nm} differ: " + "; ".join(bad[:4]))
import email.utils as eu, datetime as _dt
lb = re.search(r"<lastBuildDate>([^<]+)</lastBuildDate>", feed)
if feed and (not lb or lb.group(1) != eu.format_datetime(_dt.datetime.fromisoformat(sc["generated"]))): F("stale", f"build stale vs scored file ({SCF}): feed lastBuildDate {lb.group(1) if lb else None} != scored generated {sc['generated']}")
# blog: every published post is built, has Article JSON-LD and a sitemap entry
import blog as _blog
_sm = open(os.path.join(D, "sitemap.xml")).read() if os.path.exists(os.path.join(D, "sitemap.xml")) else ""
for _p in _blog.posts():
    _f = os.path.join(D, "blog", _p["slug"], "index.html")
    if not os.path.isfile(_f): F("blog", f"post {_p['slug']} not built"); continue
    if '"@type": "Article"' not in open(_f, encoding="utf-8").read(): F("blog", f"post {_p['slug']} has no Article JSON-LD")
    if f"<loc>{SITE}/blog/{_p['slug']}/</loc>" not in _sm: F("blog", f"post {_p['slug']} not in sitemap.xml")
if _blog.posts() and not os.path.isfile(os.path.join(D, "blog", "index.html")): F("blog", "/blog/ index not built")
print(f"selfcheck ({SCF}): {len(files)} files, {len(fails)} failures")
for x in fails[:60]: print("  FAIL", x)
sys.exit(1 if fails else 0)
