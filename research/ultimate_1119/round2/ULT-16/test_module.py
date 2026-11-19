"""Smoke test: ULT-16 COST-GEO module imports and runs under the live LabStrategy (context spy_fo) on both sides (side from
the setup name): the long side fires on the ULT-03 RSI(14) collapse, the short side on the ULT-01 gap-down pop; both give
a symmetric +/- M x daily-ATR bracket (GEOM "S" with stop_price / target_price); the vol floor binds; no SPY context ->
no signal; features are point-in-time.
    pytest -q research/ultimate_1119/round2/ULT-16/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-16.py")
TZ = "America/New_York"


def _load(**kw):
    spec = importlib.util.spec_from_file_location("ult16", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _flat_spy(idx):
    s = 600 + 0.01 * np.sin(np.arange(390))
    return {"SPY": pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)}


def _long_day(day="2026-11-18"):
    # drift up to 11:00 (RSI14 > 50, buy pressure > 0), a 2.5-point slide over 5 minutes, then flat
    px = [100.0]
    for k in range(1, 390):
        step = (0.01 if k % 3 else -0.005) if k < 90 else (-0.5 if k < 95 else 0.0005 * (1 if k % 2 else -1))
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01, "close": px,
                         "volume": 20000.0}, index=idx)
    return bars, _flat_spy(idx)


def _short_day(day="2026-11-13"):
    # open 97 after a 100 close (gap -3%), slide to ~93.6 by 10:45, then a choppy pop back up
    c5 = [97.0]
    for k in range(1, 78):
        step = (-0.25 if k % 3 else 0.10) if k <= 15 else ((0.60 if k % 3 else -0.30) if k <= 30 else
                                                           (0.02 if k % 2 else -0.02))
        c5.append(c5[-1] + step)
    px = np.interp(np.arange(390) / 5.0, np.arange(78), c5)
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    bars = pd.DataFrame({"open": px, "high": px + 0.02, "low": px - 0.02, "close": px, "volume": 20000.0}, index=idx)
    s = 600 - 0.001 * np.arange(390)
    return bars, {"SPY": pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6},
                                      index=idx)}


def _ctx(bars, peers, atr=4.0):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=atr, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _st(name, window):
    from mcf.strategies.setups import LabStrategy
    return LabStrategy(name, MOD, window=window, context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=150_000_000)


def test_long_side_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    b, p = _long_day()
    st = _st("ULT-16-L", [1015, 1500])
    assert st.geom == "S" and st.mod.SIDE == "long"
    sigs = st.signals(_ctx(b, p))
    assert 1 <= len(sigs) <= 2, sigs
    t = b.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 11:00", tz=TZ) <= t <= pd.Timestamp("2026-11-18 11:15", tz=TZ), t
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    M = st.mod.M
    assert s.side == 1 and abs((e - s.stop) - M * 4.0) < 1e-6 and abs((s.target - e) - M * 4.0) < 1e-6
    _LAB_FRAMES.clear()
    assert _st("ULT-16-Lc", [1015, 1500]).signals(_ctx(b, None)) == []          # no SPY context -> no signal
    _LAB_FRAMES.clear()
    v = _st("ULT-16-Lv", [1015, 1500])
    v.mod.VOL_FLOOR = 2.5
    assert v.signals(_ctx(b, p, atr=2.0)) == []                                  # atr_d% ~2.1 < 2.5 -> blocked
    _LAB_FRAMES.clear()
    assert len(v.signals(_ctx(b, p, atr=4.0))) >= 1                              # ~4.1% -> allowed


def test_short_side_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    b, p = _short_day()
    st = _st("ULT-16-S", [1100, 1500])
    assert st.mod.SIDE == "short"
    sigs = st.signals(_ctx(b, p))
    assert 1 <= len(sigs) <= 2, sigs
    times = [b.index[s.bar_index] for s in sigs]
    assert all(t >= pd.Timestamp("2026-11-13 10:55", tz=TZ) for t in times)
    if len(times) == 2:
        assert times[1] - times[0] >= pd.Timedelta(minutes=75)
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    M = st.mod.M
    assert s.side == -1 and abs((s.stop - e) - M * 4.0) < 1e-6 and abs((e - s.target) - M * 4.0) < 1e-6
    _LAB_FRAMES.clear()
    assert _st("ULT-16-Sc", [1100, 1500]).signals(_ctx(b, None)) == []


def test_features_point_in_time():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    df = pd.DataFrame({"tod": tod, "close": c, "fromOpen": (c / c[0] - 1) * 100, "gap": -2.0, "atr_d": 4.0,
                       "spy_fo": rng.normal(0, 0.2, n), "rsi": rng.uniform(20, 80, n), "rsi5": rng.uniform(20, 95, n),
                       "buyPressure": rng.normal(0, 1, n), "dist_lod_atr": rng.uniform(0, 1, n),
                       "sma20_dist_pct": rng.normal(0, 2, n)})
    full = m.features(df)
    tl, ts = m.trigger(full, 1), m.trigger(full, -1)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("spy950", "spy_r30", "cost_r", "atrp", "crossed"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)
        assert m.trigger(part, 1)[i] == tl[i] and m.trigger(part, -1)[i] == ts[i]
