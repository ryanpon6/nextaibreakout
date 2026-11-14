#!/usr/bin/env python3
"""Step 3: the publish gate. Scheduled runs can't message Quality Checker, so these checks stand in for it.
Any failure exits 1, appends the reasons to autopost-issues.md, and publish.py stops. Nothing is auto-fixed.

Checks (each prints PASS or FAIL):
  G1  ledger      slot nab-news-DATE is not already in posted.jsonl
  G2  timing      not within 60 min of a tip slot (9 AM, 1 PM, 6 PM Atlantic = 7 AM, 11 AM, 4 PM Edmonton today)
  G3  rule19      no placeholder / TODO / TBD / coming soon / lorem / draft / not written yet / FIXME / {{ }} text,
                  no empty img src or alt, empty figure, link, heading, paragraph or list item
  G4  rule20      every token in DESIGN.md's table is in the built style.css with the same value; page uses the
                  site stylesheet, Syne font, peek title and prose layout; no retired teal/gold/off-white hex,
                  Archivo or "gold on teal"; no purple or pink colours; no #FF4B2B / var(--red) text;
                  card pixels: pale ground present, no teal/gold/purple/pink areas
  G5  links       every link, image and cited source on the page is HTTPS and returns 200 (internal links must
                  exist in the build; after deploy publish.py re-checks the live URL)
  G6  image       OG card 1200x630 PNG and X card 1600x900 PNG exist, are > 15 KB (X card < 5 MB), and the OG card
                  is the page's og:image, twitter:image, schema image and lead <img>
  G7  claims      the gate RE-FETCHES every cited post from X's public embed endpoint itself (the story file is
                  only a list of ids; a story file whose text differs from X fails). Every blockquote and every
                  quoted phrase (3+ words) is verbatim in that re-fetched text; the main X post must carry one
                  such quoted phrase; every number in title, description, body, card and X text is in a cited
                  post AND keeps the source's qualifier (~ / about / around / roughly / approximately / nearly);
                  every x.com post linked is a verified one
  G8  secrets     no token patterns, secret file paths or secret env var names, and no live secret env value
  G9  seo         one h1, title <= 60, description <= 155, canonical, in sitemap/feed/blog index/homepage,
                  in catalog.json (and catalog.py validates) when the catalog exists, Article schema, no noindex, links to 2+ existing tips, h2 subheads
  G10 xtext       main post <= 280 by twitter-text weighting (CJK, emoji, '…', '•' count 2) with no link or domain; reply is exactly the story-link reply; alt <= 1000
  G11 privacy     no Landscape Specialists, Gavin, email address or phone number
  G12 hold        per-post hold (switch: tools/news/config.json "hold_money_policy", default true). If the story
                  touches money, pricing, plans, usage limits, billing or policy (keyword list below, or
                  "sensitive": true in the story file), the gate returns HELD (exit 20) instead of PASS.
                  publish.py then writes news/held-DATE.md and an alert, and waits for publish.py --release DATE.
Exit   0 pass · 1 fail (any failure wins over a hold) · 20 held by G12 only
Usage  gate.py --dist DIR [--date YYYY-MM-DD] [--at "YYYY-MM-DD HH:MM"] [--no-log] [--release]"""
import argparse, colorsys, datetime as dt, glob, html as H, json, os, re, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nc

RETIRED = ["#274043", "#1F3336", "#E0B84E", "#F5F1E8", "#E8C45A", "Archivo", "gold on teal"]
R19 = re.compile(r"\b(placeholder|todo|tbd|coming soon|lorem|ipsum|draft|not written yet|fixme|xxx+|insert (?:link|image|here)|example coming)\b|\{\{|\}\}|\[\s*(?:link|image|tk)\s*\]", re.I)
URL_RE = re.compile(r"(https?://|www\.)|\b[a-z0-9-]+\.(com|ai|io|org|net|dev|app|co|xyz|gg|me|so|sh|ly|tv|info|us|ca)\b", re.I)  # xpost.py's rule
SECRET_PATTERNS = [r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}", r"\bxai-[A-Za-z0-9]{20,}", r"\bsk-[A-Za-z0-9_-]{20,}",
                   r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY", r"Bearer\s+[A-Za-z0-9._~+/-]{20,}", r"AAAAAAAAAAAAAAAAAAAAA[A-Za-z0-9%]{20,}",
                   r"CLOUDFLARE_API_TOKEN", r"KIT_API_KEY", r"NAB_WATCHDOG_(?:GH|CF)_TOKEN", r"X_(?:API_KEY|API_KEY_SECRET|ACCESS_TOKEN|ACCESS_TOKEN_SECRET)",
                   r"cloudflare\.env", r"gsc-nextaibreakout\.json", r"\.secrets/", r"\b\d{6,}-[A-Za-z0-9]{30,}\b"]
SECRET_ENVS = ("CLOUDFLARE_API_TOKEN", "KIT_API_KEY", "NAB_WATCHDOG_GH_TOKEN", "NAB_WATCHDOG_CF_TOKEN",
               "X_API_KEY", "X_API_KEY_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET", "GITHUB_TOKEN", "GH_TOKEN")
HOLD_RE = re.compile(r"\$\s?\d|\b(money|price[sd]?|pricing|cost[s]?|dollars?|usd|plans?|subscriptions?|subscribers? only|tier[s]?|billing|billed|bill|refunds?|"
                     r"payments?|pay|paid|charge[sd]?|fees?|credits?|usage|limits?|rate limits?|quotas?|policy|policies|terms of service|tos|"
                     r"pricing|discount|free trial|trial|revenue|earn(?:ed|ings)?|profit)\b", re.I)
QUAL = r"(?:(~)|\b((?i:about|around|roughly|approximately|approx\.|nearly))\s+)?"
MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?"

class Gate:
    def __init__(s): s.fails, s.lines = [], []
    def check(s, name, problems):
        problems = [p for p in problems if p]
        s.lines.append(f"{'PASS' if not problems else 'FAIL'} {name}" + ("" if not problems else ": " + "; ".join(problems[:8]) + (f" (+{len(problems)-8} more)" if len(problems) > 8 else "")))
        if problems: s.fails.append(f"{name}: " + "; ".join(problems[:8]))
        print(s.lines[-1], flush=True)

def visible(h):
    h = re.sub(r"<(script|style)\b.*?</\1>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", h))).strip()

def main_of(page):
    m = re.search(r"<main\b.*?</main>", page, re.S); return m.group(0) if m else ""

def png_size(p):
    with open(p, "rb") as f: d = f.read(24)
    if not d.startswith(b"\x89PNG\r\n\x1a\n"): return None
    return struct.unpack(">II", d[16:24])

def hue_bad(hexs):
    h = hexs.lstrip("#")
    if len(h) == 3: h = "".join(c * 2 for c in h)
    if len(h) != 6: return False
    r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return 0.70 <= hh <= 0.97 and ss > 0.35 and 0.15 < ll < 0.9     # ~250-350 degrees: purple, violet, magenta, pink

def pixel_check(p):
    from PIL import Image
    im = Image.open(p).convert("RGB"); im.thumbnail((400, 400)); b = im.tobytes(); px = [tuple(b[i:i+3]) for i in range(0, len(b), 3)]; n = len(px)
    near = lambda c, t, tol: abs(c[0]-t[0]) <= tol and abs(c[1]-t[1]) <= tol and abs(c[2]-t[2]) <= tol
    bad = {"teal #274043": (39, 64, 67), "dark teal #1F3336": (31, 51, 54), "gold #E0B84E": (224, 184, 78), "off-white #F5F1E8": (245, 241, 232)}
    out = []
    for k, t in bad.items():
        f = sum(near(c, t, 10) for c in px) / n
        if f > 0.01: out.append(f"{os.path.basename(p)} has {f:.1%} {k} pixels")
    pp = sum(hue_bad("#%02x%02x%02x" % c) for c in px) / n
    if pp > 0.01: out.append(f"{os.path.basename(p)} has {pp:.1%} purple/pink pixels")
    bg = sum(near(c, (233, 238, 242), 6) for c in px) / n
    if bg < 0.15: out.append(f"{os.path.basename(p)} pale ground #E9EEF2 is only {bg:.1%} of pixels")
    ink = sum(near(c, (15, 27, 61), 14) for c in px) / n
    if ink < 0.01: out.append(f"{os.path.basename(p)} has almost no ink #0F1B3D")
    return out

def num_hits(text):
    """[(qualified, bare_number)] for every figure in text, ignoring dates, times, years and URLs."""
    t = re.sub(rf"\b{MONTH}\s+\d{{1,2}}(?:,\s*\d{{4}})?", " ", text)
    t = re.sub(r"\b\d{4}-\d\d-\d\d\b|\b\d{1,2}:\d\d\s*(?:AM|PM|am|pm)?\b|\b20\d\d\b", " ", t)
    t = re.sub(r"https?://\S+|/[\w/-]*\d[\w/-]*", " ", t)
    return [(bool(m.group(1) or m.group(2)), m.group(3)) for m in re.finditer(QUAL + r"\$?(\d[\d,]*(?:\.\d+)?%?)", t)]

def quoted(text):
    out = []
    for m in re.finditer(r"\u201c([^\u201d]{3,400})\u201d|\"([^\"]{3,400})\"", text):
        s = (m.group(1) or m.group(2)).strip()
        if len(s.split()) >= 3: out.append(s)
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dist", required=True); ap.add_argument("--date", default=nc.today())
    ap.add_argument("--at", help="check timing as of this Edmonton time, e.g. '2026-11-15 08:05'"); ap.add_argument("--no-log", action="store_true")
    ap.add_argument("--skip-net", action="store_true", help="unit tests only; skips G5's external link fetches (G7 always re-fetches); never used by publish.py")
    ap.add_argument("--release", action="store_true", help="manual release of a G12 hold (publish.py --release); every other check still runs")
    a = ap.parse_args(); G = Gate()
    print(f"gate: slot {nc.slot(a.date)}, dist {a.dist}", flush=True)
    try:
        pay = nc.load(nc.path("xpayload", a.date)); story = nc.load(nc.path("story", a.date)); spec = nc.load(nc.path("spec", a.date))
    except Exception as e:
        G.check("inputs", [f"missing payload/story/spec for {a.date}: {e.__class__.__name__}"]); return finish(G, a)
    slug, url = pay["slug"], pay["url"]
    pagep = os.path.join(a.dist, "blog", slug, "index.html")
    page = open(pagep, encoding="utf-8").read() if os.path.exists(pagep) else ""
    md = open(pay["post_md"], encoding="utf-8").read() if os.path.exists(pay["post_md"]) else ""
    main_h = main_of(page); vis = visible(main_h)
    xtexts = [pay["main"]["text"], pay["reply"]["text"], pay["main"].get("alt", "")]
    cardtxt = " ".join([spec.get("card_headline", ""), spec.get("note", "")] + list(spec.get("card_points", [])))
    if not page or not md: G.check("inputs", [f"built page missing: {pagep}" if not page else "", f"post md missing: {pay['post_md']}" if not md else ""])

    # G1 ledger
    row = nc.in_ledger(a.date)
    G.check("G1 ledger", [f"slot {nc.slot(a.date)} already posted: {row.get('url')}" if row else ""])
    # G2 timing
    t = dt.datetime.strptime(a.at, "%Y-%m-%d %H:%M").replace(tzinfo=nc.MT) if a.at else nc.now()
    blocked, near = nc.tip_window(t)
    G.check("G2 timing", [f"{t:%H:%M} MT is within {nc.SLOT_GAP_MIN} min of the {near:%-I:%M %p} MT tip slot" if blocked else ""])
    # G3 rule 19
    p19 = []
    for where, txt in (("page", vis), ("page head", " ".join(re.findall(r'<title>([^<]*)</title>|content="([^"]*)"', page[:page.find("<body")]) and [x for t in re.findall(r'<title>([^<]*)</title>|content="([^"]*)"', page[:page.find("<body")]) for x in t])),
                       ("x text", " ".join(xtexts)), ("card", cardtxt), ("title/description", spec["title"] + " " + spec["description"])):
        for m in R19.finditer(txt): p19.append(f"{where}: '{m.group(0)}'")
    for m in re.finditer(r"<img\b[^>]*>", main_h):
        tag = m.group(0)
        if re.search(r'\bsrc=""|\bsrc\s*=\s*""', tag) or "src=" not in tag: p19.append("img with empty src")
        if re.search(r'\balt=""', tag) or "alt=" not in tag: p19.append("img with empty alt")
    for tag in ("figure", "a", "h1", "h2", "h3", "p", "li", "blockquote"):
        for m in re.finditer(rf"<{tag}\b[^>]*>(.*?)</{tag}>", main_h, re.S):
            if not visible(m.group(1)) and "<img" not in m.group(1) and "<svg" not in m.group(1) and "bhead" not in m.group(0): p19.append(f"empty <{tag}>")
    if re.search(r'href=""|href="#"', main_h): p19.append("empty link href")
    G.check("G3 rule19 nothing unfinished", p19)
    # G4 rule 20 design
    p20 = []
    design = open(os.path.join(nc.ROOT, "DESIGN.md"), encoding="utf-8").read()
    toks = re.findall(r"^\|\s*`(--[\w-]+)`\s*\|\s*`(#[0-9A-Fa-f]{3,6})`", design, re.M)
    if len(toks) < 6: p20.append(f"could only read {len(toks)} tokens from DESIGN.md")
    css = open(os.path.join(a.dist, "style.css"), encoding="utf-8").read() if os.path.exists(os.path.join(a.dist, "style.css")) else ""
    root = re.search(r":root\{(.*?)\}", css, re.S); root = root.group(1) if root else ""
    for k, v in toks:
        m = re.search(rf"{re.escape(k)}:\s*(#[0-9A-Fa-f]+)", root)
        if not m or m.group(1).lower() not in (v.lower(), v.lower()[:4] if len(v) == 7 and v[1::2] == v[2::2] else v.lower()):
            if not (m and v.lower() == "#ffffff" and m.group(1).lower() == "#fff"): p20.append(f"style.css {k} is {m.group(1) if m else 'missing'}, DESIGN.md says {v}")
    for need, why in (('href="/style.css', "site stylesheet"), ("Syne", "Syne font"), ('class="ptitle"', "peek title (peek_h1)"), ('class="prose post"', "prose post layout"), ('class="lead-img"', "lead card figure")):
        if need not in page: p20.append(f"page lacks {why}")
    blob = page + md + " ".join(xtexts) + cardtxt
    for r in RETIRED:
        if r.lower() in blob.lower(): p20.append(f"retired style '{r}' present")
    for hx in set(re.findall(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b", main_h + md)):
        if hue_bad(hx): p20.append(f"purple/pink colour {hx}")
    if re.search(r"\b(purple|violet|magenta|fuchsia|pink|orchid|plum)\b", " ".join(re.findall(r'style="([^"]*)"', main_h)), re.I): p20.append("named purple/pink colour in inline style")
    if re.search(r"(?<![-\w])color:\s*(#FF4B2B|var\(--red\))", main_h, re.I): p20.append("red #FF4B2B used as text colour (use --red-ink)")
    for c in (pay["og_image"], pay["x_card"]):
        if os.path.exists(c): p20 += pixel_check(c)
    G.check("G4 rule20 design", p20)
    # G5 links
    p5, ext = [], set()
    refs = re.findall(r'(?:href|src)="([^"]+)"', main_h) + re.findall(r'<meta (?:property|name)="(?:og:image|twitter:image|og:url)" content="([^"]+)"', page)
    refs += [p["url"] for p in story["posts"]] + ([story["news_url"]] if story.get("news_url") else [])
    for r in dict.fromkeys(H.unescape(x) for x in refs):
        if r.startswith("http://"): p5.append(f"not HTTPS: {r}")
        elif r.startswith(nc.SITE + "/"):
            loc = r[len(nc.SITE):]
            if loc != f"/blog/{slug}/" and not exists_in(a.dist, loc): p5.append(f"internal {loc} not in build")
        elif r.startswith("https://"): ext.add(r)
        elif r.startswith("/"):
            if not exists_in(a.dist, r): p5.append(f"internal {r} not in build")
        elif r.startswith(("mailto:", "tel:")): p5.append(f"contact link {r}")
    if not a.skip_net:
        for r in sorted(ext):
            code = nc.http_status(r)
            if code != 200: p5.append(f"{r} -> HTTP {code}")
    G.check(f"G5 links ({len(ext)} external checked over HTTPS)", p5)
    # G6 image
    p6 = []
    for c, wh, lim in ((pay["og_image"], (1200, 630), 5_000_000), (pay["x_card"], (1600, 900), 5_000_000)):
        if not os.path.exists(c): p6.append(f"missing {c}"); continue
        sz = os.path.getsize(c); dims = png_size(c)
        if sz < 15_000: p6.append(f"{os.path.basename(c)} only {sz} bytes")
        if sz > lim: p6.append(f"{os.path.basename(c)} over 5 MB")
        if dims != wh: p6.append(f"{os.path.basename(c)} is {dims}, want {wh}")
    rel = "/images/news/" + os.path.basename(pay["og_image"])
    if not os.path.exists(os.path.join(a.dist, rel.lstrip("/"))): p6.append(f"{rel} not copied into the build")
    for pat, what in ((f'property="og:image" content="{nc.SITE}{rel}"', "og:image"), (f'name="twitter:image" content="{nc.SITE}{rel}"', "twitter:image"),
                      (f'"image": "{nc.SITE}{rel}"', "schema image"), (f'<img src="{rel}"', "lead img")):
        if pat not in page: p6.append(f"{what} does not point at {rel}")
    G.check("G6 image", p6)
    # G7 claims: re-fetch every cited post here; never trust the text stored in the story file
    p7 = []; srcs = {}
    for p in story["posts"]:
        v = nc.syndication(p["id"])
        if not v or not v.get("user"): p7.append(f"post {p['id']} could not be re-fetched from X (fail closed)"); continue
        if v["user"].lower() != str(p.get("user", "")).lower(): p7.append(f"post {p['id']} is by @{v['user']}, story file says @{p.get('user')}")
        if nc.norm(v["text"]) != nc.norm(p.get("text", "")): p7.append(f"story file text for post {p['id']} differs from X (tampered or edited)")
        srcs[p["id"]] = nc.norm(v["text"])
    alltext = " ".join(srcs.values())
    body = re.split(r"\n## Sources\n", md.split("\n---\n", 1)[-1])[0]
    for m in re.finditer(r"<blockquote><p>(.*?)</p>(?:<cite>(.*?)</cite>)?</blockquote>", main_h, re.S):
        qt = nc.norm(visible(m.group(1))).strip('"\u201c\u201d '); cite = m.group(2) or ""
        ids = re.findall(r"/status/(\d+)", cite)
        if not ids: p7.append(f"blockquote without a cited post link: '{qt[:50]}'"); continue
        if ids[0] not in srcs: p7.append(f"blockquote cites unverified post {ids[0]}"); continue
        if nc.norm(qt) not in srcs[ids[0]]: p7.append(f"blockquote not verbatim in post {ids[0]}: '{qt[:60]}'")
    for qt in quoted(body.replace("\n>", "\n")) + quoted(pay["main"]["text"]) + quoted(cardtxt):
        if nc.norm(qt) not in alltext: p7.append(f"quoted phrase not in any cited post: '{qt[:60]}'")
    if not any(nc.norm(q) in alltext for q in quoted(pay["main"]["text"])):
        p7.append("main X post has no verbatim quoted phrase (3+ words, in quote marks) of the key claim")
    claim_txt = " ".join([spec["title"], spec["description"], spec.get("seo_title", ""), spec.get("seo_description", ""), re.sub(r"\]\([^)]*\)", "]", body), pay["main"]["text"], pay["main"].get("alt", ""), cardtxt])
    src_hits = num_hits(alltext); src_q = {}
    for q, n in src_hits: src_q.setdefault(n, set()).add(q)
    for q, n in num_hits(claim_txt):
        if n not in src_q: p7.append(f"figure '{n}' is not in any cited post")
        elif True in src_q[n] and False not in src_q[n] and not q: p7.append(f"figure '{n}' dropped the source's qualifier (~ or about)")
    for pid in set(re.findall(r"(?:x|twitter)\.com/\w+/status/(\d+)", md + page)):
        if pid not in srcs: p7.append(f"links post {pid}, which was not verified")
    G.check("G7 claims match cited posts", p7)
    # G8 secrets
    p8 = []; scan = {"post md": md, "page": page, "x payload": json.dumps(pay), "spec": json.dumps(spec)}
    for k, txt in scan.items():
        for pat in SECRET_PATTERNS:
            if re.search(pat, txt): p8.append(f"{k} matches secret pattern /{pat[:24]}/")
        for env in SECRET_ENVS:
            v = os.environ.get(env, "")
            if len(v) >= 12 and v in txt: p8.append(f"{k} contains the value of ${env}")
    G.check("G8 secrets", p8)
    # G9 SEO
    p9 = []
    if len(re.findall(r"<h1\b", page)) != 1: p9.append(f"{len(re.findall(r'<h1', page))} h1 tags")
    tt = re.search(r"<title>(.*?)</title>", page); tt = H.unescape(tt.group(1)) if tt else ""
    if not tt or len(tt) > 60: p9.append(f"title is {len(tt)} chars")
    dd = re.search(r'<meta name="description" content="([^"]*)"', page); dd = H.unescape(dd.group(1)) if dd else ""
    if not dd or len(dd) > 155: p9.append(f"description is {len(dd)} chars")
    if f'<link rel="canonical" href="{url}">' not in page: p9.append("canonical missing or wrong")
    if re.search(r"noindex", page, re.I): p9.append("noindex on page")
    for f, what in (("sitemap.xml", "sitemap"), ("feed.xml", "feed.xml"), ("blog/index.html", "blog index"), ("index.html", "homepage latest posts"), ("llms.txt", "llms.txt")):
        fp = os.path.join(a.dist, f)
        if not os.path.exists(fp) or (url if f in ("sitemap.xml", "feed.xml", "llms.txt") else f"/blog/{slug}/") not in open(fp, encoding="utf-8").read(): p9.append(f"not in {what}")
    lds = [json.loads(H.unescape(x)) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
    if not any(g.get("@type") == "Article" for d in lds for g in d.get("@graph", [d])): p9.append("no Article schema")
    tl = set(re.findall(r'href="/tips/([\w-]+)/"', main_h))
    if len([s for s in tl if os.path.exists(os.path.join(a.dist, "tips", s, "index.html"))]) < 2: p9.append("fewer than 2 links to existing tip pages")
    if "<h2" not in main_h: p9.append("no h2 subheads")
    cat = os.path.join(nc.ROOT, "catalog.json")   # tips-index listing catalog: must validate and list this post
    if os.path.exists(cat):
        r = __import__("subprocess").run([sys.executable, os.path.join(nc.ROOT, "catalog.py")], cwd=nc.ROOT, capture_output=True, text=True)
        if r.returncode: p9.append("catalog.py validation failed: " + (r.stdout + r.stderr).strip().splitlines()[-1][:120])
        elif f"/blog/{slug}/" not in open(cat, encoding="utf-8").read(): p9.append("post not registered in catalog.json")
    G.check("G9 seo", p9)
    # G10 X text
    p10 = []; mt = pay["main"]["text"]; xl = nc.xweight(mt)
    if not mt.strip(): p10.append("main post empty")
    if xl > 280: p10.append(f"main post weighs {xl} (twitter-text), limit 280")
    if URL_RE.search(mt): p10.append(f"main post has a link/domain '{URL_RE.search(mt).group(0)}'")
    if pay["reply"]["text"] != f"Full story + sources: {url}": p10.append("reply text is not the story-link reply")
    if len(pay["main"].get("alt", "")) > 1000 or not pay["main"].get("alt"): p10.append("alt text missing or > 1000 chars")
    G.check("G10 x text", p10)
    # G11 privacy / brand
    p11 = []
    for pat, what in ((r"landscape\s*specialists", "Landscape Specialists"), (r"\bgavin\b", "Gavin"), (r"[\w.+-]+@[\w-]+\.[\w.]+", "email address"), (r"\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b", "phone number")):
        if re.search(pat, vis + " " + " ".join(xtexts), re.I): p11.append(what)
    G.check("G11 privacy", p11)
    # G12 per-post hold (money / pricing / plans / usage limits / billing / policy)
    cfg = nc.config(); G.held = []
    if cfg["hold_money_policy"]:
        hay = " ".join([story.get("headline", ""), spec["title"], spec["description"], body, pay["main"]["text"], cardtxt] + [p.get("text", "") for p in story["posts"]])
        hits = sorted({m.group(0).lower() for m in HOLD_RE.finditer(hay)})
        if story.get("sensitive"): hits = ["story flagged sensitive"] + hits
        if hits and a.release: print(f"RELEASED G12 hold: manual release (publish.py --release); matched {', '.join(hits[:8])}")
        elif hits:
            G.held = hits; print(f"HOLD G12 money/plans/policy: matched {', '.join(hits[:10])} (switch: {cfg['_path']} hold_money_policy)")
        else: print("PASS G12 hold (no money/plans/policy terms)")
    else: print(f"OFF  G12 hold (hold_money_policy is false in {cfg['_path']})")
    return finish(G, a)

def exists_in(dist, loc):
    loc = loc.split("#")[0].split("?")[0]
    if loc in ("", "/"): return os.path.exists(os.path.join(dist, "index.html"))
    p = os.path.join(dist, loc.lstrip("/"))
    return os.path.isfile(p) or os.path.isfile(os.path.join(p, "index.html")) or os.path.isfile(p.rstrip("/") + ".html") or loc in ("/about",) and os.path.isfile(os.path.join(dist, "about.html"))

def finish(G, a):
    if getattr(G, "held", None) and not G.fails:
        print("GATE HELD: every check passed, but G12 holds this post for a manual release"); return nc.HELD
    if G.fails:
        print(f"GATE FAIL: {len(G.fails)} check(s) failed, publish blocked")
        if not a.no_log: nc.issue("gate", G.fails, a.date); print(f"logged to {nc.ISSUES}")
        return 1
    print("GATE PASS: all checks passed"); return 0

if __name__ == "__main__":
    sys.exit(main())
