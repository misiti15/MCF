"""Extend the session-replay pack to 11-13..11-17: same fetch as the Workbench fetch_replay.py (read-only SIP GET)."""
import sqlite3, pandas as pd
from datetime import timedelta
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
J = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/latch/j/mcf-data.db"
s = pd.read_sql("select day, symbol, reason from signals where strategy='L3-gap-slope-fromopen-FD' and day>='2026-11-13'", sqlite3.connect(J))
s = s[~s.reason.fillna("").str.contains("shortable")]
sd = s.groupby("day").symbol.apply(lambda x: sorted(set(x))).to_dict()
F, M = [], []
for day, syms in sorted(sd.items()):
    d = pd.Timestamp(day)
    m1 = _fetch_bars(syms, f"{(d - timedelta(days=8)).date()}T13:00:00Z", f"{d.date()}T21:00:00Z", "1Min")
    dl = _fetch_bars(syms, f"{(d - timedelta(days=40)).date()}T00:00:00Z", f"{d.date()}T00:00:00Z", "1Day")
    for sym in syms:
        g = m1[m1.symbol == sym]
        if g.empty: continue
        g = g.set_index(pd.DatetimeIndex(g.ts).tz_convert(E.TZ))[["open", "high", "low", "close", "volume"]].astype(float)
        g = E._rth(g.sort_index())
        dd = dl[dl.symbol == sym]
        dd = dd.set_index(pd.DatetimeIndex(dd.ts).tz_convert(E.TZ).date)[["open", "high", "low", "close", "volume"]].astype(float)
        dd = dd[dd.index < d.date()]
        try:
            fr = E.apply_daily(E.lab_frame(g), dd, day)
        except Exception as e:
            print("frame fail", day, sym, e); continue
        fr = fr[fr.index.date == d.date()].copy(); fr["symbol"] = sym; fr["date"] = day
        F.append(fr)
        x = g[g.index.date == d.date()].copy(); x["symbol"] = sym; x["date"] = day; M.append(x)
    print(day, len(syms), flush=True)
pd.concat(F).to_parquet("replay_frames_ext.parquet")
pd.concat(M).to_parquet("replay_1min_ext.parquet")
sp = _fetch_bars(["SPY"], "2026-11-16T13:00:00Z", "2026-11-17T22:00:00Z", "1Min")
sp.to_parquet("spy_ext.parquet"); print("spy", len(sp))
