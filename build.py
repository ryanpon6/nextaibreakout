"""Render static site + per-run OG image to dist/."""
import datetime as dt, hashlib, html, json, os, shutil, subprocess, tempfile
from common import DATA, DIST, ROOT
DIST = os.getenv("NAB_DIST") or DIST
LABS = os.getenv("LABS") == "1"
SEO2 = os.getenv("SEO2") == "1"  # SEO fixes + archive/item pages: off by default so the hourly cron does not publish them yet
import re as _re
def re_strip(s): return _re.sub(r"\s+", " ", html.unescape(_re.sub(r"<[^>]+>", "", s))).strip()  # Frontier Labs pages: off by default so the hourly cron deploy does not publish them yet
SITE = "https://nextaibreakout.com"; BRAND = "NextAiBreakout"; TAG = "Grok Bot tips, with the real build behind each one."
OG_DEFAULT = "/og-default.jpg"
OG_ALT = "GROK BOT TIPS & TRICKS, nextaibreakout.com, with a white robot figurine"
DESC = "Grok Bot and Claude tips I've tested, plus daily AI news, with sources."
X_URL = "https://x.com/ryanpon"; X_HANDLE = "@ryanpon"
H1_TEXT = "Grok Bot tips from a fleet that actually ran."
# One <h1>, three lines. Each line slides up on load (style.css: .hero h1 .ln). Crawlers read it as one sentence.
H1_HTML = '<span class="ln"><span>Grok Bot tips</span></span> <span class="ln"><span>from a fleet that</span></span> <span class="ln"><span>actually ran.</span></span>'
e = html.escape
LABEL = {"github": "GitHub", "huggingface": "Hugging Face", "npm": "npm", "pypi": "PyPI", "hackernews": "Hacker News"}
GOLD = "#E0B84E"
# Cache-busting: stylesheet/font URLs carry a hash of their contents, so a visitor's browser never pairs new pages with an old cached stylesheet.
def _filehash(files):
    parts = []
    for f in files:
        path = os.path.join(ROOT, f)
        if os.path.isfile(path):
            parts.append(open(path, "rb").read())
    return hashlib.sha1(b"".join(parts)).hexdigest()[:10]
VER = _filehash(("static/style.css", "fonts/fonts.css"))
ICON_VER = _filehash(("static/favicon.svg", "static/favicon.png", "static/favicon.ico", "static/apple-touch-icon.png"))
FONTS = ('<link rel="preload" href="/fonts/Syne-var.woff2" as="font" type="font/woff2" crossorigin>'
         '<link rel="preload" href="/fonts/DMSans-var.woff2" as="font" type="font/woff2" crossorigin>'
         f'<link rel="stylesheet" href="/fonts/fonts.css?v={VER}">')
THEME = "#E9EEF2"  # page background (style.css --bg); used for the browser theme-color

# ---- Bot Cut-outs design system (see DESIGN.md). The robots are plain HTML shapes styled by style.css; no image files.
def bot_head(c="var(--red)", hr="", big=False, mouth=True):
    """Just a robot face. c = head colour, hr = head border-radius (.16em square, 50% round), big = monocle eye."""
    style = f"--c:{c}" + (f";--hr:{hr}" if hr else "")
    return (f'<span class="bhead" style="{style}" aria-hidden="true"><i class="beye{" big" if big else ""}"></i><i class="beye"></i>'
            + ('<b class="bmouth"></b>' if mouth else "") + "</span>")
def bot(c="var(--red)", hr="", a="", b="", big=False, cls=""):
    """A whole robot: antenna, head, body, arms. Size it with font-size on a parent. cls: 'wave' waves, 'still' stops the bobbing."""
    style = f"--c:{c}" + (f";--hr:{hr}" if hr else "") + (f";--a:{a}" if a else "") + (f";--b:{b}" if b else "")
    return (f'<span class="bot{" " + cls if cls else ""}" style="{style}" aria-hidden="true"><span class="bant"></span>'
            f'<span class="bhead"><i class="beye{" big" if big else ""}"></i><i class="beye"></i><b class="bmouth"></b></span>'
            '<span class="bbody"><i class="barm l"></i><i class="barm r"></i></span></span>')
# The three characters. Keep each one's look the same everywhere so readers learn who is who.
LEAD_BOT = dict(c="var(--red)", a="var(--och)")                               # lead bot: red, rounded head
SPECIALIST_BOT = dict(c="var(--blue)", hr=".16em", a="var(--red)")            # specialist: blue, square head
CHECKER_BOT = dict(c="var(--och)", hr="50% 50% .4em .4em", a="var(--blue)", big=True)  # Quality Checker: ochre, one monocle eye
# Title style "D" (Nov 12, 2026): a hand-drawn red loop around the key words, and a bot head peeking off page titles.
_LOOP = ('<svg aria-hidden="true" viewBox="0 0 200 60" preserveAspectRatio="none">'
         '<path pathLength="1" d="M44 7C104-1 178 2 194 24S168 58 100 57 5 49 6 29 54 3 128 3"/></svg>')
def circ(html_text):
    """Circle the key words of a title. Pass escaped HTML. Keep it to 1-3 short words so it stays on one line."""
    return f'<span class="circ">{html_text}{_LOOP}</span>'
def peek_h1(inner_html, who=None):
    """A page title with a bot head peeking off its top-right corner. who = LEAD_BOT, SPECIALIST_BOT or CHECKER_BOT."""
    w = who or LEAD_BOT
    return (f'<div class="ptitle"><h1>{inner_html}</h1>'
            + bot_head(w["c"], w.get("hr", ""), big=w.get("big", False)) + '</div>')
NAVWORD = '<span class="bhead" aria-hidden="true"><i class="beye"></i><i class="beye"></i></span><span>NextAiBreakout</span>'
# Mark: a frame with a line breaking out through its top-right corner
LOGO = ('<svg class="logo" viewBox="0 0 32 32" width="32" height="32" aria-hidden="true"><path d="M17 5H5v22h22V15" fill="none" stroke="currentColor" stroke-width="2.6"/>'
        '<path class="logo-break" d="M10.5 21.5L27 5M19 5h8v8" fill="none" stroke="#E0B84E" stroke-width="2.6" stroke-linecap="square"/></svg>')
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

# Scroll-effect fallback: only runs where CSS scroll-driven animation is missing. Pairs with the .sj rules in style.css.
SCROLL_JS = ("<script>(function(){var d=document.documentElement;"
             "if(!window.CSS||!CSS.supports||CSS.supports('animation-timeline: view()')||!('IntersectionObserver' in window))return;"
             "d.classList.add('sj');document.addEventListener('DOMContentLoaded',function(){"
             "var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -12% 0px'});"
             "document.querySelectorAll('.rv,.stamp,.badge .shape,.steps').forEach(function(n){io.observe(n)})})})();</script>")

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
<meta property="og:url" content="{SITE}{path}"><meta property="og:image" content="{SITE}{OG_DEFAULT}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{e(OG_ALT)}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}"><meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{SITE}{OG_DEFAULT}"><meta name="twitter:site" content="{X_HANDLE}"><meta name="twitter:creator" content="{X_HANDLE}">
<meta name="color-scheme" content="light"><meta name="theme-color" content="{THEME}">
<link rel="icon" href="/favicon.svg?v={ICON_VER}" type="image/svg+xml"><link rel="icon" href="/favicon.png?v={ICON_VER}" type="image/png" sizes="32x32"><link rel="icon" href="/favicon.ico?v={ICON_VER}" sizes="16x16 32x32"><link rel="apple-touch-icon" href="/apple-touch-icon.png?v={ICON_VER}" sizes="180x180">{FONTS}<link rel="stylesheet" href="/style.css?v={VER}">{labscss}{extra}{MENU_JS}{SCROLL_JS}</head><body>
<header class="top"><a class="brand" href="/" aria-label="{BRAND} home">{NAVWORD}</a>
<div class="acts"><a class="ghost xf" href="{X_URL}" rel="me noopener" target="_blank" aria-label="Follow on X">{XICON}<span>Follow</span></a><button class="ib nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">{MENU}{CLOSE}</button></div>
<nav id="site-nav" aria-label="Primary"><a href="/tips/">Grok Bot Tips</a><a href="/claude/">Claude Tips</a><a href="/blog/">Blog</a><a href="/about">About</a></nav></header>"""

def foot(year, root=""):
    return f"""<footer><div class="fbase"><span>© {year} NextAiBreakout.com. {TAG}</span><span class="fmeta"><a href="/tips/">Grok Bot Tips</a><a href="/claude/">Claude Tips</a><a href="/blog/">Blog</a><a href="/about">About</a><a href="/feed.xml">RSS</a><a href="{root}llms.txt">llms.txt</a><a href="{X_URL}" rel="me noopener" target="_blank">X {X_HANDLE}</a></span></div>
<p class="fnote">Daily news posts publish once an automated gate passes them. Other posts publish on a schedule after my checker bot reviews them. Sends, spending and sign-ins still wait for my OK.</p></footer>"""

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
    """Copy the default share image (photo + Syne text from brand/render_og_photo.py)."""
    static = os.path.join(ROOT, "static")
    pairs = (
        ("og-default.jpg", "og-default.jpg"),
        ("og-default.png", "og-default.png"),
        ("og.jpg", "og.jpg"),
        ("og.png", "og.png"),
    )
    for src_name, dest_name in pairs:
        src = os.path.join(static, src_name)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(DIST, dest_name))


HOME_TITLE = "Grok Bot tips with real builds | NextAiBreakout"
HOME_DESC = "Grok Bot and Claude tips I've tested, plus daily AI news, with sources."
ABOUT_TITLE = "About this site | NextAiBreakout"
ABOUT_DESC = "Why I built NextAiBreakout: I'm not a coder, I run a company, and I only publish Grok Bot and Claude tips I've tested and can prove."
LLMS = """# NextAiBreakout
> Grok Bot tips with the real build behind each one. A separate Claude Tips index.

## Site
- [Home](https://nextaibreakout.com/)
- [Grok Bot Tips](https://nextaibreakout.com/tips/)
- [Claude Tips](https://nextaibreakout.com/claude/)
- [Blog](https://nextaibreakout.com/blog/)
- [About](https://nextaibreakout.com/about)

## Notes
Pages and posts go up after a checker review; the daily news post is cleared by an automated gate. Sends, spending and sign-ins still wait for my OK. This site no longer ranks AI repos, models, or packages by hourly velocity.
"""


def home_page(year):
    import tips as T
    import blog as BL
    import catalog as C
    # Counts come from the data, so they stay right when tips are added.
    all_tips = list(T.TIPS) + list(T.HUB_ONLY)
    n_all, n_full = len(all_tips), len(T.TIPS)
    grok_latest = C.latest(3, kind="grok", type="tip")
    claude_latest = C.latest(3, kind="claude", type="tip")
    topics = "".join(
        f'<a href="/tips/#sec-{e(k)}">{e(label)} <span>{n}</span></a>'
        for k, label in T.SECTIONS
        for n in [sum(1 for t in all_tips if t["section"] == k)] if n
    )
    # Latest blog posts (newest three). Hidden when there are none.
    # If a post is already in a tip strip, don't list it again; drop the section if that leaves it empty.
    already = {e["url"] for e in grok_latest + claude_latest}
    posts = [p for p in BL.posts() if f"/blog/{p['slug']}/" not in already][:3]
    post_html = "".join(
        f'<li><a href="/blog/{e(p["slug"])}/"><time datetime="{e(p["date"])}">{e(BL.nice(p["date"]))}</time>'
        f'<b>{e(p["title"])}</b><span>{e(p["description"])}</span><i aria-hidden="true">→</i></a></li>'
        for p in posts
    )
    posts_sec = f"""<section class="sec" aria-labelledby="h-posts"><div class="wrap">
<div class="sh rv"><h2 id="h-posts">Latest {circ("posts.")}</h2><a class="more" href="/blog/">All posts →</a></div>
<ul class="posts rv">{post_html}</ul>
</div></section>""" if posts else ""
    tape = "one lead bot <i>✶</i> a quality checker <i>✶</i> nothing posts unchecked <i>✶</i> no fix without proof <i>✶</i> quiet unless something changed <i>✶</i> one job per bot <i>✶</i>"
    org = {"@type": "Organization", "name": BRAND, "url": SITE + "/", "logo": SITE + OG_DEFAULT,
           "sameAs": [X_URL]}
    website = {"@type": "WebSite", "name": BRAND, "url": SITE + "/", "description": HOME_DESC, "inLanguage": "en-CA",
               "publisher": {"@id": SITE + "/#org"}}
    org = dict(org, **{"@id": SITE + "/#org"})
    graph = [website, org, C.item_list("Latest Grok Bot tips", grok_latest)]
    if claude_latest:
        graph.append(C.item_list("Latest Claude Tips", claude_latest))
    extra = ld({"@context": "https://schema.org", "@graph": graph})
    grok_sec = f"""<section class="sec" id="start" aria-labelledby="h-start"><div class="wrap">
<div class="sh rv"><h2 id="h-start">Latest {circ("Grok Bot tips.")}</h2><a class="more" href="/tips/">See all Grok Bot tips</a></div>
{C.listing_html(grok_latest, "rv")}
</div></section>"""
    claude_sec = f"""<section class="sec" id="claude-tips" aria-labelledby="h-claude"><div class="wrap">
<div class="sh rv"><h2 id="h-claude">Latest {circ("Claude Tips.")}</h2><a class="more" href="/claude/">See all Claude Tips</a></div>
{C.listing_html(claude_latest, "rv")}
</div></section>""" if claude_latest else ""
    return head(HOME_TITLE, HOME_DESC, "/", "/", extra) + f"""<main class="home">
<section class="hero" id="top"><div class="wrap">
<div class="art" aria-hidden="true">
<div class="shape morph1" style="left:0;top:14%;width:52%;aspect-ratio:1.1;background:var(--och);border-radius:62% 38% 54% 46%/48% 60% 40% 52%"></div>
<div class="shape morph2" style="right:2%;top:4%;width:40%;aspect-ratio:1;background:var(--sky);border-radius:50%"></div>
<div class="dots" style="right:24%;bottom:0;width:34%;aspect-ratio:1"></div>
<div class="b1"><div class="pop" style="animation-delay:.5s">{bot(cls="wave", **LEAD_BOT)}</div></div>
<div class="b2"><div class="pop" style="animation-delay:.7s">{bot(**SPECIALIST_BOT)}</div></div>
<div class="b3"><div class="pop" style="animation-delay:.9s">{bot(**CHECKER_BOT)}</div></div>
<p class="say pop" style="animation-delay:1.3s">one message in.<br>one result out!</p>
</div>
<p class="note fade">Grok Bot tips, from real work ↓</p>
<h1>{H1_HTML}</h1>
<svg class="squig" aria-hidden="true" viewBox="0 0 300 24" preserveAspectRatio="none"><path pathLength="1" d="M4 14c40-12 70 10 110-2s70-8 100 2 50-6 82-4"/></svg>
<p class="lede fade" style="animation-delay:.8s">How I run a team of Grok Bots: one lead bot, a Quality Checker, and an approval-first rule. Every tip comes from work I actually ran. You get the problem, how I did it, and what happened.</p>
<div class="btns fade" style="animation-delay:1s"><a class="btn pri" href="/tips/">Read all {n_all} tips →</a><a class="btn" href="#how">How it works</a></div>
</div></section>
<div class="tapewrap" aria-hidden="true"><div class="tape"><div><span>{tape}</span><span>{tape}</span></div></div></div>
<section class="sec" id="how" aria-labelledby="h-how"><div class="wrap split">
<div class="rv"><h2 id="h-how">How one person runs a team of {circ("Grok Bots.")}</h2><p class="note">same 5 steps, every single request</p></div>
<div class="steps">
<svg aria-hidden="true" viewBox="0 0 40 500" preserveAspectRatio="none"><path pathLength="1" d="M20 0C44 40-4 80 20 125S44 205 20 250-4 330 20 375 44 455 20 500"/></svg>
<ol>
<li class="rv">{bot_head("#fff", "50%")}<span><b>1. I send one message</b><span>To one lead bot, not the whole fleet.</span></span></li>
<li class="rv">{bot_head("var(--red)")}<span><b>2. The lead bot routes it</b><span>It picks the specialist and brings back one result.</span></span></li>
<li class="rv">{bot_head("var(--blue)", ".16em")}<span><b>3. A specialist drafts</b><span>One job each. It writes a draft; it can't publish.</span></span></li>
<li class="rv">{bot_head("var(--och)", "50% 50% .4em .4em", big=True)}<span><b>4. The Quality Checker holds weak work</b><span>No before and after, no pass.</span></span></li>
<li class="rv">{bot_head("#fff", "50%")}<span><b>5. I approve</b><span>Sends, spending and sign-ins still wait for my OK.</span></span></li>
</ol></div>
</div></section>
{grok_sec}
{claude_sec}
{posts_sec}
<section class="sec proof" aria-labelledby="h-proof"><div class="wrap">
<div class="badge" aria-hidden="true"><div class="shape"></div><div class="dots"></div><p class="stamp">1 day</p></div>
<div class="txt rv"><p class="note">proof · 16 Oct 2026</p>
<h2 id="h-proof">A real Android app, built {circ("in a day")} by a team of Grok Bots.</h2>
<p>On 16 Oct 2026, my brother and I built the Blabara Android voice-dictation app (it was called VoiceKey then) with a team of Grok Bots.</p>
<p>I use AI for daily admin (email drafts, safety forms, crew attendance, scheduling, monthly tracking), and I replaced about 10 years of Squarespace by building my company site myself.</p>
<a class="more" href="/tips/blabara-in-one-day/">How we built Blabara in one day →</a></div>
</div></section>
<section class="sec" aria-labelledby="h-topics"><div class="wrap">
<h2 id="h-topics" class="rv">{circ("Grok Bot tips")} by topic.</h2>
<p class="lede rv">{n_all} tips so far. {n_full} have a full write-up with how I did it.</p>
<nav class="stickers rv" aria-label="Tips by topic">{topics}</nav>
</div></section>
<section class="sec"><div class="wrap duo">
<div class="card rv"><h2>Using Claude too? That has its own page.</h2>
<p>This site is Grok Bot first. I'm not going to mix both tools into every tip. Claude Tips is a separate list, including the older guide on using Claude Code to debloat an Android TV, carefully.</p>
<a class="more" href="/claude/">See all Claude Tips</a></div>
<div class="card dark rv"><span class="perch">{bot(cls="wave", c="var(--och)", a="var(--red)")}</span>
<h2>Follow the build on X.</h2>
<p>I post Grok Bot tips and builds on X.</p>
<a class="btn" href="{X_URL}" rel="me noopener" target="_blank">Follow {X_HANDLE}</a></div>
</div></section>
</main>
""" + foot(year) + "</body></html>"


def about_page(year):
    url = SITE + "/about"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "AboutPage", "name": "About this site", "url": url, "description": ABOUT_DESC,
             "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE + "/"}},
            {"@type": "Organization", "name": BRAND, "url": SITE + "/", "logo": SITE + OG_DEFAULT, "sameAs": [X_URL]},
            {"@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "About", "item": url},
            ]},
        ],
    }
    body = f"""<main class="prose">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">About</span></nav>
{peek_h1("About " + circ("this site."), LEAD_BOT)}
<p class="note" style="margin:0 0 18px">a regular user, not a coder</p>
<p>NextAiBreakout is a Grok Bot tips site, with the real build behind each tip. Claude Tips has its own page.</p>

<h2>Why I {circ("built this")}</h2>
<p>I have always loved computers, AI, and code. I am not a coder. I run my own company, and I built this website while automating my work with Grok and other AI tools.</p>
<p>That is the point of the site. I am a regular user, and I can still produce work that companies pay specialists to do. I replaced about 10 years of Squarespace by building my company site myself. My brother and I built an Android app in a day with a team of Grok Bots.</p>
<p>I hope it gets you to try it. You may build something you did not think you could, with Grok and with Claude.</p>

<h2>Why keep it {circ("updated")}</h2>
<p>AI moves fast. New releases keep landing, and it gets overwhelming. I wanted one place that keeps up without the noise.</p>
<p>A lot of AI posts are made for the sake of posting. This site is curated. It only covers things I have actually tested, can prove, and want to stand behind.</p>

<h2>What gets {circ("published")}</h2>
<p>Every tip comes from work I actually ran. You get the problem, how I did it, and what happened. A screenshot goes up when I have one that's safe to show. If I don't have those, the tip stays off the site.</p>
<p>I talk to one lead bot. A Quality Checker reviews work before it reaches me. Daily news posts publish once an automated gate passes them. Other posts publish on a schedule after my checker bot reviews them. Sends, spending and sign-ins still wait for my OK.</p>
<p>This site no longer ranks AI repos, models, or packages by hourly velocity.</p>
<p><a href="/tips/">See all Grok Bot tips</a> · <a href="/claude/">See all Claude Tips</a> · <a href="/blog/">See the blog</a></p>
<p class="follow-p">Follow along on X: <a href="{X_URL}" rel="me noopener" target="_blank">{X_HANDLE}</a>.</p>
</main>"""
    return head(ABOUT_TITLE, ABOUT_DESC, "/about", "/", ld(graph)) + body + foot(year) + "</body></html>"


def not_found_page(year):
    nf = head(f"Page not found | {BRAND}", "This page doesn't exist on NextAiBreakout.", "/404.html", "/")
    nf = nf.replace('<link rel="canonical" href="https://nextaibreakout.com/404.html">', '<meta name="robots" content="noindex">')
    return nf + f"""<main class="prose">
{peek_h1("Page " + circ("not found"), CHECKER_BOT)}<p class="dim">That page doesn't exist, or hasn't launched yet.</p>
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
    static_dir = os.path.join(ROOT, "static")
    for f in os.listdir(static_dir):
        if f in ("og.png", "og-default.png", "og.jpg", "og-default.jpg"):
            continue
        src = os.path.join(static_dir, f)
        dest = os.path.join(DIST, f)
        if os.path.isdir(src):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            shutil.copy(src, dest)
    fonts_dest = os.path.join(DIST, "fonts")
    if os.path.isdir(fonts_dest):
        shutil.rmtree(fonts_dest)
    shutil.copytree(os.path.join(ROOT, "fonts"), fonts_dest)
    write_redirects()
    copy_functions()
    og_brand()
    if not os.path.exists(os.path.join(DIST, "og-default.jpg")):
        og_brand()
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
    # Google Analytics 4 (NextAiBreakout property). Injected into every built page, once.
    GA = '<script async src="https://www.googletagmanager.com/gtag/js?id=G-J7VKNV3DJ0"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag("js",new Date());gtag("config","G-J7VKNV3DJ0");</script>'
    for root_, _, files in os.walk(DIST):
        for fn in files:
            if fn.endswith(".html"):
                fp = os.path.join(root_, fn); h = open(fp, encoding="utf-8").read()
                if "G-J7VKNV3DJ0" not in h and "</head>" in h:
                    open(fp, "w", encoding="utf-8").write(h.replace("</head>", GA + "</head>", 1))
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
