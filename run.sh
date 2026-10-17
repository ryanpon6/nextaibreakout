#!/usr/bin/env bash
# Full refresh: fetch -> score -> archive -> labs -> build [-> selfcheck] [-> deploy].
# SEO2=1 is passed to score, archive and build alike (scored-seo2.json); SEO2 unset/0 = production path (scored.json).
# DEPLOY=1 deploys dist/ to Cloudflare Pages. With SEO2=1 the build must pass selfcheck.py first or the deploy is skipped.
set -euo pipefail
cd "$(dirname "$0")"
export SEO2="${SEO2:-0}"
python3 fetch.py && python3 score.py
# Archive: record real top-10 appearances every run (data only)
python3 archive.py || echo "[archive] failed"
# Frontier Labs: LABS=1 fetches + publishes /labs pages.
if [[ "${LABS:-0}" == "1" ]]; then python3 labs.py || echo "[labs] fetch failed; building with last good data"; fi
python3 build.py
if [[ "$SEO2" == "1" ]]; then
  if ! python3 selfcheck.py dist; then
    msg="!!!!! SELFCHECK FAILED $(date -Is): SEO2 build in dist/ does not match scored-seo2.json or has content errors. DEPLOY SKIPPED. !!!!!"
    echo "$msg" >&2; echo "$msg" >> data/stale.log
    exit 3
  fi
fi
if [[ "${DEPLOY:-0}" == "1" ]]; then
  set -a; . "$HOME/.secrets/cloudflare.env"; set +a
  export CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-fdc58fb4586f5e0eea17aaebad49c994}"
  ./node_modules/.bin/wrangler pages deploy dist --project-name nextaibreakout --branch main --commit-dirty=true
fi
