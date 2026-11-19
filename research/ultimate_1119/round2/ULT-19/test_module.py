"""Smoke test: ULT-19 module imports and runs under the live LabStrategy (context spy_fo) on BOTH sides (side from the
setup name), fires on a strong with-trend day for the side the score favours only, honours the refire thinning and the
2R catastrophic stop, fails safe without SPY context or without a model; and (if the frozen model and the 2-year frames
exist) the module's mask equals the backtest's candidate rule on real frames (parity).
    pytest -q research/ultimate_1119/round2/ULT-19/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

UL = Path(__file__).resolve().parents[2]
MOD = str(UL / "modules" / "ULT-19.py")
ET = "America/New_York"
# toy model: score = 1.0 x signed fromOpen(dATR) z-score; everything else 0
TOY = {"universe": "UA", "min_adv": 50e6, "cost_r_max": 0.10, "tau": 0.5,
       "mean": [0.0] * 14, "sd": [1.0] * 5 + [1.0, 0.3, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
       "w": [0.0] * 6 + [1.0] + [0.0] * 7}


def _day(sgn):
    rng = np.random.default_rng(7)
    o = 100.0
    steps = sgn * 0.02 + rng.normal(0, 0.05, 390)
    px = o + np.cumsum(steps)
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz=ET)
    bars = pd.DataFrame({"open": np.r_[o, px[:-1]], "high": np.maximum(px, np.r_[o, px[:-1]]) + 0.01,
                         "low": np.minimum(px, np.r_[o, px[:-1]]) - 0.01, "close": px, "volume": 30000.0}, index=idx)
    spy = np.full(390, 600.0)
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="ULTX", date=bars.index[0].date(), bars=bars, prior5=None, atr=4.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9, peers=peers)


def _strategy(name, model):
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy
    _LAB_FRAMES.clear()
    st = LabStrategy(name, MOD, window=[950, 1500], context=["spy_fo"], refire=True, refire_cooldown=0,
                     min_adv=50_000_000, geom="S")
    st.mod.MODEL, st.mod.TAU, st.mod.COST_R_MAX = model, (model or {}).get("tau", np.inf), 0.10
    return st


def _check(name, sgn):
    bars, peers = _day(sgn)
    st = _strategy(name, TOY)
    assert st.side == sgn
    sigs = st.signals(_ctx(bars, peers))
    assert 1 <= len(sigs) <= 2, len(sigs)
    times = [bars.index[s.bar_index] for s in sigs]
    assert all(pd.Timestamp("2026-11-18 09:45", tz=ET) <= t <= pd.Timestamp("2026-11-18 15:00", tz=ET) for t in times)
    if len(sigs) == 2:
        assert times[1] - times[0] >= pd.Timedelta(minutes=75)
    s = sigs[0]
    e = float(bars["close"].iloc[s.bar_index])
    assert s.side == sgn and s.target is None and abs(sgn * (e - s.stop) - 2.0) < 1e-6   # 2 x 0.25 x atr 4.0
    # fail safe: no SPY context -> no signal; no model -> no signal
    from mcf.strategies.setups import _LAB_FRAMES
    _LAB_FRAMES.clear()
    assert st.signals(_ctx(bars, None)) == []
    assert _strategy(name, None).signals(_ctx(bars, peers)) == []
    # the other side never fires on this day (its score is the negative of this one)
    other = _strategy("ULT-19-S" if sgn > 0 else "ULT-19-L", TOY)
    assert other.side == -sgn and other.signals(_ctx(bars, peers)) == []


def test_long_side():
    _check("ULT-19-L", 1)


def test_short_side():
    _check("ULT-19-S", -1)


def test_parity_with_backtest():
    """Module mask (unthinned) == backtest candidates with score > tau on one real check-free FIT month."""
    import importlib.util
    import json
    mj = UL / "modules" / "ULT-19_model.json"
    if not mj.exists() or not Path("/home/user/MCF/research/history2y/data/frames/month=2025-06").exists():
        pytest.skip("frozen model or frames missing")
    spec = importlib.util.spec_from_file_location("ult19_bt_t", str(Path(__file__).with_name("bt.py")))
    bt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bt)
    model = json.loads(mj.read_text())
    import pyarrow.dataset as pads
    f = pads.dataset("/home/user/MCF/research/history2y/data/frames/month=2025-06", format="parquet").to_table(
        columns=bt.FRAME_COLS).to_pandas()
    f["date"] = pd.to_datetime(f["date"]).dt.date.astype(str)
    f = f[f.date <= "2025-06-06"]
    c = pd.read_parquet("/home/user/MCF/research/history2y/data/context/month=2025-06.parquet", columns=["date", "tod", "spy_fo"])
    c["date"] = pd.to_datetime(c["date"]).dt.date.astype(str)
    f = f.merge(c, on=["date", "tod"], how="left").sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    f = f[f.adv20 >= model["min_adv"]].reset_index(drop=True)   # ADV is the YAML min_adv live (ETB: shorts only)
    spec2 = importlib.util.spec_from_file_location("ULT-19-L", MOD)
    mod = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(mod)
    mod.THIN = False
    hits = set(zip(f.symbol[mod.mask(f)], f.date[mod.mask(f)], f.tod[mod.mask(f)]))
    F = bt.month_features(("2025-06", False))
    F = F[(F.date <= "2025-06-06")].reset_index(drop=True)
    F["symbol"] = F["symbol"].astype("category")
    C = bt.candidates(mod, F, np.ones(len(F), bool), model)
    C = C[(C.pred > model["tau"]) & (C.side == 1)]
    ref = set(zip(C.symbol, C.date, C.tod.astype(int)))
    assert hits == ref, (len(hits), len(ref), len(hits ^ ref))
