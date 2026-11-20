"""Smoke test for BEG-09 (live class vs the backtest helpers vs mcf.backtest.engine.simulate).
Educational only - not financial advice."""
import sys
from datetime import date, time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import beg09 as G  # noqa: E402
from mcf.backtest.engine import simulate  # noqa: E402
from mcf.strategies.base import DayContext  # noqa: E402

idx = pd.date_range("2025-06-02 09:30", "2025-06-02 15:59", freq="1min", tz="America/New_York")
hm = np.asarray(idx.hour * 100 + idx.minute)
px = np.empty(len(idx))
px[hm < 1100] = np.linspace(50.0, 53.0, (hm < 1100).sum())      # trend up from prev close 50 (+6%)
px[(hm >= 1100) & (hm < 1130)] = 52.6                            # pull back below the high of 53.02
px[(hm >= 1130) & (hm < 1300)] = 52.7                            # tight midday range above VWAP
m = hm >= 1300
px[m] = 52.7 + np.minimum(np.arange(m.sum()) * 0.02, 3.0)        # breaks the HOD and trends
b = pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": 1e5}, index=idx)
O, H, L, C, V = (b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
ATR = 2.0

e = G.find_entry(O, H, L, C, V, hm, 50.0, ATR)
assert e is not None and e["side"] == 1, "no entry"
assert hm[e["k_arm"]] == 1159, hm[e["k_arm"]]                    # first 30-bar window 11:30..11:59
assert abs(e["trig"] - (H[: e["k_arm"] + 1].max() + 0.01)) < 1e-9 and abs(e["trig"] - 53.03) < 1e-9
assert abs(e["stop"] - (52.68 - 0.02)) < 1e-9
assert abs(e["tgt"] - (e["trig"] + 2 * (e["trig"] - e["stop"]))) < 1e-9
assert hm[e["j"]] > 1300

# live class: emits exactly once, on the bar that completes the window
ctx = lambda n, pc=50.0, rk=5: DayContext("TEST", date(2025, 6, 2), b.iloc[:n], pc, 51, 49, atr=ATR,
                                         avg_dollar_volume=5e7, rank_rvol20=rk)
s = G.Beg09MiddayRangeBreak().signals(ctx(e["k_arm"] + 1))
assert len(s) == 1 and s[0].entry_type == "stop" and s[0].side == 1, s
assert abs(s[0].entry_price - e["trig"]) < 1e-9 and abs(s[0].stop - e["stop"]) < 1e-9
assert abs(s[0].target - e["tgt"]) < 1e-9 and s[0].exit_by == time(15, 55)
assert s[0].entry_valid_bars == 180                              # 11:59 -> 14:59
assert G.Beg09MiddayRangeBreak().signals(ctx(e["k_arm"])) == []
assert G.Beg09MiddayRangeBreak().signals(ctx(e["k_arm"] + 2)) == []
assert not G.Beg09MiddayRangeBreak().eligible(ctx(e["k_arm"] + 1, rk=31))
assert G.Beg09MiddayRangeBreak().signals(ctx(e["k_arm"] + 1, pc=52.0)) == []   # day return +1.3% -> none

# walk vs engine.simulate (zero costs): same fill, same exit price and reason
w = G.walk(O, H, L, C, hm, e["j"], e["fill"], e["side"], e["stop"], e["tgt"])
tr = simulate(s[0], b, time(15, 55), 0.0)
assert tr is not None and abs(tr.entry - e["fill"]) < 1e-9, (tr, e)
assert abs(tr.exit - w[0]) < 1e-6 and tr.exit_reason in {0: ("time",), 1: ("stop",), 2: ("target",)}[w[1]], (tr, w)

# short mirror
bs = b.copy()
bs[["open", "close"]] = 100 - b[["open", "close"]].to_numpy()
bs["high"], bs["low"] = 100 - b["low"], 100 - b["high"]
O2, H2, L2, C2 = (bs[k].to_numpy(float) for k in ("open", "high", "low", "close"))
e2 = G.find_entry(O2, H2, L2, C2, V, hm, 50.0, ATR)
assert e2 is not None and e2["side"] == -1 and abs(e2["trig"] - (L2[: e2["k_arm"] + 1].min() - 0.01)) < 1e-9
assert abs(e2["stop"] - (H2[(hm >= 1130) & (hm <= 1159)].max() + 0.02)) < 1e-9

# a range wider than 0.35 ATR -> no window
assert G.find_entry(O, H, L, C, V, hm, 50.0, 0.1) is None
# a close below VWAP inside every candidate window -> no long
C3 = C.copy(); C3[(hm >= 1130) & (hm <= 1429) & (hm % 20 == 0)] = 40.0
assert G.find_entry(O, H, L, C3, V, hm, 50.0, ATR) is None
print("BEG-09 smoke test OK")
