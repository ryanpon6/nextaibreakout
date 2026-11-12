# NextAiBreakout X visual spec: Pacific Sea Teal and champagne gold (Nov 12, 2026)

Matches the live site at nextaibreakout.com after the Nov 12 relaunch. Tokens and line numbers below are from `static/style.css` in ryanpon6/nextaibreakout (the file the site serves; same values in `:root`, the prefers-dark block, and both `data-theme` blocks, L6–23). The site stays teal in every theme so champagne gold is never used as text on a light background. Renderer: `cards/make_daily_cards.py`, `"style": "teal"`. A proposed drop-in for that renderer lives in `proposals/cards-teal-gold/` until NAB Checker PASSes it. Do not edit the live renderer, and do not post, until then.

## Fonts (one family, self-hosted)
- **Archivo**, variable (wght 100–900, wdth 62–125%), OFL. **Self-hosted**: `fonts/fonts.css` line 1 has `@font-face{font-family:'Archivo';font-weight:100 900;font-stretch:62% 125%;src:url(/fonts/Archivo-var.woff2)}` with a Latin-only unicode-range, and `seo2.py` lines 11–12 and 98 swap build.py's Google Fonts link (build.py line 16, `family=Archivo:wdth,wght@62..125,100..900`) for the preload and that stylesheet. No mono or serif font.
- Stack: `style.css` line 6, `--f:'Archivo','Helvetica Neue',Arial,sans-serif` (same in every theme block).
- How the site uses it, and the card equivalent (static instances made with fontTools from the site's own woff2, saved in `fonts/archivo/`):

| Role | Site CSS | Card font file |
|---|---|---|
| Headline / big number | `h1,h2,h3{font-weight:800}` and `color:var(--accent)` (L37), `h2` at 125% stretch and tracking −0.04 em (L38), `.hero h1{font-size:104px;line-height:.92;font-stretch:125%;letter-spacing:-.045em}` (L76) | Archivo-ExpandedExtraBold (800 / 125%), tracking −0.03 to −0.05 em, in champagne gold #B8A188 when the type is large |
| Wordmark | `.brand span{font-weight:800;font-stretch:125%;letter-spacing:-.01em;color:var(--accent)}` (L43) | Archivo-ExpandedBold (700 / 125%) at card size, in #B8A188 |
| Stat lines | `.stats b{font-weight:800;font-stretch:112%}` (L197), `.mo b` 700/112% (L152) | Archivo-SemiExpandedBold (700 / 112%) |
| Rank numerals | `.rk{font-weight:200;font-stretch:125%;opacity:.6}` (L135) | Archivo-ExpandedExtraLight (200 / 125%) |
| Body, metrics, pills, sources | `body{font:400 16px/1.55}` (L27), nav 500, pills 500 (`.live` L74) | Archivo Regular / Medium / SemiBold / Bold (wdth 100%), body in off-white #F5F1E8 |
- Gap: the site's woff2 is a **Latin subset**, with no arrows (→ U+2192 missing). The renderer draws any missing glyph in DejaVu Sans Bold and notes it on stderr. Prefer words, or the drawn arrow in beforeafter.

## Colour tokens (live `static/style.css`)
Teal, which is what the cards use (every theme block is the same, L6–23):
`--bg #274043` (Benjamin Moore Pacific Sea Teal) · `--bg2 #1F3336` · `--panel #22393C` · `--ink #F5F1E8` · `--ink2 #D8D0C6` · `--mut #C5C0B6` · `--rule rgba(184,161,136,.28)` · `--rule2 rgba(184,161,136,.45)` · `--accent #B8A188` (champagne gold; also `--gold`) · `--gold-ink #BCA68E` · `--gold-hi #C9B8A5` · `--on-gold #1F3336` · `--glow rgba(184,161,136,.22)` · `--grid rgba(184,161,136,.08)`.

`--accent` / `#B8A188` is for headings, the logo and wordmark, borders, and buttons. `--gold-ink` / `#BCA68E` is the slightly lighter gold for small text and links. Body text is off-white `#F5F1E8`. A darker teal `#1F3336` is for panels and text on gold fills. Cards are teal only.

Retired, do not use on new cards: the Oct 18 gold `#F2C14E` / `#FFD98A`, green `#3DDC84`, the old near-black `#05070D`, purple, or pink. The renderer still accepts `"style": "gold"` (Oct 18 Escape Velocity) and `"style": "legacy-green"` so already-passed cards can be re-rendered unchanged. New work uses `"style": "teal"`.

WCAG contrast (computed against the tokens above):
- #B8A188 on #274043 is **4.47:1**. That just fails AA for small text (needs 4.5), but it passes for large text and UI (needs 3). Use it for headings, the wordmark, the logo, large numbers, and large quote marks. Never use it for small text or links.
- #BCA68E on #274043 is **4.73:1**, so it is the gold to use for small text and links.
- On #274043: ink #F5F1E8 is **9.80:1**, ink2 #D8D0C6 is **7.24:1**, mut #C5C0B6 is **6.10:1**, gold-hi #C9B8A5 is **5.73:1**. All pass AA for body text.
- On the darker teal #1F3336: ink 11.75, ink2 8.68, mut 7.31, #B8A188 5.36. All pass AA.
- #1F3336 on #B8A188 is **5.36:1** (AA), so it is the only text allowed on champagne-gold fills. Off-white or white on #B8A188 is 2.19 / 2.47:1, so never use those.
- #B8A188 on #F5F1E8 or on white is 2.19 / 2.47:1, so never use gold text on a light background. The site no longer has a light theme for this reason.
- Worst case, mut over the peak champagne glow (gold at 22% on #274043, about #475552): 4.31:1. That fails AA for small text but still passes for large text (3:1). Keep the glow away from small text, and do not shrink the source line below 24 px if it might sit on the glow.

## Chart style (live style.css L71 and L79–88)
- Line: 3.2 px, round joins and caps, horizontal gradient from champagne gold at 25% opacity, to solid #B8A188 at 55%, to #C9B8A5 at the end. On a 1600 px card it's 5 px.
- Glow: the same path at 10 px, #B8A188 at .32 opacity, Gaussian blur (stdDeviation 6). Card: 13 px, blur 8.
- Area: a fill under the line, a vertical gradient from #B8A188 .22 to 0.
- Tip: a 6 px #B8A188 dot plus a 14 px ring (1.5 px stroke, .5 opacity) on the last point.
- Gridlines: horizontal 1 px `rgba(184,161,136,.08)`. The site draws them every 72 px across the hero, faded in at the top and out at the bottom. Cards keep 3 or 4 inside the chart, and the baseline uses --rule.
- Axis labels: two muted labels only, start and end (`.hc-axis`: 13 px, --mut, tabular numbers). No y-axis numbers. Points sit evenly by check, not by time, so when check gaps vary, say so on the card ("Evenly spaced by check; gaps vary.") and count changes as "N checks".
- The data must be real snapshots, never interpolated. The renderer asserts 3+ points that change.
- Background glow: `radial-gradient(800px 380px at 72% 66%, var(--glow), transparent 70%)` (L71), where `--glow` is `rgba(184,161,136,.22)`.

## Logo mark
The site's own SVG (build.py L21–22, viewBox 32): the frame `M17 5H5v22h22V15` and the "break" `M10.5 21.5L27 5M19 5h8v8` are both champagne gold #B8A188, stroke 2.6, square caps. The favicon (`static/favicon.svg`) is the same mark, both strokes #B8A188, on a #274043 rounded square.
- Cards: 44 px mark at top left, both strokes #B8A188, then "NextAiBreakout" in Archivo Expanded Bold 28 px, also #B8A188.
- Never recolour the mark to green, the old #F2C14E gold, purple, or pink. Never put the domain on a card.

## Card system
- Size: **1600×900** (16:9, the current size). `"size": "1200x675"` is available. The renderer draws at 2× and downsamples, so edges are antialiased.
- Margins: 80 px left and right. Header band at y 60–110. Footer rule at y 766, with "Source: …" in mut Archivo Regular 28 below it.
- Whitespace: one idea per card, at most 4 data rows, and nothing below the source line.
- Pill (top right, `.live` look): 1 px rule2 border, panel fill #22393C, champagne-gold dot with a soft halo, Medium 22 ink2. It holds a kicker ("Day 1", "Quality", "Week 1"). Use the word "Live" only when the numbers were checked within the hour.
- Site headlines can set a phrase in the small-gold token (`.accent{color:var(--gold-ink)}`, L31). The card renderer does not do accent words yet. Use #B8A188 for large numbers and the one thing to see, and #BCA68E if that gold text is small.
- Champagne gold as text marks the one thing to see (the better value, the big number, the stat line) when the type is large. Everything else is ink or ink2. Small gold text, if any, uses #BCA68E.

Layouts (all keep the earlier JSON fields; the optional field is `kicker`):
1. **Compare** (`compare`). Headline title (Expanded ExtraBold 60, one line or a balanced two, in #B8A188 or ink). Column pills for the two variants. 1–4 rows with metric names in Medium ink and values in Expanded ExtraBold, the better value in #B8A188 and the other in ink2. A note line in ink2, then the source.
2. **Big number** (`bignum`). The number in Expanded ExtraBold up to 270 px, #B8A188, with a pale champagne glow behind it. Label in SemiExpanded Bold 60 ink, sub in Regular 36 ink2, then the source.
3. **Line chart** (`chart`, teal or gold). Item name as the headline, delta in #B8A188 with glow, a muted context line, then the hero-style chart and the two axis labels.
4. **Quote** (`quote`). Dark teal field, a large #B8A188 quotation mark, the quote in off-white SemiBold, attribution in #B8A188, optional context in mut, then the source.

`default`, `beforeafter` and `quote` all have teal versions (the quote card is teal, with a champagne quotation mark).

## Rules for every card and post
- **Mix:** stat cards in about 1 post in 3. The rest are real, credited screenshots or the source's own visuals (README images, model-card charts, GIFs), or text-only. Never 3 of the same visual type in a row (check_variety rule e).
- **No images of real people** on cards. Screenshots follow Checker's HN preset (title, points, submitter, no comments). No private names on a card.
- **Attribute every stat on the card** ("Source: …, as of <time and date in the timezone the fact was checked>"). Mark vendor claims as "per <vendor>". Do not invent numbers.
- **No URLs or domains** in card text. The NextAiBreakout name and mark are fine. Do not put "nextaibreakout.com" in the footer.
- Card text uses only glyphs Archivo has. Don't shrink text below the renderer's floors (it raises instead).
- **Re-rendering passed cards:** `"style": "legacy-green"` (or `--style legacy-green`) still reproduces pre-gold cards byte-identically. `"style": "gold"` still reproduces the Oct 18 Escape Velocity cards. New cards use `"style": "teal"` (or `--style teal`).

The Day 1 sample rendered from this spec (quote layout, exact main-post copy from the relaunch drafts) is at `/workspace/shared/nab-relaunch/cards/day1.png`. It is a local render only; nothing was posted.
