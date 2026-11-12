"""Grok Bot tips hub and per-tip pages at /tips/ and /tips/<slug>/."""
import hashlib, json, os, re
import build as B
e = B.e; SITE = B.SITE; BRAND = B.BRAND

# Cache-bust tips.css without changing the global style.css version.
TVER = hashlib.sha1(open(os.path.join(B.ROOT, "static", "tips.css"), "rb").read()).hexdigest()[:10]
CSS = f'<link rel="stylesheet" href="/tips.css?v={TVER}">'
# Force the near-black / green tips palette even if a saved theme prefers light.
THEME_COLOR = '<meta name="theme-color" content="#05070D">'

# Copy is from /workspace/shared/nab-relaunch/x-drafts.md (QC-fixed, Nov 12 2026).
# Do not add claims, numbers, or stories that are not in that file.
TIPS = [
    {
        "slug": "talk-to-one-lead-bot",
        "title": "Talk to one lead bot",
        "seo_title": "Talk to one lead bot | NextAiBreakout",
        "meta": "I don't talk to my whole Grok Bot fleet. I talk to one lead bot, and it routes work to the specialists.",
        "tip": "I don't talk to my whole Grok Bot fleet. I talk to one lead bot, and it routes work to the specialists. If everyone can ping you, you just built a louder inbox. What's your lead bot actually in charge of?",
        "how": "I made one bot the only one I talk to. It routes work to specialist bots and brings the result back. Approvals, questions, and alerts go through that lead bot, not a pile of separate chats. I still own the yes or no.",
        "alt": "Placeholder. A screenshot will show the Grok Bot desktop with the bot list, the Chief of Staff lead-bot chat open, and one routing or handoff message, with private details redacted.",
        "slot": "A screenshot of the lead-bot chat and one routing line, private details redacted.",
        "section": "teams",
        "siblings": ["agent-to-agent-handoffs", "group-chat-per-project", "quality-checker-before-it-reaches-you"],
    },
    {
        "slug": "quality-checker-before-it-reaches-you",
        "title": "Quality Checker in front of you",
        "seo_title": "Quality Checker before it reaches you | NextAiBreakout",
        "meta": "Every bot's work goes through a Quality Checker bot before it reaches me. I don't want five versions of \"done.\" I want one reviewed answer.",
        "tip": "Every bot's work goes through a Quality Checker bot before it reaches me. I don't want five versions of \"done.\" I want one reviewed answer. Who reviews work before it gets to you?",
        "how": "I added a fleet-wide Quality Checker. Work from every bot, including the lead, gets reviewed there before I see it. Small issues get cleaned up in that pass. Real risks get held. The rules live in a shared file the checker follows.",
        "alt": "Placeholder. A compare card will show five bots, five dones on one side, and one checked result on the other. No numbers or photos of people.",
        "slot": "A compare card: five dones versus one checked result.",
        "section": "quality",
        "siblings": ["bot-drafts-checker-reviews", "before-after-proof", "drafts-only-approval"],
    },
    {
        "slug": "agent-to-agent-handoffs",
        "title": "Agent-to-agent handoffs",
        "seo_title": "Agent-to-agent handoffs | NextAiBreakout",
        "meta": "Specialists don't report to me. They hand work to each other with a clear output, and the lead bot brings me one result.",
        "tip": "Specialists don't report to me. They hand work to each other with a clear output, and the lead bot brings me one result. The point is fewer pings, not more bots. How do your bots pass work along?",
        "how": "Specialist bots hand work to each other with an agent-to-agent message and a clear finish line. I don't sit in every hop. The lead bot collects one combined summary, so I get a packet instead of a trail of half-updates.",
        "alt": "Placeholder. A screenshot will show an agent-to-agent message between two named specialist bots, with a short task handoff and a defined output, and no credentials or customer data.",
        "slot": "A screenshot of an agent-to-agent handoff with a defined output, private details redacted.",
        "section": "teams",
        "siblings": ["talk-to-one-lead-bot", "group-chat-per-project", "shared-skills-across-bots"],
    },
    {
        "slug": "drafts-only-approval",
        "title": "Drafts only, then I approve",
        "seo_title": "Drafts only, then I approve | NextAiBreakout",
        "meta": "Nothing posts, sends, or goes public until I approve it. Drafts only. That's the rule that lets me run a fleet without waking up to a surprise on my account.",
        "tip": "Nothing posts, sends, or goes public until I approve it. Drafts only. That's the rule that lets me run a fleet without waking up to a surprise on my account. What still goes out without you seeing it first?",
        "how": "The rule is simple: no posts, no emails, no DMs, no spends unless I've approved them. Bots write drafts. I say yes. Another bot saying \"it's ready\" is not approval. That sounds slow. It isn't. It just means I sleep.",
        "alt": "Placeholder. A quote card will read: Drafts only. I approve before anything posts or sends.",
        "slot": "A quote card of the drafts-only rule.",
        "section": "approvals",
        "siblings": ["approve-spend-and-credentials", "bot-drafts-checker-reviews", "scheduled-pack-and-gates"],
    },
    {
        "slug": "shared-skills-across-bots",
        "title": "Save working workflows as skills",
        "seo_title": "Shared skills across Grok Bots | NextAiBreakout",
        "meta": "When a workflow works, I save it as a skill and share it across bots so they don't reinvent the steps. A skill is a reusable playbook, not a prompt I retype every morning.",
        "tip": "When a workflow works, I save it as a skill and share it across bots so they don't reinvent the steps. A skill is a reusable playbook, not a prompt I retype every morning. What workflow would you save first?",
        "how": "When a multi-step workflow holds up, I save it as a skill and share it across the fleet. Same steps, same output shape, same stop-and-ask rules. New bots inherit the playbook instead of guessing. I update the skill when the tools change, and I drop the ones we stopped using.",
        "alt": "Placeholder. A screenshot will show a saved Grok Bot skill name and the first few steps of the playbook, with tokens, logins, and private paths redacted.",
        "slot": "A screenshot of a saved skill and its step list, private details redacted.",
        "section": "skills",
        "siblings": ["talk-to-one-lead-bot", "scripted-brand-cards", "agent-to-agent-handoffs"],
    },
    {
        "slug": "check-your-routine-timezone",
        "title": "Check the timezone on every routine",
        "seo_title": "Check your routine timezone | NextAiBreakout",
        "meta": "I had a routine on the wrong timezone. It quietly missed its slot, and I only noticed when the work didn't show up. Cron doesn't care what you meant. It cares what zone you set.",
        "tip": "I had a routine on the wrong timezone. It quietly missed its slot, and I only noticed when the work didn't show up. Cron doesn't care what you meant. It cares what zone you set. Have you checked the timezone on yours?",
        "how": "I assumed a routine was on my local time. It wasn't. The job ran late and missed the window. I fixed the zone, and now I read the timezone on every routine the way I'd read the prompt.",
        "alt": "Placeholder. A screenshot will show the Grok Bot routine edit screen with the timezone field in view. Prompt text that contains private instructions will be redacted.",
        "slot": "A screenshot of the routine timezone field, as it actually appears.",
        "section": "routines",
        "siblings": ["scheduled-pack-and-gates", "watch-usage-pause-routines", "drafts-only-approval"],
    },
    {
        "slug": "watch-usage-pause-routines",
        "title": "Watch usage, then pause routines",
        "seo_title": "Watch usage, then pause routines | NextAiBreakout",
        "meta": "Usage ran out and every routine failed at once. Now I watch the meter and pause routines before they all crash. A fleet is only useful if it's still running tomorrow.",
        "tip": "Usage ran out and every routine failed at once. Now I watch the meter and pause routines before they all crash. A fleet is only useful if it's still running tomorrow. How often do you check your usage?",
        "how": "The usage allowance ran out, and every scheduled run failed until I paused them. Now I check usage on purpose, and I pause routines when I'm close to the limit instead of waiting for a silent outage. A paused routine is better than a week of empty slots.",
        "alt": "Placeholder. A screenshot will show the Grok Bot usage or allowance screen as it actually looks, with no invented percentages or remaining hours.",
        "slot": "A screenshot of the usage or allowance screen, using only numbers that appear on that day.",
        "section": "routines",
        "siblings": ["check-your-routine-timezone", "scheduled-pack-and-gates", "drafts-only-approval"],
    },
    {
        "slug": "blabara-in-one-day",
        "title": "We built Blabara in one day",
        "seo_title": "We built Blabara in one day | NextAiBreakout",
        "meta": "On Oct 16, my brother Gavin and I built Blabara, an Android voice-dictation app, in one day with a team of Grok Bots. Not a slide deck. A real app, in a day.",
        "tip": "On Oct 16, my brother Gavin and I built Blabara, an Android voice-dictation app, in one day with a team of Grok Bots. Not a slide deck. A real app, in a day. What's the biggest thing you've actually finished with a bot team?",
        "how": "Oct 16, 2026. Gavin and I wanted a voice-dictation app for Android. We used a team of Grok Bots with clear roles, and we built Blabara in a day. That's still the clearest proof I have that a small, well-directed team beats a pile of unfocused chats.",
        "alt": "Placeholder. A number card will read 1 day, labeled Blabara, Android voice dictation, built with a Grok Bot team, Oct 16, 2026. No store ranking or download counts, and no photos of people.",
        "slot": "A number card: 1 day. Blabara, Android voice dictation. Built with a Grok Bot team, Oct 16, 2026.",
        "section": "builds",
        "siblings": ["talk-to-one-lead-bot", "group-chat-per-project", "shared-skills-across-bots"],
    },
    {
        "slug": "group-chat-per-project",
        "title": "One group chat per project",
        "seo_title": "One group chat per project | NextAiBreakout",
        "meta": "When bots share a project, I put them in one group chat with clear roles. One channel, one job, then close it when the work is done.",
        "tip": "When bots share a project, I put them in one group chat with clear roles. One channel, one job, then close it when the work is done. Otherwise handoffs get lost in separate threads. Do you keep a group chat per project?",
        "how": "For a shared project, the bots go in one group chat. Each one has a distinct role, and the lead bot coordinates. When the project ends, the channel closes. It cuts down on work getting dropped between separate threads.",
        "alt": "Placeholder. A screenshot will show a Grok Bot group chat with several named bots and visible roles, cropped to the member list and a short coordinating message from the lead bot, with private task text redacted.",
        "slot": "A screenshot of a project group chat and roles, private task text redacted.",
        "section": "teams",
        "siblings": ["talk-to-one-lead-bot", "agent-to-agent-handoffs", "blabara-in-one-day"],
    },
    {
        "slug": "before-after-proof",
        "title": "No fix without a before and after",
        "seo_title": "No fix without a before and after | NextAiBreakout",
        "meta": "No bug is fixed until it's proven with a before and after. A bot saying \"done\" isn't proof. Show me what it looked like, then show me what changed.",
        "tip": "No bug is fixed until it's proven with a before and after. A bot saying \"done\" isn't proof. Show me what it looked like, then show me what changed. What do you accept as proof that something is actually fixed?",
        "how": "If a bot says it fixed something, I want the before and the after. A screenshot, a failing case that now passes, something I can see. \"I fixed it\" without proof goes back. This has saved me from a lot of false dones.",
        "alt": "Placeholder. A before-and-after card will show 'Done.' on one side and before / after, side by side, on the other, titled No fix without proof. No invented metrics or photos of people.",
        "slot": "A before-and-after card: no fix without proof.",
        "section": "quality",
        "siblings": ["quality-checker-before-it-reaches-you", "bot-drafts-checker-reviews", "drafts-only-approval"],
    },
    {
        "slug": "approve-spend-and-credentials",
        "title": "One-tap approvals for spend and credentials",
        "seo_title": "Approve spend and credentials | NextAiBreakout",
        "meta": "Spending and credentials stay on a one-tap approval. I don't auto-allow those. A bot can draft the step. I still press the button.",
        "tip": "Spending and credentials stay on a one-tap approval. I don't auto-allow those. A bot can draft the step. I still press the button. What's the last thing you'd let a bot do without asking?",
        "how": "Payments, logins, and anything with credentials come back to me as an approval. I tap yes only when I recognize the action. I don't put passwords in the chat, and I don't pre-approve spend. That's how you keep a cloud computer from becoming a blank check.",
        "alt": "Placeholder. A screenshot will show a Grok Bot approval card for a payment, purchase, or sign-in step before anyone taps it, with amounts, account names, card digits, tokens, and passwords redacted.",
        "slot": "A screenshot of an approval card, with amounts and credentials redacted.",
        "section": "approvals",
        "siblings": ["drafts-only-approval", "scheduled-pack-and-gates", "quality-checker-before-it-reaches-you"],
    },
    {
        "slug": "bot-drafts-checker-reviews",
        "title": "Bot drafts the email, a checker reviews it",
        "seo_title": "Bot drafts, checker reviews | NextAiBreakout",
        "meta": "I had a bot build a daily email, then a checker bot review it before anything could go out. Fast draft, slow send. That's the only way I'd let a routine touch an audience.",
        "tip": "I had a bot build a daily email, then a checker bot review it before anything could go out. Fast draft, slow send. That's the only way I'd let a routine touch an audience. What would you let a bot draft, but never send alone?",
        "how": "A bot pulled the day's data and wrote the email. A checker reviewed it. Only then would it be allowed to go out, and only after I approved the send. Nothing went out on a bot's say-so alone. Fast draft, slow send.",
        "alt": "Placeholder. A compare card will read: Bot drafts the email, then Checker reviews. I approve the send. No subscriber counts or photos of people.",
        "slot": "A compare card: bot drafts the email; checker reviews; I approve the send.",
        "section": "quality",
        "siblings": ["quality-checker-before-it-reaches-you", "drafts-only-approval", "scheduled-pack-and-gates"],
    },
    {
        "slug": "scripted-brand-cards",
        "title": "Script the cards, don't redesign every post",
        "seo_title": "Scripted brand cards | NextAiBreakout",
        "meta": "I don't design a new image for every post. A script builds the cards in one brand style: gold on black, same type, no photos of people. Consistency beats a one-off graphic every time.",
        "tip": "I don't design a new image for every post. A script builds the cards in one brand style: gold on black, same type, no photos of people. Consistency beats a one-off graphic every time. How do you keep your visuals from drifting?",
        "how": "I used a script to render post cards in one style: gold (#F2C14E) on deep black (#05070D), Archivo, no photos of people. Same mark, same margins, a source line on the card. It kept the feed looking like one site, not a pile of random graphics.",
        "alt": "Placeholder. A quote card will read: One style. Every card. Subtext: Gold on black. Archivo. No photos of people.",
        "slot": "A quote card: one style, every card. Gold on black. Archivo. No photos of people.",
        "section": "skills",
        "siblings": ["shared-skills-across-bots", "before-after-proof", "drafts-only-approval"],
    },
    {
        "slug": "scheduled-pack-and-gates",
        "title": "A morning pack, then gates, then I approve",
        "seo_title": "A morning pack, then gates | NextAiBreakout",
        "meta": "I run a morning pack routine, then later gates that check the work before it can go out. Scheduled prompts are useful. Unattended publish is not.",
        "tip": "I run a morning pack routine, then later gates that check the work before it can go out. Scheduled prompts are useful. Unattended publish is not. When do you actually review what your routines produced?",
        "how": "The morning pack runs at 6:45 AM Edmonton time. Later gates check the work at fixed times before anything can go out. The routine writes the draft. The gates catch problems. I still approve. A schedule without a review window is just a way to publish mistakes on time.",
        "alt": "Placeholder. A screenshot will show the routines list or schedule view with the morning pack time visible at 6:45 AM, America/Edmonton / Alberta Time, and later gate routines at their fixed times, with prompt bodies redacted.",
        "slot": "A screenshot of the morning pack and later gates on the routines schedule, showing the real times on screen.",
        "section": "routines",
        "siblings": ["check-your-routine-timezone", "bot-drafts-checker-reviews", "drafts-only-approval"],
    },
]

SECTIONS = [
    ("teams", "Teams"),
    ("quality", "Quality"),
    ("approvals", "Approvals"),
    ("skills", "Skills"),
    ("routines", "Routines"),
    ("builds", "Builds"),
]

HUB_TITLE = "Grok Bot tips | NextAiBreakout"
HUB_H1 = "Grok Bot tips"
HUB_META = "Grok Bot tips from work I actually ran: a lead bot, a Quality Checker, drafts-only approval, and other practices from my own setup."
HUB_INTRO = "Grok Bot tips from work I actually ran. Each page has the tip, how I did it, and a slot for a real example when I have one."

BY_SLUG = {t["slug"]: t for t in TIPS}


def path_of(slug=None):
    return "/tips/" if slug is None else f"/tips/{slug}/"


def crumbs(*parts):
    bits = ['<a href="/">Home</a>']
    for label, href, last in parts:
        if last:
            bits.append(f'<span aria-current="page">{e(label)}</span>')
        else:
            bits.append(f'<a href="{e(href)}">{e(label)}</a>')
    return '<nav class="crumbs" aria-label="Breadcrumb">' + " / ".join(bits) + "</nav>"


def ld_breadcrumb(items):
    els = []
    for i, (name, url) in enumerate(items, 1):
        els.append({"@type": "ListItem", "position": i, "name": name, "item": url})
    return {"@type": "BreadcrumbList", "itemListElement": els}


def page(title, desc, path, extra, main, year):
    h = B.head(title, desc, path, "/", CSS + extra)
    h = h.replace("<html lang=\"en\">", "<html lang=\"en\" class=\"tips\">", 1)
    h = h.replace("<body>", "<body class=\"tips\">", 1)
    # Tips pages stay near-black; the existing light theme-color would be misleading here.
    h = re.sub(r'<meta name="theme-color"[^>]*>', "", h)
    h = h.replace("</head>", THEME_COLOR + "</head>", 1)
    return h + main + B.foot(year, "/") + "</body></html>"


def write(DIST, rel, s):
    p = os.path.join(DIST, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def article_ld(t, url):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "headline": t["title"],
                "name": t["title"],
                "description": t["meta"],
                "url": url,
                "author": {"@type": "Organization", "name": BRAND, "url": SITE + "/"},
                "publisher": {"@type": "Organization", "name": BRAND, "url": SITE + "/"},
                "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            },
            ld_breadcrumb([("Home", SITE + "/"), ("Tips", SITE + "/tips/"), (t["title"], url)]),
        ],
    }


def tip_page(t, year):
    url = SITE + path_of(t["slug"])
    sibs = [BY_SLUG[s] for s in t["siblings"] if s in BY_SLUG]
    more = "".join(f'<li><a href="{path_of(s["slug"])}">{e(s["title"])}</a></li>' for s in sibs)
    main = f"""<main class="prose tips-main">
{crumbs(("Tips", "/tips/", False), (t["title"], path_of(t["slug"]), True))}
<h1>{e(t["title"])}</h1>
<p class="tip-body">{e(t["tip"])}</p>
<figure class="tip-shot">
<div class="tip-shot-box" role="img" aria-label="{e(t["alt"])}"><strong>Example coming soon</strong>{e(t["slot"])}</div>
<figcaption>Example coming soon. {e(t["slot"])}</figcaption>
</figure>
<h2 class="how">How I did it</h2>
<p class="how-body">{e(t["how"])}</p>
<nav class="tip-more" aria-label="More tips">
<h2>More tips</h2>
<ul>{more}</ul>
<p><a class="back" href="/tips/">All tips</a></p>
</nav>
</main>"""
    extra = B.ld(article_ld(t, url))
    return page(t["seo_title"], t["meta"], path_of(t["slug"]), extra, main, year)


def hub_page(year):
    url = SITE + "/tips/"
    secs = []
    for key, label in SECTIONS:
        items = [t for t in TIPS if t["section"] == key]
        if not items:
            continue
        cards = []
        for t in items:
            # First sentence only, no new wording.
            first = re.split(r"(?<=\.)\s", t["tip"], 1)[0]
            cards.append(
                f'<li id="{e(t["slug"])}"><a class="tip-title" href="{path_of(t["slug"])}">{e(t["title"])}</a>'
                f"<p>{e(first)}</p></li>"
            )
        secs.append(f'<section class="tips-sec" aria-label="{e(label)}"><h2>{e(label)}</h2><ul class="tip-cards">{"".join(cards)}</ul></section>')
    # Jump links should also include every tip anchor, as required.
    tip_jumps = "".join(f'<a href="#{e(t["slug"])}">{e(t["title"])}</a>' for t in TIPS)
    item_list = {
        "@type": "ItemList",
        "name": "Grok Bot tips",
        "itemListOrder": "https://schema.org/ItemListOrderAscending",
        "numberOfItems": len(TIPS),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": t["title"], "url": SITE + path_of(t["slug"])}
            for i, t in enumerate(TIPS, 1)
        ],
    }
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "Grok Bot tips", "url": url, "description": HUB_META, "mainEntity": {"@id": url + "#list"}},
            dict(item_list, **{"@id": url + "#list"}),
            ld_breadcrumb([("Home", SITE + "/"), ("Tips", url)]),
        ],
    }
    main = f"""<main class="prose tips-main">
{crumbs(("Tips", "/tips/", True))}
<h1>{e(HUB_H1)}</h1>
<p class="lede">{e(HUB_INTRO)}</p>
<nav class="tips-jump" aria-label="All tips">{tip_jumps}</nav>
{"".join(secs)}
</main>"""
    return page(HUB_TITLE, HUB_META, "/tips/", B.ld(graph), main, year)


def apply(DIST, t):
    year = t.year
    write(DIST, "tips/index.html", hub_page(year))
    for tip in TIPS:
        write(DIST, f"tips/{tip['slug']}/index.html", tip_page(tip, year))
    # sitemap + llms
    sp = os.path.join(DIST, "sitemap.xml")
    s = open(sp, encoding="utf-8").read()
    day = "2026-11-12"  # drafts written this day; not a fake "updated" date
    urls = [("/tips/", day, "weekly")] + [(path_of(tip["slug"]), day, "monthly") for tip in TIPS]
    s = s.replace("</urlset>", "".join(
        f"<url><loc>{SITE}{u}</loc><lastmod>{d}</lastmod><changefreq>{c}</changefreq></url>" for u, d, c in urls
    ) + "</urlset>", 1)
    open(sp, "w", encoding="utf-8").write(s)
    lp = os.path.join(DIST, "llms.txt")
    block = "\n## Tips\n" + f"- [Grok Bot tips]({SITE}/tips/)\n" + "".join(
        f"- [{tip['title']}]({SITE}{path_of(tip['slug'])}): {tip['meta']}\n" for tip in TIPS
    )
    open(lp, "a", encoding="utf-8").write(block)
    # copy scoped stylesheet
    import shutil
    shutil.copy(os.path.join(B.ROOT, "static", "tips.css"), os.path.join(DIST, "tips.css"))
    print(f"[tips] hub + {len(TIPS)} tip pages")


if __name__ == "__main__":
    apply("dist", __import__("datetime").date(2026, 11, 12))
