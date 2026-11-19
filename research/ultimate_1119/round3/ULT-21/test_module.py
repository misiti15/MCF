"""Smoke test: ULT-21 module imports and runs under the live LabStrategy (context spy_fo, symbols: module), infers the
symbol from the runner's frame cache (leverage / inverse flags), fires with a toy model when pred > tau, honours the
symbol allow-list, the refire thinning, the universal long filter (long-exposure funds only; inverse funds exempt), fails
safe without SPY context; the frozen model (if present) runs; features are point-in-time (removing later bars does not
change earlier rows) and the live single-day build equals the month batch build.
    pytest -q research/ultimate_1119/round3/ULT-21/test_module.py
Educational only - not financial advice."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-21.py")
ET = "America/New_York"


def _load(name="u21"):
    from importlib import util
    spec = util.spec_from_file_location(name, MOD)
    m = util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _day(drift=0.02, spy_path="flat", day="2026-11-18"):
    rng = np.random.default_rng(7)
    px = 100 + np.cumsum(drift + rng.normal(0, 0.05, 390))
    idx = pd.date_range(f"{day} 09:30", periods=390, freq="1min", tz=ET)
    op = np.r_[100, px[:-1]]
    bars = pd.DataFrame({"open": op, "high": np.maximum(px, op) + 0.01, "low": np.minimum(px, op) - 0.01, "close": px,
                         "volume": 50000.0}, index=idx)
    t = np.arange(390)
    spy = 600 + 0.01 * np.sin(t) if spy_path == "flat" else 600 * (1 - 0.005 * np.clip((t - 60) / 100, 0, 1.2))
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers, sym):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=8.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _toy(tmp_path, feat, w=1.0, tau=0.5, exit_="T5"):
    m = _load("u21toy")
    F = len(m.FEATS)
    ww = np.zeros(F); ww[m.FEATS.index(feat)] = w
    p = tmp_path / "toy.json"
    p.write_text(json.dumps({"mean": [0.0] * F, "sd": [1.0] * F, "tau": tau, "h": 45, "exit": exit_,
                             "model": {"kind": "ridge", "w": ww.tolist(), "b": 0.0}}))
    return p


def _strat(name, path, geom="t05s1"):
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy
    _LAB_FRAMES.clear()
    st = LabStrategy(name, MOD, window=[1030, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=30_000_000, geom=geom, symbols="module")
    st.mod.MODEL_PATH = Path(path)
    st.mod._MODEL.clear()
    return st


def test_fires_under_live_lab_strategy(tmp_path):
    bars, peers = _day(0.02)
    p = _toy(tmp_path, "fo_d")                     # pred = from-open distance in dATR (rises on an up day)
    st = _strat("ULT-21", p)
    sigs = st.signals(_ctx(bars, peers, "TQQQ"))
    assert 1 <= len(sigs) <= 2, len(sigs)
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 10:25", tz=ET) <= t <= pd.Timestamp("2026-11-18 15:05", tz=ET) for t in times)
    if len(sigs) == 2:
        assert times[1] - times[0] >= pd.Timedelta(minutes=75)
    s = sigs[0]
    e = float(bars["close"].iloc[s.bar_index])
    assert s.side == 1 and abs((e - s.stop) - 2.0) < 1e-6 and abs((s.target - e) - 1.0) < 1e-6   # t05s1, u = 0.25 x 8
    assert st.eligible(_ctx(bars, peers, "TQQQ")) and not st.eligible(_ctx(bars, peers, "NVDL"))   # single-stock fund out
    assert _strat("ULT-21", p).signals(_ctx(bars, None, "TQQQ")) == []                               # no SPY -> nothing


def test_symbol_flags_reach_the_features(tmp_path):
    bars, peers = _day(0.0)
    p = _toy(tmp_path, "lev", w=1.0, tau=2.5)      # pred = leverage: only 3x funds clear tau 2.5
    assert len(_strat("ULT-21", p).signals(_ctx(bars, peers, "TQQQ"))) >= 1
    assert _strat("ULT-21", p).signals(_ctx(bars, peers, "QQQ")) == []
    p2 = _toy(tmp_path, "inv", w=1.0, tau=0.5)     # pred = inverse flag
    assert len(_strat("ULT-21", p2).signals(_ctx(bars, peers, "SQQQ"))) >= 1
    assert _strat("ULT-21", p2).signals(_ctx(bars, peers, "TQQQ")) == []


def test_universal_long_filter_exempts_inverse(tmp_path):
    bars, peers = _day(0.0, spy_path="down", day="2026-11-17")   # (own date: context cache) SPY slides to ~-0.5% and keeps falling from ~10:30 on
    m = _load("u21f")
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    p = _toy(tmp_path, "blk2", w=1.0, tau=0.5)     # fire in 12:30-13:29 when SPY is in the band and falling
    long_sigs = _strat("ULT-21", p).signals(_ctx(bars, peers, "TQQQ"))
    inv_sigs = _strat("ULT-21", p).signals(_ctx(bars, peers, "SQQQ"))
    # SPY is in the -0.30..-0.75% band and falling over 30 min until the 13:00 bar close: no long-exposure entry before
    # 13:05; the inverse fund is exempt and fires at the first 12:30-13:29 bar
    t_long = [bars.index[s.bar_index] for s in long_sigs]
    t_inv = [bars.index[s.bar_index] for s in inv_sigs]
    assert all(t >= pd.Timestamp("2026-11-17 13:00", tz=ET) for t in t_long), t_long
    assert len(t_inv) >= 1 and t_inv[0] < pd.Timestamp("2026-11-17 12:35", tz=ET), t_inv
    assert m.GEOM in ("t05s1", "S")


def test_frozen_model_runs():
    real = Path(MOD).parent / "ULT-21_model.json"
    if real.exists():
        bars, peers = _day(0.02)
        st = _strat("ULT-21", real, geom=None)
        assert isinstance(st.signals(_ctx(bars, peers, "SOXL")), list)


def test_point_in_time_and_live_equals_batch():
    import research.history2y.lib as lib
    m = _load("u21e")
    lib.DATA = Path("/home/user/MCF/research/history2y/data")
    f = lib.load_month("2025-03", context=True)
    f["symbol"] = f["symbol"].astype(str)
    f = f[f.symbol.isin(["TQQQ", "SQQQ", "SOXL"])].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    f["date"] = f["date"].astype(str)
    Xb = m.raw_features(f)
    one = f[(f.symbol == "SQQQ") & (f.date == f.date.iloc[0])]
    live = one.drop(columns=["symbol", "date"]).set_index(pd.DatetimeIndex(one["ts"]))
    Xl = m.raw_features(live, sym="SQQQ")
    assert np.allclose(Xb[one.index], Xl, equal_nan=True)
    for i in (20, 40, len(live) - 1):
        part = m.raw_features(live.iloc[: i + 1], sym="SQQQ")
        assert np.allclose(part[i], Xl[i], equal_nan=True), i
    assert Xl[0, m.FEATS.index("inv")] == 1 and Xl[0, m.FEATS.index("lev")] == 3
