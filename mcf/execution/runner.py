"""Paper-trading loop: same strategy code as the backtester, run every minute on live bars.

Flow each minute during RTH:
  1. pull today's 1-minute bars for the watchlist (scanner output)
  2. build DayContexts (prior-day stats come from cached history)
  3. run strategies; act only on signals whose bar is the latest completed bar
     (stop-entry signals are converted to a market order when the trigger trades)
  4. risk-check, size, submit bracket order, journal it
At flatten time: close everything. After the close: reconcile fills into the journal.
"""

from __future__ import annotations

import time as _time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from ..backtest.engine import SymbolHistory
from ..data.alpaca_data import fetch_bars
from ..journal import Journal
from ..strategies.base import Strategy, t
from .alpaca_broker import AlpacaBroker
from .risk import RiskManager

NY = "America/New_York"


class PaperRunner:
    def __init__(self, cfg: dict, strategies: list[Strategy], watchlist: list[str], history: dict[str, pd.DataFrame]):
        self.cfg = cfg
        self.strategies = strategies
        self.watchlist = watchlist
        self.hist = {s: SymbolHistory(s, df) for s, df in history.items() if not df.empty}
        self.broker = AlpacaBroker(paper=True)
        self.journal = Journal(cfg["data"]["journal_path"])
        self.run_id = self.journal.get_or_create_run("paper", "alpaca-paper")
        self.risk = RiskManager(cfg, self.broker.equity())
        self.flatten = t(cfg["session"]["flatten_by"])
        self.pending_stops: dict[tuple[str, str], object] = {}
        self.fired: set[tuple[str, str]] = set()
        self.open_strategy: dict[str, str] = {}

    def _sync_strategy_counts(self):
        counts: dict[str, int] = {}
        for sym in self.risk.state.open_symbols:
            st = self.open_strategy.get(sym)
            if st:
                counts[st] = counts.get(st, 0) + 1
        self.risk.state.open_by_strategy = counts

    def _contexts(self, today_bars: dict[str, pd.DataFrame], today):
        ctxs = []
        for sym, bars in today_bars.items():
            h = self.hist.get(sym)
            if h is None or bars.empty:
                continue
            # append today's bars to history so the context gets prior-day stats for `today`
            h2 = SymbolHistory(sym, pd.concat([h.intraday, bars]))
            ctx = h2.context(today)
            if ctx is not None:
                ctxs.append(ctx)
        orv = [c.rvol().iloc[min(4, len(c.bars) - 1)] for c in ctxs]
        for rank, i in enumerate(np.argsort(-np.nan_to_num(np.array(orv, float), nan=-1)), 1):
            ctxs[i].rank_rvol = rank
        return ctxs

    def step(self, now: pd.Timestamp):
        today = now.date()
        start = pd.Timestamp(f"{today} 09:30", tz=NY).to_pydatetime()
        bars = fetch_bars(self.watchlist, start, now.to_pydatetime(), feed=self.cfg["data"]["feed"])
        # drop the still-forming bar
        bars = {s: b[b.index < now.floor("1min")] for s, b in bars.items()}
        for ctx in self._contexts(bars, today):
            last = len(ctx.bars) - 1
            px = float(ctx.bars["close"].iloc[-1])
            for strat in self.strategies:
                key = (ctx.symbol, strat.name)
                if key in self.fired or not strat.eligible(ctx):
                    continue
                for sig in strat.generate(ctx)[: strat.max_signals_per_day]:
                    if sig.entry_type == "market" and sig.bar_index != last:
                        continue
                    if sig.entry_type == "stop":
                        hit = (ctx.bars["high"].iloc[-1] >= sig.entry_price) if sig.side == 1 else (
                            ctx.bars["low"].iloc[-1] <= sig.entry_price)
                        if sig.bar_index >= last or not hit:
                            continue
                    self._enter(sig, px, key)

    def _enter(self, sig, px, key):
        ok, why = self.risk.check(sig, px)
        if not ok:
            print(f"skip {sig.symbol} {sig.strategy}: {why}")
            return
        qty = self.risk.size(sig, px)
        if qty < 1:
            return
        coid = f"{sig.strategy}-{sig.symbol}-{datetime.now():%Y%m%d%H%M%S}"
        try:
            o = self.broker.submit_bracket(sig, qty, coid)
        except Exception as e:  # broker rejects are journaled, not fatal
            print(f"order rejected {sig.symbol}: {e}")
            self.journal.record_order(self.run_id, sig.symbol, sig.strategy, sig.side, qty, px, sig.stop,
                                      sig.target, coid, "rejected", str(e))
            return
        self.fired.add(key)
        self.risk.state.trades_today += 1
        self.risk.state.open_symbols.add(sig.symbol)
        self.open_strategy[sig.symbol] = sig.strategy
        self._sync_strategy_counts()
        self.journal.record_order(self.run_id, sig.symbol, sig.strategy, sig.side, qty, px, sig.stop,
                                  sig.target, str(o.id), "submitted", repr(sig.meta))
        print(f"ENTER {sig.strategy} {sig.symbol} side={sig.side} qty={qty} ref={px:.2f} stop={sig.stop:.2f}")

    def run_day(self, poll_seconds: int = 60):
        while True:
            clock = self.broker.clock()
            now = pd.Timestamp(clock.timestamp).tz_convert(NY)
            if not clock.is_open:
                if now.time() > t("16:00"):
                    break
                _time.sleep(30)
                continue
            if now.time() >= self.flatten:
                print("flatten time: closing all positions")
                self.broker.flatten_all()
                break
            self.step(now)
            self.risk.state.open_symbols &= set(self.broker.positions())
            self._sync_strategy_counts()
            _time.sleep(poll_seconds - now.second % poll_seconds + 2)
        self.reconcile(now.date())

    def reconcile(self, day):
        """Pair entry/exit fills from Alpaca into closed trades in the journal."""
        from .reconcile import reconcile_day

        trades = reconcile_day(self.broker, self.journal, self.run_id, day)
        self.journal.add_trades(self.run_id, trades)
        print(f"reconciled {len(trades)} trades for {day}")
