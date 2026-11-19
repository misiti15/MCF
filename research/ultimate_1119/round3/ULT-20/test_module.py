"""Smoke test: ULT-20 module imports and runs under the live LabStrategy (context columns) on BOTH sides (side from the
setup name), fires with a toy model only on rows where an event of its side fires and its side scores above tau and
above the other side, honours the refire thinning and the 2u catastrophic stop, fails safe without SPY context; the frozen
model (if present) runs; the build on one symbol-day (live shape: datetime index, no symbol/date columns) equals the
month batch build; point-in-time: features of bar t are unchanged when the frame is truncated at t.
    pytest -q research/ultimate_1119/round3/ULT-20/test_module.py
Educational only - not financial advice."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-20.py")
ET = "America/New_York"
CTX = ["spy_fo", "qqq_fo", "breadth", "breadth_open", "qqq_vwap"]


def _load(name="ult20_t"):
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
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _toy(tmp_path, w_is_long, b, univ="L2"):
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
    st = LabStrategy(name, MOD, window=[950, 1500], context=CTX, refire=True, refire_cooldown=0, min_adv=50_000_000, geom="S")
    st.mod.MODEL_PATH = Path(path)
    st.mod._MODEL.clear()
    return st


def test_long_side_fires_only_on_long_events(tmp_path):
    bars, peers = _day(0.0)
    p = _toy(tmp_path, 1.0, 0.0)             # long rows score 1, short rows 0 -> long side wins wherever a long event fires
    L = _strat("ULT-20-L", p)
    assert L.side == 1
    sigs = L.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, len(sigs)
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 09:50", tz=ET) <= t <= pd.Timestamp("2026-11-18 15:05", tz=ET) for t in times)
    s = sigs[0]
    e = float(bars["close"].iloc[s.bar_index])
    assert s.target is None and abs((e - s.stop) - 2 * 0.25 * 4.0) < 1e-6
    S = _strat("ULT-20-S", p)
    assert S.side == -1 and S.signals(_ctx(bars, peers)) == []      # short rows score 0 < tau


def test_short_side_and_event_requirement(tmp_path):
    bars, peers = _day(0.0)
    p = _toy(tmp_path, -1.0, 1.0)            # short rows score 1, long rows 0
    S = _strat("ULT-20-S", p)
    sigs = S.signals(_ctx(bars, peers))
    for x in sigs:
        assert x.side == -1 and x.stop > float(bars["close"].iloc[x.bar_index])
    # mask fires only where a short event fires (direct module check on a synthetic frame)
    m = S.mod
    from mcf.strategies.setups import _LAB_FRAMES
    f = next(iter(_LAB_FRAMES.values())).copy()
    from mcf.strategies.lab_context import add_context, parse_context
    f = add_context(f, peers, parse_context(CTX), None)
    b = m.build(f)
    anys = b["ev"]["S1"] | b["ev"]["S2"] | b["ev"]["S3"] | b["ev"]["S4"] | b["ev"]["E5S"]
    mk = m.mask(f)
    assert not (mk[b["sel"]] & ~anys).any()


def test_fail_safe_and_frozen_model(tmp_path):
    bars, peers = _day(0.0)
    p = _toy(tmp_path, 1.0, 0.0)
    L = _strat("ULT-20-L", p)
    assert L.signals(_ctx(bars, None)) == []                         # no SPY context -> nothing
    real = Path(MOD).parent / "ULT-20_model.json"
    if real.exists():
        for nm in ("ULT-20-L", "ULT-20-S"):
            st = _strat(nm, real)
            assert isinstance(st.signals(_ctx(bars, peers)), list)


def _month_sample():
    import research.history2y.lib as lib
    lib.DATA = Path("/home/user/MCF/research/history2y/data")
    f = lib.load_month("2025-03", context=True)
    f["symbol"] = f["symbol"].astype(str)
    f["date"] = f["date"].astype(str)
    f = f[f.symbol.isin(["AAPL", "NVDA", "XLF", "TQQQ"])].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    f = f[[c for c in f.columns if not c.startswith(("win_", "r_long", "r_short")) and "heat" not in c.lower()]]
    f["sec_fo"], f["sec_atrp"], f["sec_beta"] = 0.1, 1.5, 1.0
    return f


def test_single_day_build_equals_batch_and_point_in_time():
    m = _load("ult20_e")
    f = _month_sample()
    b = m.build(f)
    XL, XS = m.side_features(b, 1), m.side_features(b, -1)
    d0 = f.date.iloc[0]
    one = f[(f.symbol == "NVDA") & (f.date == d0)]
    live = one.drop(columns=["symbol", "date"]).set_index(pd.DatetimeIndex(one["ts"]))
    bl = m.build(live)
    pos = np.searchsorted(b["sel"], one.index.to_numpy())
    skip = [m.FEATS.index("is_etf"), m.FEATS.index("log_adv")]      # need symbol / adv20 (live gaps, documented)
    keep = [i for i in range(len(m.FEATS)) if i not in skip]
    assert np.allclose(XL[pos][:, keep], m.side_features(bl, 1)[:, keep], equal_nan=True)
    assert np.allclose(XS[pos][:, keep], m.side_features(bl, -1)[:, keep], equal_nan=True)
    # point-in-time: truncate the symbol-day at bar j; features of bar j unchanged
    for j in (5, 20, 40):
        tr = one.iloc[: j + 1]
        bt = m.build(tr)
        assert np.allclose(m.side_features(bt, 1)[-1], XL[pos[j]], equal_nan=True)
        assert np.allclose(m.side_features(bt, -1)[-1], XS[pos[j]], equal_nan=True)
        for k in b["ev"]:
            assert bt["ev"][k][-1] == b["ev"][k][pos[j]]
    # no short of a leveraged ETF
    assert not m.side_rows(b, -1, "L2")[(f.symbol.to_numpy()[b["sel"]] == "TQQQ")].any()
