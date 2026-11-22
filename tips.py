"""Grok Bot tips hub and per-tip pages at /tips/ and /tips/<slug>/."""
import hashlib, json, os, re
import build as B
e = B.e; SITE = B.SITE; BRAND = B.BRAND

# Cache-bust tips.css without changing the global style.css version.
TVER = hashlib.sha1(open(os.path.join(B.ROOT, "static", "tips.css"), "rb").read()).hexdigest()[:10]
CSS = f'<link rel="stylesheet" href="/tips.css?v={TVER}">'
# Theme colour matches the Bot Cut-outs page background (DESIGN.md).
THEME_COLOR = f'<meta name="theme-color" content="{B.THEME}">'

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
        "meta": "A Quality Checker bot reviews my bots' work before it reaches me. Public posts get a full review; daily news goes through an automated gate.",
        "tip": "A Quality Checker bot reviews my bots' work before it reaches me. Public posts and anything risky get the full review; daily news posts go through an automated gate instead. I don't want five versions of \"done.\" I want one reviewed answer. Who reviews work before it gets to you?",
        "how": "I added one fleet-wide Quality Checker bot. Small issues get cleaned up in its pass. Real risks get held. The rules live in a shared file the checker follows.",
        "alt": "Brand card comparing five dones with one checked result.",
        "slot": "A compare card: five dones versus one checked result.",
        "section": "quality",
        "siblings": ["before-after-proof", "drafts-only-approval", "recheck-after-late-edits"],
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
        "title": "Sends, spending and sign-ins wait for my OK",
        "seo_title": "Sends, spending and sign-ins wait for my OK | NextAiBreakout",
        "meta": "Sends, spending and sign-ins still wait for my OK. X tip posts go out after my checker bot reviews them. Daily news publishes after an automated gate.",
        "tip": "Sends, spending and sign-ins still wait for my OK. My queued X tip posts go out on a schedule after my checker bot reviews them. Daily news posts publish once an automated gate passes them. That's the rule that lets me run a fleet without waking up to a surprise send or spend. What still goes out without you seeing it first?",
        "how": "Sends, spending and sign-ins still wait for my OK. My queued X tip posts go out on a schedule after my checker bot reviews them. Daily news posts publish once an automated gate passes them, with no human or checker-bot review. Bots write drafts. Another bot saying \"it's ready\" is not approval for a send, a spend or a sign-in. My yes is the only approval on those.",
        "alt": "Brand card quoting the drafts-only rule: sends, spending and sign-ins still wait for my OK.",
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
        "meta": "My brother and I built Blabara, an Android voice-dictation app, in one day with a team of Grok Bots. Not a slide deck. A real app, in a day.",
        "tip": "My brother and I built Blabara, an Android voice-dictation app, in one day with a team of Grok Bots. Not a slide deck. A real app, in a day. What's the biggest thing you've actually built with a bot team?",
        "how": "My brother and I wanted a voice-dictation app for Android. We used a team of Grok Bots with clear roles, and we built Blabara in a day. That's still the clearest proof I have that a small, well-directed team beats a pile of unfocused chats.",
        "alt": "Brand card with the number 1 day, labeled Blabara, Android voice dictation, built with a Grok Bot team.",
        "slot": "A number card: 1 day. Blabara, Android voice dictation. Built with a Grok Bot team.",
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
        "meta": "I don't design a new image for every post. A script builds the cards in one brand style: same colours, same type, no photos of people. Consistency beats a one-off graphic every time.",
        "tip": "I don't design a new image for every post. A script builds the cards in one brand style: same colours, same type, no photos of people. Consistency beats a one-off graphic every time. How do you keep your visuals from drifting?",
        "how": "I used a script to render post cards in one style: navy ink on a pale ground, Syne and DM Sans, no photos of people. Same mark, same margins, a source line on the card. It kept the feed looking like one site, not a pile of random graphics.",
        "alt": "Brand card quoting the visual rule: one style, every card, same colours and type, no photos of people.",
        "slot": "A quote card: one style, every card. Same colours, same type. No photos of people.",
        "section": "skills",
        "siblings": ["shared-skills-across-bots", "before-after-proof", "drafts-only-approval"],
    },
    {
        "slug": "scheduled-pack-and-gates",
        "title": "Daily news posts go out after a gate",
        "seo_title": "Daily news posts go out after a gate | NextAiBreakout",
        "meta": "Daily news posts write, pass an automated gate, and go out to the site and X on a schedule. Sends, spending and sign-ins still wait for my OK.",
        "tip": "Daily news posts write, pass an automated gate, and go out to the site and X on a schedule. Sends, spending and sign-ins still wait for my OK. Scheduled prompts are useful. Publishing with no gate is not. When do you actually review what your routines produced?",
        "how": "The 6:45 AM morning pack is retired. A scheduled routine writes each daily news post. An automated gate re-fetches every cited X post and checks each quote and number against it, confirms every link returns 200, and rejects placeholders. Then the post publishes on the site and goes to X. My queued X tip posts go out on a schedule after my checker bot reviews them. Sends, spending and sign-ins still wait for my OK. A schedule without a gate is just a way to publish mistakes on time.",
        "alt": "Brand card quoting the scheduling rule: scheduled prompts are useful, publishing with no gate is not.",
        "slot": "A card of the checked-then-scheduled rule, with no clock times.",
        "section": "routines",
        "siblings": ["drafts-only-approval", "open-with-a-hook-line", "recheck-after-late-edits"],
    },
    {
        "slug": "open-with-a-hook-line",
        "title": "Open every post with a hook line",
        "seo_title": "Open every post with a hook line | NextAiBreakout",
        "meta": "I rewrote the first line of 7 X drafts: Days 10 to 14 and two weekly thread openers. A hook is a true, specific first line the post delivers.",
        "tip": "I rewrote the first line of 7 X drafts: Days 10 to 14 and two weekly thread openers. A hook is a true, specific first line, ideally with a real number or payoff, that the post actually delivers. No clickbait. What's the first line you'd fix on your feed?",
        "how": """I rewrote the first line of 7 unposted X drafts: Days 10 to 14, and the Week 1 and Week 2 thread openers. In four of them, the opening post changed only its first line. The others needed more edits so the whole post stayed true.

Here are the real first lines.

Day 10, proof. Before: No bug is fixed until it's proven with a before and after. After: My bots aren't allowed to say "fixed" until they show me a before and an after.

Day 11, approvals. Before: Spending and credentials stay on a one-tap approval. After: Two things my bots can't do without my tap: spend money or sign in with my credentials.

Day 12, draft then check. Before: I had a bot build a daily email, then a checker bot review it before anything could go out. After: Two bots, one daily email: one wrote it, the other checked it before anything could go out.

Day 13, scripted cards. Before: I don't design a new image for every post. After: One script makes every post card in my feed, all in one brand style.

Day 14, scheduled posts. Before: I run a morning pack routine, then later gates that check the work before it can go out. After: Every post in my queue gets a full review from a checker bot before a routine posts it on schedule.

Week 1 opener. Before: This week I wrote down what actually mattered in a Grok Bot fleet, plus the tradeoffs, not just the wins. After: 7 things that actually mattered running a Grok Bot fleet this week, with the tradeoffs, not just the wins.

Week 2 opener. Before: Week 2: we built a real app in a day, and I tightened the rules that keep a fleet honest, including the tradeoffs. After: We built a real Android app in one day with a team of bots, and I tightened the rules that keep a fleet honest, tradeoffs included.

The rule I use now: lead with the most specific true thing in the post, a number, a time, or a result. Write it in first person if it's something I actually did. If the post can't pay off the hook, I change the line, not the facts. I never use a number I can't point to.""",
        "alt": "Brand card with the number 7, labeled first lines rewritten.",
        "slot": "A number card: 7 first lines rewritten.",
        "section": "quality",
        "siblings": ["turn-lessons-into-posts", "recheck-after-late-edits", "scheduled-pack-and-gates"],
    },
    {
        "slug": "turn-lessons-into-posts",
        "title": "Turn lessons into posts",
        "seo_title": "Turn lessons into posts | NextAiBreakout",
        "meta": "I wrote the hook-line rule up as a lesson post, using real before-and-after lines from our drafts.",
        "tip": "I wrote the hook-line rule up as a lesson post. When we adopt a lesson for ourselves, it also becomes a post so other people can learn it. Would you publish your bots' lessons?",
        "how": "We adopted the hook-line rule, then I wrote it up as a lesson post with the real before-and-after first lines from our own drafts. Its examples have to match our draft files word for word, and it gets a checker review before it goes out. I want other people to be able to use what we just had to learn.",
        "alt": "Brand card comparing a fix we adopted with the same lesson turned into a post.",
        "slot": "A compare card: we fixed it, now it's a post.",
        "section": "skills",
        "siblings": ["open-with-a-hook-line", "scheduled-pack-and-gates", "shared-skills-across-bots"],
    },
    {
        "slug": "recheck-after-late-edits",
        "title": "Re-check after late edits",
        "seo_title": "Re-check after late edits | NextAiBreakout",
        "meta": "Day 12 and Day 14 copy was corrected after the first review, then went back to the checker. A pass only covers the version it reviewed.",
        "tip": "Day 12 and Day 14 copy was corrected after the first review, then went back to the checker. A pass only covers the version it reviewed, so I re-check the file after any late edit. How do you catch late edits?",
        "how": "After the first review, Day 12's cons line and the Day 14 post were rewritten so they matched how publishing works now. Day 14 was reworded again after the checker said an earlier line overstated the mechanism. Those changed drafts went back to the checker and passed. A pass only covers the version it reviewed. If anyone edits the file after that, it needs another pass before it can go out.",
        "alt": "Brand card showing a passed draft that was edited, so it has to be checked again.",
        "slot": "A before-and-after card: passed, then edited, so check again.",
        "section": "quality",
        "siblings": ["open-with-a-hook-line", "quality-checker-before-it-reaches-you", "scheduled-pack-and-gates"],
    },
    {
        "slug": "light-pass-then-full-review",
        "title": "Light checks for drafts, one full review at the end",
        "seo_title": "Light checks for drafts, full review last | NextAiBreakout",
        "meta": "The back-and-forth between my site bot and checker bot was about 44% of my fleet's usage in one week. Now drafts get one light pass.",
        "tip": "My site bot and my checker bot going back and forth was about 44% of my whole fleet's usage in one week. Now drafts get one light pass, and the full review happens once, on the final version, before anything goes public. Where does your review time actually go?",
        "how": """Two rules in my checker's shared rules file split reviews by risk. The full review covers anything public, anything sent to customers, and anything that touches money, accounts or permissions. The light check covers internal reports and drafts passed between bots. It confirms numbers and claims match their source, looks for secrets and invented facts, and runs once with no re-renders.

The second rule came out of the usage audit. Work-in-progress pages and drafts get one light pass, and the checker reports every issue in a single reply, with no repeat rounds over wording. A bot asks for a pass only when its work is finished, not after each small edit.

The full review happens once, on the final version, right before it goes public. If anyone edits the file after that pass, it needs another one. When I'm not sure which tier fits, I use the higher one.""",
        "alt": "Brand card with 44%, labeled: about that much fleet usage went to review rounds.",
        "slot": "A number card: about 44% of fleet usage went to review back-and-forth.",
        "section": "quality",
        "siblings": ["quality-checker-before-it-reaches-you", "recheck-after-late-edits", "bot-drafts-checker-reviews"],
    },
    {
        "slug": "goal-block-in-bot-profiles",
        "title": "Put a goal block in each bot's profile",
        "seo_title": "A goal block in each bot's profile | NextAiBreakout",
        "meta": "14 of my Grok Bots have the same three-line block in their profile: a goal, what done looks like, and when to ask me.",
        "tip": "14 of my Grok Bots have the same three-line block in their profile: a goal, what done looks like, and when to ask me. The point is that I stop repeating myself to the same bots. What would your bot's done-when line say?",
        "how": """Each block is three short lines at the end of the bot's profile.

GOAL: what the bot is for, in one sentence.

DONE WHEN: what finished looks like, in terms someone else can check.

ASK ME WHEN: the moments it has to stop and come to me first.

The ask line holds the hard stops, and each bot's list fits its job. My trading bots stop before any trade. My site bot stops before any visible change goes live, though it can hotfix a broken site and report after. Most of them also stop before spending money. My site bot's done line includes builds that pass my checker's rules.

The done line is the one I'd write first. It's how a bot knows it's finished without asking me.""",
        "alt": "Brand card quoting the three-line goal block: goal, done when, ask me when.",
        "slot": "A quote card of the three goal-block labels.",
        "section": "job-descriptions",
        "siblings": ["talk-to-one-lead-bot", "approve-spend-and-credentials", "shared-skills-across-bots"],
    },
    {
        "slug": "baseline-before-site-changes",
        "title": "Save a baseline before you change the site",
        "seo_title": "Save a baseline before you change the site | NextAiBreakout",
        "meta": "My site bot doesn't deploy until it diffs the new sitemap against the live one. Save a baseline first, or you can't tell if the edit worked.",
        "tip": "My site bot doesn't deploy until it diffs the new sitemap against the live one. A stale copy of the site would quietly roll back pages that are already live. Save a baseline first, or you can't tell if the edit worked. What do you compare against before you ship?",
        "how": """Before any deploy, my site bot fast-forwards its copy of the repo to the latest main, builds the site, and diffs the built sitemap against the live one. Other bots commit to the same repo, so its copy can fall behind. If the diff shows live pages going missing, the copy is stale, and deploying it would roll those pages back. If the only change is the page it meant to add, it's safe to ship.

The same idea works for search traffic. Before changing pages for search, I saved a starting point from Search Console for my sites: clicks, impressions, average position, the submitted sitemaps, and how each homepage is indexed. A monthly review compares against that file.

Without a starting point, a better month and a lucky month look the same.""",
        "alt": "Brand card comparing shipping with no baseline to diffing against live first.",
        "slot": "A before-and-after card: ship blind versus diff against live first.",
        "section": "safety",
        "siblings": ["before-after-proof", "recheck-after-late-edits", "scheduled-pack-and-gates"],
    },
    {
        "slug": "cheap-checks-before-writing",
        "title": "Run cheap checks before the bot writes",
        "seo_title": "Run cheap checks before the bot writes | NextAiBreakout",
        "meta": "On a quiet news day, my pipeline's check script ran about 11 seconds and stopped. Cheap checks first; the model writes only when there's a real story.",
        "tip": "On a quiet news day in my cost log, the check script ran for about 11 seconds and stopped. Nothing cleared the bar, so no post got written. Cheap checks first, and the model only writes when there's a real story. What's the cheapest check you could put in front of your bot?",
        "how": """My daily news run starts with scripts, not writing. A small script re-reads every candidate X post from X's public embed, drops anything older than 24 hours or already covered on the site, and applies a notability bar. The biggest post in the story needs at least 500 likes, or 200 if Elon Musk, xAI or a Grok Bot team account posted it. If nothing clears the bar and no checked lesson is waiting in the queue, the run stops quietly. On that quiet day, the script made zero X API calls, and the writing step never started.

Every run, quiet or not, adds one line to a cost log: the outcome, X calls by type, whether the AI wrote anything, and how long it took. Every failure adds an entry to an issues file. A small script with no AI in it watches that file and only speaks up when something new lands. One morning that file showed the gate stopping a news post twice for the same two reasons: a 164-character description against my 155 limit, and the word "draft" left on the page.

That's now a fleet rule. Before a bot produces a post, page or report, it runs the cheap checks, then reads the recent entries in its results log if it has one, so it doesn't repeat a miss that's already written down.""",
        "alt": "Brand card with 11 sec, labeled: about that long, on a quiet news day.",
        "slot": "A number card: about 11 seconds on a quiet news day, no post written.",
        "section": "usage",
        "siblings": ["scheduled-pack-and-gates", "watch-usage-pause-routines", "light-pass-then-full-review"],
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
        "tip": "A bot asked to market, code, and file invoices gets mushy. I give each bot one job.",
        "how": "In my setup, I use named specialists (research, site, marketing, checker, desks) instead of one generalist. When jobs overlap, I end up with duplicate routines.",
        "alt": "Brand card quoting the job rule: give each bot one job.",
        "slot": "A job-description screen, once a redacted example is ready.",
    },
    {
        "slug": "write-down-checker-rules",
        "title": "Write the checker's rules down, and add one for every miss",
        "section": "quality",
        "tip": "I don't want the same mistake slipping through twice: a wrong sign-off, an invented figure, or an unproven \"fixed.\"",
        "how": "I keep the checker's rules in a shared file, with a regression pack. Named rules get dates and examples. No invented figures. I don't call a bug \"fixed\" without before-and-after proof. I also don't put other people's email addresses or private misses on a public page.",
        "alt": "Brand card quoting the checker-rules rule: write the rules down, and add one for every miss.",
        "slot": "A snippet of the rules file, no private addresses.",
    },
    {
        "slug": "isolate-the-app-repo",
        "title": "Keep one repo off-limits to the rest of the fleet",
        "section": "teams",
        "tip": "I don't want two bots pushing to the same app repo.",
        "how": "I split the work. Claude builds the Blabara app in its own repo. Chief of Staff and the Voice Keyboard Builder don't edit or push there. My other Grok Bots handle coordination and the rest of the work. That's a process split, not a claim that one model is better than the other.",
        "alt": "Brand card quoting the access rule: keep one repo off-limits to the rest of the fleet.",
        "slot": "A redacted access or handoff note, once one is ready to publish.",
    },
    {
        "slug": "change-only-watches",
        "title": "Stay quiet unless something changed",
        "section": "routines",
        "tip": "A scheduled bot that wakes up just to say nothing changed is wasted work. Silence is the correct output when nothing changed.",
        "how": "I want the watch itself to be a script, with no model in the loop. Exit quietly when nothing happened. Only speak when there's an alert. I don't want to wake a model just to say \"no change.\"",
        "alt": "Brand card quoting the quiet-watch rule: silence is the correct output when nothing changed.",
        "slot": "A redacted quiet-exit versus alert example, with no levels, sizes, or wallet data.",
    },
    {
        "slug": "script-before-model",
        "title": "Prefer a script over a model when the job is deterministic",
        "section": "usage",
        "tip": "I'd rather not pay for a model wake to diff a list, check a price, or filter an inbox when a script can do that job.",
        "how": "I'd rather use a small script: exit quietly when nothing happened, and only print a message when there's something to say. Adding another model vendor is not my first move. That's the pattern I want, though I'm not claiming every watch already runs this way.",
        "alt": "Brand card quoting the script-first rule: prefer a script over a model when the job is deterministic.",
        "slot": "A redacted dry-run of a quiet exit versus a message exit.",
    },
    {
        "slug": "human-publish-gate",
        "title": "Put a human publish gate in front of the website",
        "section": "safety",
        "tip": "Unreviewed auto content, including CJK text and unverified ranking blurbs, reached the NAB homepage and daily pages in early November 2026. I stopped the sends and the publishes.",
        "how": "I want a publish step in front of the website. Builds should come only from reviewed markdown. Checks should catch CJK unless I've allowlisted it, empty descriptions, and a missing review stamp. Nothing a bot writes should deploy on its own say-so: it needs my OK or a pass from my checker. Taking old daily pages down is not the same as that gate, and the full version isn't built yet.",
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
def hub_intro():
    """Computed counts; never type them. Hub-only tips are already written up on this page."""
    n_all, n_full, n_hub = len(TIPS) + len(HUB_ONLY), len(TIPS), len(HUB_ONLY)
    return (f"{n_all} Grok Bot tips from work I actually ran. "
            f"{n_full} have their own page, with the tip, how I did it, and a brand card for each one. "
            f"{n_hub} are written up on this page.")

BY_SLUG = {t["slug"]: t for t in TIPS}


# Beginner path on /tips/ only. Each slug must be a standalone tip page.
# Reasons are taken from that page's own tip text. Newest-first list stays below.
START_HERE = (
    ("talk-to-one-lead-bot", "I talk to one lead bot, and it routes work to the specialists."),
    ("drafts-only-approval", "My queued X tip posts go out on a schedule after my checker bot reviews them."),
    ("quality-checker-before-it-reaches-you", "A Quality Checker bot reviews work before it reaches me. Small issues get cleaned up, and real risks get held."),
    ("approve-spend-and-credentials", "Spending and credentials stay on a one-tap approval. I still press the button."),
    ("watch-usage-pause-routines", "I watch the meter and pause routines before they all crash."),
)


def start_here_html():
    """Accessible 'Start here' block: heading, ordered list, real links."""
    items = []
    for slug, reason in START_HERE:
        t = BY_SLUG[slug]
        items.append(
            f'<li><a href="{path_of(slug)}">{e(t["title"])}</a>'
            f"<p>{e(reason)}</p></li>"
        )
    return (
        '<section class="start-here" aria-labelledby="h-start-here">'
        '<h2 id="h-start-here">Start here</h2>'
        f'<ol class="start-here-list">{"".join(items)}</ol>'
        "</section>"
    )



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
    "scheduled-pack-and-gates": 'The scheduled-news-and-gate rule, as a brand card.',
    "open-with-a-hook-line": 'Seven first lines rewritten, as a brand card.',
    "turn-lessons-into-posts": 'A lesson becomes a post, as a brand card.',
    "recheck-after-late-edits": 'Re-check after a late edit, as a brand card.',
    "one-job-per-bot": 'The one-job-per-bot rule, as a brand card.',
    "write-down-checker-rules": 'The written-checker-rules rule, as a brand card.',
    "isolate-the-app-repo": 'The isolated-repo rule, as a brand card.',
    "change-only-watches": 'The change-only watch rule, as a brand card.',
    "script-before-model": 'The script-before-model rule, as a brand card.',
    "human-publish-gate": 'The human publish gate, as a brand card.',
    "light-pass-then-full-review": "About 44% of fleet usage, as a brand card.",
    "goal-block-in-bot-profiles": "The three-line goal block, as a brand card.",
    "baseline-before-site-changes": "Baseline first, then change.",
    "cheap-checks-before-writing": "About 11 seconds on a quiet news day, as a brand card.",
}




def paras(text, first_class=None):
    """Split on blank lines so a long how-section can be more than one <p>."""
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    bits = []
    for i, part in enumerate(parts):
        cls = first_class if first_class and i == 0 else None
        attr = f' class="{cls}"' if cls else ""
        bits.append(f"<p{attr}>{e(part)}</p>")
    return "".join(bits) if bits else ""


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
    # Same theme-color as the rest of the site (B.THEME).
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
            ld_breadcrumb([("Home", SITE + "/"), ("Grok Bot Tips", SITE + "/tips/"), (t["title"], url)]),
        ],
    }



# Copyable setup prompts for tips that recommend a bot, routine, or checker.
# Day 1 text is verbatim. Other drafts stay faithful to that tip; see /workspace/shared/nab-relaunch/tip-prompts.md.
PROMPTS = {
    'talk-to-one-lead-bot': [
        {'text': "You are my Chief of Staff and the only bot I talk to first. Take whatever I ask (business, ideas, research or anything else) and turn it into a clear goal, who owns it, and the next step. Keep unrelated topics in separate threads and never mix them in one answer. When one area gets deep enough, suggest a focused specialist bot, ask me before creating it, give it only the brief it needs, and stay the coordinator. Get facts from live sources, not memory; use memory for my preferences and how I like to work. Never send messages, post, spend money, delete anything or change permissions without my explicit OK. If a tool is missing, tell me what to connect. If you're blocked, stop and ask. Keep replies short and lead with the answer."},
    ],
    'quality-checker-before-it-reaches-you': [
        {'text': 'You are my Quality Checker. You review my bots\' work before it reaches me. Public posts and anything risky get the full review; daily news posts go through an automated gate instead. I don\'t want five versions of "done." I want one reviewed answer. Follow the rules in the shared file I give you. Clean up small issues in that pass. Hold real risks and do not send those through to me as finished work. You are a reviewer, not the one who publishes or sends.'},
    ],
    'agent-to-agent-handoffs': [
        {'text': 'You are a specialist bot. You do not report to me on every hop. When you finish your part, hand the work to the next specialist with an agent-to-agent message and a clear finish line — what you did, and what they need to do next. Do not leave a trail of half-updates for me. The lead bot will collect one combined summary and bring me the result.'},
    ],
    'drafts-only-approval': [
        {'text': 'Nothing you write may send, go out as a DM or email, spend money, or use my sign-ins unless I have approved it. Posts go out only after my checker bot or my automated gate clears them. Drafts only. Write the draft and wait. Another bot saying "it\'s ready" is not approval. My yes is the only approval on sends, spending and sign-ins.'},
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
        {'note': 'For the daily news writer.', 'text': 'You write the daily news post on the schedule I set. Do not publish it yourself. The draft has to pass the automated gate first: cited posts re-checked, links returning 200, and no placeholders. Open with a hook line the post actually delivers. Scheduled prompts are useful; publishing with no gate is not.'},
        {'note': 'For the automated gate.', 'text': 'You are the automated gate for the daily news post. Re-fetch every cited post and check each quote and number against it, confirm every link returns 200, and reject placeholders. If it fails, hold it. If it passes, it can publish to the site and X. This gate is only for the daily news post. Sends, spending and sign-ins still wait for my OK.'},
    ],
    'open-with-a-hook-line': [
        {'text': 'Every post you draft opens with a hook line: a true, specific first line, ideally with a real number or payoff, that the rest of the post actually delivers. No clickbait. If the post cannot pay off the hook, change the line, not the facts. Never use a number you cannot point to.'},
    ],
    'turn-lessons-into-posts': [
        {'text': 'When we adopt a lesson or improvement for ourselves, write it up as a post so other people can learn it. Use real before-and-after examples from our own files, quoted word for word. Do not invent numbers or stories. The post gets a checker review before it can publish.'},
    ],
    'recheck-after-late-edits': [
        {'text': 'A review only covers the version you checked. If the file is edited after you pass it, the pass no longer applies. Re-check the file after any late edit, and do not let it go out until that new pass is done.'},
    ],
    "light-pass-then-full-review": [
        {"note": "For the checker bot.", "text": "You are my checker bot. Scale your review to the risk. Drafts and in-progress work passed between bots get one light pass: check that numbers and claims match their source, and look for secrets and invented facts. Report every issue in one reply, with no repeat rounds over wording. Anything going public, to customers, or touching money, accounts or permissions gets one full review, on the final version. If the file changes after your pass, it needs another pass. When you're not sure which tier fits, use the full review."},
        {"note": "For the bot doing the work.", "text": "Ask the checker for a pass only when your work is finished, not after each small edit. Batch your fixes. Ask for the full review once, on the final version, before it goes public."},
    ],
    "goal-block-in-bot-profiles": [
        {"text": "Add three lines to the end of your profile, one sentence each. GOAL: what you're for. DONE WHEN: what finished looks like, in terms someone else can check. ASK ME WHEN: the moments you stop and ask me first. Always include sends, spending, deletes, publishing, permissions and live accounts in that last line. Show me the three lines before you save them."},
    ],
    "baseline-before-site-changes": [
        {"text": "Before you deploy the site, update your copy to the latest main, build it, and compare the built sitemap with the live one. If live pages would disappear, stop and tell me, because your copy is stale. Only deploy when the differences are the pages you meant to change. Before changing pages for search, save a starting point first (clicks, impressions and average position from Search Console) so we can tell later whether the change worked."},
    ],
    "cheap-checks-before-writing": [
        {"text": "Before you write anything, run the cheap checks first: scripts that confirm there's something new, that it clears the bar I set, and that it isn't already covered. If nothing passes, stop quietly and don't send a nothing-today message. Then read the recent entries in your results log so you don't repeat a miss we've already written down. Only then write. Every run, quiet or not, adds one short line to the log, with real numbers only."},
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


# Honest tradeoffs and, only when a live X post clearly fits, a "From {author}" cite.
# Proof posts must be by Elon Musk or a verifiable xAI/Grok team member, quoted verbatim,
# and re-fetched by id before publish. Skip the line rather than stretch a loose match.

PROS_CONS = {
    "talk-to-one-lead-bot": {
        "pros": [
            "I have one place to talk, instead of hopping between specialists.",
            "There's less juggling. I ask once and the lead routes the work.",
            "Specialists still do the deep work. I just don't have to manage every thread.",
        ],
        "cons": [
            "That one bot can become a bottleneck if it sits on work.",
            "It needs clear routing rules, or jobs stay in the lead chat instead of moving on.",
        ],
        "proof": {
            "text": "Grok @Bot is like hiring an incredibly competent chief of staff",
            "url": "https://x.com/elonmusk/status/2114772843997351993",
            "name": "Elon Musk",
            "handle": "elonmusk",
            "date": "October 26, 2026",
            "role": "Elon Musk, founder of xAI. Post re-fetched by id 2114772843997351993 on Nov 12, 2026; text matched exactly.",
        },
    },
    "quality-checker-before-it-reaches-you": {
        "pros": [
            "I get one reviewed answer, not five versions of \"done.\"",
            "Small issues get cleaned up before I see them.",
            "Real risks get held, so I spend my time on the ones that matter.",
        ],
        "cons": [
            "It adds a step, so I wait a bit longer for the answer.",
            "The checker is only as good as the rules file it follows.",
            "If I don't keep those rules current, bad work can still slip through.",
        ],
    },
    "agent-to-agent-handoffs": {
        "pros": [
            "I don't sit in every hop.",
            "Specialists can keep moving without waiting on me.",
            "I get one packet instead of a trail of half-updates.",
        ],
        "cons": [
            "If a handoff is vague, the next bot can stall and I won't see it right away.",
            "A missed finish line is harder to catch when I'm not in the thread.",
        ],
    },
    "drafts-only-approval": {
        "pros": [
            "Sends, spending and sign-ins still wait for my OK.",
            "Queued X tip posts go out on a schedule after my checker bot reviews them.",
            "Daily news posts publish once an automated gate passes them.",
        ],
        "cons": [
            "I have to actually approve, so work waits on me.",
            "If I'm slow, drafts pile up.",
        ],
    },
    "shared-skills-across-bots": {
        "pros": [
            "A working workflow gets reused instead of retyped every morning.",
            "New bots inherit the same steps and the same stop-and-ask rules.",
            "When the tools change, I update one skill instead of every bot.",
        ],
        "cons": [
            "A stale skill can spread the same mistake across the fleet.",
            "I have to drop the ones we stopped using, or bots keep following old steps.",
        ],
    },
    "check-your-routine-timezone": {
        "pros": [
            "Once I check the zone, the job runs when I meant it to.",
            "I catch a quiet miss before I start relying on work that never ran.",
        ],
        "cons": [
            "It's easy to assume local time and be wrong.",
            "A wrong zone fails quietly. I only notice when the work doesn't show up.",
        ],
    },
    "watch-usage-pause-routines": {
        "pros": [
            "A paused routine is better than a week of empty slots.",
            "I can keep the fleet running tomorrow instead of watching everything fail at once.",
        ],
        "cons": [
            "I have to check the meter on purpose.",
            "If I forget, every routine can still fail together.",
            "Pausing work means some jobs wait.",
        ],
    },
    "blabara-in-one-day": {
        "pros": [
            "A small team with clear roles can ship a real app in a day, not a slide deck.",
            "It's the clearest proof I have that focused bots beat a pile of unfocused chats.",
        ],
        "cons": [
            "It only worked because the roles stayed clear.",
            "One good day isn't a promise that every build goes that fast.",
        ],
    },
    "group-chat-per-project": {
        "pros": [
            "Handoffs stay in one channel instead of getting dropped between threads.",
            "Each bot has a distinct role, and the lead still coordinates.",
            "When the project ends, I close the chat so old context doesn't linger.",
        ],
        "cons": [
            "A group chat still needs a lead, or it turns into noise.",
            "If I leave it open after the work is done, old context can creep into the next job.",
        ],
    },
    "before-after-proof": {
        "pros": [
            "I can see what changed, not just take \"done\" as the answer.",
            "\"I fixed it\" without proof goes back.",
            "It's saved me from a lot of false dones.",
        ],
        "cons": [
            "I have to wait for a screenshot or a passing case, so I accept a fix later.",
            "If the proof is weak, I send it back and we go around again.",
        ],
    },
    "approve-spend-and-credentials": {
        "pros": [
            "A bot can draft the step, but I still press the button.",
            "Payments and logins don't go through on a pre-approval.",
            "I don't put passwords in the chat, and I don't leave a blank check.",
        ],
        "cons": [
            "Every spend or login waits on me.",
            "If I miss an approval, the work stops.",
        ],
    },
    "bot-drafts-checker-reviews": {
        "pros": [
            "The draft comes back fast.",
            "A checker reviews it before I ever approve a send.",
            "Nothing goes out on a bot's say-so alone.",
        ],
        "cons": [
            "Two bots plus my approval is more moving parts.",
            "The send still waits on me.",
            "If the checker is weak, I can still be the last to catch a bad draft.",
        ],
    },
    "scripted-brand-cards": {
        "pros": [
            "Every card looks like one site, not a pile of random graphics.",
            "Same type, same margins, no photos of people.",
            "I don't redesign a graphic for every post.",
        ],
        "cons": [
            "A scripted style can feel rigid when I need a one-off.",
            "If the script drifts from the live brand, every new card is off until I fix it.",
        ],
    },
    "scheduled-pack-and-gates": {
        "pros": [
            "Daily news can go out on schedule after a real gate, without me tapping send.",
            "The gate re-checks cited posts, link status, and placeholders.",
            "Sends, spending and sign-ins still wait for my OK.",
        ],
        "cons": [
            "A schedule without a gate is just a way to publish mistakes on time.",
            "If the gate is weak, a bad news post can still go out.",
            "The gate only covers the version it reviewed, so a late edit needs another pass.",
        ],
    },
    "open-with-a-hook-line": {
        "pros": [
            "The first line makes a concrete claim the rest of the post has to pay off.",
            "A real number or payoff is easier to check than a vague opener.",
            "I can point at the 7 rewrites, not a made-up example.",
        ],
        "cons": [
            "Every hook has to be checked for truth.",
            "If the post can't deliver the line, I have to rewrite the opener, not dress up the facts.",
        ],
    },
    "turn-lessons-into-posts": {
        "pros": [
            "Other people can learn the same lesson from a real example.",
            "The post uses our own drafts, so nothing is invented.",
            "It gets a checker review before it goes out.",
        ],
        "cons": [
            "You show your mistakes and late fixes in public.",
            "A lesson post still waits for review, so it doesn't go out the second you learn it.",
        ],
    },
    "recheck-after-late-edits": {
        "pros": [
            "What goes out is the version that actually passed.",
            "A late correction can't ride on an earlier pass.",
        ],
        "cons": [
            "Each late edit means another review round.",
            "If I skip the re-check, a failed line can still go out.",
        ],
    },
    "light-pass-then-full-review": {
        "pros": [
            "Drafts move faster, because one pass covers them.",
            "Every issue arrives in one reply, not spread over rounds.",
            "The full review still happens on the version that actually goes public.",
        ],
        "cons": [
            "A light pass can miss something the full review only catches at the end.",
            "A late edit still needs another pass, so a sloppy finish costs a round.",
        ],
    },
    "goal-block-in-bot-profiles": {
        "pros": [
            "I stop repeating the same goal to the same bot.",
            "Each bot knows when to stop and ask, instead of guessing.",
            "A checker can hold work against a written done line.",
        ],
        "cons": [
            "A stale goal keeps steering the bot until I update it.",
            "Three lines can't cover every case, so some questions still come to me.",
        ],
    },
    "baseline-before-site-changes": {
        "pros": [
            "A stale copy gets caught before it overwrites live pages.",
            "I can point to what changed instead of guessing.",
            "The sitemap diff is one quick command before each deploy.",
        ],
        "cons": [
            "A sitemap diff catches missing or added pages, not a page that broke.",
            "A baseline only helps if someone goes back and compares.",
        ],
    },
    "cheap-checks-before-writing": {
        "pros": [
            "A quiet day costs seconds of script time, not a written post.",
            "The model only writes when a story clears the bar.",
            "A logged miss gets read before the next run instead of repeated.",
        ],
        "cons": [
            "A fixed bar can skip a real story that's still small.",
            "The logs only help if the bot actually reads them before it starts.",
        ],
    },
}


def team_proof_block(slug):
    proof = (PROS_CONS.get(slug) or {}).get("proof")
    if not proof:
        return ""
    heading = f"From {proof['name']}"
    label = f"{proof['name']} (@{proof['handle']}), {proof['date']}"
    return (
        f'<aside class="team-proof" aria-labelledby="team-proof-heading">'
        f'<h2 id="team-proof-heading">{e(heading)}</h2>'
        f"<blockquote>"
        f"<p>{e(proof['text'])}</p>"
        f"<footer><cite><a href=\"{e(proof['url'])}\">{e(label)}</a></cite></footer>"
        f"</blockquote>"
        f"</aside>"
    )


def pros_cons_block(slug):
    data = PROS_CONS.get(slug)
    if not data:
        raise KeyError(f"missing pros/cons for tip {slug}")
    if not (2 <= len(data["pros"]) <= 4 and 2 <= len(data["cons"]) <= 3):
        raise ValueError(f"pros/cons count out of range for {slug}")
    pros = "".join(f"<li>{e(item)}</li>" for item in data["pros"])
    cons = "".join(f"<li>{e(item)}</li>" for item in data["cons"])
    return (
        f'<section class="pros-cons" id="pros-cons" aria-labelledby="pros-cons-heading">'
        f'<h2 id="pros-cons-heading">Pros and cons</h2>'
        f"<h3>Pros</h3>"
        f"<ul>{pros}</ul>"
        f"<h3>Cons</h3>"
        f"<ul>{cons}</ul>"
        f"</section>"
    )


def tip_extras(slug):
    # Proof (if any), then pros/cons, then the copy-prompt box so the
    # tradeoffs sit immediately before #copy-prompt when one exists.
    return team_proof_block(slug) + pros_cons_block(slug) + prompt_blocks(slug)



def tip_date_html(slug):
    """Hidden publish date from the catalog, or empty if the slug is missing."""
    import catalog as C
    row = C.by_id(slug)
    if not row:
        return ""
    return f'<time class="vh" datetime="{e(row["date"])}"></time>'


def tip_page(t, year):
    url = SITE + path_of(t["slug"])
    sibs = [BY_SLUG[s] for s in t["siblings"] if s in BY_SLUG]
    more = "".join(f'<li><a href="{path_of(s["slug"])}">{e(s["title"])}</a></li>' for s in sibs)
    main = f"""<main class="prose tips-main">
{crumbs(("Grok Bot Tips", "/tips/", False), (t["title"], path_of(t["slug"]), True))}
{B.peek_h1(e(t["title"]), B.CHECKER_BOT)}
{tip_date_html(t["slug"])}
{paras(t["tip"], "tip-body")}
{card_figure(t["slug"], t["alt"], CAPTIONS[t["slug"]], lazy=False)}
<h2 class="how">How I did it</h2>
{paras(t["how"], "how-body")}
{tip_extras(t["slug"])}
<nav class="tip-more" aria-label="More tips">
<h2>More tips</h2>
<ul>{more}</ul>
<p><a class="back" href="/tips/">See all Grok Bot tips</a></p>
</nav>
</main>"""
    extra = B.ld(article_ld(t, url))
    html_page = page(t["seo_title"], t["meta"], path_of(t["slug"]), extra, main, year)
    og = f"{SITE}/images/tips/{t['slug']}-og.jpg"
    # Share image is the tip's own card, so its alt must describe that card, not the site-wide default.
    html_page = html_page.replace(f'<meta property="og:image:alt" content="{e(B.OG_ALT)}">', f'<meta property="og:image:alt" content="{e(t["alt"])}">', 1)
    return html_page.replace(f"{SITE}{B.OG_DEFAULT}", og)


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
                f'<li id="{e(t["slug"])}">{tip_date_html(t["slug"])}'
                f'<a class="tip-title" href="{path_of(t["slug"])}">{e(t["title"])}</a>'
                f"<p>{e(first)}</p></li>"
            )
        page_list = f'<ul class="tip-cards">{"".join(cards)}</ul>' if cards else ""
        blocks = []
        for t in hubs:
            blocks.append(
                f'<article class="hub-only" id="{e(t["slug"])}">'
                f'{tip_date_html(t["slug"])}'
                f'<h3>{e(t["title"])}</h3>'
                f'<p class="tip-body">{e(t["tip"])}</p>'
                f'<h2 class="how">How I did it</h2>'
                f'<p class="how-body">{e(t["how"])}</p>'
                f'{card_figure(t["slug"], t["alt"], CAPTIONS[t["slug"]], lazy=True)}'
                f"</article>"
            )
        secs.append(
            f'<section class="tips-sec" id="sec-{e(key)}" aria-label="{e(label)}"><h2>{e(label)}</h2>'
            f"{page_list}{''.join(blocks)}</section>"
        )
    import catalog as C
    dated = C.filter_entries(kind="grok", type="tip")
    item_list = dict(C.item_list("Grok Bot tips", dated), **{"@id": url + "#list"})
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "Grok Bot tips", "url": url, "description": HUB_META, "mainEntity": {"@id": url + "#list"}},
            item_list,
            ld_breadcrumb([("Home", SITE + "/"), ("Grok Bot Tips", url)]),
        ],
    }
    main = f"""<main class="prose tips-main">
{crumbs(("Grok Bot Tips", "/tips/", True))}
{B.peek_h1(B.circ(e(HUB_H1)), B.LEAD_BOT)}
<p class="lede">{e(hub_intro())}</p>
{start_here_html()}
<h2 class="tips-index-h">All tips, newest first</h2>
{C.listing_html(dated, "tips-index")}
<p class="tips-jump-label">Tip pages</p>
<nav class="tips-jump" aria-label="Tip pages">{page_jumps}</nav>
<p class="tips-jump-label">On this page</p>
<nav class="tips-jump" aria-label="Tips on this page">{hub_jumps}</nav>
{"".join(secs)}
</main>"""
    return page(HUB_TITLE, HUB_META, "/tips/", B.ld(graph), main, year)


def apply(DIST, t):
    import catalog as C
    cat_ids = {e["id"] for e in C.filter_entries(kind="grok", type="tip")}
    src_ids = {x["slug"] for x in list(TIPS) + list(HUB_ONLY)}
    if cat_ids != src_ids:
        missing = src_ids - cat_ids
        extra = cat_ids - src_ids
        raise SystemExit(f"catalog grok tips out of sync with tips.py: missing {sorted(missing)} extra {sorted(extra)}")
    year = t.year
    write(DIST, "tips/index.html", hub_page(year))
    for tip in TIPS:
        write(DIST, f"tips/{tip['slug']}/index.html", tip_page(tip, year))
    # sitemap + llms
    sp = os.path.join(DIST, "sitemap.xml")
    s = open(sp, encoding="utf-8").read()
    import catalog as C
    dated = {e["url"]: e["date"] for e in C.filter_entries(kind="grok", type="tip")}
    hub_day = C.newest_date(kind="grok", type="tip") or "2026-11-12"
    urls = [("/tips/", hub_day, "weekly")] + [(path_of(tip["slug"]), dated.get(path_of(tip["slug"]), hub_day), "monthly") for tip in TIPS]
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
