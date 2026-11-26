"""Tag each live trade with point-in-time index state at entry (bars closed before the entry minute) + hindsight day type."""
import numpy as np, pandas as pd
D = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/crd/"
t = pd.read_parquet(D + "live.parquet")
et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["em"] = et.dt.hour * 60 + et.dt.minute
b = pd.read_parquet(D + "idx_bars.parquet"); b["date"] = b.ts.dt.date.astype(str); b["m"] = b.ts.dt.hour * 60 + b.ts.dt.minute
fo = {}
day = {}
for s, g in b.groupby("symbol"):
    for d, x in g.groupby("date"):
        x = x.sort_values("m"); o = x.open.iloc[0]
        arr = np.full(400, np.nan); mm = x.m.values - 570; ok = (mm >= 0) & (mm < 390)
        arr[mm[ok] + 1] = x.close.values[ok] / o - 1      # value available at minute index m+1 (bar closed)
        arr = pd.Series(arr).ffill().fillna(0).values
        fo[(s, d)] = arr
        if s == "SPY":
            day[d] = dict(o=o, c=x.close.iloc[-1], lo=x.low.min() / o - 1, hi=x.high.max() / o - 1)
dd = pd.DataFrame(day).T.sort_index(); dd["pc"] = dd.c.shift(); dd["gap"] = dd.o / dd.pc - 1; dd["oc"] = dd.c / dd.o - 1
def dtype(r):
    if r.oc >= 0.0025 and r.lo <= -0.005: return "V-up"
    if r.oc <= -0.0025 and r.hi >= 0.005: return "V-down"
    return "up" if r.oc >= 0.0025 else ("down" if r.oc <= -0.0025 else "flat")
dd["dtype"] = dd.apply(dtype, axis=1)
idx = np.clip(t.em.values - 570, 0, 389)
for s in ("SPY", "QQQ", "IWM"):
    t[s.lower() + "_fo"] = [fo.get((s, d), np.zeros(400))[i] for d, i in zip(t.date, idx)]
t = t[t.date.isin(dd.index)]
t["gap"] = t.date.map(dd.gap); t["dtype"] = t.date.map(dd.dtype); t["day_oc"] = t.date.map(dd.oc)
th = lambda v, k: np.where(v > k, 1, np.where(v < -k, -1, 0))
a, q, w = th(t.spy_fo, .001), th(t.qqq_fo, .001), th(t.iwm_fo, .001)
t["idx3"] = np.where((a == q) & (q == w), a, 0)
t["gapst"] = th(t.gap, .0025)
t.to_parquet(D + "live_feat.parquet")
dd.to_csv(D + "spy_days.csv")
print(len(t)); print(dd[["gap", "oc", "dtype"]].tail(40).round(4).to_string())
