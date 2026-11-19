"""Smoke test: ULT-27 module builds a pre-open profile from 1-minute history (prior sessions only), runs under the live
LabStrategy (context spy_fo, GEOM "S" 2u stop) on both sides (two entries, one file; "-S" = short), fires only at the
listed slot, never lists a LEV fund, caps listings at 2 per symbol-session, fails safe without SPY context / profile,
and its scores / features are point-in-time (truncation tests).
    pytest -q research/ultimate_1119/round3/ULT-27/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-27.py")
TZ = "America/New_York"


def _load(name="ult27", **kw):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _bars(day, drift_1000=0.0, base=100.0, seed=0):
    """390 1-minute bars; a small random walk plus `drift_1000` (fraction) spread over 10:00-10:30."""
    rng = np.random.default_rng(seed)
    t = np.arange(390)
    step = rng.normal(0, 0.0003, 390)
    step[(t >= 30) & (t < 60)] += drift_1000 / 30
    px = base * np.exp(np.cumsum(step))
    op = np.r_[base, px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    return pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01,
                         "close": px, "volume": 50000.0}, index=idx)


def _spy(day, trend=0.002):
    t = np.arange(390)
    s = 600 * (1 + trend * t / 390)
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    return pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)


DAYS = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2026-10-01", periods=26)]
TODAY = DAYS[-1]


def _profile(m, tmp_path, syms=("UPUP", "DNDN", "FLAT", "SQQQ"), etb=("DNDN", "FLAT", "UPUP")):
    drift = {"UPUP": 0.004, "DNDN": -0.004, "FLAT": 0.0, "SQQQ": 0.008}
    xn = {}
    for k, s in enumerate(syms):
        ret = pd.concat([m.interval_returns(_bars(d, drift[s], seed=k * 100 + i)) for i, d in enumerate(DAYS[:-1])])
        xn[s] = ret * 100 / 2.0          # ATR% 2
    meta = pd.DataFrame({"adv20": 5e8, "prev_close": 100.0, "atr_d": 10.0}, index=list(syms))
    m.PROFILE_PATH = tmp_path / "ULT-27_profile.json"
    return m.build_profile(TODAY, xn, meta, set(etb), L_=10, N_=1, write=True)


def _ctx(bars, peers, sym, atr=10.0):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=atr, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=5e8, peers=peers)


def _st(name, tmp_path):
    from mcf.strategies.setups import LabStrategy
    st = LabStrategy(name, MOD, r_atr_frac=0.25, window=[1000, 1500], context=["spy_fo"], refire=True,
                     refire_cooldown=0, min_adv=200_000_000, geom="S", time_stop_min=30, time_stop_min_r=99)
    st.mod.PROFILE_PATH = tmp_path / "ULT-27_profile.json"
    st.mod.N = 1
    return st


def test_profile_lists(tmp_path):
    m = _load()
    prof = _profile(m, tmp_path)[TODAY]
    assert prof["1000"]["L"] == ["UPUP"] and prof["1000"]["S"] == ["DNDN"], prof["1000"]
    assert all("SQQQ" not in v["L"] + v["S"] for v in prof.values())            # LEV never listed
    cnt = {}
    for v in prof.values():
        for s in v["L"] + v["S"]:
            cnt[s] = cnt.get(s, 0) + 1
    assert max(cnt.values()) <= 2                                                 # listing cap per symbol-session


def test_long_and_short_under_live_lab_strategy(tmp_path):
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _profile(m, tmp_path)
    peers = {"SPY": _spy(TODAY)}
    for sym, name, sgn in (("UPUP", "ULT-27", 1), ("DNDN", "ULT-27-S", -1)):
        _LAB_FRAMES.clear()
        bars = _bars(TODAY, 0.0, seed=7 if sgn > 0 else 8)
        st = _st(name, tmp_path)
        assert st.side == sgn
        sigs = st.signals(_ctx(bars, peers, sym))
        assert len(sigs) >= 1, (sym, sigs)
        assert bars.index[sigs[0].bar_index] == pd.Timestamp(f"{TODAY} 09:59", tz=TZ)   # the 10:00 decision bar
        entry = float(bars["close"].iloc[sigs[0].bar_index])
        assert abs(sgn * (entry - sigs[0].stop) - 2 * 0.25 * 10.0) < 1e-6
        _LAB_FRAMES.clear()
        assert _st(name, tmp_path).signals(_ctx(bars, None, sym)) == []          # no SPY context -> nothing
    _LAB_FRAMES.clear()
    st = _st("ULT-27", tmp_path)
    bars = _bars(TODAY, seed=9)
    t10 = pd.Timestamp(f"{TODAY} 09:59", tz=TZ)
    assert all(bars.index[s.bar_index] != t10 for s in st.signals(_ctx(bars, peers, "FLAT")))   # unlisted at 10:00
    st.mod.PROFILE_PATH = tmp_path / "missing.json"
    _LAB_FRAMES.clear()
    assert st.signals(_ctx(_bars(TODAY, seed=7), peers, "UPUP")) == []           # no profile -> nothing


def test_scores_point_in_time():
    m = _load()
    rng = np.random.default_rng(1)
    x = pd.DataFrame(rng.normal(0, 1, (40, 6)), columns=list(m.SLOTS))
    x.iloc[5:9] = np.nan
    full = m.scores(x, 10)
    for i in (12, 25, 39):
        part = m.scores(x.iloc[: i + 1].copy(), 10)
        assert np.allclose(full.iloc[i].to_numpy(), part.iloc[i].to_numpy(), equal_nan=True)
        y = x.iloc[: i + 1].copy()
        y.iloc[i] = 99.0                                                          # today's own interval never used
        assert np.allclose(m.scores(y, 10).iloc[i].to_numpy(), full.iloc[i].to_numpy(), equal_nan=True)
    assert full.iloc[:7].isna().all().all()                                       # < 0.7L valid days -> NaN


def test_features_point_in_time_and_filters():
    m = _load()
    mins = np.arange(m._m(950), m._m(1500) + 1, 5)
    tod = (mins // 60) * 100 + mins % 60
    n = len(tod)
    rng = np.random.default_rng(2)
    df = pd.DataFrame({"tod": tod, "close": 50 + rng.normal(0, 0.1, n), "atr_d": 2.0, "gap": 0.2,
                       "rsi5": rng.uniform(10, 90, n), "spy_fo": np.cumsum(rng.normal(-0.05, 0.1, n))})
    full = m.features(df)
    i1000 = int(np.flatnonzero(tod == 1000)[0])
    assert abs(full["spy_r30"][i1000] - df.spy_fo[i1000]) < 1e-9                  # 30 min back = the 09:30 open
    for i in (i1000, 20, n - 1):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("spy_r30", "cost_r"):
            assert abs(full[k][i] - part[k][i]) < 1e-9 or (np.isnan(full[k][i]) and np.isnan(part[k][i]))
        for sg in (1, -1):
            assert bool(m.day_ok(full, sg)[i]) == bool(m.day_ok(part, sg)[i])
    r = {"close": np.array([50.0, 50, 50, 8]), "cost_r": np.array([0.02, 0.02, 0.02, 0.02]),
         "gap": np.array([0.0, 0.6, 0.0, 0.0]), "atr_d": np.full(4, 2.0), "rsi5": np.array([50.0, 50, 20, 50]),
         "spy_fo": np.array([-0.5, 0.1, 0.1, 0.1]), "spy_r30": np.array([-0.1, 0.1, 0.1, 0.1])}
    assert list(m.day_ok(r, 1)) == [False, True, True, False]                    # falling-tape long / $8 name
    assert list(m.day_ok(r, -1)) == [True, False, False, False]                  # gap-up / RSI5 < 25 short / $8
