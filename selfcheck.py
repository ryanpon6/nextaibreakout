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
    if ndays < 7 and rel.endswith(".html"):
        for m in re.finditer(r"\b(this|last) week\b|week's", txt, re.I): F(rel, f"'week' wording with only {ndays} days of data: {txt[max(0,m.start()-40):m.end()+20]!r}")
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
        if "hourly" in raw.lower() and "top 10" in raw.lower(): F(rel, "feed still describes hourly top 10")
        for t_ in re.findall(r"<item><title>(.*?)</title>", raw):
            if re.match(r"\d+\. ", t_): F(rel, f"numbered feed title {t_!r}")
# Relaunch checks: no leftover ranking product on kept pages; sitemap and llms match the new IA.
LEFTOVERS = (
    "Last run", "Trending AI", "See today's top 10", "top 10 movers",
    "Hugging Face", "Hacker News", "breaking out right now", "what's breaking out",
    "Don't miss the next breakout", "Get the daily email", "Get the daily brief",
    "daily breakout", "ranked hourly",
)
# 'Gavin' must never appear. 'data.json' must not be linked from HTML/llms/sitemap.
KEEP_PREFIXES = ("https://nextaibreakout.com/", "https://nextaibreakout.com/about",
                 "https://nextaibreakout.com/tips/", "https://nextaibreakout.com/claude/",
                 "https://nextaibreakout.com/blog/")
kept = ("index.html", "about.html", "404.html", "llms.txt", "robots.txt", "sitemap.xml",
        "feed.xml", os.path.join("claude", "index.html"), os.path.join("tips", "index.html"),
        os.path.join("blog", "index.html"))
for rel in kept:
    fp = os.path.join(D, rel)
    if not os.path.isfile(fp):
        if rel in ("index.html", "about.html", os.path.join("claude", "index.html"), os.path.join("tips", "index.html"), "sitemap.xml", "llms.txt"):
            F(rel, "missing from build")
        continue
    raw = open(fp, encoding="utf-8").read()
    for pat in LEFTOVERS + ("Gavin",):
        if pat in raw:
            F(rel, f"leftover ranking or disallowed copy: {pat!r}")
    if rel.endswith(".html") and rel != "404.html":
        if 'name="robots" content="noindex"' in raw:
            F(rel, "kept page is noindex")
        if rel == "index.html" and 'rel="canonical" href="https://nextaibreakout.com/"' not in raw:
            F(rel, "homepage canonical missing")
        if rel == "about.html" and 'rel="canonical" href="https://nextaibreakout.com/about"' not in raw:
            F(rel, "about canonical missing")
        if rel == os.path.join("claude", "index.html") and 'rel="canonical" href="https://nextaibreakout.com/claude/"' not in raw:
            F(rel, "claude canonical missing")
    if "data.json" in raw and rel != "robots.txt":
        F(rel, "links to or mentions data.json")

sm = open(os.path.join(D, "sitemap.xml"), encoding="utf-8").read() if os.path.isfile(os.path.join(D, "sitemap.xml")) else ""
for loc in re.findall(r"<loc>([^<]+)</loc>", sm):
    if not any(loc == p or loc.startswith(p if p.endswith("/") else p + "/") or loc == p for p in (
        "https://nextaibreakout.com/",
        "https://nextaibreakout.com/about",
        "https://nextaibreakout.com/tips/",
        "https://nextaibreakout.com/claude/",
        "https://nextaibreakout.com/blog/",
    )):
        F("sitemap.xml", f"unexpected URL {loc}")
    if loc in ("https://nextaibreakout.com/about.html", "https://nextaibreakout.com/data.json", "https://nextaibreakout.com/thanks/"):
        F("sitemap.xml", f"retired or excluded URL {loc}")
# old product paths must not be built into dist
for shadow in ("item", "daily", "labs", "github", "huggingface", "npm", "pypi", "breakouts", "agents", "models", "grok-bot"):
    if os.path.exists(os.path.join(D, shadow)):
        F(shadow, "retired path still present in dist")

# blog: every published post is built, has Article JSON-LD and a sitemap entry
import blog as _blog
_sm = open(os.path.join(D, "sitemap.xml")).read() if os.path.exists(os.path.join(D, "sitemap.xml")) else ""
for _p in _blog.posts():
    _f = os.path.join(D, "blog", _p["slug"], "index.html")
    if not os.path.isfile(_f): F("blog", f"post {_p['slug']} not built"); continue
    if '"@type": "Article"' not in open(_f, encoding="utf-8").read(): F("blog", f"post {_p['slug']} has no Article JSON-LD")
    if f"<loc>{SITE}/blog/{_p['slug']}/</loc>" not in _sm: F("blog", f"post {_p['slug']} not in sitemap.xml")
if _blog.posts() and not os.path.isfile(os.path.join(D, "blog", "index.html")): F("blog", "/blog/ index not built")
print(f"selfcheck: {len(files)} files, {len(fails)} failures")
for x in fails[:60]: print("  FAIL", x)
sys.exit(1 if fails else 0)
