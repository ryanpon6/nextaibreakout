# Catalog: how a new post registers itself

`catalog.json` is the source of truth for dated lists on this site:

- the homepage latest Grok Bot tips (up to 3, newest first)
- the homepage latest Claude Tips (up to 3, or fewer if that is all that exists — never empty slots)
- the dated list of every Grok Bot tip on `/tips/`
- the dated list of every Claude tip on `/claude/`

Tip *bodies* still live in `tips.py`. Blog posts still live in `blog/posts/`. The catalog only stores listing metadata so a daily news auto-post can append one row and the lists update on the next build.

## Fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Stable id, unique. Use the slug (`talk-to-one-lead-bot`, `nab-news-2026-11-15`). |
| `date` | yes | Real publish date, `YYYY-MM-DD`. Never invent one. Use the post's own date, front matter, or the git commit that first added it. |
| `title` | yes | The public title. |
| `url` | yes | Site path, starting with `/`. A full page ends in `/`. A hub-only tip uses an anchor (`/tips/#one-job-per-bot`). |
| `kind` | yes | `grok` or `claude`. |
| `type` | yes | `tip` or `news`. |
| `summary` | no | One short line for the list. Do not invent claims. |
| `seq` | no | Integer tie-break when two entries share a date. Higher is newer. If you omit it, `catalog.append` sets the next value for that date and kind. |
| `source` | no | Where the date came from (commit, front matter). Keep this so dates stay auditable. |

Counts on the site are computed from this file (and from `tips.py` for topic stickers). Never type "3 tips" or "20 tips" into copy.

## Sort order

Newest first: `date` descending, then `seq` descending, then `id`. The 20 Grok Bot tips all share the publish date 2026-11-12 (see each row's `source`). Their `seq` is the order they were registered that day: the 14 full tip pages (Days 1–14), then the 6 hub-only tips that landed in a later commit the same morning.

## How the news pipeline should append

After a finished news page is written into `dist` (or into the repo) and before the site build:

```python
import catalog
catalog.append({
    "id": "nab-news-2026-11-15",          # example id
    "date": "2026-11-15",                 # the real publish date
    "title": "The post title",
    "url": "/news/the-post-slug/",        # the live path of the page you just wrote
    "kind": "grok",                       # or "claude"
    "type": "news",
    "summary": "One short factual line.",
    "source": "Appended by the daily news pipeline on 2026-11-15.",
})
```

Or edit `catalog.json` by hand with the same fields, then run `python3 catalog.py` to validate.

Then run the normal default build (`python3 build.py && python3 cjkcheck.py dist/index.html`). Do not pad lists: `catalog.latest(3, kind="grok", type="tip")` returns fewer than 3 when fewer exist.

## What shows up where

- Grok tip lists and the Grok homepage strip: `kind=grok` and `type=tip`.
- Claude tip lists and the Claude homepage strip: `kind=claude` and `type=tip`.
- `type=news` is reserved for a news list or strip. There is no news section on the site until at least one news entry exists (rule 19: no empty slots). When you append the first news row, add the list in the same Bot Cut-outs pattern as "Latest posts" (see `DESIGN.md`).

Existing URLs stay as they are. A news page should pick a new path (`/news/<slug>/` is the expected shape) and 301 only if an old path is retired.

## Dates already in this file

- 14 Grok tip pages: 2026-11-12, first added in commit `803137e`.
- 6 hub-only Grok tips: 2026-11-12, first added in commit `a7fdbdf`.
- Claude Code Android TV guide: 2026-10-19, blog front matter and commit `ace6dcc`. The live URL stays `/blog/claude-code-android-tv-debloat/`.
