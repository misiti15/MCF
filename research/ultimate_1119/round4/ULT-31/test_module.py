"""Smoke test: ULT-31 module imports and runs under the live LabStrategy (context columns) on BOTH sides (side from the
setup name), fires with a toy model only where its side scores above tau and above the other side, honours the refire
thinning and the 2u catastrophic stop, fails safe without SPY context; the frozen model (if present) runs; the build on
one symbol-day (live shape: datetime index, no symbol/date columns, bars from 09:35) equals the month batch build;
point-in-time: features of bar t are unchanged when the frame is truncated at t; the earnings state uses no field dated
after the bar (REACT only on RD+1 and only from closes <= RD; RD rows carry no REACT); EVT trades only RD / RD+1 rows;
the live STATE path (SYMBOL_HINT) gives the same earnings features as frame columns.
    pytest -q research/ultimate_1119/round4/ULT-31/test_module.py
Educational only - not financial advice."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-31.py")
ET = "America/New_York"
CTX = ["spy_fo", "qqq_fo", "breadth", "breadth_open", "qqq_vwap"]


def _load(name="ult31_t"):
    from importlib import util
    spec = util.spec_from_file_location(name, MOD)
    m = util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _day(drift, seed=7, vol=0.15):
    rng = np.random.default_rng(seed)
    steps = drift + rng.normal(0, vol, 390)
    px = 100 + np.cumsum(steps)
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz=ET)
    bars = pd.DataFrame({"open": np.r_[100, px[:-1]], "high": np.maximum(px, np.r_[100, px[:-1]]) + 0.02,
                         "low": np.minimum(px, np.r_[100, px[:-1]]) - 0.02, "close": px, "volume": 50000.0}, index=idx)
    spy = 600 + 0.01 * np.arange(390)
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb, "QQQ": spyb * 0.8, "ULTX": bars}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=8.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _toy(tmp_path, w_is_long, b, univ="ALL"):
    m = _load()
    F = len(m.FEATS)
    w = np.zeros(F)
    w[m.FEATS.index("is_long")] = w_is_long
    model = {"mean": [0.0] * F, "sd": [1.0] * F, "tau": 0.5, "univ": univ, "h": 45,
             "model": {"kind": "ridge", "w": w.tolist(), "b": b}}
    p = tmp_path / "toy.json"
    p.write_text(json.dumps(model))
    return p


def _strat(name, path):
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy
    _LAB_FRAMES.clear()
    st = LabStrategy(name, MOD, window=[1000, 1500], context=CTX, refire=True, refire_cooldown=0, min_adv=100_000_000,
                     geom="S")
    st.mod.MODEL_PATH = Path(path)
    st.mod._MODEL.clear()
    return st


def test_long_side_fires_short_side_silent(tmp_path):
    bars, peers = _day(0.0)
    p = _toy(tmp_path, 1.0, 0.0)             # long rows score 1, short rows 0
    L = _strat("ULT-31-L", p)
    assert L.side == 1
    sigs = L.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, len(sigs)
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 09:55", tz=ET) <= t <= pd.Timestamp("2026-11-18 15:05", tz=ET) for t in times)
    s = sigs[0]
    e = float(bars["close"].iloc[s.bar_index])
    assert s.target is None and abs((e - s.stop) - 2 * 0.25 * 8.0) < 1e-6
    S = _strat("ULT-31-S", p)
    assert S.side == -1 and S.signals(_ctx(bars, peers)) == []


def test_short_side(tmp_path):
    bars, peers = _day(0.0)
    p = _toy(tmp_path, -1.0, 1.0)            # short rows score 1, long rows 0
    S = _strat("ULT-31-S", p)
    sigs = S.signals(_ctx(bars, peers))
    assert len(sigs) >= 1
    for x in sigs:
        assert x.side == -1 and x.stop > float(bars["close"].iloc[x.bar_index])


def test_fail_safe_evt_and_frozen_model(tmp_path):
    bars, peers = _day(0.0)
    p = _toy(tmp_path, 1.0, 0.0)
    L = _strat("ULT-31-L", p)
    assert L.signals(_ctx(bars, None)) == []                         # no SPY context -> nothing
    pe = _toy(tmp_path, 1.0, 0.0, univ="EVT")
    assert _strat("ULT-31-L", pe).signals(_ctx(bars, peers)) == []  # EVT: no earnings state -> nothing
    real = Path(MOD).parent / "ULT-31_model.json"
    if real.exists():
        for nm in ("ULT-31-L", "ULT-31-S"):
            st = _strat(nm, real)
            assert isinstance(st.signals(_ctx(bars, peers)), list)


def _month_sample():
    import research.history2y.lib as lib
    lib.DATA = Path("/home/user/MCF/research/history2y/data")
    f = lib.load_month("2025-04", context=True)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f[f.symbol.isin(["AAPL", "NVDA", "XLF", "TQQQ"])].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    f = f[[c for c in f.columns if not c.startswith(("win_", "r_long", "r_short")) and "heat" not in c.lower()]]
    f["sec_fo"] = 0.1
    for k in ("e_rd", "e_rd1", "e_pre", "e_bmo"):
        f[k] = 0.0
    f["e_surp"], f["e_react"] = np.nan, np.nan
    d0 = f.date.iloc[0]
    rd = (f.symbol == "NVDA") & (f.date == d0)
    f.loc[rd, ["e_rd", "e_bmo", "e_surp"]] = [1.0, 1.0, 12.0]
    return f


def test_single_day_build_equals_batch_point_in_time_and_live_state():
    m = _load("ult31_e")
    f = _month_sample()
    b = m.build(f)
    XL, XS = m.side_features(b, 1), m.side_features(b, -1)
    d0 = f.date.iloc[0]
    one = f[(f.symbol == "NVDA") & (f.date == d0)]
    live = one.drop(columns=["symbol", "date"]).set_index(pd.DatetimeIndex(one["ts"]))
    bl = m.build(live)
    pos = np.searchsorted(b["sel"], one.index[(one.tod >= 1000) & (one.tod <= 1500)].to_numpy())
    skip = [m.FEATS.index("is_etf"), m.FEATS.index("log_adv")]
    keep = [i for i in range(len(m.FEATS)) if i not in skip]
    assert np.allclose(XL[pos][:, keep], m.side_features(bl, 1)[:, keep], equal_nan=True)
    assert np.allclose(XS[pos][:, keep], m.side_features(bl, -1)[:, keep], equal_nan=True)
    assert XL[pos][:, m.FEATS.index("e_rd")].min() == 1 and XL[pos][:, m.FEATS.index("s_surp_sign")].min() == 1
    assert XS[pos][:, m.FEATS.index("s_surp_sign")].max() == -1
    # point-in-time: truncate the symbol-day at bar j; features of bar j unchanged
    for j in (8, 20, 40):
        tr = one.iloc[: j + 1]
        bt = m.build(tr)
        jj = np.searchsorted(b["sel"], one.index[j])
        assert np.allclose(m.side_features(bt, 1)[-1], XL[jj], equal_nan=True)
        assert np.allclose(m.side_features(bt, -1)[-1], XS[jj], equal_nan=True)
    # live STATE path (no e_* columns, SYMBOL_HINT) == frame columns
    m.STATE = {"NVDA": {"e_rd": 1.0, "e_rd1": 0.0, "e_pre": 0.0, "e_bmo": 1.0, "e_surp": 12.0, "e_react": np.nan}}
    m.SYMBOL_HINT = "NVDA"
    lv = live.drop(columns=["e_rd", "e_rd1", "e_pre", "e_bmo", "e_surp", "e_react"])
    bs = m.build(lv)
    assert np.allclose(m.side_features(bs, 1)[:, keep], XL[pos][:, keep], equal_nan=True)
    # EVT only on RD/RD+1 rows; never short a leveraged ETF
    ev = m.univ_ok(b, "EVT")
    assert not (ev & ~b["evt"]).any()
    assert not m.side_rows(b, -1, "ALL")[(f.symbol.to_numpy()[b["sel"]] == "TQQQ")].any()


def test_earn_state_point_in_time():
    m = _load("ult31_s")
    sess = m.sessions("2025-04-01", "2025-05-30")
    earn = pd.DataFrame({"symbol": ["AAA", "BBB"], "date": pd.to_datetime(["2025-04-15", "2025-04-15"]),
                         "session": ["amc", "bmo"], "surprise_pct": [10.0, -5.0]})
    daily = pd.DataFrame({"symbol": ["AAA"] * 4 + ["BBB"] * 4 + ["SPY"] * 4,
                          "date": ["2025-04-15", "2025-04-16", "2025-04-17", "2025-04-21"] * 3,
                          "close": [100, 110, 999, 999, 50, 45, 1, 1, 500, 505, 1, 1]})
    st = m.earn_state(earn, sess, daily).set_index(["symbol", "date"])
    # AAA reports after the close on 04-15 -> RD 04-16, RD+1 04-17; REACT = (110/100 - 1) - (505/500 - 1) = 9%
    assert st.loc[("AAA", "2025-04-16"), "e_rd"] == 1 and np.isnan(st.loc[("AAA", "2025-04-16"), "e_react"])
    assert abs(st.loc[("AAA", "2025-04-17"), "e_react"] - 9.0) < 1e-9
    assert st.loc[("AAA", "2025-04-15"), "e_pre"] == 1 and st.loc[("AAA", "2025-04-15"), "e_win"] == 1
    assert st.loc[("AAA", "2025-04-11"), "e_pre"] == 1 and st.loc[("AAA", "2025-04-11"), "e_win"] == 0
    assert st.loc[("BBB", "2025-04-15"), "e_rd"] == 1 and st.loc[("BBB", "2025-04-15"), "e_bmo"] == 1
    # closes dated after RD never change REACT
    d2 = daily.copy()
    d2.loc[d2.date > "2025-04-16", "close"] = 12345.0
    st2 = m.earn_state(earn, sess, d2).set_index(["symbol", "date"])
    assert abs(st2.loc[("AAA", "2025-04-17"), "e_react"] - 9.0) < 1e-9
    # drop(): events whose RD-1 / RD / RD+1 touch a blocked date are removed entirely
    st3 = m.earn_state(earn, sess, daily, drop=lambda a: np.asarray(a, dtype=str) == "2025-04-17")
    assert "AAA" not in set(st3.symbol)
