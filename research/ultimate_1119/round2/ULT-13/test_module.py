"""Smoke test: ULT-13 module imports and runs under the live LabStrategy (context spy_fo), fires on a ONE-bar RSI(14)
collapse with buy pressure, gives t1s1 / 2u-stop levels, does not fire on a slow (multi-bar) RSI slide, honours the G1
down-tape guard and the universal SPY long filter, fails safe without SPY context, and its features are point-in-time.
    pytest -q research/ultimate_1119/round2/ULT-13/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-13.py")


def _load(**kw):
    spec = importlib.util.spec_from_file_location("ult13", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _day(slide_min=5, spy="flat", day="2026-11-18"):
    # drift up to 11:00 (RSI14 > 50, buy pressure > 0), then a 2.5-point slide over `slide_min` minutes, then flat
    px = [100.0]
    for k in range(1, 390):
        if k < 90:
            step = 0.01 if k % 3 else -0.005
        elif k < 90 + slide_min:
            step = -2.5 / slide_min
        else:
            step = 0.0005 * (1 if k % 2 else -1)
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01, "close": px,
                         "volume": 20000.0}, index=idx)
    t = np.arange(390)
    if spy == "flat":
        s = 600 + 0.01 * np.sin(t)
    elif spy == "down_falling":      # -1.0% from the open by 10:30 and still falling: G1 and universal both apply? no:
        s = 600 * (1 - 0.0001 * t)   # universal band is -0.30..-0.75 only; at 11:05 SPY is ~ -0.95% -> only G1 blocks
    else:                            # "band_falling": -0.5% at 11:05 and falling -> the universal filter blocks
        s = 600 * (1 - 0.005 * np.clip(t / 95, 0, 2))
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _st(name, geom="t1s1"):
    from mcf.strategies.setups import LabStrategy
    return LabStrategy(name, MOD, window=[950, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=50_000_000, geom=geom)


def test_module_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES

    _LAB_FRAMES.clear()
    bars, peers = _day()
    sigs = _st("ULT-13").signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2
    tz = "America/New_York"
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 11:00", tz=tz) <= t <= pd.Timestamp("2026-11-18 11:10", tz=tz), t
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((entry - s.stop) - 1.0) < 1e-6 and abs((s.target - entry) - 1.0) < 1e-6   # t1s1, u = 1
    # geom S (EXIT "X"): 2u catastrophic stop, no target
    _LAB_FRAMES.clear()
    x = _st("ULT-13X", geom="S").signals(_ctx(bars, peers))[0]
    assert x.target is None and abs((float(bars["close"].iloc[x.bar_index]) - x.stop) - 2.0) < 1e-6
    # fail safe: no SPY context -> no signal
    _LAB_FRAMES.clear()
    assert _st("ULT-13c").signals(_ctx(bars, None)) == []
    # universal long filter: SPY -0.30..-0.75% from its open and falling over 30 min -> blocked
    _LAB_FRAMES.clear()
    b2, p2 = _day(spy="band_falling", day="2026-11-17")
    assert _st("ULT-13d").signals(_ctx(b2, p2)) == []


def test_one_bar_only_and_guard():
    from mcf.strategies.setups import _LAB_FRAMES

    # a slow slide (25 min) does not produce a one-bar collapse
    _LAB_FRAMES.clear()
    b, p = _day(slide_min=25, day="2026-11-16")
    assert _st("ULT-13e").signals(_ctx(b, p)) == []
    # G0 fires on a SPY -0.95%-and-falling day (outside the universal band); G1 blocks it
    _LAB_FRAMES.clear()
    b, p = _day(spy="down_falling", day="2026-11-13")
    assert len(_st("ULT-13f").signals(_ctx(b, p))) >= 1
    _LAB_FRAMES.clear()
    g1 = _st("ULT-13g")
    g1.mod.GUARD = "G1"
    assert g1.signals(_ctx(b, p)) == []
    m = _load(GUARD="G1")
    # direct check of the guard logic
    df = pd.DataFrame({"tod": [1000, 1030, 1030], "spy_fo": [-0.5, -0.5, -0.5], "date": ["d", "d", "e"],
                       "close": 50.0, "atr_d": 2.0, "gap": 0.0, "rsi": 30.0, "fromOpen": -2.0, "buyPressure": 1.0})
    df.loc[0, "date"] = "d"
    r = m.features(df)
    assert not r["g1_ok"][0]                # no 30-min SPY history and SPY <= -0.30% -> G1 blocks (fixed build rule)
    assert not r["g1_ok"][1]                # flat over 30 min (r30 = 0) and SPY <= -0.30% -> blocked
    df2 = df.assign(spy_fo=[-0.9, -0.5, -0.5])
    assert m.features(df2)["g1_ok"][1]      # rising over 30 min -> allowed


def test_features_point_in_time():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    df = pd.DataFrame({"tod": tod, "close": c, "fromOpen": (c / c[0] - 1) * 100, "gap": 0.0, "atr_d": 4.0,
                       "spy_fo": rng.normal(0, 0.2, n), "rsi": rng.uniform(20, 80, n), "buyPressure": rng.normal(0, 1, n)})
    full = m.features(df)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("rsi_prev", "cost_r", "spy_r30", "g1_ok", "univ_ok"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)
