"""SKEPTIC_1127 scoring of skeptic_control.py output (K_lots.parquet). Educational only - not financial advice.
Usage: python skeptic_score.py WORKDIR   -> prints tables, writes K_results.csv / K_controls.csv / K_days.csv here."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W, OUT = Path(sys.argv[1]), Path(__file__).parent
L = pd.read_parquet(W / "K_lots.parquet")
L["r"] = L.r.fillna(0.0)
assert not ((L.date >= "2024-11-01") & (L.date <= "2025-02-28")).any()
NS = {"FIT": 170, "T2": 427, "CHECK": 276}           # sessions (score.py SPY calendar)
NS["T2+CHECK"] = NS["T2"] + NS["CHECK"]
NS["ALL"] = sum(NS[p] for p in ("FIT", "T2", "CHECK"))
day = L.groupby(["cfg", "per", "date"]).r.sum().unstack("cfg").fillna(0.0)
# exposure actually removed, in R-at-risk units: half stop -> 0.5 per tight lot, size s -> 1 - s per lot
lots = L[L.i >= 0].copy()
lots["cut"] = np.where(lots.tight & (lots["size"] >= 0.999), 0.5, 1.0 - lots["size"])
cut = lots.groupby(["cfg", "per"]).cut.sum().unstack("per")


def sel(per):
    if per == "ALL":
        return day
    if per == "T2+CHECK":
        return day[day.index.get_level_values("per").isin(["T2", "CHECK"])]
    return day.xs(per, level="per", drop_level=False)


def stats(c, per):
    d = sel(per)
    b, x = d["base"], d[c]
    dd = x - b
    pos = dd[dd > 0]
    return dict(cfg=c, per=per, R=x.sum(), dR=dd.sum(), dR_yr=dd.sum() / NS[per] * 252, worst=x.min(),
                worst_cut=x.min() - b.min(), w5_cut=x.nsmallest(5).sum() - b.nsmallest(5).sum(),
                dR_wo_best=dd.sum() - (dd.max() if len(dd) else 0), best_dday_share=(dd.max() / pos.sum()) if len(pos) else np.nan,
                R_wo_best=x.sum() - x.max(), best_share=x.max() / x[x > 0].sum(),
                exp_cut=sum(cut.loc[c].get(p, 0.0) for p in (("FIT", "T2", "CHECK") if per == "ALL" else
                                                              ("T2", "CHECK") if per == "T2+CHECK" else (per,))))


PERS = ("FIT", "T2", "CHECK", "T2+CHECK", "ALL")
named = ["AV50", "Q50", "CONST", "AVSIZE"]
R = pd.DataFrame([stats(c, p) for c in named for p in PERS])
b = sel("ALL")["base"]
print("base R", {p: round(sel(p)["base"].sum(), 2) for p in PERS})
pd.set_option("display.width", 250)
print(R.round(3).to_string(index=False))
R.round(4).to_csv(OUT / "K_results.csv", index=False)

fams = {"RTB": "half stop, random burst lots (tests the SPY<VWAP filter)",
        "RTA": "half stop, random lots of any kind (tests burst+VWAP targeting)",
        "RHA": "half size, random lots of any kind (size-matched random cut)"}
rows = []
for f, desc in fams.items():
    cs = sorted(c for c in day.columns if c.startswith(f))
    for p in PERS:
        S = pd.DataFrame([stats(c, p) for c in cs])
        a = R[(R.cfg == "AV50") & (R.per == p)].iloc[0]
        rows.append(dict(fam=f, per=p, n=len(cs), exp_cut_med=S.exp_cut.median(), exp_cut_AV50=a.exp_cut,
                         dR_med=S.dR.median(), dR_p5=S.dR.quantile(.05), dR_p95=S.dR.quantile(.95), dR_AV50=a.dR,
                         pct_dR=(S.dR < a.dR).mean() * 100,
                         worst_cut_med=S.worst_cut.median(), worst_cut_p95=S.worst_cut.quantile(.95), worst_cut_AV50=a.worst_cut,
                         pct_worst=(S.worst_cut < a.worst_cut).mean() * 100,
                         w5_med=S.w5_cut.median(), w5_p95=S.w5_cut.quantile(.95), w5_AV50=a.w5_cut,
                         pct_w5=(S.w5_cut < a.w5_cut).mean() * 100))
C = pd.DataFrame(rows)
print(C.round(2).to_string(index=False))
C.round(3).to_csv(OUT / "K_controls.csv", index=False)

# AV50 dR by day (one-big-day check on the benefit) + which days drive it
dd = (day["AV50"] - day["base"])
dd = dd[dd.abs() > 1e-9].sort_values()
K = pd.DataFrame({"dR_AV50": dd, "base": day["base"].reindex(dd.index), "Q50_dR": (day["Q50"] - day["base"]).reindex(dd.index)})
K.round(3).to_csv(OUT / "K_days.csv")
print("AV50 changed days:", len(K)); print(K.round(2).to_string())
