"""Broker equity change (status.json) vs journal P/L marked at the same time (realized + open lots at the SIP 1-min close).
Localizes when a broker-vs-journal gap appears. Educational only."""
import sys, pandas as pd
S, acct, pre = sys.argv[1], sys.argv[2], float(sys.argv[3])
T = pd.read_csv("trades.csv"); T = T[T.acct == acct].copy()
for c in ("nt", "et"):
    T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
st = pd.read_csv(f"{S}/{acct}/st.csv"); st = st[(st.session == "2026-10-15") & (st.phase != "pre-open")]
bars = {}
def px(s, t):
    if s not in bars:
        b = pd.read_parquet(f"{S}/bars/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York"); bars[s] = b
    b = bars[s]; b = b[b.index < t.floor("1min")]
    return b.close.iloc[-1]
prev = 0
for r in st.itertuples():
    t = pd.Timestamp(r.asof).tz_convert("America/New_York")
    d = T[T.nt <= t]
    real = d[d.et <= t].pnl.sum()
    o = d[d.et > t]
    unr = sum(x.side * (px(x.symbol, t) - x.entry) * x.shares for x in o.itertuples())
    gap = (r.equity - pre) - (real + unr)
    flag = " <==" if abs(gap - prev) > 15 else ""
    print(f"{r.asof_et} eq {r.equity - pre:9.2f} journal {real + unr:9.2f} (real {real:8.2f}, open {len(o):3d}) gap {gap:8.2f}{flag}")
    prev = gap
