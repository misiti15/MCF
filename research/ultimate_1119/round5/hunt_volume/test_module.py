"""Smoke test: H5V module imports and runs under the live LabStrategy as one YAML entry per leg (leg from the setup
name suffix), fires leg K (long) on a one-bar volume-climax shock in a liquid ETF with t1s1 levels, takes the side
per leg (S/C/X short), honours the allow-lists, the universal SPY long filter and fails safe without SPY context;
every leg trigger fires on a hand-made row and not on its negation; features are point-in-time.
    pytest -q research/ultimate_1119/round5/hunt_volume/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parent / "H5V.py")
TZ = "America/New_York"


def _load(name="h5v"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bars(steps, day, vol=None):
    px = [100.0]
    for k in range(1, 390):
        px.append(px[-1] + steps(k))
    px = np.array(px)
    op = np.r_[px[0], px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    v = np.array([vol(k) if vol else 20000.0 for k in range(390)], float)
    return pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.005, "low": np.minimum(op, px) - 0.005,
                         "close": px, "volume": v}, index=idx)


def _spy(idx, path="flat"):
    t = np.arange(390)
    if path == "flat":
        s = 600 + 0.01 * np.sin(t)
    else:   # slides to ~-0.45% and keeps falling (inside the -0.30..-0.75 band of the long filter)
        s = 600 * (1 - 0.005 * np.clip((t - 140) / 100, 0, 1.2))   # ~-0.375% and falling at 13:05
    return {"SPY": pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)}


def _shock_day(day="2026-11-18"):
    """Quiet ETF, then a -4 drop (1 daily ATR) over 5 minutes at 13:00-13:05 on 6x volume (vol_climax needs 20 bars)."""
    st = lambda k: -0.8 if 210 <= k < 215 else 0.002 * (1 if k % 2 else -1)
    vol = lambda k: 120000.0 if 210 <= k < 215 else 20000.0
    return _bars(st, day, vol)


def _ctx(bars, peers, sym, adv=2e9):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=adv, peers=peers)


def _st(name, leg):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    return LabStrategy(name, MOD, window=list(m.WIN[leg]), context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=95e6, geom=m.P[leg]["geom"], symbols="module")


def test_leg_and_side_from_setup_name():
    for lg, side in (("F", 1), ("S", -1), ("C", -1), ("X", -1), ("K", 1), ("V", 1), ("Q", 1)):
        st = _st(f"H5V-{lg}", lg)
        assert st.mod.LEG == lg and st.side == side
    assert _load("plain").LEG == "F"


def test_leg_K_runs_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    b = _shock_day()
    st = _st("H5V-x-K", "K")
    sigs = st.signals(_ctx(b, _spy(b.index), "QQQ"))
    assert 1 <= len(sigs) <= 2
    t = b.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 13:00", tz=TZ) <= t <= pd.Timestamp("2026-11-18 13:10", tz=TZ), t
    s = sigs[0]
    e = float(b["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((e - s.stop) - 1.0) < 1e-6 and abs((s.target - e) - 1.0) < 1e-6      # t1s1, u = 1
    assert not st.eligible(_ctx(b, _spy(b.index), "AAPL"))                                         # EQB allow-list
    _LAB_FRAMES.clear()
    b2 = _shock_day("2026-11-17")       # a fresh bars object (the lab frame / context caches key on it)
    assert _st("H5V-y-K", "K").signals(_ctx(b2, _spy(b2.index, "down"), "QQQ")) == []               # SPY long filter
    _LAB_FRAMES.clear()
    assert _st("H5V-z-K", "K").signals(_ctx(b, None, "QQQ")) == []                                 # no SPY -> none


def test_short_leg_runs_and_allow_list():
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    b = _shock_day()
    st = _st("H5V-x-S", "S")
    sigs = st.signals(_ctx(b, _spy(b.index), "NVDA"))
    assert all(s.side == -1 for s in sigs)
    assert not st.eligible(_ctx(b, _spy(b.index), "SPY"))                                          # funds excluded
    assert st.eligible(_ctx(b, _spy(b.index), "NVDA"))


def _row(**kw):
    m = _load()
    n = 1
    base = {"tod": np.array([1105.0]), "close": np.array([100.0]), "adv": np.array([5e9]), "rsi": np.array([50.0]),
            "rsi_prev": np.array([50.0]), "fromOpen": np.array([0.0]), "fo_thr": np.array([1.0]),
            "bp": np.array([0.0]), "vc": np.array([1.0]), "lw": np.array([0.0]), "ret1": np.array([0.0]),
            "ret3": np.array([0.0]), "ret12": np.array([0.0]), "di7": np.array([0.0]), "atrp_ind": np.array([5.0]),
            "atrp": np.array([3.0]), "cost_r": np.array([0.05]), "intake": np.array([True]),
            "univ_ok": np.array([True]), "spy_fo": np.array([0.0]), "spy_r30": np.array([0.0])}
    g = {k: np.array([False]) for k in ("EQB", "LEV", "W", "SECT", "STOCKS")}
    for k, v in kw.items():
        if k in g:
            g[k] = np.array([v])
        else:
            base[k] = np.array([v], dtype=float if not isinstance(v, bool) else bool)
    base["g"] = g
    return m, base


def test_each_leg_trigger_and_negation():
    cases = {
        "F": (dict(EQB=True, rsi_prev=55, rsi=33, fromOpen=-1.5), dict(rsi=40)),
        "S": (dict(STOCKS=True, rsi_prev=45, rsi=72, fromOpen=1.5, bp=-1), dict(bp=1)),
        "C": (dict(STOCKS=True, rsi_prev=55, rsi=28, fromOpen=-1.5, bp=-1, spy_fo=-0.2), dict(spy_fo=0.2)),
        "X": (dict(W=True, tod=1410, ret3=0.9, di7=0, ret12=0.5, atrp_ind=5.0), dict(ret3=0.5)),
        "K": (dict(EQB=True, ret1=-0.9, vc=3.0), dict(vc=1.5)),
        "V": (dict(STOCKS=True, ret1=-0.5, vc=3.5, lw=0.5), dict(lw=0.1)),
        "Q": (dict(SECT=True, fromOpen=-2.0, spy_fo=0.0, rsi=30), dict(rsi=40)),
    }
    for leg, (hit, neg) in cases.items():
        m, r = _row(**hit)
        assert m.leg_mask(r, leg)[0], leg
        m, r = _row(**{**hit, **neg})
        assert not m.leg_mask(r, leg)[0], (leg, "negation")
        m, r = _row(**{**hit, "cost_r": 0.2})
        assert not m.leg_mask(r, leg)[0], (leg, "cost cap")


def test_features_point_in_time():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    df = pd.DataFrame({"tod": tod, "open": np.r_[c[0], c[:-1]], "high": c * 1.002, "low": c * 0.998, "close": c,
                       "volume": 1e5, "fromOpen": (c / c[0] - 1) * 100, "gap": 0.0, "atr_d": 4.0,
                       "spy_fo": rng.normal(0, 0.2, n), "rsi": rng.uniform(20, 80, n), "buyPressure": rng.normal(0, 1, n),
                       "vol_climax": rng.uniform(0.5, 4, n), "lower_wick": rng.uniform(0, 1, n)})
    full = m.features(df)
    for i in (20, 40, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("rsi_prev", "cost_r", "spy_r30", "univ_ok", "fo_thr", "ret1", "ret3", "ret12", "di7", "atrp_ind"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-6, (k, i)
        assert bool(m.mask(df)[i]) == bool(m.mask(df.iloc[: i + 1].reset_index(drop=True))[i])


def test_backtest_has_no_forbidden_columns():
    src = (Path(__file__).resolve().parent / "hunt.py").read_text()
    assert '"win_", "r_long", "r_short"' in src and "heat" in src and "breadth" in src
