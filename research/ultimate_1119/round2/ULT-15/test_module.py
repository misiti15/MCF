"""Smoke test: ULT-15 CONFLUENCE module imports and runs under the live LabStrategy (context spy_fo) on both sides (side
from the setup name), fires on >= CONF counted triggers on its base, gives the 2u catastrophic stop (GEOM "S"), honours
the base tape rules, fails safe without SPY context, never fires as frozen (both bases failed the FIT gate: SIDES_ON
empty), and its features are point-in-time.
    pytest -q research/ultimate_1119/round2/ULT-15/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

MOD = Path(__file__).resolve().parents[2] / "modules" / "ULT-15.py"
TZ = "America/New_York"


def _load(path=MOD, name="ult15"):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture()
def open_mod(tmp_path):
    """A copy of the module with both sides switched on (the frozen file has SIDES_ON = ())."""
    src = MOD.read_text()
    assert "SIDES_ON = ()" in src
    p = tmp_path / "ULT-15-open.py"
    src = src.replace("SIDES_ON = ()", 'SIDES_ON = ("long", "short")')
    p.write_text(src.replace('LIQ = "L1"', 'LIQ = "L2"'))          # L2 cost cap 0.08 (synthetic cost_r 0.06)
    return str(p)


def _day(sgn=1, spy="with", day="2026-11-18", at=90, open_px=100.0):
    """Gentle drift with the side's trend up to minute `at`, then a sharp 5-minute counter-move of 5.5 points
    (long: a drop -> RSI14 collapse + >= 1 ATR below the open; short: a pop -> >= 1 ATR above the open), then flat."""
    px = [open_px]
    for k in range(1, 390):
        if k < at:
            step = sgn * (0.02 if k % 3 else -0.01)
        elif k < at + 5:
            step = -sgn * 5.5 / 5
        elif k < at + 7:
            step = sgn * 0.3                # a small turn back (RSI5 up-cross / roll-over)
        else:
            step = 0.0005 * (1 if k % 2 else -1)
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.05, "low": np.minimum(op, px) - 0.01,
                         "close": px, "volume": 20000.0}, index=idx)
    t = np.arange(390)
    up = 600 * (1 + 0.004 * t / 390)
    dn = 600 * (1 - 0.004 * t / 390)
    s = (up if sgn > 0 else dn) if spy == "with" else (dn if sgn > 0 else up)
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, prev_close):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0,
                           prev_close=prev_close, prev_high=prev_close + 1, prev_low=prev_close - 1,
                           avg_dollar_volume=1e9, peers=peers)


def _sig(path, name, sgn, spy="with", day="2026-11-18", peers=True):
    from mcf.strategies.setups import LabStrategy, _LAB_FRAMES
    _LAB_FRAMES.clear()
    b, p = _day(sgn, spy=spy, day=day)
    prev = 100.0 if sgn > 0 else 102.5          # short base needs gap <= -1.0% (open 100 vs prev 102.5 = -2.4%)
    st = LabStrategy(name, path, window=[1030, 1500] if sgn > 0 else [1100, 1500], context=["spy_fo"], refire=True,
                     refire_cooldown=0, min_adv=50_000_000, geom="S")
    return b, st.signals(_ctx(b, p if peers else None, prev))


def test_long_side_under_live_lab_strategy(open_mod):
    b, sigs = _sig(open_mod, "ULT-15-L", 1, day="2026-11-19")
    assert 1 <= len(sigs) <= 2, sigs
    t = b.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-19 11:00", tz=TZ) <= t <= pd.Timestamp("2026-11-19 11:15", tz=TZ), t
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    assert s.side == 1 and s.target is None and abs((e - s.stop) - 2.0) < 1e-6        # 2u catastrophic stop, u = 1
    assert _sig(open_mod, "ULT-15-La", 1, peers=False, day="2026-11-17")[1] == []     # no SPY context -> no signal
    assert _sig(open_mod, "ULT-15-Lb", 1, spy="against", day="2026-11-16")[1] == []   # SPY down -> base BL closed


def test_short_side_under_live_lab_strategy(open_mod):
    b, sigs = _sig(open_mod, "ULT-15-S", -1, day="2026-11-13")
    assert 1 <= len(sigs) <= 2, sigs
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    assert s.side == -1 and s.target is None and abs((s.stop - e) - 2.0) < 1e-6
    assert _sig(open_mod, "ULT-15-Sa", -1, spy="against", day="2026-11-12")[1] == []  # SPY up -> base BS closed


def test_frozen_module_never_fires():
    b, sigs = _sig(str(MOD), "ULT-15-L", 1, day="2026-11-11")
    assert sigs == []
    b, sigs = _sig(str(MOD), "ULT-15-S", -1, day="2026-11-10")
    assert sigs == []


def test_features_point_in_time():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
    df = pd.DataFrame({"tod": tod, "close": c, "fromOpen": (c / c[0] - 1) * 100, "gap": -2.0, "atr_d": 4.0,
                       "spy_fo": rng.normal(0, 0.2, n), "rsi": rng.uniform(20, 70, n), "rsi5": rng.uniform(10, 95, n),
                       "buyPressure": rng.normal(0, 1, n), "dist_hod_atr": rng.uniform(0, 2, n),
                       "dist_lod_atr": rng.uniform(0, 2, n), "sma20_dist_pct": rng.normal(0, 2, n),
                       "upper_wick": rng.uniform(0, 0.5, n)})
    full = m.features(df)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("spy_r30", "foa", "n_long", "n_short", "TL1", "TL2", "TS2", "cost_r"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)
    assert full["n_long"].max() >= 1 and full["n_short"].max() >= 1
