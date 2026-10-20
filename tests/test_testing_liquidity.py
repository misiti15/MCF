"""Testing 1 "trade liquidity" setups (research/bdi/reddit1012liq, owner request 2026-10-12): the overlay loads them,
the live LabStrategy fires the opening-range-low sweep reversal on a synthetic day with the structural stop and the
opt-in target_price, and the management keys reach the signal. Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("LIQ-orl-sweep-open15-s25-long", "LIQ-pdl-sweep-open15-vwap-long")


def _testing_strategies(monkeypatch):
    from mcf.config import load_config
    from mcf.strategies.setups import build_strategies

    monkeypatch.setenv("MCF_ACCOUNT", "testing")
    out = {s.name: s for s in build_strategies(load_config())}
    monkeypatch.setenv("MCF_ACCOUNT", "graveyard")   # LIQ-orl: Testing 2 2026-10-20, Graveyard account 2026-10-21 (owner)
    t2 = {s.name: s for s in build_strategies(load_config())}
    assert "LIQ-orl-sweep-open15-s25-long" not in out
    out["LIQ-orl-sweep-open15-s25-long"] = t2["LIQ-orl-sweep-open15-s25-long"]
    return out


def test_overlay_enables_both_with_structural_exit_and_management(monkeypatch):
    from mcf.strategies.setups import LabStrategy

    st = _testing_strategies(monkeypatch)
    for n in NAMES:
        assert isinstance(st[n], LabStrategy) and st[n].structural and hasattr(st[n].mod, "target_price")
        assert st[n].params.get("scale_out_r") is None
    pdl = st["LIQ-pdl-sweep-open15-vwap-long"].params
    assert pdl["be_at_r"] == 1.0 and pdl["time_stop_min"] == 15 and pdl["time_stop_min_r"] == 0.25


def _day():
    """OR 09:30-10:00 around 100 (low 99.94); 10:00-10:15 sweeps to 98.84; 10:15-10:30 closes back above 100."""
    idx = pd.date_range("2026-10-12 09:30", periods=390, freq="1min", tz="America/New_York")
    px = np.r_[np.full(30, 100.0), np.linspace(100, 98.9, 15), np.linspace(98.9, 100.5, 15), np.full(330, 100.5)]
    return pd.DataFrame({"open": px, "high": px + 0.06, "low": px - 0.06, "close": px, "volume": 10000.0}, index=idx)


def test_orl_sweep_fires_with_structural_stop_and_target():
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

    st = LabStrategy("LIQ-orl-sweep-open15-s25-long", "research/bdi/reddit1012liq/live/LIQ-orl-sweep-open15-s25-long.py",
                     window=[950, 1500])
    bars = _day()
    _LAB_FRAMES.clear()
    ctx = SimpleNamespace(symbol="LIQTEST", date=bars.index[0].date(), bars=bars, prior5=None, atr=2.5, prev_close=100.0,
                          prev_high=101.0, prev_low=95.0, avg_dollar_volume=2e8)
    sig = st.generate(ctx)
    assert len(sig) == 1 and sig[0].side == 1
    end = bars.index[sig[0].bar_index] + pd.Timedelta(minutes=1)
    assert end.hour * 100 + end.minute == 1030                       # the 15-minute bar closing back above 100
    px = float(bars["close"].iloc[sig[0].bar_index])
    sweep_low = float(bars["low"].iloc[30:45].min())
    assert abs(sig[0].stop - (sweep_low - 0.05 * 2.5)) < 1e-9
    assert abs(sig[0].target - (px + 2.5 * (px - sig[0].stop))) < 1e-9


def test_mask_is_the_same_on_a_multi_day_frame():
    """The parity check runs the modules on stacked symbol-days; a live frame is one symbol-day."""
    import importlib.util

    from mcf.research.heat import heat_frame

    bars = _day()
    d5 = bars.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    f = heat_frame(d5)
    f["atr_d"] = 2.5
    f["dist_pdh_atr"] = (101.0 - f["close"]) / 2.5
    f["dist_pdl_atr"] = (f["close"] - 95.0) / 2.5
    f = f.reset_index(drop=True)
    two = pd.concat([f.assign(symbol="A", date=1), f.assign(symbol="B", date=1)], ignore_index=True)
    for n in NAMES:
        p = ROOT / "research/bdi/reddit1012liq/live" / f"{n}.py"
        import sys

        sys.path.insert(0, str(p.parent))
        spec = importlib.util.spec_from_file_location(f"t_{n.replace('-', '_')}", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        one = np.asarray(m.mask(f), bool)
        both = np.asarray(m.mask(two), bool)
        assert (both[: len(f)] == one).all() and (both[len(f):] == one).all()
    assert one.dtype == bool
