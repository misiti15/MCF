"""Smoke test for BEG-01 (live class vs the backtest helpers + the walk). Educational only - not financial advice."""
import sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import beg01 as G  # noqa: E402
from mcf.strategies.base import DayContext  # noqa: E402

idx = pd.date_range("2025-06-02 09:30", "2025-06-02 15:59", freq="1min", tz="America/New_York")
n = len(idx)
px = np.full(n, 50.0)
hm = idx.hour * 100 + idx.minute
px[hm < 945] = np.linspace(50, 51, (hm < 945).sum())       # up candle, OR15 50..51
px[(hm >= 945) & (hm < 1000)] = 50.8
px[hm >= 1000] = 51.0 + np.minimum(np.arange((hm >= 1000).sum()) * 0.05, 3)  # breakout then trend
b = pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": 1e5}, index=idx)
b.iloc[0, b.columns.get_loc("open")] = 50.0
ctx = DayContext("TEST", date(2025, 6, 2), b[hm <= 949], 49.0, 50, 48, atr=2.0, avg_dollar_volume=5e7,
                 avg_cum_volume=np.arange(1, 400) * 1e4, rank_rvol20=3)
s = G.M.Beg01ORB15().signals(ctx)
assert len(s) == 1 and s[0].side == 1 and s[0].entry_type == "stop", s
side, trig, stop, tgt = (float(x[0]) for x in G.M.plan_from_stats([50.0], [px[hm <= 944][-1]], [b.high[hm <= 944].max()],
                                                                 [b.low[hm <= 944].min()], [2.0]))
assert (side, trig) == (1, s[0].entry_price) and abs(stop - s[0].stop) < 1e-9 and abs(tgt - s[0].target) < 1e-9
assert abs(trig - 51.03) < 1e-9 and abs(stop - (51.03 - 0.2)) < 1e-9 and abs(tgt - (51.03 + 0.4)) < 1e-9
assert s[0].entry_valid_bars == 100 and s[0].be_at_r == 1.0
# low-rvol / high-rank -> no signal
ctx2 = DayContext("TEST", date(2025, 6, 2), b[hm <= 949], 49.0, 50, 48, atr=2.0, avg_dollar_volume=5e7,
                  avg_cum_volume=np.arange(1, 400) * 1e4, rank_rvol20=25)
assert G.M.Beg01ORB15().signals(ctx2) == []
# walk: target hit
r = G.walk_day(b.open.values, b.high.values, b.low.values, b.close.values, np.asarray(hm), 1, trig, stop, tgt, 1.0, 950, 1130)
assert r["kind"] == 2 and abs(r["px"] - tgt) < 1e-9, r
# far-side cap: tiny OR -> stop at OR low
_, t2, s2, _ = G.M.plan_from_stats([10.0], [10.05], [10.06], [9.99], [5.0])
assert abs(s2[0] - 9.99) < 1e-9
# doji -> side 0; down candle -> short below OR low
sd, *_ = G.M.plan_from_stats([10.0], [10.0], [10.1], [9.9], [1.0]); assert sd[0] == 0
ss, ts, sts, tgs = G.M.plan_from_stats([10.0], [9.95], [10.1], [9.9], [1.0])
assert ss[0] == -1 and abs(ts[0] - 9.89) < 1e-9 and abs(sts[0] - 9.99) < 1e-9 and abs(tgs[0] - 9.69) < 1e-9
print("smoke ok", s[0])
