"""Fetch 1-min + daily SIP bars for every live L3-fromopen ETB symbol-day (10-12..11-13), build lab frames. Read-only GET."""
import sys, pandas as pd, numpy as np
from datetime import timedelta
from mcf.replay.store import _fetch_bars
from mcf.report import engine as E
W = sys.argv[1]
s = pd.read_parquet(f"{W}/signals.parquet")
s = s[(s.day <= "2026-11-13") & ~s.reason.fillna("").str.contains("shortable")]
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
pd.concat(F).to_parquet(f"{W}/replay_frames.parquet")
pd.concat(M).to_parquet(f"{W}/replay_1min.parquet")
