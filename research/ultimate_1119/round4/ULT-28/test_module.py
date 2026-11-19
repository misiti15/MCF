"""Smoke test: ULT-28 module imports and runs under the live LabStrategy (context spy_fo) on both sides (two entries, one
file; "-S" = short), with the live allow-list (SYMBOLS from the calendar file) as the event source; fires only on a
reaction-day name with a holding gap, not on a faded gap or a non-event name; the calendar maps bmo -> report day and
amc -> next session; missing calendar -> no symbols; features are point-in-time (truncation test) and the event
columns e_rd / e_surp gate the backtest rows.
    pytest -q research/ultimate_1119/round4/ULT-28/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-28.py")
TZ = "America/New_York"


def _load(name="ult28", **kw):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
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


def _ctx(bars, peers, base=100.0, atr=4.0, sym="ABCD"):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=atr, prev_close=base,
                           prev_high=base * 1.01, prev_low=base * 0.99, avg_dollar_volume=2e8, peers=peers)


def _cal(tmp_path, rows):
    p = tmp_path / "cal.parquet"
    pd.DataFrame(rows, columns=["symbol", "date", "session", "surprise_pct"]).assign(
        date=lambda d: pd.to_datetime(d["date"])).to_parquet(p)
    return p


def _st(name, symbols):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    return LabStrategy(name, MOD, r_atr_frac=0.25, window=list(m.WINDOW), context=["spy_fo"], refire=True,
                       refire_cooldown=0, min_adv=30_000_000, geom=m.GEOM, time_stop_min=45, time_stop_min_r=99,
                       symbols=list(symbols))


def test_calendar_and_allow_list(tmp_path, monkeypatch):
    p = _cal(tmp_path, [("ABCD", "2026-11-17", "amc", 12.0), ("EFGH", "2026-11-18", "bmo", -5.0),
                        ("IJKL", "2026-11-18", "amc", 3.0), ("MNOP", "2026-11-18", "dmh", 3.0),
                        ("QRST", "2026-11-13", "amc", 3.0), ("UVWX", "2026-11-18", "bmo", np.nan)])
    monkeypatch.setenv("MCF_EARN_CAL", str(p))
    m = _load()
    assert m.today_symbols("2026-11-18", "long", "any") == {"ABCD", "EFGH", "UVWX"}   # amc 11-17 + bmo 11-18
    assert m.today_symbols("2026-11-18", "long", "agree") == {"ABCD"}
    assert m.today_symbols("2026-11-18", "short", "agree") == {"EFGH"}
    assert m.today_symbols("2026-11-16", "long", "any") == {"QRST"}                    # Fri amc -> Mon
    assert m.today_symbols("2026-11-27", "long", "any") == frozenset()
    monkeypatch.setenv("MCF_EARN_CAL", str(tmp_path / "missing.parquet"))
    assert _load().today_symbols("2026-11-18") == frozenset()                          # fail safe
    ev = m.reaction_days(pd.read_parquet(p), m.sessions("2026-11-01", "2026-12-31"))
    assert dict(zip(ev.symbol, ev.rd))["IJKL"] == "2026-11-19"
    assert "2026-11-26" not in m.sessions("2026-11-20", "2026-11-30")                  # Thanksgiving


def test_long_and_short_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _LAB_FRAMES.clear()
    bars, peers = _day(1)
    st = _st("ULT-28", ["ABCD"])
    assert st.side == 1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 09:50", tz=TZ) <= t <= pd.Timestamp("2026-11-18 12:30", tz=TZ), t
    entry = float(bars["close"].iloc[sigs[0].bar_index])
    assert abs((entry - sigs[0].stop) - (0.25 * 4.0 if m.EXIT == "T" else 0.5 * 4.0)) < 0.05
    assert not st.eligible(_ctx(bars, peers, sym="ZZZZ"))                              # not a reaction-day name
    _LAB_FRAMES.clear()
    b2, p2 = _day(1, day="2026-11-17", fade=True)
    assert _st("ULT-28", ["ABCD"]).signals(_ctx(b2, p2)) == []                         # gap fading -> nothing
    _LAB_FRAMES.clear()
    b3, p3 = _day(1, gap=1.0, day="2026-11-16")
    assert _st("ULT-28", ["ABCD"]).signals(_ctx(b3, p3)) == []                         # gap below G -> nothing
    _LAB_FRAMES.clear()
    b4, p4 = _day(-1, gap=-6.0, day="2026-11-13")
    st = _st("ULT-28-S", ["ABCD"])
    assert st.side == -1
    assert 1 <= len(st.signals(_ctx(b4, p4))) <= 2


def test_features_point_in_time_and_event_columns():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])   # 09:50 ...
    df = pd.DataFrame({"tod": tod, "close": 50 * np.exp(np.cumsum(rng.normal(0, 0.004, n))), "gap": 6.0,
                       "atr_d": 2.0, "adv20": 1e8, "spy_fo": np.cumsum(rng.normal(0.02, 0.1, n)),
                       "vwapDistPct": rng.normal(0.3, 0.5, n), "fromOpen": rng.normal(0.5, 1, n),
                       "rsi5": rng.uniform(10, 95, n), "dist_hod_atr": rng.uniform(0, 0.05, n),
                       "dist_lod_atr": rng.uniform(0, 2, n), "e_rd": True, "e_surp": 5.0})
    full = m.features(df)
    for i in (5, 30, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("cost_r", "intake", "dh_prev", "spy_r30", "univ_long_ok"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, i)
        for en in ("HOLD", "PUSH"):
            for sm in ("any", "agree"):
                assert bool(m.signal(full, 1, 3.0, en, sm)[i]) == bool(m.signal(part, 1, 3.0, en, sm)[i])
    assert not m.push(full, 1)[0]                                                      # no previous bar at 09:50
    assert not m.signal(m.features(df.assign(e_rd=False)), 1).any()                    # non-event rows never fire
    assert not m.signal(m.features(df.assign(e_surp=-5.0)), 1, 3.0, "HOLD", "agree").any()
    assert not m.signal(m.features(df.assign(e_surp=np.nan)), 1, 3.0, "HOLD", "agree").any()
