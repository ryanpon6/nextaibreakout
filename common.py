import json, os, time, urllib.request, urllib.error
UA = "BreakoutAI/0.1 (+https://nextaibreakout.com)"
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data"); SNAP = os.path.join(DATA, "snapshots"); DIST = os.path.join(ROOT, "dist")
def get_json(url, headers=None, retries=2):
    h = {"User-Agent": UA, "Accept": "application/json"}; h.update(headers or {})
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=25) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and i < retries: time.sleep(10 * (i + 1)); continue
            raise
        except Exception:
            if i < retries: time.sleep(3); continue
            raise
# ---- GitHub renames: data/gh_aliases.json maps an old ID to the canonical one, e.g. {"gh:old/name": "gh:new/name"}.
# Written by fetch.py from the API's canonical full_name; read by score/archive/seo2 so history follows the repo.
ALIASES = os.path.join(DATA, "gh_aliases.json")
def aliases():
    try: return json.load(open(ALIASES))
    except Exception: return {}
def canon(iid, _a=None):
    a = aliases() if _a is None else _a; seen = set()
    while iid in a and iid not in seen: seen.add(iid); iid = a[iid]
    return iid
def add_alias(old, new):
    if not old or not new or old.lower() == new.lower(): return False
    a = aliases()
    if a.get(old) == new: return False
    a[old] = new; a.pop(new, None)  # never point a canonical name back at an old one
    tmp = ALIASES + ".tmp"; json.dump(a, open(tmp, "w"), indent=1, sort_keys=True); os.replace(tmp, ALIASES)
    print(f"[rename] {old} -> {new}"); return True
