"""Smoke test: ULT-30 module imports and runs under the live LabStrategy (context spy_fo) on both sides (two entries,
one file; "-S" = short), with the live allow-list (SYMBOLS from the calendar + daily-close files) as the event source;
RD+1 mapping and REACT (vs SPY) use only closes dated <= RD; missing files -> no symbols; long-only kills the short
side; fires only when the day-2 tape holds (not on a fade or a reversal gap); features are point-in-time
(truncation test) and the event columns e_d2 / e_react gate the backtest rows.
    pytest -q research/ultimate_1119/round4/ULT-30/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-30.py")
TZ = "America/New_York"


def _load(name="ult30", **kw):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _day(sgn=1, gap=1.0, day="2026-11-18", fade=False, base=100.0):
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


def _st(name, symbols):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    return LabStrategy(name, MOD, r_atr_frac=0.25, window=list(m.WINDOW), context=["spy_fo"], refire=True,
                       refire_cooldown=0, min_adv=30_000_000, geom=m.GEOM, time_stop_min=45, time_stop_min_r=99,
                       symbols=list(symbols))


def _files(tmp_path, monkeypatch):
    cal = tmp_path / "cal.parquet"
    pd.DataFrame([("ABCD", "2026-11-16", "amc"), ("EFGH", "2026-11-17", "bmo"), ("IJKL", "2026-11-17", "bmo"),
                  ("MNOP", "2026-11-17", "dmh"), ("QRST", "2026-11-18", "bmo")],
                 columns=["symbol", "date", "session"]).assign(date=lambda d: pd.to_datetime(d["date"])).to_parquet(cal)
    rows = []
    for d, spy, a, e, i, m, q in [("2026-11-14", 600, 100, 50, 20, 30, 40),    # Fri (RD-1 for ABCD amc 11-16 -> RD 11-17? no)
                                  ("2026-11-16", 606, 100, 50, 20, 30, 40),    # RD-1 of RD 11-17
                                  ("2026-11-17", 606, 110, 45, 20.4, 40, 40),  # RD: ABCD +10%, EFGH -10%, IJKL +2%
                                  ("2026-11-18", 600, 999, 999, 999, 999, 999)]:   # today: must never be used
        rows += [("SPY", d, spy), ("ABCD", d, a), ("EFGH", d, e), ("IJKL", d, i), ("MNOP", d, m), ("QRST", d, q)]
    dl = tmp_path / "daily.parquet"
    pd.DataFrame(rows, columns=["symbol", "date", "close"]).to_parquet(dl)
    monkeypatch.setenv("MCF_EARN_CAL", str(cal))
    monkeypatch.setenv("MCF_DAILY_CLOSES", str(dl))
    return cal, dl


def test_calendar_react_and_allow_list(tmp_path, monkeypatch):
    cal, dl = _files(tmp_path, monkeypatch)
    m = _load()
    # ABCD amc 11-16 -> RD 11-17 -> RD+1 11-18; EFGH / IJKL bmo 11-17 -> RD+1 11-18; MNOP dmh excluded
    assert m.today_symbols("2026-11-18", "long", 4.0, "both") == {"ABCD"}
    assert m.today_symbols("2026-11-18", "short", 4.0, "both") == {"EFGH"}
    assert m.today_symbols("2026-11-18", "short", 4.0, "long") == frozenset()          # long-only
    assert m.today_symbols("2026-11-18", "long", 12.0, "both") == frozenset()          # T too high
    assert m.today_symbols("2026-11-17", "long", 0.0, "both") == frozenset()          # nothing is RD+1 on 11-17
    ev = m.day2_events(pd.read_parquet(cal), m.sessions("2026-11-01", "2026-12-31"), pd.read_parquet(dl))
    r = dict(zip(ev.symbol, ev.react))
    assert abs(r["ABCD"] - 10.0) < 1e-9 and abs(r["EFGH"] + 10.0) < 1e-9 and abs(r["IJKL"] - 2.0) < 1e-9
    assert set(ev.d2) <= {"2026-11-18", "2026-11-19"}
    monkeypatch.setenv("MCF_DAILY_CLOSES", str(tmp_path / "missing.parquet"))
    assert _load().today_symbols("2026-11-18") == frozenset()                          # fail safe
    monkeypatch.setenv("MCF_DAILY_CLOSES", str(dl))
    monkeypatch.setenv("MCF_EARN_CAL", str(tmp_path / "missing.parquet"))
    assert _load().today_symbols("2026-11-18") == frozenset()


def test_point_in_time_closes(tmp_path, monkeypatch):
    """today_symbols must not read closes dated today: change today's close and the list stays the same."""
    cal, dl = _files(tmp_path, monkeypatch)
    m = _load()
    a = m.today_symbols("2026-11-18", "long", 4.0, "both")
    d = pd.read_parquet(dl)
    d.loc[d.date == "2026-11-18", "close"] = 1.0
    d.to_parquet(dl)
    assert _load().today_symbols("2026-11-18", "long", 4.0, "both") == a


def test_long_and_short_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    _LAB_FRAMES.clear()
    bars, peers = _day(1)
    st = _st("ULT-30", ["ABCD"])
    assert st.side == 1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 09:50", tz=TZ) <= t <= pd.Timestamp("2026-11-18 12:30", tz=TZ), t
    entry = float(bars["close"].iloc[sigs[0].bar_index])
    assert abs((entry - sigs[0].stop) - (0.25 * 4.0 if m.EXIT == "T" else 0.5 * 4.0)) < 0.05
    assert not st.eligible(_ctx(bars, peers, sym="ZZZZ"))                              # not an RD+1 name
    _LAB_FRAMES.clear()
    b2, p2 = _day(1, day="2026-11-17", fade=True)
    assert _st("ULT-30", ["ABCD"]).signals(_ctx(b2, p2)) == []                         # tape fading -> nothing
    _LAB_FRAMES.clear()
    b3, p3 = _day(1, gap=-2.0, day="2026-11-16")
    assert _st("ULT-30", ["ABCD"]).signals(_ctx(b3, p3)) == []                         # reversal gap -> nothing
    _LAB_FRAMES.clear()
    b4, p4 = _day(-1, gap=-1.0, day="2026-11-13")
    st = _st("ULT-30-S", ["ABCD"])
    assert st.side == -1
    n_short = len(st.signals(_ctx(b4, p4)))
    assert (1 <= n_short <= 2) if m.SIDES == "both" else n_short == 0


def test_features_point_in_time_and_event_columns():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((590 + 5 * k) // 60) * 100 + (590 + 5 * k) % 60) for k in range(n)])   # 09:50 ...
    df = pd.DataFrame({"tod": tod, "close": 50 * np.exp(np.cumsum(rng.normal(0, 0.004, n))), "gap": 1.0,
                       "atr_d": 4.0, "adv20": 1e8, "spy_fo": np.cumsum(rng.normal(0.02, 0.1, n)),
                       "vwapDistPct": rng.normal(0.3, 0.5, n), "fromOpen": rng.normal(0.5, 1, n),
                       "rsi5": rng.uniform(10, 95, n), "e_d2": True, "e_react": 9.0})
    full = m.features(df)
    for i in (5, 30, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("cost_r", "intake", "spy_r30", "univ_long_ok"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, i)
        for t in (4.0, 8.0):
            assert bool(m.signal(full, 1, t, "both")[i]) == bool(m.signal(part, 1, t, "both")[i])
    assert m.signal(full, 1, 4.0, "both").any()
    assert not m.signal(m.features(df.assign(e_d2=False)), 1, 4.0, "both").any()     # non-event rows never fire
    assert not m.signal(m.features(df.assign(e_react=6.0)), 1, 8.0, "both").any()    # below T
    assert not m.signal(m.features(df.assign(e_react=9.0)), -1, 4.0, "both").any()   # wrong side
    neg = df.assign(e_react=-9.0, gap=-1.0, vwapDistPct=-0.5, fromOpen=-0.5, rsi5=50.0)
    assert m.signal(m.features(neg), -1, 4.0, "both").all()
    assert not m.signal(m.features(neg), -1, 4.0, "long").any()                      # long-only
    assert not m.signal(m.features(neg.assign(gap=0.6)), -1, 4.0, "both").any()      # reversal gap
