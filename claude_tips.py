"""Claude Tips with their own pages at /claude/<slug>/.

Each tip is the same loop: a Grok Bot writes the brief, I paste it into Claude, Claude builds or reviews,
then my Grok Bots verify and research. Every example is a redacted excerpt of a real handoff file.
Sources and redactions: /workspace/qc-nab-motion/claude-tips/README.md. Same page parts as the Grok tips
(tips.py): hook, card, How I did it, pros and cons, Copy this prompt.
"""
import build as B
import tips as T

e = B.e
SITE = B.SITE
BRAND = B.BRAND

CLAUDE_TIPS = [
    {
        "slug": "grok-writes-the-claude-brief",
        "ex_note": "Cut down from the brief my lead bot wrote. Words in square brackets replace client details, links and file names. [...] marks lines I cut.",
        "title": "Have your Grok Bot write the Claude prompt",
        "seo_title": "Have your Grok Bot write the Claude prompt | NextAiBreakout",
        "meta": "My Grok Bot writes my Claude prompts, paste-ready, with a How to verify list for each fix and one line up top: keep everything else exactly as it is.",
        "tip": "Stop writing Claude prompts from scratch. My Grok Bot writes them for me, ready to paste, and I paste them into Claude. One of them asked for two fixes on my company site, gave each fix its own How to verify list, and opened with one line: please keep everything else exactly as it is. What would your bot put in that first line?",
        "how": """My Grok Bots already had the details. A public data feed on my company site carried map locations more precise than the homepage map needed. So instead of me explaining that to Claude, my lead bot wrote the brief and handed it to me with one instruction: paste everything below the line.

The brief has a simple shape. One line on what we're fixing and why, then the guard rail: keep everything else exactly as it is, same look, same numbers. Each fix says where the problem is, what I want (a best option and a second best), and a numbered How to verify list I can check myself. It asks Claude to list anything it isn't sure about instead of guessing, and to tell me what changed.

Both fixes in that brief went live, the map change and a "Concept render" tag on every AI picture. My bot then checked them on the live site, and that part is its own tip.""",
        "alt": "Redacted excerpt of a real Claude brief my Grok Bot wrote: two fixes, each with a How to verify list.",
        "caption": "A real brief my bot wrote, redacted. Client details are swapped for stand-ins in brackets.",
        "siblings": ["claude-and-grok-check-each-other", "diff-claude-code-before-it-ships", "proof-standard-in-the-claude-brief"],
        "grok_links": [("talk-to-one-lead-bot", "Talk to one lead bot"), ("agent-to-agent-handoffs", "")],
        "pros": [
            "I don't have to explain the problem twice. The bot that found it writes it up.",
            "Claude gets a clear scope and a test for every fix.",
            "The How to verify list doubles as my checklist when the work comes back.",
        ],
        "cons": [
            "I still read every brief before I paste it, so it isn't hands-off.",
            "If the bot misreads the problem, Claude builds the wrong fix carefully.",
        ],
        "prompts": [
            {"note": "For your Grok Bot.", "text": "Write me a brief I can paste straight into Claude. Start with one line on what we're fixing and why, then: \"Please keep everything else exactly as it is.\" For each fix, say where the problem is, what you want (a best option and a second best), and a numbered How to verify list I can check myself. Ask Claude to list anything it isn't sure about instead of guessing, and to tell me what changed. Leave out passwords, keys and customer details. Show me the brief before I paste it."},
        ],
    },
    {
        "slug": "claude-and-grok-check-each-other",
        "ex_note": "Lines from three files: Claude's review, my Grok Bot's research, and Claude's next version. Words in square brackets replace city rules, names, dates and links.",
        "title": "Use Claude and Grok to check each other",
        "seo_title": "Use Claude and Grok to check each other | NextAiBreakout",
        "meta": "Claude listed 15 claims in my blog plan with no source yet. My Grok Bot checked each against official sources and found 7 things to fix first.",
        "tip": "Claude listed 15 claims in my company's winter blog plan that had no source yet. My Grok Bot checked every one against official sources and came back with 7 items marked Read first. One was a city rule a whole post was built on, and it had been put on hold. Let each one check the other.",
        "how": """The plan's files show who did what.

Claude reviewed the plan first. It added a writing standard and a numbered list, G1 to G15, of every claim it couldn't source yet: the claim, which post uses it, and where to look. The rule above that list is the part I'd copy: any claim on the list stays out until Grok returns a source.

My Grok Bot took the list. Official sources only, no blogs or forums, quotes word for word with the page. It put the contradictions at the top under Read first. The biggest: a new city rule one post was built around had been paused, so the post couldn't say it starts on that date.

Then Claude wrote the next version with those answers folded in. It moved that post and rescoped it, and it confirmed the pause on its own through news coverage.""",
        "alt": "Redacted excerpts: Claude's list of claims to confirm, Grok's Read first contradictions, and Claude's next version.",
        "caption": "Three real files from one plan, redacted. City rules, names and links are swapped for stand-ins.",
        "siblings": ["grok-writes-the-claude-brief", "diff-claude-code-before-it-ships", "proof-standard-in-the-claude-brief"],
        "grok_links": [("quality-checker-before-it-reaches-you", "Put a Quality Checker before it reaches you"), ("before-after-proof", "No fix without proof")],
        "pros": [
            "Claims without a source get caught before anyone writes around them.",
            "Each model checks the other's work instead of grading its own.",
            "The numbered list makes it obvious what's still unanswered.",
        ],
        "cons": [
            "It's slower: a plan goes through at least three versions.",
            "Official pages change, so a checked fact can still go stale before the post goes up.",
        ],
        "prompts": [
            {"note": "For Claude, with the plan.", "text": "Review this plan. Keep what works. Then list every claim that doesn't have a source yet in a numbered table: the claim, which part uses it, and where to look. Add one rule above the table: any claim on this list stays out of the writing until it has a source."},
            {"note": "For your Grok Bot, with Claude's list.", "text": "Check each numbered claim on this list against official sources only, no blogs or forums. For each one, give the answer, a word-for-word quote, the link and page, and how confident you are. Put anything that contradicts the plan at the top under \"Read first\". Don't publish or change anything."},
        ],
    },
    {
        "slug": "diff-claude-code-before-it-ships",
        "ex_note": "Part of the real diff between the code that was live and Claude's file. Words in square brackets replace paths. [...] marks lines I cut.",
        "title": "Diff Claude's code against live before it ships",
        "seo_title": "Diff Claude's code against live first | NextAiBreakout",
        "meta": "Claude's fix was merged but never went live. My Grok Bot caught it on the live feed, diffed Claude's file against the live code, then deployed and checked.",
        "tip": "Don't take \"deployed\" on trust, from any AI. Claude's map fix for my company site was merged, but the live feed still had location data more precise than the homepage needed. My Grok Bot caught that on the live data, diffed Claude's file against the code that was actually running, and only then deployed it.",
        "how": """Claude had written the fix from my lead bot's brief, but the merge only updated the main site. The part that served the feed deploys separately, and Claude's connection couldn't reach it. Claude said so itself. My Grok Bot, which can deploy there, checked the live feed and saw the old data still in it.

So the bot took over the deploy, in this order. Back up what's live. Diff Claude's file against the live code. Apart from the file's wrapper, the diff touched only the map points and the lock on a refresh link anyone could call, so it was safe to ship. Deploy. Then check the live result against the brief's How to verify list.

After the deploy, every map point had 2 decimal places or fewer, and the refresh link turned away anyone not signed in. The dashboard numbers were exactly the same as before. One thing didn't match the brief: Claude's neighbourhood-centre lookup didn't work, so pins are rounded instead. My bot put that in its report.""",
        "alt": "Redacted excerpt of the real diff between the live code and Claude's file, showing only the map and refresh changes.",
        "caption": "The real diff, redacted. Paths and data are swapped for stand-ins in brackets.",
        "siblings": ["grok-writes-the-claude-brief", "claude-and-grok-check-each-other", "proof-standard-in-the-claude-brief"],
        "grok_links": [("baseline-before-site-changes", "Save a baseline before you change the site"), ("isolate-the-app-repo", "Keep one repo off-limits to the rest of the fleet")],
        "pros": [
            "Nothing ships that I didn't ask for, because the diff shows every line.",
            "The live check caught a fix that was merged but not running.",
            "With a backup first, rolling back is one step.",
        ],
        "cons": [
            "The bot doing the deploy needs access, so that access has to be scoped and approved.",
            "A clean diff shows what changed, not that it works. The live check still matters.",
        ],
        "prompts": [
            {"note": "For your Grok Bot.", "text": "Before you deploy code Claude wrote, back up what's live, then diff Claude's file against the live version, not against your own copy. If the diff touches anything beyond the fix I asked for, stop and show me. After you deploy, check the live result yourself against the brief's How to verify list, confirm that numbers which shouldn't change didn't, and tell me anything that doesn't match the brief. Tell me how to roll back."},
        ],
    },
    {
        "slug": "proof-standard-in-the-claude-brief",
        "ex_note": "Cut down from the brief my lead bot wrote. Words in square brackets replace model names, the rival app and technical detail. The proof rule is word for word.",
        "title": "Put the proof standard in the Claude brief",
        "seo_title": "Put the proof standard in the Claude brief | NextAiBreakout",
        "meta": "My Claude brief for an app speed fix ends with the proof rule: before-and-after timings on a real phone, or it's \"speed-up attempted, not verified.\"",
        "tip": "Tell Claude what counts as proof before it writes a line of code. My brief for a speed fix in our app ends with the rule: the same 3 clips, timed on a real phone, old build against new, with the numbers shown. Until then, it's called \"speed-up attempted, not verified.\"",
        "how": """My lead bot wrote the brief for the Blabara app my brother and I built. It's short: a goal, what we saw in an older copy of the code (with a note to check it against the current build), two fixes in the order to do them, and then the proof rule.

The proof rule says exactly what to measure (time from releasing the button to text appearing), where (a real phone), against what (the old build), and with which inputs (the same 3 clips: short, medium, and one using the Rephrase style). Until all of that is shown, the fix keeps the label "attempted, not verified."

Claude checked the brief against the live code and pushed back. Two of the optional items were already in the app, and the smaller fix, as written, would have cost quality, so it suggested a different plan. It kept the proof rule as is, and offered to add one release-to-text timing to the app's log so the old and new builds can be compared directly. My bot agreed Claude's plan beat its own.

It's the same rule my brother and I set for every bug: nothing is fixed until the exact example fails on the old build and passes on the new one.""",
        "alt": "Redacted excerpt of a real Claude brief that ends with a proof rule for a speed fix.",
        "caption": "A real brief, redacted. Model names and the rival app are swapped for stand-ins.",
        "siblings": ["grok-writes-the-claude-brief", "claude-and-grok-check-each-other", "diff-claude-code-before-it-ships"],
        "grok_links": [("before-after-proof", "No fix without proof"), ("blabara-in-one-day", "How we built Blabara in one day")],
        "pros": [
            "\"Faster\" means a number on a real phone, not a feeling.",
            "Claude knows the finish line before it starts.",
            "The label stops anyone, bot or person, from calling it fixed too early.",
        ],
        "cons": [
            "Timing on a real phone takes someone's time, so proof is slower than a claim.",
            "Three clips can miss a case that only shows up on other phones.",
        ],
        "prompts": [
            {"note": "Add to the end of any Claude brief.", "text": "Proof required before calling this fixed: [what to measure], on [the real device or live site], on the old version and the new one, with the same [test inputs], and the numbers shown side by side. Until then, call it \"attempted, not verified.\" If you couldn't build or test something, say so at the top of your reply."},
        ],
    },
]

BY_SLUG = {t["slug"]: t for t in CLAUDE_TIPS}

# The loop every Claude tip follows, and the "when I reach for Claude" list (ia.md section 5, draft for Ryan).
LOOP_STEPS = [
    ("A Grok Bot writes the brief.", "/claude/grok-writes-the-claude-brief/"),
    ("I paste it into Claude, and Claude builds or reviews.", None),
    ("My Grok Bots research what Claude couldn't source.", "/claude/claude-and-grok-check-each-other/"),
    ("My Grok Bots check Claude's code against live before and after it ships.", "/claude/diff-claude-code-before-it-ships/"),
]
REACH_FOR_CLAUDE = [
    "When code needs writing or reviewing. One of my Grok Bots writes the brief, and I paste it in.",
    "When a plan needs a second reader. Claude reviews it and lists every claim without a source for a Grok Bot to check.",
    "When a site needs a redesign. Claude redesigned this site and left a design guide my site bot reads before it adds a page.",
    "When the Blabara app needs building. Claude works in the app's own repo, and my Grok Bots coordinate around it.",
]


def _grok_title(slug):
    for x in list(T.TIPS) + list(T.HUB_ONLY):
        if x["slug"] == slug:
            return x["title"]
    raise KeyError(f"unknown Grok tip {slug}")


def excerpt(slug):
    import os
    return open(os.path.join(B.ROOT, "claude_excerpts", slug + ".txt"), encoding="utf-8").read().rstrip("\n")


def excerpt_block(t):
    return (
        '<section class="claude-ex" aria-labelledby="claude-ex-h">'
        '<h2 id="claude-ex-h">The real file, redacted</h2>'
        f'<p>{e(t["ex_note"])}</p>'
        f'<pre tabindex="0">{e(excerpt(t["slug"]))}</pre>'
        "</section>"
    )


def path_of(slug):
    return f"/claude/{slug}/"


def pros_cons_block(t):
    if not (2 <= len(t["pros"]) <= 4 and 2 <= len(t["cons"]) <= 3):
        raise ValueError(f"pros/cons count out of range for {t['slug']}")
    pros = "".join(f"<li>{e(x)}</li>" for x in t["pros"])
    cons = "".join(f"<li>{e(x)}</li>" for x in t["cons"])
    return (
        '<section class="pros-cons" id="pros-cons" aria-labelledby="pros-cons-heading">'
        '<h2 id="pros-cons-heading">Pros and cons</h2>'
        f"<h3>Pros</h3><ul>{pros}</ul><h3>Cons</h3><ul>{cons}</ul></section>"
    )


def prompt_blocks(t):
    bits = []
    for i, item in enumerate(t["prompts"], 1):
        pid = "copy-prompt" if i == 1 else f"copy-prompt-{i}"
        bits.append(T.prompt_block(item["text"], pid, item.get("note")))
    bits.append(T.COPY_PROMPT_JS)
    return "".join(bits)


def date_html(slug):
    import catalog as C
    row = C.by_id(slug)
    return f'<time class="vh" datetime="{e(row["date"])}"></time>' if row else ""


def article_ld(t, url):
    import catalog as C
    row = C.by_id(t["slug"]) or {}
    art = {
        "@type": "Article",
        "headline": t["title"],
        "name": t["title"],
        "description": t["meta"],
        "url": url,
        "image": f"{SITE}/images/claude/{t['slug']}-og.jpg",
        "author": {"@type": "Organization", "name": BRAND, "url": SITE + "/"},
        "publisher": {"@type": "Organization", "name": BRAND, "url": SITE + "/"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }
    if row.get("date"):
        art["datePublished"] = row["date"]
    return {
        "@context": "https://schema.org",
        "@graph": [art, T.ld_breadcrumb([("Home", SITE + "/"), ("Claude Tips", SITE + "/claude/"), (t["title"], url)])],
    }


def tip_page(t, year):
    url = SITE + path_of(t["slug"])
    sibs = "".join(f'<li><a href="{path_of(s)}">{e(BY_SLUG[s]["title"])}</a></li>' for s in t["siblings"] if s in BY_SLUG)
    grok = "".join(
        f'<li><a href="{"/tips/" + s + "/" if s in T.BY_SLUG else "/tips/#" + s}">{e(label)}</a></li>'
        for s, label in [(s, _grok_title(s)) for s, _ in t["grok_links"]]
    )
    main = f"""<main class="prose tips-main">
{T.crumbs(("Claude Tips", "/claude/", False), (t["title"], path_of(t["slug"]), True))}
{B.peek_h1(e(t["title"]), B.SPECIALIST_BOT)}
{date_html(t["slug"])}
{T.paras(t["tip"], "tip-body")}
<figure class="tip-shot">
<img src="/images/claude/{e(t["slug"])}.webp" width="1200" height="675" alt="{e(t["alt"])}">
<figcaption>{e(t["caption"])}</figcaption>
</figure>
<h2 class="how">How I did it</h2>
{T.paras(t["how"], "how-body")}
{excerpt_block(t)}
{pros_cons_block(t)}
{prompt_blocks(t)}
<nav class="tip-more" aria-label="More tips">
<h2>More Claude Tips</h2>
<ul>{sibs}</ul>
<h2>Related Grok Bot tips</h2>
<ul>{grok}</ul>
<p><a class="back" href="/claude/">See all Claude Tips</a></p>
</nav>
</main>"""
    html_page = T.page(t["seo_title"], t["meta"], path_of(t["slug"]), B.ld(article_ld(t, url)), main, year)
    html_page = html_page.replace(f'<meta property="og:image:alt" content="{e(B.OG_ALT)}">', f'<meta property="og:image:alt" content="{e(t["alt"])}">', 1)
    return html_page.replace(f"{SITE}{B.OG_DEFAULT}", f"{SITE}/images/claude/{t['slug']}-og.jpg")


def loop_html():
    steps = "".join(
        f'<li>{"<a href=" + chr(34) + href + chr(34) + ">" + e(txt) + "</a>" if href else e(txt)}</li>' for txt, href in LOOP_STEPS
    )
    reach = "".join(f"<li>{e(x)}</li>" for x in REACH_FOR_CLAUDE)
    return (
        '<h2>How I use Claude with my Grok Bots</h2>'
        "<p>I don't pick one or the other. Claude and my Grok Bots work the same job in a loop.</p>"
        f'<ol class="claude-loop">{steps}</ol>'
        '<h2>When I reach for Claude</h2>'
        f"<ul>{reach}</ul>"
        "<p>The check on the live site after a deploy stays with my Grok Bots.</p>"
    )


def apply(DIST, t):
    import os
    import catalog as C
    cat_ids = {r["id"] for r in C.filter_entries(kind="claude", type="tip") if r["url"].startswith("/claude/")}
    src_ids = set(BY_SLUG)
    if cat_ids != src_ids:
        raise SystemExit(f"catalog claude tips out of sync with claude_tips.py: missing {sorted(src_ids - cat_ids)} extra {sorted(cat_ids - src_ids)}")
    for tip in CLAUDE_TIPS:
        T.write(DIST, f"claude/{tip['slug']}/index.html", tip_page(tip, t.year))
    sp = os.path.join(DIST, "sitemap.xml")
    s = open(sp, encoding="utf-8").read()
    s = s.replace("</urlset>", "".join(
        f"<url><loc>{SITE}{path_of(x['slug'])}</loc><lastmod>{C.by_id(x['slug'])['date']}</lastmod><changefreq>monthly</changefreq></url>"
        for x in CLAUDE_TIPS
    ) + "</urlset>", 1)
    open(sp, "w", encoding="utf-8").write(s)
    with open(os.path.join(DIST, "llms.txt"), "a", encoding="utf-8") as f:
        f.write("\n## Claude Tips\n" + "".join(f"- [{x['title']}]({SITE}{path_of(x['slug'])}): {x['meta']}\n" for x in CLAUDE_TIPS))
    print(f"[claude_tips] {len(CLAUDE_TIPS)} Claude tip pages")
