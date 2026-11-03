"""Replay vs live (research rule 21 bar) for each input configuration of run.py, post-fix sessions only.
Reuses research/bdi/replay_audit1029/compare.py (same matching: setup + symbol + decision minute, greedy one-to-one;
same cost layer, applied identically to live and replay). "In universe" = the replay's symbol set (lab, or the full
live universe for the F* configurations).
    MCF_REPLAY_STORE=<store> python compare.py <run dir> <conf,...> [--full-universe <dir of universe/*.txt>]
Educational only - not financial advice."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sp = importlib.util.spec_from_file_location("c1029", ROOT / "research/bdi/replay_audit1029/compare.py")
C = importlib.util.module_from_spec(sp)
sp.loader.exec_module(C)

ap = argparse.ArgumentParser()
ap.add_argument("run")
ap.add_argument("confs")
ap.add_argument("--full-universe")
ap.add_argument("--out", default=str(HERE / "results.json"))
ap.add_argument("--days", help="comma list: only these sessions (key suffix _2d)")
ap.add_argument("--key", help="results key (default: the conf)")
a = ap.parse_args()
costs = yaml.safe_load((ROOT / "config/default.yaml").read_text())["costs"]
lab = C.store.symbols
res = json.loads(Path(a.out).read_text()) if Path(a.out).exists() else {"_note": "Educational only - not financial advice."}
for conf in a.confs.split(","):
    run = Path(a.run) / conf
    if a.full_universe and conf.startswith("F"):
        u = sorted(set().union(*[set(p.read_text().split()) for p in Path(a.full_universe).glob("*.txt")]))
        C.store.symbols = lambda u=u: u
    else:
        C.store.symbols = lab
    parts, frames, out = [], [], {}
    for ac in C.ACCTS:
        if not (run / ac).exists():
            continue
        ls, lt, rs, rt, st = C.load(ac, run)
        days = sorted(d for d in st if "error" not in st[d] and (not a.days or d in a.days.split(",")))
        r = C.window(ac, ls, lt, rs, rt, st, days, costs)
        r.pop("per_setup", None)
        r["by_day"] = {}
        for d in days:
            x = C.window(ac, ls, lt, rs, rt, st, [d], costs)
            r["by_day"][d] = {k: x.get(k) for k in ("live_trades", "replay_trades", "matched_exact", "match_pct",
                                                     "live_avg_r_costs", "replay_avg_r_costs", "gap_costs")}
        out[ac] = r
        parts.append(r)
        x, y = lt[lt.day.isin(days)], rt[rt.day.isin(days)]
        frames.append((x.r_multiple.astype(float) - C.cost_r(x, costs) if len(x) else pd.Series(dtype=float),
                       y.r_multiple.astype(float) - C.cost_r(y, costs) if len(y) else pd.Series(dtype=float)))
    res[(a.key or "{}").format(conf)] = {"accounts": out, "overall": C.pooled(parts, frames)}
    print(f"===== {conf}")
    for ac, x in out.items():
        print(f"{C.NAMES[ac]:10s} s={x['sessions']} live={x['live_trades']:5d} (in univ {x['live_trades_in_lab_universe']}) "
              f"rep={x['replay_trades']:5d} match={x['match_pct']}% (in-univ {x['match_pct_in_universe']}%) "
              f"extra={x['replay_only']} liveR={x['live_avg_r_costs']} repR={x['replay_avg_r_costs']} gap={x.get('gap_costs')} "
              f"matchedRdiff={x.get('matched_r_diff_mean')}")
        print("      live-only:", dict(list(x["live_only_causes"].items())[:7]))
        print("      replay-only:", dict(list(x["replay_only_causes"].items())[:6]))
    print("overall", res[(a.key or "{}").format(conf)]["overall"])
Path(a.out).write_text(json.dumps(res, indent=1, default=str))
print("Educational only - not financial advice.")
