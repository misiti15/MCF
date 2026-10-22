"""OPS-POLL 2026-10-22 (research/ops/pollspeed1022.md): the lab-context cache key is computed once per poll's peers
object instead of once per (context setup, symbol) call. Same answers, same signals; only faster.
Educational only - not financial advice."""
import time

import numpy as np
import pandas as pd
import pytest

from mcf.data.synthetic import make_universe
from mcf.strategies import lab_context as LC
from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

CTX = list(LC.CONTEXT_COLS)
SYMS = ["SPY", "QQQ"] + [f"S{i:02d}" for i in range(14)]

MOD = '''
import numpy as np
SIDE = "long"
GEOM = "t1s1"
LAYERS = ["pollspeed"]
def mask(df):
    with np.errstate(invalid="ignore"):
        return (df["breadth"].to_numpy(float) >= BR) & (df["spy_fo"].to_numpy(float) > -99)
'''


def _old_key(peers):
    last = max((b.index[-1] for b in peers.values() if b is not None and len(b)), default=None)
    first = min((b.index[0] for b in peers.values() if b is not None and len(b)), default=None)
    return (len(peers), first, last, sum(len(b) for b in peers.values() if b is not None))


@pytest.fixture(autouse=True)
def _clear():
    LC._CACHE.clear()
    _LAB_FRAMES.clear()
    yield
    LC._CACHE.clear()
    _LAB_FRAMES.clear()


@pytest.fixture(scope="module")
def day():
    data = make_universe(SYMS, days=2, start="2025-03-03")
    d = sorted({x for df in data.values() for x in df.index.date})[-1]
    return {s: df[df.index.date == d] for s, df in data.items()}


def _cut(peers, n):
    t0 = min(b.index[0] for b in peers.values()).normalize() + pd.Timedelta(hours=9, minutes=30)
    cut = t0 + pd.Timedelta(minutes=n)
    return {s: b[b.index < cut] for s, b in peers.items()}


def _ctx(sym, peers):
    from types import SimpleNamespace

    b = peers[sym]
    return SimpleNamespace(symbol=sym, date=b.index[0].date(), bars=b, prior5=None, atr=2.0,
                           prev_close=float(b["open"].iloc[0]), prev_high=1e9, prev_low=0.0, avg_dollar_volume=1e9,
                           peers=peers)


def test_key_memo_equals_uncached_key(day):
    for n in (20, 95, 200, 389):
        p = _cut(day, n)
        assert LC._peers_key(p) == _old_key(p)
        assert LC._peers_key(p) == _old_key(p)                     # memo hit: same answer


def test_key_memo_invalidates_on_new_poll_or_replaced_frame(day):
    p1 = _cut(day, 100)
    k1 = LC._peers_key(p1)
    p2 = _cut(day, 105)                                            # the next poll: a new dict
    assert LC._peers_key(p2) == _old_key(p2) != k1
    p2["S01"] = day["S01"]                                         # same dict, a frame replaced (longer)
    assert LC._peers_key(p2) == _old_key(p2)
    t_before = LC.context_table(p1, CTX)
    LC._CACHE.clear()
    pd.testing.assert_frame_equal(t_before, LC.context_table(p1, CTX))


def test_context_table_same_as_before(day, monkeypatch):
    """Every poll's context table (and so every context column a mask sees) is identical with and without the memo."""
    for n in (25, 60, 150, 300, 390):
        p = _cut(day, n)
        new = LC.context_table(p, CTX)
        LC._CACHE.clear()
        with monkeypatch.context() as m:
            m.setattr(LC, "_peers_key", _old_key)
            old = LC.context_table(p, CTX)
        LC._CACHE.clear()
        pd.testing.assert_frame_equal(new, old)


def test_signals_identical_on_a_synthetic_day(day, tmp_path, monkeypatch):
    """A context lab setup polled every minute of a synthetic day, every symbol: the same signals with the memo as
    with the uncached key (equivalence of the live decision path)."""
    full = LC.context_table(day, CTX)
    br = float(np.nanquantile(full["breadth"], 0.5))
    path = tmp_path / "ps_mod.py"
    path.write_text(MOD.replace("BR", repr(br)))

    def run(key):
        monkeypatch.setattr(LC, "_peers_key", key)
        LC._CACHE.clear()
        _LAB_FRAMES.clear()
        st = LabStrategy("ps", str(path), window=[950, 1500], context=True, refire=True, refire_cooldown=0)
        out = []
        for n in sorted({*range(20, 391, 5), *range(21, 391, 25)}):
            p = _cut(day, n)
            for sym in SYMS[2:10]:
                c = _ctx(sym, p)
                if st.eligible(c):
                    out += [(n, sym, s.bar_index, s.side, round(s.stop, 9)) for s in st.signals(c)
                            if s.bar_index == len(c.bars) - 1]
        return out

    new = run(LC._peers_key)
    old = run(_old_key)
    assert new and new == old


def test_key_walk_runs_once_per_poll(day, monkeypatch):
    """Timing: N context setups x M symbols in one poll walk the peers once (it was once per call: ~70 ms each with
    ~4,000 live symbols, which made Gen / Testing 2 polls take 3-5 minutes)."""
    big = dict(day)
    for i in range(400):                                           # a wider poll (more peers)
        big[f"X{i:03d}"] = day["S00"]
    p = _cut(big, 120)
    walks = {"n": 0}
    real_max = max

    def counting_max(*a, **k):
        walks["n"] += 1
        return real_max(*a, **k)

    f = pd.DataFrame({"tod": np.arange(24)}, index=pd.date_range(p["SPY"].index[0], periods=24, freq="5min"))
    monkeypatch.setattr(LC, "max", counting_max, raising=False)
    t0 = time.perf_counter()
    for _ in range(40 * 10):                                       # 40 context setups x 10 symbols
        LC.add_context(f, p, CTX)
    fast = time.perf_counter() - t0
    assert walks["n"] == 1
    monkeypatch.setattr(LC, "_peers_key", _old_key)
    t0 = time.perf_counter()
    for _ in range(40 * 10):
        LC.add_context(f, p, CTX)
    slow = time.perf_counter() - t0
    assert fast < slow


def test_resample_memo_only_for_the_same_bars_object(day, tmp_path, monkeypatch):
    """LabStrategy.generate reuses the 5-minute resample only for the very same ctx.bars object (one poll, one
    symbol, every setup); a new or revised bars object is resampled afresh. Signals are identical with the memo off."""
    from mcf.data import bars as B
    from mcf.strategies import setups as S

    full = LC.context_table(day, CTX)
    br = float(np.nanquantile(full["breadth"], 0.4))
    path = tmp_path / "ps_mod2.py"
    path.write_text(MOD.replace("BR", repr(br)))
    sts = [LabStrategy(f"ps{i}", str(path), window=[950, 1500], context=True, refire=True, refire_cooldown=0)
           for i in range(3)]
    calls = {"n": 0}
    real = B.resample

    def counting(df, rule):
        if df is c.bars or df is revised.get("S02"):       # the setup's own resample (context builds use others)
            calls["n"] += 1
        return real(df, rule)

    p = _cut(day, 100)
    c = _ctx("S02", p)
    revised = {}
    monkeypatch.setattr(B, "resample", counting)
    a = [[(s.bar_index, s.side) for s in st.signals(c)] for st in sts]
    assert calls["n"] == 1                                           # three setups, one resample
    revised.update({k: v.copy() for k, v in p.items()})
    revised["S02"].iloc[-1, revised["S02"].columns.get_loc("close")] *= 1.01
    _LAB_FRAMES.clear()
    for st in sts:
        st.signals(_ctx("S02", revised))
    assert calls["n"] == 2                                           # a new bars object: resampled again

    class Never(list):
        def __getitem__(self, i):
            return object() if i == 0 else None

        def __setitem__(self, i, v):
            pass

    _LAB_FRAMES.clear()
    monkeypatch.setattr(S, "_LAB_D5", Never([None, None]))
    b = [[(s.bar_index, s.side) for s in st.signals(c)] for st in sts]
    assert a == b
