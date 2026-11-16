---
title: "Your skills and your bots are not the same thing"
description: "Why full skills inside bots cost tokens on every turn, and the LIGHT MODE / FULL SKILL MODE setup I use instead across 11 skills."
date: "2026-11-15"
status: "published"
slug: "skills-vs-bots-hybrid"
kind: "news"
story_key: "skills-vs-bots-hybrid"
image: "/images/news/2026-11-15-skills-vs-bots-hybrid.png"
image_alt: "Card that says your skills and your bots are not the same thing: full skills in bots cost tokens every turn, LIGHT MODE for quick work, FULL SKILL MODE when mistakes cost money."
sources: ""
seo_title: "Grok Bot skills vs bots: the usage trap and the hybrid fix"
seo_description: "Why full skills inside bots cost tokens on every turn, and the LIGHT MODE / FULL SKILL MODE setup I use instead across 11 skills."
keywords: "Grok Bot, skills, SKILL.md, bots, token usage, system prompt, light mode, full skill mode"
---

**I added a mode-handling section to all 11 of my Grok Bot skills. Your skills and your bots are not the same thing, and mixing them up can cost you tokens on every message.**

I run 11 skills and a fleet of Grok Bots I mostly use from my phone. I found bots and skills with the same names covering the same jobs, but the bots weren't loading the skill text. So I stopped and worked through usage before adding anything else.

**Skills and bots do different jobs**

- A skill is a detailed SKILL.md file with rules, steps and an output format. It loads in chat when the job calls for it.
- A bot is a persistent agent with a short description. It doesn't get a skill's full text unless you put it there yourself.

**The usage trap**

If you paste full skills into your bots, they carry that text on every turn. A longer system prompt means more tokens, even for a quick yes or no.

**The hybrid fix**

Bot descriptions stay short. The coordinator picks a mode for each request:

- **LIGHT MODE:** be concise and skip the full structure.
- **FULL SKILL MODE:** apply the complete rules and output format, and read the SKILL.md file first.

**What I changed**

- I added a mode-handling section to all 11 skills.
- I created one new specialist bot for pricing.
- I locked the baseline numbers so neither mode changes them.

I did the planning and the skill edits in the main Grok chat, not inside the bots. Now that the hybrid setup is live, I route work through the bots with a mode prefix.

**Who it's for**

It suits people who mostly use phone bots but want full rigor on work where mistakes cost money, like pricing or compliance.

- **Pros:** quality where it counts, and fewer tokens everywhere else.
- **Cons:** someone has to pick the mode.

It isn't for everyone. If every task you run is critical, just load the skill each time. Look at your own usage first.

## Sources

- From my own Grok Bot setup. No outside posts are cited.

## Related Grok Bot tips

- [Save working workflows as skills](/tips/shared-skills-across-bots/)
- [Watch usage, then pause routines](/tips/watch-usage-pause-routines/)
