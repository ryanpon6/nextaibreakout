"""Render static site + per-run OG image to dist/."""
import datetime as dt, html, json, os, shutil, subprocess, tempfile
from common import DATA, DIST, ROOT
DIST = os.getenv("NAB_DIST") or DIST
LABS = os.getenv("LABS") == "1"
SEO2 = os.getenv("SEO2") == "1"  # SEO fixes + archive/item pages: off by default so the hourly cron does not publish them yet
import re as _re
def re_strip(s): return _re.sub(r"\s+", " ", html.unescape(_re.sub(r"<[^>]+>", "", s))).strip()  # Frontier Labs pages: off by default so the hourly cron deploy does not publish them yet
SITE = "https://nextaibreakout.com"; BRAND = "NextAiBreakout"; TAG = "Tracking the road to superintelligence."
DESC = "AI repos, models and packages ranked hourly by velocity, not hype. Tracked across GitHub, Hugging Face, npm, PyPI and Hacker News."
e = html.escape
LABEL = {"github": "GitHub", "huggingface": "Hugging Face", "npm": "npm", "pypi": "PyPI", "hackernews": "Hacker News"}
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">'
LOGO = '<svg class="logo" viewBox="0 0 32 32" aria-hidden="true"><rect x="1" y="1" width="30" height="30" rx="8" fill="#0E100F" stroke="url(#lg)" stroke-width="2"/><defs><linearGradient id="lg" x1="0" x2="1"><stop stop-color="#3DDC84"/><stop offset="1" stop-color="#3DDC84"/></linearGradient></defs><path d="M8 22l6-6 4 4 7-8M19 12h6v6" stroke="url(#lg)" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>'
WORD = f'{LOGO}<span>NextAi<b class="grad">Breakout</b></span>'

def spark(hist, w=120, h=32, color="#3DDC84", fill=False):
    """Sparkline from REAL snapshot history only. <3 points -> flat dashed line labelled as collecting."""
    if not hist or len(hist) < 3 or max(hist) == min(hist):
        return (f'<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><title>Collecting history (needs 3+ hourly snapshots)</title>'
                f'<line x1="2" y1="{h/2}" x2="{w-2}" y2="{h/2}" stroke="#2c332f" stroke-width="1.5" stroke-dasharray="3 4"/></svg>')
    lo, hi = min(hist), max(hist); n = len(hist)
    pts = [(2 + (w - 4) * k / (n - 1), h - 3 - (h - 6) * (v - lo) / (hi - lo)) for k, v in enumerate(hist)]
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f'<polygon points="2,{h} {p} {w-2},{h}" fill="{color}" opacity=".12"/>' if fill else ""
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><title>{n} hourly snapshots</title>{area}'
            f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round"/>'
            f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="2.5" fill="{color}"/></svg>')

def head(title, desc, path, root="", extra=""):
    labscss = f'<link rel="stylesheet" href="{root or "/"}labs.css">' if LABS else ""
    labsnav = f'<a href="{root or "/"}labs/">Labs</a>' if LABS else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}"><meta property="og:image" content="{SITE}/og-default.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/og-default.png"><meta name="theme-color" content="#0A0B0A">
<link rel="icon" href="/favicon.svg">{FONTS}<link rel="stylesheet" href="{root}style.css">{labscss}{extra}</head><body>
<header class="top"><a class="brand" href="{root}index.html">{WORD}</a>
<nav><a href="{root}index.html#top10">Today</a><a href="{root}index.html#frontier">Frontier</a>{labsnav}<a href="{root}index.html#sponsor">Sponsor</a><a href="{root}about.html">About</a><a href="{root}index.html#subscribe" class="cta">Subscribe</a></nav></header>"""

def foot(year, root=""):
    return f"""<footer><span>© {year} NextAiBreakout.com · {TAG}</span><span class="mono">GitHub · Hugging Face · npm · PyPI · Hacker News · <a href="{root}about.html">About</a> · <a href="{root}llms.txt">llms.txt</a></span></footer>"""

def row(i, n):
    return f"""<tr data-src="{i['source']}" data-tag="{i['tag']}"><td class="rk mono">{n:02d}</td>
<td class="it"><div class="badges"><span class="sb s-{i['source']}">{LABEL[i['source']]}</span><span class="tg"># {e(i['tag'])}</span></div>
<a class="title" href="{e(i['url'])}" rel="nofollow noopener" target="_blank">{e(i['name'])}</a>
<p class="what">{e(i.get('what') or i['why'])}</p></td>
<td class="tr">{spark(i.get('hist'))}</td>
<td class="mo mono"><b>{e(i['momentum'])}</b><span>{e(i.get('momentum_sub',''))}</span></td>
<td class="sc mono"><b>{i['score']:.0f}</b><i><u style="width:{i['score']:.0f}%"></u></i></td></tr>"""

def short(s, n=64):
    s = s.split(". ")[0].rstrip(".")
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"
def og(d, stamp_day):
    t = d["top"][0] if d["top"] else None
    if not t: return
    others = "&nbsp;&nbsp;&nbsp;&nbsp;".join(f"{k+2:02d} {e(x['name'].split('/')[-1] if x['source']!='hackernews' else x['name'][:30].rsplit(' ',1)[0]+'…')}" for k, x in enumerate(d["top"][1:3]))
    sp = spark(t.get("hist"), 1090, 110, "#3DDC84", True)
    big, sub = t["momentum"].split(" ", 1) if " " in t["momentum"] else (t["momentum"], "")
    page = f"""<html><head>{FONTS}<style>body{{margin:0;width:1200px;height:630px;background:radial-gradient(520px 360px at 88% 18%,rgba(61,220,132,.07),#0A0B0A 70%);color:#EDEDE8;font-family:'Space Grotesk',sans-serif;padding:56px 64px;box-sizing:border-box;position:relative}}
.mono{{font-family:'JetBrains Mono',monospace}}.grad{{color:#3DDC84}}
.logo{{width:38px;height:38px;vertical-align:middle;margin-right:12px}}</style></head><body>
<div style="display:flex;justify-content:space-between;font-size:28px;font-weight:700"><div>{WORD}</div><div class="mono" style="font-size:20px;color:#3DDC84">● {stamp_day}</div></div>
<div class="mono" style="color:#3DDC84;letter-spacing:4px;font-size:18px;margin-top:52px">#1 BREAKING OUT TODAY</div>
<div style="display:flex;justify-content:space-between;align-items:flex-end"><div style="max-width:780px"><div style="font-size:{'72' if len(t['name'])<24 else '52'}px;font-weight:700;line-height:1.05;margin-top:10px">{e(t['name'])}</div>
<div style="font-size:26px;color:#8A8F8B;margin-top:12px">{e(short(t.get('what') or ''))}</div></div>
<div style="text-align:right"><div style="font-size:64px;font-weight:700;color:#3DDC84">{e(big)}</div><div class="mono" style="color:#8A8F8B;font-size:18px">{e(sub)}</div></div></div>
<div style="position:absolute;left:64px;right:46px;top:380px">{sp}</div>
<div class="mono" style="position:absolute;left:64px;right:64px;bottom:44px;display:flex;justify-content:space-between;border-top:1px solid #1E2220;padding-top:22px;font-size:18px;color:#8A8F8B"><span>{others}</span><b style="color:#EDEDE8">nextaibreakout.com</b></div></body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f: f.write(page); p = f.name
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000",
                    "--window-size=1200,630", f"--screenshot={os.path.join(DIST, 'og.png')}", "file://" + p],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    os.unlink(p)

def main():
    d = json.load(open(os.path.join(DATA, "scored-seo2.json" if SEO2 else "scored.json")))
    t = dt.datetime.fromisoformat(d["generated"]); stamp = t.strftime("%b %d, %Y %H:%M UTC"); day = t.strftime("%Y-%m-%d")
    os.makedirs(DIST, exist_ok=True)
    top = d["top"]; one = top[0] if top else None
    ticker = "".join(f'<span><i>{k+1:02d}</i> {e(x["name"][:40])} <b>▲ {x["score"]:.0f}</b></span>' for k, x in enumerate(top))
    counts = {s: sum(1 for x in top if x["source"] == s) for s in LABEL}
    srctabs = f'<button class="on" data-f="src" data-v="all">All sources <i>{len(top)}</i></button>' + "".join(
        f'<button data-f="src" data-v="{s}">{LABEL[s]} <i>{counts[s]}</i></button>' for s in LABEL)
    tagtabs = '<button class="on" data-f="tag" data-v="all"># all</button>' + "".join(
        f'<button data-f="tag" data-v="{g}"># {g}</button>' for g in ("agents", "models", "dev tools", "safety"))
    hero_card = "" if not one else f"""<a class="hcard" href="{e(one['url'])}" rel="nofollow noopener" target="_blank">
<div class="hc-top mono"><span class="pink">#1 BREAKING NOW</span><span class="sb s-{one['source']}">{LABEL[one['source']]}</span></div>
<h3>{e(one['name'])}</h3><p>{e(one.get('what') or '')}</p>{spark(one.get('hist'), 360, 90, '#3DDC84', True)}
<div class="hc-stats mono"><div><b class="green">{e(one['momentum'])}</b><span>{e(one.get('momentum_sub',''))}</span></div><div><b class="pink">{one['score']:.0f}</b><span>breakout score</span></div></div></a>"""
    fr = "".join(f"""<a class="fcard" href="{e(i['url'])}" rel="nofollow noopener" target="_blank"><div class="mono fc-top"><span>{e(i['name'].split('/')[0])}</span><b class="pink">▲ {i['score']:.0f}</b></div>
<h3>{e(i['name'].split('/')[-1])}</h3><p>{e(i.get('desc') or 'Model')}</p><div class="mono dim">{e(i['momentum'])} · {e(i.get('momentum_sub',''))}</div></a>""" for i in d["frontier"][:3]) \
        or '<p class="dim">No new frontier-lab releases trending this hour.</p>'
    page = head(f"{BRAND}: what's breaking out in AI right now", DESC, "/") + f"""
<div class="ticker mono"><span class="live">● LIVE</span><div class="tk"><div class="tk-in">{ticker}{ticker}</div></div></div><main>
<section class="hero"><div><p class="stamp mono"><span class="dot"></span>Updated hourly · last run {stamp}</p>
<h1>What's breaking out<br>in AI <span class="grad">right now.</span></h1><p class="lede">{e(DESC)}</p>
<div class="btns"><a class="btn pri" href="#top10">See today's top 10 →</a><a class="btn" href="#subscribe">Get the daily email</a></div></div>{hero_card}</section>
<section class="stats mono"><div><b>{d['items_scanned']}</b><span>items scanned this run</span></div><div><b>{len(d['sources'])}</b><span>sources tracked</span></div>
<div><b>60 <small>min</small></b><span>refresh cycle</span></div><div><b class="green">{t.strftime('%H:%M')}</b><span>last run (UTC)</span></div></section>
<section id="sponsor" class="spon"><span class="tag-s mono">SPONSOR</span><div><b>Your product here — pinned for 7 days</b><p>One slot, seen by everyone tracking new AI. Sponsor this spot: email for rates.</p></div><a class="btn" href="about.html#sponsor">Book this slot</a></section>
<section id="top10"><p class="kick mono">TODAY · {t.strftime('%b %d').upper()}</p><div class="h2row"><h2>Top 10 breaking out</h2><span class="mono dim">Score = velocity vs. baseline, 0–99</span></div>
<div class="filters">{srctabs}</div><div class="filters small">{tagtabs}</div>
<div class="tbl"><table><thead><tr class="mono"><th>Rank</th><th>Item</th><th>48h trend</th><th>Momentum</th><th>Score</th></tr></thead><tbody>
{"".join(row(i, n+1) for n, i in enumerate(top))}</tbody></table><p class="empty dim" hidden>Nothing from this filter in today's top 10.</p></div></section>
<section id="frontier"><p class="kick mono">FRONTIER</p><h2>New from the major labs</h2><p class="dim">Releases from frontier labs trending on Hugging Face.</p><div class="fgrid">{fr}</div></section>
{labs_home(t) if LABS else ""}<section id="subscribe" class="signup"><div><h2>The daily breakout, in your inbox.</h2><p class="dim">Top 10 movers and the frontier releases. One email a day. No hype.</p></div>
<form onsubmit="return false"><label class="mono dim" for="em">Email address</label><div><input id="em" type="email" placeholder="you@company.com" disabled><button class="btn pri" type="button" disabled aria-disabled="true">Email launching soon</button></div></form></section></main>
{foot(t.year)}
<script>const st={{src:'all',tag:'all'}};document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{{b.parentNode.querySelectorAll('button').forEach(x=>x.classList.remove('on'));b.classList.add('on');st[b.dataset.f]=b.dataset.v;let n=0;document.querySelectorAll('tbody tr').forEach(r=>{{const ok=(st.src=='all'||r.dataset.src==st.src)&&(st.tag=='all'||r.dataset.tag==st.tag);r.hidden=!ok;n+=ok}});document.querySelector('.empty').hidden=n>0}})</script></body></html>"""
    open(os.path.join(DIST, "index.html"), "w").write(page)
    about = head(f"About | {BRAND}", "How NextAiBreakout ranks AI launches by growth rate.", "/about.html") + f"""<main class="prose">
<p class="kick mono">ABOUT</p><h1>{TAG}</h1><p>{BRAND} checks public sources every hour and ranks what is <strong>gaining momentum fastest</strong>, not what is already biggest.</p>
<h2>How the breakout score works</h2><ul><li><b>GitHub:</b> new AI repos (AI keywords required, 50+ stars), stars gained per hour once a repo has 3+ hourly snapshots; before that, shown as stars/day since launch (lifetime stars ÷ age). Repos older than ~60 days are down-ranked unless they show real recent velocity.</li>
<li><b>Hugging Face:</b> trending score and like growth for models and Spaces.</li><li><b>npm / PyPI:</b> yesterday's downloads vs. the 7-day average.</li>
<li><b>Hacker News:</b> AI stories, points per hour since posting (opinion pieces filtered where possible).</li></ul>
<p>Each source is ranked by velocity and relative growth, then everything is re-ranked into a 0–99 score. Trend lines use only real hourly snapshots; new items show a dashed line until there's history. Descriptions come from each project's own page.</p>
<h2 id="sponsor">Sponsor</h2><p>One pinned slot per week on the site and in the daily email: Sponsor this spot: email for rates.</p></main>""" + foot(t.year) + "</body></html>"
    open(os.path.join(DIST, "about.html"), "w").write(about)
    # real 404 page: Cloudflare Pages serves dist/404.html with HTTP 404 for unknown paths (absolute links so it works at any depth)
    nf = head(f"Page not found | {BRAND}", "This page doesn't exist on NextAiBreakout.", "/404.html", "/").replace('<link rel="canonical" href="https://nextaibreakout.com/404.html">', '<meta name="robots" content="noindex">') + """<main class="prose">
<p class="kick mono">404</p><h1>Page not found</h1><p class="dim">That page doesn't exist (or hasn't launched yet).</p>
<div class="btns"><a class="btn pri" href="/">See what's breaking out →</a><a class="btn" href="/about.html">About</a></div></main>""" + foot(t.year, "/") + "</body></html>"
    open(os.path.join(DIST, "404.html"), "w").write(nf)
    for f in os.listdir(os.path.join(ROOT, "static")):
        if f != "og.png": shutil.copy(os.path.join(ROOT, "static", f), DIST)
    if LABS: shutil.copy(os.path.join(ROOT, "labs.css"), DIST)
    og(d, t.strftime("%b %d, %Y").upper())
    if not os.path.exists(os.path.join(DIST, "og.png")): shutil.copy(os.path.join(ROOT, "static", "og.png"), DIST)
    open(os.path.join(DIST, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{day}</lastmod><changefreq>{c}</changefreq></url>" for p, c in (("/", "hourly"), ("/about.html", "monthly")) + (labs_pages(t) if LABS else ())) + "</urlset>\n")
    open(os.path.join(DIST, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    llms = [f"# {BRAND}", f"> {TAG} {DESC}", "", f"Updated hourly. Last refresh: {stamp}.", "", "## Top 10 breaking out today"]
    llms += [f"- [{i['name']}]({i['url']}) ({LABEL[i['source']]}, score {i['score']:.0f}): {i.get('what','')} {i['why']}" for i in top]
    llms += ["", "## Pages", f"- [Home]({SITE}/)", f"- [About and methodology]({SITE}/about.html)", f"- [Data JSON]({SITE}/data.json)"]
    open(os.path.join(DIST, "llms.txt"), "w").write("\n".join(llms) + "\n")
    json.dump({k: d[k] for k in ("generated", "top", "frontier")}, open(os.path.join(DIST, "data.json"), "w"))
    if SEO2:
        import seo2; seo2.apply(DIST, d, t)
    if os.getenv("GROKBOT") == "1":  # Grok Bot page: off by default so the cron deploy does not publish it
        import grokbot; grokbot.apply(DIST)
    if os.getenv("KIT") == "1":  # Kit email signup: off by default so production/cron builds do not include it (preview only)
        import kit; kit.apply(DIST)
    print("built", DIST)

# ---------------- Frontier Labs ----------------
from zoneinfo import ZoneInfo
MT = ZoneInfo("America/Edmonton")
def _labs():
    cfg = json.load(open(os.path.join(ROOT, "labs_sources.json")))["labs"]
    p = os.path.join(DATA, "labs.json"); d = json.load(open(p)) if os.path.exists(p) else {"generated": None, "labs": {}}
    return cfg, d
def mt(iso, fmt="%b %d, %Y %H:%M"):
    return dt.datetime.fromisoformat(iso).astimezone(MT).strftime(fmt) + " MT" if iso else "never"
def ddate(iso, day=None):
    if day: return dt.date.fromisoformat(day).strftime("%b %d, %Y").replace(" 0", " ")  # the source's own calendar day
    return dt.datetime.fromisoformat(iso).astimezone(MT).strftime("%b %d, %Y").replace(" 0", " ") if iso else "Date not given"
def lab_list(items, n):
    if not items: return '<p class="dim lab-empty">No releases fetched yet.</p>'
    return '<ol class="lab-items">' + "".join(f"""<li><time class="mono dim" datetime="{e(i.get('day') or i['date'] or '')}">{ddate(i['date'], i.get('day'))}</time>
<a href="{e(i['url'])}" rel="noopener" target="_blank">{e(i['title'])}</a><span class="mono dim lab-src">{e(i['source'])}</span></li>""" for i in items[:n]) + "</ol>"
def lab_card(lab, L, root):
    items = L.get("items", [])
    return f"""<a class="fcard lab-card" href="{root}labs/{lab['slug']}/"><div class="mono fc-top"><span>{e(lab['name'])}</span><b class="pink">{len(items)} item{'' if len(items) == 1 else 's'}</b></div>
<h3>{e(lab['name'])}</h3><p>{e(lab['blurb'])}</p><div class="mono dim">{e(items[0]['title'][:70] + ' · ' + ddate(items[0]['date'], items[0].get('day'))) if items else 'No releases fetched yet'}</div></a>"""
def labs_home(t):
    cfg, d = _labs()
    cards = "".join(lab_card(l, d["labs"].get(l["slug"], {}), "") for l in cfg)
    return f"""<section id="labs"><p class="kick mono">FRONTIER LABS</p><div class="h2row"><h2>Latest from the frontier labs</h2><span class="mono dim">Updated {mt(d['generated'])}</span></div>
<p class="dim">Official release feeds from xAI, Tesla AI, OpenAI, Anthropic, Google DeepMind and Meta. <a class="green" href="labs/">All labs →</a></p><div class="fgrid lab-grid">{cards}</div></section>"""
def ld(obj): return '<script type="application/ld+json">' + json.dumps(obj).replace("</", "<\\/") + "</script>"
def labs_pages(t):
    cfg, d = _labs(); upd = mt(d["generated"]); os.makedirs(os.path.join(DIST, "labs"), exist_ok=True)
    crumbs = lambda extra: {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Frontier Labs", "item": SITE + "/labs/"}] + extra}
    # index
    path = "/labs/"; title = f"Frontier AI Labs: latest releases from xAI, OpenAI, Anthropic, DeepMind, Meta and Tesla AI | {BRAND}"
    desc = "Latest official releases from xAI (Grok), Tesla AI, OpenAI, Anthropic, Google DeepMind and Meta, with dates and source links. Refreshed hourly."
    j = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": "Frontier Labs", "url": SITE + path, "description": desc,
         "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": l["name"], "url": f"{SITE}/labs/{l['slug']}/"} for k, l in enumerate(cfg)]}}, crumbs([])]}
    page = head(title, desc, path, "/", ld(j)) + f"""<main><section class="labs-hero"><p class="kick mono">FRONTIER LABS</p><h1>Latest releases from the frontier AI labs</h1>
<p class="stamp mono"><span class="dot"></span>Updated {upd}</p><p class="dim">{e(desc)}</p></section>
<div class="fgrid lab-grid">{"".join(lab_card(l, d["labs"].get(l["slug"], {}), "/") for l in cfg)}</div></main>""" + foot(t.year, "/") + "</body></html>"
    open(os.path.join(DIST, "labs", "index.html"), "w").write(page)
    urls = [(path, "hourly")]
    for l in cfg:
        L = d["labs"].get(l["slug"], {}); items = L.get("items", []); path = f"/labs/{l['slug']}/"
        j = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": l["title"].split(" | ")[0], "url": SITE + path, "description": l["description"],
             "about": {"@type": "Organization", "name": l["name"]},
             "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": i["title"], "url": i["url"]} for k, i in enumerate(items)]}},
             crumbs([{"@type": "ListItem", "position": 3, "name": l["name"], "item": SITE + path}])]}
        srcs = "".join(f"""<li><a href="{e(s['url'])}" rel="noopener" target="_blank">{e(s['name'])}</a> <span class="mono dim">· {e(s['status'])}{' · live' if s.get('ok') else (' · not polled' if s['status'] == 'disabled' else ' · fetch failed this run')}</span></li>""" for s in L.get("sources", []))
        page = head(l["title"], l["description"], path, "/", ld(j)) + f"""<main><section class="labs-hero"><p class="kick mono"><a href="/labs/">FRONTIER LABS</a> / {e(l['name'].upper())}</p>
<h1>{e(l['title'].split(' | ')[0])}</h1><p class="stamp mono"><span class="dot"></span>Updated {upd}</p><p class="dim">{e(l['description'])}</p></section>
<section class="lab-panel">{lab_list(items, 10)}</section><section class="lab-sources"><h2>Sources</h2><ul>{srcs}</ul>
<p class="dim">Only official, free sources. Nothing is added by hand or invented; if a source isn't connected yet, this page says so.</p></section></main>""" + foot(t.year, "/") + "</body></html>"
        os.makedirs(os.path.join(DIST, "labs", l["slug"]), exist_ok=True)
        open(os.path.join(DIST, "labs", l["slug"], "index.html"), "w").write(page)
        urls.append((path, "hourly"))
    return tuple(urls)
if __name__ == "__main__": main()
