"""Smoke test: ULT-25 module imports and runs under the live LabStrategy (context spy_fo) on both sides (two entries, one
file; "-S" = short), gives the frozen TX-45 geometry (GEOM "S", catastrophic stop 2 x M x atr_d), honours the
cost_r <= 0.03 universe (a cheap $20 name never fires), the SPY filters, the LEV long-only rule, fails safe without SPY
context, and its features are point-in-time.
    pytest -q research/ultimate_1119/round3/ULT-25/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-25.py")
TZ = "America/New_York"


def _load(name="ult25", **kw):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _day(kind="collapse", base=500.0, day="2026-11-18", spy="flat"):
    """1-minute bars: a slow grind up all day, then at 13:30 a 5-minute event (collapse = sharp drop; pop = rally then
    a down-closing bar with an upper wick)."""
    px = [base]
    for k in range(1, 390):
        if kind == "collapse" and 240 <= k < 245:
            step = -0.025 * base / 5
        elif kind == "pop" and 225 <= k < 245:
            step = 0.0012 * base
        elif kind == "pop" and 245 <= k < 250:
            step = -0.0004 * base
        else:
            step = base * (2e-5 if k % 3 else -1e-5)
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    hi = np.maximum(op, px) + 0.02
    if kind == "pop":
        hi[245:250] += 0.002 * base
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    bars = pd.DataFrame({"open": op, "high": hi, "low": np.minimum(op, px) - 0.02, "close": px,
                         "volume": 20000.0 + 5000 * (np.arange(390) % 7)}, index=idx)
    t = np.arange(390)
    if spy == "flat":
        s = 600 + 0.01 * np.sin(t)
    elif spy == "up":
        s = 600 * (1 + 0.004 * np.clip(t / 60, 0, 1))
    else:                                       # steady SPY slide from 12:30: -0.6% by 13:35
        s = 600 * (1 - 0.006 * np.clip((t - 180) / 65, 0, 2))
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, atr=25.0, sym="TSLA"):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=atr,
                           prev_close=float(bars["open"].iloc[0]), prev_high=float(bars["open"].iloc[0]) * 1.01,
                           prev_low=float(bars["open"].iloc[0]) * 0.99, avg_dollar_volume=2e9, peers=peers)


def _st(name):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    return LabStrategy(name, MOD, r_atr_frac=m.M, window=list(m.WINDOW), context=["spy_fo"], refire=True,
                       refire_cooldown=0, min_adv=300_000_000, geom=m.GEOM, time_stop_min=45, time_stop_min_r=99,
                       symbols="module" if name.endswith("-S") else None)


def test_long_side_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _LAB_FRAMES.clear()
    bars, peers = _day("collapse")
    sigs = _st("ULT-25").signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    s = sigs[0]
    t = bars.index[s.bar_index]
    assert pd.Timestamp("2026-11-18 13:30", tz=TZ) <= t <= pd.Timestamp("2026-11-18 13:45", tz=TZ), t
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((entry - s.stop) - 2 * m.M * 25.0) < 1e-6        # TX-45: 2 Ru catastrophic stop
    _LAB_FRAMES.clear()
    assert _st("ULT-25").signals(_ctx(bars, None)) == []                          # no SPY context -> no signal
    _LAB_FRAMES.clear()
    b2, p2 = _day("collapse", day="2026-11-17", spy="down")
    assert _st("ULT-25").signals(_ctx(b2, p2)) == []                              # SPY 60-min <= -0.40% / band filter
    _LAB_FRAMES.clear()
    b3, p3 = _day("collapse", base=20.0, day="2026-11-16")
    assert _st("ULT-25").signals(_ctx(b3, p3, atr=1.0)) == []                     # $20 name: cost_r > 0.03


def test_short_side_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _LAB_FRAMES.clear()
    bars, peers = _day("pop", day="2026-11-13")
    st = _st("ULT-25-S")
    assert st.side == -1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert abs((s.stop - entry) - 2 * m.M * 25.0) < 1e-6
    assert not st.eligible(_ctx(bars, peers, sym="TQQQ"))                         # LEV fund: never shorted
    _LAB_FRAMES.clear()
    b2, p2 = _day("pop", day="2026-11-12", spy="up")   # own date: the SPY context is cached per date
    assert st.signals(_ctx(b2, p2)) == []                                         # SPY > +0.20% since 09:50


def test_lev_flag_and_universe_in_backtest_frame():
    m = _load()
    n = 4
    df = pd.DataFrame({"symbol": ["TSLA", "TQQQ", "TSLA", "TSLA"], "date": ["d", "e", "f", "g"], "tod": 1330,
                       "close": [400.0, 400.0, 400.0, 30.0], "atr_d": [20.0, 20.0, 20.0, 1.5], "gap": 0.0,
                       "fromOpen": 0.0, "high": 401.0, "low": 399.0, "spy_fo": 0.0, "adv20": [1e9, 1e9, 1e8, 1e9],
                       "rsi": 50.0, "rsi5": 85.0, "buyPressure": 1.0, "dist_lod_atr": 1.0, "sma20_dist_pct": 2.0,
                       "upper_wick": 0.3})
    r = m.features(df)
    assert list(r["is_lev"]) == [False, True, False, False]
    assert list(r["univ"]) == [True, True, False, False]                          # ADV $100M / $30 name out
    assert "TQQQ" in m.LEV and "TSLA" in m.NONLEV and "TQQQ" not in m.NONLEV


def test_features_point_in_time():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 500 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    df = pd.DataFrame({"tod": tod, "close": c, "high": c * 1.002, "low": c * 0.998, "fromOpen": (c / c[0] - 1) * 100,
                       "gap": 0.0, "atr_d": 25.0, "spy_fo": rng.normal(0, 0.2, n), "rsi": rng.uniform(20, 80, n),
                       "rsi5": rng.uniform(10, 95, n), "buyPressure": rng.normal(0, 1, n),
                       "dist_lod_atr": rng.uniform(0, 2, n), "sma20_dist_pct": rng.normal(0, 2, n),
                       "upper_wick": rng.uniform(0, 1, n)})
    full = m.features(df)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("rsi_prev", "rsi5_prev", "cost_r", "spy_r30", "spy_r60", "spy_950", "univ", "coll", "dip", "ts1",
                  "ts2", "long_ok", "short_ok"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)
        for sg in (1, -1):
            assert bool(m.signal(full, sg)[i]) == bool(m.signal(part, sg)[i])
