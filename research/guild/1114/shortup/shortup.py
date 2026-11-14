"""SHORTUP scorer (PLAN.md frozen 2026-11-14 05:30 ET). One look.
    python -I shortup.py <data dir with m30.csv.gz, daily.csv.gz>        Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
D = sys.argv[1]; ETF = "XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split(); BAR = 3.57
m = pd.read_csv(f"{D}/m30.csv.gz"); m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
m = m[(m.hm >= 930) & (m.hm <= 1530)]
assert not ((m.date >= "2024-11-01") & (m.date <= "2025-02-28")).any()
# sector map on formation 2025-03-03..2025-04-30
f = m[(m.date >= "2025-03-03") & (m.date <= "2025-04-30")].sort_values(["symbol", "t"]).copy()
f["r"] = f.groupby(["symbol", "date"]).c.pct_change(); W = f.pivot_table(index=["date", "hm"], columns="symbol", values="r")
names = [s for s in W.columns if s not in ETF + ["SPY"]]
C = pd.DataFrame({e: W[names].corrwith(W[e]) for e in ETF}); sec = C.idxmax(axis=1)[C.max(axis=1) >= 0.40]
print(f"names {len(names)}; sector-mapped (corr >= 0.40): {len(sec)}; {sec.value_counts().to_dict()}")
# ATR% from daily, days < D
d = pd.read_csv(f"{D}/daily.csv.gz"); d["date"] = d.t.str[:10]; d = d.sort_values(["symbol", "date"])
pc = d.groupby("symbol").c.shift(1); gap = (pd.to_datetime(d.date) - pd.to_datetime(d.groupby("symbol").date.shift(1))).dt.days
pc[gap > 5] = np.nan                                     # no true range across the locked-block hole
d["tr"] = np.maximum(d.h, pc) - np.minimum(d.l, pc)
d["atrp"] = d.groupby("symbol").tr.transform(lambda x: x.rolling(14, min_periods=10).mean().shift(1)) / pc
A = d.set_index(["date", "symbol"]).atrp
P = lambda hm, col: m[m.hm == hm].pivot_table(index="date", columns="symbol", values=col)
o930, c1000, o1030, o1130 = P(930, "o"), P(1000, "c"), P(1030, "o"), P(1130, "o")
days = [x for x in sorted(set(o930.index) & set(c1000.index) & set(o1030.index) & set(o1130.index)) if x >= "2025-05-01"]
rows = []
for day in days:
    if not (c1000.loc[day, "SPY"] > o930.loc[day, "SPY"]): continue
    er = (c1000.loc[day, ETF] / o930.loc[day, ETF] - 1).dropna()
    if er.empty: continue
    top = er.idxmax()
    spy = o1130.loc[day, "SPY"] / o1030.loc[day, "SPY"] - 1
    cand = pd.DataFrame({"o": o930.loc[day], "c": c1000.loc[day], "e": o1030.loc[day], "x": o1130.loc[day]}).dropna()
    cand = cand[cand.index.isin(sec.index) & (cand.e >= 5)]
    cand["atrp"] = [A.get((day, s), np.nan) for s in cand.index]; cand = cand.dropna()
    cand = cand[cand.atrp > 0]
    if len(cand) < 50: continue
    cand["mv"] = (cand.c / cand.o - 1) / cand.atrp
    cand["cx"] = (cand.x / cand.e - 1) - spy
    mem = cand[cand.index.map(sec) == top]
    if mem.empty: continue
    pick = mem.mv.idxmax(); top3 = mem.mv.nlargest(3).index
    dec = cand[cand.mv >= cand.mv.quantile(0.9)].drop(pick, errors="ignore")
    p = cand.loc[pick]; cost = (0.01 + p.e * (1.4e-4 + 4.4e-4)) / p.e + (0.01 + p.x * 1e-4) / p.x
    rows.append(dict(date=day, sector=top, pick=pick, c_bps=p.cx * 1e4, c_atr=p.cx / p.atrp, ctl_atr=(dec.cx / dec.atrp).mean(),
                     raw_bps=(p.x / p.e - 1) * 1e4, net_bps=(p.cx - cost) * 1e4, top3_atr=(cand.loc[top3].cx / cand.loc[top3].atrp).mean(),
                     etf_bps=(o1130.loc[day, top] / o1030.loc[day, top] - 1 - spy) * 1e4))
R = pd.DataFrame(rows).set_index("date"); R["x"] = R.c_atr - R.ctl_atr
tt = lambda v: v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))
print(f"test days {len(days)}; up readings traded {len(R)}")
print(f"pick ex-mkt: {R.c_bps.mean():+.1f}bps gross (t {tt(R.c_bps):+.2f}), net {R.net_bps.mean():+.1f}bps; {R.c_atr.mean():+.4f} ATR")
print(f"control (top-decile movers, same minute): {R.ctl_atr.mean():+.4f} ATR; EXCESS {R.x.mean():+.4f} ATR (day-t {tt(R.x):+.2f})")
print(f"top-3 picks {R.top3_atr.mean():+.4f} ATR; strongest-sector ETF over the hour {R.etf_bps.mean():+.1f}bps ex-SPY; pick raw {R.raw_bps.mean():+.1f}bps")
tr, va = R[R.index <= "2025-12-31"], R[R.index > "2025-12-31"]
print(f"TRAIN excess {tr.x.mean():+.4f} (t {tt(tr.x):+.2f}, n {len(tr)}) | VALID {va.x.mean():+.4f} (t {tt(va.x):+.2f}, n {len(va)})")
wob = R.drop(R.x.idxmax()).x.mean()
ok = tt(R.x) >= BAR and R.c_bps.mean() > 0 and R.net_bps.mean() > 0 and tr.x.mean() > 0 and va.x.mean() > 0 and wob > 0
print(f"excess w/o best day {wob:+.4f}. PASS {ok}{'' if ok else ' -> SHORTUP closed'} (bar 3.57; family 2,609). Educational only - not financial advice.")
R.to_csv("shortup_days.csv")
