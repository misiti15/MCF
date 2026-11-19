"""Smoke test: ULT-22 module imports and runs under the live LabStrategy (context spy_fo, symbols: module), fires on a
sharp 15-min dip after a rising hour in a high-ATR ETF inside the module window, gives t05s1 levels, honours the
symbol allow-list, the universal SPY long filter, and fails safe without SPY context.
    pytest -q research/ultimate_1119/round3/ULT-22/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-22.py")


def _day(spy_path="flat", day="2026-11-18"):
    # flat to 13:30, strong rally 13:30-14:05 (+2%), sharp dip 14:05-14:20 (~-0.9%), then flat
    px = [100.0]
    for k in range(1, 390):
        m = k  # minutes since 09:30
        if 240 <= m < 275:
            step = 2.0 / 35
        elif 275 <= m < 290:
            step = -0.92 / 15
        else:
            step = 0.0005 * (1 if k % 2 else -1)
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.005, "low": np.minimum(op, px) - 0.005,
                         "close": px, "volume": 20000.0}, index=idx)
    t = np.arange(390)
    if spy_path == "flat":
        spy = 600 + 0.01 * np.sin(t)
    else:   # SPY slides to -0.5% from its open over the afternoon and keeps falling
        spy = 600 * (1 - 0.005 * np.clip((t - 200) / 100, 0, 1.2))
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, sym="SOXL"):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _load():
    import importlib.util
    spec = importlib.util.spec_from_file_location("u22", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _st(name="ULT-22"):
    from mcf.strategies.setups import LabStrategy
    return LabStrategy(name, MOD, window=list(_load().WINDOW), context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=95_000_000, geom="t05s1", symbols="module")


def test_module_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES

    _LAB_FRAMES.clear()
    bars, peers = _day()
    st = _st()
    sigs = st.signals(_ctx(bars, peers))
    assert len(sigs) >= 1
    tz = "America/New_York"
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 14:10", tz=tz) <= t <= pd.Timestamp("2026-11-18 14:30", tz=tz)
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((entry - s.stop) - 1.0) < 1e-6 and abs((s.target - entry) - 0.5) < 1e-6   # t05s1, u = 1
    # a stock (not in the basket universe) is not eligible (YAML symbols: module = the module's SYMBOLS)
    assert st.eligible(_ctx(bars, peers)) and not st.eligible(_ctx(bars, peers, sym="AAPL"))
    # universal long filter: SPY -0.30..-0.75% from its open and falling over 30 min -> blocked
    _LAB_FRAMES.clear()
    b2, p2 = _day(spy_path="down", day="2026-11-17")
    assert _st("ULT-22b").signals(_ctx(b2, p2)) == []
    # fail safe: no SPY context -> no signal
    _LAB_FRAMES.clear()
    assert _st("ULT-22c").signals(_ctx(bars, None)) == []


def test_features_point_in_time():
    """A feature at bar i must not change when later bars are removed (no look-ahead)."""
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    df = pd.DataFrame({"tod": tod, "close": c, "high": c * 1.002, "low": c * 0.998, "fromOpen": (c / c[0] - 1) * 100,
                       "gap": 0.0, "atr_d": 4.0, "spy_fo": rng.normal(0, 0.2, n), "vwapDistPct": 0.0,
                       "dist_hod_atr": 0.0, "dist_lod_atr": 0.0})
    full = m.features(df)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("ret3", "ret12", "di7", "atrp", "cost_r", "spy_r30"):
            a, b = full[k][i], part[k][i]
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)


def test_triggers_and_universe():
    m = _load()
    assert m.UNIVERSES["W"] <= m.UNIVERSES["Q"] and "MSTX" not in m.UNIVERSES["Q"] and "GLD" not in m.UNIVERSES["Q"]
    r = {"ret3": np.array([-0.8, -0.6, -0.8, -0.8]), "ret12": np.array([0.0, 0.0, 0.0, 0.0]),
         "di7": np.array([0.0, 0.0, 0.0, 0.0]), "atrp": np.array([4.0, 2.5, 3.0, 4.0]),
         "cost_r": np.array([0.05, 0.05, 0.05, 0.09])}
    # P: needs ATR >= 3.6 and cost_r <= 0.10; A: -0.21 x ATR% drop, ATR >= 2.4, cost_r <= 0.08
    assert list(m.trigger(r, "P")) == [True, False, False, True]
    assert list(m.trigger(r, "A")) == [False, True, True, False]
