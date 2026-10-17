"""Concentration / sanity checks on the quality passes and top near-misses (symbols, days, best day, atr, tier).
python research/swarm1017/arena-pm-both/check_passes.py <rows dir>. Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search as S  # noqa: E402

from mcf.research.arena.combine import trades  # noqa: E402

S.ROWS = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
E = json.load(open(HERE / "stage3.json"))
sel = [e for e in E if e["quality_pass"]]
names = sorted({c[0] for e in sel for c in e["conds"]} | {"atr_d_pct", "gap", "from_pc", "dist_pdl_atr", "prev_range_atr"})
cols = ["symbol", "date", "tod"] + [f"{p}_{sd}_{g}" for p in ("r", "c") for sd in ("long", "short") for g in S.GEOMS] + names
A = S.load_rows(cols)
out = {}
for e in sel:
    cs = [(c[0], c[1], tuple(c[2]) if isinstance(c[2], list) else c[2]) for c in e["conds"]]
    t = trades(A, cs, e["side"], e["geom"], tuple(e["window"]))
    t = t.merge(A[["symbol", "date", "tod"] + names], on=["symbol", "date", "tod"], how="left")
    d = t.groupby("date")["r"].agg(["sum", "count"]).sort_values("sum", ascending=False)
    tot = t["r"].sum()
    rec = {"key": e["key"], "side": e["side"], "geom": e["geom"], "window": e["window"], "n": len(t),
           "sessions": int(t.date.nunique()), "top_symbols": t.symbol.value_counts().head(10).to_dict(),
           "n_symbols": int(t.symbol.nunique()),
           "best_day": str(d.index[0]), "best_day_share": float(d["sum"].iloc[0] / tot),
           "top5_days_share": float(d["sum"].head(5).sum() / tot), "max_trades_one_day": int(d["count"].max()),
           "exp_wo_best_day": float(t.loc[t.date != d.index[0], "r"].mean()),
           "exp_wo_top5_days": float(t.loc[~t.date.isin(d.index[:5]), "r"].mean()),
           "exp_by_split": t.groupby("split")["r"].mean().to_dict(), "n_by_split": t.groupby("split").size().to_dict(),
           "exp_by_month": t.groupby(pd.to_datetime(t.date).dt.strftime("%Y-%m"))["r"].agg(["mean", "count"]).round(3).to_dict("index"),
           "win_rate": float((t.r > 0).mean()), "median_atr_d_pct": float(t.atr_d_pct.median()),
           "median_gap": float(t.gap.median()), "median_prev_range_atr": float(t.prev_range_atr.median()),
           "ext_tier_share": float(((t.gap.abs() >= 20)).mean()), "tod_counts": t.tod.value_counts().sort_index().to_dict()}
    out[e["key"] + " | " + e["geom"] + " " + str(e["window"])] = rec
    t.to_csv(HERE / f"trades_{len(out)}.csv", index=False, float_format="%.5g")
(HERE / "check_passes.json").write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str))
