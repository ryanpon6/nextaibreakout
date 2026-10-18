"""SEO2 layer (enabled only with SEO2=1): keyword titles, JSON-LD, /about fixes, robots/llms, self-hosted fonts,
contrast/heading fixes, daily archive pages and permanent per-item pages. Uses only real recorded data."""
import datetime as dt, glob, json, os, re, shutil
from urllib.parse import quote
import build as B
from common import DATA, ROOT, SNAP, canon, aliases
e = B.e; SITE = B.SITE; BRAND = B.BRAND
ARC = os.path.join(DATA, "archive")
TITLE = "Trending AI Repos & Models Today | NextAiBreakout"
H1 = B.H1_HTML
FONT_LINKS = ('<link rel="preload" href="/fonts/Archivo-var.woff2" as="font" type="font/woff2" crossorigin>'
              f'<link rel="stylesheet" href="/fonts/fonts.css?v={B.VER}">')
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
           "Perplexity-User", "Google-Extended", "CCBot", "Applebot-Extended", "Bingbot", "Googlebot"]
def ipath(slug_or_I, source=None):
    """Permanent item URL: /item/<source>/<slug>/ (slug without the source prefix)."""
    sl = slug_or_I["slug"] if isinstance(slug_or_I, dict) else slug_or_I
    src = slug_or_I["source"] if isinstance(slug_or_I, dict) else source
    return f"/item/{src}/{sl.split('-', 1)[1].strip('-')}/"
CATS = [("github", "GitHub", "Trending AI GitHub repos", "source"), ("huggingface", "Hugging Face", "Trending Hugging Face models and Spaces", "source"),
        ("npm", "npm", "Accelerating AI npm packages", "source"), ("pypi", "PyPI", "Accelerating AI Python packages on PyPI", "source"),
        ("agents", "Agents", "Trending AI agent projects", "tag"), ("models", "Models", "Trending AI models", "tag")]
def vcrumbs(*pairs):
    return '<nav class="crumbs" aria-label="Breadcrumb">' + " / ".join(f'<a href="{u}">{e(n)}</a>' if k < len(pairs) - 1 else f'<span aria-current="page">{e(n)}</span>' for k, (n, u) in enumerate(pairs)) + "</nav>"
FOOT_LINKS = ('<nav class="footlinks" aria-label="Site"><a href="/">Today</a><a href="/breakouts/">Breakouts</a><a href="/daily/">Daily archive</a>'
              '<a href="/github/">GitHub</a><a href="/huggingface/">Hugging Face</a><a href="/npm/">npm</a><a href="/pypi/">PyPI</a><a href="/agents/">Agents</a><a href="/models/">Models</a>'
              '<a href="/labs/">Frontier Labs</a><a href="/about">About</a><a href="/feed.xml">RSS</a></nav>')
BLABEL = "Breakouts"
CAT_TITLE = {"github": "Trending AI GitHub Repos Today", "huggingface": "Trending Hugging Face Models Today", "npm": "Trending AI npm Packages Today",
             "pypi": "Trending AI Python Packages Today", "agents": "Trending AI Agent Projects Today", "models": "New & Trending AI Models Today"}
def gain(series, t0=None, t1=None):
    """Real gain between the first and last stored snapshot in [t0, t1]: (delta, hours) or None."""
    pts = [(t, m) for t, m in series if (t0 is None or t >= t0) and (t1 is None or t <= t1)]
    if len(pts) < 2: return None
    h = (dt.datetime.fromisoformat(pts[-1][0]) - dt.datetime.fromisoformat(pts[0][0])).total_seconds() / 3600
    return (pts[-1][1] - pts[0][1], h) if h >= 0.5 else None
def gain_txt(series, unit, t0=None, t1=None):
    g = gain(series, t0, t1)
    if not g: return "Not enough snapshots yet to measure a gain."
    return f"{'+' if g[0] >= 0 else ''}{B_fmt(g[0])} {unit} in {g[1]:.0f}h (measured between stored snapshots)"
def B_fmt(n):
    n = float(n); return f"{n/1e6:.1f}M" if abs(n) >= 1e6 else f"{n/1e3:.1f}K" if abs(n) >= 1e3 else f"{n:.0f}"
def plural(n, w): return f"{n} {w}" + ("" if n == 1 else "s")
SDKS = {"static", "gradio", "streamlit", "docker", "panel", ""}
SER = {}  # id -> [(iso, metric)] real snapshot series, filled once per build
LATEST = {}
POOL = {}
def desc_of(x):
    """Real description; for Spaces use the card summary/title, never a bare SDK name."""
    ex = x.get("extra") or {}
    if x["source"] == "huggingface" and (x.get("kind") == "tool" or ex.get("hf_type") == "space"):
        cx = (POOL.get(x["id"]) or {}).get("extra") or {}
        return ex.get("summary") or ex.get("title") or cx.get("summary") or cx.get("title") or "Hugging Face Space (no description on its card)"
    w = (x.get("what") or x.get("desc") or "").strip()
    if w.lower() in SDKS: w = ""
    if not w:
        cx = POOL.get(x["id"]) or {}; w = (cx.get("what") or "").strip()
        if not w and x["source"] == "huggingface" and cx.get("desc") and cx["desc"].lower() not in SDKS: w = f"{cx['desc']} model on Hugging Face"
    if not w and x["source"] == "hackernews":
        from urllib.parse import urlparse
        dom = urlparse(x.get("url") or "").netloc.removeprefix("www.")
        c = ((POOL.get(x["id"]) or x).get("extra") or {}).get("comments")
        w = "Hacker News story" + (f" from {dom}" if dom and dom != "news.ycombinator.com" else "") + (f", {c} comments" if c else "")
    return w
def measure(x):
    """The one shared momentum figure used on every page and in the feed."""
    m = x.get("metric") or 0; unit = x.get("metric_name") or ""; ex = x.get("extra") or {}
    if x["source"] in ("npm", "pypi"):
        wk = ex.get("week")
        return f"{B_fmt(m)} downloads/day" + (f", {m / (wk / 7):.2f}× 7-day avg" if wk else "")
    S = SER.get(x["id"], [])
    if S:
        end = dt.datetime.fromisoformat(S[-1][0]); w = [p for p in S if dt.datetime.fromisoformat(p[0]) >= end - dt.timedelta(hours=24)]
        g = gain(w)
        if g: return f"{'+' if g[0] >= 0 else ''}{B_fmt(g[0])} {unit} in {g[1]:.0f}h"
    if x["source"] == "github" and x.get("created"):
        days = max((dt.datetime.fromisoformat(LATEST["t"]) - dt.datetime.fromisoformat(x["created"].replace("Z", "+00:00"))).days, 1)
        return f"{B_fmt(m)} stars since launch, {plural(days, 'day')} ago"
    if x["source"] == "hackernews" and x.get("created"):
        hrs = (dt.datetime.fromisoformat(LATEST["t"]) - dt.datetime.fromisoformat(x["created"].replace("Z", "+00:00"))).total_seconds() / 3600
        return f"{B_fmt(m)} points since posted {hrs:.0f}h ago"
    return f"{B_fmt(m)} {unit} total"
def total_of(x):
    if x["source"] in ("npm", "pypi"): return "source: " + ("npm" if x["source"] == "npm" else "PyPI") + " downloads API"
    return f"{B_fmt(x.get('metric') or 0)} {x.get('metric_name') or ''} total"
def badge(x):
    return "HF Space" if x["source"] == "huggingface" and (x.get("kind") == "tool" or (x.get("extra") or {}).get("hf_type") == "space") else B.LABEL[x["source"]]
SPONSOR_CONTACT = os.getenv("SPONSOR_CONTACT", "").strip()  # e.g. sponsors@nextaibreakout.com once its forwarding is verified
def sponsor_strip():
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", SPONSOR_CONTACT or ""):
        return (f'<section id="sponsor" class="spon slim"><span class="tag-s">Sponsor</span><p>Your product here, pinned for 7 days. Sponsor this spot: email for rates.</p>'
                f'<a class="btn" href="mailto:{e(SPONSOR_CONTACT)}?subject=NextAiBreakout%20sponsorship">{e(SPONSOR_CONTACT)}</a></section>')
    return '<section id="sponsor" class="spon slim"><span class="tag-s">Sponsor</span><p>Your product here, pinned for 7 days. Sponsorships: contact coming soon.</p></section>'
def sponsor_about():
    if SPONSOR_CONTACT: return f'One pinned slot per week on the site. Sponsor this spot: email <a href="mailto:{e(SPONSOR_CONTACT)}">{e(SPONSOR_CONTACT)}</a> for rates.'
    return "One pinned slot per week on the site. Sponsorships: contact coming soon."
def ld(o): return '<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace("</", "<\\/") + "</script>"
def common(h):
    """Applied to every page: self-hosted fonts, /about canonical+links, root-absolute nav."""
    h = h.replace(B.FONTS, FONT_LINKS)
    # seo2.css is no longer linked: all styles live in the versioned style.css
    h = h.replace(f"{SITE}/about.html", f"{SITE}/about").replace('href="/about.html"', 'href="/about"').replace('href="about.html', 'href="/about')
    h = h.replace('href="index.html#', 'href="/#').replace('href="index.html"', 'href="/"').replace('href="/index.html#', 'href="/#').replace('href="/index.html"', 'href="/"')
    h = re.sub(r"<nav>.*?</nav>", lambda m: m.group(0) if "/breakouts/" in m.group(0) else m.group(0).replace('<a href="/#sponsor">Sponsor</a>', '<a href="/breakouts/">Breakouts</a><a href="/daily/">Archive</a>', 1), h, 1, re.S)
    h = h.replace('<a href="/#frontier">Frontier</a>', '', 1) if 'labs/">Labs</a>' in h else h.replace('<a href="/#frontier">Frontier</a>', '<a href="/#frontier">Frontier</a>', 1)
    h = re.sub(r'>\+([\d.]+[KM]?) stars<', r'>\1 stars total<', h)  # a total, not a gain
    h = re.sub(r"\b1 days\b", "1 day", h).replace(">1 hourly runs<", ">1 hourly run<")
    h = h.replace('<a href="/breakouts/">Breakouts</a>', f'<a href="/breakouts/">{BLABEL}</a>').replace('<a href="/breakouts/">Breakouts</a>', f'<a href="/breakouts/">{BLABEL}</a>')
    h = re.sub(r'<svg class="spark"([^>]*)><title>(.*?)</title>', r'<svg class="spark"\1 role="img" aria-label="\2">', h)  # no stray <title> inside SVGs
    if "footlinks" not in h: h = h.replace("<footer>", "<footer>" + FOOT_LINKS, 1)
    if 'application/rss+xml' not in h: h = h.replace("</head>", f'<link rel="alternate" type="application/rss+xml" title="{BRAND}: new breakouts" href="/feed.xml"></head>', 1)
    return h
def wr(path, h):
    os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "w").write(common(h))
def load_items():
    out = {}
    for p in glob.glob(os.path.join(ARC, "items", "*.json")):
        I = json.load(open(p)); out[I["slug"]] = I
    return out
def load_days():
    return {os.path.basename(p)[:-5]: json.load(open(p)) for p in sorted(glob.glob(os.path.join(ARC, "daily", "*.json")))}
def snap_series(ids):
    """Real metric history per id from stored hourly snapshots (~14 days kept)."""
    s = {i: [] for i in ids}
    for f in sorted(os.listdir(SNAP)):
        S = json.load(open(os.path.join(SNAP, f)))
        for x in S["items"]:
            cid = canon(x["id"])  # follow GitHub renames so history doesn't split
            if cid in s: s[cid].append((S["taken"], x["metric"] or 0))
    return s
def fmt_t(iso): return dt.datetime.fromisoformat(iso).strftime("%b %d, %Y %H:%M UTC")
def crumbs(*pairs):
    return {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": n, "item": SITE + u} for k, (n, u) in enumerate(pairs)]}
def item_schema(I, path):
    kind = {"github": "SoftwareSourceCode", "npm": "SoftwareApplication", "pypi": "SoftwareApplication",
            "huggingface": "SoftwareApplication" if I["kind"] == "tool" else "CreativeWork", "hackernews": "Article"}[I["source"]]
    o = {"@type": kind, "name": I["name"], "url": I["url"], "sameAs": I["url"], "description": desc_of(I)[:300] or None}
    if kind == "SoftwareSourceCode": o["codeRepository"] = I["url"]
    if kind == "SoftwareApplication": o["applicationCategory"] = "DeveloperApplication"
    if kind == "Article": o["headline"] = I["name"][:110]
    if I.get("created"): o["dateCreated" if kind != "Article" else "datePublished"] = I["created"]
    return {"@context": "https://schema.org", "@graph": [{"@type": "WebPage", "name": f"{I['name']}: breakout history", "url": SITE + path, "mainEntity": {k: v for k, v in o.items() if v}},
            crumbs(("Home", "/"), ("Archive", "/daily/"), (B.LABEL[I["source"]], f"/{I['source']}/" if I["source"] in {c[0] for c in CATS} else "/daily/"), (I["name"][:60], path))]}
def apply(DIST, d, t):
    shutil.copytree(os.path.join(ROOT, "fonts"), os.path.join(DIST, "fonts"), dirs_exist_ok=True)
    shutil.copy(os.path.join(ROOT, "seo2.css"), DIST)
    global BLABEL
    items, days = load_items(), load_days()
    if days and len(days) < 7: BLABEL = "Breakouts since " + dt.date.fromisoformat(min(days)).strftime("%b %-d")
    elif days: BLABEL = "This week's breakouts"
    pool = {}
    # overlay the current run (the latest top 10) so every top-10 item has a page, a daily entry and a breakouts entry
    import archive as _A
    gt = d["generated"]; today = gt[:10]
    D = days.setdefault(today, {"day": today, "runs": [], "items": {}})
    newrun = gt not in D["runs"]
    if newrun: D["runs"] = D["runs"] + [gt]
    for r, i in enumerate(d["top"], 1):
        sl = _A.slug(i); I = items.get(sl)
        if I is None:
            I = items[sl] = dict(id=i["id"], slug=sl, first_seen=gt, appearances=[], peak_score=0, best_rank=99, days=[])
        if not any(a["t"] == gt for a in I["appearances"]): I["appearances"] = I["appearances"] + [dict(rank=r, score=i["score"], metric=i["metric"], t=gt)]
        I.update(name=i["name"], url=i["url"], source=i["source"], kind=i["kind"], desc=i.get("desc") or "", what=i.get("what") or "", tag=i.get("tag"),
                 metric_name=i["metric_name"], created=i.get("created"), last_seen=gt, extra=i.get("extra") or {}, metric=i["metric"],
                 peak_score=max(I["peak_score"], i["score"]), best_rank=min(I["best_rank"], r), days=sorted(set(I.get("days", [])) | {today}))
        e_ = D["items"].get(sl)
        if e_ is None: e_ = D["items"][sl] = dict(id=i["id"], slug=sl, first_seen=gt, peak_score=0, best_rank=99, runs_in_top10=0)
        e_.update(name=i["name"], url=i["url"], source=i["source"], kind=i["kind"], what=i.get("what") or "", tag=i.get("tag"), extra=i.get("extra") or {},
                  metric_name=i["metric_name"], last_seen=gt, peak_score=max(e_["peak_score"], i["score"]), best_rank=min(e_["best_rank"], r),
                  runs_in_top10=min(e_["runs_in_top10"] + (1 if newrun else 0), len(D["runs"])))
    for k in ("top", "models", "tools", "news", "frontier"):
        for x in d.get(k, []): pool.setdefault(x["id"], x)
    ser = snap_series(set(I["id"] for I in items.values()) | set(pool))
    POOL.clear()
    _sn = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "snapshots", "*.json")))
    if _sn:
        for x in json.load(open(_sn[-1])).get("items", []): POOL[x["id"]] = x
    POOL.update(pool); SER.clear(); SER.update(ser); LATEST["t"] = d["generated"]
    slug_of = {i["id"]: _A.slug(i) for i in d["top"]}
    # ---- homepage
    hp = os.path.join(DIST, "index.html"); h = open(hp).read()
    h = re.sub(r"<title>.*?</title>", f"<title>{e(TITLE)}</title>", h, 1, re.S)
    h = h.replace('<meta property="og:title" content="' + e(f"{BRAND}: what's breaking out in AI right now") + '">', f'<meta property="og:title" content="{e(TITLE)}">')
    h = re.sub(r"<h1>.*?</h1>", f"<h1>{H1}</h1>", h, 1, re.S)
    def hrow(i, n):
        sl = slug_of[i["id"]]; ip = ipath(sl, i["source"]) if sl in items else None
        t_ = (f'<a class="title" href="{ip}">{e(i["name"])}</a>' if ip else f'<a class="title" href="{e(i["url"])}" rel="nofollow noopener" target="_blank">{e(i["name"])}</a>')
        return (f'<tr data-src="{i["source"]}" data-tag="{i["tag"]}"><td class="rk">{n}</td><td class="it"><div class="badges"><span class="sb s-{i["source"]}">{badge(i)}</span><span class="tg">#{e(i["tag"])}</span></div>'
                f'{t_}<a class="out" href="{e(i["url"])}" rel="nofollow noopener" target="_blank" aria-label="Open on {B.LABEL[i["source"]]}">↗</a><p class="what">{e(desc_of(i))}</p></td>'
                f'<td class="tr">{B.trend(i.get("hist"))}</td><td class="mo"><b>{e(measure(i))}</b><span>{e(total_of(i))}</span></td>'
                f'<td class="sc"><b>{i["score"]:.0f}</b><i><u style="width:{i["score"]:.0f}%"></u></i></td></tr>')
    h = re.sub(r"<tbody>.*?</tbody>", "<tbody>" + "".join(hrow(i, n + 1) for n, i in enumerate(d["top"])).replace("\\", "\\\\") + "</tbody>", h, 1, re.S)
    # hero chart label: link to the item's permanent page when it has one
    for o in d["top"]:
        if slug_of[o["id"]] in items:
            h = h.replace(f'<a class="hc-link" href="{e(o["url"])}" rel="nofollow noopener" target="_blank">', f'<a class="hc-link" href="{ipath(slug_of[o["id"]], o["source"])}">', 1)
    # sponsor: slim strip below the top 10
    m = re.search(r'<section id="sponsor" class="spon">.*?</section>', h, re.S)
    if m: h = h.replace(m.group(0), sponsor_strip(), 1)
    cats = "".join(f'<a href="/{c[0]}/">{c[1]}</a>' for c in CATS)
    h = h.replace('<p class="empty dim" hidden>', f'<p class="catlinks">Browse: {cats}<a href="/breakouts/">Breakouts</a></p><p class="empty dim" hidden>', 1)
    latest = max(days) if days else None
    arch = (f'<p class="arch dim">Every top-10 item gets a permanent history page. <a href="/daily/{latest}/">Today\'s archive ({latest})</a> <a href="/daily/">All days</a></p>'
            if latest else "")
    h = h.replace('<p class="empty dim" hidden>', arch + '<p class="empty dim" hidden>', 1)
    j = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": SITE + "/#website", "name": BRAND, "url": SITE + "/", "description": B.DESC, "publisher": {"@id": SITE + "/#org"}},
        {"@type": "Organization", "@id": SITE + "/#org", "name": BRAND, "url": SITE + "/", "logo": SITE + "/favicon.svg", "sameAs": [B.X_URL]},
        {"@type": "ItemList", "name": "Top 10 breaking out in AI right now", "numberOfItems": len(d["top"]), "itemListOrder": "https://schema.org/ItemListOrderDescending",
         "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": i["name"],
                              "url": SITE + ipath(slug_of[i["id"]], i["source"]) if slug_of[i["id"]] in items else i["url"]} for k, i in enumerate(d["top"])]}]}
    h = h.replace("</head>", ld(j) + "</head>", 1)
    wr(hp, h)
    # ---- about: FAQPage built from the about page's own text
    ap = os.path.join(DIST, "about.html"); a = open(ap).read()
    a = a.replace("One pinned slot per week on the site and in the daily email: Sponsor this spot: email for rates.", sponsor_about())
    lis = [B.re_strip(x) for x in re.findall(r"<li>(.*?)</li>", a, re.S)]
    paras = [B.re_strip(x) for x in re.findall(r"<p>(.*?)</p>", a, re.S)]
    faq = [("What does NextAiBreakout rank?", paras[0]),
           ("Which sources are tracked and how is each measured?", " ".join(lis)),
           ("How is the breakout score calculated?", next(p for p in paras if p.startswith("Each source"))),
           ("How can I sponsor NextAiBreakout?", next(p for p in paras if "Sponsor" in p or "sponsor" in p))]
    a = a.replace("</head>", ld({"@context": "https://schema.org", "@graph": [{"@type": "AboutPage", "name": f"About {BRAND}", "url": SITE + "/about"},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in faq]}]}) + "</head>", 1)
    wr(ap, a)
    for f in ("404.html",): wr(os.path.join(DIST, f), open(os.path.join(DIST, f)).read())
    for p in glob.glob(os.path.join(DIST, "labs", "**", "index.html"), recursive=True): wr(p, open(p).read())
    # ---- per-item pages
    for s, I in items.items():
        path = ipath(I); S = ser.get(I["id"], [])
        cur = POOL.get(I["id"], {}); Iv = {**I, **{k: cur[k] for k in ("metric", "extra") if k in cur}}
        if not Iv.get("metric") and I.get("appearances"): Iv["metric"] = I["appearances"][-1]["metric"]
        hist = [m for _, m in S]
        rows = "".join(f"<tr><td class='dim'>{fmt_t(a['t'])}</td><td>#{a['rank']}</td><td>{a['score']:.0f}</td><td>{B.e(str(a['metric']))}</td></tr>" for a in reversed(I["appearances"][-48:]))
        dlinks = ", ".join(f'<a href="/daily/{x}/">{x}</a>' for x in reversed(I.get("days", [])))
        kind = {"github": "trending AI repo", "npm": "trending AI package", "pypi": "trending AI package", "hackernews": "trending AI story"}.get(I["source"], "trending AI Space" if badge(I) == "HF Space" else "trending AI model")
        title = B.seo_title(f"{I['name']}: {kind}") if len(I['name']) <= 40 else B.seo_title(I['name'])
        desc = B.fit(f"{I['name'][:80]} ({badge(I)}) reached #{I['best_rank']} on NextAiBreakout's hourly AI ranking. Real {I['metric_name']} history and top-10 runs.", 155)
        enough = len(hist) >= 3 and max(hist) != min(hist)
        chart = (f'<div class="item-spark">{B.spark(hist, 720, 120, B.GOLD, True)}</div>' if enough else
                 f'<div class="item-spark wait"><p>The history chart appears once this item has 3 hourly snapshots. {plural(len(hist), "snapshot")} recorded so far.</p></div>')
        page = B.head(title, desc, path, "/", ld(item_schema(Iv, path))) + f"""<main><section class="labs-hero">
<h1>{e(I['name'])}</h1><p class="dim">{e(desc_of(I))}</p>
<div class="btns"><a class="btn pri" href="{e(I['url'])}" rel="nofollow noopener" target="_blank">Open on {B.LABEL[I['source']]}</a><a class="btn share" href="https://x.com/intent/tweet?text={quote(I['name'][:120] + ' is breaking out on NextAiBreakout')}&amp;url={quote(SITE + path)}&amp;via={B.X_HANDLE[1:]}" rel="noopener" target="_blank">Share on X</a></div></section>
<section class="stats"><div><span>Best rank</span><b>#{I['best_rank']}</b></div><div><span>Peak score</span><b>{I['peak_score']:.0f}</b></div>
<div><span>Hours in top 10</span><b>{len(I['appearances'])}</b></div><div><span>First seen</span><b class="fs">{fmt_t(I['first_seen'])[:12]}</b></div></section>
<section><h2>{e(I['metric_name'].capitalize())} history</h2><p class="dim">From {len(hist)} real hourly snapshots{(' (' + fmt_t(S[0][0]) + ' to ' + fmt_t(S[-1][0]) + ')') if S else ''}. Nothing is interpolated.</p>
{chart}<p class="dim mom">Momentum: {e(measure(Iv))}, {e(total_of(Iv))}</p></section>
<section><h2>Top-10 appearances</h2><div class="tbl"><table class="apps"><thead><tr><th>Run</th><th>Rank</th><th>Score</th><th>{e(I['metric_name'])}</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="dim">Days in the archive: {dlinks}</p></section></main>""" + B.foot(t.year, "/") + "</body></html>"
        page = page.replace("<main>", "<main>" + vcrumbs(("Home", "/"), (B.LABEL[I["source"]], f"/{I['source']}/" if I["source"] in {c[0] for c in CATS} else "/daily/"), (I["name"][:60], path)), 1)
        wr(os.path.join(DIST, path.strip("/"), "index.html"), page)
    # ---- daily pages
    ds = sorted(days)
    for k, day in enumerate(ds):
        D = days[day]; its = sorted(D["items"].values(), key=lambda x: (-x["peak_score"], x["best_rank"]))
        path = f"/daily/{day}/"; nice = dt.date.fromisoformat(day).strftime("%B %-d, %Y")
        nav = (f'<a href="/daily/{ds[k-1]}/">← {ds[k-1]}</a>' if k else "") + (f' <a href="/daily/{ds[k+1]}/">{ds[k+1]} →</a>' if k + 1 < len(ds) else "")
        lis = "".join(f"""<li><span class="rk">{n}</span><div><span class="sb s-{x['source']}">{badge(x)}</span> <a class="title" href="{ipath(x)}">{e(x['name'])}</a>
<p class="what">{e(desc_of(x))}</p><p class="meta dim">Peak score {x['peak_score']:.0f} · best #{x['best_rank']} · {min(x['runs_in_top10'], len(D['runs']))} of {plural(len(D['runs']), 'hourly run')} in top 10 · {e(measure(dict(x, metric=(SER.get(x['id']) or [(0, x.get('metric_at_peak') or 0)])[-1][1], created=items.get(x['slug'], {}).get('created'))))}</p></div></li>""" for n, x in enumerate(its, 1))
        title = B.seo_title(f"Trending AI repos & models, {dt.date.fromisoformat(day).strftime('%b %-d, %Y')}")
        desc = f"The AI repos, models and stories that hit NextAiBreakout's hourly top 10 on {nice} (UTC), with peak scores and real metrics."
        j = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": f"AI breakouts on {nice}", "url": SITE + path, "datePublished": day,
             "mainEntity": {"@type": "ItemList", "numberOfItems": len(its), "itemListElement": [{"@type": "ListItem", "position": n, "name": x["name"], "url": SITE + ipath(x)} for n, x in enumerate(its, 1)]}},
             crumbs(("Home", "/"), ("Archive", "/daily/"), (day, path))]}
        page = B.head(title, desc, path, "/", ld(j)) + f"""<main><section class="labs-hero">
<h1>Trending AI on {nice}</h1><p class="stamp"><span class="dot"></span>{len(D['runs'])} hourly run{'s' if len(D['runs']) != 1 else ''} recorded · day in UTC · last {fmt_t(D['runs'][-1])}</p>
<p class="dim">Everything that reached the hourly top 10 on this day, ordered by peak breakout score. Recorded live; no days are backfilled.</p></section>
<ol class="daylist">{lis}</ol><p class="daynav">{nav}</p></main>""" + B.foot(t.year, "/") + "</body></html>"
        page = page.replace("<main>", "<main>" + vcrumbs(("Home", "/"), ("Daily archive", "/daily/"), (day, path)), 1)
        wr(os.path.join(DIST, "daily", day, "index.html"), page)
    idx = "".join(f'<li><a href="/daily/{x}/">{dt.date.fromisoformat(x).strftime("%B %-d, %Y")}</a> <span class="dim">{len(days[x]["items"])} items, {len(days[x]["runs"])} runs</span></li>' for x in reversed(ds))
    page = B.head(B.seo_title("Daily archive of trending AI repos & models"), "Day-by-day archive of the AI repos, models and stories that reached NextAiBreakout's hourly top 10. Recorded live since Oct 15, 2026.", "/daily/", "/",
                  ld({"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": "Daily AI breakout archive", "url": SITE + "/daily/"}, crumbs(("Home", "/"), ("Archive", "/daily/"))]})) + f"""<main><section class="labs-hero"><h1>Daily AI breakout archive</h1>
<p class="dim">One page per day, recorded live from the hourly ranking since {ds[0] if ds else 'today'}. No backfilled days.</p></section><ul class="dayidx">{idx or '<li class="dim">No days recorded yet.</li>'}</ul></main>""" + B.foot(t.year, "/") + "</body></html>"
    wr(os.path.join(DIST, "daily", "index.html"), page.replace("<main>", "<main>" + vcrumbs(("Home", "/"), ("Daily archive", "/daily/")), 1))
    extra_pages(DIST, d, t, items, days, slug_of, ser)
    # ---- sitemap, robots, llms
    urls = [("/", "hourly"), ("/about", "monthly"), ("/daily/", "daily")] + [(f"/daily/{x}/", "daily" if x == latest else "monthly") for x in ds] + [(ipath(items[s]), "daily") for s in sorted(items)] + [("/breakouts/", "daily")] + [(f"/{c[0]}/", "hourly") for c in CATS]
    if B.LABS: urls += [(p, "hourly") for p in ["/labs/"] + [f"/labs/{l['slug']}/" for l in B._labs()[0]]]
    day = t.strftime("%Y-%m-%d")
    open(os.path.join(DIST, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{day}</lastmod><changefreq>{c}</changefreq></url>" for p, c in urls) + "</urlset>\n")
    open(os.path.join(DIST, "robots.txt"), "w").write("# Search engines and AI assistants are welcome to crawl, cite and link to NextAiBreakout.\n"
        + "".join(f"User-agent: {b}\nAllow: /\n\n" for b in AI_BOTS) + "User-agent: *\nAllow: /\n\n" + f"Sitemap: {SITE}/sitemap.xml\n")
    lp = os.path.join(DIST, "llms.txt"); L = open(lp).read().replace(f"{SITE}/about.html", f"{SITE}/about")
    tl = "\n".join(f"- [{i['name']}]({SITE}{ipath(slug_of[i['id']], i['source'])}) ({badge(i)}, score {i['score']:.0f}): {' — '.join(v for v in (desc_of(i), measure(i)) if v)}" for i in d["top"])
    L = re.sub(r"(## Top 10 breaking out today\n).*?(\n\n## Pages)", lambda m: m.group(1) + tl + m.group(2), L, 1, re.S)
    extra = ["", "## Archive", f"- [Daily archive]({SITE}/daily/)"] + [f"- [{x}]({SITE}/daily/{x}/)" for x in reversed(ds[-14:])]
    if B.LABS:
        cfg, ld_ = B._labs(); extra += ["", "## Frontier Labs (official release feeds)", f"- [All labs]({SITE}/labs/)"] + [f"- [{l['name']}]({SITE}/labs/{l['slug']}/): {l['description']}" for l in cfg]
    open(lp, "w").write(L.rstrip("\n") + "\n" + "\n".join(extra) + "\n")
    print(f"[seo2] {len(items)} item pages, {len(ds)} daily pages")

def row_html(x, items, slug_of, n):
    """One list row; links on-site when a permanent item page exists, plus an outbound source icon."""
    import archive
    sl = archive.slug(x); ip = ipath(sl, x["source"]) if sl in items else None
    title = f'<a class="title" href="{ip}">{e(x["name"])}</a>' if ip else f'<a class="title" href="{e(x["url"])}" rel="nofollow noopener" target="_blank">{e(x["name"])}</a>'
    return (f'<li><span class="rk">{n}</span><div><span class="sb s-{x["source"]}">{badge(x)}</span> <span class="tg">#{e(x.get("tag") or "")}</span> {title}'
            f'<a class="out" href="{e(x["url"])}" rel="nofollow noopener" target="_blank" aria-label="Open on {B.LABEL[x["source"]]}">↗</a>'
            f'<p class="what">{e(desc_of(x))}</p><p class="meta dim">Score {x["score"]:.0f} · {e(measure(x))} · {e(total_of(x))}</p></div></li>')
def extra_pages(DIST, d, t, items, days, slug_of, ser):
    pool = {}
    for k in ("top", "models", "tools", "news", "frontier"):
        for x in d.get(k, []): pool.setdefault(x["id"], x)
    allx = sorted(pool.values(), key=lambda x: -x["score"])
    stamp = t.strftime("%b %d, %Y %H:%M UTC")
    # ---- source / category pages (current hourly run, real data)
    for key, label, h1, kind in CATS:
        its = [x for x in allx if (x["source"] == key if kind == "source" else x.get("tag") == key)][:30]
        rule = (f"Every {label} item in this hour's scored set, ordered by breakout score." if kind == "source" else
                f"Items tagged <b>#{key}</b> by a keyword rule on each item's own name, description and topics ({'agent, MCP, browser-use, autonomous, skill' if key=='agents' else 'Hugging Face model, or words like model, weights, LLM, NNb'}). Heuristic, not hand-curated.")
        path = f"/{key}/"; title = B.seo_title(CAT_TITLE[key])
        desc = B.fit(f"{h1} right now, ranked every hour by growth rate. Real metrics from public APIs, updated {stamp}.", 155)
        j = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": h1, "url": SITE + path,
             "mainEntity": {"@type": "ItemList", "numberOfItems": len(its), "itemListElement": [{"@type": "ListItem", "position": n, "name": x["name"],
             "url": SITE + ipath(slug_of.get(x["id"]) or __import__("archive").slug(x), x["source"]) if (__import__("archive").slug(x) in items) else x["url"]} for n, x in enumerate(its, 1)]}},
             crumbs(("Home", "/"), (label, path))]}
        body = "".join(row_html(x, items, slug_of, n) for n, x in enumerate(its, 1)) or f'<li class="dim lab-empty">Nothing from {e(label)} in this hour\'s scored set.</li>'
        page = B.head(title, desc, path, "/", ld(j)) + f"""<main>{vcrumbs(("Home", "/"), (label, path))}<section class="labs-hero"><h1>{e(h1)}</h1>
<p class="stamp"><span class="dot"></span>Updated {stamp}</p><p class="dim">{rule}</p></section><ol class="daylist">{body}</ol></main>""" + B.foot(t.year, "/") + "</body></html>"
        wr(os.path.join(DIST, key, "index.html"), page)
    # ---- weekly breakouts (last 7 recorded days, real archive only)
    last = sorted(days)[-7:]; agg = {}
    for dday in last:
        for sl, x in days[dday]["items"].items():
            a = agg.setdefault(sl, dict(x, runs=0, days=set()))
            a["runs"] += x["runs_in_top10"]; a["days"].add(dday); a["peak_score"] = max(a["peak_score"], x["peak_score"]); a["best_rank"] = min(a["best_rank"], x["best_rank"])
    # top 25 by runs in the top 10, plus every item in the current top 10 (a new entrant with few runs would
    # otherwise fall below the cut once the archive holds more than 25 items, leaving it with no /breakouts/ entry)
    cur10 = set(slug_of.values())
    ranked = sorted(agg.items(), key=lambda kv: (-kv[1]["runs"], -kv[1]["peak_score"]))
    its = [x for n, (sl, x) in enumerate(ranked) if n < 25 or sl in cur10]
    nruns = sum(len(days[x]["runs"]) for x in last)
    lis = "".join(f"""<li><span class="rk">{n}</span><div><span class="sb s-{x['source']}">{badge(x)}</span> <a class="title" href="{ipath(x)}">{e(x['name'])}</a><a class="out" href="{e(x['url'])}" rel="nofollow noopener" target="_blank" aria-label="Open on {B.LABEL[x['source']]}">↗</a>
<p class="what">{e(desc_of(x))}</p><p class="meta dim">{min(x['runs'], nruns)} of {plural(nruns, 'hourly run')} in the top 10 · peak score {x['peak_score']:.0f} · best #{x['best_rank']} · {len(x['days'])} day{'s' if len(x['days'])!=1 else ''}</p></div></li>""" for n, x in enumerate(its, 1)) or '<li class="dim">No runs recorded yet.</li>'
    span = f"{last[0]} to {last[-1]}" if last else "no days yet"
    j = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": BLABEL, "url": SITE + "/breakouts/",
         "mainEntity": {"@type": "ItemList", "numberOfItems": len(its), "itemListElement": [{"@type": "ListItem", "position": n, "name": x["name"], "url": SITE + ipath(x)} for n, x in enumerate(its, 1)]}}, crumbs(("Home", "/"), (BLABEL, "/breakouts/"))]}
    page = B.head(B.seo_title("Top AI breakouts: most hours in the top 10"), f"The AI repos, models and stories that held NextAiBreakout's hourly top 10 longest over the last 7 recorded days ({span}).", "/breakouts/", "/", ld(j)) + f"""<main>{vcrumbs(("Home", "/"), (BLABEL, "/breakouts/"))}
<section class="labs-hero"><h1>{e(BLABEL)}</h1><p class="stamp"><span class="dot"></span>{span} · {plural(nruns, 'hourly run')} recorded</p>
<p class="dim">Ranked by how many hourly runs each item spent in the top 10, then by peak score; everything in the current top 10 is always listed. Built only from recorded runs{' (recording started Oct 15, 2026, so this list is partial)' if len(last) < 7 else ''}.</p></section><ol class="daylist">{lis}</ol></main>""" + B.foot(t.year, "/") + "</body></html>"
    wr(os.path.join(DIST, "breakouts", "index.html"), page)
    # ---- RSS: newest items to enter the top 10 (real first-seen times)
    import email.utils as eu
    import archive as _a
    feed = [dict(x, slug=_a.slug(x)) for x in d["top"]]
    def rfc(iso): return eu.format_datetime(dt.datetime.fromisoformat(iso))
    xi = "".join(f"<item><title>{e(I['name'])} ({badge(I)})</title><link>{SITE}{ipath(I)}</link><guid isPermaLink=\"false\">{SITE}{ipath(I)}#{d['generated'][:13]}</guid>"
                 f"<pubDate>{rfc(d['generated'])}</pubDate><description>{e(' — '.join(v for v in [desc_of(I)[:300], measure(I), 'score ' + format(I['score'], '.0f')] if v))}</description></item>" for n, I in enumerate(feed, 1))
    open(os.path.join(DIST, "feed.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>{BRAND}: new AI breakouts</title>'
        f'<link>{SITE}/</link><atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/><description>The current hourly top 10 AI breakouts, rebuilt every run.</description>'
        f'<lastBuildDate>{rfc(d["generated"])}</lastBuildDate>{xi}</channel></rss>\n')
    # ---- Cloudflare Pages redirects for legacy/bare nav paths
    # renamed GitHub repos: the old item page 301s to the canonical one
    for o in aliases():  # drop the old page left over from earlier builds so the 301 applies
        if o.startswith("gh:"): shutil.rmtree(os.path.join(DIST, ipath(_a.slug(dict(source='github', id=o, name=o)), 'github').strip("/")), ignore_errors=True)
    ren = "".join(f"{ipath(_a.slug(dict(source='github', id=o, name=o)), 'github')} {ipath(_a.slug(dict(source='github', id=canon(o), name=o)), 'github')} 301\n"
                  for o in sorted(aliases()) if o.startswith("gh:"))
    open(os.path.join(DIST, "_redirects"), "w").write("/today /#top10 301\n/frontier " + ("/labs/" if B.LABS else "/#frontier") + " 301\n/archive /daily/ 301\n" + ren)
