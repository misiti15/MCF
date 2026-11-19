"""Smoke test: ULT-05 module imports and runs under the live LabStrategy (context spy_fo) on BOTH sides (side from the
setup name), fires a with-the-gap pullback near VWAP inside its window, honours the refire thinning, and fails safe
without SPY context.
    pytest -q research/ultimate_1119/ULT-05-withgap-continuation/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[1] / "modules" / "ULT-05-withgap-continuation.py")
ET = "America/New_York"


def _day(sgn):
    # gap of 4% in direction sgn, then the price drifts in the gap direction with small pullbacks hugging VWAP
    rng = np.random.default_rng(5)
    o = 100 * (1 + sgn * 0.04)
    steps = sgn * 0.002 + rng.normal(0, 0.15, 390)
    px = o + np.cumsum(steps)
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz=ET)
    vol = 20000 + 15000 * (np.sign(steps) == sgn)       # more volume on with-trend minutes -> buyPressure sign
    bars = pd.DataFrame({"open": np.r_[o, px[:-1]], "high": np.maximum(px, np.r_[o, px[:-1]]) + 0.01,
                         "low": np.minimum(px, np.r_[o, px[:-1]]) - 0.01, "close": px, "volume": vol}, index=idx)
    spy = 600 + 0.0 * np.arange(390)
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _check(name, sgn):
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

    _LAB_FRAMES.clear()
    bars, peers = _day(sgn)
    st = LabStrategy(name, MOD, window=[1015, 1400], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=20_000_000, geom="t1s1")
    assert st.side == sgn
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, len(sigs)
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 10:10", tz=ET) <= t <= pd.Timestamp("2026-11-18 14:00", tz=ET) for t in times)
    if len(sigs) == 2:
        assert times[1] - times[0] >= pd.Timedelta(minutes=75)
    s = sigs[0]
    e = float(bars["close"].iloc[s.bar_index])
    assert s.side == sgn and abs(sgn * (e - s.stop) - 1.0) < 1e-6 and abs(sgn * (s.target - e) - 1.0) < 1e-6
    # geom S (EXIT "X"): 2R catastrophic stop beyond the entry, no target
    _LAB_FRAMES.clear()
    sx = LabStrategy(name, MOD, window=[1015, 1400], context=["spy_fo"], refire=True, refire_cooldown=0, geom="S")
    x = sx.signals(_ctx(bars, peers))[0]
    assert x.target is None and abs(sgn * (float(bars["close"].iloc[x.bar_index]) - x.stop) - 2.0) < 1e-6
    # fail safe: no SPY context -> no signal
    _LAB_FRAMES.clear()
    assert st.signals(_ctx(bars, None)) == []
    # the wrong-side setup never fires on this day
    _LAB_FRAMES.clear()
    other = LabStrategy("ULT-05-S" if sgn > 0 else "ULT-05-L", MOD, window=[1015, 1400], context=["spy_fo"])
    assert other.side == -sgn and other.signals(_ctx(bars, peers)) == []


def test_long_side():
    _check("ULT-05-L", 1)


def test_short_side():
    _check("ULT-05-S", -1)
