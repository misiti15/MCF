"""Smoke test: the ULT-10 book module loads under the live LabStrategy for every leg (leg / T / set from the setup
name), routes by the point-in-time SPY regime (the ULT-07 leg fires on an afternoon dip only while SPY is >= +T from
its open, not on a flat tape), and fails safe without SPY context.
    pytest -q research/ultimate_1119/ULT-10-regime-switch-book/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[1] / "modules" / "ULT-10-regime-switch-book.py")
TZ = "America/New_York"


def _day(spy_up=0.0, day="2026-11-18"):
    # same 1-minute path as the ULT-07 smoke test: slow up-drift to 13:35, sharp low-volume slide 13:35-13:55,
    # steady rebound from 13:55 (RSI5 turns up through 30 with positive 19-bar buy pressure)
    px, vol = [100.0], [20000.0]
    for k in range(1, 390):
        step, v = (0.004, 20000.0) if k < 245 else ((-0.30, 2000.0) if k < 265 else (0.02, 20000.0))
        px.append(px[-1] + step); vol.append(v)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01,
                         "close": px, "volume": vol}, index=idx)
    spy = 600 * (1 + spy_up * np.clip(np.arange(390) / 120, 0, 1))      # SPY reaches +spy_up by 11:30, then holds
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _st(name, window, geom=None, context=("spy_fo",)):
    from mcf.strategies import lab_context
    from mcf.strategies.setups import LabStrategy
    lab_context._CACHE.clear()       # the context table is cached per poll (symbol count + latest bar time)
    return LabStrategy(name, MOD, window=list(window), context=list(context) if context else None, refire=True,
                       refire_cooldown=0, min_adv=20_000_000, geom=geom)


def test_every_leg_loads_with_its_side_and_geometry():
    from mcf.strategies.setups import _LAB_FRAMES
    bars, peers = _day(0.01)
    for st_set in ("a", "b"):
        for t in ("30", "50"):
            for leg in ("01", "02", "03", "04", "05", "06", "07", "08", "09"):
                _LAB_FRAMES.clear()
                s = _st(f"ULT-10-T{t}{st_set}-L{leg}", (950, 1500))
                m = s.mod
                assert m.LEG == leg and m.SET == st_set and abs(m.T_PCT - int(t) / 100) < 1e-12
                assert s.side == (1 if m.LEG_SIDE[leg] == "long" else -1)
                assert s.geom == m.GEOM and m.HOLD <= 45
                s.signals(_ctx(bars, peers))          # runs end to end on a live-style frame


def test_routes_by_regime_and_fails_safe():
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    bars, peers = _day(0.01)                           # SPY +1% from its open: "up" regime -> ULT-07 leg active
    s = _st("ULT-10-T50b-L07", (1400, 1500))
    sig = s.signals(_ctx(bars, peers))
    assert len(sig) == 1 and sig[0].side == 1
    t = bars.index[sig[0].bar_index]
    assert pd.Timestamp("2026-11-18 13:55", tz=TZ) <= t <= pd.Timestamp("2026-11-18 15:00", tz=TZ)
    e = float(bars["close"].iloc[sig[0].bar_index])
    assert abs((e - sig[0].stop) - 1.0) < 1e-6 and abs((sig[0].target - e) - 0.5) < 1e-6    # t05s1, R = 1
    _LAB_FRAMES.clear()
    flat_bars, flat_peers = _day(0.0)                  # flat tape: same name, same dip, but routed to 01/06/08
    assert _st("ULT-10-T50b-L07", (1400, 1500)).signals(_ctx(flat_bars, flat_peers)) == []
    _LAB_FRAMES.clear()
    assert _st("ULT-10-T50b-L07", (1400, 1500), context=None).signals(_ctx(bars, peers)) == []


def test_regime_labels():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ult10_t", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    tod = [950, 1000, 1020, 1030, 1040]
    df = pd.DataFrame({"tod": tod, "spy_fo": [0.0, -0.6, -0.2, 0.6, 0.1]},
                      index=pd.DatetimeIndex([pd.Timestamp(f"2026-11-18 {t // 100:02d}:{t % 100:02d}") for t in tod]))
    r = m.regime(df, 0.50)
    # 09:50 flat; 10:00 down (no 30-min ref yet); 10:20 vs 09:50 -0.2% -> flat; 10:30 vs 10:00 +1.2% -> up;
    # 10:40 vs 10:10 (missing) -> not flush, +0.1% -> flat
    assert list(r) == ["flat", "down", "flat", "up", "flat"]
    df2 = pd.DataFrame({"tod": [1000, 1030], "spy_fo": [0.4, -0.3]},
                       index=pd.DatetimeIndex([pd.Timestamp("2026-11-18 10:00"), pd.Timestamp("2026-11-18 10:30")]))
    assert list(m.regime(df2, 0.50)) == ["flat", "flush"]          # -0.7% in 30 min -> flush (before 'down')
