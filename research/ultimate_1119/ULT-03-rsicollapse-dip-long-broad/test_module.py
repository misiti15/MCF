"""Smoke test: ULT-03 module imports and runs under the live LabStrategy (context spy_fo), fires on an RSI collapse
with buy pressure inside its window, gives t1s1 / 2R-stop levels, honours the SPY falling-hour guard, and fails safe
without SPY context.
    pytest -q research/ultimate_1119/ULT-03-rsicollapse-dip-long-broad/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[1] / "modules" / "ULT-03-rsicollapse-dip-long-broad.py")


def _day(spy_slope=0.0):
    # 1-minute path: drift up to ~11:00 (RSI14 > 50), then a sharp slide (RSI collapses, > 1% below the open),
    # each 5-min bucket closing near its high late in the slide (buy pressure)
    px = [100.0]
    for k in range(1, 390):
        if k < 90:
            step = 0.01 if k % 3 else -0.005
        elif k < 105:
            step = -0.35 if k % 5 != 4 else 0.10
        else:
            step = 0.0
        px.append(px[-1] + step)
    px = np.array(px)
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": px, "high": px + 0.03, "low": px - 0.03, "close": px, "volume": 20000.0}, index=idx)
    spy = 600 * (1 + spy_slope * np.arange(390))
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def test_module_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

    _LAB_FRAMES.clear()
    bars, peers = _day()
    st = LabStrategy("ULT-03", MOD, window=[1015, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=20_000_000, geom="t1s1")
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2
    times = [bars.index[s.bar_index] for s in sigs]
    tz = "America/New_York"
    assert all(pd.Timestamp("2026-11-18 10:10", tz=tz) <= t <= pd.Timestamp("2026-11-18 15:00", tz=tz) for t in times)
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((entry - s.stop) - 1.0) < 1e-6 and abs((s.target - entry) - 1.0) < 1e-6   # t1s1, R = 1
    # EXIT "X": geom S -> 2R catastrophic stop below, no target
    _LAB_FRAMES.clear()
    sx = LabStrategy("ULT-03X", MOD, window=[1015, 1500], context=["spy_fo"], refire=True, refire_cooldown=0, geom="S")
    x = sx.signals(_ctx(bars, peers))[0]
    assert x.target is None and abs((float(bars["close"].iloc[x.bar_index]) - x.stop) - 2.0) < 1e-6
    # fail safe: no SPY context -> no signal
    _LAB_FRAMES.clear()
    assert st.signals(_ctx(bars, None)) == []


def test_spy_guard_blocks_falling_hour():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ult03", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    tod = np.array([1000, 1005, 1010, 1015, 1020, 1025, 1030])
    df = pd.DataFrame({"tod": tod, "spy_fo": [0.0, -0.1, -0.2, -0.3, -0.4, -0.45, -0.5]})
    g = m.spy_gate(df)
    assert not g[:6].any()           # first 6 rows: no 30-min history -> blocked (fail safe)
    assert not g[6]                  # SPY -0.5% from open and falling over 30 min -> blocked
    df2 = df.assign(spy_fo=[-1.0, -0.9, -0.8, -0.7, -0.6, -0.55, -0.5])
    assert m.spy_gate(df2)[6]        # in the band but rising -> allowed
    df3 = df.assign(spy_fo=[0.5, 0.4, 0.3, 0.2, 0.1, 0.0, -0.1])
    assert m.spy_gate(df3)[6]        # falling but outside the band -> allowed
