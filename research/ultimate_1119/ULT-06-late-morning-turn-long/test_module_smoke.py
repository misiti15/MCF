"""Smoke test: the ULT-06 module loads and runs under the live LabStrategy (type: lab, context [spy_fo]) on a synthetic
morning-turn day, fires only after the new low is reclaimed with SPY off its low, and gives the same signal on bars cut
at the signal (no look-ahead).
    pytest -q research/ultimate_1119/ULT-06-late-morning-turn-long/test_module_smoke.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from mcf.strategies import lab_context as LC
from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

ROOT = Path(__file__).resolve().parents[3]
MOD = "research/ultimate_1119/modules/ULT-06-late-morning-turn-long.py"


def _bars(path):
    idx = pd.date_range("2026-11-02 09:30", periods=390, freq="1min", tz="America/New_York")
    c = np.asarray(path, float)
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0005, "low": np.minimum(o, c) * 0.9995, "close": c,
                         "volume": 50_000.0}, index=idx)


def _day(spy_turns=True):
    m = np.arange(390).astype(float)
    # SPY: flat to 10:00, -0.5% by 10:40, then (optionally) +0.3% back by 11:00
    dn = np.where(m < 30, 0.0, np.where(m < 70, -0.005 * (m - 30) / 40, -0.005))
    up = np.where(m < 70, 0.0, np.where(m < 90, 0.003 * (m - 70) / 20, 0.003)) if spy_turns else 0.0
    spy = 600 * (1 + dn + up)
    # XYZ: 50 to 10:30, new low 47 at 10:45, reclaim to 48.5 by 11:05
    xyz = np.where(m < 60, 50.0, np.where(m < 75, 50 - 3 * (m - 60) / 15, np.where(m < 95, 47 + 1.5 * (m - 75) / 20, 48.5)))
    return {"SPY": _bars(spy), "XYZ": _bars(xyz)}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="XYZ", date=bars.index[0].date(), bars=bars, prior5=None, atr=3.0,
                           prev_close=float(bars["open"].iloc[0]), prev_high=1e9, prev_low=0.0,
                           avg_dollar_volume=1e9, peers=peers, index_priors=None)


def _strategy():
    return LabStrategy("ULT-06-late-morning-turn-long", str(ROOT / MOD), window=[1050, 1130], context=["spy_fo"],
                       refire=True, refire_cooldown=11, r_atr_frac=0.5, min_adv=20e6,
                       time_stop_min=30, time_stop_min_r=1e9)


def _clear():
    LC._CACHE.clear()
    _LAB_FRAMES.clear()


def test_module_runs_live_and_fires_on_turn():
    _clear()
    peers = _day()
    sigs = _strategy().signals(_ctx(peers["XYZ"], peers))
    assert sigs, "expected a signal on the turn day"
    first = sigs[0]
    t = peers["XYZ"].index[first.bar_index]
    assert 1049 <= t.hour * 100 + t.minute <= 1130
    assert first.side == 1 and first.target is None
    assert abs((peers["XYZ"]["close"].iloc[first.bar_index] - first.stop) - 1.5) < 1e-6   # 2R = 0.5 x ATR 3.0
    assert first.time_stop_min == 30 and first.time_stop_min_r >= 1e6
    k = first.bar_index + 1
    _clear()
    cut = {s: b.iloc[:k] for s, b in peers.items()}
    live = _strategy().signals(_ctx(cut["XYZ"], cut))
    assert live and live[-1].bar_index == first.bar_index


def test_no_signal_without_spy_turn():
    _clear()
    peers = _day(spy_turns=False)
    assert not _strategy().signals(_ctx(peers["XYZ"], peers))
