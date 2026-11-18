"""U7: trades of the 20 setups + entry-time features + 1-min paths (Alpaca SIP). Writes prep.pkl and paths.pkl."""
import sys, os, glob, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u7"
t = pd.read_pickle(f"{S}/trades2.pkl"); top = open(f"{S}/top20.txt").read().split()
x = t[t.strategy.isin(top)].copy()
# de-dup: same setup / symbol-day in >1 account -> keep the account with most trades of that setup
cnt = x.groupby(["strategy", "acct"]).size()
x["acn"] = [cnt[(s, a)] for s, a in zip(x.strategy, x.acct)]
best = x.groupby(["strategy", "symbol", "date"]).acn.transform("max")
nd = x.groupby(["strategy", "symbol", "date"]).acct.transform("nunique")
drop = (nd > 1) & (x.acn < best)
print("dedup dropped", int(drop.sum()))
x = x[~drop].copy()
# daily priors
dd = pd.read_parquet(f"{S}/daily.parquet"); dd["d"] = pd.to_datetime(dd.ts).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
dd = dd.sort_values(["symbol", "d"])
pri = {}
for s, g in dd.groupby("symbol"):
    pc = g.close.shift(); tr = np.maximum(g.high - g.low, np.maximum((g.high - pc).abs(), (g.low - pc).abs()))
    atr = tr.rolling(14).mean().shift(); adv = g.volume.rolling(20, min_periods=10).mean().shift()
    for d, a, b, c in zip(g.d, atr, adv, pc): pri[(s, d)] = (a, b, c)
paths = {}
rows = []
for d, g in x.groupby("date"):
    m = pd.read_parquet(f"{S}/m1/{d}.parquet")
    m["ts"] = pd.to_datetime(m.ts).dt.tz_convert("America/New_York")
    m = m[(m.ts.dt.strftime("%H:%M") >= "09:30") & (m.ts.dt.strftime("%H:%M") < "16:00")]
    for s, b in m.groupby("symbol"):
        b = b.sort_values("ts")
        mins = ((b.ts.dt.hour * 60 + b.ts.dt.minute) - 570).to_numpy()
        pv = (b.high + b.low + b.close) / 3 * b.volume
        vw = (pv.cumsum() / b.volume.cumsum().replace(0, np.nan)).to_numpy()
        paths[(d, s)] = dict(m=mins, o=b.open.to_numpy(), h=b.high.to_numpy(), l=b.low.to_numpy(), c=b.close.to_numpy(),
                             cv=b.volume.cumsum().to_numpy(), vw=vw)
for i, r in x.iterrows():
    P = paths.get((r.date, r.symbol)); a, adv, pc = pri.get((r.symbol, r.date), (np.nan, np.nan, np.nan))
    em = (r.et.hour * 60 + r.et.minute) - 570 + r.et.second / 60
    f = dict(idx=i, emin=em, risk_pct=abs(r.entry - r.stop) / r.entry,
             stopcost=(max(0.02, 4e-4 * r.entry) + 0.01) / abs(r.entry - r.stop))
    if P is not None and len(P["m"]) and P["m"][0] <= 5:
        k = np.searchsorted(P["m"], int(em)) - 1     # last completed bar before entry minute
        if k >= 0 and a == a and a > 0:
            px = P["c"][k]; op = P["o"][0]
            f.update(ext=r.side * (px - op) / a, vwd=r.side * (px - P["vw"][k]) / a,
                     gap=r.side * (op / pc - 1) if pc == pc else np.nan,
                     rvol=P["cv"][k] / (adv * max(P["m"][k] + 1, 1) / 390) if adv == adv and adv > 0 else np.nan)
    rows.append(f)
F = pd.DataFrame(rows).set_index("idx")
x = x.join(F)
x["tR"] = (x.target - x.entry).abs() / (x.entry - x.stop).abs()
x["nth"] = x.sort_values("et").groupby(["strategy", "symbol", "date"]).cumcount() + 1
x.to_pickle(f"{S}/prep.pkl"); pd.to_pickle(paths, f"{S}/paths.pkl")
print(len(x), x[["ext", "vwd", "gap", "rvol"]].notna().mean().round(3).to_dict())
