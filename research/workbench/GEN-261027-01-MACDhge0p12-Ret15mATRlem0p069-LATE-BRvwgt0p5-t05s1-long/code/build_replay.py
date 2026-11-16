"""Mechanic GEN-261027-01: lab frames for the live sessions after the 2-year frames end (2026-11-05..11-13), built with the
SAME pipeline as research/history2y/build_frames.py (cache 1-minute + fetched SIP 1-minute -> resample 5min ->
mcf.research.setup_lab.build; adv20 from the daily table), lab universe; context (breadth...) via context_from_frames;
then the candidate rows (cand.cands). 11-03/11-04 are also built for a parity check vs the history2y frames.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT
from mcf.data.bars import resample
from mcf.data.store import BarStore
from mcf.research.setup_lab import build
from build_frames import daily_table
from mcf.strategies.lab_context import context_from_frames
from cand import cands
F = None

def init():
    global F
    F = pd.read_parquet(OUT + "fetch_1m.parquet")
    F["ts"] = pd.DatetimeIndex(F.ts).tz_convert("America/New_York")
    F = {s: g.set_index("ts")[["open", "high", "low", "close", "volume"]].astype(float) for s, g in F.groupby("symbol")}

def one(syms):
    st = BarStore("/home/user/MCF/data/cache_hist"); out = []
    for s in syms:
        a = st.load(s, start="2026-06-01")
        a = a[["open", "high", "low", "close", "volume"]].astype(float) if len(a) else a
        b = F.get(s)
        if b is not None:
            b = b[(b.index.time >= pd.Timestamp("09:30").time()) & (b.index.time < pd.Timestamp("16:00").time())]
            a = pd.concat([a[a.index < pd.Timestamp("2026-11-05", tz=a.index.tz)] if len(a) else a, b])
        if a.empty: continue
        a = a[~a.index.duplicated()].sort_index()
        dd = daily_table(a, s)
        x = build({s: resample(a, "5min")}, log=lambda *_: None)
        if x is None or not len(x): continue
        x = x.reset_index(names="ts").merge(dd[["date", "adv20"]], on="date", how="left")
        x["date"] = x.date.astype(str)
        out.append(x[x.date >= "2026-11-03"])
    return pd.concat(out, ignore_index=True) if out else None

if __name__ == "__main__":
    syms = open("/home/user/MCF/research/lab_symbols.txt").read().split()
    ch = [syms[i::12] for i in range(12)]
    with Pool(3, initializer=init) as p:
        parts = [x for x in p.map(one, ch) if x is not None]
    fr = pd.concat(parts, ignore_index=True)
    fr.to_parquet(OUT + "replay_frames_new.parquet")
    ctx = context_from_frames(fr[["symbol", "date", "tod", "fromOpen", "vwapDistPct"]]); ctx["date"] = ctx.date.astype(str)
    ctx.to_parquet(OUT + "replay_ctx_new.parquet")
    r = cands(fr, ctx); r.to_parquet(OUT + "cand_replay_new.parquet")
    print(len(fr), fr.date.min(), fr.date.max(), len(r))
