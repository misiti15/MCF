"""Smoke test: ULT-08 module imports and runs under the live LabStrategy (context spy_fo, geom S), fires short on an
extended name whose RSI(5) rolls over from an overbought print in 14:00-15:00 while SPY is falling, and gives no signal
without SPY context, on a rising tape or on a gap-up day.
    pytest -q research/ultimate_1119/ULT-08-pm-overbought-rollover-short/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[1] / "modules" / "ULT-08-pm-overbought-rollover-short.py")


def _day(spy_slope=-0.002, open_px=100.0):
    # 5-minute closes: flat until bar 39, a steady climb (+0.7/bar, RSI(5) = 100) to ~+2.5 daily ATR by the 14:00 bar,
    # then a roll-over (-0.3/bar) - the first lower RSI(5) print falls inside the 14:00-15:00 window
    c5 = [open_px]
    for k in range(1, 78):
        c5.append(c5[-1] + (0.7 if 40 <= k <= 54 else (-0.3 if k > 54 else 0.0)))
    px = np.interp(np.arange(390) / 5.0, np.arange(78), c5)
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": px, "high": px + 0.03, "low": px - 0.02, "close": px, "volume": 20000.0}, index=idx)
    spy = 600 + spy_slope * np.arange(390) * 600 / 100
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _clear():
    from mcf.strategies import lab_context
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear(); lab_context._CACHE.clear()


def test_module_runs_under_live_lab_strategy():
    from mcf.strategies.setups import LabStrategy

    tz = "America/New_York"
    mk = lambda: LabStrategy("ULT-08", MOD, window=[1400, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                             min_adv=20_000_000, geom="S")
    _clear()
    bars, peers = _day()
    st = mk()
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 13:55", tz=tz) <= t <= pd.Timestamp("2026-11-18 15:00", tz=tz) for t in times)
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == -1 and s.target is None and abs((s.stop - entry) - 2.0) < 1e-6      # 2R catastrophic, R = 1
    # fail safe: no SPY context, rising tape, gap-up day -> no signal
    _clear()
    assert mk().signals(_ctx(bars, None)) == []
    _clear()
    ub, up = _day(spy_slope=+0.002)
    assert mk().signals(_ctx(ub, up)) == []
    _clear()
    gb, gp = _day(open_px=101.0)          # +1% gap
    assert mk().signals(_ctx(gb, gp)) == []
