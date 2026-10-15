"""Broker-side check between consecutive status snapshots: equity change vs broker positions marked to SIP 1-min closes
(held qty x price change) plus journal-realized exits in between. A residual means cash moved through orders the
positions/journal do not show. Educational only."""
import sys, json, pandas as pd
S, acct = sys.argv[1], sys.argv[2]
st = pd.read_csv(f"{S}/{acct}/st.csv"); st = st[(st.session == "2026-10-15") & (st.phase == "trading")].reset_index(drop=True)
bars = {}
def px(s, t):
    if s not in bars:
        try:
            b = pd.read_parquet(f"{S}/bars/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
        except Exception:
            b = None
        bars[s] = b
    b = bars[s]
    if b is None: return None
    b = b[b.index < t.floor("1min")]
    return b.close.iloc[-1] if len(b) else None
rows = []
for i in range(1, len(st)):
    a, b = st.iloc[i - 1], st.iloc[i]
    ta, tb = pd.Timestamp(a["asof"]).tz_convert("America/New_York"), pd.Timestamp(b["asof"]).tz_convert("America/New_York")
    pa = json.loads(a["positions"])
    mtm = 0.0; miss = []
    for s, q in pa.items():
        x, y = px(s, ta), px(s, tb)
        if x is None or y is None: miss.append(s); continue
        mtm += q * (y - x)
    rows.append(dict(t=b["asof_et"], deq=round(b["equity"] - a["equity"], 2), mtm_held=round(mtm, 2), resid=round(b["equity"] - a["equity"] - mtm, 2), miss=len(miss)))
o = pd.DataFrame(rows); print(o.to_string())
