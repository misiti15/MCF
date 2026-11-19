"""Smoke test: ULT-23 module imports and runs under the live LabStrategy (context spy_fo), fires on a ONE-bar RSI(14)
collapse with buy pressure, gives t1s1 / t05s1 levels, does not fire on a slow slide, honours the universal SPY long
filter, the ATR-scaled from-open threshold and the universe flags (Q / M / QM, price >= $20 for mega caps), fails safe
without SPY context, and its features are point-in-time.
    pytest -q research/ultimate_1119/round3/ULT-23/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-23.py")


def _load(**kw):
    spec = importlib.util.spec_from_file_location("ult23", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _day(slide_min=5, spy="flat", day="2026-11-18", drop=2.5):
    px = [100.0]
    for k in range(1, 390):
        if k < 90:
            step = 0.01 if k % 3 else -0.005
        elif k < 90 + slide_min:
            step = -drop / slide_min
        else:
            step = 0.0005 * (1 if k % 2 else -1)
        px.append(px[-1] + step)
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01, "close": px,
                         "volume": 20000.0}, index=idx)
    t = np.arange(390)
    s = 600 + 0.01 * np.sin(t) if spy == "flat" else 600 * (1 - 0.005 * np.clip(t / 95, 0, 2))
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, atr=4.0):
    return SimpleNamespace(symbol="SPY", date=bars.index[0].date(), bars=bars, prior5=None, atr=atr, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=2e9, peers=peers)


def _st(name, geom="t1s1", univ="Q"):
    from mcf.strategies.setups import LabStrategy
    s = LabStrategy(name, MOD, window=[1015, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                    min_adv=30_000_000, geom=geom)
    s.mod.UNIV = univ
    return s


def test_module_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES

    _LAB_FRAMES.clear()
    bars, peers = _day()
    sigs = _st("ULT-23").signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2
    tz = "America/New_York"
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 11:00", tz=tz) <= t <= pd.Timestamp("2026-11-18 11:10", tz=tz), t
    s = sigs[0]
    entry = float(bars["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((entry - s.stop) - 1.0) < 1e-6 and abs((s.target - entry) - 1.0) < 1e-6   # t1s1, u = 1
    _LAB_FRAMES.clear()
    h = _st("ULT-23H", geom="t05s1").signals(_ctx(bars, peers))[0]
    e2 = float(bars["close"].iloc[h.bar_index])
    assert abs((e2 - h.stop) - 1.0) < 1e-6 and abs((h.target - e2) - 0.5) < 1e-6
    _LAB_FRAMES.clear()
    assert _st("ULT-23c").signals(_ctx(bars, None)) == []          # no SPY context -> no signal
    _LAB_FRAMES.clear()
    b2, p2 = _day(spy="band_falling", day="2026-11-17")
    assert _st("ULT-23d").signals(_ctx(b2, p2)) == []              # universal long filter
    _LAB_FRAMES.clear()
    b3, p3 = _day(slide_min=25, day="2026-11-16")
    assert _st("ULT-23e").signals(_ctx(b3, p3)) == []              # slow slide: no one-bar collapse
    _LAB_FRAMES.clear()
    assert len(_st("ULT-23m", univ="M").signals(_ctx(bars, peers))) >= 1   # M live: price ~ $98 >= $20


def test_atr_scaled_from_open_and_universe_flags():
    m = _load(UNIV="QM")
    base = {"tod": [1100, 1105], "spy_fo": [0.1, 0.1], "date": "d", "gap": 0.0, "rsi": [60.0, 30.0],
            "buyPressure": 1.0, "close": 50.0}
    # atr_d 1.0 on $50 = 2% -> threshold -min(1, 0.6) = -0.6%: fromOpen -0.7 fires, -0.5 does not
    for fo, ok in ((-0.7, True), (-0.5, False)):
        df = pd.DataFrame({**base, "atr_d": 1.0, "fromOpen": fo, "symbol": "IWM", "adv20": 5e7})
        r = m.features(df)
        assert bool(m.trigger(r, 35.0)[1]) == ok
    # universe: EQB ETF with ADV 50M -> Q; a mega stock with ADV 2B -> M; price $15 stock -> not M; fund not M
    df = pd.DataFrame({"tod": [1105] * 4, "spy_fo": 0.1, "date": "d", "gap": 0.0, "rsi": 30.0, "buyPressure": 1.0,
                       "close": [50.0, 150.0, 15.0, 500.0], "atr_d": 5.0, "fromOpen": -2.0,
                       "symbol": ["IWM", "NVDA", "NVDA", "GLD"], "adv20": [5e7, 2e9, 2e9, 5e9]})
    r = m.features(df)
    assert list(r["is_q"]) == [True, False, False, False]
    assert list(r["is_m"]) == [False, True, False, False]
    assert "NVDA" in m.STOCKS and "IWM" in m.EQB and "GLD" in m.FUNDS


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
        for k in ("rsi_prev", "cost_r", "spy_r30", "univ_ok", "fo_thr"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)
        assert bool(m.mask(df)[i]) == bool(m.mask(df.iloc[: i + 1].reset_index(drop=True))[i])
