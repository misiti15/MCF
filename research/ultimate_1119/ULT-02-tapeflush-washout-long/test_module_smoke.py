"""Smoke test: the ULT-02 module loads and runs under the live LabStrategy (type: lab, context [spy_fo]) on a synthetic
tape-flush day, fires only after the flush, and gives the same signal on bars cut at the signal (no look-ahead).
    pytest -q research/ultimate_1119/ULT-02-tapeflush-washout-long/test_module_smoke.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from mcf.strategies import lab_context as LC
from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

ROOT = Path(__file__).resolve().parents[3]
MOD = "research/ultimate_1119/modules/ULT-02-tapeflush-washout-long.py"


def _bars(path):
    idx = pd.date_range("2026-11-02 09:30", periods=390, freq="1min", tz="America/New_York")
    c = np.asarray(path, float)
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0005, "low": np.minimum(o, c) * 0.9995, "close": c,
                         "volume": 50_000.0}, index=idx)


def _day():
    m = np.arange(390)
    spy = 600 * (1 + np.where(m < 90, 0.0, np.where(m < 120, -0.008 * (m - 90) / 30, -0.008)))  # -0.8% 11:00-11:30
    xyz = 50 * (1 + np.where(m < 60, 0.0, np.where(m < 120, -0.12 * (m - 60) / 60, -0.12)))     # -12% by 11:30
    return {"SPY": _bars(spy), "XYZ": _bars(xyz)}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="XYZ", date=bars.index[0].date(), bars=bars, prior5=None, atr=3.0,
                           prev_close=float(bars["open"].iloc[0]), prev_high=1e9, prev_low=0.0,
                           avg_dollar_volume=1e9, peers=peers, index_priors=None)


def _strategy():
    return LabStrategy("ULT-02-tapeflush-washout-long", str(ROOT / MOD), window=[1030, 1500], context=["spy_fo"],
                       refire=True, refire_cooldown=14, r_atr_frac=0.5, min_adv=20e6,
                       time_stop_min=45, time_stop_min_r=1e9)


def test_module_runs_live_and_fires_after_flush():
    peers = _day()
    st = _strategy()
    sigs = st.signals(_ctx(peers["XYZ"], peers))
    assert sigs, "expected a signal on the flush day"
    first = sigs[0]
    t = peers["XYZ"].index[first.bar_index]
    assert t.hour * 100 + t.minute >= 1029          # decision bar closes >= 10:30
    assert first.side == 1 and first.target is None
    assert abs((peers["XYZ"]["close"].iloc[first.bar_index] - first.stop) - 1.5) < 1e-6   # 2R = 0.5 x ATR 3.0
    assert first.time_stop_min == 45 and first.time_stop_min_r >= 1e6
    # live: bars cut right after the first signal's bar give the same decision (no look-ahead)
    k = first.bar_index + 1
    LC._CACHE.clear()
    _LAB_FRAMES.clear()
    cut = {s: b.iloc[:k] for s, b in peers.items()}
    live = _strategy().signals(_ctx(cut["XYZ"], cut))
    assert live and live[-1].bar_index == first.bar_index


def test_no_signal_without_flush():
    peers = _day()
    peers["SPY"] = _bars(np.full(390, 600.0))
    LC._CACHE.clear()
    _LAB_FRAMES.clear()
    assert not _strategy().signals(_ctx(peers["XYZ"], peers))
