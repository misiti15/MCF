"""PVSCALE (plan PLAN.md, frozen before any score): alpha-partial vol scaling for M1 (close side) and the size band.
    python pvscale.py > pvscale_out.txt          Educational only - not financial advice."""
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
ALPHAS = np.round(np.arange(0, 1.01, 0.1), 1)
MK_SIDE = list(range(600, 951, 10)); MK_SIZE = list(range(585, 916, 15)); HZ = {"30m": 30, "60m": 60, "90m": 90, "close": None}
rows_side, rows_size = [], []
for d, g in s.groupby(s.index.date):
    if g.m.iloc[0] != 570 or g.m.iloc[-1] < 955: continue
    o, cl = g.open.iloc[0], g.close.iloc[-1]; mm = g.m.to_numpy(); C = g.close.to_numpy(); H = g.high.to_numpy(); L = g.low.to_numpy()
    for T in sorted(set(MK_SIDE) | set(MK_SIZE)):
        k = np.searchsorted(mm, T)                        # bars with start < T
        if k == 0: continue
        c = C[k - 1]; rg = (H[:k].max() - L[:k].min()) / o * 100
        if T in MK_SIDE: rows_side.append((d, T, (c / o - 1) * 100, (cl / o - 1) * 100 - (c / o - 1) * 100, rg))
        if T in MK_SIZE:
            for hz, h in HZ.items():
                if h is None: e = cl
                else:
                    j = np.searchsorted(mm, T + h)
                    if j == 0 or T + h > 955: continue
                    e = C[j - 1]
                rows_size.append((d, T, hz, abs(e / c - 1) * 100, rg))
A = pd.DataFrame(rows_side, columns=["date", "T", "fo", "m", "rg"]); A = A[A.fo != 0]
Z = pd.DataFrame(rows_size, columns=["date", "T", "hz", "mv", "rg"])
per = lambda d: np.where(pd.to_datetime(d) <= "2025-09-30", "TRAIN", np.where(pd.to_datetime(d) <= "2026-10-07", "VALID", "FWD"))
A["per"] = per(A.date); Z["per"] = per(Z.date)
dl = sorted(A.date.unique()); pos = {d: i for i, d in enumerate(dl)}
MV = A.pivot_table(index="date", columns="T", values="m"); RG = A.pivot_table(index="date", columns="T", values="rg")
A["y"] = (np.sign(A.fo + A.m) == np.sign(A.fo)).astype(int)
P = {a: [] for a in ALPHAS}
for d, T, fo, rg in zip(A.date, A["T"], A.fo, A.rg):
    i = pos[d]; ixd = dl[max(0, i - 60):i]; mv = MV[T].reindex(ixd).to_numpy(); rv = RG[T].reindex(ixd).to_numpy()
    ok = np.isfinite(mv) & np.isfinite(rv) & (rv > 0)
    for a in ALPHAS:
        P[a].append(np.mean(np.sign(fo) * (fo + mv[ok] * (rg / rv[ok]) ** a) > 0) if ok.sum() >= 30 else np.nan)
for a in ALPHAS: A[f"p{a}"] = P[a]
A = A.dropna(subset=[f"p{a}" for a in ALPHAS]).copy()
tr = A[A.per == "TRAIN"]; brier_tr = {a: float(((tr[f"p{a}"] - tr.y) ** 2).mean()) for a in ALPHAS}
a1 = min(brier_tr, key=brier_tr.get)
print(f"M1-alpha: close-side marks {len(A)} on {A.date.nunique()} days; TRAIN Brier by alpha: " + " ".join(f"{a}:{v:.5f}" for a, v in brier_tr.items()) + f" -> alpha* {a1}")
tq = tr.groupby("T").rg.quantile([1/3, 2/3]).unstack(); A["volt"] = np.where(A.rg <= A["T"].map(tq[1/3]), "low", np.where(A.rg >= A["T"].map(tq[2/3]), "high", "mid"))
def dclust(x, col_a, col_b, f):
    dd = (f(x, col_a) - f(x, col_b)).groupby(x.date).mean(); return dd.mean(), dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))), dd.std(ddof=1) / np.sqrt(len(dd))
bri = lambda x, c: (x[c] - x.y) ** 2
for pr in ("VALID", "FWD"):
    x = A[A.per == pr]; mu, t, se = dclust(x, f"p{a1}", "p0.0", bri)
    print(f"  {pr}: Brier alpha* {bri(x, f'p{a1}').mean():.5f} vs alpha 0 {bri(x, 'p0.0').mean():.5f}; per-day diff {mu:+.5f} (se {se:.5f}), day-t {t:.2f}")
    print("    by vol tercile (obs / alpha0 / alpha*): " + "; ".join(f"{v} {x[x.volt == v].y.mean():.3f} / {x[x.volt == v]['p0.0'].mean():.3f} / {x[x.volt == v][f'p{a1}'].mean():.3f}" for v in ("low", "mid", "high")))
# ---- size band
dz = sorted(Z.date.unique()); pz = {d: i for i, d in enumerate(dz)}
Q = {}
for hz in HZ:
    W = Z[Z.hz == hz].pivot_table(index="date", columns="T", values="mv"); R2 = Z[Z.hz == hz].pivot_table(index="date", columns="T", values="rg")
    Q[hz] = (W, R2)
for a in ALPHAS: Z[f"q50_{a}"] = np.nan; Z[f"q80_{a}"] = np.nan
q50s = {a: [] for a in ALPHAS}; q80s = {a: [] for a in ALPHAS}
for d, T, hz, rg in zip(Z.date, Z["T"], Z.hz, Z.rg):
    W, R2 = Q[hz]; i = pz[d]; ixd = dz[max(0, i - 60):i]; mv = W[T].reindex(ixd).to_numpy(); rv = R2[T].reindex(ixd).to_numpy()
    ok = np.isfinite(mv) & np.isfinite(rv) & (rv > 0)
    for a in ALPHAS:
        if ok.sum() >= 40:
            v = mv[ok] * (rg / rv[ok]) ** a; q50s[a].append(np.quantile(v, .5)); q80s[a].append(np.quantile(v, .8))
        else: q50s[a].append(np.nan); q80s[a].append(np.nan)
for a in ALPHAS: Z[f"q50_{a}"] = q50s[a]; Z[f"q80_{a}"] = q80s[a]
Z = Z.dropna(subset=[f"q80_{a}" for a in ALPHAS]).copy()
pin = lambda y, q, tau: np.where(y >= q, tau * (y - q), (1 - tau) * (q - y))
for a in ALPHAS: Z[f"pl_{a}"] = pin(Z.mv, Z[f"q50_{a}"], .5) + pin(Z.mv, Z[f"q80_{a}"], .8)
tz = Z[Z.per == "TRAIN"]; pl_tr = {a: float(tz[f"pl_{a}"].mean()) for a in ALPHAS}; a2 = min(pl_tr, key=pl_tr.get)
print(f"\nSIZE-alpha: rows {len(Z)} on {Z.date.nunique()} days; TRAIN pinball by alpha: " + " ".join(f"{a}:{v:.4f}" for a, v in pl_tr.items()) + f" -> alpha* {a2}")
tq2 = tz.groupby("T").rg.quantile([1/3, 2/3]).unstack(); Z["volt"] = np.where(Z.rg <= Z["T"].map(tq2[1/3]), "low", np.where(Z.rg >= Z["T"].map(tq2[2/3]), "high", "mid"))
for pr in ("VALID", "FWD"):
    x = Z[Z.per == pr]; dd = (x[f"pl_{a2}"] - x["pl_0.0"]).groupby(x.date).mean(); se = dd.std(ddof=1) / np.sqrt(len(dd))
    cov = lambda a: (f"in80 {(x.mv <= x[f'q80_{a}']).mean():.3f} in50 {(x.mv <= x[f'q50_{a}']).mean():.3f}")
    print(f"  {pr}: pinball alpha* {x[f'pl_{a2}'].mean():.4f} vs alpha 0 {x['pl_0.0'].mean():.4f}; per-day diff {dd.mean():+.4f} (se {se:.4f}), day-t {dd.mean() / se:.2f} | alpha0 {cov('0.0')} | alpha* {cov(a2)}")
    print("    in80 by vol tercile (alpha0 -> alpha*): " + "; ".join(f"{v} {(x[x.volt == v].mv <= x[x.volt == v]['q80_0.0']).mean():.2f} -> {(x[x.volt == v].mv <= x[x.volt == v][f'q80_{a2}']).mean():.2f}" for v in ("low", "mid", "high")))
print("\nadoption rule (fixed): use alpha* if VALID improves with day-t <= -1.0 AND FWD not worse by > 1 se; else alpha 0.")
print("Educational only - not financial advice.")
