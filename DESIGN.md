# NextAiBreakout design guide: "Bot Cut-outs"

Live since Nov 12, 2026. Chosen by Ryan from six mockups (he picked the mix of "Cut-outs" and "Zine").
Built by Claude. **Grok Bot: read this before you add a post, a tip, or a page, and before any style change.**
It replaces the teal and gold look. `brand/x-visual-spec.md` describes the card and share-image palette, which now matches this guide.

## The idea in one paragraph
A pale gallery wall with paper cut-out shapes, drawn like a comic. Three small robots stand for the three roles on
this site: the lead bot, a specialist, and the Quality Checker. Everything is HTML and CSS. There are no image
files for the art, so pages stay light and nothing has to be generated to publish a post.

## Why it is built this way
| Decision | Why |
|---|---|
| Phone first | Ryan reviews on his phone, and most visitors will too. Every section is one column at 390 px wide. |
| No tap needed to read anything | The first mockups hid step text behind buttons. Ryan rejected that. All copy is visible on load. |
| CSS motion, no library | No GSAP, no framework. Faster pages rank better, and nothing can break the build. One small inline script (`SCROLL_JS` in `build.py`) replays the scroll effects in browsers without CSS scroll-driven animation (Firefox, older Safari). |
| Motion never hides content | Scroll effects sit inside `@supports (animation-timeline: view())`. Old browsers show the finished state. |
| Real text for everything | Headings, steps, and card copy are plain HTML so Google reads all of it. Art is `aria-hidden`. |
| Counts come from data | "20 tips", "14 full write-ups", and topic counts are computed in `build.py` from `tips.py`. Never type them. |

## Tokens (`static/style.css`, top of file)
| Token | Value | Use |
|---|---|---|
| `--bg` | `#E9EEF2` | page background |
| `--paper` | `#FFFFFF` | cards, speech bubbles |
| `--ink` | `#0F1B3D` | all text, outlines, hard shadows |
| `--mut` | `#46506B` | secondary text |
| `--red` | `#FF4B2B` | fills only (lead bot, card, shadow) |
| `--red-ink` | `#B92E16` | red **text** and links (passes AA on `--bg`) |
| `--blue` | `#2747F5` | fills; white text is allowed on it |
| `--och` | `#F2B01E` | fills; ink text only |

Rules: never white text on red or ochre. Never red `#FF4B2B` as text on the pale background; use `--red-ink`.
Outlines are always `3px solid var(--ink)`. Shadows are hard and offset (`7px 7px 0`), never blurred.

## Type (self-hosted in `fonts/`, all OFL)
- **Syne 800**: headings. It is very wide, so keep headings short. Hero is capped at 84 px for that reason.
- **DM Sans**: body, 17 to 19 px.
- **Gochi Hand**: handwritten notes only (class `note` or `hand`). One short line. Never body copy.

## The robots (`build.py`: `bot()`, `bot_head()`)
| Character | Constant | Look |
|---|---|---|
| Lead bot | `LEAD_BOT` | red, rounded head |
| Specialist | `SPECIALIST_BOT` | blue, square head |
| Quality Checker | `CHECKER_BOT` | ochre, one big monocle eye |
| Ryan ("you") | `bot_head("#fff", "50%")` | white round face, no antenna |

Use `B.bot(**B.LEAD_BOT)` in any page builder. Size it with `font-size` on the parent. Add `cls="wave"` to wave,
`cls="still"` to stop the bobbing. Keep each character's colours the same everywhere. These are original
characters. Do not swap in the Grok logo, the xAI logo, or any other company's mascot.

## Titles: style "D" (chosen by Ryan, Nov 12, 2026)
Two helpers in `build.py`, used on every page:
- `circ("words")`: draws a red hand-drawn loop around the key words of a title. The loop draws itself on load
  (page titles) or as it scrolls in (section titles). Pass 1 to 3 short words; they never wrap.
- `peek_h1(inner_html, WHO)`: wraps the page `<h1>` with a bot head peeking off the top-right corner.
  `WHO` is `LEAD_BOT` (About, tips hub), `CHECKER_BOT` (each tip, 404) or `SPECIALIST_BOT` (Claude, blog).

Rules: circle one phrase per title, never more. Circle the word a reader would search for or the payoff
("Grok Bot tips", "in a day", "this site."). Tip and blog post titles get the peeking bot but no circle, because
those titles come from data. Every new page builder should use `peek_h1` for its title. Example:
`B.peek_h1("Grok Bot " + B.circ("routines"), B.CHECKER_BOT)`

## Building blocks (class names)
| Block | Classes | Where |
|---|---|---|
| Comic button | `btn`, `btn pri` | everywhere |
| Handwritten note | `note` | above or below a heading |
| Speech bubble | `say` | hero; `.team-proof blockquote` on tip pages |
| Paper card | `card`, `card dark` | home, bottom |
| Stacking tip cards | `stack` > `tipc` | home; colours cycle red, blue, ochre, navy by position |
| Stickers | `stickers` | topic links |
| Stamp | `stamp` inside `badge` | home proof |
| Five steps | `steps` | home; keep each explanation to one short line |
| Scroll reveal | add `rv` | any block that should rise in as it enters the screen |

## Motion list
Load: headline lines slide up, bots pop in, underline draws. Always on: bots bob, blink and wave; shapes morph;
tape scrolls. Scroll: bots drift apart, the red line draws through the steps, cards stack (`position: sticky`),
the stamp lands. Hover: buttons press, cards change corner shape, stickers wiggle, a bot rises out of each card.
`prefers-reduced-motion` (Windows "Animation effects" off, Mac "Reduce motion" on) gets a calm version: fades and line-draws
stay; bobbing, drifting, sliding, spinning and the tape stop. Changed 2026-11-14 because Ryan's desktop showed a dead page.

**Do not** put `overflow: hidden` on `body`, `main`, or `.stack`'s parents. It breaks the stacking cards.

## How to publish each day (no design work needed)
**A blog post:** add `blog/posts/YYYY-MM-DD-slug.md` with front matter `title`, `date`, `description`,
`status: published` (optional `seo_title`, `seo_description`, `keywords`, `modified`). The build then:
- makes `/blog/<slug>/` in this design,
- lists it on `/blog/`,
- shows the newest three on the homepage under "Latest posts",
- adds it to `sitemap.xml`, `feed.xml` and `llms.txt`.

**A tip:** add it to `TIPS` (own page) or `HUB_ONLY` (hub only) in `tips.py`, with `PROS_CONS`, `CAPTIONS` and a
card image as today. Homepage counts and topic stickers update on their own. To change the four homepage cards,
edit `FEATURED_SLUGS` in `build.py`.

**SEO checklist for every post:** keyword at the start of the title, title 60 characters or less, description
155 or less, one `h1`, plain `h2` subheads that say what the section answers, link to two related tips, and link
back from one older page.

## Before every deploy
`python3 build.py && python3 selfcheck.py dist && python3 cjkcheck.py dist/index.html`
All three must pass. Then look at `/`, `/tips/` and one tip page at 390 px wide.

## Open items
- Tip brand cards, share images, `og_brand()` and `brand/x-visual-spec.md` now use this palette
  (renderer: `brand/render_cutouts.py`). Daily X cards live in `/workspace/shared/nab-relaunch/cards/`.
- Email signup is off (as before). When Ryan turns it back on, put the form in the `card dark` slot on the
  homepage, where "Follow the build on X" sits now.
