"""Smoke test for BEG-10 (live class vs the backtest helpers vs mcf.backtest.engine.simulate).
Educational only - not financial advice."""
import sys
from datetime import date, time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import beg10 as G  # noqa: E402
from mcf.backtest.engine import simulate  # noqa: E402
from mcf.strategies.base import DayContext  # noqa: E402

idx = pd.date_range("2025-06-02 09:30", "2025-06-02 15:59", freq="1min", tz="America/New_York")
hm = np.asarray(idx.hour * 100 + idx.minute)
px = np.full(len(idx), 50.0)
px[hm < 1000] = 50.0 + 0.4 * np.sin(np.arange((hm < 1000).sum()))      # OR30 ~ 49.6..50.4 (+-0.02 wicks)
m = hm >= 1030
px[m] = 50.0 + np.minimum(np.arange(m.sum()) * 0.01, 2.5)              # breaks up at ~10:70 and trends
b = pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": 1e5}, index=idx)
O, H, L, C = (b[k].to_numpy(float) for k in ("open", "high", "low", "close"))
ATR = 2.0
orh, orl = H[hm < 1000].max(), L[hm < 1000].min()

assert G.nr_day(51.0, 50.0, ATR) and not G.nr_day(52.0, 50.0, ATR)      # 1.0 <= 1.2 ; 2.0 > 1.2
e = G.find_entry(O, H, L, hm, ATR)
assert e is not None and e["side"] == 1, e
assert abs(e["trig"] - (orh + 0.01)) < 1e-9 and abs(e["stop"] - (orh + orl) / 2) < 1e-9
assert abs(e["tgt"] - (e["trig"] + 2 * (e["trig"] - e["stop"]))) < 1e-9
assert 1000 <= hm[e["j"]] <= 1229 and hm[e["k_or"]] == 959

# live class: emits two OCO legs once, on the 09:59 bar close, valid 150 bars (10:00..12:29)
ctx = lambda n, ph=51.0, pl=50.0, pc=50.5, adv=5e7: DayContext("TEST", date(2025, 6, 2), b.iloc[:n], pc, ph, pl,
                                                               atr=ATR, avg_dollar_volume=adv)
k = int(np.flatnonzero(hm == 959)[0]) + 1
st = G.Beg10NrDayOrb30()
s = st.signals(ctx(k))
assert len(s) == 2 and {x.side for x in s} == {1, -1} and all(x.entry_type == "stop" for x in s), s
lg = [x for x in s if x.side == 1][0]
sh = [x for x in s if x.side == -1][0]
assert abs(lg.entry_price - e["trig"]) < 1e-9 and abs(lg.stop - e["stop"]) < 1e-9 and abs(lg.target - e["tgt"]) < 1e-9
assert abs(sh.entry_price - (orl - 0.01)) < 1e-9 and abs(sh.stop - (orh + orl) / 2) < 1e-9
assert lg.entry_valid_bars == 150 and lg.exit_by == time(15, 55) and lg.meta["oco"] == sh.meta["oco"]
assert st.signals(ctx(k - 1)) == [] and st.signals(ctx(k + 1)) == []
assert st.eligible(ctx(k)) and not st.eligible(ctx(k, ph=52.0)) and not st.eligible(ctx(k, adv=2e7))
assert not st.eligible(ctx(k, pc=9.0))

# walk vs engine.simulate (zero costs): same fill, same exit price and reason
w = G.walk(O, H, L, C, hm, e["j"], e["fill"], e["side"], e["stop"], e["tgt"])
tr = simulate(lg, b, time(15, 55), 0.0)
assert tr is not None and abs(tr.entry - e["fill"]) < 1e-9, (tr, e)
assert abs(tr.exit - w[0]) < 1e-6 and tr.exit_reason in {0: ("time",), 1: ("stop",), 2: ("target",)}[w[1]], (tr, w)

# short mirror; and a non-ETB name places only the buy-stop
bs = b.copy()
bs[["open", "close"]] = 100 - b[["open", "close"]].to_numpy()
bs["high"], bs["low"] = 100 - b["low"], 100 - b["high"]
O2, H2, L2, C2 = (bs[k_].to_numpy(float) for k_ in ("open", "high", "low", "close"))
e2 = G.find_entry(O2, H2, L2, hm, ATR)
assert e2 is not None and e2["side"] == -1 and abs(e2["trig"] - (L2[hm < 1000].min() - 0.01)) < 1e-9
assert G.find_entry(O2, H2, L2, hm, ATR, etb=False) is None                 # never goes above OR30 high

# OR30 wider than 0.8 ATR -> no trade
assert G.find_entry(O, H, L, hm, 1.0) is None
# a break only after 12:29 -> no trade
H3 = H.copy(); H3[(hm >= 1000)] = np.minimum(H3[(hm >= 1000)], orh); H3[hm == 1230] = orh + 1
assert G.find_entry(O, H3, np.maximum(L, orl), hm, ATR) is None
print("BEG-10 smoke test OK")
