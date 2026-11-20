"""Smoke test for BEG-03 (live class vs the backtest helpers vs mcf.backtest.engine.simulate).
Educational only - not financial advice."""
import sys
from datetime import date, time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import beg03 as G  # noqa: E402
from mcf.backtest.engine import simulate  # noqa: E402
from mcf.strategies.base import DayContext  # noqa: E402

idx = pd.date_range("2025-06-02 09:30", "2025-06-02 15:59", freq="1min", tz="America/New_York")
hm = np.asarray(idx.hour * 100 + idx.minute)
px = np.full(len(idx), 52.0)
px[hm < 950] = np.linspace(52.0, 53.0, (hm < 950).sum())          # gap day (prev close 50 -> open 52 = +4%)
px[(hm >= 950) & (hm < 1010)] = 52.9                                  # pause above VWAP
m = hm >= 1010
px[m] = 52.9 + np.minimum(np.arange(m.sum()) * 0.03, 4.0)             # breakout and trend
b = pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": 2e5}, index=idx)
vol_avg = np.arange(1, 400) * 1e4                                      # 20-min avg = 2e5 -> rvol = 20*2e5/2e5 = 20
O, H, L, C, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))

e = G.find_entry(O, H, L, C, V, hm)
assert e is not None, "no entry"
r20hi = H[hm <= 949].max()
assert abs(e["trig"] - round(r20hi + 0.01, 2)) < 1e-9 and hm[e["j"]] >= 1010, e
vw = G.vwap(H, L, C, V)
assert abs(e["stop"] - (max(L[hm <= 949].min(), vw[e["j"] - 1]) - 0.02)) < 1e-9
assert abs(e["tgt"] - (e["trig"] + 2 * (e["trig"] - e["stop"]))) < 1e-9

# live class: called with bars through j-1 it arms the same order for bar j
ctx = DayContext("TEST", date(2025, 6, 2), b.iloc[: e["j"]], 50.0, 51, 49, atr=2.0, avg_dollar_volume=5e7,
                 avg_cum_volume=vol_avg)
s = G.Beg03GapAndGo().signals(ctx)
assert len(s) == 1 and s[0].entry_type == "stop" and s[0].entry_valid_bars == 1, s
assert abs(s[0].entry_price - e["trig"]) < 1e-9 and abs(s[0].stop - e["stop"]) < 1e-9 and abs(s[0].target - e["tgt"]) < 1e-9
assert s[0].exit_by == time(12, 0) and s[0].trail_r == 1.0
# small gap -> no signal; low rvol -> no signal
assert G.Beg03GapAndGo().signals(DayContext("TEST", date(2025, 6, 2), b.iloc[: e["j"]], 51.0, 51, 49, atr=2.0,
                                            avg_dollar_volume=5e7, avg_cum_volume=vol_avg)) == []
assert G.Beg03GapAndGo().signals(DayContext("TEST", date(2025, 6, 2), b.iloc[: e["j"]], 50.0, 51, 49, atr=2.0,
                                            avg_dollar_volume=5e7, avg_cum_volume=vol_avg * 10)) == []

# walk vs engine.simulate (zero costs): same fill, same exit price and reason
w = G.walk(O, H, L, C, hm, e["j"], e["fill"], e["stop"], e["tgt"])
tr = simulate(s[0], b, time(15, 55), 0.0)
assert tr is not None and abs(tr.entry - e["fill"]) < 1e-9, (tr, e)
assert abs(tr.exit - w[0]) < 1e-6 and tr.exit_reason in {0: ("time",), 1: ("stop", "trail"), 2: ("target",)}[w[1]], (tr, w)

# stop-band skip: a huge R20 range (> 3%) never arms
H2 = H.copy(); L2 = L.copy(); L2[5] = 45.0
assert G.find_entry(O, H2, L2, C, V, hm) is None or G.find_entry(O, H2, L2, C, V, hm)["stop"] > 46

# trail: after +1R the stop follows 1R behind the best price -> a pullback exits as a stop above entry (gap-through at the open)
H3, L3, C3, O3 = H.copy(), L.copy(), C.copy(), O.copy()
j = e["j"]; R = e["fill"] - e["stop"]
peak = e["fill"] + 1.5 * R
H3[j + 2] = peak; L3[j + 3] = e["fill"] - 0.5 * R; O3[j + 3] = e["fill"] + 0.2 * R
w3 = G.walk(O3, H3, L3, C3, hm, j, e["fill"], e["stop"], e["tgt"])
assert w3[1] == 1 and abs(w3[0] - O3[j + 3]) < 1e-6, w3   # trail at +0.5R, bar opens below it -> fills at the open
print("smoke ok", e, w, tr.exit_reason)
