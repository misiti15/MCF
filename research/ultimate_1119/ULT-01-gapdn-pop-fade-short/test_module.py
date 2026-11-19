"""Smoke test: ULT-01 module imports and runs under the live LabStrategy (context spy_fo), fires on a gap-down pop
inside its window, honours the refire thinning, and fails safe without SPY context.
    pytest -q research/ultimate_1119/ULT-01-gapdn-pop-fade-short/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[1] / "modules" / "ULT-01-gapdn-pop-fade-short.py")


def _day():
    # 5-minute closes: open 97 after a 100 close (gap -3%), slide to ~93.6 by 10:45, then a choppy pop back up
    c5 = [97.0]
    for k in range(1, 78):
        if k <= 15:
            step = -0.25 if k % 3 else 0.10
        elif k <= 30:
            step = 0.60 if k % 3 else -0.30
        else:
            step = 0.02 if k % 2 else -0.02
        c5.append(c5[-1] + step)
    px = np.interp(np.arange(390) / 5.0, np.arange(78), c5)
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": 20000.0}, index=idx)
    spy = 600 + 0.0 * np.arange(390) - 0.001 * np.arange(390)
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def test_module_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

    _LAB_FRAMES.clear()
    bars, peers = _day()
    st = LabStrategy("ULT-01", MOD, window=[1100, 1300], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=20_000_000, geom="t1s1")   # EXIT "T" variant
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 10:55", tz="America/New_York") <= t <= pd.Timestamp("2026-11-18 13:00", tz="America/New_York") for t in times)
    if len(sigs) == 2:
        assert (times[1] - times[0]) >= pd.Timedelta(minutes=75)
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == -1 and abs((s.stop - entry) - 1.0) < 1e-6 and abs((entry - s.target) - 1.0) < 1e-6   # t1s1, R = 1
    # EXIT "X" (the module default, fit-selected 01f): geom S -> 2R catastrophic stop, no target
    _LAB_FRAMES.clear()
    sx = LabStrategy("ULT-01X", MOD, window=[1100, 1300], context=["spy_fo"], refire=True, refire_cooldown=0)
    assert sx.geom == "S"
    x = sx.signals(_ctx(bars, peers))[0]
    assert x.target is None and abs((x.stop - float(bars["close"].iloc[x.bar_index])) - 2.0) < 1e-6
    # fail safe: no SPY context -> no signal
    _LAB_FRAMES.clear()
    assert st.signals(_ctx(bars, None)) == []
