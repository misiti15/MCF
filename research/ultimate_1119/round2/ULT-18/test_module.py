"""Smoke test: ULT-18 module - select_book ranks the cross-section exactly as specified (MOM / REV, excluded and blocked
names replaced by the next eligible one, no name on both sides); under the live LabStrategy both sides fire only at the
fixed decision bars when a book (runner hook set_book) puts the name inside its side's cut-off, never without a book or
without SPY context; the GEOM "S" stop sits 2u beyond the decision close; features are point-in-time.
    pytest -q research/ultimate_1119/round2/ULT-18/test_module.py
Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

MOD = str(Path(__file__).resolve().parents[2] / "modules" / "ULT-18.py")
ET = "America/New_York"


def _mod(name="ult18_t"):
    from importlib import util
    spec = util.spec_from_file_location(name, MOD)
    m = util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_select_book():
    m = _mod()
    xs = pd.DataFrame({"symbol": list("ABCDEFGH"), "k1": [3.0, 2.0, 1.0, 0.5, -0.5, -1.0, -2.0, -3.0],
                       "k2": np.nan, "adv20": 1e9, "ok_long": [False, True, True, True, True, True, True, True],
                       "ok_short": [True] * 7 + [False]})
    p, cut = m.select_book(xs, "k1", "MOM", 2)
    assert p == [("B", "long"), ("C", "long"), ("G", "short"), ("F", "short")]          # A not long-eligible, H not short
    assert cut == {"long": 1.0, "short": -1.0}
    p, _ = m.select_book(xs, "k1", "REV", 2, blocked={"G"})
    assert p == [("H", "long"), ("F", "long"), ("A", "short"), ("B", "short")]          # G blocked -> F
    p, cut = m.select_book(xs, "k2", "MOM", 2)
    assert p == [] and cut == {"long": None, "short": None}                             # missing key -> no book
    xs2 = xs.iloc[:3].copy()
    xs2["ok_long"] = True
    xs2["ok_short"] = True
    p, _ = m.select_book(xs2, "k1", "MOM", 2)
    assert len({s for s, _ in p}) == len(p) == 3                                        # no name on both sides


def _day(drift, gap=0.0):
    rng = np.random.default_rng(3)
    o = 100 * (1 + gap / 100)
    px = o + np.cumsum(drift + rng.normal(0, 0.02, 390))
    idx = pd.date_range("2026-11-18 09:30", periods=390, freq="1min", tz=ET)
    bars = pd.DataFrame({"open": np.r_[o, px[:-1]], "high": np.maximum(px, np.r_[o, px[:-1]]) + 0.01,
                         "low": np.minimum(px, np.r_[o, px[:-1]]) - 0.01, "close": px, "volume": 50000.0}, index=idx)
    spy = 600 + 0.005 * np.arange(390)
    spyb = pd.DataFrame({"open": spy, "high": spy + 0.01, "low": spy - 0.01, "close": spy, "volume": 1e6}, index=idx)
    return bars, {"SPY": spyb, "AAPL": bars}


def _ctx(bars, peers):
    return SimpleNamespace(symbol="AAPL", date=bars.index[0].date(), bars=bars, prior5=None, atr=5.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e10, peers=peers)


def _strat(name):
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy
    _LAB_FRAMES.clear()
    return LabStrategy(name, MOD, window=[1100, 1400], context=["spy_fo"], refire=True, refire_cooldown=0,
                       min_adv=200_000_000, geom="S", symbols="module")


def test_live_lab_strategy_both_sides():
    bars, peers = _day(0.01)                   # steady up day: K1 > 0 and growing
    L = _strat("ULT-18-L")
    assert L.side == 1 and "AAPL" in L.symbols
    assert L.signals(_ctx(bars, peers)) == []                           # no book -> nothing (fail safe)
    for t in (1100, 1300, 1400):
        L.mod.set_book("2026-11-18", t, {"long": 0.0, "short": -99.0}, key="k1", direction="MOM")
    sigs = L.signals(_ctx(bars, peers))
    times = sorted(bars.index[s.bar_index].strftime("%H%M") for s in sigs)
    assert times == ["1059", "1259", "1359"], times   # last minute of the 5-min bars closing 11:00 / 13:00 / 14:00
    s = sigs[0]
    e = float(bars["close"].iloc[s.bar_index])
    assert s.target is None and abs((e - s.stop) - 2 * 0.25 * 5.0) < 1e-6
    L.mod._BOOK.clear()
    for t in (1100, 1300, 1400):
        L.mod.set_book("2026-11-18", t, {"long": 99.0, "short": None}, key="k1", direction="MOM")
    assert L.signals(_ctx(bars, peers)) == []                           # key below the cut-off -> not in the book
    assert L.signals(_ctx(bars, None)) == []                            # no SPY context -> nothing
    S = _strat("ULT-18-S")
    assert S.side == -1
    S.mod._BOOK.clear()
    for t in (1100, 1300, 1400):
        S.mod.set_book("2026-11-18", t, {"long": None, "short": 0.0}, key="k1", direction="REV")
    ss = S.signals(_ctx(bars, peers))                                   # REV shorts the top names: up name qualifies
    assert len(ss) == 3 and all(x.side == -1 and x.stop > float(bars["close"].iloc[x.bar_index]) for x in ss)
    bg, pg = _day(0.01, gap=1.0)                                        # gap >= +0.5%: never shorted
    S2 = _strat("ULT-18-S")
    for t in (1100, 1300, 1400):
        S2.mod.set_book("2026-11-18", t, {"long": None, "short": 0.0}, key="k1", direction="REV")
    assert S2.signals(SimpleNamespace(**{**vars(_ctx(bg, pg)), "prev_close": 100.0})) == []


def test_point_in_time_features():
    import research.history2y.lib as lib
    m = _mod("ult18_p")
    lib.DATA = Path("/home/user/MCF/research/history2y/data")
    f = lib.load_month("2025-03", context=True)
    f["symbol"] = f["symbol"].astype(str)
    f = f[f.symbol.isin(["AAPL", "NVDA"])].reset_index(drop=True)
    f["sec_fo"], f["sec_beta"] = 0.1, 1.0
    full = m.features(f)
    cut = f[f.tod <= 1300].reset_index(drop=True)
    part = m.features(cut)
    sel = (f.tod <= 1300).to_numpy()
    for k in ("k1", "k2", "ok_long", "ok_short", "spy_r30"):
        assert np.allclose(np.asarray(full[k][sel], float), np.asarray(part[k], float), equal_nan=True), k
    assert set(np.unique(f.tod[full["ok_long"] | full["ok_short"]])) <= {1100, 1300, 1400}
