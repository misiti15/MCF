"""Smoke test: ULT-34 module imports and runs under the live LabStrategy (context spy_fo) on both sides (two entries,
one file; "-S" = short). The live allow-list comes from the calendar + daily-bar files (r1 from closes dated < today,
ATR14, no report in d-5..d+1, calendar-covered or ETF, no leveraged funds); missing files -> no symbols; the live
per-name r1 is matched by the prior-day high / low fingerprint; features are point-in-time (truncation test) and the
backtest event columns e_ok / e_r1 / e_k gate the rows.
    pytest -q research/ultimate_1119/round4/ULT-34/test_module.py
Educational only - not financial advice."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-34.py")
TZ = "America/New_York"


def _load(name="ult34", **kw):
    spec = importlib.util.spec_from_file_location(name, MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


def _files(tmp_path, monkeypatch, lev="SQQQ", etf="XLE"):
    m = _load()
    sess = m.sessions("2026-10-01", "2026-11-18")
    names = {"DOWN": -12.0, "UPP": 12.0, "EARN": -12.0, "NOCAL": -12.0, lev: -12.0, etf: -12.0, "SMALL": -1.0}
    rows = []
    for i, d in enumerate(sess):
        for s, mv in names.items():
            c = 100.0 * (1 + 0.001 * (i % 2))
            if d == "2026-11-17":                       # d-1 of today: the extreme move
                c = 100.1 * (1 + mv / 100) if i % 2 == 0 else 100.0 * (1 + mv / 100)
            if d == "2026-11-18":                       # today: must never be used
                c = 1.0
            rows.append((s, d, c * 1.01, c * 0.99, c))
        rows.append(("SPY", d, 601, 599, 600))
    dl = tmp_path / "daily.parquet"
    pd.DataFrame(rows, columns=["symbol", "date", "high", "low", "close"]).to_parquet(dl)
    cal = tmp_path / "cal.parquet"
    pd.DataFrame([("DOWN", "2026-10-20", "amc"), ("UPP", "2026-10-21", "bmo"), ("EARN", "2026-11-18", "amc"),
                  (lev, "2026-10-01", "bmo")],     # LEV covered by the calendar on purpose: still excluded
                 columns=["symbol", "date", "session"]).assign(date=lambda d: pd.to_datetime(d["date"])).to_parquet(cal)
    monkeypatch.setenv("MCF_EARN_CAL", str(cal))
    monkeypatch.setenv("MCF_DAILY_BARS", str(dl))
    return cal, dl


def test_events_and_allow_list(tmp_path, monkeypatch):
    cal, dl = _files(tmp_path, monkeypatch)
    m = _load()
    long_ = set(m.today_events("2026-11-18", "long", 2.0).symbol)
    short = set(m.today_events("2026-11-18", "short", 2.0).symbol)
    # DOWN faded long; UPP faded short; EARN (amc 11-18 -> reaction 11-19 = d+1) excluded; NOCAL not covered and not an
    # ETF -> excluded; SQQQ leveraged -> excluded; XLE is an ETF (no calendar needed); SMALL below K
    assert "XLE" in m.ETF and "SQQQ" in m.LEV
    assert long_ == {"DOWN", "XLE"}, long_
    assert short == {"UPP"}, short
    assert m.today_events("2026-11-18", "long", 50.0).empty                       # K too high
    ev = m.nonews_events(pd.read_parquet(dl), pd.read_parquet(cal), m.sessions("2026-10-01", "2026-12-31"),
                         with_atr=True)
    e = ev[ev.d == "2026-11-18"].set_index("symbol")
    assert abs(e.loc["UPP", "r1"] - 12.0) < 0.2 and bool(e.loc["EARN", "news"]) and not bool(e.loc["DOWN", "news"])
    # news window d-5..d+1: a report reacting on 11-11 (= d-5) blocks d = 11-18; one reacting on 11-10 does not
    for rd, blocked in (("2026-11-11", True), ("2026-11-10", False), ("2026-11-19", True), ("2026-11-20", False)):
        c2 = pd.DataFrame([("DOWN", rd, "bmo")], columns=["symbol", "date", "session"])
        ev2 = m.nonews_events(pd.read_parquet(dl), c2, m.sessions("2026-10-01", "2026-12-31"))
        assert bool(ev2[(ev2.symbol == "DOWN") & (ev2.d == "2026-11-18")].news.iloc[0]) == blocked, rd
    monkeypatch.setenv("MCF_DAILY_BARS", str(tmp_path / "missing.parquet"))
    assert _load().SYMBOLS == frozenset() and _load().today_events("2026-11-18").empty      # fail safe
    monkeypatch.setenv("MCF_DAILY_BARS", str(dl))
    monkeypatch.setenv("MCF_EARN_CAL", str(tmp_path / "missing.parquet"))
    assert _load().today_events("2026-11-18").empty


def test_point_in_time_daily(tmp_path, monkeypatch):
    """today_events must not read bars dated today (or later): change them and the list stays the same."""
    cal, dl = _files(tmp_path, monkeypatch)
    m = _load()
    a = m.today_events("2026-11-18", "long", 2.0)
    d = pd.read_parquet(dl)
    d.loc[d.date == "2026-11-18", ["high", "low", "close"]] = 500.0
    d.to_parquet(dl)
    b = _load().today_events("2026-11-18", "long", 2.0)
    assert a.equals(b)


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


def _ctx(bars, peers, base=100.0, atr=4.0, sym="ABCD", ph=None, pl=None):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=atr, prev_close=base,
                           prev_high=base * 1.01 if ph is None else ph, prev_low=base * 0.99 if pl is None else pl,
                           avg_dollar_volume=2e8, peers=peers)


def _st(name, symbols, ev):
    from mcf.strategies.setups import LabStrategy
    m = _load()
    st = LabStrategy(name, MOD, r_atr_frac=0.25, window=list(m.WINDOW), context=["spy_fo"], refire=True,
                     refire_cooldown=0, min_adv=50_000_000, geom=m.GEOM, time_stop_min=45, time_stop_min_r=99,
                     symbols=list(symbols))
    st.mod._EV = ev
    return st


def test_long_and_short_under_live_lab_strategy():
    from mcf.strategies.setups import _LAB_FRAMES
    m = _load()
    evL = pd.DataFrame({"symbol": ["ABCD"], "r1": [-10.0], "prev_high": [101.0], "prev_low": [99.0]})
    _LAB_FRAMES.clear()
    bars, peers = _day(1, gap=1.0)
    st = _st("ULT-34", ["ABCD"], evL)
    assert st.side == 1
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, sigs
    t = bars.index[sigs[0].bar_index]
    assert pd.Timestamp("2026-11-18 10:00", tz=TZ) <= t <= pd.Timestamp("2026-11-18 13:00", tz=TZ), t
    entry = float(bars["close"].iloc[sigs[0].bar_index])
    assert abs((entry - sigs[0].stop) - (0.25 * 4.0 if m.EXIT == "T" else 0.5 * 4.0)) < 0.05
    assert not st.eligible(_ctx(bars, peers, sym="ZZZZ"))                              # not an event name
    _LAB_FRAMES.clear()
    assert _st("ULT-34", ["ABCD"], evL).signals(_ctx(bars, peers, ph=120.0, pl=80.0)) == []   # no fingerprint match
    _LAB_FRAMES.clear()
    b2, p2 = _day(1, day="2026-11-17", fade=True)
    assert _st("ULT-34", ["ABCD"], evL).signals(_ctx(b2, p2)) == []                   # tape keeps falling -> nothing
    _LAB_FRAMES.clear()
    b3, p3 = _day(1, gap=6.0, day="2026-11-16")
    assert _st("ULT-34", ["ABCD"], evL).signals(_ctx(b3, p3)) == []                   # gap already > half reverted
    _LAB_FRAMES.clear()
    evS = evL.assign(r1=10.0)
    b4, p4 = _day(-1, gap=-1.0, day="2026-11-13")
    st = _st("ULT-34-S", ["ABCD"], evS)
    assert st.side == -1
    assert 1 <= len(st.signals(_ctx(b4, p4))) <= 2
    _LAB_FRAMES.clear()
    assert _st("ULT-34-S", ["ABCD"], evL).signals(_ctx(b4, p4)) == []                 # r1 < 0 never shorts


def test_features_point_in_time_and_event_columns():
    m = _load()
    rng = np.random.default_rng(0)
    n = 63
    tod = np.array([int(((600 + 5 * k) // 60) * 100 + (600 + 5 * k) % 60) for k in range(n)])   # 10:00 ...
    df = pd.DataFrame({"tod": tod, "close": 50 * np.exp(np.cumsum(rng.normal(0, 0.004, n))), "gap": 1.0,
                       "atr_d": 4.0, "adv20": 1e8, "spy_fo": np.cumsum(rng.normal(0.02, 0.1, n)),
                       "vwapDistPct": rng.normal(0.3, 0.5, n), "fromOpen": rng.normal(0.5, 1, n),
                       "rsi5": rng.uniform(10, 95, n), "e_ok": True, "e_r1": -9.0, "e_k": 2.5})
    full = m.features(df)
    for i in (5, 30, 62):
        part = m.features(df.iloc[: i + 1].reset_index(drop=True))
        for k in ("cost_r", "intake", "spy_r30", "univ_long_ok"):
            a, b = float(full[k][i]), float(part[k][i])
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (k, i)
        for kk, f in ((2.0, "V"), (2.0, "VO"), (3.0, "V")):
            assert bool(m.signal(full, 1, kk, f)[i]) == bool(m.signal(part, 1, kk, f)[i])
    assert m.signal(full, 1, 2.0, "V").any()
    assert not m.signal(full, 1, 3.0, "V").any()                                       # below K
    assert not m.signal(m.features(df.assign(e_ok=False)), 1, 2.0, "V").any()          # news / not covered / LEV
    assert not m.signal(full, -1, 2.0, "V").any()                                      # r1 < 0 -> long only
    assert not m.signal(m.features(df.assign(gap=5.0)), 1, 2.0, "V").any()             # gap > 0.5 x |r1|
    vo = m.signal(full, 1, 2.0, "VO")
    assert not (vo & (df.fromOpen.to_numpy() < 0)).any() and (vo <= m.signal(full, 1, 2.0, "V")).all()
    up = df.assign(e_r1=9.0, gap=-1.0, vwapDistPct=-0.5, fromOpen=-0.5, rsi5=50.0)
    assert m.signal(m.features(up), -1, 2.0, "VO").all()
    assert not m.signal(m.features(up.assign(rsi5=20.0)), -1, 2.0, "V").any()         # short RSI5 floor
    assert not m.signal(m.features(up.assign(gap=0.6)), -1, 2.0, "V").any()           # no short into a gap-up
