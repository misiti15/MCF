"""Deploy-time duplicate check for BEG-ORB / BEG-GNG (2026-11-20). Inputs (trade lists, day tables) are session-scratchpad
files, not in git; output overlap.json is. Educational only - not financial advice.
Check the ported live classes reproduce the research trades (side, trigger, stop, target, fill bar) on sampled rows."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
ROOT = S / "beg_deploy"
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research/ultimate_1119/top10"))
import bench10 as B
from mcf.strategies.base import DayContext
from mcf.strategies.beginner_setups import BegORB15, BegGapAndGo
from mcf.backtest.engine import simulate
from datetime import time

def day_bars(sym, d):
    b = B.hist_bars(sym)
    b = b[b.index.date.astype(str) == d]
    hm = b.index.hour * 100 + b.index.minute
    return b[(hm >= 930) & (hm < 1600)]

def run(strat, rows, prev=None):
    ok = bad = miss = 0; ex = []
    for _, r in rows.iterrows():
        b = day_bars(r.symbol, r.date)
        ctx = DayContext(symbol=r.symbol, date=pd.Timestamp(r.date).date(), bars=b,
                         prev_close=float(r.prev_close) if prev else 50.0, prev_high=0, prev_low=0, atr=float(r.atr),
                         avg_dollar_volume=1e12, avg_cum_volume=np.full(400, 1.0), rank_rvol20=1)
        sig = strat.signals(ctx)
        if not sig:
            miss += 1; ex.append((r.symbol, r.date, "no signal")); continue
        s = sig[0]
        t = simulate(s, b, time(15, 55), 0.0)
        fill_hm = None if t is None else None
        same = (s.side == r.side and abs(s.stop - r.stop) < 0.006 and abs(s.target - r.tgt) < 0.011)
        if prev:   # BEG-03: fill bar = tod
            hm = b.index.hour * 100 + b.index.minute
            same = same and int(hm[s.bar_index + 1]) == int(r.tod)
        ok += same; bad += (not same)
        if not same: ex.append((r.symbol, r.date, s.side, s.stop, s.target, r.side, r.stop, r.tgt))
    return ok, bad, miss, ex[:8]

b1 = pd.read_parquet(S / "beg01w/booked_t1_stopOR_check.parquet").sample(120, random_state=1)
print("BEG-01 stopOR", run(BegORB15(scale_out_r=None), b1))
b3 = pd.read_parquet(S / "beg03w/bk_base_all.parquet"); b3 = b3[b3.test.str.lower() == "t1"].sample(120, random_state=1)
print("BEG-03 base", run(BegGapAndGo(scale_out_r=None), b3, prev=True))
