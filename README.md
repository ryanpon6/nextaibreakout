# Breakout AI — nextaibreakout.com
"Tracking the road to superintelligence." Static site ranking AI models, tools/repos and news by **growth rate**, refreshed hourly.

## Pipeline (Python 3 stdlib only)
- `fetch.py` → public APIs → `data/snapshots/<UTC>.json` (keeps ~14 days)
  - GitHub search (repos created in last 30d, topics llm/ai-agents/generative-ai/mcp/machine-learning). Uses `GITHUB_TOKEN` if set; else paced for the 10 req/min unauth search limit.
  - Hugging Face `/api/models` and `/api/spaces?sort=trendingScore`
  - npm downloads API, pypistats.org (fixed AI package lists in fetch.py)
  - Hacker News Algolia (last 36h, points>15; AI-title filter applied in score.py)
  - Deliberately skipped: Product Hunt (non-commercial API terms), Reddit (commercial use needs contract), X (paid API).
- `score.py` → `data/scored.json`. Velocity = metric delta per hour vs the snapshot ≥45 min older; on first run falls back to stars/day since creation, HF trendingScore, HN points/hour, downloads vs 7-day avg. Percentile-ranked within each source (65% velocity, 35% relative growth), +15% if <3 days old; top 10 max 3 per source. Text = item's own description + a factual metric line (no invented claims).
- `build.py` → `dist/` (index.html, about.html, style.css, sitemap.xml, robots.txt, llms.txt, data.json, favicon/og svg).
- `./run.sh` runs all three; `DEPLOY=1 ./run.sh` also deploys.

## Deploy plan (not done yet)
1. Cloudflare dashboard → API token with **Cloudflare Pages: Edit** (account scope). Note Account ID.
2. On the box: `export CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=...`
3. First deploy: `npx wrangler pages project create nextaibreakout --production-branch main` then `DEPLOY=1 ./run.sh`.
4. Pages project → Custom domains → add `nextaibreakout.com` (+ `www`); domain is already on Cloudflare so DNS is automatic.
5. Hourly refresh, option A (simplest): box cron  
   `7 * * * * cd /workspace/nextaibreakout && DEPLOY=1 ./run.sh >> data/cron.log 2>&1`  
   Option B: port fetch/score to a Cloudflare Worker with a `0 * * * *` cron trigger writing to KV/R2 and serving HTML; independent of the box, more work.
6. Optional: set `GITHUB_TOKEN` (fine-grained, no scopes) for 30 req/min search.

## TODO before launch
Email provider (beehiiv/Buttondown) for signup form; sponsor booking (Stripe Payment Link); PNG og image (some platforms ignore SVG); analytics (Cloudflare Web Analytics, free).
