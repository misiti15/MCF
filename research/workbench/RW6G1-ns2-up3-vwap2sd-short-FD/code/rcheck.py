import sys, numpy as np, pandas as pd
sys.path.insert(0, "code"); import sim3, band, importlib.util
src = open("code/load.py").read().split("C = pd.read_parquet")[0]
exec(src)
v = sim3.BASE
s = sim3.signals(RF, v); print("replay signals", len(s), s.groupby(["symbol","date"]).ngroups)
t = sim3.book(sim3.trades(RF, v, getA), v); print(sim3.stats(t)); print(t.kind.value_counts())
# parity vs module mask on replay frames (module needs volume: use 5-min from 1-min)
L = pd.read_parquet("signals.parquet"); L = L[L.day <= "2026-11-13"]
L["tod"] = pd.to_datetime(L.ts, utc=True).dt.tz_convert("America/New_York"); L["tod"] = ((L.tod.dt.floor("5min")).dt.hour*100 + (L.tod.dt.floor("5min")).dt.minute)
ls = set(zip(L.symbol, L.day, L.tod)); ss = set(zip(s.symbol, s.date, s.tod))
print("live sig bars", len(ls), "bench", len(ss), "overlap", len(ls & ss))
print("live-only sample", sorted(ls - ss)[:15]); print("bench-only sample", sorted(ss - ls)[:15])
t.to_parquet("parent_replay.parquet")
