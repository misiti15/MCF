"""Is risk more persistent than return? Rolling weekly folds: past metric (>= 20 trades) vs next-week per-setup
worst day R and total R; also lots/day. Read-only. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
from scipy import stats
SCR = sys.argv[1]
t = pd.read_parquet(f"{SCR}/live.parquet")
t["wk"] = pd.to_datetime(t.date).dt.to_period("W-FRI").astype(str)
rows = []
for w in sorted(t.wk.unique()):
    past, nxt = t[t.wk < w], t[t.wk == w]
    if past.date.nunique() < 5: continue
    def f(g):
        d = g.groupby("date").r.sum()
        return pd.Series({"n": len(g), "avg": g.r.mean(), "worst": d.min(), "dsd": d.std(ddof=1), "lpd": len(g) / len(d), "ulcer": np.sqrt(((d.cumsum() - np.maximum(d.cumsum().cummax(), 0)) ** 2).mean())})
    a = past.groupby("strategy").apply(f); a = a[a.n >= 20]
    b = nxt.groupby("strategy").apply(f); b = b[b.n >= 5]
    j = a.join(b, rsuffix="_n", how="inner")
    if len(j) < 20: continue
    rec = {"wk": w, "N": len(j)}
    for c in ["avg", "worst", "dsd", "lpd", "ulcer"]:
        rec[c + "->avg"] = stats.spearmanr(j[c], j.avg_n).correlation
        rec[c + "->worst"] = stats.spearmanr(j[c], j.worst_n).correlation
    rec["avg->avg"] = stats.spearmanr(j.avg, j.avg_n).correlation
    rec["dsd->dsd"] = stats.spearmanr(j.dsd, j.dsd_n, nan_policy="omit").correlation
    rec["lpd->lpd"] = stats.spearmanr(j.lpd, j.lpd_n).correlation
    rows.append(rec)
r = pd.DataFrame(rows).set_index("wk")
pd.set_option("display.width", 250)
print(r.round(2).to_string())
print("\nMean over folds (t):")
for c in r.columns[1:]:
    x = r[c].dropna(); print(f"  {c:14s} {x.mean():6.3f} (t {x.mean()/(x.std(ddof=1)/np.sqrt(len(x))):5.2f})")
