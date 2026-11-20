"""Smoke test for beg02.py (synthetic trend day + the live Strategy interface). Educational only - not financial advice."""
import sys
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import beg02 as G
from mcf.strategies.base import DayContext
from mcf.backtest.engine import simulate, Costs


def synth():
    idx = pd.date_range("2025-06-02 09:30", "2025-06-02 15:59", freq="1min", tz="America/New_York")
    n = len(idx)
    c = np.empty(n)
    c[:20] = np.linspace(102, 105, 20)               # up-trend to 09:49 (+5% vs prev close 100)
    c[20:30] = np.linspace(105, 103.2, 10)           # pull back toward VWAP
    c[30:] = np.linspace(103.4, 110, n - 30)
    o = np.r_[c[0], c[:-1]]
    h, l = np.maximum(o, c) + 0.05, np.minimum(o, c) - 0.05
    v = np.r_[np.full(20, 50000.0), np.full(n - 20, 5000.0)]
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}, index=idx)


def test_signal():
    b = synth()
    hh = (b.index.hour * 100 + b.index.minute).to_numpy()
    a = [b[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")]
    vw = G.vwap(*a[1:])
    side, mv = G.setup_side(hh, a[3], vw, 100.0)
    assert side == 1 and mv > 2
    sig = G.find_signal(*a, hh, 100.0, 2.0)
    assert sig is not None and sig["side"] == 1 and hh[sig["k"]] >= 950, sig
    assert sig["ref"] - sig["stop"] >= 0.15 * 2.0 - 1e-9
    assert 1.5 <= sig["tgt_r"] <= 2.0
    w = G.walk(*[a[i] for i in range(4)], hh, sig)
    assert w is not None and w[3] in (0, 1, 2)
    # mirror: short side
    bs = b.copy()
    for k in ("open", "high", "low", "close"):
        bs[k] = 200 - b[k]
    bs["high"], bs["low"] = bs["low"].copy(), bs["high"].copy()
    a2 = [bs[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume")]
    s2 = G.find_signal(*a2, hh, 100.0 * (200 / 100 - 1) * 1.0 + 100.0 * 0 + (200 - 100), 2.0)
    assert s2 is None or s2["side"] == -1
    # live interface
    ctx = DayContext(symbol="TEST", date=date(2025, 6, 2), bars=b, prev_close=100.0, prev_high=101, prev_low=99,
                     atr=2.0, avg_dollar_volume=50e6, rank_rvol20=3)
    st = G.BEG02()
    assert st.eligible(ctx)
    sigs = st.signals(ctx)
    assert len(sigs) == 1 and sigs[0].side == 1 and sigs[0].time_stop_min == 60
    tr = simulate(sigs[0], b, pd.Timestamp("15:55").time(), Costs(bps=0, per_share=0, stop_extra_per_share=0))
    assert tr is not None
    print("ok", sig, w, tr.exit_reason, round(tr.r_multiple, 3))


if __name__ == "__main__":
    test_signal()
