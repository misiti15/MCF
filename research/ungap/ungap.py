"""UNGAP pilot (PLAN.md frozen 2026-11-10 21:20 ET). python ungap.py <optflow_dir> <hodsep_dir>. 0 configs. Educational only."""
import sys, numpy as np, pandas as pd
OF, HS = sys.argv[1], sys.argv[2]
SECT = "XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split()
S = pd.read_csv(f"{OF}/stock1m.csv.gz"); S["t"] = pd.to_datetime(S.t, utc=True).dt.tz_convert("America/New_York")
S["d"] = S.t.dt.strftime("%Y-%m-%d"); S["m"] = S.t.dt.hour * 60 + S.t.dt.minute
Dd = pd.read_csv(f"{OF}/daily.csv.gz").sort_values(["symbol", "date"]); pc = Dd.groupby("symbol").c.shift(1)
tr = np.maximum(Dd.h - Dd.l, np.maximum((Dd.h - pc).abs(), (Dd.l - pc).abs()))
Dd["pc"] = pc; Dd["atr"] = tr.groupby(Dd.symbol).transform(lambda s: s.shift(1).rolling(14, min_periods=10).mean())
INFO = {(s, d): (p, a) for s, d, p, a in Dd[["symbol", "date", "pc", "atr"]].itertuples(index=False)}
H = pd.read_csv(f"{HS}/daily.csv.gz"); H["date"] = pd.to_datetime(H.t, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
H = H.sort_values(["symbol", "date"]); H["pc"] = H.groupby("symbol").c.shift(1); H["ret"] = H.c / H.pc - 1; H["gapx"] = H.o / H.pc - 1
W = H[(H.date >= "2026-06-01") & (H.date <= "2026-08-01")].pivot(index="date", columns="symbol", values="ret")
names = sorted(set(S.symbol) - {"SPY"})
C = W.corr().loc[[n for n in names if n in W.columns], [s for s in SECT if s in W.columns]]
SECTOR = C.idxmax(axis=1).to_dict()
SG = {(s, d): g for s, d, g in H[H.symbol.isin(SECT)][["symbol", "date", "gapx"]].itertuples(index=False)}
N = pd.read_csv(f"{OF}/news.csv.gz"); N["t"] = pd.to_datetime(N.t, utc=True).dt.tz_convert("America/New_York")
N = N.assign(sym=N.symbols.fillna("").str.split("|")).explode("sym")
sess = sorted(S[S.symbol == "SPY"].d.unique()); spy = {d: g.set_index("m") for d, g in S[S.symbol == "SPY"].groupby("d")}
rows = []
for k, d in enumerate(sess[1:], 1):
    lo = pd.Timestamp(f"{sess[k - 1]} 16:00", tz="America/New_York"); hi = pd.Timestamp(f"{d} 09:25", tz="America/New_York")
    newsy = set(N[(N.t >= lo) & (N.t < hi)].sym)
    sp = spy.get(d)
    if sp is None or 590 not in sp.index or 955 not in sp.index: continue
    spm = float(sp.loc[955, "c"]) / float(sp.loc[590, "o"]) - 1
    for s, g in S[(S.d == d) & (S.symbol != "SPY")].groupby("symbol"):
        g = g.set_index("m"); inf = INFO.get((s, d))
        if inf is None or not all(x in g.index for x in (570, 590, 955)) or not (np.isfinite(inf[1]) and inf[1] > 0 and np.isfinite(inf[0])): continue
        p, a = inf; gap = float(g.loc[570, "o"]) / p - 1
        e, x = float(g.loc[590, "o"]), float(g.loc[955, "c"])
        sec = SECTOR.get(s); sgap = SG.get((sec, d), np.nan)
        sector_expl = bool(np.isfinite(sgap) and np.sign(sgap) == np.sign(gap) and abs(sgap) >= 0.4 * abs(gap))
        rows.append(dict(symbol=s, date=d, gap=gap, ex=(x - e) / a - spm * e / a, news=s in newsy, sector=sector_expl))
X = pd.DataFrame(rows); X["exd"] = X.ex - X.groupby("date").ex.transform("mean")
G = X[X.gap.abs() >= 0.01].copy(); G["gs"] = np.sign(G.gap) * G.exd
G["cls"] = np.where(G.news | G.sector, "explained", "unexplained")
print(f"name-days {len(X)} ({X.symbol.nunique()} names, {X.date.nunique()} sessions); gaps >= 1%: {len(G)} -> "
      f"{G.cls.value_counts().to_dict()}; explained by news {int(G.news.sum())}, by sector {int(G.sector.sum())}")
def dt_(v, d):
    g = v.groupby(d).mean().dropna(); return g.mean(), g.mean() / (g.std(ddof=1) / np.sqrt(len(g))), len(g), int((g > 0).sum())
for c in ("explained", "unexplained"):
    m, t, n, pos = dt_(G[G.cls == c].gs, G[G.cls == c].date)
    print(f"  {c:11s} gap-signed outcome {m:+.3f} ATR (t {t:.2f}, days {n}, + {pos})")
both = G.groupby(["date", "cls"]).gs.mean().unstack().dropna()
dd = both.unexplained - both.explained
print(f"THE LOOK: unexplained minus explained (same days) {dd.mean():+.3f} ATR, day-t {dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):.2f}, "
      f"days {len(dd)}, unexplained lower on {int((dd < 0).sum())}")
mu, tu, nu, _ = dt_(-G[G.cls == "unexplained"].gs, G[G.cls == "unexplained"].date)
print(f"  unexplained FADE (minus gap-signed) {mu:+.3f} ATR, day-t {tu:.2f}")
print("  by |gap| bucket (gross gap-signed mean):", G.assign(b=pd.cut(G.gap.abs(), [0.01, 0.02, 0.04, 1])).groupby(["b", "cls"], observed=True).gs.mean().round(3).to_dict())
G.to_csv(f"{OF}/ungap_rows.csv.gz", index=False)
print("Educational only - not financial advice.")
