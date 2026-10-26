"""Paper-trading loop: same strategy code as the backtester, run every minute on live SIP bars.

Flow each minute during RTH:
  1. fetch only the NEW 1-minute bars for the universe (incremental; ~5,000 symbols)
  2. build DayContexts from pre-market priors (mcf.data.priors) + today's bars
  3. run strategies; act only on signals whose bar is the latest completed bar
     (stop-entry signals are converted to a market order when the trigger trades)
  4. fill-realism checks (live spread vs stop distance, participation), risk-check, size,
     submit, journal. EVERY signal is journaled: taken, skipped (with reason), or shadow.
At flatten time: close MCF's own positions only. Then reconcile fills into the journal and
"what-if" simulate every signal that was not taken, so skipped/shadow setups are measured too.

The runner can stop and restart mid-day (two CI jobs per session): fired setups, trade counts
and open MCF positions are rebuilt from the journal and the broker on start.
"""

from __future__ import annotations

import json
import os
import re
import time as _time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from ..backtest.engine import Costs, in_play_filter, is_extended, rank_contexts, simulate, universe_ok
from ..data.bars import TZ, normalize, rth
from ..journal import Journal
from ..strategies.base import DayContext, Strategy, t
from .alpaca_broker import AlpacaBroker
from .outage import outage_cfg, protect_open_lots
from .risk import RiskManager

NY = TZ
SPLIT_TAPE_SYMBOLS = ("QQQ", "IWM")
COID_PREFIX = os.environ.get("MCF_COID_PREFIX", "mcf-")   # Testing account: "mct-" (never touches the other book)
# Entry client order ids: <prefix><setup>-<symbol>-<YYYYMMDD> (one entry per setup/symbol/day, live.same_setup_reentry
# false) or <prefix><setup>-<symbol>-<YYYYMMDD>-<HHMM> (HHMM = the signal's decision bar, so every lot of a setup on a
# symbol has its own id). A lot's own exit is <entry id>-x; a flatten close is <prefix>flatten-<symbol>-<YYYYMMDDHHMMSS>.
_COID_RE = re.compile(r"^(?P<setup>.+)-(?P<symbol>[^-]+)-(?P<day>\d{8})(?:-(?P<hhmm>\d{4}))?$")


def parse_coid(coid: str | None, prefix: str | None = None):
    """(setup, symbol, YYYYMMDD, HHMM or None) of an MCF entry id; None for a lot's own orders (exit -x, scale-out -s,
    protection -p / -p<N>, unprotected close -u), flatten closes, other ids."""
    prefix = COID_PREFIX if prefix is None else prefix
    coid = coid or ""
    if not coid.startswith(prefix) or re.search(r"-(x|s|u|p\d*)$", coid):
        return None
    m = _COID_RE.match(coid[len(prefix):])
    if m is None or m["setup"].startswith("flatten"):
        return None
    return m["setup"], m["symbol"], m["day"], m["hhmm"]


def _info(raw) -> dict:
    try:
        d = json.loads(raw or "{}")
        return d if isinstance(d, dict) else {}
    except (TypeError, ValueError):
        return {}


class PaperRunner:
    def __init__(self, cfg: dict, strategies: list[Strategy], priors: dict, dry_run: bool = False,
                 status_path: str | None = None, on_status=None, broker=None, data_client=None):
        self.cfg = cfg
        self.live = cfg.get("live", {})
        self.strategies = strategies
        self.priors = priors
        # Split-tape short gate (owner 2026-10-14, live.split_tape_short_gate; Testing 1 only): QQQ and IWM bars are
        # fetched every poll even when they are not in today's universe (they are never traded unless in priors).
        sg = self.live.get("split_tape_short_gate") or {}
        self.split_gate = bool(sg.get("enabled", False))
        self.split_spread = float(sg.get("spread_pct", 0.50))
        self.split_stale_min = int(sg.get("max_stale_min", 3))
        # Lab context (opt-in `context:` with spy_fo / qqq_fo, 2026-10-17): the index bars are polled like the split-tape
        # symbols - fetched every poll for the context columns, traded only when they are in priors.
        ctx_syms = set().union(*(getattr(s, "context_symbols", None) or set() for s in strategies))
        self.watchlist = sorted(set(priors) | (set(SPLIT_TAPE_SYMBOLS) if self.split_gate else set()) | ctx_syms)
        self._split_cache: tuple | None = None
        self.dry_run = dry_run
        self.broker = broker or AlpacaBroker(paper=True)
        self.dc = data_client
        self.journal = Journal(cfg["data"]["journal_path"])
        self.run_id = self.journal.get_or_create_run("paper", "MCF Update (live paper)")
        self.risk = RiskManager(cfg, self.broker.equity())
        self.flatten = t(cfg["session"]["flatten_by"])
        self.no_entry_before = t(self.live.get("no_entry_before", "09:30"))
        self.fired: set[tuple[str, str]] = set()
        self.seen: set[tuple[str, str]] = set()      # signals already journaled today
        # GX1 clock gate (owner 2026-10-26): symbol -> (start of its latest decided 5-minute bucket, the lab setups that
        # evaluated it), so each completed bucket is evaluated once per setup and symbol (a symbol without a new bar keeps
        # its latest bucket for several polls). After a restart the journal dedupe (seen / moments) keeps a fired bucket
        # from firing again.
        self.lab_bucket: dict[str, tuple[pd.Timestamp, set]] = {}
        self.open_strategy: dict[str, str] = {}
        # symbol -> time an entry was submitted. A market entry is not a broker position until it fills, so without
        # this a second setup firing on the same symbol in the same poll passed "already in symbol" (2026-10-08:
        # EDV x4, GDXJ x3, KMI x3, SHW x2, ARKK x2 stacked).
        self.pending: dict[str, float] = {}
        # trade-management state (time stop / breakeven / trail): keyed by symbol when max_lots_per_symbol is 1, by lot
        # (symbol, lot id) when lots stack, so a stop move or time-stop exit only ever touches that lot's own orders.
        self.managed: dict = {}
        # Live scale-out (opt-in per setup: `live_scale_out: true` plus the setup's own scale_out_r; 2026-10-16). Keyed by
        # (symbol, lot id): {side, stop, target, r, frac, t0, entry, risk, strategy, tries}. Mirrors simulate(): bank
        # scale_out_frac at +scale_out_r R from the entry fill, the rest's stop to breakeven. Setups without the flag
        # never scale out live, whatever exits.scale_out_r says (that default only applies to backtests).
        self.scaling: dict[tuple[str, str], dict] = {}
        # Per-lot stacking (owner 2026-10-13, live.max_lots_per_symbol; 1 = one position per symbol, the old behaviour).
        # symbol -> lot id (the entry's client order id) -> {strategy, side, qty, order_id, coid}: every open or pending
        # lot (one bracket). Keyed by client id, not setup: one setup can hold several lots on a symbol (re-entry).
        self.max_lots = self.risk.max_lots
        self.lots: dict[str, dict[str, dict]] = {}
        # Same-setup re-entry (owner 2026-10-14, live.same_setup_reentry): a setup may enter a symbol again the same day
        # on a NEW signal - a later decision bar than its previous entry there - never twice for the same bar.
        # false: a setup/symbol pair is handled once per day (self.seen), the pre-2026-10-14 behaviour.
        self.same_setup_reentry = self.risk.same_setup_reentry
        self.moments: set[tuple[str, str, str]] = set()   # (symbol, setup, HHMM decision bar) signals handled today
        self.last_entry: dict[tuple[str, str], str] = {}  # (symbol, setup) -> HHMM of its latest entry today
        self.entered: set[str] = set()                    # entry client ids submitted today
        self._fill_px: dict[str, float] = {}   # broker order id -> parent fill price (restart: per-lot entry price)
        # Testing-account flags (owner 2026-10-13, research/bdi/longs1013 Q3 Mf / Ma); both off in config/default.yaml.
        # retry_after_release: a market entry skipped "already in symbol" may take the setup's next FRESH signal on
        # that symbol (latest bar, later than the blocked one) once the holder's position has closed; once per
        # setup/symbol/day. longs_first_on_ties: setups firing on one symbol in the same poll are tried longs first,
        # then in setup_order.
        # Re-entry supersedes retry_after_release (every later fresh signal is evaluated anyway), so it is off with it.
        self.retry_after_release = bool(self.live.get("retry_after_release", False)) and not self.same_setup_reentry
        self.longs_first_on_ties = bool(self.live.get("longs_first_on_ties", False))
        self.blocked: dict[tuple[str, str], dict] = {}   # (symbol, setup) -> {"bar": blocked bar_index, "done": bool}
        self.bars: dict[str, pd.DataFrame] = {}
        self.last_fetch: pd.Timestamp | None = None
        self.health = {"polls": 0, "last_poll_s": None, "symbols_last_bar": 0, "last_bar": None,
                       "data_stale": None, "data_outages": [], "outage_actions": []}
        # Stale-data guard (2026-10-15: SIP bars missing for all 389 symbols 12:57-14:10 ET, symbols_last_bar 0 for
        # ~70 polls, no alert). When fewer than data_stale_fresh_frac of the symbols have a bar in the last
        # data_stale_min minutes during the session, no new entries are evaluated (signals would be computed on old
        # bars); open lots keep their broker-side brackets and trade management unchanged. One alert per outage.
        # Outage escalation (owner 2026-10-16, live.outage; docs/OPERATIONS.md "Outage plan"): entries pause at
        # enter_pause_min of stale data (= data_stale_min when that is not set), after protect_min of CONTINUOUS
        # staleness the stops of open lots in profit move to breakeven, after flatten_min (or flatten_min with the broker
        # unreachable) every MCF position is flattened. Each step once per outage, logged in health.outage_actions.
        self.outage = outage_cfg(self.live)
        self.stale_min = int(self.live.get("data_stale_min", self.outage["enter_pause_min"]))
        self.stale_fresh_frac = float(self.live.get("data_stale_fresh_frac", 0.05))
        self._esc: dict | None = None                 # current stale-data outage: {"since", "done": set of steps}
        self._down: dict | None = None                # broker unreachable: {"since", "flattened"}
        # Pre-entry cross-check (owner 2026-10-16): the signal's reference price must agree with the live quote mid
        # within quote_crosscheck_max_dev_pct, the quote must be at most quote_crosscheck_max_age_s old and the bar the
        # signal was computed on at most quote_crosscheck_max_bar_age_min old. 0 / null disables a check. The defaults
        # (2.0% / 300 s / 10 min) are above everything seen in normal operation (journal 10-06..10-16: max |ref - mid|
        # 1.73% over 3,380 submitted entries; decision bar <= 3.6 min old; SIP quote age p99.9 68 s for adv >= $95M).
        self.xc_dev = float(self.live.get("quote_crosscheck_max_dev_pct", 2.0) or 0)
        self.xc_age = float(self.live.get("quote_crosscheck_max_age_s", 300) or 0)
        self.xc_bar = float(self.live.get("quote_crosscheck_max_bar_age_min", 10) or 0)
        self._quote_ts: dict[str, pd.Timestamp] = {}
        self._now: pd.Timestamp | None = None
        self.status_path = status_path
        self.on_status = on_status
        self.today = None
        # Poll input log (owner 2026-10-21, live.log_poll_inputs, default on): what each poll actually received - per
        # symbol the latest bar time and bar count (only the exceptions are listed), poll wall time, data-stale flag -
        # so a replay can be checked against (and later driven by) the real inputs. Set by `mcf live` (state
        # polls/<date>/<HHMMSS>.jsonl.gz chunks, each written once and pushed with the status). Never raises.
        self.poll_log_dir: str | None = None
        self.poll_log_flush_min = float(self.live.get("poll_log_flush_min", 10))
        self._poll_buf: list[str] = []
        self._poll_buf_since: float | None = None
        self._poll_log_ms = 0.0

    # ---------------------------------------------------------------- state
    def restore(self, today):
        """Rebuild per-day state after a restart (second CI job, crash)."""
        self.today = today
        sig = self.journal.signals(self.run_id, str(today))
        for r in sig.itertuples():
            key = (r.symbol, r.strategy)
            self.seen.add(key)
            info = _info(getattr(r, "info", None))
            bt = None
            if self.same_setup_reentry:
                bt = info.get("bar_time")
                if not bt:
                    try:
                        bt = f"{pd.Timestamp(r.ts).tz_convert(NY):%H%M}"   # rows from before re-entry: decision time
                    except (TypeError, ValueError):
                        bt = "2359"                                      # unknown: no re-entry today (safe side)
                self.moments.add((*key, bt))
            if r.status in ("submitted", "dry_run"):
                self.fired.add(key)
                self.open_strategy[r.symbol] = r.strategy
                coid = info.get("coid") or f"{COID_PREFIX}{r.strategy}-{r.symbol}-{pd.Timestamp(str(today)):%Y%m%d}"
                self.lots.setdefault(r.symbol, {})[coid] = {
                    "strategy": r.strategy, "side": int(r.side), "qty": int(r.qty or 0), "order_id": r.broker_order_id,
                    "coid": coid}
                self.entered.add(coid)
                if bt:
                    self.last_entry[key] = max(self.last_entry.get(key, ""), bt)
        self.risk.state.trades_today = int((sig.status == "submitted").sum()) if len(sig) else 0
        if self.retry_after_release:
            self._restore_blocked(sig)
        if not self.dry_run:
            self._restore_from_broker(today)
            self._restore_lots()
            self._restore_management()
            self._restore_scaling()
        done = self.journal.trades(run_id=self.run_id)
        if len(done):
            td = done.loc[done.date == str(today)]
            self.risk.state.realized_r = float(td["r_multiple"].sum())
            # per-setup net R today (account.max_setup_daily_loss_r)
            self.risk.state.realized_r_by_strategy = (
                {str(k): float(v) for k, v in td.groupby("strategy")["r_multiple"].sum().items()}
                if "strategy" in td.columns and len(td) else {})
            # LL-LATCH after a restart: a setup that touched the limit at any point today (running net R in exit order)
            # stays stopped, even if it has since recovered
            if "strategy" in td.columns and len(td):
                order = td.sort_values("exit_time", kind="stable") if "exit_time" in td.columns else td
                low = order.groupby("strategy")["r_multiple"].cumsum().groupby(order["strategy"]).min()
                self.risk.latch_setup_losses({str(k): float(v) for k, v in low.items()})
        self._sync_open()

    def _restore_blocked(self, sig: pd.DataFrame):
        """retry_after_release state after a restart: blocked market entries, and which already used their retry."""
        for r in sig.itertuples():
            key = (r.symbol, r.strategy)
            if '"retry_after_release": true' in str(getattr(r, "info", "") or ""):
                self.blocked[key] = {"bar": int(r.bar_index), "done": True}
            elif r.status == "skipped" and r.reason in self._retry_reasons() and r.entry_type == "market":
                self.blocked.setdefault(key, {"bar": int(r.bar_index), "done": False, "side": int(r.side)})

    def _retry_reasons(self) -> tuple[str, ...]:
        """Blocks that retry_after_release may lift: the symbol held (one lot per symbol), or with stacked lots only an
        opposite-side holder or the lot cap."""
        return ("already in symbol", "twin held") if self.max_lots <= 1 else ("opposite side held", "lot cap", "twin held")

    def _retry_ready(self, key: tuple[str, str]) -> bool:
        """A blocked setup may look for one fresh signal once the symbol is no longer held (nor pending) by MCF."""
        b = self.blocked.get(key) if self.retry_after_release else None
        if not b or b["done"]:
            return False
        if key[0] not in self.risk.state.open_symbols and key[0] not in self.pending:
            return True
        if self.max_lots <= 1:
            return False
        lots = self.lots.get(key[0]) or {}     # stacked lots: room under the cap and every holder on the blocked side
        return bool(lots) and len(lots) < self.max_lots and b.get("side") is not None and \
            all(lot["side"] == b["side"] for lot in lots.values())

    def _restore_from_broker(self, today):
        """The broker is the source of truth for what MCF holds: the journal on the state branch can lag a
        crashed or cancelled job by a few minutes. Every MCF entry id is mcf-<strategy>-<symbol>-<YYYYMMDD>[-<HHMM>]."""
        after = pd.Timestamp(f"{today} 00:00", tz=NY).to_pydatetime()
        try:
            orders = self.broker.orders_today_with_prefix(COID_PREFIX, after)
        except Exception as e:
            print(f"broker restore skipped: {e}")
            return
        known = set(self.journal.open_orders(self.run_id).broker_order_id) | set(
            self.journal.signals(self.run_id, str(today)).broker_order_id.dropna())
        added = 0
        for o in orders:
            if o.filled_avg_price:
                self._fill_px[str(o.id)] = float(o.filled_avg_price)
            parsed = parse_coid(o.client_order_id)   # None: a lot's own exit (-x) or a flatten close, not an entry
            if parsed is None:
                continue
            strategy, symbol, _, hhmm = parsed
            if symbol != getattr(o, "symbol", symbol):
                continue
            coid = o.client_order_id
            self.seen.add((symbol, strategy))
            self.fired.add((symbol, strategy))
            self.open_strategy.setdefault(symbol, strategy)
            self.entered.add(coid)
            if hhmm and self.same_setup_reentry:
                self.moments.add((symbol, strategy, hhmm))
                self.last_entry[(symbol, strategy)] = max(self.last_entry.get((symbol, strategy), ""), hhmm)
            side = 1 if str(getattr(o.side, "value", o.side)).lower() == "buy" else -1
            lots = self.lots.setdefault(symbol, {})
            for k in [k for k, lot in lots.items() if k != coid and str(lot.get("order_id")) == str(o.id)]:
                lots[coid] = lots.pop(k)                 # the journal's lot for this order: key it by the broker's id
            lots.setdefault(coid, {}).update(strategy=strategy, side=side, order_id=str(o.id), coid=coid,
                                             qty=int(float(getattr(o, "filled_qty", None) or o.qty or 0)))
            if str(o.id) in known:
                continue
            stop = next((float(l.stop_price) for l in (o.legs or []) if getattr(l, "stop_price", None)), float("nan"))
            tgt = next((float(l.limit_price) for l in (o.legs or []) if getattr(l, "limit_price", None)), None)
            ref = float(o.filled_avg_price) if o.filled_avg_price else float("nan")
            self.journal.record_order(self.run_id, symbol, strategy, side, int(float(o.qty or 0)), ref, stop, tgt,
                                      str(o.id), "submitted", '{"restored_from_broker": true}')
            added += 1
        if added:
            print(f"restored {added} MCF orders from the broker that the journal had not saved yet")

    def _restore_lots(self):
        """Open lots after a restart = today's entries whose journal order is not closed yet (reconcile closes a lot's
        order when its exit is paired; a symbol no longer held drops all its lots in _sync_open)."""
        try:
            orders = self.journal.open_orders(self.run_id)
        except Exception as e:
            print(f"lot restore skipped: {e}")
            return
        open_ids = set(orders.broker_order_id.astype(str))
        for sym in list(self.lots):
            for lot_id, lot in list(self.lots[sym].items()):
                if lot.get("order_id") is None or str(lot["order_id"]) not in open_ids:
                    self.lots[sym].pop(lot_id)
            if not self.lots[sym]:
                self.lots.pop(sym)

    def _restore_management(self):
        """Re-arm time stops / breakeven / trailing for MCF positions still open after a restart."""
        by_name = {s.name: s for s in self.strategies}
        keys = ("be_at_r", "trail_r", "trail_after_r", "time_stop_min", "time_stop_min_r")
        try:
            held = self.broker.positions()
            orders = self.journal.open_orders(self.run_id)
        except Exception as e:
            print(f"management restore skipped: {e}")
            return
        if self.max_lots > 1:
            return self._restore_lot_management(by_name, keys, held, orders)
        for sym, strat in self.open_strategy.items():
            st = by_name.get(strat)
            if sym not in held or st is None or not any(st.params.get(k) is not None for k in keys[:2] + keys[3:4]):
                continue
            rec = orders[orders.symbol == sym].tail(1)
            if rec.empty:
                continue
            rec = rec.iloc[0]
            entry = float(getattr(held[sym], "avg_entry_price", rec.entry_ref) or rec.entry_ref)
            self.managed[sym] = {"side": int(rec.side), "entry": entry, "risk": abs(entry - float(rec.stop)),
                                 "stop": float(rec.stop), "t0": pd.Timestamp(rec.created_at).tz_convert(NY), "best": 0.0,
                                 **{k: st.params.get(k) for k in keys}}
            self.managed[sym]["trail_after_r"] = self.managed[sym]["trail_after_r"] or 1.0
            self.managed[sym]["time_stop_min_r"] = self.managed[sym]["time_stop_min_r"] or 0.0
        if self.managed:
            print(f"re-armed trade management for {len(self.managed)} open positions")

    def _restore_lot_management(self, by_name, keys, held, orders):
        """Stacked lots: one management state per lot, entry = that lot's own parent fill (the broker position's
        average price blends every lot on the symbol)."""
        oids = orders.broker_order_id.astype(str)
        for sym, lots in self.lots.items():
            if sym not in held:
                continue
            for lot_id, lot in lots.items():
                strat = lot.get("strategy")
                st = by_name.get(strat)
                if st is None or not any(st.params.get(k) is not None for k in keys[:2] + keys[3:4]):
                    continue
                rec = orders[oids == str(lot.get("order_id"))].tail(1)   # this lot's own order, not its setup's last
                if rec.empty:
                    continue
                rec = rec.iloc[0]
                entry = self._fill_px.get(str(rec.broker_order_id)) or float(rec.entry_ref)
                m = {"side": int(rec.side), "entry": entry, "risk": abs(entry - float(rec.stop)), "stop": float(rec.stop),
                     "t0": pd.Timestamp(rec.created_at).tz_convert(NY), "best": 0.0, "coid": lot.get("coid") or lot_id,
                     "strategy": strat, **{k: st.params.get(k) for k in keys}}
                m["trail_after_r"] = m["trail_after_r"] or 1.0
                m["time_stop_min_r"] = m["time_stop_min_r"] or 0.0
                self.managed[(sym, lot_id)] = m
        if self.managed:
            print(f"re-armed trade management for {len(self.managed)} open lots")

    def _mcf_symbols(self) -> set[str]:
        return set(self.open_strategy)

    PENDING_GRACE_S = 300

    def _sync_open(self):
        held = set(self.broker.positions()) if not self.dry_run else self._mcf_symbols()
        now = _time.time()
        self.pending = {s: t0 for s, t0 in self.pending.items() if s not in held and now - t0 < self.PENDING_GRACE_S}
        self.risk.state.open_symbols = (held | set(self.pending)) & self._mcf_symbols()
        for sym in [s for s in self.lots if s not in self.risk.state.open_symbols]:
            self.lots.pop(sym)                        # flat and nothing pending: every lot on it is closed
        counts: dict[str, int] = {}
        if self.max_lots <= 1:
            for sym in self.risk.state.open_symbols:
                st = self.open_strategy.get(sym)
                counts[st] = counts.get(st, 0) + 1
            # holders only (twin check, live.block_twin_same_symbol); the lot cap / opposite side do not apply here
            self.risk.state.lots = {sym: ([(lot.get("strategy", lid), lot["side"])
                                           for lid, lot in self.lots.get(sym, {}).items()]
                                          or ([(self.open_strategy[sym], 0)] if sym in self.open_strategy else []))
                                    for sym in self.risk.state.open_symbols}
        else:                                         # slots and per-setup caps count lots
            self.risk.state.lots = {sym: [(lot.get("strategy", lid), lot["side"])
                                          for lid, lot in self.lots.get(sym, {}).items()]
                                    for sym in self.risk.state.open_symbols}
            # live.lot_cap_ignore_residual_frac (owner 2026-10-16, option B): a lot left with < frac of its original
            # quantity after a partial target fill no longer counts toward max_lots_per_symbol (it still holds shares,
            # so it still counts for the opposite-side check, slots and per-setup caps).
            frac = self.risk.residual_frac
            self.risk.state.residual = {
                sym: n for sym in self.risk.state.open_symbols
                if (n := sum(1 for lot in self.lots.get(sym, {}).values() if frac > 0 and lot.get("left") is not None
                             and lot.get("orig_qty") and 0 < lot["left"] < frac * lot["orig_qty"]))}
            for sym, lots in self.risk.state.lots.items():
                for st in [x for x, _ in lots] or [self.open_strategy.get(sym)]:
                    counts[st] = counts.get(st, 0) + 1
        self.risk.state.open_by_strategy = counts

    # ---------------------------------------------------------------- data
    def _client(self):
        if self.dc is None:
            from alpaca.data.historical import StockHistoricalDataClient

            self.dc = StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
        return self.dc

    def fetch(self, now: pd.Timestamp):
        """Fetch bars since the last poll (re-reading 2 minutes so late prints update the last bars)."""
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        t0 = _time.time()
        start = pd.Timestamp(f"{now.date()} 09:30", tz=NY)
        if self.last_fetch is not None:
            start = max(start, self.last_fetch - pd.Timedelta(minutes=2))
        batch = int(self.live.get("fetch_batch", 400))

        def one(i):
            req = StockBarsRequest(symbol_or_symbols=self.watchlist[i:i + batch], timeframe=TimeFrame.Minute,
                                   start=start.to_pydatetime(), end=now.to_pydatetime(),
                                   feed=DataFeed(self.cfg["data"]["feed"]))
            try:
                return self._client().get_stock_bars(req).df
            except Exception as e:  # one failed batch must not stop the session
                print(f"fetch error batch {i}: {e}")
                return pd.DataFrame()

        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=8) as ex:
            frames = list(ex.map(one, range(0, len(self.watchlist), batch)))
        for df in frames:
            if df.empty:
                continue
            for sym, g in df.groupby(level=0):
                g = rth(normalize(g.droplevel(0)))
                if g.empty:
                    continue
                old = self.bars.get(sym)
                self.bars[sym] = g if old is None else pd.concat([old[old.index < g.index[0]], g])
        cut = now.floor("1min")
        last_min = cut - pd.Timedelta(minutes=1)
        self.health.update(polls=self.health["polls"] + 1, last_poll_s=round(_time.time() - t0, 1),
                           symbols_last_bar=sum(1 for b in self.bars.values() if len(b) and b.index[-1] >= last_min),
                           last_bar=str(last_min.time())[:5])
        self.last_fetch = cut
        # drop the still-forming bar
        return {s: b[b.index < cut] for s, b in self.bars.items()}

    def _contexts(self, today_bars: dict[str, pd.DataFrame], today) -> list[DayContext]:
        ctxs = []
        for sym, bars in today_bars.items():
            p = self.priors.get(sym)
            if p is None or bars.empty:
                continue
            ctx = DayContext(symbol=sym, date=today, bars=bars, prev_close=p.prev_close, prev_high=p.prev_high,
                             prev_low=p.prev_low, atr=p.atr, avg_dollar_volume=p.adv,
                             avg_cum_volume=p.avg_cum, avg_move=p.avg_move, prior5=getattr(p, "tail5", None),
                             sma20=getattr(p, "sma20", float("nan")), peers=today_bars)
            if universe_ok(ctx, self.cfg):
                ctxs.append(ctx)
        orv = [c.rvol().iloc[min(4, len(c.bars) - 1)] for c in ctxs]
        ctxs, orv = in_play_filter(ctxs, orv, self.cfg)
        rank_contexts(ctxs)
        return ctxs

    # ---------------------------------------------------------------- trading
    def manage(self, now: pd.Timestamp, bars: dict):
        """Per-minute trade management mirroring simulate(): time stop, breakeven move, trailing stop.
        Uses completed 1-minute bars since entry; stop changes go to the broker-side stop order."""
        if not self.managed or self.dry_run:
            return
        held = set(self.broker.positions())
        for key, m in list(self.managed.items()):
            lot = isinstance(key, tuple)              # (symbol, lot id) when lots stack
            sym = key[0] if lot else key
            if sym not in held or (lot and key[1] not in self.lots.get(sym, {})):
                self.managed.pop(key)
                continue
            b = bars.get(sym)
            if b is None or b.empty or m["risk"] <= 0:
                continue
            since = b[b.index >= m["t0"].floor("1min")]
            if since.empty:
                continue
            fav = since["high"].max() if m["side"] == 1 else since["low"].min()
            m["best"] = max(m["best"], m["side"] * (fav - m["entry"]) / m["risk"])
            mins = (now - m["t0"]).total_seconds() / 60
            if m["time_stop_min"] and mins >= m["time_stop_min"] and m["best"] < m["time_stop_min_r"]:
                if lot:
                    self._lot_time_stop(key, m, mins)
                    continue
                try:
                    if not self.broker.close_mcf_position(sym, COID_PREFIX):
                        raise RuntimeError("close not confirmed")
                    print(f"TIME STOP {sym}: {mins:.0f} min, best {m['best']:.2f}R")
                except Exception as e:
                    print(f"time stop {sym} failed: {e}")
                self.managed.pop(sym)
                continue
            new = m["stop"]
            if m["be_at_r"] is not None and m["best"] >= m["be_at_r"]:
                new = max(new, m["entry"]) if m["side"] == 1 else min(new, m["entry"])
            if m["trail_r"] is not None and m["best"] >= m["trail_after_r"]:
                tr = m["entry"] + m["side"] * (m["best"] - m["trail_r"]) * m["risk"]
                new = max(new, tr) if m["side"] == 1 else min(new, tr)
            if m["side"] * (new - m["stop"]) > 0.005:
                try:
                    if lot:
                        self.broker.move_lot_stop(sym, m["coid"], round(new, 2), COID_PREFIX)
                    else:
                        self.broker.move_stop(sym, round(new, 2), COID_PREFIX)
                    print(f"STOP {sym} {m['stop']:.2f} -> {new:.2f} (best {m['best']:.2f}R)")
                    m["stop"] = new
                except Exception as e:
                    print(f"move stop {sym} failed: {e}")

    # ---------------------------------------------------------------- live scale-out (opt-in per setup)
    def _strategy(self, name):
        return next((s for s in self.strategies if getattr(s, "name", None) == name), None)

    def _live_scale_out(self, sig) -> bool:
        st = self._strategy(sig.strategy)
        return bool((getattr(st, "params", None) or {}).get("live_scale_out")) and bool(sig.scale_out_r)

    @staticmethod
    def _scale_state(side, stop, target, r, frac, t0, strategy) -> dict:
        return {"side": int(side), "stop": float(stop), "target": None if target is None else float(target),
                "r": float(r), "frac": float(frac or 0.5), "t0": t0, "entry": None, "risk": None,
                "strategy": strategy, "tries": 0}

    SCALE_TRIES = 5

    def scale_outs(self, now: pd.Timestamp, bars: dict):
        """Live scale-out, bar for bar as simulate() does it. Over the completed 1-minute bars since the entry (same
        window as manage()), in order: a bar that touches the lot's stop or its target ends it (the stop/target wins a
        bar that also touches the scale level - the broker leg closes the whole lot); the first bar whose high (long) /
        low (short) reaches entry + side x scale_out_r x R (entry = the lot's own fill, R = |entry - stop|) triggers:
        the broker cancels the lot's legs, sells the banked shares (floor(qty x scale_out_frac); a lot under 2 shares is
        never scaled) and protects the rest with its own OCO / stop at breakeven (AlpacaBroker.scale_out_lot). Stop
        moves of manage() apply as usual (to the protective stop once scaled)."""
        if not self.scaling or self.dry_run:
            return
        for key, s in list(self.scaling.items()):
            sym, coid = key
            if coid not in self.lots.get(sym, {}):
                self.scaling.pop(key)                     # released (closed) lot
                continue
            try:
                if s["entry"] is None:
                    px = self._fill_px.get(str(self.lots[sym][coid].get("order_id")))
                    if px is None:
                        f = self.broker.lot_fill(sym, coid, COID_PREFIX)
                        if f is None:
                            continue                      # entry not filled yet
                        px = f[1]
                    s["entry"] = float(px)
                    s["risk"] = s["side"] * (s["entry"] - s["stop"])
                    if s["risk"] <= 0:
                        print(f"scale-out {sym}/{s['strategy']}: no risk (entry {s['entry']} stop {s['stop']}); off")
                        self.scaling.pop(key)
                        continue
            except Exception as e:
                print(f"scale-out {sym}/{s['strategy']}: fill lookup failed: {e}")
                continue
            b = bars.get(sym)
            if b is None or b.empty:
                continue
            since = b[b.index >= s["t0"].floor("1min")]
            m = self.managed.get(key) or (self.managed.get(sym) if self.max_lots <= 1 else None)
            stop = float(m["stop"]) if m else s["stop"]
            verdict = self._scale_verdict(since, s, stop)
            if verdict is None:
                continue
            if verdict != "scale":
                self.scaling.pop(key)                     # the stop or target took the bar first: no scale-out
                continue
            if not s.get("started") and not self._scale_cap_ok(now):
                self.scaling.pop(key)                     # the lot keeps its bracket unchanged
                print(f"scale-out {sym}/{s['strategy']}: daily cap live.scale_out_max_per_day reached; lot unchanged")
                continue
            s["started"] = True
            self._do_scale(key, s, m)

    def _scale_cap_ok(self, now: pd.Timestamp) -> bool:
        """live.scale_out_max_per_day (owner SO1 2026-10-19: try the new cancel/bank/protect method on a few paper lots
        first): counts today's banked (-s) orders at the broker, so the cap survives job restarts. None = no cap."""
        cap = self.live.get("scale_out_max_per_day")
        if cap is None:
            return True
        try:
            day0 = now.tz_convert("America/New_York").normalize().to_pydatetime()
            n = sum(1 for o in self.broker.orders_today_with_prefix(COID_PREFIX, day0)
                    if (o.client_order_id or "").endswith("-s"))
        except Exception as e:
            print(f"scale-out cap check failed ({e}); not scaling")
            return False
        return n < int(cap)

    @staticmethod
    def _scale_verdict(since: pd.DataFrame, s: dict, stop: float) -> str | None:
        side = s["side"]
        level = s["entry"] + side * s["r"] * s["risk"]
        for hi, lo in zip(since["high"].to_numpy(), since["low"].to_numpy()):
            if (lo <= stop) if side == 1 else (hi >= stop):
                return "stop"
            if s["target"] is not None and ((hi >= s["target"]) if side == 1 else (lo <= s["target"])):
                return "target"
            if side * ((hi if side == 1 else lo) - level) >= 0:
                return "scale"
        return None

    def _do_scale(self, key, s, m):
        sym, coid = key
        try:
            res = self.broker.scale_out_lot(sym, coid, s["frac"], COID_PREFIX)
        except Exception as e:
            res = {"status": "error", "error": str(e)[:200]}
        st = res.get("status")
        if st in ("scaled", "already"):
            self.scaling.pop(key, None)
            be = float(res.get("stop") or round(s["entry"], 2))
            if m is not None:                             # trade management never moves the stop back below breakeven
                m["stop"] = max(m["stop"], be) if s["side"] == 1 else min(m["stop"], be)
            lot = self.lots.get(sym, {}).get(coid)
            if lot is not None and st == "scaled":
                lot["scaled"] = res.get("qty")
            if st == "scaled":
                self.health.setdefault("scale_outs", []).append(
                    {"symbol": sym, "strategy": s["strategy"], "coid": coid, "qty": res.get("qty"),
                     "left": res.get("left"), "stop": be, "at": str(self._now)})
                print(f"SCALE-OUT {sym}/{s['strategy']}: banked {res.get('qty')} at +{s['r']:g}R, "
                      f"{res.get('left')} left, stop -> {be:.2f}")
            return
        if st == "closed_unprotected":                   # protection refused: the rest was closed at market
            self.scaling.pop(key, None)
            msg = (f"{sym} {s['strategy']} lot {coid}: scale-out banked {res.get('qty')}, but the broker refused the "
                   f"breakeven protection for the remaining {res.get('left')}; they were closed at market.")
            print(f"SCALE-OUT UNPROTECTED: {msg}")
            self.health.setdefault("scale_out_failed", []).append(msg)
            return
        if st in ("closed", "skip"):
            self.scaling.pop(key, None)
            print(f"scale-out {sym}/{s['strategy']}: {st} {res.get('qty', '')}".rstrip())
            return
        if st == "pending":
            return
        s["tries"] += 1
        print(f"scale-out {sym}/{s['strategy']} {st} (try {s['tries']}/{self.SCALE_TRIES}): {res.get('error', '')}")
        if s["tries"] >= self.SCALE_TRIES:
            self.scaling.pop(key, None)                   # the lot keeps its bracket (or its re-placed protection)
            msg = (f"{sym} {s['strategy']} lot {coid}: scale-out not completed after {s['tries']} tries ({st}). "
                   "The lot keeps its broker-side stop; the 15:55 flatten closes whatever it still holds.")
            print(f"SCALE-OUT FAILED: {msg}")             # no email (owner 2026-10-16: no mid-session alerts)
            self.health.setdefault("scale_out_failed", []).append(msg)

    def _restore_scaling(self):
        """Re-arm live scale-out for open lots of flagged setups after a restart (a lot already scaled is found by its
        -s order at the broker and dropped; one banked but not yet protected gets its -p protection then)."""
        try:
            orders = self.journal.open_orders(self.run_id)
        except Exception as e:
            print(f"scale-out restore skipped: {e}")
            return
        oids = orders.broker_order_id.astype(str)
        for sym, lots in self.lots.items():
            for lot_id, lot in lots.items():
                st = self._strategy(lot.get("strategy"))
                params = getattr(st, "params", None) or {}
                if not params.get("live_scale_out") or not params.get("scale_out_r"):
                    continue
                rec = orders[oids == str(lot.get("order_id"))].tail(1)
                if rec.empty:
                    continue
                rec = rec.iloc[0]
                tgt = None if rec.target is None or pd.isna(rec.target) else float(rec.target)
                self.scaling[(sym, lot.get("coid") or lot_id)] = self._scale_state(
                    int(rec.side), float(rec.stop), tgt, params["scale_out_r"], params.get("scale_out_frac", 0.5),
                    pd.Timestamp(rec.created_at).tz_convert(NY), lot.get("strategy"))
        if self.scaling:
            print(f"re-armed live scale-out for {len(self.scaling)} open lots")

    def _lot_time_stop(self, key, m, mins):
        """Time stop for ONE lot: cancel its own legs and close exactly its quantity; other lots keep theirs."""
        sym, lot_id = key
        strat = m.get("strategy", lot_id)
        try:
            ok = self.broker.close_mcf_lot(sym, m["coid"], COID_PREFIX)
        except Exception as e:
            print(f"time stop {sym}/{strat} failed: {e}")
            ok = False
        if not ok:
            print(f"time stop {sym}/{strat} not confirmed; retrying next poll")
            return
        print(f"TIME STOP {sym}/{strat}: {mins:.0f} min, best {m['best']:.2f}R")
        self.managed.pop(key, None)
        self.lots.get(sym, {}).pop(lot_id, None)

    def _check_data(self, now: pd.Timestamp, bars: dict) -> bool:
        """True while the market data is stale: during the session (from data_stale_min after the open), fewer than
        data_stale_fresh_frac of the symbols have a completed bar in the last data_stale_min minutes. Sets
        health.data_stale, logs a warning, and alerts once per outage; on recovery the outage goes to
        health.data_outages."""
        n = max(len(self.watchlist), len(bars))
        start = pd.Timestamp(f"{now.date()} 09:30", tz=NY) + pd.Timedelta(minutes=self.stale_min)
        if n == 0 or now < start:
            return False
        cut = now.floor("1min") - pd.Timedelta(minutes=self.stale_min)
        last = [b.index[-1] for b in bars.values() if b is not None and len(b)]
        fresh = sum(1 for x in last if x >= cut)
        newest = max(last) if last else None
        cur = self.health.get("data_stale")
        if fresh >= max(1.0, self.stale_fresh_frac * n):
            if cur:
                mins = round((now - pd.Timestamp(cur["since"])).total_seconds() / 60, 1)
                self.health["data_outages"] = [*self.health.get("data_outages", []),
                                               {**cur, "until": str(now), "minutes": mins}]
                self.health["data_stale"] = None
                print(f"DATA RESUMED: {fresh} of {n} symbols fresh again after {mins} min (stale since {cur['since']})")
            return False
        if cur:
            cur.update(fresh=fresh, polls=cur.get("polls", 0) + 1,
                       stale_min=round((now - pd.Timestamp(cur["last_bar"])).total_seconds() / 60, 1)
                       if cur.get("last_bar") else None)
        else:
            cur = {"since": str(now), "last_bar": str(newest) if newest is not None else None, "fresh": fresh,
                   "of": n, "polls": 1, "threshold_min": self.stale_min,
                   "stale_min": round((now - newest).total_seconds() / 60, 1) if newest is not None else None}
            self.health["data_stale"] = cur
            msg = (f"DATA STALE: {fresh} of {n} symbols have a bar in the last {self.stale_min} min "
                   f"(newest bar {cur['last_bar'] or 'none'}, now {now:%H:%M:%S} ET). New entries paused; "
                   "open lots keep their broker-side stops and targets.")
            print(msg)   # no email alert (owner 2026-10-16); health.data_stale + dashboard only
        return True

    # ---------------------------------------------------------------- outage escalation (live.outage)
    def _outage_action(self, now, action: str, minutes: float, **detail):
        rec = {"at": str(now), "action": action, "minutes": round(float(minutes), 1), **detail}
        self.health["outage_actions"] = [*self.health.get("outage_actions", []), rec]
        print(f"OUTAGE {action.upper()} after {rec['minutes']} min: {detail}")   # log only; no email (owner 2026-10-16)

    def _escalate(self, now: pd.Timestamp, stale: bool):
        """Stale data: pause (already in effect) -> protect (breakeven for lots in profit) after protect_min of
        continuous staleness -> flatten every MCF position after flatten_min. Nothing happens while data is fresh."""
        if not stale:
            self._esc = None
            return
        if not self.outage["enabled"]:
            return
        since = (self.health.get("data_stale") or {}).get("since") or str(now)
        if self._esc is None or self._esc["since"] != since:
            self._esc = {"since": since, "done": set()}
        done = self._esc["done"]
        mins = (now - pd.Timestamp(since)).total_seconds() / 60
        if "pause" not in done:
            done.add("pause")
            self._outage_action(now, "pause", mins, reason="data stale", since=since)
        if mins >= self.outage["protect_min"] and "protect" not in done:
            done.add("protect")
            self._protect(now, mins, "data stale")
        if mins >= self.outage["flatten_min"] and "flatten" not in done:
            done.add("flatten")
            self._outage_flatten(now, mins, "data stale")

    def _protect(self, now, mins, reason):
        if self.dry_run:
            return self._outage_action(now, "protect", mins, reason=reason, dry_run=True)
        try:
            res = protect_open_lots(self.broker, COID_PREFIX)
        except Exception as e:
            return self._outage_action(now, "protect", mins, reason=reason, error=str(e)[:200])
        for mv in res["moved"]:                       # trade management must never move a protected stop back
            for key, m in self.managed.items():
                if (m.get("coid") or (key if isinstance(key, str) else None)) in (mv["coid"], mv["symbol"]):
                    s = m["side"]
                    m["stop"] = mv["new_stop"] if s * (mv["new_stop"] - m["stop"]) > 0 else m["stop"]
        self._outage_action(now, "protect", mins, reason=reason,
                            moved=[f"{x['symbol']} {x['coid']} -> {x['new_stop']}" for x in res["moved"]],
                            not_in_profit=len([x for x in res["skipped"] if x["why"] == "not in profit"]),
                            errors=[f"{x['coid']}: {x['error']}" for x in res["errors"]])

    def _outage_flatten(self, now, mins, reason, log_failure: bool = True) -> bool:
        try:
            self.flatten_mcf()
            ok = not self.health.get("flatten_failed")
            self._outage_action(now, "flatten", mins, reason=reason, left=self.health.get("flatten_failed") or [],
                                **({"dry_run": True} if self.dry_run else {}))
            return ok
        except Exception as e:
            if log_failure:
                self._outage_action(now, "flatten_failed", mins, reason=reason, error=str(e)[:200])
            else:
                print(f"outage flatten retry failed: {e}")
            return False

    def _broker_unreachable(self, now: pd.Timestamp, err: Exception):
        """The broker clock call failed (start of a poll). After flatten_min of continuous failures every MCF position is
        flattened (retried every poll until it goes through)."""
        if self._down is None:
            self._down = {"since": now, "flattened": False, "tries": 0}
            self._outage_action(now, "broker_unreachable", 0, error=str(err)[:200])
        mins = (now - self._down["since"]).total_seconds() / 60
        if self.outage["enabled"] and mins >= self.outage["flatten_min"] and not self._down["flattened"]:
            self._down["tries"] += 1                  # retried every poll; a failure is logged in health once
            self._down["flattened"] = self._outage_flatten(now, mins, "broker unreachable",
                                                           log_failure=self._down["tries"] == 1)

    def _broker_reachable(self, now: pd.Timestamp):
        """The broker answers again. If a flatten was due (flatten_min reached) but could not go through, finish it now."""
        if self._down is not None:
            mins = (now - self._down["since"]).total_seconds() / 60
            self._outage_action(now, "broker_restored", mins)
            if self.outage["enabled"] and mins >= self.outage["flatten_min"] and not self._down["flattened"]:
                self._outage_flatten(now, mins, "broker was unreachable")
            self._down = None

    def _alert(self, subject: str, text: str):
        """Best-effort email alert (same SMTP secrets as the brief / EOD email); never raises, never in a dry run."""
        if self.dry_run or not (os.environ.get("MCF_SMTP_USER") and os.environ.get("MCF_SMTP_PASSWORD")):
            return
        to = os.environ.get("MCF_EMAIL_TO") or (self.cfg.get("report") or {}).get("email_to")
        if not to:
            return
        try:
            from ..report.brief import DISCLAIMER, send_email

            send_email(subject, f"{text}\n\n{DISCLAIMER}", None, to)
        except Exception as e:
            print(f"alert email failed: {type(e).__name__}")

    def step(self, now: pd.Timestamp):
        today = now.date()
        self._now = now
        bars = self.fetch(now)
        self.manage(now, bars)
        self.scale_outs(now, bars)
        stale = self._check_data(now, bars)
        if self.poll_log_dir:
            self._log_poll(now, bars, stale)
        self._escalate(now, stale)
        if stale:
            return                                    # stale data: no new entries (signals would use old bars)
        self.ctxs = {c.symbol: c for c in self._contexts(bars, today)}
        for ctx in self.ctxs.values():
            last = len(ctx.bars) - 1
            px = float(ctx.bars["close"].iloc[-1])
            ties = []   # longs_first_on_ties: (signal, key) entered after every setup on this symbol was scanned
            for strat in self.strategies:
                if getattr(strat, "ticker_split", None) and not strat.trades_symbol(ctx.symbol):
                    continue   # split copy (ticker_split): the other testing account trades this half; never journaled
                key = (ctx.symbol, strat.name)
                retry = False
                if key in self.seen and not self.same_setup_reentry:   # re-entry: deduped per signal bar below
                    if not self._retry_ready(key):
                        continue
                    retry = True
                if not strat.eligible(ctx):
                    continue
                if self._bucket_done(strat, key, ctx):
                    continue   # lab setup: this 5-minute bucket was already evaluated for this symbol
                for sig in strat.signals(ctx):
                    if retry:
                        # only a fresh market signal on the latest bar, later than the blocked one; never a stale price
                        if sig.entry_type != "market" or sig.bar_index != last or sig.bar_index <= self.blocked[key]["bar"]:
                            continue
                        self.blocked[key]["done"] = True
                        sig.meta = {**sig.meta, "retry_after_release": True}
                        if self.longs_first_on_ties:
                            ties.append((sig, key))
                        else:
                            self._enter(sig, px, key, ctx, now)
                        break
                    if sig.entry_type == "market" and sig.bar_index != last:
                        continue
                    if self.same_setup_reentry and self._handled(key, sig, ctx, now):
                        continue   # this bar already handled, or not later than the setup's last entry here
                    if sig.entry_type == "stop":
                        if sig.bar_index >= last or last - sig.bar_index > sig.entry_valid_bars:
                            continue  # same validity window as the backtester's simulate()
                        seg = ctx.bars.iloc[sig.bar_index + 1:]
                        crossed = (seg["high"] >= sig.entry_price) if sig.side == 1 else (seg["low"] <= sig.entry_price)
                        if not crossed.any():
                            continue
                        first = int(np.argmax(crossed.to_numpy()))
                        if first < len(seg) - 1:
                            # the trigger traded on an earlier bar (e.g. while no job was running):
                            # a late entry would not be the setup the backtest measures
                            self._mark(key, sig, ctx, now)
                            self._log(sig, "skipped", f"missed: triggered at {seg.index[first]:%H:%M}", px, now)
                            continue
                    self._mark(key, sig, ctx, now)
                    if self.longs_first_on_ties:
                        ties.append((sig, key))
                        continue
                    self._enter(sig, px, key, ctx, now)
            # stable sort: longs before shorts, setup_order (scan order) kept within each side
            for sig, key in sorted(ties, key=lambda x: x[0].side != 1):
                self._enter(sig, px, key, ctx, now)

    def _bucket_done(self, strat, key, ctx) -> bool:
        """GX1: True when this lab setup already evaluated the bucket the latest bar decides on this symbol; otherwise
        records it as evaluated now. Setups without decision_bucket (non-lab) are never held back."""
        db = getattr(strat, "decision_bucket", None)
        if db is None:
            return False
        b = db(ctx)
        if b is None:
            return False
        cur = self.lab_bucket.get(key[0])
        if cur is None or cur[0] != b:
            cur = self.lab_bucket[key[0]] = (b, set())
        if key[1] in cur[1]:
            return True
        cur[1].add(key[1])
        return False

    # ---------------------------------------------------------------- re-entry (live.same_setup_reentry)
    def _moment(self, sig, ctx, now) -> str:
        """HHMM (ET) of the signal's decision bar: the 'moment' a setup may use a symbol only once."""
        m = sig.meta.get("bar_time")
        if m:
            return m
        idx = getattr(getattr(ctx, "bars", None), "index", None)
        ts = idx[sig.bar_index] if isinstance(idx, pd.DatetimeIndex) and 0 <= sig.bar_index < len(idx) else now
        ts = pd.Timestamp(ts)
        m = f"{ts.tz_convert(NY) if ts.tzinfo else ts:%H%M}"
        sig.meta = {**sig.meta, "bar_time": m}           # journaled with the signal (restart dedupe)
        return m

    def _handled(self, key, sig, ctx, now) -> bool:
        """Re-entry: True for a signal bar this setup already handled on the symbol, or one not later than its last
        entry there (a re-entry needs a new signal, also for stop-entry setups)."""
        m = self._moment(sig, ctx, now)
        return (*key, m) in self.moments or (key in self.last_entry and m <= self.last_entry[key])

    def _mark(self, key, sig, ctx, now):
        self.seen.add(key)
        if self.same_setup_reentry:
            self.moments.add((*key, self._moment(sig, ctx, now)))

    def _coid(self, sig, ctx, now) -> str:
        base = f"{COID_PREFIX}{sig.strategy}-{sig.symbol}-{now:%Y%m%d}"
        return f"{base}-{self._moment(sig, ctx, now)}" if self.same_setup_reentry else base

    # ---------------------------------------------------------------- split-tape short gate
    def _split_tape(self, now) -> dict | None:
        """QQQ and IWM return from today's open (%) on their latest completed 1-minute bars, and the spread QQQ - IWM.
        None when either is missing or stale (> max_stale_min behind the last completed minute): the gate then does not
        block, and health carries a warning. Cached per poll minute."""
        cut = pd.Timestamp(now).floor("1min")
        if self._split_cache and self._split_cache[0] == cut:
            return self._split_cache[1]
        rets, why = {}, None
        for sym in SPLIT_TAPE_SYMBOLS:
            b = self.bars.get(sym)
            b = b[(b.index < cut) & (b.index.date == cut.date())] if b is not None and len(b) else None
            if b is None or b.empty:
                why = f"{sym} bars missing"
                break
            if b.index[-1] < cut - pd.Timedelta(minutes=1 + self.split_stale_min):
                why = f"{sym} bars stale (last {b.index[-1]:%H:%M})"
                break
            o = float(b["open"].iloc[0])
            if not o > 0:
                why = f"{sym} open missing"
                break
            rets[sym] = (float(b["close"].iloc[-1]) / o - 1) * 100
        if why:
            out = None
            self.health["split_tape_gate"] = {"warning": f"split-tape short gate not applied: {why}", "at": str(cut)}
            print(f"WARNING split-tape short gate: {why}; shorts not blocked")
        else:
            out = {"qqq_ret": round(rets["QQQ"], 4), "iwm_ret": round(rets["IWM"], 4),
                   "spread": round(rets["QQQ"] - rets["IWM"], 4)}
            self.health["split_tape_gate"] = {**out, "blocking": out["spread"] >= self.split_spread, "at": str(cut)}
        self._split_cache = (cut, out)
        return out

    def _quote(self, symbol: str):
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockLatestQuoteRequest

        q = self._client().get_stock_latest_quote(
            StockLatestQuoteRequest(symbol_or_symbols=symbol, feed=DataFeed(self.cfg["data"]["feed"])))[symbol]
        ts = getattr(q, "timestamp", None)
        if ts is not None:
            self._quote_ts[symbol] = pd.Timestamp(ts)
        else:
            self._quote_ts.pop(symbol, None)
        return float(q.bid_price or 0), float(q.ask_price or 0)

    def _realism(self, sig, ctx, px) -> tuple[bool, str, dict]:
        """Paper fills anything the price touches; skip what a real order book would not give us."""
        info = {}
        try:
            bid, ask = self._quote(sig.symbol)
        except Exception as e:
            return False, f"no quote ({e.__class__.__name__})", info
        if bid <= 0 or ask <= 0 or ask < bid:
            return False, "no two-sided quote", info
        mid = (bid + ask) / 2
        spread = ask - bid
        info.update(bid=bid, ask=ask, spread_bps=round(spread / mid * 1e4, 1))
        ok, why = self._crosscheck(sig, ctx, px, mid, info)
        if not ok:
            return False, why, info
        if info["spread_bps"] > self.live.get("max_spread_bps", 30):
            return False, f"spread {info['spread_bps']:.0f}bps > max", info
        risk_ps = abs(px - sig.stop)
        if risk_ps > 0 and spread / risk_ps > self.live.get("max_spread_risk_frac", 0.25):
            return False, f"spread is {spread / risk_ps:.0%} of stop distance", info
        vol = ctx.bars["volume"].tail(5).mean()
        info["cap_qty"] = int(self.live.get("max_participation", 0.10) * vol)
        return True, "ok", info

    @staticmethod
    def _utcnow() -> pd.Timestamp:
        return pd.Timestamp.now(tz="UTC")

    def _crosscheck(self, sig, ctx, px, mid, info) -> tuple[bool, str]:
        """Before any new entry: the bars the signal used are fresh and agree with the broker's live quote (owner
        2026-10-16, outage plan step 3). Rejections are journaled as skipped with a 'crosscheck:' reason."""
        dev = abs(px - mid) / mid * 100
        info["quote_dev_pct"] = round(dev, 3)
        qts = self._quote_ts.get(sig.symbol)
        if qts is not None:
            qts = qts if qts.tzinfo else qts.tz_localize("UTC")
            info["quote_age_s"] = round(max(0.0, (self._utcnow() - qts).total_seconds()), 1)
        idx = getattr(getattr(ctx, "bars", None), "index", None)
        if self._now is not None and isinstance(idx, pd.DatetimeIndex) and len(idx):
            info["bar_age_min"] = round((self._now - idx[-1]).total_seconds() / 60, 2)
        if self.xc_dev and dev > self.xc_dev:
            return False, f"crosscheck: ref {px:.2f} vs quote mid {mid:.2f} ({dev:.2f}% > {self.xc_dev:g}%)"
        if self.xc_age and info.get("quote_age_s") is not None and info["quote_age_s"] > self.xc_age:
            return False, f"crosscheck: quote {info['quote_age_s']:.0f}s old > {self.xc_age:g}s"
        if self.xc_bar and info.get("bar_age_min") is not None and info["bar_age_min"] > self.xc_bar:
            return False, f"crosscheck: bar {info['bar_age_min']:.1f} min old > {self.xc_bar:g} min"
        return True, "ok"

    def _log(self, sig, status, why, ref, now, info=None, qty=0, order_id=None):
        self.journal.record_signal(
            self.run_id, str(now.date()), now.isoformat(), sig.symbol, sig.strategy, sig.side, ref, sig.stop,
            sig.target, sig.entry_type, sig.entry_price, int(sig.bar_index), status, why, qty, order_id,
            json.dumps({**(info or {}), **{k: (float(v) if isinstance(v, (np.floating, float)) else v)
                                           for k, v in sig.meta.items()}}, default=str))

    def _enter(self, sig, px, key, ctx, now):
        coid = self._coid(sig, ctx, now)
        if self.same_setup_reentry:
            self.moments.add((sig.symbol, sig.strategy, self._moment(sig, ctx, now)))
            last = self.last_entry.get((sig.symbol, sig.strategy))
            if coid in self.entered or (last is not None and self._moment(sig, ctx, now) <= last):
                return self._log(sig, "skipped", "same setup, same moment", px, now)   # never twice for one bar
        if now.time() < self.no_entry_before:
            self._log(sig, "shadow", f"before {self.no_entry_before:%H:%M} (owner rule)", px, now)
            return
        if sig.side == -1:
            sh = self.cfg.get("shorts", {})
            if not sh.get("enabled", True):
                return self._log(sig, "skipped", "shorts disabled", px, now)
            if self.split_gate:
                gate = self._split_tape(now)
                if gate is not None and gate["spread"] >= self.split_spread:
                    return self._log(sig, "skipped", "split-tape short gate", px, now, gate)
            if sh.get("require_easy_to_borrow", True) and not self.broker.can_short(sig.symbol):
                return self._log(sig, "skipped", "not shortable/ETB", px, now)
        ok, why = self.risk.check(sig, px)
        if not ok:
            # logging only (playing-time report, 2026-10-12): which setup holds the symbol. Same decision, same reason.
            held = {"held_by": self.open_strategy.get(sig.symbol)} if why == "already in symbol" else None
            if why in ("opposite side held", "lot cap", "twin held"):                   # every setup holding a lot on the symbol
                held = {"held_by": list(dict.fromkeys(lot.get("strategy", lid)
                                                      for lid, lot in self.lots.get(sig.symbol, {}).items()))}
            if held and why in self._retry_reasons() and self.retry_after_release and sig.entry_type == "market":
                self.blocked.setdefault(key, {"bar": int(sig.bar_index), "done": False, "side": int(sig.side)})
            return self._log(sig, "skipped", why, px, now, held)
        ok, why, info = self._realism(sig, ctx, px)
        if not ok:
            return self._log(sig, "skipped", why, px, now, info)
        qty = self.risk.size(sig, px)
        if info.get("cap_qty") is not None and qty > info["cap_qty"]:
            info["size_capped_from"] = qty
            qty = info["cap_qty"]
        if qty < 1:
            return self._log(sig, "skipped", "size < 1 share after liquidity cap", px, now, info)
        if is_extended(ctx, self.cfg):
            info["tier"] = "extended"
        info["coid"] = coid                               # restart: the lot's id (several per setup/symbol/day)
        if self.dry_run:
            self.fired.add(key)
            self.open_strategy[sig.symbol] = sig.strategy
            self._entered(sig, coid, ctx, now)
            self.lots.setdefault(sig.symbol, {})[coid] = {"strategy": sig.strategy, "side": sig.side, "qty": qty,
                                                          "order_id": None, "coid": coid}
            print(f"DRY {sig.strategy} {sig.symbol} side={sig.side} qty={qty} ref={px:.2f} stop={sig.stop:.2f} {info}")
            return self._log(sig, "dry_run", "dry run", px, now, info, qty)
        try:
            o = self.broker.submit_bracket(sig, qty, coid)
        except Exception as e:  # broker rejects are journaled, not fatal
            return self._log(sig, "rejected", str(e)[:200], px, now, info, qty)
        self.fired.add(key)
        self.pending[sig.symbol] = _time.time()
        self.risk.state.trades_today += 1
        self.risk.state.open_symbols.add(sig.symbol)
        self.open_strategy[sig.symbol] = sig.strategy
        self._entered(sig, coid, ctx, now)
        self.lots.setdefault(sig.symbol, {})[coid] = {"strategy": sig.strategy, "side": sig.side, "qty": qty,
                                                      "order_id": str(o.id), "coid": coid}
        self._sync_open()
        self.journal.record_order(self.run_id, sig.symbol, sig.strategy, sig.side, qty, px, sig.stop,
                                  sig.target, str(o.id), "submitted", json.dumps(info, default=str))
        if sig.be_at_r is not None or sig.trail_r is not None or sig.time_stop_min:
            m = {"side": sig.side, "entry": px, "risk": abs(px - sig.stop), "stop": sig.stop,
                 "t0": now, "be_at_r": sig.be_at_r, "trail_r": sig.trail_r,
                 "trail_after_r": sig.trail_after_r, "time_stop_min": sig.time_stop_min,
                 "time_stop_min_r": sig.time_stop_min_r, "best": 0.0}
            if self.max_lots <= 1:
                self.managed[sig.symbol] = m
            else:
                self.managed[(sig.symbol, coid)] = {**m, "coid": coid, "strategy": sig.strategy}
        if self._live_scale_out(sig):
            self.scaling[(sig.symbol, coid)] = self._scale_state(sig.side, sig.stop, sig.target, sig.scale_out_r,
                                                                 sig.scale_out_frac, now, sig.strategy)
        self._log(sig, "submitted", "ok", px, now, info, qty, str(o.id))
        print(f"ENTER {sig.strategy} {sig.symbol} side={sig.side} qty={qty} ref={px:.2f} stop={sig.stop:.2f}")

    def _entered(self, sig, coid, ctx, now):
        self.entered.add(coid)
        if self.same_setup_reentry:
            k = (sig.symbol, sig.strategy)
            self.last_entry[k] = max(self.last_entry.get(k, ""), self._moment(sig, ctx, now))

    # ---------------------------------------------------------------- session
    def run(self, until: pd.Timestamp | None = None, poll_seconds: int = 60):
        """Trade until `until` (end of this job's slot) or the session flatten time."""
        clock = self.broker.clock()
        now = pd.Timestamp(clock.timestamp).tz_convert(NY)
        self.restore(now.date())
        last_status = None
        while True:
            try:
                clock = self.broker.clock()
            except Exception as e:                    # broker API unreachable: escalate (live.outage), keep polling
                now = pd.Timestamp.now(tz=NY)
                if until is not None and now >= until:
                    print(f"slot ends {until:%H:%M} with the broker unreachable: handing over")
                    break
                print(f"broker clock failed: {e}")
                self._broker_unreachable(now, e)
                _time.sleep(poll_seconds)
                continue
            now = pd.Timestamp(clock.timestamp).tz_convert(NY)
            self._broker_reachable(now)
            if until is not None and now >= until:
                print(f"slot ends {until:%H:%M}: handing over (broker-side stops stay in place)")
                break
            if not clock.is_open:
                if now.time() >= t("16:00") or pd.Timestamp(clock.next_open).tz_convert(NY).date() > now.date():
                    print("market closed for the day (after close or holiday)")
                    break
                self.write_status(now, "pre-open")
                _time.sleep(min(30, max(1, (pd.Timestamp(clock.next_open).tz_convert(NY) - now).total_seconds())))
                continue
            if now.time() >= self.flatten:
                self.flatten_mcf()
                _time.sleep(20)  # let the closing market orders fill before reconciling
                break
            self.step(now)
            self._sync_open()
            if last_status is None or now - last_status >= pd.Timedelta(minutes=self.live.get("status_every_min", 2)):
                self.reconcile(now.date())
                self.write_status(now, "trading")
                last_status = now
            _time.sleep(max(1, poll_seconds - now.second % poll_seconds + 3))
        self.reconcile(now.date())
        if now.time() >= self.flatten:
            self.what_if(now.date())
        self.write_status(now, "closed" if now.time() >= self.flatten else "handover")

    def flatten_mcf(self):
        """Close MCF's own positions/orders only — never anything else on the account."""
        print("flatten time: closing MCF positions")
        if self.dry_run:
            return
        mine = set(self._mcf_symbols())
        try:   # also every symbol MCF traded today, in case local state missed one
            mine |= {o.symbol for o in self.broker.orders_today_with_prefix(
                COID_PREFIX, pd.Timestamp.now(tz=NY).normalize().to_pydatetime())}
        except Exception as e:
            print(f"order lookup failed: {e}")
        self.broker.cancel_orders_with_prefix(COID_PREFIX)
        left = []
        for attempt in range(3):
            left = sorted(mine & set(self.broker.positions()))
            if not left:
                break
            for sym in left:
                try:
                    if not self.broker.close_mcf_position(sym, COID_PREFIX):
                        print(f"close {sym} not confirmed (pass {attempt + 1})")
                except Exception as e:
                    print(f"close {sym} failed: {e}")
            _time.sleep(3)
        left = sorted(mine & set(self.broker.positions()))
        self.health["flatten_failed"] = left
        if left:
            print(f"FLATTEN FAILED: still open after 3 passes: {left}")
        else:
            print("flatten complete: no MCF positions open")

    def reconcile(self, day):
        """Pair entry/exit fills from Alpaca into closed trades in the journal."""
        if self.dry_run:
            return
        from .reconcile import reconcile_day

        trades = reconcile_day(self.broker, self.journal, self.run_id, day, self.cfg)
        self._note_residuals(trades.attrs.get("residual") or {})
        self._excursions(trades)
        self.journal.add_trades(self.run_id, trades)
        self._release_closed_lots()
        if len(trades):
            today = trades[trades["date"] == str(day)]   # late-recovered trades of earlier sessions don't count today
            self.risk.state.realized_r += float(today["r_multiple"].sum())
            if "strategy" in today.columns:
                by = self.risk.state.realized_r_by_strategy
                order = today.sort_values("exit_time", kind="stable") if "exit_time" in today.columns else today
                for k, v in zip(order["strategy"], order["r_multiple"]):   # trade by trade, in exit order:
                    by[str(k)] = by.get(str(k), 0.0) + float(v)
                    self.risk.latch_setup_losses({str(k): by[str(k)]})   # LL-LATCH: touching the limit latches
            print(f"reconciled {len(trades)} trades for {day}")

    def _note_residuals(self, residual: dict):
        """Status only: lots still open after a partial exit (e.g. a target leg that filled part of the lot and keeps
        working for the rest). They hold shares, so they stay open lots (lot cap unchanged); health.partial_lots
        shows how much of each is left (2026-10-15: SYNA 2 of 7, XRT 1 of 10 held for hours)."""
        out = []
        for sym, lots in self.lots.items():
            for lot in lots.values():
                r = residual.get(str(lot.get("order_id")))
                lot["left"] = r["left"] if r else None
                lot["orig_qty"] = r["qty"] if r else None     # after a scale-out: what the scale-out left
                if r:
                    out.append({"symbol": sym, "strategy": lot.get("strategy"), "left": r["left"], "qty": r["qty"],
                                **({"scaled_out": r["scaled"]} if r.get("scaled") else {})})
        self.health["partial_lots"] = out

    def _release_closed_lots(self):
        """A lot is released once reconcile has paired its exit (journal order closed) or found it never filled.
        Reconcile closes a lot's order only when the lot is flat at the broker: none of its own legs is still working
        and its whole filled quantity is accounted for by its own fills (legs, moved-stop replacements, -x exit) plus
        genuine flatten closes - never by a sibling lot's fill (2026-10-13 mispairing)."""
        if not self.lots:
            return
        try:
            open_ids = set(self.journal.open_orders(self.run_id).broker_order_id.astype(str))
        except Exception as e:
            print(f"lot release skipped: {e}")
            return
        changed = False
        for sym in list(self.lots):
            for lot_id, lot in list(self.lots[sym].items()):
                if lot.get("order_id") is not None and str(lot["order_id"]) not in open_ids:
                    self.lots[sym].pop(lot_id)
                    changed = True
            if not self.lots[sym]:
                self.lots.pop(sym)
        if changed:
            self._sync_open()

    def _excursions(self, trades: pd.DataFrame):
        """MFE / MAE in R for each journaled trade (one row per lot), from the 1-minute bars between its entry and exit."""
        for i, r in trades.iterrows() if len(trades) else []:
            try:
                b = self.bars.get(r["symbol"])
                risk = abs(float(r["entry"]) - float(r["stop"]))
                if b is None or b.empty or not risk or np.isnan(risk):
                    continue
                t0 = pd.Timestamp(r["entry_time"]).tz_convert(NY).floor("1min")
                seg = b[(b.index >= t0) & (b.index <= pd.Timestamp(r["exit_time"]).tz_convert(NY))]
                if seg.empty:
                    continue
                side, e = int(r["side"]), float(r["entry"])
                hi, lo = float(seg["high"].max()), float(seg["low"].min())
                trades.at[i, "mfe_r"] = side * ((hi if side == 1 else lo) - e) / risk
                trades.at[i, "mae_r"] = side * ((lo if side == 1 else hi) - e) / risk
            except Exception:
                continue

    def what_if(self, day):
        """Simulate every signal NOT taken (shadow / skipped) on the full day's bars, with backtest costs,
        so the dashboard can show what each rule and skip reason cost or saved."""
        sig = self.journal.signals(self.run_id, str(day))
        sig = sig[~sig.status.isin(["submitted"])] if len(sig) else sig
        if not len(sig):
            return
        from ..strategies.base import Signal

        costs, flat = Costs.from_cfg(self.cfg["costs"]), t(self.cfg["session"]["flatten_by"])
        rows = []
        for r in sig.itertuples():
            bars = self.bars.get(r.symbol)
            if bars is None or bars.empty:
                continue
            s = Signal(r.symbol, r.strategy, int(r.side), int(r.bar_index), float(r.stop),
                       None if pd.isna(r.target) else float(r.target), r.entry_type,
                       None if pd.isna(r.entry_price) else float(r.entry_price))
            tr = simulate(s, bars, flat, costs)
            if tr is not None:
                d = tr.__dict__.copy()
                d["meta"] = f"status={r.status};why={r.reason}"
                rows.append(d)
        if rows:
            wid = self.journal.get_or_create_run("whatif", "MCF what-if (signals not taken)")
            self.journal.add_trades(wid, pd.DataFrame(rows))
            print(f"what-if: simulated {len(rows)} signals not taken")

    # ---------------------------------------------------------------- poll input log (live.log_poll_inputs)
    def _log_poll(self, now: pd.Timestamp, bars: dict, stale: bool):
        """Buffer one compact record of this poll's inputs (see poll_record). Errors are printed, never raised."""
        t0 = _time.perf_counter()
        try:
            rec = poll_record(now, bars, self.watchlist, self.health, stale, self._poll_log_ms)
            if self._poll_buf_since is None:
                self._poll_buf_since = _time.time()
            self._poll_buf.append(json.dumps(rec, separators=(",", ":")))
        except Exception as e:
            print(f"poll log failed: {type(e).__name__}: {e}")
        self._poll_log_ms = round((_time.perf_counter() - t0) * 1000, 2)

    def flush_poll_log(self, now: pd.Timestamp | None = None, force: bool = False) -> str | None:
        """Write the buffered poll records as one new gzip chunk <poll_log_dir>/<date>/<HHMMSS>.jsonl.gz (each chunk is
        written once, so the state branch grows by the compressed size only). Flushed every poll_log_flush_min minutes
        and at handover / close. Returns the chunk path or None. Never raises."""
        if not self.poll_log_dir or not self._poll_buf:
            return None
        if not force and self._poll_buf_since is not None and \
                _time.time() - self._poll_buf_since < self.poll_log_flush_min * 60:
            return None
        try:
            import gzip

            now = pd.Timestamp(now if now is not None else self._now or pd.Timestamp.now(tz=NY))
            d = os.path.join(self.poll_log_dir, str(now.date()))
            os.makedirs(d, exist_ok=True)
            path = os.path.join(d, f"{now:%H%M%S}.jsonl.gz")
            k = 1
            while os.path.exists(path):                       # never rewrite a chunk that may be pushed already
                path = os.path.join(d, f"{now:%H%M%S}-{k}.jsonl.gz")
                k += 1
            with gzip.open(path + ".tmp", "wt", compresslevel=9) as f:
                f.write("\n".join(self._poll_buf) + "\n")
            os.replace(path + ".tmp", path)
            self._poll_buf, self._poll_buf_since = [], None
            return path
        except Exception as e:
            print(f"poll log flush failed: {type(e).__name__}: {e}")
            return None

    def write_status(self, now, phase):
        self.flush_poll_log(now, force=phase in ("closed", "handover"))
        if not (self.status_path or self.on_status):
            return
        from ..report.live_status import build_status

        st = build_status(self, now, phase)
        if self.status_path:
            tmp = self.status_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(st, f, default=str, separators=(",", ":"))
            os.replace(tmp, self.status_path)
        if self.on_status:
            self.on_status(st)


def poll_record(now: pd.Timestamp, bars: dict, watchlist, health: dict, stale: bool, log_ms: float = 0.0) -> dict:
    """One poll's inputs, compactly (live.log_poll_inputs). Keys:
      t      poll time (ET, HH:MM:SS); ms = the fetch's wall time (ms); lms = the previous record's logging time (ms)
      n      watchlist size; got = symbols with at least one completed bar; fresh = symbols whose latest completed bar is
             the last completed minute (lm, HH:MM); exp = minutes 09:30..lm (a symbol trading every minute has exp bars)
      late   {"HHMM": [symbols]} symbols whose latest bar is older than lm, by that bar's minute
      miss   {"k": [symbols]} symbols holding exp - k bars (k > 0: minutes without a bar; only k != 0 listed)
      none   watchlist symbols without any bar (at most 50 listed; none_n = the count)
      stale  the runner's data-stale verdict this poll
    Everything a replay needs to rebuild each symbol's bar count (lab setups evaluate when a 5-minute bucket completes) and the
    data gaps the live runner saw."""
    cut = pd.Timestamp(now).floor("1min")
    lm = cut - pd.Timedelta(minutes=1)
    open_ = pd.Timestamp(f"{cut.date()} 09:30", tz=cut.tz)
    exp = max(0, int((lm - open_).total_seconds() // 60) + 1)
    late: dict[str, list] = {}
    miss: dict[str, list] = {}
    got = fresh = 0
    for s, b in bars.items():
        n = len(b) if b is not None else 0
        if not n:
            continue
        got += 1
        last = b.index[-1]
        if last >= lm:
            fresh += 1
        else:
            late.setdefault(f"{last:%H%M}", []).append(s)
        if n != exp:
            miss.setdefault(str(exp - n), []).append(s)
    none = sorted(set(watchlist) - {s for s, b in bars.items() if b is not None and len(b)})
    return {"t": f"{pd.Timestamp(now):%H:%M:%S}", "ms": round(float(health.get("last_poll_s") or 0) * 1000),
            "lms": log_ms, "n": len(watchlist), "got": got, "fresh": fresh, "lm": f"{lm:%H:%M}", "exp": exp,
            "late": late, "miss": miss, "none_n": len(none), "none": none[:50], "stale": bool(stale)}


def read_poll_log(poll_dir: str, day: str) -> list[dict]:
    """Every poll record of `day` from its chunks (<poll_dir>/<day>/*.jsonl.gz), in poll order."""
    import glob
    import gzip

    out = []
    for p in sorted(glob.glob(os.path.join(poll_dir, str(day), "*.jsonl.gz"))):
        with gzip.open(p, "rt") as f:
            out += [json.loads(line) for line in f if line.strip()]
    return sorted(out, key=lambda r: r["t"])
