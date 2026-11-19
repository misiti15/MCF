"""Smoke test: ULT-07 module imports and runs under the live LabStrategy (context spy_fo), fires on an afternoon dip
in a high-ATR name when RSI(5) turns up through 30 with buy pressure, gives t05s1 / 2R-stop levels, honours the SPY
falling-hour guard, and fails safe without SPY context.
    pytest -q research/ultimate_1119/ULT-07-pm-volatile-dip-long/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[1] / "modules" / "ULT-07-pm-volatile-dip-long.py")


def _day(spy_drop=0.0, day="2026-11-18"):
    # 1-minute path: slow up-drift on heavy volume to 13:35 (positive buy pressure), a sharp low-volume slide
    # 13:35-13:55 (RSI5 collapses, > 1 daily ATR below the open), then a steady rebound from 13:55 (RSI5 turns up)
    px, vol = [100.0], [20000.0]
    for k in range(1, 390):
        if k < 245:
            step, v = (0.004, 20000.0)
        elif k < 265:
            step, v = (-0.30, 2000.0)
        else:
            step, v = (0.02, 20000.0)
        px.append(px[-1] + step); vol.append(v)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01,
                         "close": px, "volume": vol}, index=idx)
    spy = 600 * (1 - spy_drop * np.clip((np.arange(390) - 250) / 60, 0, 1))
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def test_module_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

    _LAB_FRAMES.clear()
    bars, peers = _day()
    st = LabStrategy("ULT-07", MOD, window=[1400, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=20_000_000, geom="t05s1")
    sigs = st.signals(_ctx(bars, peers))
    assert len(sigs) == 1
    tz = "America/New_York"
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 13:55", tz=tz) <= t <= pd.Timestamp("2026-11-18 15:00", tz=tz)
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((entry - s.stop) - 1.0) < 1e-6 and abs((s.target - entry) - 0.5) < 1e-6   # t05s1, R = 1
    _LAB_FRAMES.clear()
    sx = LabStrategy("ULT-07X", MOD, window=[1400, 1500], context=["spy_fo"], refire=True, refire_cooldown=0, geom="S")
    x = sx.signals(_ctx(bars, peers))[0]
    assert x.target is None and abs((float(bars["close"].iloc[x.bar_index]) - x.stop) - 2.0) < 1e-6
    # falling hour: SPY -1% over the hour -> blocked (another date: the context columns are cached per session)
    _LAB_FRAMES.clear()
    b2, p2 = _day(spy_drop=0.01, day="2026-11-17")
    assert st.signals(_ctx(b2, p2)) == []
    # fail safe: no SPY context -> no signal
    _LAB_FRAMES.clear()
    assert st.signals(_ctx(bars, None)) == []
