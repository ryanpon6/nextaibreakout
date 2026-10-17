#!/usr/bin/env bash
# Pipeline state (data/: hourly snapshots, archive, labs/grokbot caches, scored files) lives on the orphan
# branch `state`, separate from the code on `main`.  Usage: ci/state.sh restore|save
# init: worktree; restore: copy state/<files> -> data/   save: copy data/ -> state/, commit, push (rebuilds the branch as one
# commit when it passes MAX_COMMITS so the repo doesn't grow without bound).
set -euo pipefail
cd "$(dirname "$0")/.."
S=state; MAX_COMMITS="${MAX_COMMITS:-336}"   # ~2 weeks of hourly commits
case "${1:-}" in
  init)   # check out the state branch as a worktree at ./state (creates an empty orphan branch on the first run)
    if git ls-remote --exit-code --heads origin state >/dev/null 2>&1; then
      git fetch -q origin state:state && git worktree add -q "$S" state
    else
      git worktree add -q --detach "$S" && (cd "$S" && git checkout -q --orphan state && git rm -rqf . 2>/dev/null || true)
    fi; echo "state: worktree ready" ;;
  restore)
    mkdir -p data
    if [[ -d "$S/data" ]]; then cp -a "$S/data/." data/; echo "state: restored $(find data -type f | wc -l) files"; else echo "state: none yet (first run)"; fi ;;
  save)
    [[ -e "$S/.git" ]] || { echo "state: no checkout at ./$S"; exit 1; }
    rm -rf "$S/data"; mkdir -p "$S/data"
    cp -a data/. "$S/data/"   # then drop runner-local files (locks, logs, pids)
    find "$S/data" \( -name '*.lock' -o -name 'cron.log' -o -name 'tick-loop.*' -o -name 'last_success' -o -name '*.tmp' \) -delete
    cd "$S"; git config user.name "nab-refresh"; git config user.email "nab-refresh@users.noreply.github.com"
    git add -A data
    if git diff --cached --quiet; then echo "state: unchanged"; exit 0; fi
    msg="state $(date -u +%FT%TZ) run ${GITHUB_RUN_ID:-local}"
    if [[ "$(git rev-list --count HEAD 2>/dev/null || echo 0)" -ge "$MAX_COMMITS" ]]; then
      git checkout -q --orphan state-new && git commit -qm "$msg (history squashed)" && git branch -D state 2>/dev/null || true
      git branch -m state && git push -f origin state
    else
      git commit -qm "$msg" && git push origin HEAD:state
    fi ;;
  *) echo "usage: $0 init|restore|save"; exit 2 ;;
esac
