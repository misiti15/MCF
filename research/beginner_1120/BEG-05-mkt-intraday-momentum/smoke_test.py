"""Smoke test for beg05.py (synthetic up day + mirror down day + the live Strategy interface).
Educational only - not financial advice."""
import sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import beg05 as G
from mcf.strategies.base import DayContext
from mcf.backtest.engine import simulate, Costs


def synth(sign=1):
    idx = pd.date_range("2025-06-02 09:30", "2025-06-02 15:59", freq="1min", tz="America/New_York")
    n = len(idx)
    c = 500 + sign * np.linspace(1.0, 8.0, n)          # opens +0.2%, +~0.5% by 10:00, keeps trending (above VWAP)
    o = np.r_[c[0], c[:-1]]
    h, l = np.maximum(o, c) + 0.05, np.minimum(o, c) - 0.05
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": np.full(n, 1e5)}, index=idx)


def run(sign):
    b = synth(sign)
    hh = (b.index.hour * 100 + b.index.minute).to_numpy()
    a = [b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")]
    sig = G.find_signal(*a, hh, 500.0, 6.0)
    assert sig is not None and sig["side"] == sign and hh[sig["k"]] == 1529, sig
    assert abs(sig["dist"] - 0.9) < 1e-9
    w = G.walk(*a[:4], hh, sig)
    assert w is not None and hh[w[0]] == 1530 and w[4] == 0 and w[5] == 1555, w
    # no trade when r1 is inside the band
    assert G.find_signal(*a, hh, a[3][29] / 1.001, 6.0) is None
    ctx = DayContext(symbol="SPY", date=date(2025, 6, 2), bars=b, prev_close=500.0, prev_high=501, prev_low=499,
                     atr=6.0, avg_dollar_volume=5e10)
    st = G.BEG05()
    assert st.eligible(ctx) and not st.eligible(DayContext(symbol="SQQQ", date=ctx.date, bars=b, prev_close=1,
                                                         prev_high=1, prev_low=1, atr=1, avg_dollar_volume=1))
    sigs = st.signals(ctx)
    assert len(sigs) == 1 and sigs[0].side == sign and sigs[0].target is None
    assert st.signals(DayContext(symbol="SPY", date=ctx.date, bars=b.iloc[:300], prev_close=500.0, prev_high=501,
                                 prev_low=499, atr=6.0, avg_dollar_volume=5e10)) == []   # before 15:29: nothing
    tr = simulate(sigs[0], b, pd.Timestamp("15:55").time(), Costs(bps=0, per_share=0, stop_extra_per_share=0))
    assert tr is not None
    print("ok", sign, sig, w[4:], tr.exit_reason, round(tr.r_multiple, 3))


if __name__ == "__main__":
    run(1)
    run(-1)
