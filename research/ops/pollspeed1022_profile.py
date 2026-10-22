"""OPS-POLL 2026-10-22: time the live runner's per-poll path offline (no broker, no orders, no network).

    python research/ops/pollspeed1022_profile.py 2026-10-16 gen,testing2,primary,testing old,new [HH:MM,...]

Builds the real PaperRunner on a recorded session from the replay store (mcf/replay: the simulated clock, feed, quotes
and broker the replay harness uses; exact mode = no replay fast path), restores, then calls runner.step() at a set of
poll minutes and times each poll by phase with wall-clock wrappers (inclusive times; cProfile is not used because its
per-generator-step overhead inflates the old peers-key walk ~10x). `old` swaps lab_context._peers_key back to the
un-memoised key and turns the per-setup resample memo off (the code before the fix), so before/after run on identical inputs.
Universe: the replay store's lab universe (~1,200 symbols) - live polls ~4,000, so live costs of the peers walk are
~3x per call and ~3x more calls (scale noted in research/ops/pollspeed1022.md). Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict

import pandas as pd

from mcf.replay import harness
from mcf.replay.broker import NY, SimClock, SimDataClient, SimMarket, SimTradingClient
from mcf.strategies import lab_context as LC

POLLS = ["10:00", "10:01", "11:00", "13:30"]       # 10:00 / 11:00 / 13:30 = 5-minute decision bars, 10:01 not


def _old_key(peers):
    last = max((b.index[-1] for b in peers.values() if b is not None and len(b)), default=None)
    first = min((b.index[0] for b in peers.values() if b is not None and len(b)), default=None)
    return (len(peers), first, last, sum(len(b) for b in peers.values() if b is not None))


class _NoMemo(list):
    """`old` mode: the per-setup resample memo never hits (code before the fix)."""

    def __init__(self):
        super().__init__([None, None])

    def __getitem__(self, i):
        return object() if i == 0 else None

    def __setitem__(self, i, v):
        pass


class Timers:
    def __init__(self):
        self.t = defaultdict(float)
        self.n = defaultdict(int)

    def wrap(self, label, fn):
        def w(*a, **k):
            t0 = time.perf_counter()
            try:
                return fn(*a, **k)
            finally:
                self.t[label] += time.perf_counter() - t0
                self.n[label] += 1
        return w


def run(day: str, account: str, mode: str, polls) -> dict:
    from mcf.execution import runner as R
    from mcf.execution.alpaca_broker import AlpacaBroker
    from mcf.research import heat as H
    from mcf.research import setup_lab as SL
    from mcf.strategies import setups as S
    from mcf.strategies.setups import build_strategies

    cfg = harness.account_config(account)
    cfg = json.loads(json.dumps(cfg, default=str))
    cfg["data"]["journal_path"] = ":memory:"
    bars, priors, notes = harness.session_inputs(cfg, day, universe="lab")
    d = pd.Timestamp(day).date()
    market = SimMarket(d, bars)
    clock = SimClock(pd.Timestamp(f"{d} 09:29:50", tz=NY))
    client = SimTradingClient(clock, market, cfg.get("costs"), equity=100_000.0, shortable=harness.shortable_flags())
    broker = AlpacaBroker.__new__(AlpacaBroker)
    broker.client = client
    T = Timers()
    saved = (LC._peers_key, LC.add_context, LC._breadth, H.heat_frame, SL.extra_features)
    saved_d5 = S._LAB_D5
    if mode == "old":
        S._LAB_D5 = _NoMemo()
    LC._peers_key = T.wrap("context: peers key walk", _old_key if mode == "old" else saved[0])
    LC.add_context = T.wrap("context: add_context (incl. key)", saved[1])
    LC._breadth = T.wrap("context: breadth build", saved[2])
    H.heat_frame = T.wrap("lab frame: heat_frame", saved[3])
    SL.extra_features = T.wrap("lab frame: extra_features", saved[4])
    out = {"account": account, "day": day, "mode": mode, "symbols": len(priors), "polls": []}
    try:
        with harness._patched(clock):
            quotes = SimDataClient(clock, market, 2.0, None)
            client.half_spread_bps = lambda sym, k: quotes._bps(sym, k) / 2
            strategies = build_strategies(cfg)
            r = R.PaperRunner(cfg, strategies, priors, broker=broker, data_client=quotes)
            r._utcnow = lambda: clock.now.tz_convert("UTC")
            feed = harness.ReplayFeed(r, bars)
            r.fetch = T.wrap("fetch (replay feed)", feed.fetch)
            for name in ("manage", "scale_outs", "_check_data", "_contexts", "_enter", "_log_poll"):
                setattr(r, name, T.wrap(f"runner.{name}", getattr(r, name)))
            for st in strategies:
                st.eligible = T.wrap("setup eligible()", st.eligible)
                st.signals = T.wrap("setup signals() (incl. frames, context, mask)", st.signals)
                if hasattr(st, "mod") and hasattr(st.mod, "mask"):
                    st.mod.mask = T.wrap("setup masks", st.mod.mask)
            r.restore(d)
            for hm in polls:
                now = pd.Timestamp(f"{d} {hm}:03", tz=NY)
                clock.now = now
                LC._CACHE.clear()
                S._LAB_FRAMES.clear()
                T.t.clear()
                T.n.clear()
                t0 = time.perf_counter()
                r.step(now)
                wall = time.perf_counter() - t0
                rec = {"t": hm, "wall_s": round(wall, 2), "contexts": len(r.ctxs),
                       "phases_s": {k: round(v, 2) for k, v in sorted(T.t.items(), key=lambda x: -x[1])},
                       "calls": dict(T.n)}
                out["polls"].append(rec)
                print(account, mode, hm, f"wall {wall:.1f}s ctxs {len(r.ctxs)}", rec["phases_s"],
                      {k: v for k, v in T.n.items() if k.startswith("context")}, flush=True)
    finally:
        LC._peers_key, LC.add_context, LC._breadth, H.heat_frame, SL.extra_features = saved
        S._LAB_D5 = saved_d5
    return out


if __name__ == "__main__":
    day = sys.argv[1]
    accts = sys.argv[2].split(",")
    modes = sys.argv[3].split(",") if len(sys.argv) > 3 else ["old", "new"]
    polls = sys.argv[4].split(",") if len(sys.argv) > 4 else POLLS
    res = [run(day, a, m, polls) for a in accts for m in modes]
    print("JSON " + json.dumps(res))
