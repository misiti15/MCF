"""Smoke test: ULT-35 module imports and runs under the live LabStrategy (context spy_fo) on both sides ("-S" = short),
with the live allow-list (SYMBOLS from the calendar file) as the event source; fires on a reaction-day gap-down that
reclaims VWAP and the open (long) / a gap-up that fails (short), not on a holding gap, a small gap or a non-event name;
fires only on the FIRST bar of the failure; features are point-in-time (truncation test); the e_rd column gates the
backtest rows; mutually exclusive with ULT-28's HOLD rule on every bar.
    pytest -q research/ultimate_1119/round4/ULT-35/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MODS = Path(__file__).resolve().parents[2] / "modules"
MOD = str(MODS / "ULT-35.py")
TZ = "America/New_York"


def _load(name="ult35", path=MOD):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _day(gap=-6.0, day="2026-11-18", reclaim=True, base=100.0, osc=0.0005):
    """Gap of `gap`%; price first extends with the gap until ~10:30, then (reclaim) reverses through open/VWAP."""
    t = np.arange(390)
    o0 = base * (1 + gap / 100)
    s = np.sign(gap)
    ext = np.where(t < 60, s * 0.012 * t / 60, s * 0.012)
    rev = np.where(t < 60, 0.0, -s * 0.045 * np.minimum(t - 60, 150) / 150) if reclaim else 0.0
    px = o0 * (1 + ext + rev + osc * np.sin(t / 5.0))
    op = np.r_[o0, px[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=TZ)
    vol = 20000.0 + 5000 * (np.arange(390) % 7)
    bars = pd.DataFrame({"open": op, "high": np.maximum(op, px) + 0.01, "low": np.minimum(op, px) - 0.01, "close": px,
                         "volume": vol}, index=idx)
    sp = 600 * (1 + 0.002 * np.sin(t / 50))
    spyb = pd.DataFrame({"open": sp, "high": sp + 0.01, "low": sp - 0.01, "close": sp, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, base=100.0, atr=4.0, sym="ABCD"):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=atr, prev_close=base,
                           prev_high=base * 1.01, prev_low=base * 0.99, avg_dollar_volume=2e8, peers=peers)


def _st(name, symbols):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    return LabStrategy(name, MOD, r_atr_frac=0.25, window=list(m.WINDOW), context=["spy_fo"], refire=True,
                       refire_cooldown=0, min_adv=30_000_000, geom=m.GEOM, time_stop_min=45, time_stop_min_r=99,
                       symbols=list(symbols))


def test_calendar_and_allow_list(tmp_path, monkeypatch):
    p = tmp_path / "cal.parquet"
    pd.DataFrame([("ABCD", "2026-11-17", "amc", 12.0), ("EFGH", "2026-11-18", "bmo", -5.0),
                  ("IJKL", "2026-11-18", "amc", 3.0), ("MNOP", "2026-11-18", "dmh", 3.0)],
                 columns=["symbol", "date", "session", "surprise_pct"]).assign(
        date=lambda d: pd.to_datetime(d["date"])).to_parquet(p)
    monkeypatch.setenv("MCF_EARN_CAL", str(p))
    m = _load()
    assert m.today_symbols("2026-11-18") == {"ABCD", "EFGH"}
    assert m.today_symbols("2026-11-19") == {"IJKL"}
    monkeypatch.setenv("MCF_EARN_CAL", str(tmp_path / "missing.parquet"))
    assert _load().today_symbols("2026-11-18") == frozenset()


def test_long_and_short_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _LAB_FRAMES.clear()
    bars, peers = _day(-6.0)
    st = _st("ULT-35", ["ABCD"])
    assert st.side == 1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 10:15", tz=TZ) <= t <= pd.Timestamp("2026-11-18 13:30", tz=TZ), t
    i = sigs[0].bar_index
    assert bars["close"].iloc[i] > bars["open"].iloc[0]                                # back above the open
    entry = float(bars["close"].iloc[i])
    assert abs((entry - sigs[0].stop) - (0.25 * 4.0 if m.EXIT == "T" else 0.5 * 4.0)) < 0.05
    assert not st.eligible(_ctx(bars, peers, sym="ZZZZ"))                              # not a reaction-day name
    _LAB_FRAMES.clear()
    b2, p2 = _day(-6.0, day="2026-11-17", reclaim=False)
    assert _st("ULT-35", ["ABCD"]).signals(_ctx(b2, p2)) == []                         # gap holding -> nothing
    _LAB_FRAMES.clear()
    b3, p3 = _day(-1.0, day="2026-11-16")
    assert _st("ULT-35", ["ABCD"]).signals(_ctx(b3, p3)) == []                         # gap below G -> nothing
    _LAB_FRAMES.clear()
    b4, p4 = _day(6.0, day="2026-11-13", osc=0.006)   # choppy: RSI5 not pinned (short needs RSI5 >= 25)
    st = _st("ULT-35-S", ["ABCD"])
    assert st.side == -1
    assert 1 <= len(st.signals(_ctx(b4, p4))) <= 2
    _LAB_FRAMES.clear()
    assert _st("ULT-35", ["ABCD"]).signals(_ctx(b4, p4)) == []                          # gap-up never long


def _frame(n=63, seed=0, gap=-6.0):
    rng = np.random.default_rng(seed)
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])   # 09:50 ...
    return pd.DataFrame({"tod": tod, "close": 50 * np.exp(np.cumsum(rng.normal(0, 0.004, n))), "gap": gap,
                         "atr_d": 4.0, "adv20": 1e8, "spy_fo": np.cumsum(rng.normal(0.02, 0.1, n)),
                         "vwapDistPct": rng.normal(0.0, 0.5, n), "fromOpen": rng.normal(0.0, 2, n),
                         "rsi5": rng.uniform(10, 95, n), "dist_hod_atr": rng.uniform(0, 0.05, n),
                         "dist_lod_atr": rng.uniform(0, 2, n), "e_rd": True, "e_surp": 5.0})


def test_features_point_in_time_first_bar_and_event_column():
    m = _load()
    for gap, sg in ((-6.0, 1), (6.0, -1)):
        df = _frame(gap=gap)
        full = m.features(df)
        assert m.signal(full, sg, 3.0, 0.0).any()
        for i in (5, 30, 62):
            part = m.features(df.iloc[: i + 1].reset_index(drop=True))
            for k in ("cost_r", "intake", "foa", "foa_prev", "vd_prev", "spy_r30", "univ_long_ok"):
                a, b = float(full[k][i]), float(part[k][i])
                assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, i)
            for d in (0.0, 0.5):
                assert bool(m.signal(full, sg, 3.0, d)[i]) == bool(m.signal(part, sg, 3.0, d)[i])
        sig = m.signal(full, sg, 3.0, 0.0)
        assert not sig[0]                                                                # no previous bar
        c = m.core(full["vd"], full["foa"], sg, 0.0)
        assert (c[np.flatnonzero(sig)] & ~c[np.flatnonzero(sig) - 1]).all()             # first bar of the failure
        assert not m.signal(full, -sg, 3.0, 0.0).any()                                   # never with the gap
        assert not m.signal(m.features(df.assign(e_rd=False)), sg).any()                 # non-event rows never fire
    # foa matches (close - open) / atr_d
    df = _frame()
    f = m.features(df)
    op = df.close / (1 + df.fromOpen / 100)
    assert np.allclose(f["foa"], (df.close - op) / df.atr_d)


def test_mutually_exclusive_with_ult28():
    m35, m28 = _load(), _load("ult28", str(MODS / "ULT-28.py"))
    for gap, sg in ((-6.0, 1), (6.0, -1)):
        df = _frame(gap=gap, seed=3)
        r35, r28 = m35.features(df), m28.features(df)
        a = m35.signal(r35, sg, 3.0, 0.0)
        b = m28.signal(r28, -sg, 3.0, "HOLD", "any")      # ULT-28 trades with the gap: side -sg
        assert a.any() and not (a & b).any()
