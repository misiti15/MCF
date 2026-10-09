"""RW6 + VWAP band guard (owner-directed 2026-10-09): the guard blocks shorts while a close above VWAP + 2 SD is
unresolved, and the live LabStrategy frame carries the volume the guard needs."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = Path("research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py")


def _mod():
    spec = importlib.util.spec_from_file_location("rw6g1", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_guard_blocks_until_a_close_back_at_or_below_vwap():
    m = _mod()
    close = np.array([100, 100, 100, 100, 100, 100, 106, 105, 104, 99, 101], dtype=float)
    df = pd.DataFrame({"high": close, "low": close, "close": close, "volume": 1000.0})
    b = m.vwap_band_block(df)
    assert not b[:6].any()            # flat: no excursion
    assert b[6] and b[7] and b[8]     # closed above +2 SD at bar 6 -> blocked while still above VWAP
    assert not b[9] and not b[10]     # bar 9 closes below VWAP -> reset; bar 10 above VWAP but no new +2 SD close


def test_guard_fails_safe_without_volume():
    m = _mod()
    df = pd.DataFrame({"high": [1.0], "low": [1.0], "close": [1.0]})
    assert m.vwap_band_block(df).all()


def test_live_lab_frame_has_volume_and_module_runs():
    from mcf.strategies.setups import LabStrategy

    from mcf.strategies.setups import _LAB_FRAMES

    _LAB_FRAMES.clear()
    st = LabStrategy("RW6G1", str(MOD), window=[950, 1130])
    idx = pd.date_range("2026-10-09 09:30", periods=120, freq="1min", tz="America/New_York")
    px = np.linspace(100, 104, 120)
    bars = pd.DataFrame({"open": px, "high": px + 0.05, "low": px - 0.05, "close": px, "volume": 1000.0}, index=idx)
    ctx = SimpleNamespace(symbol="RW6TEST", date=idx[0].date(), bars=bars, prior5=None, atr=2.0, prev_close=100.0,
                          prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9)
    st.generate(ctx)                  # must not raise
    f = next(v for k, v in _LAB_FRAMES.items() if k[0] == "RW6TEST")
    assert "volume" in f and float(f["volume"].iloc[0]) == 5000.0
