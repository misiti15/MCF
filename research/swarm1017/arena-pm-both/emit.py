"""Write the lab modules (candidate + labelled near-misses) and check that each module's mask(df) on raw history
frames reproduces the arena trades (gates.lab_trades vs combine.trades), plus concentration detail for the candidate.
python research/swarm1017/arena-pm-both/emit.py <rows dir>. Educational only - not financial advice."""
import json
import sys
import importlib.util
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search as S  # noqa: E402

from mcf.research import gates  # noqa: E402
from mcf.research.arena import data as D  # noqa: E402
from mcf.research.arena.combine import trades, write_module  # noqa: E402

S.ROWS = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
MODS = [
    ("modules", "AR-PM-S-gapdn-reclaim-pdh-fade", "short", "t1s1", (1400, 1530),
     [("gap_atr", "<=", -0.6141), ("dist_pdh_atr", "<=", -0.453), ("rvol_day", ">=", 0.8386)],
     "Gap-down (> 0.61 daily ATR) that has rallied back to > 0.45 ATR ABOVE the prior-day high, on above-normal\n"
     "volume (rvol_day >= 0.84), shorted 14:00-15:00 for a late-day fade. Stage-4 plateau pick (VALID seen):\n"
     "train t 4.92 vs bar 4.89, n 202 - marginal; ~0.47 trades/day."),
    ("near_miss", "NM-PM-S-gapdn-above-pdh-rvol", "short", "t1s1", (1400, 1530),
     [("gap_atr", "<=", -0.6141), ("dist_pdh_atr", "<=", -0.1494), ("rvol_day", ">=", 0.8386)],
     "NEAR-MISS (not a candidate): base of the candidate family; train t 3.46 < bar 4.89."),
    ("near_miss", "NM-PM-L-belowvwap-orh-retest", "long", "t1s1", (1400, 1530),
     [("vwapDistPct", "<=", -1.3328), ("or_high_dist_atr", ">=", -0.1904), ("day_pos", "<=", 0.1957)],
     "NEAR-MISS (not a candidate): far below VWAP, near the day low, but the day low sits at/above the\n"
     "opening-range high (rally-then-full-fade); long 14:00-15:00. Train t 4.56 < bar 4.89, valid +0.046R t 0.78."),
]
names = sorted({c[0] for m in MODS for c in m[5]})
cols = ["symbol", "date", "tod"] + [f"{p}_{sd}_{g}" for p in ("r", "c") for sd in ("long", "short") for g in S.GEOMS] + names
A = S.load_rows(cols)
lib = D._lib()
CHECK_MONTHS = ["2025-04", "2026-03"]
frames = {m: lib.load_month(m) for m in CHECK_MONTHS}
rep = {}
for folder, nm, side, geom, w, cs, doc in MODS:
    p = write_module(cs, side, geom, w, HERE / folder / f"{nm}.py", nm, doc=doc)
    spec = importlib.util.spec_from_file_location(nm.replace("-", "_"), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    t = trades(A, cs, side, geom, w)
    chk = {}
    for m, df in frames.items():
        a = t[pd.to_datetime(t.date).dt.strftime("%Y-%m") == m]
        min_adv = df["adv20"].to_numpy(float) >= 95e6
        b = gates.lab_trades(df, mod.mask(df) & min_adv, side, geom)
        chk[m] = {"arena_n": len(a), "module_n": len(b), "arena_exp": round(float(a.r.mean()), 4) if len(a) else None,
                  "module_exp": round(float(b.r.mean()), 4) if len(b) else None,
                  "same_trades": sorted(zip(a.symbol.astype(str), map(str, a.date))) == sorted(zip(b.symbol.astype(str), map(str, b.date)))}
    mo = t.groupby(pd.to_datetime(t.date).dt.strftime("%Y-%m"))["r"].agg(["mean", "count"]).round(3)
    d = t.groupby("date")["r"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    rep[nm] = {"module": str(p.relative_to(HERE.parents[2])), "roundtrip": chk, "n": len(t),
               "n_symbols": int(t.symbol.nunique()), "top_symbols": t.symbol.astype(str).value_counts().head(8).to_dict(),
               "top5_days": {str(k): [round(v["sum"], 2), int(v["count"])] for k, v in d.head(5).iterrows()},
               "top5_days_share": round(float(d["sum"].head(5).sum() / t.r.sum()), 3),
               "months_positive_share": round(float((mo["mean"] > 0).mean()), 3),
               "months": {k: [v["mean"], int(v["count"])] for k, v in mo.iterrows()},
               "train_excess": round(float(t[t.split == "train"].x.mean()), 4),
               "valid_excess": round(float(t[t.split == "valid"].x.mean()), 4),
               "valid_summary": gates.summary(t[t.split == "valid"][["date", "r"]]),
               "train_summary": gates.summary(t[t.split == "train"][["date", "r"]])}
(HERE / "emit.json").write_text(json.dumps(rep, indent=1, default=str))
print(json.dumps(rep, indent=1, default=str))
