"""Mechanic GEN-261027-01: sensor values for the 8 live trades whose symbols are outside the lab universe (read-only SIP
GET, same frame pipeline as build_replay.py; breadth from the lab-universe context). Educational only - not financial advice."""
import pandas as pd, numpy as np
from common import OUT, IND
from mcf.replay.store import _fetch_bars
from mcf.data.bars import resample
from mcf.research.setup_lab import build
from build_frames import daily_table
from mcf.research.arena.indicators import compute
L = pd.read_csv(OUT + "live.csv"); syms = set(open("/home/user/MCF/research/lab_symbols.txt").read().split())
off = L[~L.symbol.isin(syms)]
m = _fetch_bars(sorted(off.symbol.unique()), "2026-08-01T13:00:00Z", "2026-11-13T21:05:00Z", "1Min")
m["ts"] = pd.DatetimeIndex(m.ts).tz_convert("America/New_York")
rows = []
for s, g in m.groupby("symbol"):
    a = g.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float).sort_index()
    a = a[(a.index.time >= pd.Timestamp("09:30").time()) & (a.index.time < pd.Timestamp("16:00").time())]
    dd = daily_table(a, s)
    x = build({s: resample(a, "5min")}, log=lambda *_: None).reset_index(names="ts").merge(dd[["date", "adv20"]], on="date", how="left")
    x["date"] = x.date.astype(str)
    x = x[x.date.isin(off[off.symbol == s].date)]
    x = x.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    y = pd.concat([x[["symbol", "date", "tod", "close", "atr_d", "adv20"]], compute(x, names=IND, context=False)], axis=1)
    rows.append(y)
y = pd.concat(rows)
ctx = pd.concat([pd.read_parquet(OUT + "replay_ctx_new.parquet")] + [pd.read_parquet(f"/home/user/MCF/research/history2y/data/context/month=2026-10.parquet")])
ctx["date"] = ctx.date.astype(str)
y = y.merge(ctx[["date", "tod", "breadth"]].drop_duplicates(["date", "tod"]), on=["date", "tod"], how="left")
y.to_parquet(OUT + "live_off_frames.parquet"); print(len(y))
