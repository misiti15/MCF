"""eu1103/preopen: can pre-open features rank the day's big movers (Move Hunt: 33-36 of the top 50 start 09:35-09:45)?
Per lab symbol-day (adv20 >= $95M): rest-of-day range RDR = (max high - min low over bar closes 09:40..15:55) / atr_d.
Top 50 RDR names per day = the day's big movers. For each pre-open ranking (one feature, fixed direction), the share of
the top 50 that sit in the ranking's top 150 (of ~700-900 names), vs 150/N at random. Descriptive, TRAIN and VALID.
    python movers.py <scratch>  -> research/bdi/eu1103/preopen/movers.csv
Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1])
F = pd.read_parquet(S / "feat_hist.parquet")
TRAIN = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)]
VALID = ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
R = []
for mo in TRAIN + VALID:
    f = lib.load_month(mo, columns=["symbol", "date", "tod", "high", "low", "atr_d", "adv20"])
    f = f[(f.tod >= 940)]
    g = f.groupby(["symbol", "date"], observed=True).agg(hi=("high", "max"), lo=("low", "min"), atr=("atr_d", "last"), adv=("adv20", "last")).reset_index()
    g = g[(g.adv >= 95e6) & (g.atr > 0)]
    g["rdr"] = (g.hi - g.lo) / g.atr
    g["split"] = "TRAIN" if mo in TRAIN else "VALID"
    R.append(g[["symbol", "date", "rdr", "split"]])
R = pd.concat(R, ignore_index=True)
R["symbol"] = R.symbol.astype(str); R["date"] = R.date.astype(str)
R = R[(R.split == "TRAIN") | (R.date <= "2026-09-15")]
X = R.merge(F, on=["symbol", "date"], how="left")
X["abs_o5"] = X.o5_ret_atrs.abs()
X["pm_rvol_x_gap"] = X.pm_rvol.rank(pct=True) + X.pm_gap_atr.rank(pct=True)
X["top50"] = X.groupby("date").rdr.rank(ascending=False, method="first") <= 50
rows = []
for fe in ["pm_rvol", "pm_share", "pm_gap_atr", "pm_range_atr", "news_n", "o5_rvol", "abs_o5", "pm_rvol_x_gap"]:
    for sp in ("TRAIN", "VALID"):
        x = X[(X.split == sp)].copy()
        x["rk"] = x.groupby("date")[fe].rank(ascending=False, method="first")
        n = x.groupby("date").size()
        hit = x[x.top50 & (x.rk <= 150)].groupby("date").size().reindex(n.index, fill_value=0)
        base = (150 / n).mean()
        rows.append({"feature": fe, "split": sp, "days": len(n), "names_per_day": n.mean(), "top50_in_top150": (hit / 50).mean(),
                     "random": base, "lift_x": (hit / 50).mean() / base, "coverage": x[fe].notna().mean()})
pd.DataFrame(rows).to_csv("/home/user/MCF/research/bdi/eu1103/preopen/movers.csv", index=False, float_format="%.3f")
print(pd.DataFrame(rows).to_string())
