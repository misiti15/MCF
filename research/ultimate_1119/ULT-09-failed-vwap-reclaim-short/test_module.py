"""Smoke test: ULT-09 module imports and runs under the live LabStrategy (context spy_fo), fires on a weak name that
pokes back above VWAP and fails inside its window while SPY is not rising since 09:50, and fails safe without SPY
context or on a rising tape.
    pytest -q research/ultimate_1119/ULT-09-failed-vwap-reclaim-short/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[1] / "modules" / "ULT-09-failed-vwap-reclaim-short.py")


def _day(spy_slope=-0.004):
    # 5-minute closes: light-volume run 100 -> 110 (bars 1-10), slide to 92 (bars 11-20; heavy volume on bars 16-23 sinks VWAP to
    # the mid 90s), a 3-bar poke back above VWAP (93, 95, 96.5), then a failure back below VWAP (93.5) while still
    # far below the 5-min SMA20 and below the open; then a slow drift lower
    c5 = [100.0] + [100 + k for k in range(1, 11)] + [110 - 1.8 * k for k in range(1, 11)] + [93.0, 95.0, 96.5, 93.5]
    while len(c5) < 78:
        c5.append(c5[-1] - 0.05)
    v5 = [5000.0] * 16 + [200000.0] * 8 + [20000.0] * 54
    px = np.interp(np.arange(390) / 5.0, np.arange(78), c5)
    vol = np.repeat(v5, 5)[:390]
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": vol}, index=idx)
    spy = 600 + spy_slope * np.arange(390) * 600 / 100
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def test_module_runs_under_live_lab_strategy():
    from mcf.strategies import lab_context
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

    tz = "America/New_York"
    _LAB_FRAMES.clear(); lab_context._CACHE.clear()
    bars, peers = _day()
    st = LabStrategy("ULT-09", MOD, window=[1030, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=20_000_000)      # module default EXIT "T" -> t1s1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 10:25", tz=tz) <= t <= pd.Timestamp("2026-11-18 15:00", tz=tz) for t in times)
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert entry < 100.0                                                         # below the open
    assert s.side == -1 and abs((s.stop - entry) - 1.0) < 1e-6 and abs((entry - s.target) - 1.0) < 1e-6   # t1s1, R = 1
    # geom S (the TX45 variant): 2R catastrophic stop, no target
    _LAB_FRAMES.clear()
    sx = LabStrategy("ULT-09X", MOD, window=[1030, 1500], context=["spy_fo"], refire=True, refire_cooldown=0, geom="S")
    x = sx.signals(_ctx(bars, peers))[0]
    assert x.target is None and abs((x.stop - float(bars["close"].iloc[x.bar_index])) - 2.0) < 1e-6
    # fail safe: no SPY context -> no signal; rising tape -> no signal
    _LAB_FRAMES.clear()
    assert st.signals(_ctx(bars, None)) == []
    _LAB_FRAMES.clear(); lab_context._CACHE.clear()
    up_bars, up_peers = _day(spy_slope=+0.004)
    assert st.signals(_ctx(up_bars, up_peers)) == []
