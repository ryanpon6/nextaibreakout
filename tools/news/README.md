# Daily Grok Bot news pipeline (tools/news)

One routine a day. Scripts do the fetching and checking; the AI only writes when there is a real story.

| Step | File | AI? | What it does |
|---|---|---|---|
| 0 | routine agent | reads only | Grok Bot's public X tools (`x.search_news`, `x.search_posts_all`, `x.get_posts_by_ids`) -> `candidates-DATE.json` |
| 1 | `fetch.py` | no | re-reads every post from X's public embed endpoint (no login, no X API spend), dedupes against `trend-log.md` and `blog/posts/`, 24h window, notability bar, Grok Bot before Claude. Exit 10 = quiet day, stop. |
| 2 | routine agent | writes | `spec-DATE.json` (title, description, body, card text, X text) from `story-DATE.json` only |
| 3 | `make_post.py` | no | `blog/posts/DATE-slug.md` (kind: news), OG card `static/images/news/DATE-slug.png`, X card, `xpayload-DATE.json`, tips-index entry (`entries_hook.py`) |
| 4 | `publish.py` | no | build, selfcheck, cjkcheck, `gate.py`, commit + push main (ff only), wrangler deploy, live 200 check, X post + link reply (`xnews.py`), ledger |

State files live in `/workspace/shared/nab-relaunch/news/` (override with `NAB_NEWS_STATE`).
Live mode needs `/workspace/shared/nab-relaunch/autopost-live.flag`. Failures go to `autopost-issues.md`;
dry-run failures go to `news/dryrun-issues.md` so they never alert Ryan.

## candidates-DATE.json (written by the routine agent)
```json
{"date": "YYYY-MM-DD", "stories": [
  {"key": "grok-bot-usage-boost", "topic": "grokbot", "headline": "one line",
   "news_url": "https://x.com/i/trending/<id>", "post_ids": ["<id>", "<id>"]}]}
```
`topic` is `grokbot` or `claude`. Only ids are trusted; text is re-fetched by `fetch.py`.

## spec-DATE.json (written by the routine agent)
Keys: `slug`, `title`, `seo_title` (<= 60), `description` (<= 155), `keywords`, `note` (one short handwritten line),
`card_headline`, `card_points` (1-3 short lines), `card_source` (post id credited on the card), `image_alt`,
`related_tips` (2 slugs from `tips.TIPS`), `x_main` (<= 280, no links), `body_md`.
In `body_md`: plain `##` subheads; quotes as `> exact post text ~ [Name (@user) on X, Mon D, YYYY](https://x.com/user/status/id)`;
every quote verbatim, every number from a cited post, no "this week"/"last week" (selfcheck.py blocks it).

## Gate (`gate.py`), proven by `selftest.py` (17 broken builds, all caught)
G1 ledger · G2 tip-slot timing · G3 rule 19 · G4 rule 20 design · G5 links 200 over HTTPS · G6 image ·
G7 claims vs. fetched post text · G8 secrets · G9 SEO · G10 X text · G11 privacy. Details in the file header.
