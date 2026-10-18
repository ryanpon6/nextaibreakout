"""Grok Bot updates page (/grok-bot/). Gated by GROKBOT=1 in build.py; also runnable standalone: python3 grokbot.py <distdir>.
Sources: x.ai/changelog/bot/rss.xml (cached, refetched at most hourly), x.ai/news (change check at most daily).
No X API calls; x.com posts are linked only, never fetched."""
import datetime as dt, hashlib, html, json, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from common import DATA
RSS = "https://x.ai/changelog/bot/rss.xml"; NEWS = "https://x.ai/news"
SITE = "https://nextaibreakout.com"; PATH = "/grok-bot/"
e = html.escape
UA = {"User-Agent": "Mozilla/5.0 (nextaibreakout.com bot)"}
def cached(url, fn, max_age):
    p = os.path.join(DATA, fn)
    if os.path.exists(p) and time.time() - os.path.getmtime(p) < max_age: return open(p, encoding="utf-8").read()
    try:
        b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode("utf-8", "replace")
        if len(b) > 500:
            open(p + ".tmp", "w", encoding="utf-8").write(b); os.replace(p + ".tmp", p); return b
    except Exception as x: print(f"[grokbot] fetch {url} failed: {x}")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""
def news_check():
    b = cached(NEWS, "grokbot-news.html", 86400)
    links = sorted(set(re.findall(r'href="(/news/[a-z0-9-]*grok-bot[a-z0-9-]*|/news/team-bots)"', b)))
    st = os.path.join(DATA, "grokbot-news.json"); old = json.load(open(st)) if os.path.exists(st) else {}
    h = hashlib.sha256("\n".join(links).encode()).hexdigest()
    if old.get("hash") != h:
        new = [l for l in links if l not in old.get("links", [])]
        json.dump({"hash": h, "links": links, "changed": dt.datetime.now(dt.timezone.utc).isoformat(), "new": new}, open(st, "w"))
        if old: print(f"[grokbot] x.ai/news Grok Bot links changed: {new}")
    return links
# Curated items from grok-bot-updates.md (Research, Oct 16). Team Bots + 'Grok Bot now works with X' removed: already on /labs/xai/.
CURATED = [
 ("2026-10-11", "Grok Bots get their own email address, X search and payments (v0.70.2)", "Per the Grok Bot changelog, Bots can claim their own email address (mail they send waits for your approval on a draft card), search X without a connected account, and pay with X Money or Stripe Link.", "https://x.ai/changelog/bot#v0.70.2", "Changelog"),
 ("2026-10-08", "Grok Bot can run your Shopify store", "@bot says that after you connect Shopify you can ask it to check orders, track inventory and keep product listings up to date.", "https://x.com/bot/status/2108228871938359347", "@bot on X"),
 ("2026-09-30", "Grok Bot gets better at building software", "@bot says Bots can hand coding tasks to Cursor, manage PRs with the GitHub and Origin plugins, and share video demos of what they build.", "https://x.com/bot/status/2105373767568621895", "@bot on X"),
 ("2026-09-26", "Grok Bot connects to your finances", "@bot says a new Finance integration links bank, card and investment accounts so a Bot can help manage spending and investments.", "https://x.com/bot/status/2103936247995752705", "@bot on X"),
 ("2026-09-22", "How SpaceXSI runs customer support on Grok Bot", "SpaceXSI says its combined SpaceXSI/Cursor support team had a 175% rise in tickets with no new hires, resolved tickets for as little as $0.20–$0.30 each, and resolves 99% of refund requests without a person.", "https://x.ai/news/grok-bot-customer-support", "x.ai/news"),
 ("2026-09-04|Sep 4, 2026 (announced by @bot)", "“Haggle Bot” identified $100K+ in procurement savings", "SpaceXSI says its procurement Bot identified more than $100,000 in direct savings and, in one run, cut a $14,629 tech order to $6,143 (58%). It is available to copy in the Bot Marketplace.", "https://x.ai/news/grok-bot-procurement", "x.ai/news"),
]
def strip(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
def releases(n=12):
    b = cached(RSS, "grokbot-rss.xml", 3600); out = []
    try: root = ET.fromstring(b)
    except Exception as x: print(f"[grokbot] rss parse failed: {x}"); return out
    for it in root.iter("item"):
        d = parsedate_to_datetime(it.findtext("pubDate")).date().isoformat()
        desc = it.findtext("description") or ""
        lis = [strip(m) for m in re.findall(r"<li>(.*?)</li>", desc, re.S)][:3]
        out.append((d, it.findtext("title").strip(), lis, it.findtext("link").strip()))
    return out[:n]
def labs_xai_urls(DIST):
    p = os.path.join(DIST, "labs", "xai", "index.html")
    return set(re.findall(r'href="(https?://[^"]+)"', open(p).read())) if os.path.exists(p) else set()
def fd(d):
    if "|" in d: return d.split("|", 1)[1]
    return dt.date.fromisoformat(d).strftime("%b %-d, %Y")
def ld(o): return '<script type="application/ld+json">' + json.dumps(o, ensure_ascii=False).replace("</", "<\\/") + "</script>"
def apply(DIST):
    news_check()
    dup = labs_xai_urls(DIST)
    cur = [c for c in CURATED if c[3] not in dup]
    curl = {c[3] for c in cur}
    rel = [r for r in releases() if r[3] not in curl and r[3] not in dup][:10]
    Q1 = ("What is Grok Bot?", "Grok Bot is SpaceXSI's AI agent product. You create Bots that connect to your apps and accounts, such as email, Slack, Shopify, GitHub and X, and they do work for you, with approval steps for actions like sending email.")
    top = cur[:3]
    Q2 = ("What’s new in Grok Bot?", "The latest updates: " + " ".join(f"{t} ({fd(d)})." for d, t, *_ in top))
    tpl = open(os.path.join(DIST, "about.html")).read()
    headpart = tpl.split("</head>")[0]
    headpart = re.sub(r"<title>.*?</title>", "<title>Grok Bot updates, features &amp; changelog | NextAiBreakout</title>", headpart, count=1, flags=re.S)
    desc = "Every Grok Bot update in one place: new features, integrations and changelog releases from SpaceXSI, with links to the official source for each item."
    headpart = re.sub(r'<meta name="description" content="[^"]*"', f'<meta name="description" content="{e(desc)}"', headpart, count=1)
    headpart = re.sub(r'<link rel="canonical" href="[^"]*"', f'<link rel="canonical" href="{SITE}{PATH}"', headpart, count=1)
    headpart = re.sub(r'(property="og:(?:url)" content=")[^"]*', rf'\g<1>{SITE}{PATH}', headpart)
    headpart = re.sub(r'(property="og:title" content=")[^"]*', r'\g<1>Grok Bot updates, features &amp; changelog', headpart)
    headpart = re.sub(r'(property="og:description" content=")[^"]*', rf'\g<1>{e(desc)}', headpart)
    headpart = re.sub(r'<script type="application/ld\+json">.*?</script>', "", headpart, flags=re.S)
    allitems = [(d, t, u) for d, t, _, u, _ in cur] + [(d, t, u) for d, t, _, u in rel]
    schema = [ld({"@context": "https://schema.org", "@type": "ItemList", "name": "Grok Bot updates", "url": SITE + PATH,
                  "itemListElement": [{"@type": "ListItem", "position": k, "name": t, "url": u} for k, (d, t, u) in enumerate(allitems, 1)]}),
              ld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in (Q1, Q2)]}),
              ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}, {"@type": "ListItem", "position": 2, "name": "Grok Bot updates", "item": SITE + PATH}]})]
    headpart += "".join(schema)  # page styles live in style.css (.gb), so they follow the site theme
    body_open = re.search(r"<body[^>]*>.*?</header>", tpl, re.S).group(0)
    foot = re.search(r"<footer.*?</footer>", tpl, re.S).group(0)
    footlinks = re.search(r'<nav class="footlinks.*?</nav>', tpl, re.S)
    def card(d, t, txt, u, src):
        return f'<li class="c"><div class="meta mono">{fd(d)} · <b>{e(src)}</b></div><a href="{e(u)}" rel="noopener" target="_blank">{e(t)}</a><p>{e(txt)}</p></li>'
    def rcard(d, t, lis, u):
        return f'<li class="c"><div class="meta mono">{fd(d)} · <b>Changelog</b></div><a href="{e(u)}" rel="noopener" target="_blank">{e(t)}</a>' + ("<ul class=\"n\">" + "".join(f"<li>{e(x)}</li>" for x in lis) + "</ul>" if lis else "") + "</li>"
    main = f"""<main class="wrap gb"><nav class="crumbs mono" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/labs/xai/">SpaceXSI</a> / <span aria-current="page">Grok Bot updates</span></nav>
<h1><span class="accent">Grok Bot</span> updates, features &amp; changelog</h1>
<p class="lede">New Grok Bot features and releases from SpaceXSI, newest first. Each item links to its official source: the <a href="https://x.ai/changelog/bot">Grok Bot changelog</a>, <a href="https://x.ai/news">x.ai/news</a> or the official @bot account on X. Figures are the publishing company's own claims (SpaceXSI on x.ai, SpaceXAI on @bot). More SpaceXSI (xAI) news: <a href="/labs/xai/">xAI on Frontier Labs</a>.</p>
<h2>Top Grok Bot updates</h2><ol>{"".join(card(*c) for c in cur)}</ol>
<h2>Latest changelog releases</h2><ol>{"".join(rcard(*r) for r in rel)}</ol>
<section class="faq"><h2>FAQ</h2><h3>{e(Q1[0])}</h3><p>{e(Q1[1])}</p><h3>{e(Q2[0])}</h3><p>{e(Q2[1])}</p></section>
<p class="meta mono">Changelog checked hourly · <a href="{RSS}">changelog RSS</a></p>{footlinks.group(0) if footlinks else ""}</main>"""
    page = re.sub(r'(href|src)="(?![/#]|https?:|mailto:|data:)', r'\1="/', headpart + "</head>" + body_open + main + foot + "</body></html>")
    os.makedirs(os.path.join(DIST, "grok-bot"), exist_ok=True)
    open(os.path.join(DIST, "grok-bot", "index.html"), "w").write(page)
    # nav, homepage, /labs/xai/ links
    link = '<a href="/grok-bot/">Grok Bot</a>'
    for root, _, fs in os.walk(DIST):
        for f in fs:
            if not f.endswith(".html"): continue
            p = os.path.join(root, f); h = open(p).read()
            h2 = re.sub(r"(<nav>.*?<a href=\"/labs/\">Labs</a>)", lambda m: m.group(1) if "/grok-bot/" in m.group(0) else m.group(1) + link, h, count=1, flags=re.S)
            if h2 != h: open(p, "w").write(h2)
    hp = os.path.join(DIST, "index.html"); h = open(hp).read()
    if 'class="gbhome"' not in h:
        h = h.replace('<footer', '<p class="wrap gbhome">New: <a href="/grok-bot/">Grok Bot updates, features &amp; changelog</a></p><footer', 1); open(hp, "w").write(h)
    xp = os.path.join(DIST, "labs", "xai", "index.html")
    if os.path.exists(xp):
        h = open(xp).read()
        if 'class="gbx"' not in h: h = h.replace("<footer", '<p class="wrap mono gbx">All Grok Bot releases and features: <a href="/grok-bot/">Grok Bot updates &amp; changelog</a></p><footer', 1); open(xp, "w").write(h)
    sp = os.path.join(DIST, "sitemap.xml"); s = open(sp).read()
    if PATH not in s: open(sp, "w").write(s.replace("</urlset>", f"<url><loc>{SITE}{PATH}</loc><lastmod>{allitems[0][0].split("|")[0]}</lastmod></url></urlset>"))
    lp = os.path.join(DIST, "llms.txt"); L = open(lp).read()
    if PATH not in L: open(lp, "w").write(L.rstrip("\n") + f"\n- [Grok Bot updates, features & changelog]({SITE}{PATH}): Grok Bot releases and features from SpaceXSI, with official sources.\n")
    print(f"[grokbot] wrote {PATH}: {len(cur)} featured + {len(rel)} changelog = {len(allitems)} items")
    return len(allitems)
if __name__ == "__main__": apply(sys.argv[1] if len(sys.argv) > 1 else "dist")
