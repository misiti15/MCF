"""Smoke test: ULT-33 module imports and runs under the live LabStrategy (context spy_fo, GEOM "S" with stop_price /
target_price) on both sides ("-S" = short), with the live allow-list (SYMBOLS from the calendar file, ULT-28 code) as
the event source; the stop is 1 Ru and the target K Ru (Ru = M x atr_d); fires only on a reaction-day name with a
holding gap; ADV floor $100M; features are point-in-time (truncation test); the e_rd column gates backtest rows;
cost_r scales with 1/m; the LMT price is VWAP + s x 0.05 x atr_d.
    pytest -q research/ultimate_1119/round4/ULT-33/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-33.py")
TZ = "America/New_York"


def _load(name="ult33"):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _day(sgn=1, gap=6.0, day="2026-11-18", fade=False, base=100.0):
    t = np.arange(390)
    o0 = base * (1 + gap / 100)
    drift = -sgn * 0.03 * t / 390 if fade else sgn * 0.03 * t / 390
    px = o0 * (1 + drift + 0.002 * np.sin(t / 7.0))
    op = np.r_[o0, px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    vol = 20000.0 + 5000 * (np.arange(390) % 7)
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01, "close": px,
                         "volume": vol}, index=idx)
    s = 600 * (1 + 0.002 * np.sin(t / 50))
    spyb = pd.DataFrame({"open": s, "high": s + 0.01, "low": s - 0.01, "close": s, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, base=100.0, atr=4.0, sym="ABCD", adv=2e8):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=atr, prev_close=base,
                           prev_high=base * 1.01, prev_low=base * 0.99, avg_dollar_volume=adv, peers=peers)


def _st(name, symbols):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    return LabStrategy(name, MOD, r_atr_frac=m.M, window=list(m.WINDOW), context=["spy_fo"], refire=True,
                       refire_cooldown=0, min_adv=100_000_000, geom=m.GEOM, time_stop_min=45, time_stop_min_r=99,
                       symbols=list(symbols))


def test_allow_list_from_calendar(tmp_path, monkeypatch):
    p = tmp_path / "cal.parquet"
    pd.DataFrame([("ABCD", "2026-11-17", "amc", 12.0), ("EFGH", "2026-11-18", "bmo", -5.0),
                  ("MNOP", "2026-11-18", "dmh", 3.0)], columns=["symbol", "date", "session", "surprise_pct"]).assign(
        date=lambda d: pd.to_datetime(d["date"])).to_parquet(p)
    monkeypatch.setenv("MCF_EARN_CAL", str(p))
    m = _load()
    assert m.B28.today_symbols("2026-11-18", "long", "any") == {"ABCD", "EFGH"}
    monkeypatch.setenv("MCF_EARN_CAL", str(tmp_path / "missing.parquet"))
    assert _load().B28.today_symbols("2026-11-18") == frozenset()          # fail safe


def test_long_and_short_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _LAB_FRAMES.clear()
    bars, peers = _day(1)
    st = _st("ULT-33", ["ABCD"])
    assert st.side == 1 and st.structural
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 09:50", tz=TZ) <= t <= pd.Timestamp("2026-11-18 12:30", tz=TZ), t
    entry = float(bars["close"].iloc[sigs[0].bar_index])
    assert abs((entry - sigs[0].stop) - m.M * 4.0) < 0.05
    assert abs((sigs[0].target - entry) - m.K * m.M * 4.0) < 0.05
    assert not st.eligible(_ctx(bars, peers, sym="ZZZZ"))                   # not a reaction-day name
    assert not st.eligible(_ctx(bars, peers, adv=5e7))                      # below the $100M tier
    _LAB_FRAMES.clear()
    b2, p2 = _day(1, day="2026-11-17", fade=True)
    assert _st("ULT-33", ["ABCD"]).signals(_ctx(b2, p2)) == []              # gap fading -> nothing
    _LAB_FRAMES.clear()
    b3, p3 = _day(1, gap=1.0, day="2026-11-16")
    assert _st("ULT-33", ["ABCD"]).signals(_ctx(b3, p3)) == []              # gap below 3% -> nothing
    _LAB_FRAMES.clear()
    b4, p4 = _day(-1, gap=-6.0, day="2026-11-13")
    st = _st("ULT-33-S", ["ABCD"])
    assert st.side == -1
    sg = st.signals(_ctx(b4, p4))
    assert 1 <= len(sg) <= 2 and sg[0].stop > sg[0].target


def test_features_point_in_time_cost_scaling_and_limit():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])
    df = pd.DataFrame({"tod": tod, "close": 50 * np.exp(np.cumsum(rng.normal(0, 0.004, n))), "gap": 6.0,
                       "atr_d": 2.0, "adv20": 2e8, "spy_fo": np.cumsum(rng.normal(0.02, 0.1, n)),
                       "vwapDistPct": rng.normal(0.3, 0.5, n), "fromOpen": rng.normal(0.5, 1, n),
                       "rsi5": rng.uniform(10, 95, n), "e_rd": True})
    full = m.features(df)
    for i in (5, 30, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("cost_r", "intake", "univ_long_ok"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, i)
        assert bool(m.signal(full, 1)[i]) == bool(m.signal(part, 1)[i])
    assert not m.signal(m.features(df.assign(e_rd=False)), 1).any()          # non-event rows never fire
    assert not m.signal(m.features(df.assign(adv20=5e7)), 1).any()           # liquidity tier
    a, b = m.features(df, m=0.25)["cost_r"], m.features(df, m=1.0)["cost_r"]
    assert np.allclose(a, 4 * b)
    L = m.limit_price(np.array([101.0]), np.array([1.0]), np.array([2.0]), 1)
    assert abs(L[0] - (100.0 + 0.1)) < 1e-9
    L = m.limit_price(np.array([99.0]), np.array([-1.0]), np.array([2.0]), -1)
    assert abs(L[0] - (100.0 - 0.1)) < 1e-9
