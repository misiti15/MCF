"""Rule-19 locked block (2024-11-01..2025-02-28): ONE scoring of the longhold finalist, authorised by the lead
(2026-10-10). Look 1 bar: active return vs the equal-weight universe over the block > 0.

Reuses study.py's data, features, target builders and simulator exactly (its source up to the grid section is
executed with the single line that zeroes locked-block returns removed), so the frozen rule and the portfolio
state carried in from October 2024 are those of the backtest. Statistics cover block days only.
Refuses to run unless MCF_HIST_ALLOW_LOCKED=1 and refuses to overwrite an existing locked.json (scored once).
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "locked.json"
if os.environ.get("MCF_HIST_ALLOW_LOCKED") != "1":
    sys.exit("locked block: set MCF_HIST_ALLOW_LOCKED=1 (lead only)")
if OUT.exists():
    sys.exit("locked.json exists: the block has already been scored once")

src = (HERE / "study.py").read_text()
src = src[: src.index("# ---------------------------------------------------------------------------------------------- grid")]
ZERO = "    R[locked] = 0.0"
assert src.count(ZERO) == 1
src = src.replace(ZERO, "    pass")
ns: dict = {"__file__": str(HERE / "study.py"), "__name__": "study_locked"}
exec(compile(src, "study.py(locked)", "exec"), ns)

dates = ns["dates"]
blk = np.asarray((dates >= ns["LOCK_A"]) & (dates <= ns["LOCK_B"]))
sim, T = ns["simulate"], ns["T"]

SER = {
    "S6_mom12_1rev_N20_W": sim(ns["stock_targets"]("mom12_1", 20, "W", filt_rev=True)),
    "E1_faber10_Erisk": sim(ns["etf_targets"]("faber", ns["E_RISK"], 10)),
    "BENCH_EW": sim(ns["ew_universe_targets"]()),
    "ERISK": sim(ns["bh_targets"](ns["E_RISK"])),
    "BH_SPY": sim(ns["bh_targets"](["SPY"])),
}
BENCH = {"S6_mom12_1rev_N20_W": "BENCH_EW", "E1_faber10_Erisk": "ERISK"}
iso = dates.isocalendar()
wk = (iso.year.values * 100 + iso.week.values)[blk]


def comp(x, key):
    return pd.Series(x).groupby(key).apply(lambda v: (1 + v).prod() - 1)


def stats(cid):
    r, to, c = (a[blk] for a in SER[cid])
    n = len(r)
    eq = np.cumprod(1 + r)
    tot = float(eq[-1] - 1)
    out = {"days": n, "total_return": tot, "cagr_equiv": float((1 + tot) ** (252 / n) - 1),
           "vol": float(r.std() * math.sqrt(252)), "sharpe": float(r.mean() / r.std() * math.sqrt(252)),
           "maxdd": float((eq / np.maximum.accumulate(eq) - 1).min()),
           "turnover_block": float(to.sum()), "turnover_yr_equiv": float(to.sum() * 252 / n),
           "cost_block": float(c.sum()), "weekly_hit": float((comp(r, wk) > 0).mean())}
    for b in ("BENCH_EW", "BH_SPY") + ((BENCH[cid],) if cid in BENCH and BENCH[cid] != "BENCH_EW" else ()):
        rb = SER[b][0][blk]
        tb = float(np.prod(1 + rb) - 1)
        aw = comp(r, wk) - comp(rb, wk)
        out[f"vs_{b}"] = {"bench_total": tb, "active_total": tot - tb,
                          "active_ann_arith": float((r.mean() - rb.mean()) * 252),
                          "weekly_hit_vs": float((aw > 0).mean()),
                          "weekly_active_t": float(aw.mean() / aw.std() * math.sqrt(len(aw)))}
    return out


res = {k: stats(k) for k in ("S6_mom12_1rev_N20_W", "E1_faber10_Erisk", "BENCH_EW", "BH_SPY", "ERISK")}
f = res["S6_mom12_1rev_N20_W"]["vs_BENCH_EW"]["active_ann_arith"]
res["_verdict"] = {"finalist": "S6_mom12_1rev_N20_W", "look": 1, "bar": "active (annualised arithmetic) vs EW universe > 0",
                   "pass": bool(f > 0), "active_vs_EW": f,
                   "control": "E1_faber10_Erisk (information only, not a candidate)",
                   "block": "2024-11-01..2025-02-28", "scored": "2026-10-10, once, authorised by the lead"}
OUT.write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
