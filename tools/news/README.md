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
## Switches
- **Kill switch:** delete `/workspace/shared/nab-relaunch/autopost-live.flag`. Live runs stop at step 0 and log a dated
  line saying so. Recreate the file (only after a QC PASS) to turn auto-publishing back on.
- **G12 money/plans/policy hold:** `tools/news/config.json` `"hold_money_policy": true` (default; also the default if
  the file or key is missing). To switch it off, set it to `false` and commit. `NAB_NEWS_CONFIG` can point at another
  config only in dry runs and selftests (`NAB_DRYRUN=1`); live runs always read the committed file.
- **Releasing a held post:** read `news/held-DATE.md`, then `python3 tools/news/publish.py --release DATE`.
  Needs the live flag; rebuilds and re-runs every gate, and only G12 is released. Preview with `--dry-run`.

## Alerts
Every failure path writes a dated entry to `/workspace/shared/nab-relaunch/autopost-issues.md` (dry runs write
`news/dryrun-issues.md` instead, so they never alert Ryan). `tools/news/watch_issues.py` (no AI) prints the lines
added since its last check and exits 1 when there is something new, 0 when not. State: `news/.issues-watch.json`.
On its very first run it reports the whole file once.

## Exit codes
fetch.py 0 story / 10 quiet / 2 bad input · gate.py 0 pass / 1 fail / 20 held · publish.py 0 done / 1 stopped / 20 held ·
xnews.py 0 ok / 1 refused / 2 auth / 3 definite X failure / 4 UNKNOWN (check by hand, never retried)

## X posting and retries (xnews.py, staged in /workspace/nextaibreakout/proposals/nab-news/)
- The ledger row (slot nab-news-DATE, `reply_ids: []`) is written under a lock, atomically, right after the main post
  returns an id, then updated with the reply id.
- Ambiguous result (timeout, 5xx, no id) on the main post or reply: row marked unknown, alert "unknown, check by
  hand", never retried; publish.py refuses that slot until a human fixes the row.
- Reply-only re-run: allowed only when the row has a main tweet_id and empty reply_ids (no reply_unknown).
- Every attempt first checks posted.jsonl and the @ryanpon timeline (text normalised: html.unescape, NFKC, whitespace).
- Offline tests: `xnews_selftest.py` (16 checks).

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
`related_tips` (2 slugs from `tips.TIPS`), `x_main` (<= 280 weighted, no links, must contain one verbatim quoted phrase of the key claim in quote marks), `body_md`.
In `body_md`: plain `##` subheads; quotes as `> exact post text ~ [Name (@user) on X, Mon D, YYYY](https://x.com/user/status/id)`;
every quote verbatim, every number from a cited post with its ~/about qualifier kept, no "this week"/"last week" (selfcheck.py blocks it).

## Gate (`gate.py`), proven by `selftest.py` (26 cases)
G1 ledger · G2 tip-slot timing (re-checked again right before the X post) · G3 rule 19 · G4 rule 20 design ·
G5 links 200 over HTTPS · G6 image · G7 claims (the gate re-fetches every cited post itself; quotes verbatim, the X
post carries one verbatim quoted phrase, numbers keep the source's ~/about qualifier) · G8 secrets · G9 SEO ·
G10 X text (twitter-text weighting) · G11 privacy · G12 money/plans/policy hold. Details in the file header.
The live check after deploy needs HTTP 200 and the post's title in the HTML.

## Tips-index hook
`entries_hook.py` adds `{id: slug, date, title, url: /blog/slug/, kind, type: news, source}` to `catalog.json`
(via `catalog.append()` when catalog.py exists). No-op while catalog.json is absent.
