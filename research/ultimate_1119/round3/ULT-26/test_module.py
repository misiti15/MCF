"""Smoke test: ULT-26 module imports and runs under the live LabStrategy (context spy_fo) on both sides (two entries, one
file; "-S" = short), gives the frozen exit geometry, needs BOTH the gap and the trend tape (no signal on a flat or
opposite tape, none without a gap), never shorts a LEV fund, fails safe without SPY context, and its features are
point-in-time (truncation test).
    pytest -q research/ultimate_1119/round3/ULT-26/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-26.py")
TZ = "America/New_York"


def _load(name="ult26", **kw):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _day(sgn=1, gap=4.0, day="2026-11-18", spy="trend", base=100.0):
    """1-minute bars: open at base x (1 + gap), a wavy trend in direction sgn all day (~ +-4%); SPY trends sgn x 0.9%
    ("trend"), stays flat ("flat") or trends against ("against")."""
    t = np.arange(390)
    o0 = base * (1 + gap / 100)
    px = o0 * (1 + sgn * (0.04 * t / 390 + 0.003 * np.sin(t / 9.0)))
    op = np.r_[o0, px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    up = (px >= op)
    vol = 20000.0 + 5000 * (np.arange(390) % 7) + np.where(up == (sgn > 0), 15000.0, 0.0)
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01, "close": px,
                         "volume": vol}, index=idx)
    d = {"trend": sgn, "flat": 0, "against": -sgn}[spy]
    s = 600 * (1 + d * 0.009 * np.clip(t / 200, 0, 1.5)) + (0.01 * np.sin(t) if d == 0 else 0)
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, base=100.0, atr=4.0, sym="ABCD"):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=atr, prev_close=base,
                           prev_high=base * 1.01, prev_low=base * 0.99, avg_dollar_volume=2e8, peers=peers)


def _st(name):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    return LabStrategy(name, MOD, r_atr_frac=0.25, window=list(m.WINDOW), context=["spy_fo"], refire=True,
                       refire_cooldown=0, min_adv=50_000_000, geom=m.GEOM, time_stop_min=45, time_stop_min_r=99,
                       symbols="module" if name.endswith("-S") else None)


def _check_geom(m, s, bars, sgn):
    entry = float(bars["close"].iloc[s.bar_index]) if hasattr(s, "bar_index") else s.entry
    if m.EXIT == "X":
        assert abs(sgn * (entry - s.stop) - 2 * 0.25 * 4.0) < 1e-6, (entry, s.stop)
    else:
        assert abs(sgn * (entry - s.stop) - 0.25 * 4.0) < 1e-6


def test_long_side_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _LAB_FRAMES.clear()
    bars, peers = _day(1)
    st = _st("ULT-26")
    assert st.side == 1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 10:25", tz=TZ) <= t <= pd.Timestamp("2026-11-18 14:30", tz=TZ), t
    _check_geom(m, sigs[0], bars, 1)
    _LAB_FRAMES.clear()
    assert _st("ULT-26").signals(_ctx(bars, None)) == []                          # no SPY context -> no signal
    _LAB_FRAMES.clear()
    b2, p2 = _day(1, day="2026-11-17", spy="flat")
    assert _st("ULT-26").signals(_ctx(b2, p2)) == []                              # flat tape -> nothing
    _LAB_FRAMES.clear()
    b3, p3 = _day(1, day="2026-11-16", spy="against")
    assert _st("ULT-26").signals(_ctx(b3, p3)) == []                              # tape against the gap -> nothing
    _LAB_FRAMES.clear()
    b4, p4 = _day(1, gap=0.5, day="2026-11-13")
    assert _st("ULT-26").signals(_ctx(b4, p4, base=100.0)) == []                  # no gap -> nothing


def test_short_side_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _LAB_FRAMES.clear()
    bars, peers = _day(-1, gap=-4.0, day="2026-11-12")
    st = _st("ULT-26-S")
    assert st.side == -1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    _check_geom(m, sigs[0], bars, -1)
    assert not st.eligible(_ctx(bars, peers, sym="SQQQ"))                         # LEV fund: never shorted
    _LAB_FRAMES.clear()
    b2, p2 = _day(-1, gap=-4.0, day="2026-11-11", spy="against")
    assert st.signals(_ctx(b2, p2)) == []                                         # SPY up -> no short


def test_features_point_in_time():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((575 + 5 * k) // 60) * 100 + (575 + 5 * k) % 60) for k in range(n)])   # 09:35 ...
    c = 50 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    df = pd.DataFrame({"tod": tod, "close": c, "gap": 3.0, "atr_d": 2.0, "adv20": 1e8,
                       "spy_fo": np.cumsum(rng.normal(0.02, 0.1, n)), "vwapDistPct": rng.normal(0.3, 0.5, n),
                       "buyPressure": rng.normal(0, 1, n), "rsi5": rng.uniform(10, 95, n),
                       "dist_lod_atr": rng.uniform(0, 2, n), "dist_hod_atr": rng.uniform(0, 2, n)})
    full = m.features(df)
    assert np.isnan(full["spy_rp"][:3]).all()                                    # rows before 09:50 never used
    for i in (10, 30, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("spy_rp", "rp", "cost_r", "intake", "atrp"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, i)
        for sg in (1, -1):
            assert bool(m.signal(full, sg)[i]) == bool(m.signal(part, sg)[i])


def test_lev_flag_and_spy_range():
    m = _load()
    df = pd.DataFrame({"symbol": ["ABCD", "SQQQ", "ABCD", "ABCD"], "date": "d", "tod": [950, 950, 1000, 1005],
                       "close": 50.0, "gap": -3.0, "atr_d": 2.0, "adv20": 1e8, "spy_fo": [-0.2, -0.2, -0.6, -0.4],
                       "vwapDistPct": -0.5, "buyPressure": -1.0, "rsi5": 40.0, "dist_lod_atr": 0.1,
                       "dist_hod_atr": 1.0})
    r = m.features(df.sort_values(["symbol", "date", "tod"]).reset_index(drop=True))
    # sorted rows: ABCD 950, 1000, 1005, SQQQ 950
    assert list(r["is_lev"]) == [False, False, False, True]
    assert abs(r["spy_rp"][0] - 0.0) < 1e-9 and abs(r["spy_rp"][1]) < 1e-9 and abs(r["spy_rp"][2] - 1 / 3) < 1e-9
