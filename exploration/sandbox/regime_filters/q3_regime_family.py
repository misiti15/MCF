"""Q3: point-in-time SPY regimes by setup family x side; persistence of best-minus-worst cell across the two halves of
DISC; and book-level per-side tables. Usage: python q3_regime_family.py <scratch>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import load, dayt
S = sys.argv[1]; t = load(S)
b = pd.read_parquet(f"{S}/spy.parquet"); b.index = pd.to_datetime(b.index)
if b.index.tz is None:
    b.index = b.index.tz_localize("America/New_York")
b = b.tz_convert("America/New_York"); b = b[(b.index.time >= pd.Timestamp("09:30").time()) & (b.index.time < pd.Timestamp("16:00").time())]
rows = {}
for d, g in b.groupby(b.index.date):
    g10 = g[g.index.time <= pd.Timestamp("09:59").time()]
    rows[str(d)] = dict(o=g.open.iloc[0], c=g.close.iloc[-1], p10=g10.close.iloc[-1] if len(g10) else g.open.iloc[0])
D = pd.DataFrame(rows).T.astype(float); D = D.sort_index()
D["ret"] = np.log(D.c / D.c.shift(1)); D["rv20"] = D.ret.rolling(20).std().shift(1) * np.sqrt(252) * 100  # known at prior close
D["gap"] = (D.o / D.c.shift(1) - 1) * 100; D["o30"] = (D.p10 / D.o - 1) * 100
cal = D[(D.index >= "2026-08-03") & (D.index < "2026-10-23")].rv20.dropna()
q1, q2 = cal.quantile([1/3, 2/3]).values
print(f"RV20 tercile cut points (fixed on 08-03..10-22, n {len(cal)}): {q1:.1f} / {q2:.1f} (ann. %)")
D["rvb"] = np.where(D.rv20 <= q1, "lowvol", np.where(D.rv20 <= q2, "midvol", "highvol"))
D["gapb"] = np.where(D.gap < -0.3, "gapdn", np.where(D.gap > 0.3, "gapup", "gapflat"))
D["o30b"] = np.where(D.o30 < -0.2, "o30dn", np.where(D.o30 > 0.2, "o30up", "o30flat"))
print(D.loc[D.index >= "2026-10-06", ["rv20", "rvb", "gap", "gapb", "o30", "o30b"]].round(2).to_string())
t = t.join(D[["rvb", "gapb", "o30b", "rv20", "gap", "o30"]], on="date")
x = t[t.period == "DISC"].copy(); x["half"] = np.where(x.date < "2026-11-10", "H1", "H2")
x.loc[x.emin < 600, "o30b"] = np.nan  # open->10:00 move only known for entries from 10:00
# book-level by side
print("\n=== DISC, all non-Graveyard accounts, R/lot by side x regime (lots; day t of daily side R) ===")
for var in ["rvb", "gapb", "o30b"]:
    g = x.dropna(subset=[var]).groupby(["sidel", var])
    tab = g.r.agg(["size", "mean", "sum"]).join(g.date.nunique().rename("days"))
    print(tab.round(3).to_string())
fam = x.groupby(["family", "sidel"]).size(); fam = fam[fam >= 150].index
res = []
for var in ["rvb", "gapb", "o30b"]:
    kept = tot = 0
    for (f, s) in fam:
        y = x[(x.family == f) & (x.sidel == s)].dropna(subset=[var])
        c1 = y[y.half == "H1"].groupby(var).r.agg(["mean", "size"]); c1 = c1[c1["size"] >= 20]
        c2 = y[y.half == "H2"].groupby(var).r.agg(["mean", "size"]); c2 = c2[c2["size"] >= 20]
        if len(c1) < 2:
            continue
        best, worst = c1["mean"].idxmax(), c1["mean"].idxmin()
        if best in c2.index and worst in c2.index:
            tot += 1; k = c2.loc[best, "mean"] > c2.loc[worst, "mean"]; kept += k
            res.append(dict(var=var, family=f, side=s, best=best, worst=worst, h1_spread=c1.loc[best, "mean"] - c1.loc[worst, "mean"],
                            h2_spread=c2.loc[best, "mean"] - c2.loc[worst, "mean"], kept=bool(k)))
    print(f"\n{var}: family x side cells with a comparable best/worst in both halves: {tot}; best-minus-worst sign kept H1->H2: {kept} ({100*kept/max(tot,1):.0f}%)")
R = pd.DataFrame(res); R.to_csv("q3_cells.csv", index=False)
print(R.round(3).to_string())
D.to_csv(f"{S}/spyday.csv")
