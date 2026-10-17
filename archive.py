"""Record real top-10 appearances for daily archive + per-item pages (data only; never touches dist/).
Runs every hour from run.sh. Writes data/archive/daily/YYYY-MM-DD.json (UTC day) and data/archive/items/<slug>.json.
No backfill: only runs that actually happened are recorded."""
import datetime as dt, json, os, re
from common import DATA, aliases, canon
ARC = os.path.join(DATA, "archive"); DAY = os.path.join(ARC, "daily"); ITM = os.path.join(ARC, "items")
def slug(i):
    pre = {"github": "gh", "huggingface": "hf", "hackernews": "hn", "npm": "npm", "pypi": "pypi"}[i["source"]]
    if i["id"].startswith("hfspace:"): pre = "hf-space"  # a Space and a model can share an ID; keep them separate
    base = i["id"].split(":", 1)[1] if i["source"] != "hackernews" else i["id"].split(":", 1)[1] + "-" + i["name"][:50]
    return (pre + "-" + re.sub(r"[^a-z0-9]+", "-", base.lower())).strip("-")[:90]
def merge_aliases():
    """Dedupe renamed repos: fold the archive record (item file + daily entries) of every old ID in
    data/gh_aliases.json into its canonical ID, so one repo keeps one history and one item page. Idempotent."""
    import glob
    AL = aliases()
    for old in sorted(AL):
        new = canon(old, AL)
        if new == old or not old.startswith("gh:"): continue
        so, sn = slug(dict(source="github", id=old, name=old)), slug(dict(source="github", id=new, name=new))
        po, pn = os.path.join(ITM, so + ".json"), os.path.join(ITM, sn + ".json")
        if os.path.exists(po):
            O = json.load(open(po)); N = json.load(open(pn)) if os.path.exists(pn) else dict(O, id=new, slug=sn, appearances=[])
            have = {a["t"] for a in N["appearances"]}
            N["appearances"] = sorted(N["appearances"] + [a for a in O["appearances"] if a["t"] not in have], key=lambda a: a["t"])
            N["first_seen"] = min(O["first_seen"], N["first_seen"]); N["peak_score"] = max(O["peak_score"], N["peak_score"])
            N["best_rank"] = min(O["best_rank"], N["best_rank"]); N["days"] = sorted(set(O.get("days", [])) | set(N.get("days", [])))
            N.update(id=new, slug=sn, name=new[3:], url="https://github.com/" + new[3:]); N.setdefault("aliases", [])
            if old not in N["aliases"]: N["aliases"].append(old)
            json.dump(N, open(pn, "w"), indent=1); os.remove(po); print(f"[archive] merged item {so} -> {sn}")
        for dp in glob.glob(os.path.join(DAY, "*.json")):
            D = json.load(open(dp))
            if so not in D["items"]: continue
            o = D["items"].pop(so); n = D["items"].get(sn)
            if n is None: n = dict(o)
            else:
                n["runs_in_top10"] = min(n["runs_in_top10"] + o["runs_in_top10"], len(D["runs"]))
                n["first_seen"] = min(o["first_seen"], n["first_seen"]); n["last_seen"] = max(o["last_seen"], n["last_seen"])
                n["best_rank"] = min(o["best_rank"], n["best_rank"])
                if o["peak_score"] > n["peak_score"]:
                    n.update({k: o[k] for k in ("peak_score", "why_at_peak", "metric_at_peak", "metric_name") if k in o})
            n.update(id=new, slug=sn, name=new[3:], url="https://github.com/" + new[3:])
            D["items"][sn] = n; json.dump(D, open(dp, "w"), indent=1); print(f"[archive] merged {os.path.basename(dp)} entry {so} -> {sn}")
def run():
    merge_aliases()
    d = json.load(open(os.path.join(DATA, "scored-seo2.json" if os.getenv("SEO2") == "1" else "scored.json"))); t = d["generated"]; day = t[:10]
    os.makedirs(DAY, exist_ok=True); os.makedirs(ITM, exist_ok=True)
    dp = os.path.join(DAY, day + ".json"); D = json.load(open(dp)) if os.path.exists(dp) else {"day": day, "runs": [], "items": {}}
    if t in D["runs"]: print("[archive] run already recorded", t); return
    D["runs"].append(t)
    for r, i in enumerate(d["top"], 1):
        s = slug(i); rec = dict(rank=r, score=i["score"], metric=i["metric"], t=t)
        e = D["items"].setdefault(s, dict(id=i["id"], slug=s, name=i["name"], url=i["url"], source=i["source"], kind=i["kind"],
                                          first_seen=t, peak_score=0, best_rank=99, runs_in_top10=0))
        e.update(last_seen=t, runs_in_top10=min(e["runs_in_top10"] + 1, len(D["runs"])), what=i.get("what") or "", tag=i.get("tag"), extra=i.get("extra") or {})
        if i["score"] >= e["peak_score"]: e.update(peak_score=i["score"], why_at_peak=i["why"], metric_at_peak=i["metric"], metric_name=i["metric_name"])
        e["best_rank"] = min(e["best_rank"], r)
        ip = os.path.join(ITM, s + ".json"); I = json.load(open(ip)) if os.path.exists(ip) else dict(id=i["id"], slug=s, first_seen=t, appearances=[], peak_score=0, best_rank=99)
        I.update(name=i["name"], url=i["url"], source=i["source"], kind=i["kind"], desc=i.get("desc") or "", what=i.get("what") or "",
                 tag=i.get("tag"), metric_name=i["metric_name"], created=i.get("created"), last_seen=t, last_why=i["why"], extra=i.get("extra") or {})
        I["appearances"].append(rec); I["peak_score"] = max(I["peak_score"], i["score"]); I["best_rank"] = min(I["best_rank"], r)
        I["days"] = sorted(set(I.get("days", [])) | {day})
        json.dump(I, open(ip, "w"), indent=1)
    json.dump(D, open(dp, "w"), indent=1)
    print(f"[archive] {day}: {len(d['top'])} top items recorded ({len(D['runs'])} runs today)")
if __name__ == "__main__":
    import sys
    merge_aliases() if sys.argv[1:] == ["--merge-only"] else run()
