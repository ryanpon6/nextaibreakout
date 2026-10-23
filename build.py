"""Render static site + per-run OG image to dist/."""
import datetime as dt, hashlib, html, json, os, shutil, subprocess, tempfile
from common import DATA, DIST, ROOT
DIST = os.getenv("NAB_DIST") or DIST
LABS = os.getenv("LABS") == "1"
SEO2 = os.getenv("SEO2") == "1"  # SEO fixes + archive/item pages: off by default so the hourly cron does not publish them yet
import re as _re
def re_strip(s): return _re.sub(r"\s+", " ", html.unescape(_re.sub(r"<[^>]+>", "", s))).strip()  # Frontier Labs pages: off by default so the hourly cron deploy does not publish them yet
SITE = "https://nextaibreakout.com"; BRAND = "NextAiBreakout"; TAG = "Tracking the road to superintelligence."
DESC = "AI repos, models and packages ranked hourly by velocity, not hype. Tracked across GitHub, Hugging Face, npm, PyPI and Hacker News."
X_URL = "https://x.com/ryanpon"; X_HANDLE = "@ryanpon"
H1_TEXT = "Trending AI, caught the hour it breaks out."
H1_HTML = 'Trending <span class="accent">AI</span>, caught the hour it breaks out.'
e = html.escape
LABEL = {"github": "GitHub", "huggingface": "Hugging Face", "npm": "npm", "pypi": "PyPI", "hackernews": "Hacker News"}
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=swap" rel="stylesheet">'
GOLD = "#F2C14E"
# Cache-busting: stylesheet/font URLs carry a hash of their contents, so a visitor's browser never pairs new pages with an old cached stylesheet.
VER = hashlib.sha1(b"".join(open(os.path.join(ROOT, f), "rb").read() for f in ("static/style.css", "fonts/fonts.css"))).hexdigest()[:10]
# Mark: a frame with a line breaking out through its top-right corner
LOGO = ('<svg class="logo" viewBox="0 0 32 32" width="32" height="32" aria-hidden="true"><path d="M17 5H5v22h22V15" fill="none" stroke="currentColor" stroke-width="2.6"/>'
        '<path class="logo-break" d="M10.5 21.5L27 5M19 5h8v8" fill="none" stroke="#F2C14E" stroke-width="2.6" stroke-linecap="square"/></svg>')
WORD = f'{LOGO}<span>NextAiBreakout</span>'
XICON = '<svg class="xi" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M17.8 2.5h3.1l-6.8 7.8 8 10.6h-6.3l-4.9-6.4-5.6 6.4H2.2l7.3-8.3L1.9 2.5h6.4l4.4 5.9 5.1-5.9zm-1.1 16.6h1.7L7.4 4.3H5.6l11.1 14.8z"/></svg>'
SUN = '<svg class="i-sun" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>'
MOON = '<svg class="i-moon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>'
# Theme: follows the device (prefers-color-scheme) until the visitor picks one with the header button; the choice is kept in localStorage.
THEME_JS = ("<script>(function(){var d=document.documentElement;try{var t=localStorage.getItem('nab-theme');if(t==='dark'||t==='light')d.setAttribute('data-theme',t)}catch(_){}"
            "document.addEventListener('click',function(ev){var b=ev.target.closest&&ev.target.closest('[data-theme-toggle]');if(!b)return;"
            "var c=d.getAttribute('data-theme')||(window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'),n=c==='dark'?'light':'dark';"
            "d.setAttribute('data-theme',n);try{localStorage.setItem('nab-theme',n)}catch(_){}})})();</script>")

def fit(s, n):
    """Trim to n characters on a word boundary (titles/descriptions that Google would otherwise cut off)."""
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n - 1].rsplit(' ', 1)[0].rstrip(' ,:;-') + '…'
def seo_title(core, n=60):
    """'core | NextAiBreakout' when it fits in n characters, else just the core (trimmed)."""
    t = f'{core} | {BRAND}'
    return t if len(t) <= n else fit(core, n)

def fmt(n):
    n = float(n); return f"{n/1e6:.1f}M" if abs(n) >= 1e6 else f"{n/1e3:.1f}K" if abs(n) >= 1e3 else f"{n:.0f}"

def spark(hist, w=120, h=32, color=GOLD, fill=False):
    """Sparkline from REAL snapshot history only. <3 points -> flat dashed line labelled as collecting.
    The stroke attribute is the fallback colour (OG image); on the site the stylesheet colours it per theme."""
    if not hist or len(hist) < 3 or max(hist) == min(hist):
        return (f'<svg class="spark empty" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><title>Collecting history (needs 3+ hourly snapshots)</title>'
                f'<line x1="2" y1="{h/2}" x2="{w-2}" y2="{h/2}" stroke="#596175" stroke-width="1.5" stroke-dasharray="3 4"/></svg>')
    lo, hi = min(hist), max(hist); n = len(hist)
    pts = [(2 + (w - 4) * k / (n - 1), h - 3 - (h - 6) * (v - lo) / (hi - lo)) for k, v in enumerate(hist)]
    p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f'<polygon class="sa" points="2,{h} {p} {w-2},{h}" fill="{color}" opacity=".12"/>' if fill else ""
    return (f'<svg class="spark" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><title>{n} hourly snapshots</title>{area}'
            f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round"/>'
            f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="2.5" fill="{color}"/></svg>')

def trend(hist):
    """Table cell trend: a real sparkline, or a plain note while an item has fewer than 3 hourly snapshots."""
    if not hist or len(hist) < 3 or max(hist) == min(hist):
        return '<span class="na">New. Trend line starts after 3 hourly checks</span>'
    return spark(hist)

def head(title, desc, path, root="", extra=""):
    labscss = ""  # lab styles now live in style.css
    labsnav = f'<a href="{root or "/"}labs/">Labs</a>' if LABS else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}"><meta property="og:image" content="{SITE}/og-default.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{SITE}/og-default.png"><meta name="twitter:site" content="{X_HANDLE}"><meta name="twitter:creator" content="{X_HANDLE}">
<meta name="color-scheme" content="light dark"><meta name="theme-color" content="#EDEFF4" media="(prefers-color-scheme: light)"><meta name="theme-color" content="#05070D" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.svg">{FONTS}<link rel="stylesheet" href="/style.css?v={VER}">{labscss}{extra}{THEME_JS}</head><body>
<header class="top"><a class="brand" href="{root}index.html" aria-label="{BRAND} home">{WORD}</a>
<nav><a href="{root}index.html#top10">Today</a>{labsnav}<a href="{root}index.html#sponsor">Sponsor</a><a href="{root}about.html">About</a></nav>
<div class="acts"><button class="ib" type="button" data-theme-toggle aria-label="Switch light or dark theme">{SUN}{MOON}</button><a class="ghost xf" href="{X_URL}" rel="me noopener" target="_blank">{XICON}Follow</a><a href="{root}index.html#subscribe" class="cta">Subscribe</a></div></header>"""

def foot(year, root=""):
    return f"""<footer><div class="fbase"><span>© {year} NextAiBreakout.com. {TAG}</span><span class="fmeta"><a href="{root}about.html">About</a><a href="{root}llms.txt">llms.txt</a><a href="{X_URL}" rel="me noopener" target="_blank">X {X_HANDLE}</a></span></div></footer>"""

def row(i, n):
    return f"""<tr data-src="{i['source']}" data-tag="{i['tag']}"><td class="rk">{n}</td>
<td class="it"><div class="badges"><span class="sb s-{i['source']}">{LABEL[i['source']]}</span><span class="tg">#{e(i['tag'])}</span></div>
<a class="title" href="{e(i['url'])}" rel="nofollow noopener" target="_blank">{e(i['name'])}</a>
<p class="what">{e(i.get('what') or i['why'])}</p></td>
<td class="tr">{trend(i.get('hist'))}</td>
<td class="mo"><b>{e(i['momentum'])}</b><span>{e(i.get('momentum_sub',''))}</span></td>
<td class="sc"><b>{i['score']:.0f}</b><i><u style="width:{i['score']:.0f}%"></u></i></td></tr>"""

def chart(top):
    """Hero chart: the highest-ranked GitHub / Hugging Face item with at least 6 real hourly snapshots. Nothing is interpolated."""
    c = next((i for i in top if i["source"] in ("github", "huggingface") and len(i.get("hist") or []) >= 6 and len(set(i["hist"])) >= 4), None)
    if not c: return ""
    h = c["hist"]; lo, hi = min(h), max(h); n = len(h); unit = c.get("metric_name") or ""
    pts = " ".join(f"{6 + 1188 * k / (n - 1):.1f},{294 - 288 * (v - lo) / (hi - lo):.1f}" for k, v in enumerate(h))
    end = pts.split(" ")[-1].split(",")
    delta = h[-1] - h[0]
    return f"""<div class="hc"><div class="hc-label"><a class="hc-link" href="{e(c['url'])}" rel="nofollow noopener" target="_blank">{e(c['name'])}</a>
<p><b>{'+' if delta >= 0 else ''}{fmt(delta)}</b> {e(unit)} over the last {n - 1} hourly checks</p></div>
<div class="hc-chart" aria-hidden="true"><svg viewBox="0 0 1200 300" preserveAspectRatio="none"><defs>
<linearGradient id="hcg" x1="0" x2="1"><stop offset="0" class="g0"/><stop offset=".55" class="g1"/><stop offset="1" class="g2"/></linearGradient>
<linearGradient id="hcf" x1="0" x2="0" y1="0" y2="1"><stop offset="0" class="f0"/><stop offset="1" class="f1"/></linearGradient>
<filter id="hcb" x="-5%" y="-30%" width="110%" height="160%"><feGaussianBlur stdDeviation="6"/></filter></defs>
<polygon class="hc-area" points="6,300 {pts} 1194,300"/><polyline class="hc-glow" points="{pts}"/><polyline class="hc-line" vector-effect="non-scaling-stroke" points="{pts}"/>
<g class="hc-tip"><circle class="r" cx="{end[0]}" cy="{end[1]}" r="14"/><circle class="c" cx="{end[0]}" cy="{end[1]}" r="6"/></g></svg></div>
<div class="hc-axis"><span>{fmt(h[0])} {e(unit)}, {n - 1} checks ago</span><span>{fmt(h[-1])} {e(unit)} now</span></div></div>"""

def short(s, n=64):
    s = s.split(". ")[0].rstrip(".")
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"
def og(d, stamp_day):
    t = d["top"][0] if d["top"] else None
    if not t: return
    others = "&nbsp;&nbsp;&nbsp;&nbsp;".join(f"{k+2}. {e(x['name'].split('/')[-1] if x['source']!='hackernews' else x['name'][:30].rsplit(' ',1)[0]+'…')}" for k, x in enumerate(d["top"][1:3]))
    sp = spark(t.get("hist"), 1090, 110, GOLD, True)
    big, sub = t["momentum"].split(" ", 1) if " " in t["momentum"] else (t["momentum"], "")
    page = f"""<html><head>{FONTS}<style>html{{background:#05070D}}body{{margin:0;width:1200px;height:630px;background:radial-gradient(560px 380px at 86% 88%,rgba(242,193,78,.16),transparent 70%),#05070D;color:#F2F4F9;font-family:'Archivo',sans-serif;padding:56px 64px;box-sizing:border-box;position:relative}}
.logo{{width:40px;height:40px;vertical-align:middle;margin-right:14px;color:#F2F4F9}}.w{{font-stretch:125%;font-weight:800}}</style></head><body>
<div style="display:flex;justify-content:space-between;align-items:center;font-size:28px"><div class="w">{WORD}</div><div style="font-size:20px;color:#F2C14E">● {stamp_day}</div></div>
<div style="color:#F2C14E;font-size:22px;font-weight:600;margin-top:52px">Breaking out fastest right now</div>
<div style="display:flex;justify-content:space-between;align-items:flex-end"><div style="max-width:780px"><div style="font-size:{'70' if len(t['name'])<24 else '50'}px;font-weight:800;font-stretch:112%;line-height:1.02;letter-spacing:-.02em;margin-top:10px">{e(t['name'])}</div>
<div style="font-size:26px;color:#C2C8D6;margin-top:12px">{e(short(t.get('what') or ''))}</div></div>
<div style="text-align:right"><div style="font-size:64px;font-weight:800;font-stretch:112%;color:#F2C14E">{e(big)}</div><div style="color:#8C94A8;font-size:18px">{e(sub)}</div></div></div>
<div style="position:absolute;left:64px;right:46px;top:380px">{sp}</div>
<div style="position:absolute;left:64px;right:64px;bottom:44px;display:flex;justify-content:space-between;border-top:1px solid rgba(255,255,255,.12);padding-top:22px;font-size:18px;color:#8C94A8"><span>{others}</span><b style="color:#F2F4F9">nextaibreakout.com</b></div></body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f: f.write(page); p = f.name
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=4000",
                    "--window-size=1200,630", f"--screenshot={os.path.join(DIST, 'og.png')}", "file://" + p],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    os.unlink(p)

def main():
    d = json.load(open(os.path.join(DATA, "scored-seo2.json" if SEO2 else "scored.json")))
    t = dt.datetime.fromisoformat(d["generated"]); stamp = t.strftime("%b %d, %Y %H:%M UTC"); day = t.strftime("%Y-%m-%d")
    os.makedirs(DIST, exist_ok=True)
    top = d["top"]
    counts = {s: sum(1 for x in top if x["source"] == s) for s in LABEL}
    srctabs = f'<button class="on" data-f="src" data-v="all">All sources <i>{len(top)}</i></button>' + "".join(
        f'<button data-f="src" data-v="{s}">{LABEL[s]} <i>{counts[s]}</i></button>' for s in LABEL if counts[s])
    tagtabs = '<button class="on" data-f="tag" data-v="all">#all</button>' + "".join(
        f'<button data-f="tag" data-v="{g}">#{g}</button>' for g in ("agents", "models", "dev tools", "safety"))
    page = head(f"{BRAND}: what's breaking out in AI right now", DESC, "/") + f"""<main>
<section class="hero" id="top"><div class="hcopy"><p class="live"><span class="dot" aria-hidden="true"></span>Live. Last run {stamp}, {d['items_scanned']} items checked across {len(d['sources'])} sources</p>
<h1>{H1_HTML}</h1><p class="lede">{e(DESC)}</p>
<!--kit-hero--><div class="btns"><a class="btn pri" href="#top10">See today's top 10</a><a class="btn" href="#subscribe">Get the daily email</a></div><!--/kit-hero--></div>
{chart(top)}</section>
<section id="top10" class="board"><div class="sh"><h2>Breaking out right now</h2><p class="dim">Each score compares an item's growth this hour with its own baseline, from 0 to 99. Refreshed every hour.</p></div>
<div class="filters" role="group" aria-label="Filter by source">{srctabs}</div><div class="filters small" role="group" aria-label="Filter by topic">{tagtabs}</div>
<div class="tbl"><table><thead><tr><th>Rank</th><th>Item</th><th>48h trend</th><th>Momentum</th><th>Score</th></tr></thead><tbody>
{"".join(row(i, n+1) for n, i in enumerate(top))}</tbody></table><p class="empty dim" hidden>Nothing from this filter in today's top 10.</p></div></section>
<section id="sponsor" class="spon"><span class="tag-s">Sponsor</span><div><b>Your product here, pinned for 7 days</b><p>One slot, seen by everyone tracking new AI. Sponsor this spot: email for rates.</p></div><a class="btn" href="about.html#sponsor">Book this slot</a></section>
{labs_home(t) if LABS else ""}<section id="subscribe" class="signup"><div><h2>Don't miss the next breakout.</h2><p class="dim">The top 10 movers and the frontier releases, in one email a day.</p></div>
<form onsubmit="return false"><label for="em">Email address</label><div><input id="em" type="email" placeholder="you@company.com" disabled><button class="btn pri" type="button" disabled aria-disabled="true">Email launching soon</button></div></form></section>
<section class="follow"><p>New breakouts post live on X, three times a day.</p><a class="ghost" href="{X_URL}" rel="me noopener" target="_blank">{XICON}Follow {X_HANDLE}</a></section></main>
{foot(t.year)}
<script>const st={{src:'all',tag:'all'}};document.querySelectorAll('.filters button').forEach(b=>b.onclick=()=>{{b.parentNode.querySelectorAll('button').forEach(x=>{{x.classList.remove('on');x.setAttribute('aria-pressed','false')}});b.classList.add('on');b.setAttribute('aria-pressed','true');st[b.dataset.f]=b.dataset.v;let n=0;document.querySelectorAll('tbody tr').forEach(r=>{{const ok=(st.src=='all'||r.dataset.src==st.src)&&(st.tag=='all'||r.dataset.tag==st.tag);r.hidden=!ok;n+=ok}});document.querySelector('.empty').hidden=n>0}})</script></body></html>"""
    open(os.path.join(DIST, "index.html"), "w").write(page)
    about = head(seo_title("How we rank trending AI repos & models"), "How NextAiBreakout finds trending AI repos, models and packages every hour: the sources, the 0–99 breakout score, and how to sponsor.", "/about.html") + f"""<main class="prose">
<h1>{TAG}</h1><p>{BRAND} checks public sources every hour and ranks what is <strong>gaining momentum fastest</strong>, not what is already biggest.</p>
<h2>How the breakout score works</h2><ul><li><b>GitHub:</b> new AI repos (AI keywords required, 50+ stars), stars gained per hour once a repo has 3+ hourly snapshots; before that, shown as stars/day since launch (lifetime stars ÷ age). Repos older than ~60 days are down-ranked unless they show real recent velocity.</li>
<li><b>Hugging Face:</b> trending score and like growth for models and Spaces.</li><li><b>npm / PyPI:</b> yesterday's downloads vs. the 7-day average.</li>
<li><b>Hacker News:</b> AI stories, points per hour since posting (opinion pieces filtered where possible).</li></ul>
<p>Each source is ranked by velocity and relative growth, then everything is re-ranked into a 0–99 score. Trend lines use only real hourly snapshots; new items show a dashed line until there's history. Descriptions come from each project's own page.</p>
<h2 id="sponsor">Sponsor</h2><p>One pinned slot per week on the site and in the daily email: Sponsor this spot: email for rates.</p>
<h2>Follow along</h2><p class="follow-p">New breakouts also post live on X, three times a day: <a href="{X_URL}" rel="me noopener" target="_blank">{X_HANDLE}</a>.</p></main>""" + foot(t.year) + "</body></html>"
    open(os.path.join(DIST, "about.html"), "w").write(about)
    # real 404 page: Cloudflare Pages serves dist/404.html with HTTP 404 for unknown paths (absolute links so it works at any depth)
    nf = head(f"Page not found | {BRAND}", "This page doesn't exist on NextAiBreakout.", "/404.html", "/").replace('<link rel="canonical" href="https://nextaibreakout.com/404.html">', '<meta name="robots" content="noindex">') + """<main class="prose">
<h1>Page not found</h1><p class="dim">That page doesn't exist, or hasn't launched yet.</p>
<div class="btns"><a class="btn pri" href="/">See what's breaking out</a><a class="btn" href="/about.html">About</a></div></main>""" + foot(t.year, "/") + "</body></html>"
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
    import blog; blog.apply(DIST, t)  # blog: always on (posts only render with status: published)
    if os.getenv("KIT") == "1":  # Kit email signup: off by default so production/cron builds do not include it (preview only); after blog so posts get the box
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
    return '<ol class="lab-items">' + "".join(f"""<li><time class="dim" datetime="{e(i.get('day') or i['date'] or '')}">{ddate(i['date'], i.get('day'))}</time>
<a href="{e(i['url'])}" rel="noopener" target="_blank">{e(i['title'])}</a><span class="dim lab-src">{e(i['source'])}</span></li>""" for i in items[:n]) + "</ol>"
def lab_card(lab, L, root):
    items = L.get("items", [])
    latest = "".join(f'<li><time>{ddate(i["date"], i.get("day"))}</time><span>{e(i["title"][:90])}</span></li>' for i in items[:2]) or '<li><span class="dim">No releases fetched yet</span></li>'
    return f"""<a class="lab-card" href="{root}labs/{lab['slug']}/"><div class="lc-top"><h3>{e(lab['name'])}</h3><span class="lc-n">{len(items)} release{'' if len(items) == 1 else 's'}</span></div>
<p>{e(lab['blurb'])}</p><ul class="lc-items">{latest}</ul></a>"""
def labs_home(t):
    cfg, d = _labs()
    cards = "".join(lab_card(l, d["labs"].get(l["slug"], {}), "/") for l in cfg)
    return f"""<section id="labs" class="labs-home"><div class="sh"><h2>From the frontier labs</h2><p class="dim">Official release feeds from xAI, Tesla AI, OpenAI, Anthropic, Google DeepMind and Meta. Updated {mt(d['generated'])}. <a href="/labs/">All labs</a></p></div>
<div class="lab-strip">{cards}</div></section>"""
def ld(obj): return '<script type="application/ld+json">' + json.dumps(obj).replace("</", "<\\/") + "</script>"
def labs_pages(t):
    cfg, d = _labs(); upd = mt(d["generated"]); os.makedirs(os.path.join(DIST, "labs"), exist_ok=True)
    crumbs = lambda extra: {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Frontier Labs", "item": SITE + "/labs/"}] + extra}
    # index
    path = "/labs/"; title = "Latest AI lab releases: OpenAI, Anthropic, xAI, DeepMind"
    desc = "Latest official releases from xAI (Grok), Tesla AI, OpenAI, Anthropic, Google DeepMind and Meta, with dates and source links. Refreshed hourly."
    j = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": "Frontier Labs", "url": SITE + path, "description": desc,
         "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": l["name"], "url": f"{SITE}/labs/{l['slug']}/"} for k, l in enumerate(cfg)]}}, crumbs([])]}
    page = head(title, desc, path, "/", ld(j)) + f"""<main><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">Frontier Labs</span></nav>
<section class="labs-hero"><h1>Latest releases from the <span class="accent">frontier AI labs</span></h1>
<p class="stamp"><span class="dot"></span>Updated {upd}</p><p class="dim">{e(desc)}</p></section>
<div class="lab-strip lab-grid">{"".join(lab_card(l, d["labs"].get(l["slug"], {}), "/") for l in cfg)}</div></main>""" + foot(t.year, "/") + "</body></html>"
    open(os.path.join(DIST, "labs", "index.html"), "w").write(page)
    urls = [(path, "hourly")]
    for l in cfg:
        L = d["labs"].get(l["slug"], {}); items = L.get("items", []); path = f"/labs/{l['slug']}/"
        j = {"@context": "https://schema.org", "@graph": [{"@type": "CollectionPage", "name": l["title"].split(" | ")[0], "url": SITE + path, "description": l["description"],
             "about": {"@type": "Organization", "name": l["name"]},
             "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": i["title"], "url": i["url"]} for k, i in enumerate(items)]}},
             crumbs([{"@type": "ListItem", "position": 3, "name": l["name"], "item": SITE + path}])]}
        srcs = "".join(f"""<li><a href="{e(s['url'])}" rel="noopener" target="_blank">{e(s['name'])}</a> <span class="dim">· {e(s['status'])}{' · live' if s.get('ok') else (' · not polled' if s['status'] == 'disabled' else ' · fetch failed this run')}</span></li>""" for s in L.get("sources", []))
        page = head(l["title"], fit(l["description"], 155), path, "/", ld(j)) + f"""<main><nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/labs/">Frontier Labs</a> / <span aria-current="page">{e(l['name'])}</span></nav>
<section class="labs-hero"><h1>{e(l['title'].split(' | ')[0])}</h1><p class="stamp"><span class="dot"></span>Updated {upd}</p><p class="dim">{e(l['description'])}</p></section>
<section class="lab-panel">{lab_list(items, 10)}</section><section class="lab-sources"><h2>Sources</h2><ul>{srcs}</ul>
<p class="dim">Only official, free sources. Nothing is added by hand or invented; if a source isn't connected yet, this page says so.</p></section></main>""" + foot(t.year, "/") + "</body></html>"
        os.makedirs(os.path.join(DIST, "labs", l["slug"]), exist_ok=True)
        open(os.path.join(DIST, "labs", l["slug"], "index.html"), "w").write(page)
        urls.append((path, "hourly"))
    return tuple(urls)
if __name__ == "__main__": main()
