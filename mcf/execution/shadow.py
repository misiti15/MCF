"""Shadow mode (owner 2026-11-16): setups that cannot take a real trade, evaluated on the live runner's own polls.

What is shadowed (config `shadow:` and `shadow_setups:`):
  of_live    every setup enabled in this account (shadow.of_live, default on). The live loop hands each signal it draws
             to the shadow book (PaperRunner._tap) - the same signal objects, no second strategy call. Shadow then
             applies the same timing and setup gates but none of the account's resources, so it also records the
             trades live could not take (slots, buying power, per-setup caps, twin, max positions, lot cap). These lots
             are the TRUST CHECK: each night they are compared with the real trades (mcf/research/shadow_calib.py).
  only       every setup named in `shadow_setups` that is not live here (e.g. arena setups not live anywhere, Workbench
             copies awaiting deployment): its own strategy objects, evaluated on the same contexts after the real
             decisions of the poll.

Same as live: the 1-minute bars of the poll, the contexts (universe, in-play filter, ranking, earnings blackout - the
priors already exclude those names), market signals only on the latest completed bar, stop entries only when the
trigger traded on the latest bar, re-entry dedupe per decision bar, live.no_entry_before (09:50), shorts enabled /
split-tape gate / easy-to-borrow (the broker's cached asset read), price below minimum / through stop / through
target, the setup daily loss latch (shadow's OWN realized R), and the full fill-realism path of PaperRunner._realism
(quote cross-check, spread, spread vs stop, LR8-era stop-cost filter, participation cap) on a live SIP quote.

Fill model - CONSERVATIVE (owner 2026-11-16: "slightly harder to fill than our current estimates"; numbers in config
shadow:). Paper entries fill about at the quote seen at decision time (measured entry slip vs signal: median +3.6 bps,
research/live_ready/NOTES.md), so a shadow entry fills at the decision-time ask (long) / bid (short) PLUS
max(1 cent, 0.5 x the median slip) - 1.5 x the live median slip in all - plus shadow.latency_bps. Exits on the completed
1-minute bars after the entry, as the broker bracket does: stop first inside a bar (at the stop, or the open on a gap
through it, less half the entry spread and less stop_extra_bps (1 bp); the LR8 stop cost comes on top in pnl_adj),
then target ONLY when a bar trades THROUGH it by max(1 cent, 1 bp) - a touch is not a fill (at the limit, or the open on
a gap through it), then the opt-in live scale-out (bank at that bar's close, rest to breakeven). Entries that would rest
as limits fill only when traded through the same way. The assumptions are written into each shadow trade's meta. Per poll, after the bars: the live
trade management of PaperRunner.manage (time stop at the latest close, breakeven, trail). Every open lot closes at the
runner's flatten time at the latest close less half the spread. Costs: the LR8 production model (mcf.costs.pnl_adj),
so shadow R = pnl_adj / (|entry - stop| x shares), exactly like a live trade's R after costs.

Never: an order, a cancel, a slot, buying power, a trade count, a latch or halt of the real account. Shadow lots live in
the journal under their own run (kind "shadow", run id 3 when free), never run 1 (live) or 2 (what-if). Educational
only - not financial advice."""

from __future__ import annotations

import copy
import json
import math
import time as _time

import numpy as np
import pandas as pd

from ..costs import pnl_adj as _pnl_adj

NY = "America/New_York"
SHADOW_KIND = "shadow"
SHADOW_LABEL = "MCF shadow (no orders)"
SHADOW_RUN_ID = 3
WHATIF_LABEL = "MCF what-if (signals not taken)"

# live skip reasons that come from the ACCOUNT's resources (shadow ignores them; calibration does not call a shadow
# trade "extra" when live skipped the same signal for one of these)
RESOURCE_REASONS = ("halted", "daily loss limit", "max trades/day", "max concurrent positions",
                    "max positions for this setup", "twin held", "already in symbol", "opposite side held", "lot cap",
                    "position mismatch", "rejected", "same setup, same moment")


def ensure_run(journal) -> int:
    """The shadow run's id: an existing kind-'shadow' run, else id 3 when it is free (1 = live, 2 = what-if, created
    first when missing so the numbering holds), else the next id. Callers find it by kind, never by number."""
    row = journal.db.execute("SELECT id FROM runs WHERE kind=? AND label=? ORDER BY id LIMIT 1",
                             (SHADOW_KIND, SHADOW_LABEL)).fetchone()
    if row:
        return int(row[0])
    ids = {int(r[0]) for r in journal.db.execute("SELECT id FROM runs")}
    if SHADOW_RUN_ID not in ids:
        if 2 not in ids and 1 in ids:
            journal.get_or_create_run("whatif", WHATIF_LABEL)
            ids.add(2)
        if max(ids or {0}) < SHADOW_RUN_ID:
            from datetime import datetime, timezone

            journal.db.execute("INSERT INTO runs(id,kind,label,created_at,config) VALUES(?,?,?,?,?)",
                               (SHADOW_RUN_ID, SHADOW_KIND, SHADOW_LABEL, datetime.now(timezone.utc).isoformat(), "{}"))
            journal.db.commit()
            return SHADOW_RUN_ID
    return journal.new_run(SHADOW_KIND, SHADOW_LABEL)


def shadow_run_id(journal) -> int | None:
    row = journal.db.execute("SELECT min(id) FROM runs WHERE kind=?", (SHADOW_KIND,)).fetchone()
    return None if row is None or row[0] is None else int(row[0])


def extra_strategies(cfg: dict, live_names: set[str]) -> list:
    """Strategies for `shadow_setups` (names) not live in this account. Params from this account's config (enabled or
    not), else from another account overlay (config/account_*.yaml), else from `shadow_strategies` (a name -> params
    map for Workbench copies). A name that cannot be built is reported and skipped."""
    names = [n for n in (cfg.get("shadow_setups") or []) if n not in live_names]
    if not names:
        return []
    import yaml

    from ..config import CONFIG_DIR
    from ..strategies.setups import build_strategies

    pool: dict = {}
    for f in sorted(CONFIG_DIR.glob("account_*.yaml")):
        try:
            for k, v in ((yaml.safe_load(f.read_text()) or {}).get("strategies") or {}).items():
                pool.setdefault(k, v or {})
        except Exception:
            continue
    pool.update(cfg.get("strategies") or {})
    pool.update(cfg.get("shadow_strategies") or {})
    out = []
    for n in dict.fromkeys(names):
        if n not in pool:
            print(f"shadow: setup {n} not found in any config; skipped")
            continue
        sub = {**cfg, "strategies": {n: {**(pool[n] or {}), "enabled": True}}}
        try:
            out += build_strategies(sub)
        except Exception as e:
            print(f"shadow: setup {n} failed to build: {type(e).__name__}: {e}")
    return out


def make_shadow(runner):
    sc = runner.cfg.get("shadow") or {}
    if not sc.get("enabled", False):
        return None
    live = {getattr(s, "name", None) for s in runner.strategies}
    return ShadowBook(runner, extra_strategies(runner.cfg, live))


def _ts(x) -> pd.Timestamp:
    t = pd.Timestamp(x)
    return t.tz_localize(NY) if t.tzinfo is None else t.tz_convert(NY)


class ShadowBook:
    def __init__(self, runner, extras: list | None = None):
        self.r = runner
        sc = runner.cfg.get("shadow") or {}
        self.of_live = bool(sc.get("of_live", True))
        self.latency_bps = float(sc.get("latency_bps", 0.0) or 0.0)
        self.slip_bps = float(sc.get("entry_median_slip_bps", 3.6))
        self.slip_mult = float(sc.get("entry_slip_mult", 1.5))
        self.entry_min_ps = float(sc.get("entry_min_extra_ps", 0.01))
        self.thru_ps = float(sc.get("through_min_ps", 0.01))
        self.thru_bps = float(sc.get("through_bps", 1.0))
        self.stop_bps = float(sc.get("stop_extra_bps", 1.0))
        self.fill_tag = (f"cons:entry=quote+max({self.entry_min_ps:g},{self.slip_mult - 1:g}x{self.slip_bps:g}bp)"
                         f"+{self.latency_bps:g}bp|thru=max({self.thru_ps:g},{self.thru_bps:g}bp)|stop=-half_spread"
                         f"-{self.stop_bps:g}bp+LR8")
        self.budget = float(sc.get("budget_frac", 0.10) or 0.10)
        self.extras = list(extras or [])
        self.extra_names = {getattr(s, "name", "") for s in self.extras}
        self._run_id: int | None = None
        self.cands: list[tuple] = []          # (strat, ctx, sig, last, px, mode) of this poll
        self.lots: dict[str, dict] = {}       # shadow lot id -> state (JSON-serialisable)
        self.seen: set = set()
        self.moments: set = set()
        self.last_entry: dict = {}
        self.entered: set[str] = set()
        self.lab_bucket: dict = {}
        self.realized: dict[str, float] = {}  # setup -> today's shadow R after costs (own setup loss latch)
        self.stopped: set[str] = set()
        self.marked: set[tuple] = set()       # (day, setup, mode) session markers written
        self.errors = 0
        self.every = 1                        # extras evaluated every N polls (budget guard)
        self._poll_n = 0
        self._ema_sh = None
        self._ema_live = None
        self._sig_rows: list[tuple] = []
        self._new_lots: list[dict] = []
        self._dirty: set[str] = set()          # lots whose stop / scale-out changed: persisted this poll
        self._touched: set[str] = set()        # lots with new bars only: persisted every PERSIST_EVERY polls
        self._closed: list[dict] = []
        self.stats = {"polls": 0, "entered": 0, "closed": 0, "skipped": 0, "quote_calls": 0}

    # ------------------------------------------------------------------------------------------------ journal
    @property
    def run_id(self) -> int:
        if self._run_id is None:
            self._run_id = ensure_run(self.r.journal)
        return self._run_id

    def mode_of(self, name: str) -> str:
        return "only" if name in self.extra_names else "of_live"

    def restore(self, today):
        """After a restart: today's shadow dedupe, open shadow lots and the shadow setup-loss latch."""
        rid = shadow_run_id(self.r.journal)
        if rid is None:
            return
        self._run_id = rid
        sig = self.r.journal.signals(rid, str(today))
        for x in sig.itertuples():
            info = _info(x.info)
            if x.status == "shadow_session":
                self.marked.add((str(today), x.strategy, info.get("mode", "of_live")))
                continue
            key = (x.symbol, x.strategy)
            self.seen.add(key)
            bt = info.get("bar_time") or "2359"
            self.moments.add((*key, bt))
            if x.status == "shadow_entered":
                self.entered.add(str(x.broker_order_id))
                self.last_entry[key] = max(self.last_entry.get(key, ""), bt)
        for o in self.r.journal.open_orders(rid).itertuples():
            st = _info(o.meta)
            if not st or str(st.get("day")) != str(today):
                self.r.journal.update_order_status(o.broker_order_id, "expired")   # an earlier day's lot: never carried
                continue
            self.lots[str(o.broker_order_id)] = st
        tr = self.r.journal.trades(run_id=rid)
        if len(tr):
            from ..costs import cost_r

            td = tr.loc[tr.date.astype(str) == str(today)].copy()
            if len(td):
                td["_rc"] = cost_r(td)
                self.realized = {str(k): float(v) for k, v in td.groupby("strategy")["_rc"].sum().items()}
                lim = self.r.risk.setup_loss_limit
                if lim is not None:
                    low = td.sort_values("exit_time", kind="stable").groupby("strategy")["_rc"].cumsum() \
                        .groupby(td.sort_values("exit_time", kind="stable")["strategy"]).min()
                    self.stopped |= {str(k) for k, v in low.items() if v <= -lim}

    def _signal(self, sig, status, why, ref, now, info=None, qty=0, sid=None):
        self._sig_rows.append((self.run_id, str(now.date()), now.isoformat(), sig.symbol, sig.strategy, int(sig.side),
                               ref, sig.stop, sig.target, sig.entry_type, sig.entry_price, int(sig.bar_index), status,
                               why, int(qty), sid, json.dumps({**(info or {}), **_plain(sig.meta)}, default=str)))
        if status != "shadow_entered" and status != "shadow_session":
            self.stats["skipped"] += 1

    def _session_markers(self, now):
        day = str(now.date())
        names = ([(getattr(s, "name", ""), "of_live") for s in self.r.strategies] if self.of_live else []) + \
                [(getattr(s, "name", ""), "only") for s in self.extras]
        for n, mode in names:
            if (day, n, mode) in self.marked:
                continue
            self.marked.add((day, n, mode))
            self._sig_rows.append((self.run_id, day, now.isoformat(), "", n, 0, None, None, None, None, None, -1,
                                   "shadow_session", "evaluated", 0, None, json.dumps({"mode": mode})))

    PERSIST_EVERY = 5

    def flush(self, force: bool = False):
        """One transaction per poll: shadow signals, new / changed / closed lots, closed shadow trades. Lots that only
        saw new bars (excursions, last bar) are written every PERSIST_EVERY polls and at the flatten (restart state)."""
        j = self.r.journal
        if force or self._poll_n % self.PERSIST_EVERY == 0:
            self._dirty |= self._touched
            self._touched = set()
        if not (self._sig_rows or self._new_lots or self._dirty or self._closed):
            return
        db = j.db
        if self._sig_rows:
            db.executemany("INSERT INTO signals(run_id,day,ts,symbol,strategy,side,ref_price,stop,target,entry_type,"
                           "entry_price,bar_index,status,reason,qty,broker_order_id,info) "
                           "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", self._sig_rows)
        for lot in self._new_lots:
            db.execute("INSERT OR IGNORE INTO orders(run_id,created_at,symbol,strategy,side,qty,entry_ref,stop,target,"
                       "broker_order_id,status,meta) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                       (self.run_id, lot["t0"], lot["symbol"], lot["strategy"], lot["side"], lot["qty"], lot["ref"],
                        lot["stop0"], lot["target"], lot["sid"], "shadow_open", json.dumps(lot, default=str)))
        for sid in self._dirty:
            lot = self.lots.get(sid)
            if lot is not None:
                db.execute("UPDATE orders SET meta=? WHERE broker_order_id=?", (json.dumps(lot, default=str), sid))
        for row in self._closed:
            db.execute("UPDATE orders SET status='closed', meta=? WHERE broker_order_id=?",
                       (json.dumps(row["_lot"], default=str), row["broker_order_id"]))
        db.commit()
        if self._closed:
            j.add_trades(self.run_id, pd.DataFrame([{k: v for k, v in c.items() if k != "_lot"} for c in self._closed]))
        self._sig_rows, self._new_lots, self._dirty, self._closed = [], [], set(), []

    # ------------------------------------------------------------------------------------------------ the poll
    def begin_poll(self):
        self.cands = []

    def offer(self, strat, ctx, sig, last, px, mode="of_live"):
        if mode == "of_live" and not self.of_live:
            return
        s = copy.copy(sig)
        s.meta = dict(sig.meta or {})
        self.cands.append((strat, ctx, s, int(last), float(px), mode))

    def poll(self, now: pd.Timestamp, bars: dict, ctxs: dict | None, live_ms: float):
        t0 = _time.perf_counter()
        self.stats["polls"] += 1
        self._poll_n += 1
        self._session_markers(now)
        self.manage(now, bars)
        if ctxs is not None:
            if self.extras and self._poll_n % self.every == 0:
                self._scan_extras(ctxs)
            self._process(now)
        self.cands = []
        self.flush()
        self._budget((_time.perf_counter() - t0) * 1000, live_ms)

    def _budget(self, sh_ms: float, live_ms: float):
        """Poll-time guard: shadow work is measured against the live part of the poll (fetch + decisions). Over
        shadow.budget_frac (10%) on average, the `only` setups are evaluated every other poll (logged in health)."""
        a = 0.2
        self._ema_sh = sh_ms if self._ema_sh is None else (1 - a) * self._ema_sh + a * sh_ms
        self._ema_live = live_ms if self._ema_live is None else (1 - a) * self._ema_live + a * live_ms
        share = self._ema_sh / self._ema_live if self._ema_live and self._ema_live > 0 else 0.0
        if self.extras and self.stats["polls"] >= 5:
            if share > self.budget and self.every == 1:
                self.every = 2
                print(f"shadow: {share:.0%} of poll time > {self.budget:.0%}: shadow-only setups every other poll")
            elif share < self.budget / 2 and self.every > 1:
                self.every = 1
        self.r.health["shadow"] = {
            "run_id": self._run_id, "of_live": self.of_live, "only_setups": len(self.extras),
            "open_lots": len(self.lots), "entered": self.stats["entered"], "closed": self.stats["closed"],
            "polls": self.stats["polls"], "avg_ms": round(self._ema_sh, 1), "live_avg_ms": round(self._ema_live or 0, 1),
            "share_of_poll": round(share, 3), "only_every_n_polls": self.every, "quote_calls": self.stats["quote_calls"],
            "errors": self.errors}

    def _scan_extras(self, ctxs: dict):
        """`only` setups: the live loop's evaluation order and pre-filters, on their own strategy objects."""
        for ctx in ctxs.values():
            last = len(ctx.bars) - 1
            px = float(ctx.bars["close"].iloc[-1])
            for strat in self.extras:
                if getattr(strat, "ticker_split", None) and not strat.trades_symbol(ctx.symbol):
                    continue
                key = (ctx.symbol, strat.name)
                if key in self.seen and not self.r.same_setup_reentry:
                    continue
                if not strat.eligible(ctx):
                    continue
                if self._bucket_done(strat, key, ctx):
                    continue
                for sig in strat.signals(ctx):
                    self.offer(strat, ctx, sig, last, px, mode="only")

    def _bucket_done(self, strat, key, ctx) -> bool:
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

    def _moment(self, sig, ctx, now) -> str:
        return self.r._moment(sig, ctx, now)

    def _process(self, now: pd.Timestamp):
        r = self.r
        want = []
        for strat, ctx, sig, last, px, mode in self.cands:
            key = (ctx.symbol, strat.name)
            if key in self.seen and not r.same_setup_reentry:
                continue
            if sig.entry_type == "market" and sig.bar_index != last:
                continue
            m = self._moment(sig, ctx, now)
            if r.same_setup_reentry and ((*key, m) in self.moments or (key in self.last_entry and m <= self.last_entry[key])):
                continue
            if sig.entry_type == "stop":
                if sig.bar_index >= last or last - sig.bar_index > sig.entry_valid_bars:
                    continue
                seg = ctx.bars.iloc[sig.bar_index + 1:]
                crossed = (seg["high"] >= sig.entry_price) if sig.side == 1 else (seg["low"] <= sig.entry_price)
                if not crossed.any():
                    continue
                first = int(np.argmax(crossed.to_numpy()))
                if first < len(seg) - 1:
                    self._mark(key, m)
                    self._signal(sig, "shadow_skipped", f"missed: triggered at {seg.index[first]:%H:%M}", px, now,
                                 {"mode": mode})
                    continue
            if sig.entry_type == "limit" and sig.entry_price is not None:
                # a resting limit fills only when the latest bar trades THROUGH it (owner 2026-11-16: a touch is not a fill)
                lp, b = float(sig.entry_price), ctx.bars.iloc[-1]
                thr = max(self.thru_ps, self.thru_bps * lp / 1e4)
                if (sig.side == 1 and float(b["low"]) > lp - thr) or (sig.side == -1 and float(b["high"]) < lp + thr):
                    continue
            self._mark(key, m)
            ok, why = self._gates(sig, px, now, m)
            if not ok:
                self._signal(sig, "shadow_skipped", why, px, now, {"mode": mode, "bar_time": m})
                continue
            want.append((strat, ctx, sig, px, mode, m))
        if not want:
            return
        quotes = self._quotes(sorted({w[2].symbol for w in want}))
        for strat, ctx, sig, px, mode, m in want:
            q = quotes.get(sig.symbol)
            if q is None:
                self._signal(sig, "shadow_skipped", "no quote", px, now, {"mode": mode, "bar_time": m})
                continue
            ok, why, info = r._realism(sig, ctx, px, quote=q)
            info.update(mode=mode, bar_time=m)
            if not ok:
                self._signal(sig, "shadow_skipped", why, px, now, info)
                continue
            qty = r.risk.size(sig, px)
            if info.get("cap_qty") is not None and qty > info["cap_qty"]:
                info["size_capped_from"] = qty
                qty = info["cap_qty"]
            if qty < 1:
                self._signal(sig, "shadow_skipped", "size < 1 share after liquidity cap", px, now, info)
                continue
            self._open(strat, sig, px, q, qty, now, m, mode, info)

    def _mark(self, key, m):
        self.seen.add(key)
        if self.r.same_setup_reentry:
            self.moments.add((*key, m))

    def _gates(self, sig, px, now, m) -> tuple[bool, str]:
        """PaperRunner._enter's gates that are the SETUP's (timing, shorts, borrow, price) - not the account's."""
        r = self.r
        sid = self._sid(sig, now, m)
        if r.same_setup_reentry:
            last = self.last_entry.get((sig.symbol, sig.strategy))
            if sid in self.entered or (last is not None and m <= last):
                return False, "same setup, same moment"
        if now.time() < r.no_entry_before:
            return False, f"before {r.no_entry_before:%H:%M} (owner rule)"
        if sig.side == -1:
            sh = r.cfg.get("shorts", {})
            if not sh.get("enabled", True):
                return False, "shorts disabled"
            if r.split_gate:
                gate = r._split_tape(now)
                if gate is not None and gate["spread"] >= r.split_spread:
                    return False, "split-tape short gate"
            if sh.get("require_easy_to_borrow", True):
                try:
                    if not r.broker.can_short(sig.symbol):
                        return False, "not shortable/ETB"
                except Exception:
                    return False, "not shortable/ETB"
        if px < r.risk.min_price:
            return False, "price below minimum"
        lim = r.risk.setup_loss_limit
        if lim is not None and (sig.strategy in self.stopped or self.realized.get(sig.strategy, 0.0) <= -lim):
            self.stopped.add(sig.strategy)
            return False, "setup daily loss limit"
        if sig.side * (px - sig.stop) <= 0:
            return False, "price already through stop"
        if sig.target is not None and sig.side * (sig.target - px) <= 0:
            return False, "price already through target"
        return True, "ok"

    def _sid(self, sig, now, m) -> str:
        return f"shadow-{sig.strategy}-{sig.symbol}-{now:%Y%m%d}-{m}"

    def _quotes(self, symbols: list[str]) -> dict:
        """(bid, ask, ts) per symbol: the quote live fetched this poll when there is one, else ONE batched latest-quote
        request for the rest (per-symbol fallback when the batch fails)."""
        out = {s: self.r._poll_quotes[s] for s in symbols if s in self.r._poll_quotes}
        rest = [s for s in symbols if s not in out]
        if rest:
            out.update(self.fetch_quotes(rest))
        return out

    def fetch_quotes(self, symbols: list[str]) -> dict:
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockLatestQuoteRequest

        def one(syms):
            self.stats["quote_calls"] += 1
            res = self.r._client().get_stock_latest_quote(
                StockLatestQuoteRequest(symbol_or_symbols=syms, feed=DataFeed(self.r.cfg["data"]["feed"])))
            o = {}
            for s, q in (res or {}).items():
                ts = getattr(q, "timestamp", None)
                o[s] = (float(q.bid_price or 0), float(q.ask_price or 0), None if ts is None else pd.Timestamp(ts))
            return o

        try:
            return one(symbols)
        except Exception:
            out = {}
            for s in symbols:
                try:
                    out.update(one([s]))
                except Exception:
                    continue
            return out

    # ------------------------------------------------------------------------------------------------ lots
    def _open(self, strat, sig, px, q, qty, now, m, mode, info):
        bid, ask = q[0], q[1]
        side = int(sig.side)
        q0 = ask if side == 1 else bid
        extra = max(self.entry_min_ps, (self.slip_mult - 1) * self.slip_bps * q0 / 1e4) + self.latency_bps * q0 / 1e4
        fill = q0 + side * extra
        sid = self._sid(sig, now, m)
        params = getattr(strat, "params", None) or {}
        scale = bool(params.get("live_scale_out")) and bool(sig.scale_out_r)
        managed = sig.be_at_r is not None or sig.trail_r is not None or bool(sig.time_stop_min)
        lot = {"sid": sid, "day": str(now.date()), "mode": mode, "symbol": sig.symbol, "strategy": sig.strategy,
               "side": side, "qty": int(qty), "left": int(qty), "ref": float(px), "entry": float(fill),
               "half_spread": float(max(0.0, (ask - bid) / 2)), "quote": float(q0), "stop0": float(sig.stop), "stop": float(sig.stop),
               "target": None if sig.target is None else float(sig.target), "t0": now.isoformat(), "bar_time": m,
               "last_ns": None, "best": 0.0, "mfe": 0.0, "mae": 0.0, "parts": [],
               "managed": managed, "be_at_r": _f(sig.be_at_r), "trail_r": _f(sig.trail_r),
               "trail_after_r": _f(sig.trail_after_r), "time_stop_min": _f(sig.time_stop_min),
               "time_stop_min_r": _f(sig.time_stop_min_r),
               "scale_r": float(sig.scale_out_r) if scale else None, "scale_frac": float(sig.scale_out_frac or 0.5),
               "scaled": False, "spread_bps": _f(info.get("spread_bps"))}
        self.lots[sid] = lot
        self._new_lots.append(lot)
        self.entered.add(sid)
        if self.r.same_setup_reentry:
            k = (sig.symbol, sig.strategy)
            self.last_entry[k] = max(self.last_entry.get(k, ""), m)
        self.stats["entered"] += 1
        self._signal(sig, "shadow_entered", "ok", px, now, {**info, "fill": round(fill, 4)}, qty, sid)

    def manage(self, now: pd.Timestamp, bars: dict):
        arr: dict = {}                                    # symbol -> numpy views of its bars, built once per poll
        for sid, lot in list(self.lots.items()):
            sym = lot["symbol"]
            b = bars.get(sym) if bars else None
            if b is not None and len(b):
                if sym not in arr:
                    arr[sym] = (b.index.as_unit("ns").asi8, b["open"].to_numpy(float), b["high"].to_numpy(float),
                                b["low"].to_numpy(float), b["close"].to_numpy(float), b.index)
                self._bars(lot, arr[sym])
            if sid not in self.lots:
                continue
            if lot["managed"]:
                self._manage_rules(lot, now, b)

    def _bars(self, lot, a):
        """Completed bars since the entry, in order: stop (first inside a bar), target, scale-out. a = (ns, o, h, l, c,
        index) of the symbol's bars this poll."""
        ns, O, H, L, Cl, idx = a
        if "t0_ns" not in lot:
            lot["t0_ns"] = int(_ts(lot["t0"]).floor("1min").value)
        lo_ns = lot["t0_ns"] if lot.get("last_ns") is None else int(lot["last_ns"]) + 1
        k0 = int(np.searchsorted(ns, lo_ns, side="left"))
        if k0 >= len(ns):
            return
        side, e = lot["side"], lot["entry"]
        risk0 = abs(e - lot["stop0"]) or 1e-9
        hs = lot["half_spread"]
        mrisk = abs(lot["ref"] - lot["stop0"])
        for k in range(k0, len(ns)):
            o, hi, lo, c = O[k], H[k], L[k], Cl[k]
            lot["last_ns"] = int(ns[k])
            stop, tgt = lot["stop"], lot["target"]
            adverse, fav = (lo, hi) if side == 1 else (hi, lo)
            lot["mae"] = min(lot["mae"], side * (adverse - e) / risk0)
            if side * (adverse - stop) <= 0:                                      # stop first inside a bar
                px = o if side * (o - stop) <= 0 else stop
                px = float(px)
                self._close(lot, px - side * (hs + self.stop_bps * px / 1e4), "stop", idx[k])
                return
            if tgt is not None and side * (fav - tgt) >= max(self.thru_ps, self.thru_bps * tgt / 1e4):   # through
                px = o if side * (o - tgt) >= 0 else tgt
                self._close(lot, float(px), "target", idx[k])
                return
            lot["mfe"] = max(lot["mfe"], float(side * (fav - e) / risk0))
            if mrisk > 0:
                lot["best"] = max(lot["best"], float(side * (fav - lot["ref"]) / mrisk))
            if lot["scale_r"] and not lot["scaled"]:
                level = e + side * lot["scale_r"] * risk0
                if side * (fav - level) >= 0 and lot["left"] >= 2:
                    q = int(math.floor(lot["left"] * lot["scale_frac"]))
                    if q >= 1:
                        lot["parts"].append([q, float(c - side * hs), "scaleout", idx[k].isoformat()])
                        lot["left"] -= q
                        lot["stop"] = max(lot["stop"], e) if side == 1 else min(lot["stop"], e)
                    lot["scaled"] = True
                    self._dirty.add(lot["sid"])
        lot["mae"] = float(lot["mae"])
        self._touched.add(lot["sid"])

    def _manage_rules(self, lot, now, b):
        """PaperRunner.manage on a shadow lot: time stop, breakeven move, trailing stop (entry = the reference price,
        as live manage() uses)."""
        if lot["sid"] not in self.lots:
            return
        side, ref = lot["side"], lot["ref"]
        risk = abs(ref - lot["stop0"])
        if risk <= 0:
            return
        if "t0_exact_ns" not in lot:
            lot["t0_exact_ns"] = int(_ts(lot["t0"]).value)
        mins = (now.value - lot["t0_exact_ns"]) / 6e10
        if lot["time_stop_min"] and mins >= lot["time_stop_min"] and lot["best"] < (lot["time_stop_min_r"] or 0.0):
            px = self._last_close(b, now)
            if px is not None:
                self._close(lot, px - side * lot["half_spread"], "timestop", now)
            return
        new = lot["stop"]
        if lot["be_at_r"] is not None and lot["best"] >= lot["be_at_r"]:
            new = max(new, ref) if side == 1 else min(new, ref)
        if lot["trail_r"] is not None and lot["best"] >= (lot["trail_after_r"] or 1.0):
            tr = ref + side * (lot["best"] - lot["trail_r"]) * risk
            new = max(new, tr) if side == 1 else min(new, tr)
        if side * (new - lot["stop"]) > 0.005:
            lot["stop"] = round(new, 2)
            self._dirty.add(lot["sid"])

    @staticmethod
    def _last_close(b, now) -> float | None:
        if b is None or not len(b):
            return None
        done = b[b.index < now.floor("1min")]
        return float((done if len(done) else b)["close"].iloc[-1])

    def flatten(self, now: pd.Timestamp):
        """Close every open shadow lot at the runner's flatten time (latest completed close less half the spread)."""
        bars = {s: b for s, b in (self.r.bars or {}).items() if len(b)}
        cut = now.floor("1min")
        done = {s: b[b.index < cut] for s, b in bars.items()}
        self.manage(now, done)
        for sid, lot in list(self.lots.items()):
            px = self._last_close(done.get(lot["symbol"]), now)
            if px is None:
                px = lot["entry"]
            self._close(lot, px - lot["side"] * lot["half_spread"], "flatten", now)
        self.flush(force=True)

    def _close(self, lot, px: float, why: str, ts):
        side, e, qty = lot["side"], lot["entry"], lot["qty"]
        ts = pd.Timestamp(ts)
        parts = [(float(q), float(p), w) for q, p, w, *_ in lot["parts"]]
        if lot["left"] > 0:
            parts.append((float(lot["left"]), float(px), why))
        pnl = sum(side * q * (p - e) for q, p, _ in parts)
        adj, tag = _pnl_adj(pnl, side, e, qty, parts, lot["target"], lot["day"], self.r.cfg)
        risk = abs(e - lot["stop0"]) * qty
        shares_out = sum(q for q, *_ in parts) or 1.0
        exit_px = sum(q * p for q, p, _ in parts) / shares_out
        # live naming (mcf.execution.reconcile): scaled+<remainder exit>, a stop after a scale-out is "breakeven"
        reason = why if not lot["parts"] else "scaled+" + ("breakeven" if why == "stop" else why)
        meta = (f"shadow;mode={lot['mode']};fill_model={self.fill_tag};quote={lot.get('quote')};bar_time={lot['bar_time']};cost_model={tag};spread_bps={lot.get('spread_bps')}"
                f";exit_parts=" + ",".join(f"{w}:{q:g}@{p:.4f}" for q, p, w in parts))
        row = {"symbol": lot["symbol"], "strategy": lot["strategy"], "side": side, "date": lot["day"],
               "signal_time": lot["t0"], "entry_time": lot["t0"], "entry": e, "stop": lot["stop0"], "target": lot["target"],
               "exit_time": ts.isoformat(), "exit": exit_px, "exit_reason": reason,
               "r_multiple": pnl / risk if risk > 0 else None, "mae_r": lot["mae"], "mfe_r": lot["mfe"],
               "success": int(adj > 0), "shares": qty, "pnl": pnl, "meta": meta, "broker_order_id": lot["sid"],
               "pnl_adj": adj, "_lot": {**lot, "closed": ts.isoformat(), "exit_reason": reason}}
        self._closed.append(row)
        self.lots.pop(lot["sid"], None)
        self._dirty.discard(lot["sid"])
        self._touched.discard(lot["sid"])
        self.realized[lot["strategy"]] = self.realized.get(lot["strategy"], 0.0) + (adj / risk if risk > 0 else 0.0)
        lim = self.r.risk.setup_loss_limit
        if lim is not None and self.realized[lot["strategy"]] <= -lim:
            self.stopped.add(lot["strategy"])
        self.stats["closed"] += 1


def _f(x) -> float | None:
    """A JSON-safe float (numpy scalars too); None stays None."""
    if x is None:
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def _info(x) -> dict:
    if isinstance(x, dict):
        return x
    try:
        v = json.loads(x) if x else {}
        return v if isinstance(v, dict) else {}
    except (TypeError, ValueError):
        return {}


def _plain(meta: dict | None) -> dict:
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in (meta or {}).items()}
