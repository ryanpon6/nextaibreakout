"""Claude Tips index at /claude/. Keeps the existing URL and the already-published notes."""
import os
import build as B
import catalog as C

e = B.e
SITE = B.SITE
BRAND = B.BRAND
PATH = "/claude/"
TITLE = "Claude Tips | NextAiBreakout"
H1 = "Claude Tips"
META = "Claude Tips I have published, including the Claude Code Android TV guide, and a note on a Landscape Specialists build. This site is Grok Bot first."


def apply(DIST, t):
    year = t.year
    url = SITE + PATH
    dated = C.filter_entries(kind="claude", type="tip")
    item_list = dict(C.item_list("Claude Tips", dated), **{"@id": url + "#list"})
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "name": "Claude Tips",
                "url": url,
                "description": META,
                "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE + "/"},
                "mainEntity": {"@id": url + "#list"},
            },
            item_list,
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Claude Tips", "item": url},
                ],
            },
        ],
    }
    n = len(dated)
    if n == 0:
        list_block = ""
        list_lede = "This site is Grok Bot first. I'm not going to mix both tools into every tip."
        # Rule 19: do not render an empty list. The existing notes on this page stay.
    elif n == 1:
        list_block = f'<h2 class="tips-index-h">The published tip</h2>\n{C.listing_html(dated, "tips-index")}'
        list_lede = "This site is Grok Bot first. I'm not going to mix both tools into every tip. Claude Tips is the list of Claude write-ups I have published."
    else:
        list_block = f'<h2 class="tips-index-h">All tips, newest first</h2>\n{C.listing_html(dated, "tips-index")}'
        list_lede = "This site is Grok Bot first. I'm not going to mix both tools into every tip. Claude Tips is the list of Claude write-ups I have published."
    # n==0 copy must not be a "coming soon". Today there is one published tip, so this branch will not render.
    # Keep it only so a future empty catalog does not emit an empty list.
    main = f"""<main class="prose">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">Claude Tips</span></nav>
{B.peek_h1(B.circ("Claude Tips."), B.SPECIALIST_BOT)}
<p>{e(list_lede)}</p>
{list_block}
<p>After the 16 Oct 2026 one-day Blabara build, website and Google Play setup continued with Grok and Claude. The one-day build itself is the one my brother and I did with a team of Grok Bots, not with Claude.</p>
<p>Claude is what builds the Blabara app in a separate repo, ryanpon6/voicekey-app. The Chief of Staff bot does not edit or push there.</p>
<h2>How this site was built</h2>
<p>Although I mostly use Claude for coding because it produces better results, I relied on Grok to help build this website. Once Grok creates the site and I add the final touches, I use Claude to refine the template and confirm the code structure is correct.</p>
<h2>A real build: my landscaping company's site</h2>
<p>Another example is the Landscape Specialists site, which was built with Claude. I have Claude connected to my GitHub, Cloudflare and everything else. It creates mockups for pictures and similar assets for me, and then I narrow them down or combine them to reach a finalized product.</p>
<figure>
<img src="/images/claude/landscape-specialists-home.webp" width="1200" height="750" alt="The Landscape Specialists homepage, built with Claude." loading="lazy">
<figcaption>The Landscape Specialists homepage, built with Claude.</figcaption>
</figure>
<p><a href="https://landscapespecialists.ca" rel="noopener" target="_blank">landscapespecialists.ca</a></p>
<p><a href="/tips/">See all Grok Bot tips</a></p>
</main>"""
    page = B.head(TITLE, META, PATH, "/", B.ld(graph)) + main + B.foot(year, "/") + "</body></html>"
    dest = os.path.join(DIST, "claude", "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(page)
    # sitemap: add /claude/ if the base build did not; lastmod is the newer of the page's first publish day and the newest listed tip.
    sp = os.path.join(DIST, "sitemap.xml")
    if os.path.isfile(sp):
        s = open(sp, encoding="utf-8").read()
        loc = f"<loc>{SITE}{PATH}</loc>"
        page_day = "2026-11-12"  # first published in commit 7e64428
        tip_day = C.newest_date(kind="claude", type="tip")
        day = max(d for d in (page_day, tip_day) if d)
        if loc not in s:
            s = s.replace(
                "</urlset>",
                f"<url><loc>{SITE}{PATH}</loc><lastmod>{day}</lastmod><changefreq>weekly</changefreq></url></urlset>",
                1,
            )
            open(sp, "w", encoding="utf-8").write(s)
        else:
            s = s.replace(
                f"<loc>{SITE}{PATH}</loc><lastmod>2026-11-12</lastmod><changefreq>monthly</changefreq>",
                f"<loc>{SITE}{PATH}</loc><lastmod>{day}</lastmod><changefreq>weekly</changefreq>",
                1,
            )
            open(sp, "w", encoding="utf-8").write(s)
    print(f"[claude] /claude/ ({n} tip{'' if n == 1 else 's'})")


if __name__ == "__main__":
    import datetime as _dt

    apply("dist", _dt.date(2026, 11, 12))
