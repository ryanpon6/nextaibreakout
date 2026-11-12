"""Grok Bot tips hub and per-tip pages at /tips/ and /tips/<slug>/."""
import hashlib, json, os, re
import build as B
e = B.e; SITE = B.SITE; BRAND = B.BRAND

# Cache-bust tips.css without changing the global style.css version.
TVER = hashlib.sha1(open(os.path.join(B.ROOT, "static", "tips.css"), "rb").read()).hexdigest()[:10]
CSS = f'<link rel="stylesheet" href="/tips.css?v={TVER}">'
# Browser chrome follows the teal brand; CSS uses the same palette in light and dark themes.
THEME_COLOR = '<meta name="theme-color" content="#274043">'

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
        "alt": "Brand card quoting the lead-bot rule: talk to one lead bot, not the whole fleet.",
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
        "alt": "Brand card comparing five dones with one checked result.",
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
        "alt": "Brand card quoting the handoff rule: specialists hand work to each other with a clear output.",
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
        "alt": "Brand card quoting the drafts-only rule: I approve before anything posts or sends.",
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
        "alt": "Brand card quoting the skills rule: a skill is a reusable playbook, not a prompt I retype.",
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
        "alt": "Brand card quoting the timezone rule: cron cares what zone you set.",
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
        "alt": "Brand card quoting the usage rule: watch the meter and pause routines before they crash.",
        "slot": "A screenshot of the usage or allowance screen, using only numbers that appear on that day.",
        "section": "routines",
        "siblings": ["check-your-routine-timezone", "scheduled-pack-and-gates", "drafts-only-approval"],
    },
    {
        "slug": "blabara-in-one-day",
        "title": "We built Blabara in one day",
        "seo_title": "We built Blabara in one day | NextAiBreakout",
        "meta": "On Oct 16, my brother and I built Blabara, an Android voice-dictation app, in one day with a team of Grok Bots. Not a slide deck. A real app, in a day.",
        "tip": "On Oct 16, my brother and I built Blabara, an Android voice-dictation app, in one day with a team of Grok Bots. Not a slide deck. A real app, in a day. What's the biggest thing you've actually built with a bot team?",
        "how": "Oct 16, 2026. My brother and I wanted a voice-dictation app for Android. We used a team of Grok Bots with clear roles, and we built Blabara in a day. That's still the clearest proof I have that a small, well-directed team beats a pile of unfocused chats.",
        "alt": "Brand card with the number 1 day, labeled Blabara, Android voice dictation, built with a Grok Bot team on Oct 16, 2026.",
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
        "alt": "Brand card quoting the group-chat rule: one channel, one job, then close it when the work is done.",
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
        "alt": "Brand card comparing a bot saying 'Done.' with a before-and-after you can see.",
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
        "alt": "Brand card quoting the approval rule: a bot can draft the step, I still press the button.",
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
        "alt": "Brand card comparing a bot's say-so with a send I approve after a checker reviews it.",
        "slot": "A compare card: bot drafts the email; checker reviews; I approve the send.",
        "section": "quality",
        "siblings": ["quality-checker-before-it-reaches-you", "drafts-only-approval", "scheduled-pack-and-gates"],
    },
    {
        "slug": "scripted-brand-cards",
        "title": "Script the cards, don't redesign every post",
        "seo_title": "Scripted brand cards | NextAiBreakout",
        "meta": "I don't design a new image for every post. A script builds the cards in one brand style: yellow gold on teal, same type, no photos of people. Consistency beats a one-off graphic every time.",
        "tip": "I don't design a new image for every post. A script builds the cards in one brand style: yellow gold on teal, same type, no photos of people. Consistency beats a one-off graphic every time. How do you keep your visuals from drifting?",
        "how": "I used a script to render post cards in one style: yellow gold (#E0B84E) on Pacific Sea Teal (#274043), Archivo, no photos of people. Same mark, same margins, a source line on the card. It kept the feed looking like one site, not a pile of random graphics.",
        "alt": "Brand card quoting the visual rule: one style, every card, gold on teal, Archivo, no photos of people.",
        "slot": "A quote card: one style, every card. Yellow gold on teal. Archivo. No photos of people.",
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
        "alt": "Brand card quoting the scheduling rule: scheduled prompts are useful, unattended publish is not.",
        "slot": "A screenshot of the morning pack and later gates on the routines schedule, showing the real times on screen.",
        "section": "routines",
        "siblings": ["check-your-routine-timezone", "bot-drafts-checker-reviews", "drafts-only-approval"],
    },
]


# Site-only tips: live on the hub as #anchors, no standalone /tips/<slug>/ page.
# Copy is trimmed from pillar-guide.md seed outlines.
# Asset names, token savings, and proposed-but-not-live results are left out of public copy.
HUB_ONLY = [
    {
        "slug": "one-job-per-bot",
        "title": "Give every bot one job",
        "section": "job-descriptions",
        "tip": "One bot asked to market, code, and file invoices gets mushy. Give each bot one job.",
        "how": "The fleet has named specialists (research, site, marketing, checker, desks) instead of one generalist. Overlapping jobs create duplicate routines.",
        "alt": "Brand card quoting the job rule: give each bot one job.",
        "slot": "A job-description screen, once a redacted example is ready.",
    },
    {
        "slug": "write-down-checker-rules",
        "title": "Write the checker's rules down, and add one for every miss",
        "section": "quality",
        "tip": "The same mistake slipping through twice is the problem: a wrong sign-off, an invented figure, or an unproven \"fixed.\"",
        "how": "The checker's rules live in a shared file, with a regression pack. Named rules get dates and examples. No invented figures. No bug is \"fixed\" without before-and-after proof. Don't paste other people's email addresses or private misses onto a public page.",
        "alt": "Brand card quoting the checker-rules rule: write the rules down, and add one for every miss.",
        "slot": "A snippet of the rules file, no private addresses.",
    },
    {
        "slug": "isolate-the-app-repo",
        "title": "Keep one repo off-limits to the rest of the fleet",
        "section": "teams",
        "tip": "Two bots pushing to the same app repo is the problem this is meant to stop.",
        "how": "A decision on 24 Oct 2026 split the work: Claude builds the Blabara app in its own repo. Chief of Staff and the Voice Keyboard Builder don't edit or push there. The Grok Bot fleet handles coordination and other work. This is a process split, not a claim about Claude versus Grok quality.",
        "alt": "Brand card quoting the access rule: keep one repo off-limits to the rest of the fleet.",
        "slot": "A redacted access or handoff note, once one is ready to publish.",
    },
    {
        "slug": "change-only-watches",
        "title": "Stay quiet unless something changed",
        "section": "routines",
        "tip": "Scheduled bots waking dozens of times a week to say nothing changed is wasted work. Silence is the correct output when nothing changed.",
        "how": "Change-only scripts do the watch, with no model in the loop: exit quietly when nothing happened, and only speak when there is an alert. The model is not woken for a \"no change\" line. Don't publish thresholds.",
        "alt": "Brand card quoting the quiet-watch rule: silence is the correct output when nothing changed.",
        "slot": "A redacted quiet-exit versus alert example, with no levels, sizes, or wallet data.",
    },
    {
        "slug": "script-before-model",
        "title": "Prefer a script over a model when the job is deterministic",
        "section": "usage",
        "tip": "Don't pay for a model wake to diff a list, check a price, or filter an inbox when a script can do that job.",
        "how": "The pattern is a change-only script: exit quietly when nothing happened, and print the message only when there is something to say. Don't claim those routines are already running, and don't treat a second model vendor as the first move.",
        "alt": "Brand card quoting the script-first rule: prefer a script over a model when the job is deterministic.",
        "slot": "A redacted dry-run of a quiet exit versus a message exit.",
    },
    {
        "slug": "human-publish-gate",
        "title": "Put a human publish gate in front of the website",
        "section": "safety",
        "tip": "Unreviewed auto content, including CJK text and unverified ranking blurbs, reached the NAB homepage and daily pages in early November 2026. Ryan stopped sends and publishes.",
        "how": "A structural publish gate is proposed, not live: builds would come only from reviewed markdown, checks would catch CJK unless it is allowlisted, empty descriptions, and a missing review stamp, and nothing would deploy without Ryan's OK. That result is not in place yet, so it is not written here as if it already shipped. 404-ing old daily pages is not the same as a gate.",
        "alt": "Brand card quoting the publish rule: put a human publish gate in front of the website.",
        "slot": "A selfcheck failure example, and a redacted before-shot if one can be published.",
    },
]

SECTIONS = [
    ("teams", "Teams"),
    ("job-descriptions", "Job descriptions"),
    ("quality", "Quality"),
    ("approvals", "Approvals"),
    ("skills", "Skills"),
    ("routines", "Routines"),
    ("usage", "Usage"),
    ("builds", "Builds"),
    ("safety", "Safety"),
]

HUB_TITLE = "Grok Bot tips | NextAiBreakout"
HUB_H1 = "Grok Bot tips"
HUB_META = "Grok Bot tips from work I actually ran: a lead bot, a Quality Checker, drafts-only approval, and other practices from my own setup."
HUB_INTRO = "Grok Bot tips from work I actually ran. Fourteen have their own page, with the tip, how I did it, and a brand card for each one. Six more live on this page until they have a full write-up."

BY_SLUG = {t["slug"]: t for t in TIPS}

CAPTIONS = {
    "talk-to-one-lead-bot": 'The lead-bot rule, as a brand card.',
    "quality-checker-before-it-reaches-you": 'Five dones versus one checked result.',
    "agent-to-agent-handoffs": 'The agent-to-agent handoff rule, as a brand card.',
    "drafts-only-approval": 'The drafts-only rule, as a brand card.',
    "shared-skills-across-bots": 'The reusable-skills rule, as a brand card.',
    "check-your-routine-timezone": 'The routine timezone rule, as a brand card.',
    "watch-usage-pause-routines": 'The usage-and-pause rule, as a brand card.',
    "blabara-in-one-day": 'Blabara built in one day, as a brand card.',
    "group-chat-per-project": 'The one-group-chat-per-project rule, as a brand card.',
    "before-after-proof": 'No fix without proof, as a brand card.',
    "approve-spend-and-credentials": 'The spend-and-credentials approval rule, as a brand card.',
    "bot-drafts-checker-reviews": 'Bot drafts, checker reviews, I approve the send.',
    "scripted-brand-cards": 'One style, every card.',
    "scheduled-pack-and-gates": 'The scheduled-pack-and-gates rule, as a brand card.',
    "one-job-per-bot": 'The one-job-per-bot rule, as a brand card.',
    "write-down-checker-rules": 'The written-checker-rules rule, as a brand card.',
    "isolate-the-app-repo": 'The isolated-repo rule, as a brand card.',
    "change-only-watches": 'The change-only watch rule, as a brand card.',
    "script-before-model": 'The script-before-model rule, as a brand card.',
    "human-publish-gate": 'The human publish gate, as a brand card.',
}



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
    # Tips pages stay teal; replace the global theme-color tags with the brand swatch.
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



# Copyable setup prompts for tips that recommend a bot, routine, or checker.
# Day 1 text is verbatim. Other drafts stay faithful to that tip; see /workspace/shared/nab-relaunch/tip-prompts.md.
PROMPTS = {
    'talk-to-one-lead-bot': [
        {'text': "You are my Chief of Staff and the only bot I talk to first. Take whatever I ask (business, ideas, research or anything else) and turn it into a clear goal, who owns it, and the next step. Keep unrelated topics in separate threads and never mix them in one answer. When one area gets deep enough, suggest a focused specialist bot, ask me before creating it, give it only the brief it needs, and stay the coordinator. Get facts from live sources, not memory; use memory for my preferences and how I like to work. Never send messages, post, spend money, delete anything or change permissions without my explicit OK. If a tool is missing, tell me what to connect. If you're blocked, stop and ask. Keep replies short and lead with the answer."},
    ],
    'quality-checker-before-it-reaches-you': [
        {'text': 'You are my Quality Checker. Every bot\'s work, including the lead bot\'s, comes to you before it reaches me. I don\'t want five versions of "done." I want one reviewed answer. Follow the rules in the shared file I give you. Clean up small issues in that pass. Hold real risks and do not send those through to me as finished work. You are a reviewer, not the one who publishes or sends.'},
    ],
    'agent-to-agent-handoffs': [
        {'text': 'You are a specialist bot. You do not report to me on every hop. When you finish your part, hand the work to the next specialist with an agent-to-agent message and a clear finish line — what you did, and what they need to do next. Do not leave a trail of half-updates for me. The lead bot will collect one combined summary and bring me the result.'},
    ],
    'drafts-only-approval': [
        {'text': 'Nothing you write may post, send, go out as a DM or email, or spend money unless I have approved it. Drafts only. Write the draft and wait. Another bot saying "it\'s ready" is not approval. My yes is the only approval.'},
    ],
    'group-chat-per-project': [
        {'text': 'You are the lead bot in this project group chat. Every bot in this channel has a distinct role. You coordinate the work here, in this one channel, not across a pile of separate threads. When the project is done, say so and remind me to close the channel. Do not let handoffs get lost.'},
    ],
    'before-after-proof': [
        {'text': 'Do not call a bug or problem fixed until you can prove it with a before and after. "I fixed it" or "done" is not proof. Show me what it looked like, then show me what changed — a screenshot, a failing case that now passes, or something else I can see. If you cannot show that, the work goes back; it is not done.'},
    ],
    'approve-spend-and-credentials': [
        {'text': 'Spending and credentials stay on a one-tap approval from me. You may draft the step. I still press the button. Payments, logins, and anything with credentials come back to me as an approval. Do not put passwords in the chat. Do not treat spend as pre-approved. Do not go ahead on those until I tap yes on an action I recognize.'},
    ],
    'bot-drafts-checker-reviews': [
        {'note': 'For the draft bot.', 'text': "You pull the day's data and write the email draft. You do not send it. Hand the draft to the checker. Fast draft, slow send. Nothing goes out on your say-so."},
        {'note': 'For the checker bot.', 'text': "You are the checker for this email. Review the draft before anything can go out. Do not send it. Flag problems and hold it if it isn't ready. It only goes out after I approve the send. Nothing goes out on a bot's say-so alone. Fast draft, slow send."},
    ],
    'scheduled-pack-and-gates': [
        {'note': 'For the morning pack.', 'text': 'You run the morning pack. Write the draft of the work for the day. Do not publish or send it. Scheduled prompts are useful; unattended publish is not. Later gates will check the work, and I still approve, before anything can go out.'},
        {'note': 'For a later gate.', 'text': 'You are a later gate on scheduled work. Check the draft at the time I scheduled you. Catch problems before anything can go out. Do not publish or send. I still approve. A schedule without a review is not a reason to let work go out.'},
    ],
}

COPY_PROMPT_JS = (
    '<script>(function(){'
    'function copy(pre,btn){var t=pre.textContent,old=btn.textContent;'
    'function done(){btn.textContent="Copied";btn.setAttribute("aria-label","Copied");'
    'setTimeout(function(){btn.textContent=old;btn.setAttribute("aria-label","Copy this prompt")},2000)}'
    'function fallback(){var r=document.createRange();r.selectNodeContents(pre);'
    'var s=window.getSelection();s.removeAllRanges();s.addRange(r);'
    'try{if(document.execCommand("copy"))done()}catch(err){}}'
    'if(navigator.clipboard&&navigator.clipboard.writeText){'
    'navigator.clipboard.writeText(t).then(done,fallback)}else fallback()}'
    'document.querySelectorAll("[data-prompt-copy]").forEach(function(btn){'
    'btn.addEventListener("click",function(){var pre=document.getElementById(btn.getAttribute("aria-controls"));'
    'if(pre)copy(pre,btn)})})})();</script>'
)


def prompt_block(text, pid, note=None):
    """Build-time 'Copy this prompt' block. The text is always visible and selectable without JS."""
    note_html = f'<p class="prompt-note">{e(note)}</p>' if note else ""
    return (
        f'<section class="prompt-block" id="{e(pid)}" aria-labelledby="prompt-h-{e(pid)}">'
        f'<div class="prompt-head">'
        f'<h2 class="prompt-title" id="prompt-h-{e(pid)}">Copy this prompt</h2>'
        f'<button type="button" class="btn pri prompt-copy" data-prompt-copy'
        f' aria-label="Copy this prompt" aria-controls="prompt-text-{e(pid)}">Copy this prompt</button>'
        f"</div>"
        f"{note_html}"
        f'<pre id="prompt-text-{e(pid)}" class="prompt-text" tabindex="0">{e(text)}</pre>'
        f"</section>"
    )


def prompt_blocks(slug):
    items = PROMPTS.get(slug) or []
    if not items:
        return ""
    bits = []
    for i, item in enumerate(items, 1):
        pid = "copy-prompt" if i == 1 else f"copy-prompt-{i}"
        bits.append(prompt_block(item["text"], pid, item.get("note")))
    bits.append(COPY_PROMPT_JS)
    return "".join(bits)


def tip_page(t, year):
    url = SITE + path_of(t["slug"])
    sibs = [BY_SLUG[s] for s in t["siblings"] if s in BY_SLUG]
    more = "".join(f'<li><a href="{path_of(s["slug"])}">{e(s["title"])}</a></li>' for s in sibs)
    main = f"""<main class="prose tips-main">
{crumbs(("Tips", "/tips/", False), (t["title"], path_of(t["slug"]), True))}
<h1>{e(t["title"])}</h1>
<p class="tip-body">{e(t["tip"])}</p>
{card_figure(t["slug"], t["alt"], CAPTIONS[t["slug"]], lazy=False)}
<h2 class="how">How I did it</h2>
<p class="how-body">{e(t["how"])}</p>
{prompt_blocks(t["slug"])}
<nav class="tip-more" aria-label="More tips">
<h2>More tips</h2>
<ul>{more}</ul>
<p><a class="back" href="/tips/">All tips</a></p>
</nav>
</main>"""
    extra = B.ld(article_ld(t, url))
    html_page = page(t["seo_title"], t["meta"], path_of(t["slug"]), extra, main, year)
    og = f"{SITE}/images/tips/{t['slug']}-og.jpg"
    return html_page.replace(f"{SITE}/og-default.png", og)


def first_sentence(text):
    return re.split(r"(?<=\.)\s", text, 1)[0]


def card_figure(slug, alt, caption, lazy=True):
    loading = ' loading="lazy"' if lazy else ""
    return (
        f'<figure class="tip-shot">'
        f'<img src="/images/tips/{e(slug)}.webp" width="1200" height="675" alt="{e(alt)}"{loading}>'
        f'<figcaption>{e(caption)}</figcaption>'
        f"</figure>"
    )


def hub_page(year):
    url = SITE + "/tips/"
    # Jump links: every standalone page slug, plus every site-only anchor.
    page_jumps = "".join(f'<a href="#{e(t["slug"])}">{e(t["title"])}</a>' for t in TIPS)
    hub_jumps = "".join(f'<a href="#{e(t["slug"])}">{e(t["title"])}</a>' for t in HUB_ONLY)
    secs = []
    for key, label in SECTIONS:
        pages = [t for t in TIPS if t["section"] == key]
        hubs = [t for t in HUB_ONLY if t["section"] == key]
        if not pages and not hubs:
            continue
        cards = []
        for t in pages:
            first = first_sentence(t["tip"])
            cards.append(
                f'<li id="{e(t["slug"])}"><a class="tip-title" href="{path_of(t["slug"])}">{e(t["title"])}</a>'
                f"<p>{e(first)}</p></li>"
            )
        page_list = f'<ul class="tip-cards">{"".join(cards)}</ul>' if cards else ""
        blocks = []
        for t in hubs:
            blocks.append(
                f'<article class="hub-only" id="{e(t["slug"])}">'
                f'<h3>{e(t["title"])}</h3>'
                f'<p class="tip-body">{e(t["tip"])}</p>'
                f'<h2 class="how">How I did it</h2>'
                f'<p class="how-body">{e(t["how"])}</p>'
                f'{card_figure(t["slug"], t["alt"], CAPTIONS[t["slug"]], lazy=True)}'
                f"</article>"
            )
        secs.append(
            f'<section class="tips-sec" aria-label="{e(label)}"><h2>{e(label)}</h2>'
            f"{page_list}{''.join(blocks)}</section>"
        )
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
<p class="tips-jump-label">Tip pages</p>
<nav class="tips-jump" aria-label="Tip pages">{page_jumps}</nav>
<p class="tips-jump-label">On this page</p>
<nav class="tips-jump" aria-label="Tips on this page">{hub_jumps}</nav>
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
