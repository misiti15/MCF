"""HODSEP descriptive scan (PLAN.md). python hodsep.py <data_dir>. 0 configs. Educational only - not financial advice."""
import re, sys, numpy as np, pandas as pd
DIR = sys.argv[1]
ETP_RE = re.compile(r"\bETF\b|\bETN\b|\bFund\b|ProShares|Direxion|iShares|SPDR|Invesco QQQ|\b[23]X\b|Leveraged|Inverse|"
                    r"\bUltra|\bBear\b|\bBull\b|Daily Target|GraniteShares|Tradr|Defiance|T-Rex|Volatility|VIX|Physical (?:Gold|Silver)", re.I)
SECT = "XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split()
uni = pd.read_csv("/home/user/MCF/data/universe.csv", usecols=["symbol", "name"])
etp = set(uni[uni.name.fillna("").str.contains(ETP_RE)].symbol) | {"SPY", "QQQ", "IWM", "DIA"}

D = pd.read_csv(f"{DIR}/daily.csv.gz"); D["date"] = pd.to_datetime(D.t, utc=True).dt.tz_convert("America/New_York").dt.date
D = D.sort_values(["symbol", "date"]); g = D.groupby("symbol")
D["pc"] = g.c.shift(1); D["ph"] = g.h.shift(1); D["pl"] = g.l.shift(1)
tr = np.maximum(D.h - D.l, np.maximum((D.h - D.pc).abs(), (D.l - D.pc).abs()))
D["atr"] = tr.groupby(D.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
D["adv20"] = (D.c * D.v).groupby(D.symbol).transform(lambda s: s.shift(1).rolling(20, min_periods=15).mean())
D["pdcl"] = ((D.pc - D.pl) / (D.ph - D.pl)).where(D.ph > D.pl)
D["ret"] = D.c / D.pc - 1
# sector assignment from daily returns 2026-06-01..2026-09-23 (before the 5-min sample)
W = D[(D.date >= pd.Timestamp("2026-06-01").date()) & (D.date <= pd.Timestamp("2026-09-23").date())].pivot(index="date", columns="symbol", values="ret")
C = W.corr().loc[:, [s for s in SECT if s in W.columns]]
SECTOR = C.drop(index=[s for s in SECT if s in C.index], errors="ignore").idxmax(axis=1).to_dict()
INFO = {(s, d): (a, adv, pc, pdcl) for s, d, a, adv, pc, pdcl in D[["symbol", "date", "atr", "adv20", "pc", "pdcl"]].itertuples(index=False)}

M = pd.read_csv(f"{DIR}/m5.csv.gz"); M["t"] = pd.to_datetime(M.t, utc=True).dt.tz_convert("America/New_York")
mm = M.t.dt.hour * 60 + M.t.dt.minute; M = M[(mm >= 570) & (mm < 960)].copy(); M["b"] = ((M.t.dt.hour * 60 + M.t.dt.minute) - 570) // 5
M["date"] = M.t.dt.date
A = {}
for (s, d), x in M.groupby(["symbol", "date"]):
    a = np.full((78, 5), np.nan); a[x.b.to_numpy()] = x[["o", "h", "l", "c", "v"]].to_numpy()
    if np.isnan(a[0, 0]): continue
    c = pd.Series(a[:, 3]).ffill().to_numpy(); miss = np.isnan(a[:, 0]); a[miss, :3] = c[miss, None]; a[:, 3] = c; a[miss, 4] = 0
    A[(s, d)] = a
DATES = sorted({d for (_, d) in A}); print(f"symbol-days {len(A)}, sessions {len(DATES)} ({DATES[0]}..{DATES[-1]}), sectors assigned {len(SECTOR)}")
I950, I1400 = 4, 53                                          # bar index of the 09:50 and 14:00 closes
rows = []
bysym = {}
for (s, d) in A: bysym.setdefault(s, []).append(d)
for s, ds in bysym.items():
    if s in etp or s in SECT: continue
    ds = sorted(ds)
    for k, d in enumerate(ds):
        inf = INFO.get((s, d))
        if inf is None or k < 5: continue
        atr, adv, pc, pdcl = inf
        if not (np.isfinite(atr) and atr > 0 and adv >= 60e6 and np.isfinite(pc)): continue
        a = A[(s, d)]; o = a[0, 0]; hod = np.maximum.accumulate(a[:, 1]); lod = np.minimum.accumulate(a[:, 2]); c = a[:, 3]
        ok = ((hod - c) <= 0.25 * atr) & (c >= o); ok[:I950] = False; ok[I1400 + 1:] = False
        h = np.flatnonzero(ok)
        if not len(h): continue
        b = int(h[0]); prev = [A[(s, x)] for x in ds[max(0, k - 20):k]]
        vn3 = np.mean([p[b - 2:b + 1, 4].sum() for p in prev]); vn6 = np.mean([p[b - 5:b + 1, 4].sum() for p in prev])
        sec = SECTOR.get(s); sa = A.get((sec, d)) if sec else None
        sr30 = (sa[b, 3] / sa[b - 6, 3] - 1) * 100 if sa is not None else np.nan
        sgap = (sa[0, 0] / INFO[(sec, d)][2] - 1) * 100 if (sa is not None and (sec, d) in INFO) else np.nan
        fwd = a[b + 1:min(78, b + 13)]
        if len(fwd) < 6: continue
        rows.append(dict(symbol=s, date=d, tod=b, sector=sec, rvol15=a[b - 2:b + 1, 4].sum() / vn3 if vn3 > 0 else np.nan,
                         rvol30=a[b - 5:b + 1, 4].sum() / vn6 if vn6 > 0 else np.nan, sector_ret30=sr30,
                         sector_minus_stock30=sr30 - (c[b] / c[b - 6] - 1) * 100 if np.isfinite(sr30) else np.nan,
                         pdcl=pdcl, gap_vs_sector=(o / pc - 1) * 100 - sgap if np.isfinite(sgap) else np.nan,
                         range_atr=(hod[b] - lod[b]) / atr, fo_atr=(c[b] - o) / atr,
                         up=float(fwd[:, 1].max() - c[b] >= 0.75 * atr), fwd60=(fwd[-1, 3] - c[b]) / atr))
X = pd.DataFrame(rows); X.to_csv(sys.path[0] + "/hodsep_rows.csv.gz" if False else f"{DIR}/hodsep_rows.csv.gz", index=False)
print(f"candidates {len(X)} on {X.date.nunique()} days; up-mover base rate {X.up.mean():.1%}; mean fwd60 {X.fwd60.mean():+.3f} ATR")
def auc(f, y):
    m = f.notna(); f, y = f[m], y[m]; r = f.rank(); n1 = y.sum(); n0 = len(y) - n1
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0) if n1 and n0 else np.nan
half = X.date < DATES[len(DATES) // 2 + 2]
F = ["rvol15", "rvol30", "sector_ret30", "sector_minus_stock30", "pdcl", "gap_vs_sector", "range_atr", "fo_atr"]
out = []
for f in F:
    q = pd.qcut(X[f].rank(method="first"), 5, labels=False)
    out.append(dict(feature=f, n=int(X[f].notna().sum()), auc=round(auc(X[f], X.up), 3), auc_h1=round(auc(X[f][half], X.up[half]), 3),
                    auc_h2=round(auc(X[f][~half], X.up[~half]), 3), up_q1=round(X.up[q == 0].mean(), 3), up_q5=round(X.up[q == 4].mean(), 3),
                    fwd_q1=round(X.fwd60[q == 0].mean(), 3), fwd_q5=round(X.fwd60[q == 4].mean(), 3),
                    q5_cut=round(float(X[f][q == 4].min()), 3)))
R = pd.DataFrame(out); pd.set_option("display.width", 250); print(R.to_string(index=False))
# days with Q5 rvol15 lift > Q1 (stability across days)
for f in ("rvol15", "rvol30", "sector_ret30", "pdcl", "gap_vs_sector"):
    dd = X.dropna(subset=[f]).groupby("date").apply(lambda g: (g.up[g[f] >= g[f].quantile(.8)].mean() - g.up[g[f] <= g[f].quantile(.2)].mean()) if len(g) >= 20 else np.nan).dropna()
    print(f"{f}: top-minus-bottom quintile up-rate per day: positive on {int((dd > 0).sum())} of {len(dd)} days, mean {dd.mean():+.3f}")
# Move Hunt movers
mv = pd.read_csv("/home/user/MCF/research/bdi/moves/moves.csv")
mv = mv[(mv.side == "long") & (mv.blackout.astype(str) != "True") & (mv.decision >= "09:50")].copy(); mv["date"] = pd.to_datetime(mv.date).dt.date
mm_ = mv.merge(X, on=["symbol", "date"], how="inner")
print(f"\nMove Hunt long movers (non-blackout, decision >= 09:50): {len(mv)}; that were near-HOD candidates that day: {len(mm_)} "
      f"(first near-HOD bar at/before decision: {int((mm_.tod <= ((mm_.decision.str[:2].astype(int) * 60 + mm_.decision.str[3:].astype(int)) - 570) // 5 - 1).sum())})")
for f in F:
    if not len(mm_): break
    pct = [float((X[(X.date == r.date)][f] < getattr(r, f)).mean()) for r in mm_.itertuples() if np.isfinite(getattr(r, f))]
    print(f"  {f}: movers' median percentile among same-day candidates {np.median(pct):.2f} (n {len(pct)})")
R.to_csv(f"{DIR}/hodsep_results.csv", index=False)
print("Educational only - not financial advice.")
