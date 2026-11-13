"""Claude page at /claude/. Copy is from /workspace/shared/nab-relaunch/ia.md, facts only."""
import os
import build as B

e = B.e
SITE = B.SITE
BRAND = B.BRAND
PATH = "/claude/"
TITLE = "Claude notes | NextAiBreakout"
H1 = "Claude, on its own page."
# Mentions the Landscape Specialists build and the existing Android TV guide already on the site.
META = "This site is Grok Bot first. Claude has its own page, including a Landscape Specialists build and the existing Claude Code Android TV guide. Not a second tips hub."
BLOG = "/blog/claude-code-android-tv-debloat/"
BLOG_TITLE = "Claude Code Android TV Debloat: cleanyourtv Explained"


def apply(DIST, t):
    year = t.year
    url = SITE + PATH
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "name": H1,
                "url": url,
                "description": META,
                "isPartOf": {"@type": "WebSite", "name": BRAND, "url": SITE + "/"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Claude", "item": url},
                ],
            },
        ],
    }
    main = f"""<main class="prose">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <span aria-current="page">Claude</span></nav>
{B.peek_h1(B.circ("Claude,") + " on its own page.", B.SPECIALIST_BOT)}
<p>This site is Grok Bot first. I'm not going to mix both tools into every tip. Claude is a separate lane, and this is its page.</p>
<p>After the 16 Oct 2026 one-day Blabara build, website and Google Play setup continued with Grok and Claude. The one-day build itself is the one my brother and I did with a team of Grok Bots, not with Claude. I am not claiming Blabara is live on Google Play.</p>
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
<h2>A guide that's already on the site</h2>
<p>The one older guide already published here is about using Claude Code to debloat an Android TV, carefully. It covers a public repo, not a build I shipped, and it keeps the safety framing: what the method does, what it doesn't, and what to watch for.</p>
<p><a href="{BLOG}">{e(BLOG_TITLE)}</a></p>
<p><a href="/tips/">Back to Grok Bot tips</a></p>
</main>"""
    page = B.head(TITLE, META, PATH, "/", B.ld(graph)) + main + B.foot(year, "/") + "</body></html>"
    dest = os.path.join(DIST, "claude", "index.html")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(page)
    # sitemap: add /claude/ if the base build did not
    sp = os.path.join(DIST, "sitemap.xml")
    if os.path.isfile(sp):
        s = open(sp, encoding="utf-8").read()
        loc = f"<loc>{SITE}{PATH}</loc>"
        if loc not in s:
            day = "2026-11-12"
            s = s.replace(
                "</urlset>",
                f"<url><loc>{SITE}{PATH}</loc><lastmod>{day}</lastmod><changefreq>monthly</changefreq></url></urlset>",
                1,
            )
            open(sp, "w", encoding="utf-8").write(s)
    print("[claude] /claude/")


if __name__ == "__main__":
    import datetime as dt

    apply("dist", dt.date(2026, 11, 12))
