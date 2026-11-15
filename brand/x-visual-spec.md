# NextAiBreakout X visual spec: Bot Cut-outs (Nov 12, 2026)

Matches the live site after the Bot Cut-outs redesign (Claude, commit 420352a, chosen by Ryan). Read `DESIGN.md` in the repo root before changing a card, a tip, or a colour. The earlier Pacific Sea Teal and gold look is retired for new work. A teal Day 1 card is kept as `day1.png.bak-teal` in `/workspace/shared/nab-relaunch/cards/`.

Renderer: `brand/render_cutouts.py`. Tip brand cards live in `static/images/tips/*.webp` (1200×675) with matching `*-og.jpg` share images (1200×630). The default share image is `static/og-default.jpg` (1200×630; a PNG is kept at `static/og-default.png` for the old URL), produced by `brand/render_og_photo.py` and copied by `og_brand()` in `build.py`. Tip cards still use `brand/render_cutouts.py`. Daily X cards are 1600×900 PNGs in `/workspace/shared/nab-relaunch/cards/dayN.png`.

## The idea
A pale gallery wall with paper cut-out shapes, drawn like a comic. Three original robots stand for the three roles on this site. Do not swap in the Grok logo, the xAI logo, or any other company's mascot.

## Tokens (from `DESIGN.md` / `static/style.css`)
| Token | Value | Use |
|---|---|---|
| `--bg` | `#E9EEF2` | page and card background |
| `--paper` | `#FFFFFF` | paper cards, speech bubbles |
| `--ink` | `#0F1B3D` | all text, outlines, hard shadows |
| `--mut` | `#46506B` | secondary text, footers |
| `--red` | `#FF4B2B` | fills only (lead bot, some shapes) |
| `--red-ink` | `#B92E16` | red **text** and links (passes AA on `--bg`) |
| `--blue` | `#2747F5` | fills; white text is allowed on it |
| `--och` | `#F2B01E` | fills; ink text only |
| `--sky` | `#BFD0FF` | decorative shapes only |

Rules: never white text on red or ochre. Never red `#FF4B2B` as text on the pale background; use `--red-ink`. Outlines are always `3px solid` ink. Shadows are hard and offset (`7px 7px 0` ink), never blurred.

## Type (self-hosted in `fonts/`, all OFL)
- **Syne 800**: headings and the wordmark. It is very wide, so keep headings short.
- **DM Sans**: body, quotes, tip lines, Pros/Cons copy, footers.
- **Gochi Hand**: at most one short handwritten note per card (class `note`). Never body copy.

System TTFs used by the renderer: Syne, DM Sans and Gochi Hand under `/usr/share/fonts/truetype/sand-box/google/`.

## The robots
| Character | Look |
|---|---|
| Lead bot | red, rounded head, ochre antenna tip |
| Specialist | blue, square head |
| Quality Checker | ochre, one big monocle eye |
| Brand mark | the lead-bot head beside "NextAiBreakout" in Syne 800 ink (also the favicon) |

Draw them in flat colour, with ink outlines and hard shadows, the same way `bot()` / `bot_head()` do on the site. No photos of people. No domain name on an X card (the site OG image may show nextaibreakout.com).

## Card anatomy
- **Tip brand cards (1200×675)** and **OG share crops (1200×630):** wordmark + topic pill, a paper cut-out (or a number / compare / before-after layout), footer "From my Grok Bot setup". Same text as the previous teal cards; only the palette and type change.
- **X cards (1600×900):** wordmark + Day N pill, one Gochi Hand title, the tip line, a Pros card and a Cons card, then the same footer. Pros heading is blue; Cons heading is `--red-ink`. No question, no prompt, no domain, no people.
- Pills are ochre fills with ink text, a 3px ink outline and a hard offset shadow.
- Decorative ochre and sky shapes, and a dotted field, sit behind the type and must not cover it.

## Layouts
1. **Quote.** A large paper card, a `--red-ink` opening quotation mark, the quote in DM Sans, the tip title in Syne `--red-ink`. Optional muted sub-line.
2. **Big number.** The number on an ochre cut-out in Syne ink, then a Syne label and a muted sub-line. Used for Blabara "1 day".
3. **Compare.** A Syne headline, two pills, then a paper row with the weaker value in muted ink and the better value in a blue fill with white text.
4. **Before / after.** A Syne headline, a muted "before" paper card, a blue arrow, and an ochre "after" card with ink text.

## Rules for every card
- Same text content when re-rendering an existing tip or X card. Spell every word correctly and keep it fully inside the frame.
- No placeholders, no empty slots, no "coming soon".
- No Grok or xAI logos. No photos of people. No invented numbers.
- Look at every rendered image before shipping.
- Re-rendering a passed teal card: keep a `.bak-teal` copy first. New work uses this spec only.

The Day 1 X card rendered from this spec is `/workspace/shared/nab-relaunch/cards/day1.png`. Nothing is posted until Ryan approves the text and the image.
