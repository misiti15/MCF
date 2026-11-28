"""Does any ranking metric predict next-week results? Rolling folds: metric on all live data before week w (>= 20 trades)
vs that setup's avg R / total R in week w (>= 5 trades). Pooled and within side. Also a family-clustered view.
Read-only. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
from scipy import stats

SCR = sys.argv[1]
t = pd.read_parquet(f"{SCR}/live.parquet")
t["side"] = np.where(t.side > 0, "L", "S")
t["wk"] = pd.to_datetime(t.date).dt.to_period("W-FRI").astype(str)

def met(g):
    d = g.groupby("date")["r"].sum()
    n = len(g); ns = len(d); se = d.std(ddof=1) / np.sqrt(ns) if ns > 1 else np.nan
    best = d.idxmax(); wo = g[g.date != best].r
    srt = d.sort_values(ascending=False).index[:2]; wo2 = g[~g.date.isin(srt)].r
    cum = d.sort_index().cumsum(); dd = cum - np.maximum(cum.cummax(), 0)
    return pd.Series({"n": n, "side": g.side.iloc[0], "score": g.r.mean() * n / (n + 20), "R_sess": d.mean(),
                      "med_day": d.median(), "worst_day": d.min(), "green_sh": (d > 0).mean(),
                      "day_t": d.mean() / se if se and se > 0 else np.nan, "ulcer_neg": -np.sqrt((dd ** 2).mean()),
                      "wo1": wo.mean() if len(wo) else np.nan, "wo2": wo2.mean() if len(wo2) else np.nan,
                      "shrunk_wo1": wo.sum() / (len(wo) + 20)})

wks = sorted(t.wk.unique())
M = ["score", "R_sess", "med_day", "worst_day", "green_sh", "day_t", "ulcer_neg", "wo1", "wo2", "shrunk_wo1"]
rows = []
for w in wks:
    past, nxt = t[t.wk < w], t[t.wk == w]
    if past.date.nunique() < 5:
        continue
    a = past.groupby("strategy").apply(met); a = a[a.n >= 20]
    b = nxt.groupby("strategy").r.agg(["count", "mean", "sum"]); b = b[b["count"] >= 5]
    j = a.join(b, how="inner")
    if len(j) < 20:
        continue
    for grp, jj in [("all", j), ("L", j[j.side == "L"]), ("S", j[j.side == "S"])]:
        if len(jj) < 10:
            continue
        rec = {"wk": w, "grp": grp, "N": len(jj)}
        for c in M:
            rec[c] = stats.spearmanr(jj[c], jj["mean"], nan_policy="omit").correlation
            k = max(len(jj) // 5, 2); top = jj.nlargest(k, c)
            rec[c + "_topR"] = top["mean"].mean() - jj["mean"].mean()   # top-quintile excess next-week avg R vs all
        rows.append(rec)
r = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print("Per-fold Spearman (metric before week -> setup avg R in week), N = setups in fold:")
print(r[["wk", "grp", "N"] + M].round(2).to_string(index=False))
print("\nMean over folds (t over folds) of Spearman rho, and top-quintile excess next-week avg R (R/trade):")
for grp in ["all", "L", "S"]:
    q = r[r.grp == grp]
    print(f"  [{grp}] folds {len(q)}")
    for c in M:
        x, y = q[c].dropna(), q[c + "_topR"].dropna()
        tt = x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else np.nan
        ty = y.mean() / (y.std(ddof=1) / np.sqrt(len(y))) if len(y) > 1 else np.nan
        print(f"    {c:11s} rho {x.mean():6.3f} (t {tt:5.2f})   top20% excess {y.mean():6.3f} R/trade (t {ty:5.2f})")
