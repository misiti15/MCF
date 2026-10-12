"""ONE-TIME lead scoring of the package C candidates on the rule-19 locked block (trades ENTERED 2024-11-01..
2025-02-28), same code, rules and costs as families.py. NOT run by the worker. Educational only - not financial advice.

    python research/bdi/cwt/test_c/score_locked.py            # lead only, once per version -> locked.json
    python research/bdi/cwt/test_c/score_locked.py --dry-run  # code-path check, locked block still blanked (0 trades)

Bars (rule 18/19 rising bar per lineage): the two C1 limit-entry dip buys belong to the Connors dip-buy lineage
(sw-w3-connors-rsi3-daily look 1 FAILED, sat1010-rw-connors-vixp30 look 2 FAILED) -> this is look 3: exp > 0 and
day-clustered t >= 2.0. C7_streak3_upclose is a new lineage -> look 1: exp > 0 and t >= 1.0.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
DRY = "--dry-run" in sys.argv

if not DRY:   # load common.py with the blanking switched off (lead only)
    src = (HERE / "common.py").read_text()
    old = 'LOCK_A, LOCK_B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")'
    assert old in src
    src = src.replace(old, 'LOCK_A, LOCK_B = pd.Timestamp("1900-01-01"), pd.Timestamp("1900-01-02")  # lead: no blanking')
    spec = importlib.util.spec_from_loader("common", loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(HERE / "common.py")
    sys.modules["common"] = mod
    exec(compile(src, str(HERE / "common.py"), "exec"), mod.__dict__)
import common as cm  # noqa: E402
import families as fa  # noqa: E402

A, B = pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28")
BARS = {"C1_L_rsi2_5_none_L5_sma5": (3, 2.0), "C1_L_rsi3_15_none_L3_sma5": (3, 2.0), "C7_streak3_upclose": (1, 1.0)}
RUN = {"C1_L_rsi2_5_none_L5_sma5": lambda: fa.c1_long("rsi2_5", "none", 0.05, "sma5"),
       # lead 2026-10-12: one per lineage -> C1_L_rsi3_15_none_L3_sma5 NOT scored (kept unseen)
       "C7_streak3_upclose": lambda: fa.c7_streak(3, "upclose")}


def tday(r, keys):
    mu = r.mean()
    d = pd.Series(r).groupby(keys).agg(["sum", "size"])
    se = math.sqrt(((d["sum"] - d["size"] * mu) ** 2).sum()) / len(r)
    return mu / se if se > 0 else float("nan")


out = {"_dry_run": DRY}
for cid, fn in RUN.items():
    t = fn()
    ed = cm.dates[t.ei.to_numpy()] if len(t) else pd.DatetimeIndex([])
    t = t[(ed >= A) & (ed <= B)].copy() if len(t) else t
    look, bar = BARS[cid]
    if not len(t):
        out[cid] = {"n": 0, "look": look, "bar_t": bar, "verdict": "no trades"}
        print(cid, out[cid]); continue
    r = t.net.to_numpy()
    hold = max(1, int(np.median(t.hold)))
    res = {"n": int(len(r)), "net_bps": round(r.mean() * 1e4, 1), "win": round(float((r > 0).mean()), 3),
           "t_day_clustered": round(tday(r, t.date.to_numpy()), 2),
           "t_block": round(tday(r, t.i.to_numpy() // max(1, 2 * hold)), 2), "entry_sessions": int(t.i.nunique()),
           "look": look, "bar_t": bar}
    if cid.startswith("C1"):
        res["excess_bps"] = round(float(np.nanmean(t.gross - cm.bench(t))) * 1e4, 1)
    res["verdict"] = "PASS" if (res["net_bps"] > 0 and res["t_day_clustered"] >= bar) else "FAIL"
    out[cid] = res
    print(cid, res, flush=True)
if not DRY:
    spy = cm.C["SPY"]
    out["_context"] = {"SPY_return_block_pct": round(float(spy[(spy.index >= A) & (spy.index <= B)].iloc[-1]
                                                           / spy[spy.index >= A].iloc[0] - 1) * 100, 2)}
if not DRY:
    json.dump(out, open(HERE / "locked.json", "w"), indent=1)
else:
    print("dry run: nothing written", out)
