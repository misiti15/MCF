"""Mechanic GEN-261023-09: replay parity vs the live journal (all 10 live trades are Setup Generator, 2026-11-09, no cost
filter -> cf=None for this check). Educational only - not financial advice."""
import pandas as pd
from sim import *
from common import SETUP
from mcf.report import engine as E
tr, sigs = E.live_trades(SETUP)
L = pd.DataFrame(tr); L["sig"] = pd.to_datetime(L.signal_time, utc=True).dt.tz_convert("America/New_York")
f = L.sig.dt.floor("5min"); L["tod"] = f.dt.hour * 100 + f.dt.minute
L.to_pickle(OUT + "live.pkl")
D = load(); RC, RP = D["rep"]
t = trades(RC, RP, {"cf": None}); tc = trades(RC, RP, {})
m = L.merge(t[["symbol", "date", "tod", "r", "why", "mfe", "fill"]], on=["symbol", "date"], how="outer", suffixes=("_live", "_rep"), indicator=True)
m = m[m.date == "2026-11-09"]
print(m[["symbol", "tod_live", "tod_rep", "entry", "fill", "r_live", "r_rep", "exit_reason", "why", "mfe_r", "mfe", "_merge"]].sort_values("symbol").round(3).to_string())
print(m._merge.value_counts().to_dict())
print("signals logged live (all, incl. blocked):", sorted({(s.get('symbol'), s.get('date')) for s in sigs})[:40] if sigs and isinstance(sigs[0], dict) else len(sigs))
print("replay cf off:", stats(t)); print("replay cf 0.15 (parent as run in Testing E):", stats(tc))
print("replay parent by day:", t.groupby("date").r.agg(["count", "sum"]).round(2).to_dict())
