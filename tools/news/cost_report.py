#!/usr/bin/env python3
"""Monthly totals from the auto-post cost log (one JSON row per real run, written by fetch.py / publish.py).

Usage: cost_report.py [--month YYYY-MM] [--json] [--file PATH]
  default file: $NAB_AUTOPOST_COST or /workspace/shared/nab-relaunch/autopost-cost.jsonl
  A missing or empty file (or no rows for --month) prints nothing and exits 0.
Counts: runs, quiet, posted, held, failed (by stage), X API calls by endpoint, AI writing runs, gate-fix retries,
embed (syndication) fetches, agent X reads, average wall seconds. Prices are NOT applied here: X's per-call pricing
is not verified, so the report gives counts only."""
import argparse, json, os, sys
from collections import Counter, OrderedDict

DEFAULT = os.getenv("NAB_AUTOPOST_COST", "/workspace/shared/nab-relaunch/autopost-cost.jsonl")
KEYS = ("users_me", "timeline_read", "media_upload", "media_metadata", "post", "reply")

def rows(path):
    try: lines = open(path, encoding="utf-8").read().splitlines()
    except OSError: return []
    out = []
    for ln in lines:
        try:
            r = json.loads(ln)
            if isinstance(r, dict) and r.get("date"): out.append(r)
        except ValueError: pass
    return out

def summarise(rs):
    months = OrderedDict()
    for r in sorted(rs, key=lambda r: (r.get("date", ""), r.get("run_at", ""))):
        m = months.setdefault(r["date"][:7], {"runs": 0, "quiet": 0, "posted": 0, "held": 0, "failed": 0, "failed_by_stage": Counter(),
                                               "x_api_calls": Counter(), "ai_writing_runs": 0, "gate_fix_retries": 0,
                                               "syndication_fetches": 0, "x_reads_agent": 0, "_wall": []})
        o = str(r.get("outcome", ""))
        m["runs"] += 1
        if o == "quiet": m["quiet"] += 1
        elif o == "posted" and r.get("posted"): m["posted"] += 1
        elif o == "held": m["held"] += 1
        elif o.startswith("failed"): m["failed"] += 1; m["failed_by_stage"][o.split(":", 1)[-1]] += 1
        for k in KEYS: m["x_api_calls"][k] += int((r.get("x_api_calls") or {}).get(k) or 0)
        m["ai_writing_runs"] += bool(r.get("ai_writing_step"))
        m["gate_fix_retries"] += 1 if o == "failed:gate" else 0
        m["syndication_fetches"] += int(r.get("syndication_fetches") or 0)
        m["x_reads_agent"] += int(r.get("x_reads_agent") or 0)
        if isinstance(r.get("wall_seconds"), (int, float)): m["_wall"].append(r["wall_seconds"])
    for m in months.values():
        w = m.pop("_wall"); m["avg_wall_seconds"] = round(sum(w) / len(w), 1) if w else None
        m["x_api_calls"] = {k: m["x_api_calls"][k] for k in KEYS}; m["x_api_calls"]["total"] = sum(m["x_api_calls"].values())
        m["failed_by_stage"] = dict(m["failed_by_stage"])
    return months

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--month"); ap.add_argument("--json", action="store_true"); ap.add_argument("--file", default=DEFAULT)
    a = ap.parse_args()
    months = summarise(rows(a.file))
    if a.month: months = OrderedDict((k, v) for k, v in months.items() if k == a.month)
    if not months: return 0
    if a.json: print(json.dumps(months, indent=2)); return 0
    for k, m in months.items():
        x = m["x_api_calls"]
        fails = ", ".join(f"{s} {n}" for s, n in sorted(m["failed_by_stage"].items())) or "none"
        print(f"{k}: {m['runs']} runs | quiet {m['quiet']} | posted {m['posted']} | held {m['held']} | failed {m['failed']} ({fails})")
        print(f"  X API calls {x['total']}: users/me {x['users_me']}, timeline read {x['timeline_read']}, media upload {x['media_upload']}, "
              f"alt text {x['media_metadata']}, post {x['post']}, reply {x['reply']}")
        print(f"  AI writing runs {m['ai_writing_runs']} | gate-fix retries {m['gate_fix_retries']} | agent X reads {m['x_reads_agent']} | "
              f"embed fetches {m['syndication_fetches']} | avg wall {m['avg_wall_seconds']}s")
    return 0

if __name__ == "__main__": sys.exit(main())
