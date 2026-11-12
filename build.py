"""Render static site + per-run OG image to dist/."""
import datetime as dt, hashlib, html, json, os, shutil, subprocess, tempfile
from common import DATA, DIST, ROOT
DIST = os.getenv("NAB_DIST") or DIST
LABS = os.getenv("LABS") == "1"
SEO2 = os.getenv("SEO2") == "1"  # SEO fixes + archive/item pages: off by default so the hourly cron does not publish them yet
import re as _re
def re_strip(s): return _re.sub(r"\s+", " ", html.unescape(_re.sub(r"<[^>]+>", "", s))).strip()  # Frontier Labs pages: off by default so the hourly cron deploy does not publish them yet
SITE = "https://nextaibreakout.com"; BRAND = "NextAiBreakout"; TAG = "Grok Bot tips, with the real build behind each one."
DESC = "Grok Bot tips with the real build behind each one: the problem, how I did it, and what happened. Plus a separate page for Claude."
X_URL = "https://x.com/ryanpon"; X_HANDLE = "@ryanpon"
H1_TEXT = "Grok Bot tips, with the real build behind each one."
H1_HTML = 'Grok Bot tips, with the real build behind each one.'
e = html.escape
LABEL = {"github": "GitHub", "huggingface": "Hugging Face", "npm": "npm", "pypi": "PyPI", "hackernews": "Hacker News"}
GOLD = "#B8A188"
# Cache-busting: stylesheet/font URLs carry a hash of their contents, so a visitor's browser never pairs new pages with an old cached stylesheet.
VER = hashlib.sha1(b"".join(open(os.path.join(ROOT, f), "rb").read() for f in ("static/style.css", "fonts/fonts.css"))).hexdigest()[:10]
FONTS = ('<link rel="preload" href="/fonts/Archivo-var.woff2" as="font" type="font/woff2" crossorigin>'
         f'<link rel="stylesheet" href="/fonts/fonts.css?v={VER}">')
# Mark: a frame with a line breaking out through its top-right corner
LOGO = ('<svg class="logo" viewBox="0 0 32 32" width="32" height="32" aria-hidden="true"><path d="M17 5H5v22h22V15" fill="none" stroke="currentColor" stroke-width="2.6"/>'
        '<path class="logo-break" d="M10.5 21.5L27 5M19 5h8v8" fill="none" stroke="#B8A188" stroke-width="2.6" stroke-linecap="square"/></svg>')
WORD = f'{LOGO}<span>NextAiBreakout</span>'
XICON = '<svg class="xi" viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M17.8 2.5h3.1l-6.8 7.8 8 10.6h-6.3l-4.9-6.4-5.6 6.4H2.2l7.3-8.3L1.9 2.5h6.4l4.4 5.9 5.1-5.9zm-1.1 16.6h1.7L7.4 4.3H5.6l11.1 14.8z"/></svg>'
MENU = '<svg class="i-menu" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
CLOSE = '<svg class="i-close" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>'
MENU_JS = ("<script>(function(){function q(){return document.querySelector('.nav-toggle')}"
           "function set(open){var b=q();if(!b)return;b.setAttribute('aria-expanded',open?'true':'false');b.setAttribute('aria-label',open?'Close menu':'Open menu')}"
           "document.addEventListener('click',function(ev){var b=q();if(!b)return;"
           "if(ev.target.closest&&ev.target.closest('.nav-toggle')){set(b.getAttribute('aria-expanded')!=='true');ev.stopPropagation();return}"
           "if(b.getAttribute('aria-expanded')==='true'&&!(ev.target.closest&&ev.target.closest('#site-nav')))set(false)});"
           "document.addEventListener('keydown',function(ev){if(ev.key!=='Escape')return;var b=q();if(b&&b.getAttribute('aria-expanded')==='true'){set(false);b.focus()}})})();</script>")

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
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}"><link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}"><meta property="og:image" content="{SITE}/og-default.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{SITE}/og-default.png"><meta name="twitter:site" content="{X_HANDLE}"><meta name="twitter:creator" content="{X_HANDLE}">
<meta name="color-scheme" content="dark"><meta name="theme-color" content="#274043">
<link rel="icon" href="/favicon.svg">{FONTS}<link rel="stylesheet" href="/style.css?v={VER}">{labscss}{extra}{MENU_JS}</head><body>
<header class="top"><a class="brand" href="/" aria-label="{BRAND} home">{WORD}</a>
<nav id="site-nav" aria-label="Primary"><a href="/tips/">Tips</a><a href="/claude/">Claude</a><a href="/blog/">Blog</a><a href="/about">About</a></nav>
<div class="acts"><button class="ib nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">{MENU}{CLOSE}</button><a class="ghost xf" href="{X_URL}" rel="me noopener" target="_blank">{XICON}Follow</a></div></header>"""

def foot(year, root=""):
    return f"""<footer><div class="fbase"><span>© {year} NextAiBreakout.com. {TAG}</span><span class="fmeta"><a href="/tips/">Tips</a><a href="/claude/">Claude</a><a href="/blog/">Blog</a><a href="/about">About</a><a href="/feed.xml">RSS</a><a href="{root}llms.txt">llms.txt</a><a href="{X_URL}" rel="me noopener" target="_blank">X {X_HANDLE}</a></span></div>
<p class="fnote">Tips are reviewed before they go up. Unreviewed bot output does not publish.</p></footer>"""

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
def og_brand():
    """Teal and champagne-gold default OG image. No ranking product, no invented stats."""
    font = os.path.join(ROOT, "fonts", "Archivo-var.woff2")
    page = f"""<!doctype html><html><head><style>
@font-face{{font-family:Archivo;src:url('file://{font}') format('woff2');font-weight:100 900;font-stretch:62% 125%;}}
html,body{{margin:0;padding:0}}
body{{width:1200px;height:630px;background:#274043;color:#F5F1E8;font-family:Archivo,Helvetica Neue,Arial,sans-serif;padding:56px 64px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between}}
.top{{display:flex;align-items:center;gap:14px;font-stretch:125%;font-weight:800;font-size:28px;color:#B8A188}}
.logo{{width:40px;height:40px;color:#B8A188}}
.k{{font-size:20px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#BCA68E;margin:0 0 16px}}
h1{{font-size:72px;line-height:1.02;font-weight:800;font-stretch:112%;letter-spacing:-.03em;margin:0;max-width:18ch;color:#F5F1E8}}
.bot{{display:flex;justify-content:space-between;align-items:flex-end;border-top:1px solid rgba(184,161,136,.28);padding-top:22px;font-size:20px}}
.bot span{{color:#C5C0B6}}.bot b{{color:#B8A188}}
</style></head><body>
<div class="top">{WORD}</div>
<div><p class="k">Grok Bot first. One page for Claude.</p>
<h1>Grok Bot tips, with the real build behind each one.</h1></div>
<div class="bot"><span>nextaibreakout.com</span><b>Tips · Claude · Blog · About</b></div>
</body></html>"""
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(page); src = f.name
    dest = os.path.join(DIST, "og-default.png")
    try:
        subprocess.run(
            ["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
             "--virtual-time-budget=4000", "--window-size=1200,630", f"--screenshot={dest}", "file://" + src],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False,
        )
    finally:
        os.unlink(src)
    if os.path.isfile(dest) and os.path.getsize(dest) > 1000:
        shutil.copy(dest, os.path.join(DIST, "og.png"))
    else:
        # Fall back to a solid teal card generated without Chrome, still no ranking art.
        try:
            from PIL import Image, ImageDraw, ImageFont
            im = Image.new("RGB", (1200, 630), "#274043")
            d = ImageDraw.Draw(im)
            d.rectangle((64, 520, 1136, 521), fill="#B8A188")
            font_lg = font_sm = ImageFont.load_default()
            d.text((64, 80), "NextAiBreakout", fill="#B8A188", font=font_lg)
            d.text((64, 220), "Grok Bot tips, with the real", fill="#F5F1E8", font=font_lg)
            d.text((64, 280), "build behind each one.", fill="#F5F1E8", font=font_lg)
            d.text((64, 560), "nextaibreakout.com", fill="#C5C0B6", font=font_sm)
            im.save(dest, "PNG")
            shutil.copy(dest, os.path.join(DIST, "og.png"))
        except Exception:
            fallback = os.path.join(ROOT, "static", "og-default.png")
            if os.path.isfile(fallback):
                shutil.copy(fallback, dest)
                shutil.copy(fallback, os.path.join(DIST, "og.png"))


FEATURED_SLUGS = (
    "talk-to-one-lead-bot",
    "quality-checker-before-it-reaches-you",
    "drafts-only-approval",
    "blabara-in-one-day",
)

HOME_TITLE = "Grok Bot tips with real builds | NextAiBreakout"
# Honest meta: do not promise screenshots that are still placeholders.
HOME_DESC = "Grok Bot tips with the real build behind each one: the problem, how I did it, and what happened. Plus a separate page for Claude."
ABOUT_TITLE = "About this site | NextAiBreakout"
ABOUT_DESC = "NextAiBreakout is a Grok Bot tips site, with a separate page for Claude. Tips are reviewed before they go up."
LLMS = """# NextAiBreakout
> Grok Bot tips with the real build behind each one. One separate page for Claude.

## Site
- [Home](https://nextaibreakout.com/)
- [Tips](https://nextaibreakout.com/tips/)
- [Claude](https://nextaibreakout.com/claude/)
- [Blog](https://nextaibreakout.com/blog/)
- [About](https://nextaibreakout.com/about)

## Notes
Pages are reviewed before they go up. Unreviewed model output is not published. This site no longer ranks AI repos, models, or packages by hourly velocity.
"""


def featured():
    import tips as T
    out = []
    for slug in FEATURED_SLUGS:
        tip = T.BY_SLUG[slug]
        out.append({"slug": slug, "title": tip["title"], "line": tip["meta"], "path": T.path_of(slug)})
    return out


def home_page(year):
    cards = featured()
    card_html = "".join(
        f'<li><a class="tip-title" href="{e(c["path"])}">{e(c["title"])}</a><p>{e(c["line"])}</p></li>'
        for c in cards
    )
    org = {"@type": "Organization", "name": BRAND, "url": SITE + "/", "logo": SITE + "/og-default.png",
           "sameAs": [X_URL]}
    website = {"@type": "WebSite", "name": BRAND, "url": SITE + "/", "description": HOME_DESC, "inLanguage": "en-CA",
               "publisher": {"@id": SITE + "/#org"}}
    org = dict(org, **{"@id": SITE + "/#org"})
    item_list = {
        "@type": "ItemList",
        "name": "Featured Grok Bot tips",
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "numberOfItems": len(cards),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": c["title"], "url": SITE + c["path"]}
            for i, c in enumerate(cards, 1)
        ],
    }
    extra = ld({"@context": "https://schema.org", "@graph": [website, org, item_list]})
    return head(HOME_TITLE, HOME_DESC, "/", "/", extra) + f"""<main>
<section class="hero relaunch" id="top"><div class="hcopy">
<p class="kicker">Grok Bot first. One page for Claude.</p>
<h1>{H1_HTML}</h1>
<p class="lede">Most Grok Bot tip lists are one-liners. Fine as a checklist. Not how I learned this.</p>
<p class="lede">Every tip here comes from work I actually ran. You get the problem, how I did it, and what happened. A screenshot goes up when I have one that's safe to show. If I don't have the real story, the tip stays off the site.</p>
<div class="btns"><a class="btn pri" href="/tips/">Browse the tips</a><a class="btn" href="/claude/">Read the Claude notes</a></div>
</div></section>
<section class="proof" aria-label="From work I actually ran">
<article><h2>A real app in a day.</h2><p>On 16 Oct 2026, my brother and I built the Blabara Android voice-dictation app (it was called VoiceKey then) with a team of Grok Bots. I am not claiming it is live on Google Play.</p></article>
<article><h2>A coordinator, plus a checker.</h2><p>I talk to one Chief of Staff bot. A fleet-wide Quality Checker reviews work before it reaches me.</p></article>
<article><h2>Quiet unless something changed.</h2><p>Change-only scripts watch prices and other lists, and stay silent when nothing moved.</p></article>
<article><h2>I already use this for real work.</h2><p>I use AI for daily admin (email drafts, safety forms, crew attendance, scheduling, monthly tracking), and I replaced about 10 years of Squarespace by building my company site myself.</p></article>
</section>
<section class="home-sec" aria-label="Featured tips">
<h2>A few to start with.</h2>
<p>Each one links to the full write-up.</p>
<ul class="tip-cards">{card_html}</ul>
<p class="btns"><a class="btn" href="/tips/">See all tips</a></p>
</section>
<section class="claude-band">
<h2>I also use Claude. That work lives on its own page.</h2>
<p>This site is Grok Bot first. I'm not going to mix both tools into every tip.</p>
<p>Claude has its own page: what I can stand behind so far, and the one older guide already published on using Claude Code to debloat an Android TV, carefully.</p>
<div class="btns"><a class="btn pri" href="/claude/">Go to the Claude page</a></div>
</section>
</main>
""" + foot(year) + "</body></html>"


def about_page(year):
    url = SITE + "/about"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "AboutPage", "name": "About this site", "url": url, "description": ABOUT_DESC,
             "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE + "/"}},
            {"@type": "Organization", "name": BRAND, "url": SITE + "/", "logo": SITE + "/og-default.png", "sameAs": [X_URL]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "About", "item": url},
            ]},
        ],
    }
    body = f"""<main class="prose">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">About</span></nav>
<h1>About this site.</h1>
<p>NextAiBreakout is a Grok Bot tips site, with the real build behind each tip. There is a separate page for Claude.</p>
<p>Every tip comes from work I actually ran. You get the problem, how I did it, and what happened. A screenshot goes up when I have one that's safe to show. If I don't have those, the tip stays off the site.</p>
<p>I talk to one lead bot. A Quality Checker reviews work before it reaches me. Tips are reviewed before they go up. Unreviewed bot output does not publish.</p>
<p>This site no longer ranks AI repos, models, or packages by hourly velocity.</p>
<p><a href="/tips/">Browse the tips</a> · <a href="/claude/">Read the Claude notes</a> · <a href="/blog/">See the blog</a></p>
<p class="follow-p">Follow along on X: <a href="{X_URL}" rel="me noopener" target="_blank">{X_HANDLE}</a>.</p>
</main>"""
    return head(ABOUT_TITLE, ABOUT_DESC, "/about", "/", ld(graph)) + body + foot(year) + "</body></html>"


def not_found_page(year):
    nf = head(f"Page not found | {BRAND}", "This page doesn't exist on NextAiBreakout.", "/404.html", "/")
    nf = nf.replace('<link rel="canonical" href="https://nextaibreakout.com/404.html">', '<meta name="robots" content="noindex">')
    return nf + """<main class="prose">
<h1>Page not found</h1><p class="dim">That page doesn't exist, or hasn't launched yet.</p>
<div class="btns"><a class="btn pri" href="/tips/">Browse the tips</a><a class="btn" href="/about">About</a></div></main>""" + foot(year, "/") + "</body></html>"


def clear_dist():
    if os.path.isdir(DIST):
        for name in os.listdir(DIST):
            path = os.path.join(DIST, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    os.makedirs(DIST, exist_ok=True)


def write_redirects():
    src = os.path.join(ROOT, "_redirects")
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(DIST, "_redirects"))


def copy_functions():
    """Copy _routes.json into dist so the Pages Function stays scoped after wrangler pages deploy."""
    src = os.path.join(ROOT, "functions", "_routes.json")
    if os.path.isfile(src):
        shutil.copy(src, os.path.join(DIST, "_routes.json"))


def main():
    d = json.load(open(os.path.join(DATA, "scored-seo2.json" if SEO2 else "scored.json")))
    t = dt.datetime.fromisoformat(d["generated"])
    day = "2026-11-12"  # relaunch copy date, not a fake "updated hourly" stamp
    clear_dist()
    open(os.path.join(DIST, "index.html"), "w", encoding="utf-8").write(home_page(t.year))
    open(os.path.join(DIST, "about.html"), "w", encoding="utf-8").write(about_page(t.year))
    open(os.path.join(DIST, "404.html"), "w", encoding="utf-8").write(not_found_page(t.year))
    for f in os.listdir(os.path.join(ROOT, "static")):
        if f not in ("og.png", "og-default.png"):
            shutil.copy(os.path.join(ROOT, "static", f), DIST)
    fonts_dest = os.path.join(DIST, "fonts")
    if os.path.isdir(fonts_dest):
        shutil.rmtree(fonts_dest)
    shutil.copytree(os.path.join(ROOT, "fonts"), fonts_dest)
    write_redirects()
    copy_functions()
    og_brand()
    if not os.path.exists(os.path.join(DIST, "og-default.png")):
        src = os.path.join(ROOT, "static", "og-default.png")
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(DIST, "og-default.png"))
            shutil.copy(src, os.path.join(DIST, "og.png"))
    sitemap_urls = [("/", day, "weekly"), ("/about", day, "monthly"), ("/claude/", day, "monthly")]
    open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(
            f"<url><loc>{SITE}{p}</loc><lastmod>{d_}</lastmod><changefreq>{c}</changefreq></url>"
            for p, d_, c in sitemap_urls
        )
        + "</urlset>\n"
    )
    open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"
    )
    open(os.path.join(DIST, "llms.txt"), "w", encoding="utf-8").write(LLMS)
    # /data.json is retired (410 via the Pages Function). Do not emit the stale hourly payload.
    if SEO2:
        print("[build] SEO2=1 is set, but ranking pages are not emitted in this relaunch build")
    import tips
    tips.apply(DIST, t)
    import blog
    blog.apply(DIST, t)
    import claude
    claude.apply(DIST, t)
    # Site feed at /feed.xml (same items as the blog feed; no hourly ranking items).
    blog_rss = os.path.join(DIST, "blog", "rss.xml")
    if os.path.isfile(blog_rss):
        shutil.copy(blog_rss, os.path.join(DIST, "feed.xml"))
    if os.getenv("KIT") == "1":
        print("[build] KIT=1 is set, but NAB email sends are stopped and the form was not verified; signup is not injected")
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
