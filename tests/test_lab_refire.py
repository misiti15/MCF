"""LabStrategy refire mode (owner 2026-10-14, research/bdi/refire1014): 2nd+ signals of a setup on a symbol-day,
with a cooldown in decision bars, inside the setup's window; off = the first-qualifying-bar behaviour unchanged."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from mcf.strategies.setups import _LAB_FRAMES, LabStrategy, build_strategies, refire_select

# qualifying decision bars (bar-close HHMM): a continuous run 10:00-10:20, then 11:00 and 14:00
MOD_SRC = '''
import numpy as np
SIDE = "short"
GEOM = "t1s1"
LAYERS = ["test"]
QUAL = {1000, 1005, 1010, 1015, 1020, 1100, 1400}
def mask(df):
    return np.isin(df["tod"].to_numpy(), list(QUAL))
'''


@pytest.fixture
def mod(tmp_path):
    p = tmp_path / "refire_mod.py"
    p.write_text(MOD_SRC)
    return str(p)


def _ctx(minutes=390, sym="RF"):
    idx = pd.date_range("2026-10-14 09:30", periods=minutes, freq="1min", tz="America/New_York")
    px = 100 + 0.5 * np.sin(np.arange(minutes) / 7.0)
    bars = pd.DataFrame({"open": px, "high": px + 0.05, "low": px - 0.05, "close": px, "volume": 1000.0}, index=idx)
    return SimpleNamespace(symbol=sym, date=idx[0].date(), bars=bars, prior5=None, atr=2.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9)


def _hhmm(ctx, sigs):
    out = []
    for s in sigs:
        ts = ctx.bars.index[s.bar_index] + pd.Timedelta(minutes=1)
        out.append(ts.hour * 100 + ts.minute)
    return out


def test_refire_select_cooldown():
    hits = [2, 3, 4, 5, 6, 14, 15, 30]
    assert refire_select(hits, 0) == hits
    assert refire_select(hits, 1) == [2, 4, 6, 14, 30]
    assert refire_select(hits, 3) == [2, 6, 14, 30]
    assert refire_select(hits, 6) == [2, 14, 30]
    assert refire_select(hits, 1, valid=lambda i: i != 2) == [3, 5, 14, 30]   # an invalid bar starts no cooldown
    assert refire_select([], 1) == []


def test_off_is_first_bar_only_and_identical(mod):
    _LAB_FRAMES.clear()
    ctx = _ctx()
    off = LabStrategy("off", mod, window=[950, 1500])
    default = LabStrategy("dflt", mod, window=[950, 1500], refire=False, refire_cooldown=3)
    a, b = off.signals(ctx), default.signals(ctx)
    assert _hhmm(ctx, a) == [1000] == _hhmm(ctx, b)
    assert (a[0].bar_index, a[0].stop, a[0].target) == (b[0].bar_index, b[0].stop, b[0].target)
    assert off.max_signals_per_day == 1 and "refire" not in a[0].meta


@pytest.mark.parametrize("cd,want", [(1, [1000, 1010, 1020, 1100, 1400]), (3, [1000, 1020, 1100, 1400]),
                                     (6, [1000, 1100, 1400]), (0, [1000, 1005, 1010, 1015, 1020, 1100, 1400])])
def test_refire_cooldown_full_day(mod, cd, want):
    _LAB_FRAMES.clear()
    ctx = _ctx()
    st = LabStrategy("on", mod, window=[950, 1500], refire=True, refire_cooldown=cd)
    sigs = st.signals(ctx)
    assert _hhmm(ctx, sigs) == want
    assert [s.meta["refire"] for s in sigs] == [False] + [True] * (len(want) - 1)
    for s in sigs:   # every refire signal carries its own bar's bracket
        px = float(ctx.bars["close"].iloc[s.bar_index])
        assert s.stop == pytest.approx(px + 0.5) and s.target == pytest.approx(px - 0.5)


def test_refire_respects_window(mod):
    _LAB_FRAMES.clear()
    ctx = _ctx()
    st = LabStrategy("win", mod, window=[1005, 1100], refire=True, refire_cooldown=1)
    assert _hhmm(ctx, st.signals(ctx)) == [1005, 1015, 1100]   # 10:00 and 14:00 are outside the window


def test_refire_live_latest_bar(mod):
    """Live: at each 5-minute poll the latest completed bar fires only if the chain picks it (same chain as backtest)."""
    st = LabStrategy("live", mod, window=[950, 1500], refire=True, refire_cooldown=1)
    fired = []
    for n in range(25, 390, 5):
        _LAB_FRAMES.clear()
        ctx = _ctx(n)
        if not st.eligible(ctx):
            continue
        last = len(ctx.bars) - 1
        fired += _hhmm(ctx, [s for s in st.signals(ctx) if s.bar_index == last])
    assert fired == [1000, 1010, 1020, 1100, 1400]
    _LAB_FRAMES.clear()
    off = LabStrategy("live_off", mod, window=[950, 1500])
    fired = []
    for n in range(25, 390, 5):
        _LAB_FRAMES.clear()
        ctx = _ctx(n)
        if off.eligible(ctx):
            last = len(ctx.bars) - 1
            fired += _hhmm(ctx, [s for s in off.signals(ctx) if s.bar_index == last])
    assert fired == [1000]


def test_build_strategies_live_default_and_override(mod):
    cfg = {"live": {"lab_refire": True, "lab_refire_cooldown": 3},
           "strategies": {"a": {"type": "lab", "module": mod},
                          "b": {"type": "lab", "module": mod, "refire": False},
                          "c": {"type": "lab", "module": mod, "refire_cooldown": 6}}}
    st = {s.name: s for s in build_strategies(cfg)}
    assert (st["a"].refire, st["a"].refire_cooldown) == (True, 3)
    assert st["b"].refire is False and st["b"].max_signals_per_day == 1
    assert (st["c"].refire, st["c"].refire_cooldown) == (True, 6)
    st = {s.name: s for s in build_strategies({"strategies": cfg["strategies"]})}
    assert st["a"].refire is False and st["a"].refire_cooldown == 1     # no live default: off


def test_negative_cooldown_rejected(mod):
    with pytest.raises(ValueError):
        LabStrategy("bad", mod, refire=True, refire_cooldown=-1)
