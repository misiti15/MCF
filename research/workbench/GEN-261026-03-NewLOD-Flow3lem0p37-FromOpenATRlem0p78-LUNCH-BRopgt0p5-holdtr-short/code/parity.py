"""Mechanic GEN-261026-03: replay parity vs the live journal (Gen ran with no cost filter -> cf=None for this check).
Educational only - not financial advice."""
import pandas as pd
from sim import *
D = load(); RC, RP = D["rep"]
L = pd.read_pickle(OUT + "live.pkl")
L["sig"] = pd.to_datetime(L.signal_time, utc=True).dt.tz_convert("America/New_York")
L["tod"] = ((L.sig.dt.floor("5min")).dt.hour * 100 + (L.sig.dt.floor("5min")).dt.minute)
t = trades(RC, RP, {"cf": None}); tc = trades(RC, RP, {})
m = L.merge(t[["symbol", "date", "tod", "r", "why"]], on=["symbol", "date"], how="outer", suffixes=("_live", "_rep"), indicator=True)
m = m[m.date <= "2026-11-13"]
print(m[["symbol", "date", "tod_live", "tod_rep", "r_live", "r_rep", "exit_reason", "why", "_merge"]].sort_values(["date", "symbol"]).round(2).to_string())
print(m._merge.value_counts())
print("live-day replay trades (cf off):", stats(t[t.date.isin(set(L.date))]))
print("replay cf off:", stats(t)); print("replay cf 0.15 (parent as run in Testing D):", stats(tc))
print("cf removes live trades:", sorted(set(zip(t.symbol, t.date)) - set(zip(tc.symbol, tc.date)) & set(zip(L.symbol, L.date))))
