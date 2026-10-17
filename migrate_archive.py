"""One-off (2026-10-16): move archive records to type+ID slugs and restore history dropped by the
model/Space merge. Restored ranks, scores (rounded to whole numbers as displayed) and like counts come from
the deployed production pages for those runs (9f6075ac = 21:08 UTC, b337bef9 = 03:05, c5bcbd4c = 03:07)."""
import json, os, glob
import archive as A
from common import DATA, SNAP
snap = json.load(open(sorted(glob.glob(os.path.join(SNAP, "*.json")))[-1]))["items"]; S = {x["id"]: x for x in snap}
T = {"a": "2026-10-15T21:08:25.792112+00:00", "b": "2026-10-16T03:05:22.658292+00:00", "c": "2026-10-16T03:07:01.766756+00:00"}
RESTORE = {"hfmodel:black-forest-labs/flux-3-image-klein": [("a", 4, 96, 173), ("b", 2, 98, 256), ("c", 2, 98, 257)],
           "hfspace:black-forest-labs/flux-3-image-klein": [("b", 6, 92, 45), ("c", 6, 92, 45)]}
# 1. re-key: any record whose stored slug differs from the type+ID slug
for p in glob.glob(os.path.join(A.ITM, "*.json")):
    I = json.load(open(p)); new = A.slug(I)
    if new != I["slug"]:
        old = I["slug"]; I["slug"] = new; json.dump(I, open(os.path.join(A.ITM, new + ".json"), "w"), indent=1); os.remove(p)
        for dp in glob.glob(os.path.join(A.DAY, "*.json")):
            D = json.load(open(dp))
            if old in D["items"]: e = D["items"].pop(old); e["slug"] = new; D["items"][new] = e; json.dump(D, open(dp, "w"), indent=1)
        print("rekeyed", old, "->", new)
# 2. restore dropped history
for iid, apps in RESTORE.items():
    x = S[iid]; s = A.slug(x); ip = os.path.join(A.ITM, s + ".json")
    if os.path.exists(ip): print("exists", s); continue
    I = dict(id=iid, slug=s, first_seen=T[apps[0][0]], appearances=[dict(rank=r, score=float(sc), metric=m, t=T[k]) for k, r, sc, m in apps],
             peak_score=float(max(a[2] for a in apps)), best_rank=min(a[1] for a in apps), name=x["name"], url=x["url"], source=x["source"], kind=x["kind"],
             desc=x.get("desc") or "", what="", tag="models" if x["kind"] == "model" else "tools", metric_name=x["metric_name"], created=x.get("created"),
             last_seen=T[apps[-1][0]], last_why="", extra=x.get("extra") or {}, days=sorted({T[a[0]][:10] for a in apps}))
    json.dump(I, open(ip, "w"), indent=1)
    for day in I["days"]:
        dp = os.path.join(A.DAY, day + ".json"); D = json.load(open(dp)); mine = [a for a in apps if T[a[0]][:10] == day]
        D["items"][s] = dict(id=iid, slug=s, name=x["name"], url=x["url"], source=x["source"], kind=x["kind"], first_seen=T[mine[0][0]], last_seen=T[mine[-1][0]],
                             peak_score=float(max(a[2] for a in mine)), best_rank=min(a[1] for a in mine), runs_in_top10=min(len(mine), len(D["runs"])),
                             what="", tag=I["tag"], extra=I["extra"], metric_name=x["metric_name"], metric_at_peak=max(mine, key=lambda a: a[2])[3], why_at_peak="")
        json.dump(D, open(dp, "w"), indent=1)
    print("restored", s, len(apps), "appearances")
