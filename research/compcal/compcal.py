"""COMPCAL (plan PLAN.md, frozen before any score): M0 cell table vs M1 remaining-move benchmark vs M2 (M1 + prior-close
side) for P(SPY closes on the same side of its open as at mark T). SPY 1-min SIP cache; locked block dropped (asserted).
    python compcal.py > compcal_out.txt          Educational only - not financial advice."""
import os
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
HERE = Path(__file__).resolve().parent; NY = "America/New_York"
TL0, TL1 = pd.Timestamp("2024-11-01", tz=NY), pd.Timestamp("2025-03-01", tz=NY)
p = "/home/user/MCF/data/cache_hist/1Min/SPY.parquet"; ix = "__index_level_0__"
s = pds.dataset(p, format="parquet").to_table(filter=(pds.field(ix) < TL0) | (pds.field(ix) >= TL1)).to_pandas()
if ix in s.columns: s = s.set_index(ix)
s.index = pd.DatetimeIndex(s.index).tz_convert(NY); s = s[~s.index.duplicated(keep="last")].sort_index()
assert not ((s.index >= TL0) & (s.index < TL1)).any()
m = s.index.hour * 60 + s.index.minute; s = s[(m >= 570) & (m < 960)]; s["m"] = s.index.hour * 60 + s.index.minute
MARKS = list(range(600, 951, 10))
days = []
for d, g in s.groupby(s.index.date):
    if g.m.iloc[0] != 570 or g.m.iloc[-1] < 955: continue            # full sessions only (half days out)
    o, cl = g.open.iloc[0], g.close.iloc[-1]
    for T in MARKS:
        x = g[g.m < T]
        if not len(x): continue
        c = x.close.iloc[-1]; days.append((d, T, (c / o - 1) * 100, (cl / c - 1) * 100 * (c / o), c, cl, o))
D = pd.DataFrame(days, columns=["date", "T", "fo", "m_pct_o", "cT", "close", "open"])
D["m"] = (D.close / D.open - 1) * 100 - D.fo                          # rest-of-day move in % of the open
pc = D.groupby("date").close.first().shift(1)                        # yesterday's close (consecutive sessions in the table)
gap = pd.Series(pd.to_datetime(pc.index)).diff().dt.days.to_numpy() > 5; pc[gap] = np.nan
D["pc"] = D.date.map(pc); D = D.dropna(subset=["pc"]); D = D[D.fo != 0].copy()
D["y"] = (np.sign(D.fo + D.m) == np.sign(D.fo)).astype(int)
D["same_pc"] = (np.sign(D.cT - D.pc) == np.sign(D.fo)).astype(int)
dt = pd.to_datetime(D.date)
D["per"] = np.where(dt <= "2025-09-30", "TRAIN", np.where(dt <= "2026-10-07", "VALID", "FWD"))
# M1: prior 60 sessions' rest-of-day moves from the same T
dl = sorted(D.date.unique()); pos = {d: i for i, d in enumerate(dl)}
M = D.pivot_table(index="date", columns="T", values="m")
p1 = []
for d, T, fo in zip(D.date, D["T"], D.fo):
    i = pos[d]; prev = M[T].reindex(dl[max(0, i - 60):i]).dropna().to_numpy()
    p1.append(np.mean(np.sign(fo) * (fo + prev) > 0) if len(prev) >= 30 else np.nan)
D["M1"] = p1; D = D.dropna(subset=["M1"]).copy()
# M0: TRAIN cell table
bins = [-np.inf, -.4, -.2, 0, .2, .4, np.inf]; D["bin"] = pd.cut(D.fo, bins, labels=False)
tr = D[D.per == "TRAIN"]
c3 = tr.groupby(["T", "bin", "same_pc"]).y.agg(["sum", "size"]); c2 = tr.groupby(["T", "bin"]).y.agg(["sum", "size"])
def m0(T, b, sp):
    k = (T, b, sp)
    if k in c3.index and c3.loc[k, "size"] >= 15: r = c3.loc[k]
    elif (T, b) in c2.index: r = c2.loc[(T, b)]
    else: return 0.5
    return (r["sum"] + 1) / (r["size"] + 2)
D["M0"] = [m0(T, b, sp) for T, b, sp in zip(D["T"], D.bin, D.same_pc)]
# M2: logistic on TRAIN (Newton)
lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
X = np.column_stack([np.ones(len(D[D.per == "TRAIN"])), lg(D[D.per == "TRAIN"].M1.to_numpy()), D[D.per == "TRAIN"].same_pc.to_numpy()])
yv = D[D.per == "TRAIN"].y.to_numpy(); w = np.zeros(3)
for _ in range(50):
    pr = 1 / (1 + np.exp(-X @ w)); H = X.T @ (X * (pr * (1 - pr))[:, None]); w += np.linalg.solve(H + 1e-9 * np.eye(3), X.T @ (yv - pr))
D["M2"] = 1 / (1 + np.exp(-(w[0] + w[1] * lg(D.M1.to_numpy()) + w[2] * D.same_pc.to_numpy())))
print(f"marks {len(D)} on {D.date.nunique()} days; periods {D.groupby('per').date.nunique().to_dict()}; M2 coef a {w[0]:+.3f} b {w[1]:+.3f} c(same prior-close side) {w[2]:+.3f}")
out = []
for per in ("TRAIN", "VALID", "FWD"):
    x = D[D.per == per]
    for mdl in ("M0", "M1", "M2"):
        b = (x[mdl] - x.y) ** 2; ll = -(x.y * np.log(np.clip(x[mdl], 1e-4, 1)) + (1 - x.y) * np.log(np.clip(1 - x[mdl], 1e-4, 1)))
        out.append(dict(period=per, model=mdl, n=len(x), days=x.date.nunique(), brier=round(b.mean(), 5), logloss=round(ll.mean(), 5), base_rate=round(x.y.mean(), 4)))
    for a, b_ in (("M1", "M0"), ("M2", "M0"), ("M2", "M1")):
        dd = ((x[a] - x.y) ** 2 - (x[b_] - x.y) ** 2).groupby(x.date).mean()
        out.append(dict(period=per, model=f"{a}-{b_} brier diff", n=len(dd), brier=round(dd.mean(), 5), logloss=None,
                        base_rate=round(dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))), 2)))
O = pd.DataFrame(out); pd.set_option("display.width", 200); print(O.to_string(index=False)); print("(for the diff rows, base_rate column = day-clustered t; negative brier diff = first model better)")
print("\ncalibration (VALID+FWD pooled; predicted-prob decile: mean predicted vs observed):")
z = D[D.per != "TRAIN"]
for mdl in ("M0", "M1", "M2"):
    q = pd.qcut(z[mdl].rank(method="first"), 10, labels=False)
    t = z.groupby(q).agg(pred=(mdl, "mean"), obs=("y", "mean")).round(3)
    print(f"  {mdl}: " + "  ".join(f"{a:.2f}->{b:.2f}" for a, b in zip(t.pred, t.obs)))
O.to_csv(HERE / "compcal_results.csv", index=False)
print("Educational only - not financial advice.")
