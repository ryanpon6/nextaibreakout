"""Breakout score = growth rate (velocity + relative growth), not raw size."""
import datetime as dt, json, math, os, re
from common import SNAP, DATA, canon, aliases
def ts(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
def load():
    files = sorted(os.listdir(SNAP)); cur = json.load(open(os.path.join(SNAP, files[-1])))
    now = ts(cur["taken"]); prev = None
    for f in reversed(files[:-1]):  # newest snapshot at least 45 min older
        s = json.load(open(os.path.join(SNAP, f)))
        if (now - ts(s["taken"])).total_seconds() >= 2700: prev = s; break
    return cur, prev, now
def fmt(n):
    n = float(n)
    return f"{n/1e6:.1f}M" if n >= 1e6 else f"{n/1e3:.1f}K" if n >= 1e3 else f"{n:.0f}"
def clean(s, n=140):
    s = re.sub(r"\s+", " ", re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "", s or "")).strip(" -:|")
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"
FRONTIER = ("openai", "meta-llama", "google", "qwen", "deepseek-ai", "mistralai", "microsoft", "nvidia",
            "moonshotai", "zai-org", "xai-org", "anthropic", "minimaxai", "ibm-granite", "allenai", "stepfun-ai")
AI_RE = re.compile(r"\b(AI|AGI|LLMs?|GPT[-\w.]*|Claude|Gemini|Grok|OpenAI|Anthropic|DeepSeek|Qwen|Llama|Mistral|xAI|agents?|agentic|MCP|inference|transformer|diffusion|neural|machine learning|chatbot|superintelligence|Copilot|Hugging ?Face|[\w.-]*-\d+B[\w-]*)\b", re.I)
GH_AI = re.compile(r"\b(ai|llms?|agents?|agentic|mcp|gpt|claude|gemini|grok|openai|anthropic|model|models|inference|rag|embedding|transformer|diffusion|neural|machine learning|deep learning|copilot|codex|prompt|fine-?tun\w*|vlm|multimodal|speech|tts|asr)\b", re.I)
GH_OFF = re.compile(r"(calorie|recipe|food|diet|restaurant|mcdonald|麦当劳|热量|game cheat|crypto airdrop)", re.I)
OPINION = re.compile(r"(^(ask|tell) hn|\?$|^(why|i|i'm|my|is|are|should|what if|how i|we need|stop|in defense)\b|until it|thoughts on|the case (for|against)|considered harmful|is dead|is overrated)", re.I)
OPINION_HOSTS = ("substack.com", "medium.com", "bearblog.dev")
SEO2 = os.getenv("SEO2") == "1"
SCORED = "scored-seo2.json" if os.getenv("SEO2") == "1" else "scored.json"  # staging and production never share a file
def write_scored(res):
    """One writer per file: exclusive flock on <file>.lock, then atomic replace."""
    import fcntl, tempfile
    p = os.path.join(DATA, SCORED)
    with open(p + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        fd, tmp = tempfile.mkstemp(dir=DATA, prefix=SCORED + ".")
        with os.fdopen(fd, "w") as f: json.dump(res, f, indent=1)
        os.replace(tmp, p)  # staged fixes (tagging, Spaces) only when SEO2=1; production scoring unchanged
MODEL_WORDS = re.compile(r"\b(models?|weights|llms?|checkpoints?|\d+(\.\d+)?b|fine-?tuned?|vlm|text-generation|image-text-to-text|text-to-image|text-to-speech)\b", re.I)
def weak_space(i):
    return i["source"] == "huggingface" and i["extra"].get("hf_type") == "space" and (i.get("desc") or "").strip().lower() in ("", "static", "gradio", "streamlit", "docker")
def score():
    cur, prev, now = load()
    AL = aliases()  # GitHub renames: older snapshots carry the old ID; key history by the canonical one
    pv = {canon(i["id"], AL): i for i in (prev or {}).get("items", [])}
    hrs = (now - ts(prev["taken"])).total_seconds() / 3600 if prev else None
    nsnap = {}
    for f in sorted(os.listdir(SNAP)):
        for x in json.load(open(os.path.join(SNAP, f)))["items"]: c = canon(x["id"], AL); nsnap[c] = nsnap.get(c, 0) + 1
    out = []
    for it in cur["items"]:
        if it["source"] == "hackernews":
            if not AI_RE.search(it["name"]) or OPINION.search(it["name"]) or any(h in it["url"] for h in OPINION_HOSTS): continue
        if it["source"] == "github":
            blob = " ".join([it.get("desc") or ""] + it["extra"].get("topics", []))
            if (it["metric"] or 0) < 50 or not GH_AI.search(blob.replace("-", " ")) or GH_OFF.search(blob): continue
        age_h = max((now - ts(it["created"])).total_seconds() / 3600, 1) if it.get("created") else None
        m, p, why = it["metric"] or 0, pv.get(it["id"]), ""
        if it["source"] in ("npm", "pypi"):
            avg = (it["extra"]["week"] or 1) / 7
            vel, rel = m - avg, m / max(avg, 1)
            why = f"{fmt(m)} downloads yesterday, {rel:.2f}× its 7-day average."
            if rel < 1.15: continue  # only show packages that are actually accelerating
        elif p and hrs and not (it["source"] == "github" and nsnap.get(it["id"], 0) < 3):
            vel = (m - (p["metric"] or 0)) / hrs; rel = vel / max(p["metric"] or 1, 30)
            why = f"+{fmt(max(vel*24,0))} {it['metric_name']}/day pace right now ({fmt(m)} total)."
        elif it["source"] == "huggingface":
            vel = it["extra"].get("trending") or 0; rel = vel / max(m, 1)
            why = f"Trending score {vel} on Hugging Face; {fmt(m)} likes, {fmt(it['extra'].get('downloads') or 0)} downloads."
        else:
            vel = m / (age_h or 720) * 24; rel = 1 / math.sqrt((age_h or 720) / 24)
            unit = it["metric_name"]
            why = (f"{fmt(m)} points in {age_h:.0f}h on Hacker News ({it['extra'].get('comments') or 0} comments)."
                   if it["source"] == "hackernews" else f"{fmt(m)} stars since launch {max(age_h/24,1):.0f} days ago ≈ {fmt(vel)} stars/day since launch.")
        it["true_vel"] = bool(p and hrs) and not (it["source"] == "github" and nsnap.get(it["id"], 0) < 3)
        # stale-repo guard: GitHub repos (or HN posts of GitHub repos) older than ~60 days are down-ranked
        # unless they show real recent velocity from 3+ snapshots
        rc = it["created"] if it["source"] == "github" else (it.get("extra") or {}).get("repo_created")
        it["stale"] = bool(rc and (now - ts(rc)).days > 60 and not (it["source"] == "github" and it["true_vel"] and vel > 2))
        it.update(vel=vel, rel=rel, why=why, what=clean(it.get("desc")) or "")
        if it["source"] == "huggingface" and it["extra"].get("hf_type") == "model":
            it["what"] = (f"{it['desc']} model" if it["desc"] else "Model") + " on Hugging Face"
        out.append(it)
    # percentile-rank velocity and relative growth within each source, so sources are comparable
    for src in {i["source"] for i in out}:
        g = [i for i in out if i["source"] == src]
        for key in ("vel", "rel"):
            for r, i in enumerate(sorted(g, key=lambda x: x[key])): i[key + "_p"] = (r + 1) / len(g)
        for i in g:
            fresh = 1.15 if i.get("created") and (now - ts(i["created"])).days < 3 else 1.0
            i["raw"] = (0.65 * i["vel_p"] + 0.35 * i["rel_p"]) * fresh * (0.3 if i["stale"] else 1.0) * (0.5 if SEO2 and weak_space(i) else 1.0); i["score"] = round(100 * min(1, i["raw"]), 1)
    for i in out: i["raw"] += 0.001 * math.log10(max(i["vel"], 0) + 1)  # tie-break by absolute pace
    out.sort(key=lambda x: (-x["raw"], x["id"]))  # deterministic ties: score desc, then type+ID
    n = len(out)  # rescale: global rank -> 99 (top) down to ~10, so scores don't cluster at 100
    for r, i in enumerate(out): i["score"] = round(10 + 89 * (1 - r / max(n - 1, 1)) ** 2, 1)
    top, cap = [], {}
    for i in out:  # top 10 with source diversity
        if i["stale"] or (i["source"] == "hackernews" and (i["metric"] or 0) < 40): continue  # no stale repos / thin HN posts in top 10
        if cap.get(i["source"], 0) < 3 and i["score"] >= 60: top.append(i); cap[i["source"]] = cap.get(i["source"], 0) + 1
        if len(top) == 10: break
    if SEO2: top.sort(key=lambda x: (-x["score"], x["id"]))  # deterministic ties: score desc, then type+ID
    frontier = [i for i in out if i["source"] == "huggingface" and i["kind"] == "model"
                and i["name"].split("/")[0].lower() in FRONTIER and i.get("created")
                and (now - ts(i["created"])).days <= 45][:6]
    # real history for sparklines: metric per snapshot over the last 48h (never synthesized)
    want = {i["id"] for i in top + frontier} | {i["id"] for k in ("models", "tools", "news") for i in [x for x in out if x["kind"] == k][:25]}
    hist = {k: [] for k in want}
    for f in sorted(os.listdir(SNAP)):
        s = json.load(open(os.path.join(SNAP, f)))
        if (now - ts(s["taken"])).total_seconds() > 48 * 3600: continue
        for x in s["items"]:
            c = canon(x["id"], AL)
            if c in hist: hist[c].append(x["metric"] or 0)
    for i in out:
        if i["id"] in hist: i["hist"] = hist[i["id"]]
        b = (i["name"] + " " + (i.get("desc") or "") + " " + " ".join(i.get("extra", {}).get("topics", []) or [])).lower()
        if SEO2:  # whole-word model terms in the item's own description/pipeline tag; never from name substrings or topics
            mb = (i.get("desc") or "")
            i["tag"] = ("safety" if re.search(r"\b(safety|alignment|jailbreak|security|guardrails?|red.?team)\b", b) else
                        "agents" if re.search(r"\b(agents?|agentic|mcp|browser.?use|autonomous|skills?)\b", b) else
                        "models" if i["kind"] == "model" or MODEL_WORDS.search(mb) else "dev tools")
        else: i["tag"] = ("safety" if re.search(r"safety|alignment|jailbreak|security|hack|guardrail|red.?team|risk", b) else
                    "agents" if re.search(r"agent|mcp|browser.?use|autonom|skill", b) else
                    "models" if i["kind"] == "model" or re.search(r"\bmodel|\d+b\b|weights|llm", b) else "dev tools")
        m = i["metric"] or 0; age_d = (now - ts(i["created"])).days if i.get("created") else None
        i["momentum"] = {"github": (f"+{fmt(m)} stars" if age_d is not None and age_d <= 7 else (f"+{fmt(i['vel']*24)} stars/day" if i["true_vel"] else f"{fmt(i['vel'])} stars/day since launch")),
                         "hackernews": f"{fmt(m)} points", "huggingface": f"{fmt(m)} likes", "npm": f"{fmt(m)} dl/day",
                         "pypi": f"{fmt(m)} dl/day"}[i["source"]]
        if i["source"] == "github" and age_d is not None: i["momentum_sub"] = (f"{max(age_d,1)} days old · +{fmt(i['vel']*24)} stars/day now" if i["true_vel"] else f"{max(age_d,1)} days · {fmt(i['vel'])} stars/day since launch")
        elif i["source"] == "hackernews": i["momentum_sub"] = f"{(now - ts(i['created'])).total_seconds()/3600:.0f}h · {i['extra'].get('comments') or 0} comments"
        elif i["source"] == "huggingface":
            i["momentum_sub"] = ("Space" + (f" · {i['desc']}" if i.get("desc") and i["desc"] not in ("static",) else "")) if SEO2 and i["extra"].get("hf_type") == "space" else f"{fmt(i['extra'].get('downloads') or 0)} downloads"
        else: i["momentum_sub"] = f"{i['rel']:.2f}× 7-day avg"
    res = {"items_scanned": len(cur["items"]), "sources": sorted({x["source"] for x in cur["items"]}), "generated": now.isoformat(), "has_prev": bool(prev), "errors": cur["errors"], "top": top,
           "frontier": frontier, "models": [i for i in out if i["kind"] == "model"][:25],
           "tools": [i for i in out if i["kind"] == "tool"][:25], "news": [i for i in out if i["kind"] == "news"][:25]}
    write_scored(res)
    return res
if __name__ == "__main__":
    r = score()
    for i in r["top"][:5]: print(i["score"], i["source"], i["name"], "|", i["why"])
