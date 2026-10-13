"""Per-setup P/L marked at a given time (realized + open lots marked to the SIP 1-min close). Educational only."""
import sys, pandas as pd
S = sys.argv[1]
T = pd.read_csv("trades.csv", parse_dates=["nt", "et"])
T["nt"] = pd.to_datetime(T.nt, utc=True).dt.tz_convert("America/New_York"); T["et"] = pd.to_datetime(T.et, utc=True).dt.tz_convert("America/New_York")
bars = {}
def px(s, t):
    if s not in bars:
        b = pd.read_parquet(f"{S}/bars/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York"); bars[s] = b
    b = bars[s]; b = b[b.index < t]
    return b.close.iloc[-1]
def at(acct, hhmm):
    t = pd.Timestamp(f"2026-10-13 {hhmm}", tz="America/New_York")
    d = T[(T.acct == acct) & (T.nt < t)].copy()
    d["v"] = [r.pnl if r.et <= t else r.side * (px(r.symbol, t) - r.entry) * r.shares for r in d.itertuples()]
    return d.groupby("strategy").v.sum().sort_values()
for acct, hh in [("p", "11:39"), ("t1", "11:37"), ("t2", "10:13"), ("t1", "13:30")]:
    s = at(acct, hh); print(f"== {acct} at {hh}: total {s.sum():.2f}"); print(" top:", s.tail(5).round(1).to_dict()); print(" bottom:", s.head(4).round(1).to_dict())
for k in ["SPY", "QQQ", "IWM"]:
    b = pd.read_parquet(f"{S}/bars/{k}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
    b = b.between_time("09:30", "15:59"); o = b.open.iloc[0]
    r = (b.close / o - 1) * 100
    print(k, "close %+.2f%%" % r.iloc[-1], "hi %+.2f%% at %s" % (r.max(), r.idxmax().strftime("%H:%M")), "lo %+.2f%% at %s" % (r.min(), r.idxmin().strftime("%H:%M")),
          {h: round(r[r.index.strftime("%H:%M") == h].iloc[0], 2) for h in ["10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "14:00", "15:00"]})
