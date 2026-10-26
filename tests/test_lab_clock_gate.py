"""GX1 clock gate (owner 2026-10-26, research/ops/genexposure1025.md): a lab setup is evaluated when the latest 1-minute
bar completes a 5-minute clock bucket (the buckets of resample(bars, '5min')), not when the bar count is a multiple of 5.
A symbol that missed a minute earlier in the day is still evaluated at each bucket; each bucket is evaluated once per
setup and symbol, also across a runner restart; only completed buckets are decided (no lookahead); no catch-up of
older buckets."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from mcf.config import load_config
from mcf.execution import runner as R
from mcf.strategies import setups as S
from mcf.strategies.setups import _LAB_FRAMES, LabStrategy, lab_decision_buckets

NY = "America/New_York"
MOD_SRC = '''
import numpy as np
SIDE = "long"
GEOM = "t1s1"
LAYERS = ["test"]
QUAL = {1000}
def mask(df):
    return np.isin(df["tod"].to_numpy(), list(QUAL))
'''


@pytest.fixture
def mod(tmp_path):
    p = tmp_path / "gate_mod.py"
    p.write_text(MOD_SRC)
    return str(p)


def _bars(drop=(), n=390):
    idx = pd.date_range("2026-10-26 09:30", periods=n, freq="1min", tz=NY)
    idx = idx[~idx.strftime("%H:%M").isin(list(drop))]
    px = 100 + 0.5 * np.sin(np.arange(len(idx)) / 7.0)
    return pd.DataFrame({"open": px, "high": px + 0.05, "low": px - 0.05, "close": px, "volume": 1000.0}, index=idx)


def _ctx(bars, sym="GX"):
    return SimpleNamespace(symbol=sym, date=bars.index[0].date(), bars=bars, prior5=None, atr=2.0, prev_close=100.0,
                           prev_high=101.0, prev_low=99.0, avg_dollar_volume=1e9)


def _old_gate(index):
    n = len(index)
    return [index[-1] - pd.Timedelta(minutes=4)] if n >= 5 and n % 5 == 0 else []


def _polls(st, bars, gate=None):
    """Live-style: one poll per new bar; the runner acts only on a signal of the latest bar. Returns fired bar times."""
    saved = S.lab_decision_buckets
    if gate is not None:
        S.lab_decision_buckets = gate
    try:
        fired = []
        for k in range(1, len(bars)):   # n == 390 is the backtest's full-day context
            _LAB_FRAMES.clear()
            ctx = _ctx(bars.iloc[:k])
            if not st.eligible(ctx):
                continue
            last = len(ctx.bars) - 1
            fired += [f"{ctx.bars.index[s.bar_index]:%H:%M}" for s in st.signals(ctx) if s.bar_index == last]
        return fired
    finally:
        S.lab_decision_buckets = saved


def test_full_minute_names_unchanged():
    """A name trading every minute: decided exactly when the old count test fired, on the same bucket."""
    b = _bars()
    for k in range(1, 390):
        idx = b.index[:k]
        new, old = lab_decision_buckets(idx), _old_gate(idx)
        assert [str(x) for x in new] == [str(x) for x in old], k


def test_missing_minute_symbol_still_evaluated(mod):
    """09:41 missing: every later count is off by one, so the old gate never evaluated the 09:55 bucket (bar close
    10:00); the clock gate evaluates it at its 4th-minute bar 09:59, as the screen / backtest do."""
    st = LabStrategy("gx", mod, window=[950, 1500])
    b = _bars(drop=["09:41"])
    assert _polls(st, b, gate=_old_gate) == []
    assert _polls(st, b) == ["09:59"]
    full = LabStrategy("gx_full", mod, window=[950, 1500])
    _LAB_FRAMES.clear()
    fb = _bars()
    assert [f"{fb.index[s.bar_index]:%H:%M}" for s in full.signals(_ctx(fb))] == ["09:59"]   # backtest: same bar


def test_missing_fourth_minute_decided_by_next_bar(mod):
    """09:59 missing: the 09:55 bucket completes with the next bar (10:00), the bar _signal already uses; the entry
    reference is the bucket's own close (09:58), nothing after it."""
    st = LabStrategy("gx4", mod, window=[950, 1500])
    b = _bars(drop=["09:59"])
    assert _polls(st, b) == ["10:00"]
    _LAB_FRAMES.clear()
    ctx = _ctx(b[b.index <= pd.Timestamp("2026-10-26 10:00", tz=NY)])
    sig = st.signals(ctx)[0]
    assert sig.stop == pytest.approx(float(b.loc[pd.Timestamp("2026-10-26 09:58", tz=NY), "close"]) - 0.5)


def test_two_buckets_one_decision_bar():
    """09:57..10:03 missing: 10:04 decides the 09:55 bucket (no 4th-minute bar) and its own 10:00 bucket."""
    b = _bars(drop=["09:57", "09:58", "09:59", "10:00", "10:01", "10:02", "10:03"])
    idx = b.index[b.index <= pd.Timestamp("2026-10-26 10:04", tz=NY)]
    assert [f"{x:%H:%M}" for x in lab_decision_buckets(idx)] == ["09:55", "10:00"]
    assert lab_decision_buckets(idx[:-1]) == []          # 09:56: the 09:55 bucket is not complete yet


def test_no_lookahead():
    """A bucket is only ever decided once it is complete (bucket end <= latest bar + 1 min), and only by the latest
    bar: the answer for a prefix never depends on later bars."""
    b = _bars(drop=["09:41", "10:13", "10:14", "11:02", "11:03", "11:04", "11:05", "11:06"])
    one = pd.Timedelta(minutes=1)
    seen = []
    for k in range(1, len(b) + 1):
        idx = b.index[:k]
        got = lab_decision_buckets(idx)
        for x in got:
            assert x + pd.Timedelta(minutes=5) <= idx[-1] + one       # complete
            assert idx[-1] >= x + pd.Timedelta(minutes=4)               # decided by its first bar at/after minute 4
            assert k == 1 or idx[-2] < x + pd.Timedelta(minutes=4)      # ... and not by an earlier bar
        seen += got
    assert len(seen) == len(set(seen))                                  # every bucket decided once
    d5 = pd.Series(1, index=b.index).resample("5min").count()
    assert set(seen) == set(d5[d5 > 0].index)                           # ... and every non-empty bucket is decided


# ---------------------------------------------------------------- runner: once per bucket, also across a restart
def _runner(tmp_path, monkeypatch, st, bars):
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["live"]["same_setup_reentry"] = False
    r = R.PaperRunner(cfg, [st], {}, broker=SimpleNamespace(equity=lambda: 1e5))
    r.dry_run = True
    r.today = bars.index[0].date()
    for k in ("manage", "scale_outs", "_escalate"):
        monkeypatch.setattr(r, k, lambda *a, **kw: None)
    monkeypatch.setattr(r, "_check_data", lambda now, b: False)
    monkeypatch.setattr(r, "fetch", lambda now: {})
    r.poll_log_dir = None
    r.feed = {"bars": bars}
    monkeypatch.setattr(r, "_contexts", lambda b, today: [_ctx(r.feed["bars"])])
    entered = []

    def enter(sig, px, key, ctx, now):
        entered.append(f"{ctx.bars.index[sig.bar_index]:%H:%M}")
        r._log(sig, "dry_run", "dry run", px, now)
    monkeypatch.setattr(r, "_enter", enter)
    return r, entered


class Counting(LabStrategy):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.calls = 0

    def generate(self, ctx):
        self.calls += 1
        return super().generate(ctx)


def test_runner_evaluates_each_bucket_once(tmp_path, monkeypatch, mod):
    st = Counting("gxr", mod, window=[950, 1500])
    b = _bars(drop=["09:41"])
    upto = lambda hhmm: b[b.index <= pd.Timestamp(f"2026-10-26 {hhmm}", tz=NY)]   # noqa: E731
    r, entered = _runner(tmp_path, monkeypatch, st, upto("09:59"))
    now = pd.Timestamp("2026-10-26 10:00:03", tz=NY)
    for _ in range(3):                      # no new bar for three polls: the 09:55 bucket is evaluated once
        _LAB_FRAMES.clear()
        r.step(now)
    assert st.calls == 1 and entered == ["09:59"]
    r.feed["bars"] = upto("10:01")          # 10:00, 10:01: the 10:00 bucket is not complete, nothing evaluated
    r.step(now)
    assert st.calls == 1
    r.feed["bars"] = upto("10:04")          # 10:00 bucket complete: evaluated (the setup already fired today: seen)
    r.step(now)
    assert entered == ["09:59"]


def test_restart_does_not_fire_a_bucket_twice(tmp_path, monkeypatch, mod):
    b = _bars(drop=["09:41"])
    bars = b[b.index <= pd.Timestamp("2026-10-26 09:59", tz=NY)]
    now = pd.Timestamp("2026-10-26 10:00:03", tz=NY)
    st = LabStrategy("gxs", mod, window=[950, 1500])
    r, entered = _runner(tmp_path, monkeypatch, st, bars)
    _LAB_FRAMES.clear()
    r.step(now)
    assert entered == ["09:59"]
    st2 = Counting("gxs", mod, window=[950, 1500])
    r2, entered2 = _runner(tmp_path, monkeypatch, st2, bars)   # same journal: a restart in the same minute
    r2.restore(bars.index[0].date())
    _LAB_FRAMES.clear()
    r2.step(now)
    assert entered2 == [] and st2.calls == 0                   # journal dedupe: (symbol, setup) already handled today
    assert len(r2.journal.signals(r2.run_id, "2026-10-26")) == 1


def test_replay_fast_path_uses_the_same_gate():
    """The replay's poll gate calls the very function live uses (so replay validation covers the gate)."""
    import inspect

    from mcf.replay import fast

    src = inspect.getsource(fast.FastSession.can_act) + inspect.getsource(fast.FastSession._gen_wrap)
    assert src.count("S.lab_decision_buckets(") == 2
    assert "n % 5:" not in src
