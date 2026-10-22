"""Replay one recorded session through the real live runner (mcf.execution.runner.PaperRunner.run).

What is real: the runner's whole loop - restore, poll cadence, fetch -> manage -> scale-outs -> stale-data check ->
contexts (universe, in-play, ranking) -> every setup's eligible()/signals() -> dedupe / re-entry / twin / caps / risk
checks -> quote cross-check and fill-realism -> sizing -> bracket submission through AlpacaBroker -> trade management ->
reconcile (mcf.execution.reconcile) -> 15:55 flatten -> what-if of every signal not taken. The priors are the live
prep's (mcf.data.priors.build_priors) computed from the replay store.

What is simulated (mcf.replay.broker): the clock (each poll at hh:mm:03, the live cadence without its fetch latency),
the market data feed (a poll sees exactly the 1-minute bars that existed before its minute), the latest quote (last
close +- a synthetic spread), and the broker (fills from the recorded bars; production costs or raw paper fills).

Known differences from true live (reported per session, measured in research/replay/VALIDATION.md): no fetch latency
or late/revised bars (the live poll log, live.log_poll_inputs, records them from 2026-10-22), synthetic quotes (spread
skips rarely fire), the universe is the lab universe (research/lab_symbols.txt, ~1,200 most liquid names) intersected
with the live universe when it is on record, breadth context is computed over that universe, shortability is taken as
today's flags. Educational only - not financial advice."""

from __future__ import annotations

import json
import os
import time as _wall
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import store
from .broker import NY, SimClock, SimDataClient, SimMarket, SimTime, SimTradingClient

DISCLAIMER = "Educational only - not financial advice."


class ReplayFeed:
    """runner.fetch replacement: at a poll in minute m, every watchlist symbol's bars that started before m."""

    def __init__(self, runner, day_bars: dict[str, pd.DataFrame]):
        self.r = runner
        self.bars = {s: b for s, b in day_bars.items() if s in set(runner.watchlist) and len(b)}
        self.ns = {s: b.index.as_unit("ns").asi8 for s, b in self.bars.items()}
        self.cache: dict[str, tuple[int, pd.DataFrame]] = {}
        self.on_slice = None              # fast path: rvol registry

    def fetch(self, now: pd.Timestamp):
        cut = now.floor("1min")
        c = cut.value
        out = {}
        for s, b in self.bars.items():
            k = int(np.searchsorted(self.ns[s], c, side="left"))
            if k == 0:
                continue
            old = self.cache.get(s)
            if old is None or old[0] != k:
                new = (k, b.iloc[:k])
                self.cache[s] = new
                if self.on_slice is not None:
                    self.on_slice(s, k, new[1], None if old is None else old[1])
                old = new
            out[s] = old[1]
        last_min = cut - pd.Timedelta(minutes=1)
        r = self.r
        r.bars = out
        r.health.update(polls=r.health["polls"] + 1, last_poll_s=0.0,
                        symbols_last_bar=sum(1 for b in out.values() if b.index[-1] >= last_min),
                        last_bar=str(last_min.time())[:5])
        r.last_fetch = cut
        return out


@contextmanager
def _patched(clock: SimClock):
    """Module-level wall-clock hooks of the live code -> the replay clock (restored afterwards)."""
    from .. import journal as J
    from ..execution import runner as R

    class _DT(datetime):
        @classmethod
        def now(cls, tz=None):
            n = clock.now.tz_convert("UTC").to_pydatetime()
            return n.astimezone(tz) if tz else n.replace(tzinfo=None)

    saved = (R._time, J.datetime)
    R._time, J.datetime = SimTime(clock), _DT
    try:
        yield
    finally:
        R._time, J.datetime = saved


def shortable_flags() -> dict:
    """symbol -> (shortable, easy_to_borrow) from the newest universe.csv we have (today's flags; labelled)."""
    p = store.ROOT / "data" / "universe.csv"
    if not p.exists():
        return {}
    u = pd.read_csv(p, usecols=["symbol", "shortable", "easy_to_borrow"])
    return {str(s): (bool(a), bool(b)) for s, a, b in zip(u.symbol, u.shortable, u.easy_to_borrow)}


def run_session(cfg: dict, day, bars: dict[str, pd.DataFrame], priors: dict, *, fills: str = "costs",
                limit_fill: str = "through", exact: bool = False, check: int = 24, equity: float | None = None,
                spread_bps: float = 2.0, spreads: dict | None = None, shortable: dict | None = None, out_dir: str | Path | None = None,
                log=print) -> dict:
    """Replay `day` for the account config `cfg` (already merged; strategies enabled as wanted). Returns a dict with
    signals / trades / what-if / per-setup summary DataFrames and run stats; writes them under out_dir when given."""
    from ..execution import runner as R
    from ..execution.alpaca_broker import AlpacaBroker
    from ..strategies.setups import build_strategies

    t_start = _wall.time()
    day = pd.Timestamp(str(day)).date()
    cfg = json.loads(json.dumps(cfg, default=str))               # own copy (the runner and fast path keep refs)
    cfg["data"]["journal_path"] = ":memory:"
    market = SimMarket(day, bars)
    clock = SimClock(pd.Timestamp(f"{day} 09:29:50", tz=NY))
    ext = {s for s, p in priors.items() if p.adv < cfg["universe"]["min_avg_dollar_volume"]}
    client = SimTradingClient(clock, market, cfg.get("costs"), fills=fills, limit_fill=limit_fill,
                              equity=equity or float(cfg["account"].get("starting_equity", 100_000)),
                              shortable=shortable if shortable is not None else shortable_flags(), extended=ext)
    broker = AlpacaBroker.__new__(AlpacaBroker)
    broker.client = client
    strategies = build_strategies(cfg)
    fast = None
    with _patched(clock):
        spreads = store.load_spreads() if spreads is None else spreads
        r = R.PaperRunner(cfg, strategies, priors, broker=broker,
                          data_client=SimDataClient(clock, market, spread_bps, spreads or None))
        r._utcnow = lambda: clock.now.tz_convert("UTC")
        feed = ReplayFeed(r, bars)
        r.fetch = feed.fetch
        if not exact:
            from .fast import FastSession

            fast = FastSession(r, feed.bars, day).install()
            feed.on_slice = fast.on_slice
        quiet = os.environ.get("MCF_REPLAY_VERBOSE") != "1"
        import contextlib
        import io

        buf = io.StringIO()
        try:
            with (contextlib.redirect_stdout(buf) if quiet else contextlib.nullcontext()):
                r.run(until=None)
        finally:
            try:
                fc = fast.check(check) if (fast is not None and check) else None
            except Exception as e:                    # the fidelity check never costs the session
                fc = {"error": f"{type(e).__name__}: {e}"[:200]}
            fstats = None if fast is None else {"frame_hits": S_hits(fast), "mask_hits": fast.mask_hits,
                                                 "mask_misses": fast.mask_misses, "ctx_kept": fast.kept,
                                                 "ctx_dropped": fast.dropped}
            if fast is not None:
                fast.uninstall()
    res = collect(r, client, day)
    res["stats"] = {"day": str(day), "account": cfg.get("account_name"), "fills": fills, "limit_fill": limit_fill,
                    "exact": exact, "symbols": len(feed.bars), "priors": len(priors),
                    "setups": [s.name for s in strategies], "polls": r.health["polls"],
                    "seconds": round(_wall.time() - t_start, 1), "fast": fstats, "fast_check": fc,
                    "touches": len(client.touches), "fills_n": len(client.fill_log),
                    "log_tail": buf.getvalue().splitlines()[-5:]}
    if out_dir is not None:
        write(res, Path(out_dir))
    log(f"replay {day} {cfg.get('account_name')}: {len(res['trades'])} trades, {len(res['signals'])} signals, "
        f"{res['stats']['seconds']}s")
    return res


def S_hits(fast) -> int:
    from ..strategies import setups as S

    p = S._LAB_FRAMES
    return getattr(p, "hits", 0)


def collect(r, client: SimTradingClient, day) -> dict:
    """Journal-format rows of the replayed session plus the touch-fill counterfactual per trade."""
    j = r.journal
    sig = j.signals(r.run_id, str(day))
    tr = j.trades(run_id=r.run_id)
    wid = j.get_or_create_run("whatif", "MCF what-if (signals not taken)")
    wi = j.trades(run_id=wid)
    tr = tr.copy()
    if len(tr):
        par = {o.id: o.client_order_id for o in client.orders}
        tt = pd.DataFrame(client.touches)
        r_touch, touched = [], []
        for row in tr.itertuples():
            coid = par.get(str(row.broker_order_id))
            rt, hit = float(row.r_multiple), False
            if len(tt) and coid is not None and row.exit_reason != "target" and row.target is not None \
                    and not pd.isna(row.target):
                x = tt[tt.parent == coid]
                if len(x):
                    k = int(x.minute.min())
                    t_touch = client.mkt.bar_time(k)
                    if t_touch < pd.Timestamp(row.exit_time).tz_convert(NY).floor("1min") + pd.Timedelta(minutes=1):
                        risk = abs(float(row.entry) - float(row.stop))
                        if risk > 0:
                            rt, hit = int(row.side) * (float(row.target) - float(row.entry)) / risk, True
            r_touch.append(rt)
            touched.append(hit)
        tr["r_touch"] = r_touch
        tr["touch_only"] = touched
    return {"signals": sig, "trades": tr, "whatif": wi, "summary": summarize(sig, tr)}


def summarize(sig: pd.DataFrame, tr: pd.DataFrame) -> pd.DataFrame:
    """Per setup: signals, entries, skips (by reason), trades, win rate, avg / total R (and with touch fills)."""
    names = (set(sig.strategy) if len(sig) else set()) | (set(tr.strategy) if len(tr) else set())
    rows = []
    for n in sorted(names):
        s = sig[sig.strategy == n] if len(sig) else sig
        t = tr[tr.strategy == n] if len(tr) else tr
        r = t.r_multiple.astype(float) if len(t) else pd.Series(dtype=float)
        skips = s[s.status != "submitted"].reason.value_counts().to_dict() if len(s) else {}
        rows.append({"setup": n, "signals": len(s), "submitted": int((s.status == "submitted").sum()) if len(s) else 0,
                     "trades": len(t), "wins": int((r > 0).sum()), "total_r": float(r.sum()),
                     "avg_r": float(r.mean()) if len(r) else float("nan"),
                     "total_r_touch": float(t.r_touch.sum()) if len(t) and "r_touch" in t else float("nan"),
                     "skips": json.dumps(skips)})
    return pd.DataFrame(rows)


def write(res: dict, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for k in ("signals", "trades", "whatif", "summary"):
        res[k].to_csv(out / f"{k}.csv.gz", index=False)
    (out / "stats.json").write_text(json.dumps({**res["stats"], "_note": DISCLAIMER}, indent=1, default=str))


def account_config(account: str, day=None, as_live: bool = False, branch: str | None = None) -> dict:
    """The account's config: today's files (MCF_ACCOUNT overlay), or with as_live=True the setups frozen for `day` on
    the account's data branch (strategies / exits / shorts / live / universe as they traded that session)."""
    from ..config import load_config

    old = os.environ.get("MCF_ACCOUNT")
    os.environ["MCF_ACCOUNT"] = account
    try:
        cfg = load_config()
    finally:
        if old is None:
            os.environ.pop("MCF_ACCOUNT", None)
        else:
            os.environ["MCF_ACCOUNT"] = old
    if as_live and day is not None:
        frozen = store.frozen_setups(day, branch or data_branch(account))
        if frozen is None:
            raise FileNotFoundError(f"no frozen setups for {account} {day}")
        from ..execution.session import SETUP_KEYS

        cfg.update({k: frozen[k] for k in SETUP_KEYS if k in frozen})
        acct_then = config_at(account, day)     # the snapshot has no account limits: take them from the config then
        if acct_then is not None:
            cfg["account"] = acct_then["account"]
            cfg["costs"] = acct_then.get("costs", cfg["costs"])
            cfg["_replay_config_commit"] = acct_then["_commit"]
        missing = [n for n, v in cfg["strategies"].items() if (v or {}).get("enabled") and (v or {}).get("module")
                   and not (store.ROOT / v["module"]).exists()]
        for n in missing:                       # a module renamed / removed since: cannot be replayed
            cfg["strategies"][n]["enabled"] = False
        cfg["_replay_missing_modules"] = missing
    return cfg


def config_at(account: str, day) -> dict | None:
    """config/default.yaml + config/account_<account>.yaml as committed before that session's open (09:30 ET), merged
    as load_config does - for the sections the frozen setup snapshot does not hold (account limits, costs)."""
    import subprocess

    import yaml

    from ..config import _merge

    when = f"{pd.Timestamp(str(day)).date()} 09:30:00 -0400"
    r = subprocess.run(["git", "-C", str(store.ROOT), "rev-list", "-1", "--first-parent", f"--before={when}", "HEAD"],
                       capture_output=True, text=True)
    sha = r.stdout.strip()
    if not sha:
        return None

    def show(path):
        x = subprocess.run(["git", "-C", str(store.ROOT), "show", f"{sha}:{path}"], capture_output=True, text=True)
        return yaml.safe_load(x.stdout) if x.returncode == 0 else None

    cfg = show("config/default.yaml")
    if cfg is None:
        return None
    if account != "primary":
        cfg = _merge(cfg, show(f"config/account_{account}.yaml") or {})
    cfg["_commit"] = sha[:10]
    return cfg


def data_branch(account: str) -> str:
    return {"primary": "origin/mcf-data", "testing": "origin/mcf-data-testing", "testing2": "origin/mcf-data-testing2",
            "gen": "origin/mcf-data-gen", "graveyard": "origin/mcf-data-graveyard"}.get(account,
                                                                                      f"origin/mcf-data-{account}")


def add_setup(cfg: dict, name: str, module: str | None = None, alone: bool = False, block: dict | None = None) -> dict:
    """Ad-hoc config: one extra setup (a lab module, or any `strategies:` block), alone or alongside the account's.
    It goes last in live.setup_order (lowest priority on shared symbols), as a newly added setup would."""
    b = dict(block or {})
    if module:
        b.setdefault("type", "lab")
        b["module"] = module
        b.setdefault("min_adv", 95_000_000)
        b.setdefault("window", [950, 1500])
        b.setdefault("scale_out_r", None)
    b["enabled"] = True
    if alone:
        for k in cfg["strategies"]:
            cfg["strategies"][k] = {**(cfg["strategies"][k] or {}), "enabled": False}
    cfg["strategies"][name] = b
    order = list(cfg.get("live", {}).get("setup_order") or [])
    cfg.setdefault("live", {})["setup_order"] = [x for x in order if x != name] + [name]
    return cfg


def session_inputs(cfg: dict, day, universe: str = "lab", branch: str | None = None) -> tuple[dict, dict, dict]:
    """(bars, priors, notes) for a replayed session: the store's bars, the live prep's priors from the store, the
    universe (lab symbols, intersected with the live universe of that day when the data branch has it, minus the
    PTP denylist and the live earnings blackout when recorded)."""
    from ..backtest.engine import pinned_symbols

    day = store.check_dates([day])[0]
    syms = set(store.symbols())
    notes = {"universe": "lab"}
    live_u = store.live_universe(day, branch or "origin/mcf-data") if universe == "live" else None
    if live_u:
        notes["universe"] = f"lab ∩ live universe.csv ({len(live_u)} live symbols)"
        notes["live_not_in_lab"] = len(live_u - syms)
        syms &= live_u | pinned_symbols(cfg)
    syms -= set(cfg.get("universe", {}).get("ptp_denylist") or [])
    eb = store.earnings_blackout(day, branch or "origin/mcf-data")
    if eb is not None:
        syms -= eb
        notes["earnings_blackout"] = len(eb)
    else:
        notes["earnings_blackout"] = "not on record (not applied)"
    exact = sorted({s for st in cfg["strategies"].values() if (st or {}).get("enabled")
                    for s in (st.get("symbols") or []) if isinstance(st.get("symbols"), list)})
    bars = store.load_day(day, sorted(syms | set(exact)))
    allp = store.build_priors_for(day, store.symbols(), exact_symbols=[])
    priors = {s: p for s, p in allp.items() if s in syms}
    notes["symbols"] = len(priors)
    return bars, priors, notes
