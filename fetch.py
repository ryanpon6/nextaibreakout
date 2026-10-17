"""Pull free, ToS-safe public APIs and store an hourly snapshot."""
import datetime as dt, json, os, sys, time, urllib.parse as up
from common import get_json, SNAP, DATA, add_alias, canon
NOW = dt.datetime.now(dt.timezone.utc)
errors, items = [], []
def safe(name, fn):
    try:
        n = fn(); print(f"[ok] {name}: {n}")
    except Exception as e:
        errors.append(f"{name}: {e}"); print(f"[fail] {name}: {e}", file=sys.stderr)

def github():
    hdr = {"Accept": "application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"): hdr["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    since = (NOW - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    seen = {}
    for q in ["topic:llm", "topic:ai-agents", "topic:generative-ai", "topic:mcp", "topic:machine-learning"]:
        url = "https://api.github.com/search/repositories?" + up.urlencode(
            {"q": f"{q} created:>{since}", "sort": "stars", "order": "desc", "per_page": 40})
        for r in get_json(url, hdr).get("items", []):
            seen[r["full_name"]] = dict(id="gh:" + r["full_name"], source="github", kind="tool",
                name=r["full_name"], url=r["html_url"], desc=(r.get("description") or "").strip(),
                metric=r["stargazers_count"], metric_name="stars", created=r["created_at"],
                extra={"forks": r["forks_count"], "lang": r.get("language"), "topics": r.get("topics", []), "repo_id": r.get("id")})
        time.sleep(2 if "Authorization" in hdr else 7)  # unauth search limit: 10/min
    gh_renames(seen, hdr)
    items.extend(seen.values()); return len(seen)

def gh_renames(seen, hdr):
    """Follow GitHub renames. The API always returns the canonical full_name (old names redirect), so:
    1) a known numeric repo ID whose full_name changed is a rename;
    2) archived repos missing from this run's search are re-checked (at most once a day) via /repos/<old name>,
       which redirects to the canonical repo.
    Each rename is recorded in data/gh_aliases.json (old ID -> new ID) so score/archive/seo2 merge the history."""
    import glob
    rp = os.path.join(DATA, "gh_repos.json")
    try: R = json.load(open(rp))
    except Exception: R = {"ids": {}, "checked": {}}
    for fn, x in seen.items():
        rid = str(x["extra"].get("repo_id") or "")
        if not rid: continue
        old = R["ids"].get(rid)
        if old and old != fn: add_alias("gh:" + old, "gh:" + fn)
        R["ids"][rid] = fn
    names = set()
    for p in glob.glob(os.path.join(DATA, "archive", "items", "gh-*.json")):
        try: iid = json.load(open(p))["id"]
        except Exception: continue
        if iid.startswith("gh:") and canon(iid) == iid: names.add(iid[3:])
    now = time.time(); n = 0
    for fn in sorted(names - set(seen)):
        if now - R["checked"].get(fn, 0) < 86400 or n >= 10: continue
        n += 1; R["checked"][fn] = now
        try: r = get_json(f"https://api.github.com/repos/{fn}", hdr, retries=0)
        except Exception: continue  # 404 (deleted) or rate-limited: leave as is
        if r.get("id"): R["ids"][str(r["id"])] = r["full_name"]
        if r.get("full_name") and r["full_name"].lower() != fn.lower(): add_alias("gh:" + fn, "gh:" + r["full_name"])
    tmp = rp + ".tmp"; json.dump(R, open(tmp, "w"), indent=1); os.replace(tmp, rp)

def hf():
    n = 0
    for kind, ep in (("model", "models"), ("space", "spaces")):
        url = f"https://huggingface.co/api/{ep}?sort=trendingScore&limit=40" + ("&full=true" if kind == "space" else "")
        for m in get_json(url):
            mid = m["id"]; card = m.get("cardData") or {}
            desc = m.get("pipeline_tag") or ""
            if kind == "space": desc = m.get("sdk") or ""  # (production display unchanged; real title/summary kept in extra)
            items.append(dict(id=f"hf{kind}:{mid}", source="huggingface", kind="model" if kind == "model" else "tool",
                name=mid, url=f"https://huggingface.co/{'spaces/' if kind=='space' else ''}{mid}", desc=desc,
                metric=m.get("likes", 0), metric_name="likes", created=m.get("createdAt"),
                extra={"downloads": m.get("downloads"), "trending": m.get("trendingScore"), "hf_type": kind,
                       "title": card.get("title"), "summary": card.get("short_description"), "sdk": m.get("sdk")}))
            n += 1
    return n

NPM = ["openai", "@anthropic-ai/sdk", "ai", "langchain", "@langchain/core", "@modelcontextprotocol/sdk",
       "@google/genai", "ollama", "llamaindex", "@mistralai/mistralai", "groq-sdk", "@xai-org/sdk"]
PYPI = ["openai", "anthropic", "transformers", "langchain", "llama-index", "vllm", "mcp", "litellm",
        "google-genai", "ollama", "crewai", "dspy", "smolagents", "pydantic-ai", "sglang", "unsloth"]
def npm():
    n = 0
    for p in NPM:
        try: d = get_json("https://api.npmjs.org/downloads/range/last-week/" + p)
        except Exception: continue
        days = [x["downloads"] for x in d.get("downloads", [])]
        if len(days) < 2: continue
        items.append(dict(id="npm:" + p, source="npm", kind="tool", name=p, url="https://www.npmjs.com/package/" + p,
            desc="npm package", metric=days[-1], metric_name="downloads/day", created=None,
            extra={"week": sum(days), "days": days})); n += 1
    return n
def pypi():
    n = 0
    for p in PYPI:
        try: d = get_json(f"https://pypistats.org/api/packages/{p}/recent")["data"]
        except Exception: continue
        items.append(dict(id="pypi:" + p, source="pypi", kind="tool", name=p, url="https://pypi.org/project/" + p,
            desc="Python package", metric=d["last_day"], metric_name="downloads/day", created=None,
            extra={"week": d["last_week"], "month": d["last_month"]})); n += 1
        time.sleep(1)
    return n
def hn():
    seen = {}
    t0 = int((NOW - dt.timedelta(hours=36)).timestamp())
    for q in ["AI", "LLM", "GPT", "Claude", "Gemini", "Grok", "OpenAI", "model", "agent", "AGI"]:
        url = "https://hn.algolia.com/api/v1/search_by_date?" + up.urlencode(
            {"query": q, "tags": "story", "numericFilters": f"created_at_i>{t0},points>15", "hitsPerPage": 50})
        for h in get_json(url).get("hits", []):
            if h["objectID"] in seen: continue
            seen[h["objectID"]] = dict(id="hn:" + h["objectID"], source="hackernews", kind="news",
                name=h["title"], url=h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                desc="", metric=h.get("points", 0), metric_name="points", created=h["created_at"],
                extra={"comments": h.get("num_comments"), "hn": f"https://news.ycombinator.com/item?id={h['objectID']}"})
    # HN posts that link a GitHub repo: record the repo's creation date so score.py can down-rank old repos
    hdr = {"Accept": "application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"): hdr["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    for it in list(seen.values()):
        p = up.urlparse(it["url"])
        parts = [x for x in p.path.split("/") if x]
        if p.netloc.lower() in ("github.com", "www.github.com") and len(parts) >= 2:
            try:
                r = get_json(f"https://api.github.com/repos/{parts[0]}/{parts[1]}", hdr, retries=0)
                it["extra"]["repo_created"] = r["created_at"]
                if r.get("full_name"):  # canonical name after any rename
                    it["extra"]["repo"] = r["full_name"]; add_alias(f"gh:{parts[0]}/{parts[1]}", "gh:" + r["full_name"])
            except Exception: pass  # rate-limited or missing: skip quietly
    items.extend(seen.values()); return len(seen)

if __name__ == "__main__":
    for n, f in (("github", github), ("huggingface", hf), ("npm", npm), ("pypi", pypi), ("hackernews", hn)): safe(n, f)
    os.makedirs(SNAP, exist_ok=True)
    path = os.path.join(SNAP, NOW.strftime("%Y%m%dT%H%M") + ".json")
    json.dump({"taken": NOW.isoformat(), "errors": errors, "items": items}, open(path, "w"))
    print("snapshot", path, len(items), "items")
    snaps = sorted(os.listdir(SNAP))
    for old in snaps[:-24 * 14]: os.remove(os.path.join(SNAP, old))  # keep ~14 days hourly
