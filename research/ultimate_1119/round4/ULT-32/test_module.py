"""Smoke test: ULT-32 module imports and runs under the live LabStrategy as three YAML entries (leg from the setup
name suffix -E / -M / -D), fires leg E on a sharp 15-min dip after a rising hour in a high-ATR basket ETF at 14:00-15:00
(t05s1 levels), leg M on a one-bar RSI(14) collapse in a large stock (t1s1 levels), honours the allow-lists, the
universal SPY long filter, fails safe without SPY context, and its features are point-in-time.
    pytest -q research/ultimate_1119/round4/ULT-32/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-32.py")
TZ = "America/New_York"


def _load(name="u32"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bars(steps, day):
    px = [100.0]
    for k in range(1, 390):
        px.append(px[-1] + steps(k))
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    return pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.005, "low": np.minimum(op, px) - 0.005,
                         "close": px, "volume": 20000.0}, index=idx)


def _spy(idx, path="flat"):
    t = np.arange(390)
    if path == "flat":
        s = 600 + 0.01 * np.sin(t)
    elif path == "pm_down":   # SPY slides to ~-0.45% by 14:20 and keeps falling (inside the -0.30..-0.75 band)
        s = 600 * (1 - 0.005 * np.clip((t - 200) / 100, 0, 1.2))
    else:
        s = 600 * (1 - 0.005 * np.clip(t / 95, 0, 2))
    return {"SPY": pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)}


def _etf_day(day="2026-11-18"):     # rally 13:30-14:05 (+2%), dip 14:05-14:20 (-0.92%)
    return _bars(lambda k: 2.0 / 35 if 240 <= k < 275 else (-0.92 / 15 if 275 <= k < 290 else 0.0005 * (1 if k % 2 else -1)), day)


def _stock_day(day="2026-11-18", slide=5):   # gentle rise to 11:00, then a 2.5 drop over `slide` minutes
    def st(k):
        if k < 90:
            return 0.01 if k % 3 else -0.005
        if k < 90 + slide:
            return -2.5 / slide
        return 0.0005 * (1 if k % 2 else -1)
    return _bars(st, day)


def _ctx(bars, peers, sym, adv=2e9):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=adv, peers=peers)


def _st(name, leg):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    return LabStrategy(name, MOD, window=list(m.WIN[leg]), context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=95e6 if leg == "E" else m.ADV_MD, geom=m.GEOMS[leg], symbols="module")


def test_leg_from_setup_name():
    assert _st("ULT-32-FLOWDIP-E", "E").mod.LEG == "E"
    assert _st("ULT-32-FLOWDIP-M", "M").mod.LEG == "M"
    assert _st("ULT-32-FLOWDIP-D", "D").mod.LEG == "D"
    assert _load("plain").LEG == "EMD"


def test_leg_E_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    b = _etf_day()
    st = _st("ULT-32-x-E", "E")
    sigs = st.signals(_ctx(b, _spy(b.index), "SOXL"))
    assert len(sigs) >= 1
    t = b.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 14:10", tz=TZ) <= t <= pd.Timestamp("2026-11-18 14:30", tz=TZ), t
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((e - s.stop) - 1.0) < 1e-6 and abs((s.target - e) - 0.5) < 1e-6     # t05s1, u = 1
    assert not st.eligible(_ctx(b, _spy(b.index), "AAPL"))                                        # W allow-list
    _LAB_FRAMES.clear()
    b2 = _etf_day("2026-11-17")
    assert _st("ULT-32-y-E", "E").signals(_ctx(b2, _spy(b2.index, "pm_down"), "SOXL")) == []         # SPY long filter
    _LAB_FRAMES.clear()
    assert _st("ULT-32-z-E", "E").signals(_ctx(b, None, "SOXL")) == []                            # no SPY -> none


def test_leg_M_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    b = _stock_day()
    st = _st("ULT-32-x-M", "M")
    sigs = st.signals(_ctx(b, _spy(b.index), "NVDA"))
    assert 1 <= len(sigs) <= 2
    t = b.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 11:00", tz=TZ) <= t <= pd.Timestamp("2026-11-18 11:10", tz=TZ), t
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    assert abs((e - s.stop) - 1.0) < 1e-6 and abs((s.target - e) - 1.0) < 1e-6                     # t1s1
    assert not st.eligible(_ctx(b, _spy(b.index), "SPY"))                                         # funds excluded
    assert not st.eligible(_ctx(b, _spy(b.index), "NVDA", adv=1e8))                               # min_adv
    _LAB_FRAMES.clear()
    b3 = _stock_day("2026-11-16", slide=25)
    assert _st("ULT-32-y-M", "M").signals(_ctx(b3, _spy(b3.index), "NVDA")) == []                 # slow slide


def test_universe_flags_and_triggers():
    m = _load()
    df = pd.DataFrame({"tod": [1405] * 4, "spy_fo": 0.1, "date": "d", "gap": 0.0, "rsi": 30.0, "buyPressure": 1.0,
                       "close": [50.0, 150.0, 15.0, 500.0], "atr_d": 5.0, "fromOpen": -2.0,
                       "symbol": ["SOXL", "NVDA", "NVDA", "GLD"], "adv20": [5e8, 2e9, 2e9, 5e9]})
    is_w, is_md = m.universe_flags(df, df.close.to_numpy())
    assert list(is_w) == [True, False, False, False]
    assert list(is_md) == [False, True, False, False]
    _, md2 = m.universe_flags(df, df.close.to_numpy(), adv_md=3e9)
    assert not md2.any()


def test_features_point_in_time():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    df = pd.DataFrame({"tod": tod, "open": np.r_[c[0], c[:-1]], "high": c * 1.002, "low": c * 0.998, "close": c,
                       "volume": 1e5, "fromOpen": (c / c[0] - 1) * 100, "gap": 0.0, "atr_d": 4.0,
                       "spy_fo": rng.normal(0, 0.2, n), "rsi": rng.uniform(20, 80, n), "buyPressure": rng.normal(0, 1, n)})
    full = m.features(df)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("rsi_prev", "cost_r", "spy_r30", "univ_ok", "fo_thr", "ret3", "ret12", "di7", "atrp_ind"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)
        assert bool(m.mask(df)[i]) == bool(m.mask(df.iloc[: i + 1].reset_index(drop=True))[i])


def test_backtest_has_no_forbidden_columns():
    src = (Path(__file__).resolve().parent / "bt.py").read_text()
    assert '"win_", "r_long", "r_short"' in src and "heat" in src
