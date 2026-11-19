"""Smoke test: ULT-04 module imports and runs under the live LabStrategy (context spy_fo), fires on a weak name's
overbought pop inside its window while SPY is down from its open and falling, and fails safe without SPY context
or on a rising tape.
    pytest -q research/ultimate_1119/ULT-04-downtape-pop-fade-short/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[1] / "modules" / "ULT-04-downtape-pop-fade-short.py")


def _day(spy_slope=-0.004):
    # 5-minute closes: open 100 (flat vs prior close), a steep slide to 64 by ~11:35, then a choppy 5-bar pop
    # (+0.4, +0.4, -0.3, +0.4, +0.4 -> simple RSI(5) ~84, still far below the 5-min SMA20), then a slow drift lower
    pop = {25: 0.4, 26: 0.4, 27: -0.3, 28: 0.4, 29: 0.4}
    c5 = [100.0]
    for k in range(1, 78):
        c5.append(c5[-1] + (-1.5 if k <= 24 else pop.get(k, -0.05)))
    px = np.interp(np.arange(390) / 5.0, np.arange(78), c5)
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": 20000.0}, index=idx)
    spy = 600 + spy_slope * np.arange(390) * 600 / 100     # ~ -0.4%/100 min
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
    st = LabStrategy("ULT-04", MOD, window=[1030, 1430], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=20_000_000)      # module default EXIT "T" -> t1s1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 10:25", tz=tz) <= t <= pd.Timestamp("2026-11-18 14:30", tz=tz) for t in times)
    if len(sigs) == 2:
        assert (times[1] - times[0]) >= pd.Timedelta(minutes=75)
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == -1 and abs((s.stop - entry) - 1.0) < 1e-6 and abs((entry - s.target) - 1.0) < 1e-6   # t1s1, R = 1
    # geom S (the TX30 / TX45 variants): 2R catastrophic stop, no target
    _LAB_FRAMES.clear()
    sx = LabStrategy("ULT-04X", MOD, window=[1030, 1430], context=["spy_fo"], refire=True, refire_cooldown=0, geom="S")
    x = sx.signals(_ctx(bars, peers))[0]
    assert x.target is None and abs((x.stop - float(bars["close"].iloc[x.bar_index])) - 2.0) < 1e-6
    # fail safe: no SPY context -> no signal; rising tape -> no signal
    _LAB_FRAMES.clear()
    assert st.signals(_ctx(bars, None)) == []
    _LAB_FRAMES.clear(); lab_context._CACHE.clear()   # context is cached per peers/bar
    up_bars, up_peers = _day(spy_slope=+0.004)
    assert st.signals(_ctx(up_bars, up_peers)) == []
