"""Smoke test: ULT-11 module imports and runs under the live LabStrategy (context columns) on BOTH sides (side from the
setup name), fires with a toy model when its side's prediction is above tau and better than the other side, honours the
refire thinning and the 2u catastrophic stop, fails safe without SPY context; the frozen model (if present) runs; the
feature build on one symbol-day (live shape: datetime index, no symbol/date columns) equals the month batch build.
    pytest -q research/ultimate_1119/round2/ULT-11/test_module.py
Educational only - not financial advice."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-11.py")
ET = "America/New_York"
CTX = ["spy_fo", "qqq_fo", "breadth", "breadth_open", "qqq_vwap"]


def _day(drift):
    rng = np.random.default_rng(7)
    steps = drift + rng.normal(0, 0.05, 390)
    px = 100 + np.cumsum(steps)
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz=ET)
    bars = pd.DataFrame({"open": np.r_[100, px[:-1]], "high": np.maximum(px, np.r_[100, px[:-1]]) + 0.01,
                         "low": np.minimum(px, np.r_[100, px[:-1]]) - 0.01, "close": px, "volume": 50000.0}, index=idx)
    spy = 600 + 0.01 * np.arange(390)
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb, "QQQ": spyb * 0.8, "ULTX": bars}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _toy(tmp_path, wl, ws):
    from importlib import util
    spec = util.spec_from_file_location("ult11_t", MOD)
    m = util.module_from_spec(spec); spec.loader.exec_module(m)
    F = len(m.FEATS)
    i = m.FEATS.index("fo_d")
    w_l, w_s = np.zeros(F), np.zeros(F)
    w_l[i], w_s[i] = wl, ws
    model = {"mean": [0.0] * F, "sd": [1.0] * F, "tau": 0.5, "h": 45, "long": {"kind": "ridge", "w": w_l.tolist(), "b": 0.0},
             "short": {"kind": "ridge", "w": w_s.tolist(), "b": 0.0}}
    p = tmp_path / "toy.json"
    p.write_text(json.dumps(model))
    return p


def _strat(name, path):
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy
    _LAB_FRAMES.clear()
    st = LabStrategy(name, MOD, window=[950, 1500], context=CTX, refire=True, refire_cooldown=0, min_adv=50_000_000, geom="S")
    st.mod.MODEL_PATH = Path(path)
    st.mod._MODEL.clear()
    return st


def test_long_and_short_with_toy_model(tmp_path):
    bars, peers = _day(0.02)               # steady up day: fo_d > 0 grows
    p = _toy(tmp_path, 1.0, -1.0)          # long pred = fo_d, short pred = -fo_d
    L = _strat("ULT-11-L", p)
    assert L.side == 1
    sigs = L.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, len(sigs)
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 09:50", tz=ET) <= t <= pd.Timestamp("2026-11-18 15:05", tz=ET) for t in times)
    if len(sigs) == 2:
        assert times[1] - times[0] >= pd.Timedelta(minutes=75)
    s = sigs[0]
    e = float(bars["close"].iloc[s.bar_index])
    assert s.target is None and abs((e - s.stop) - 2 * 0.25 * 4.0) < 1e-6
    S = _strat("ULT-11-S", p)
    assert S.side == -1 and S.signals(_ctx(bars, peers)) == []      # the long side is better all day
    bars_d, peers_d = _day(-0.02)          # down day: the short side wins (gap 0 < 0.5, RSI5 low may block)
    S2 = _strat("ULT-11-S", p)
    L2 = _strat("ULT-11-L", p)
    assert L2.signals(_ctx(bars_d, peers_d)) == []
    for x in S2.signals(_ctx(bars_d, peers_d)):
        assert x.side == -1 and x.stop > float(bars_d["close"].iloc[x.bar_index])


def test_fail_safe_and_frozen_model(tmp_path):
    bars, peers = _day(0.02)
    p = _toy(tmp_path, 1.0, -1.0)
    L = _strat("ULT-11-L", p)
    assert L.signals(_ctx(bars, None)) == []                         # no SPY context -> nothing
    real = Path(MOD).parent / "ULT-11_model.json"
    if real.exists():
        for nm in ("ULT-11-L", "ULT-11-S"):
            st = _strat(nm, real)
            assert isinstance(st.signals(_ctx(bars, peers)), list)


def test_single_day_features_equal_batch():
    import research.history2y.lib as lib
    from importlib import util
    spec = util.spec_from_file_location("ult11_e", MOD)
    m = util.module_from_spec(spec); spec.loader.exec_module(m)
    lib.DATA = Path("/home/user/MCF/research/history2y/data")
    f = lib.load_month("2025-03", context=True)
    f["symbol"] = f["symbol"].astype(str)
    f = f[f.symbol.isin(["AAPL", "NVDA", "XLF"])].reset_index(drop=True)
    f["sec_fo"], f["sec_r30"], f["sec_beta"] = 0.1, 0.0, 1.0
    Xb = m.raw_features(f)
    one = f[(f.symbol == "NVDA") & (f.date == f.date.iloc[0])]
    live = one.drop(columns=["symbol", "date"]).set_index(pd.DatetimeIndex(one["ts"]))
    Xl = m.raw_features(live)
    assert np.allclose(Xb[one.index], Xl, equal_nan=True)
    assert np.isfinite(Xl[:, m.FEATS.index("ret12")]).sum() == len(one) - 12
