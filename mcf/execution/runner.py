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
import time as _time
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from ..backtest.engine import Costs, in_play_filter, is_extended, rank_contexts, simulate, universe_ok
from ..data.bars import TZ, normalize, rth
from ..journal import Journal
from ..strategies.base import DayContext, Strategy, t
from .alpaca_broker import AlpacaBroker
from .risk import RiskManager

NY = TZ
COID_PREFIX = os.environ.get("MCF_COID_PREFIX", "mcf-")   # Testing account: "mct-" (never touches the other book)


class PaperRunner:
    def __init__(self, cfg: dict, strategies: list[Strategy], priors: dict, dry_run: bool = False,
                 status_path: str | None = None, on_status=None, broker=None, data_client=None):
        self.cfg = cfg
        self.live = cfg.get("live", {})
        self.strategies = strategies
        self.priors = priors
        self.watchlist = sorted(priors)
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
        self.open_strategy: dict[str, str] = {}
        self.managed: dict[str, dict] = {}   # symbol -> trade-management state (time stop / breakeven / trail)
        self.bars: dict[str, pd.DataFrame] = {}
        self.last_fetch: pd.Timestamp | None = None
        self.health = {"polls": 0, "last_poll_s": None, "symbols_last_bar": 0, "last_bar": None}
        self.status_path = status_path
        self.on_status = on_status
        self.today = None

    # ---------------------------------------------------------------- state
    def restore(self, today):
        """Rebuild per-day state after a restart (second CI job, crash)."""
        self.today = today
        sig = self.journal.signals(self.run_id, str(today))
        for r in sig.itertuples():
            self.seen.add((r.symbol, r.strategy))
            if r.status in ("submitted", "dry_run"):
                self.fired.add((r.symbol, r.strategy))
                self.open_strategy[r.symbol] = r.strategy
        self.risk.state.trades_today = int((sig.status == "submitted").sum()) if len(sig) else 0
        if not self.dry_run:
            self._restore_from_broker(today)
            self._restore_management()
        done = self.journal.trades(run_id=self.run_id)
        if len(done):
            self.risk.state.realized_r = float(done.loc[done.date == str(today), "r_multiple"].sum())
        self._sync_open()

    def _restore_from_broker(self, today):
        """The broker is the source of truth for what MCF holds: the journal on the state branch can lag a
        crashed or cancelled job by a few minutes. Every MCF order id is mcf-<strategy>-<symbol>-<YYYYMMDD>."""
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
            try:
                strategy, symbol, _ = o.client_order_id[len(COID_PREFIX):].rsplit("-", 2)
            except ValueError:
                continue
            self.seen.add((symbol, strategy))
            self.fired.add((symbol, strategy))
            self.open_strategy.setdefault(symbol, strategy)
            if str(o.id) in known:
                continue
            side = 1 if str(getattr(o.side, "value", o.side)).lower() == "buy" else -1
            stop = next((float(l.stop_price) for l in (o.legs or []) if getattr(l, "stop_price", None)), float("nan"))
            tgt = next((float(l.limit_price) for l in (o.legs or []) if getattr(l, "limit_price", None)), None)
            ref = float(o.filled_avg_price) if o.filled_avg_price else float("nan")
            self.journal.record_order(self.run_id, symbol, strategy, side, int(float(o.qty or 0)), ref, stop, tgt,
                                      str(o.id), "submitted", '{"restored_from_broker": true}')
            added += 1
        if added:
            print(f"restored {added} MCF orders from the broker that the journal had not saved yet")

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

    def _mcf_symbols(self) -> set[str]:
        return set(self.open_strategy)

    def _sync_open(self):
        held = set(self.broker.positions()) if not self.dry_run else self._mcf_symbols()
        self.risk.state.open_symbols = held & self._mcf_symbols()
        counts: dict[str, int] = {}
        for sym in self.risk.state.open_symbols:
            st = self.open_strategy.get(sym)
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
                             sma20=getattr(p, "sma20", float("nan")))
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
        for sym, m in list(self.managed.items()):
            if sym not in held:
                self.managed.pop(sym)
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
                    self.broker.move_stop(sym, round(new, 2), COID_PREFIX)
                    print(f"STOP {sym} {m['stop']:.2f} -> {new:.2f} (best {m['best']:.2f}R)")
                    m["stop"] = new
                except Exception as e:
                    print(f"move stop {sym} failed: {e}")

    def step(self, now: pd.Timestamp):
        today = now.date()
        bars = self.fetch(now)
        self.manage(now, bars)
        self.ctxs = {c.symbol: c for c in self._contexts(bars, today)}
        for ctx in self.ctxs.values():
            last = len(ctx.bars) - 1
            px = float(ctx.bars["close"].iloc[-1])
            for strat in self.strategies:
                key = (ctx.symbol, strat.name)
                if key in self.seen or not strat.eligible(ctx):
                    continue
                for sig in strat.signals(ctx):
                    if sig.entry_type == "market" and sig.bar_index != last:
                        continue
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
                            self.seen.add(key)
                            self._log(sig, "skipped", f"missed: triggered at {seg.index[first]:%H:%M}", px, now)
                            continue
                    self.seen.add(key)
                    self._enter(sig, px, key, ctx, now)

    def _quote(self, symbol: str):
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockLatestQuoteRequest

        q = self._client().get_stock_latest_quote(
            StockLatestQuoteRequest(symbol_or_symbols=symbol, feed=DataFeed(self.cfg["data"]["feed"])))[symbol]
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
        if info["spread_bps"] > self.live.get("max_spread_bps", 30):
            return False, f"spread {info['spread_bps']:.0f}bps > max", info
        risk_ps = abs(px - sig.stop)
        if risk_ps > 0 and spread / risk_ps > self.live.get("max_spread_risk_frac", 0.25):
            return False, f"spread is {spread / risk_ps:.0%} of stop distance", info
        vol = ctx.bars["volume"].tail(5).mean()
        info["cap_qty"] = int(self.live.get("max_participation", 0.10) * vol)
        return True, "ok", info

    def _log(self, sig, status, why, ref, now, info=None, qty=0, order_id=None):
        self.journal.record_signal(
            self.run_id, str(now.date()), now.isoformat(), sig.symbol, sig.strategy, sig.side, ref, sig.stop,
            sig.target, sig.entry_type, sig.entry_price, int(sig.bar_index), status, why, qty, order_id,
            json.dumps({**(info or {}), **{k: (float(v) if isinstance(v, (np.floating, float)) else v)
                                           for k, v in sig.meta.items()}}, default=str))

    def _enter(self, sig, px, key, ctx, now):
        if now.time() < self.no_entry_before:
            self._log(sig, "shadow", f"before {self.no_entry_before:%H:%M} (owner rule)", px, now)
            return
        if sig.side == -1:
            sh = self.cfg.get("shorts", {})
            if not sh.get("enabled", True):
                return self._log(sig, "skipped", "shorts disabled", px, now)
            if sh.get("require_easy_to_borrow", True) and not self.broker.can_short(sig.symbol):
                return self._log(sig, "skipped", "not shortable/ETB", px, now)
        ok, why = self.risk.check(sig, px)
        if not ok:
            return self._log(sig, "skipped", why, px, now)
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
        coid = f"{COID_PREFIX}{sig.strategy}-{sig.symbol}-{now:%Y%m%d}"
        if self.dry_run:
            self.fired.add(key)
            self.open_strategy[sig.symbol] = sig.strategy
            print(f"DRY {sig.strategy} {sig.symbol} side={sig.side} qty={qty} ref={px:.2f} stop={sig.stop:.2f} {info}")
            return self._log(sig, "dry_run", "dry run", px, now, info, qty)
        try:
            o = self.broker.submit_bracket(sig, qty, coid)
        except Exception as e:  # broker rejects are journaled, not fatal
            return self._log(sig, "rejected", str(e)[:200], px, now, info, qty)
        self.fired.add(key)
        self.risk.state.trades_today += 1
        self.risk.state.open_symbols.add(sig.symbol)
        self.open_strategy[sig.symbol] = sig.strategy
        self._sync_open()
        self.journal.record_order(self.run_id, sig.symbol, sig.strategy, sig.side, qty, px, sig.stop,
                                  sig.target, str(o.id), "submitted", json.dumps(info, default=str))
        if sig.be_at_r is not None or sig.trail_r is not None or sig.time_stop_min:
            self.managed[sig.symbol] = {"side": sig.side, "entry": px, "risk": abs(px - sig.stop), "stop": sig.stop,
                                        "t0": now, "be_at_r": sig.be_at_r, "trail_r": sig.trail_r,
                                        "trail_after_r": sig.trail_after_r, "time_stop_min": sig.time_stop_min,
                                        "time_stop_min_r": sig.time_stop_min_r, "best": 0.0}
        self._log(sig, "submitted", "ok", px, now, info, qty, str(o.id))
        print(f"ENTER {sig.strategy} {sig.symbol} side={sig.side} qty={qty} ref={px:.2f} stop={sig.stop:.2f}")

    # ---------------------------------------------------------------- session
    def run(self, until: pd.Timestamp | None = None, poll_seconds: int = 60):
        """Trade until `until` (end of this job's slot) or the session flatten time."""
        clock = self.broker.clock()
        now = pd.Timestamp(clock.timestamp).tz_convert(NY)
        self.restore(now.date())
        last_status = None
        while True:
            clock = self.broker.clock()
            now = pd.Timestamp(clock.timestamp).tz_convert(NY)
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
        self.journal.add_trades(self.run_id, trades)
        if len(trades):
            self.risk.state.realized_r += float(trades["r_multiple"].sum())
            print(f"reconciled {len(trades)} trades for {day}")

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

    def write_status(self, now, phase):
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
