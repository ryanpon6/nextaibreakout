"""Blog: renders blog/posts/*.md (status: published) to /blog/<slug>/, a /blog/ index and /blog/rss.xml.
Drafts live in blog/drafts/ (not committed, never rendered). Uses build.py's head/foot so pages match the site template."""
import datetime as dt, email.utils as eu, glob, html, json, os, re
import build as B
e = B.e; SITE = B.SITE; BRAND = B.BRAND
POSTS = os.path.join(B.ROOT, "blog", "posts")
CSS = ("<style>.post .meta{font-size:14px;color:var(--mut);margin:-12px 0 28px}.post code{font-size:.92em;padding:.1em .35em;border:1px solid var(--rule);"
       "border-radius:4px;background:var(--bg2);color:var(--ink)}.post ol,.post ul{padding-left:1.4em}.post strong{color:var(--ink)}"
       ".post h2{font-size:clamp(24px,3vw,32px)}.post a{overflow-wrap:anywhere}.bloglist{list-style:none;padding:0}.bloglist li{margin:0 0 24px}"
       ".bloglist a{font-size:22px;font-weight:700}</style>")
FEED = f'<link rel="alternate" type="application/rss+xml" title="{BRAND} blog" href="/blog/rss.xml">'

def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    fm = {}
    for ln in m.group(1).splitlines():
        k, _, v = ln.partition(":"); v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] == '"': v = v[1:-1].replace('\\"', '"')
        fm[k.strip()] = v
    fm["body"] = m.group(2); fm.setdefault("slug", re.sub(r"^\d{4}-\d\d-\d\d-", "", os.path.basename(path)[:-3]))
    return fm

def inline(s):
    codes = []
    def keep(m): codes.append(f"<code>{e(m.group(1))}</code>"); return f"\x00{len(codes)-1}\x00"
    s = re.sub(r"`([^`]+)`", keep, s)
    s = e(s, quote=False)
    def link(m):
        u = html.unescape(m.group(2)); ext = re.match(r"https?://", u) and not u.startswith(SITE)
        rel = ' rel="noopener"' if ext else ""
        return f'<a href="{e(u)}"{rel}>{m.group(1)}</a>'
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], s)

def md(text):
    out, para, lst = [], [], None
    def flush():
        nonlocal lst
        if para: out.append("<p>" + inline(" ".join(para)) + "</p>"); para.clear()
        if lst: out.append(f"</{lst}>"); lst = None
    for ln in text.splitlines():
        s = ln.strip()
        h = re.match(r"(#{1,6})\s+(.*)", s); ul = re.match(r"[-*]\s+(.*)", s); ol = re.match(r"\d+\.\s+(.*)", s)
        if not s: flush()
        elif h: flush(); n = max(2, len(h.group(1))); out.append(f"<h{n}>{inline(h.group(2))}</h{n}>")
        elif ul or ol:
            tag = "ul" if ul else "ol"
            if para: flush()
            if lst != tag:
                if lst: out.append(f"</{lst}>")
                out.append(f"<{tag}>"); lst = tag
            out.append("<li>" + inline((ul or ol).group(1)) + "</li>")
        else:
            if lst: flush()
            para.append(s)
    flush(); return "\n".join(out)

def posts():
    ps = [parse(p) for p in sorted(glob.glob(os.path.join(POSTS, "*.md")))]
    return sorted([p for p in ps if p.get("status") == "published"], key=lambda p: p["date"], reverse=True)

def nice(d): return dt.date.fromisoformat(d).strftime("%b %d, %Y").replace(" 0", " ")

def page(title, desc, path, extra, main, year, og_type="website"):
    h = B.head(title, desc, path, "/", CSS + FEED + extra).replace('<meta property="og:type" content="website">', f'<meta property="og:type" content="{og_type}">', 1)
    h = h.replace('<meta name="twitter:card"', f'<meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:card"', 1)
    h += main + B.foot(year, "/") + "</body></html>"
    if B.SEO2:
        import seo2; return seo2.common(h)
    return h

def write(DIST, rel, s):
    p = os.path.join(DIST, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(s)

def apply(DIST, t):
    ps = posts(); year = t.year
    if not ps: print("[blog] no published posts"); return
    org = {"@type": "Organization", "name": BRAND, "url": SITE + "/", "logo": {"@type": "ImageObject", "url": SITE + "/og-default.png"}}
    for p in ps:
        path = f"/blog/{p['slug']}/"; url = SITE + path
        title = p.get("seo_title") or B.seo_title(p["title"]); desc = p.get("seo_description") or p["description"]
        mod = p.get("modified") or p["date"]
        j = {"@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": title, "name": p["title"], "description": desc, "datePublished": p["date"], "dateModified": mod,
             "author": org, "publisher": org, "image": SITE + "/og-default.png", "mainEntityOfPage": {"@type": "WebPage", "@id": url}, "url": url,
             **({"keywords": [k.strip() for k in p["keywords"].split(",")]} if p.get("keywords") else {})},
            {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"}, {"@type": "ListItem", "position": 3, "name": p["title"], "item": url}]}]}
        extra = B.ld(j) + f'<meta property="article:published_time" content="{p["date"]}"><meta property="article:modified_time" content="{mod}">'
        main = (f'<main class="prose post"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/blog/">Blog</a> / <span aria-current="page">Post</span></nav>'
                f'<article><h1>{e(p["title"])}</h1><p class="meta"><time datetime="{p["date"]}">{nice(p["date"])}</time> · {BRAND}</p>\n{md(p["body"])}\n</article></main>')
        write(DIST, f"blog/{p['slug']}/index.html", page(title, desc, path, extra, main, year, "article"))
    desc = f"Explainers from {BRAND} on the AI stories breaking out right now: what happened, what's real and what to watch."
    lis = "".join(f'<li><a href="/blog/{p["slug"]}/">{e(p["title"])}</a><p class="dim"><time datetime="{p["date"]}">{nice(p["date"])}</time> · {e(p["description"])}</p></li>' for p in ps)
    j = {"@context": "https://schema.org", "@graph": [{"@type": "Blog", "name": f"{BRAND} blog", "url": SITE + "/blog/", "description": desc,
         "blogPost": [{"@type": "BlogPosting", "headline": p.get("seo_title") or p["title"], "url": f"{SITE}/blog/{p['slug']}/", "datePublished": p["date"]} for p in ps]},
         {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}, {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"}]}]}
    main = f'<main class="prose"><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">Blog</span></nav><h1>Blog</h1><p class="dim">{e(desc)}</p><ul class="bloglist">{lis}</ul></main>'
    write(DIST, "blog/index.html", page(B.seo_title("AI Explainers & Analysis"), desc, "/blog/", B.ld(j), main, year))
    rfc = lambda d: eu.format_datetime(dt.datetime.fromisoformat(d + "T12:00:00+00:00"))
    items = "".join(f"<item><title>{e(p['title'])}</title><link>{SITE}/blog/{p['slug']}/</link><guid isPermaLink=\"true\">{SITE}/blog/{p['slug']}/</guid>"
                    f"<pubDate>{rfc(p['date'])}</pubDate><description>{e(p['description'])}</description></item>" for p in ps)
    write(DIST, "blog/rss.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>{BRAND} blog</title>'
          f'<link>{SITE}/blog/</link><description>{e(desc)}</description><language>en</language><atom:link href="{SITE}/blog/rss.xml" rel="self" type="application/rss+xml"/>'
          f'<lastBuildDate>{rfc(ps[0].get("modified") or ps[0]["date"])}</lastBuildDate>{items}</channel></rss>\n')
    # sitemap + llms.txt entries
    sp = os.path.join(DIST, "sitemap.xml"); s = open(sp).read()
    urls = [("/blog/", ps[0]["date"], "daily")] + [(f"/blog/{p['slug']}/", p.get("modified") or p["date"], "monthly") for p in ps]
    s = s.replace("</urlset>", "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod><changefreq>{c}</changefreq></url>" for u, d, c in urls) + "</urlset>", 1)
    open(sp, "w").write(s)
    lp = os.path.join(DIST, "llms.txt")
    open(lp, "a").write("\n## Blog\n" + f"- [Blog]({SITE}/blog/)\n" + "".join(f"- [{p['title']}]({SITE}/blog/{p['slug']}/): {p['description']}\n" for p in ps))
    # one footer link to /blog/ on every page (before About), no layout change
    n = 0
    for root, _, fs in os.walk(DIST):
        for f in fs:
            if not f.endswith(".html"): continue
            fp = os.path.join(root, f); h = open(fp, encoding="utf-8").read()
            if 'href="/blog/">Blog</a></' in h.split("<footer", 1)[-1] or "<footer" not in h: continue
            ft = h.rfind("<footer"); tail = h[ft:]
            new = re.sub(r'(<a href="/?about(?:\.html)?">About</a>)', r'<a href="/blog/">Blog</a>\1', tail, 1)
            if new != tail: open(fp, "w", encoding="utf-8").write(h[:ft] + new); n += 1
    print(f"[blog] {len(ps)} post(s), footer link on {n} pages")
