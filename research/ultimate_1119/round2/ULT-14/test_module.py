"""Smoke test: ULT-14 SNAP module imports and runs under the live LabStrategy (context spy_fo) on both sides (side from
the setup name), fires on a sharp 15-min counter-move against an intact trend, gives t05s1 / t1s1 levels, honours the
SPY 60-min long rule and the SPY-since-09:50 short rule, fails safe without SPY context, and its features are
point-in-time.
    pytest -q research/ultimate_1119/round2/ULT-14/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-14.py")
TZ = "America/New_York"


def _load(name="ult14"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _day(sgn=1, spy="flat", day="2026-11-18", snap_at=270):
    """Gentle trend in direction sgn, a strong trend leg over the hour before minute snap_at (14:00 by default), then a
    sharp 2.4-point counter-move over 5 minutes (~0.35 daily ATR over 15 min while +DI/-DI(7) still favour the trend),
    then flat."""
    px = [100.0]
    for k in range(1, 390):
        if k < snap_at - 60:
            step = sgn * (0.03 if k % 4 else -0.01)
        elif k < snap_at:
            step = sgn * (0.15 if k % 4 else -0.05)
        elif k < snap_at + 5:
            step = -sgn * 2.4 / 5
        else:
            step = 0.0005 * (1 if k % 2 else -1)
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01, "close": px,
                         "volume": 20000.0}, index=idx)
    t = np.arange(390)
    if spy == "flat":
        s = 600 + 0.01 * np.sin(t)
    elif spy == "falling_hour":       # SPY -0.6% over the hour before 14:00 -> the long rule blocks
        s = 600 * (1 - 0.006 * np.clip((t - 210) / 60, 0, 1))
    else:                             # "up": SPY +0.5% since 09:50 by 14:00 -> the short rule blocks
        s = 600 * (1 + 0.005 * np.clip((t - 20) / 190, 0, 1))
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _st(name, geom=None):
    from mcf.strategies.setups import LabStrategy
    return LabStrategy(name, MOD, window=[1400, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=50_000_000, geom=geom)


def _sig(name, sgn, spy="flat", day="2026-11-18", geom=None, peers=True):
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    b, p = _day(sgn, spy=spy, day=day)
    return b, _st(name, geom).signals(_ctx(b, p if peers else None))


def test_long_side_under_live_lab_strategy():
    b, sigs = _sig("ULT-14-L", 1)
    assert 1 <= len(sigs) <= 2, sigs
    t = b.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 14:00", tz=TZ) <= t <= pd.Timestamp("2026-11-18 14:10", tz=TZ), t
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((e - s.stop) - 1.0) < 1e-6 and abs((s.target - e) - 0.5) < 1e-6    # t05s1, u = 1
    _, x = _sig("ULT-14-L1", 1, geom="t1s1")
    assert abs((x[0].target - float(b["close"].iloc[x[0].bar_index])) - 1.0) < 1e-6              # t1s1
    assert _sig("ULT-14-Lc", 1, peers=False)[1] == []                       # no SPY context -> no signal
    assert _sig("ULT-14-Ld", 1, spy="falling_hour", day="2026-11-17")[1] == []   # SPY 60-min <= -0.40% -> blocked
    assert _sig("ULT-14-Le", -1, day="2026-11-16")[1] == []                 # a pop in a downtrend is not a long


def test_short_side_under_live_lab_strategy():
    b, sigs = _sig("ULT-14-S", -1, day="2026-11-13")
    assert 1 <= len(sigs) <= 2, sigs
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    assert _sig("ULT-14d-S", -1, peers=False, day="2026-11-10")[1] == []   # no SPY context -> no signal
    assert s.side == -1 and abs((s.stop - e) - 1.0) < 1e-6 and abs((e - s.target) - 0.5) < 1e-6
    assert _sig("ULT-14b-S", -1, spy="up", day="2026-11-12")[1] == []      # SPY since 09:50 > +0.20% -> blocked
    assert _sig("ULT-14c-S", 1, day="2026-11-11")[1] == []                 # a drop in an uptrend is not a short


def test_features_point_in_time():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    df = pd.DataFrame({"tod": tod, "close": c, "high": c * 1.001, "low": c * 0.999, "fromOpen": (c / c[0] - 1) * 100,
                       "gap": 0.0, "atr_d": 4.0, "spy_fo": rng.normal(0, 0.2, n), "rsi5": rng.uniform(20, 80, n),
                       "buyPressure": rng.normal(0, 1, n), "vwapDistPct": 0.0, "dist_hod_atr": 0.1,
                       "dist_lod_atr": 0.1, "dist_pdh_atr": 0.5, "dist_pdl_atr": 0.5})
    full = m.features(df)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("r3a", "di7", "atrp", "spy60", "spy950", "cost_r"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)
