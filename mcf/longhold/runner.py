"""Long-hold (S6) runner: plan, submit, reconcile, mark. See research/longhold/DESIGN.md (the spec).

Everything is injected (state dir, market data, broker, clock), so tests run it end to end on a fake broker.
State lives under <state_dir>/longhold/ (the `mcf-data-longhold` branch is checked out as <state_dir>):
  plans/<signal day>.json   targets, orders, data date, code version, config hash, submissions
  marks.csv                 one row per session: equity, cash, day P/L, vs SPY / EW universe / model, drawdown
  fills.csv                 fills vs the official open/close (slippage)
  status.json               last run, alerts, holdings (read by docs/live/index.html, ?account=longhold)
  events.jsonl              every alert / skip / submission, append-only
  HALT                      manual kill switch (any content): no orders at all, holdings kept
Paper account only. Educational only - not financial advice.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yaml

from . import core, signals
from .book import Book
from .core import RiskCaps

ET = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "longhold.yaml"
DISCLAIMER = "Educational only - not financial advice."


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(Path(path).read_text())


def config_hash(path: Path = CONFIG) -> str:
    h = hashlib.sha256(Path(path).read_bytes())
    h.update(Path(signals.__file__).read_bytes())
    h.update(Path(core.__file__).read_bytes())
    return h.hexdigest()[:12]


def code_version() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha[:12]
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                              text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def size_orders(orders: list[core.Order], prices: dict[str, float], held_qty: dict[str, float], cash: float,
                equity: float, buffer: float, targets: dict[str, float]) -> tuple[list[dict], list[str]]:
    """Whole shares: buys floor(notional / price); a name leaving the targets sells its whole position; other sells
    floor(notional / price) capped at the held quantity. Buys are trimmed (largest first, one share at a time) until
    their cost fits cash + sell proceeds - buffer x equity (no margin). Returns (orders, notes)."""
    out, notes = [], []
    for o in orders:
        px = prices.get(o.symbol)
        if not px or not math.isfinite(px) or px <= 0:
            notes.append(f"{o.symbol}: no price, order skipped")
            continue
        if o.side == "sell":
            held = abs(held_qty.get(o.symbol, 0.0))
            qty = held if targets.get(o.symbol, 0.0) == 0 else min(held, math.floor(o.notional / px))
            qty = math.floor(qty) if qty >= 1 else 0
        else:
            qty = math.floor(o.notional / px)
        if qty < 1:
            notes.append(f"{o.symbol}: {o.side} ${o.notional:,.0f} is under one share at {px:.2f}")
            continue
        out.append({"symbol": o.symbol, "side": o.side, "qty": int(qty), "ref_price": round(px, 4),
                    "notional": round(qty * px, 2), "target_notional": o.notional,
                    "client_order_id": o.client_order_id})
    room = cash + sum(x["notional"] for x in out if x["side"] == "sell") - buffer * equity
    buys = [x for x in out if x["side"] == "buy"]
    while buys and sum(x["notional"] for x in buys) > room:
        big = max(buys, key=lambda x: x["notional"])
        big["qty"] -= 1
        big["notional"] = round(big["qty"] * big["ref_price"], 2)
        if big["qty"] < 1:
            out.remove(big); buys.remove(big)
            notes.append(f"{big['symbol']}: buy dropped to fit cash")
    return sorted(out, key=lambda x: (x["side"] != "sell", x["symbol"])), notes


class Runner:
    def __init__(self, state_dir, data, broker=None, calendar=None, now: datetime | None = None, live: bool = False,
                 cfg: dict | None = None, etf: set[str] | None = None, universe: list[str] | None = None):
        self.dir = Path(state_dir) / "longhold"
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "plans").mkdir(exist_ok=True)
        self.data = data
        self.broker = broker
        self.cal = calendar or broker
        self.now = (now or datetime.now(ET)).astimezone(ET)
        self.today = self.now.date()
        self.live = bool(live)
        if self.live and broker is None:
            raise RuntimeError("live mode needs the long-hold broker")
        self.cfg = cfg or load_config()
        self.caps = RiskCaps(**self.cfg.get("caps", {}))
        self.strategy = self.cfg.get("strategy", signals.STRATEGY)
        self._etf = etf
        self._universe = universe
        self.alerts: list[dict] = []

    # ------------------------------------------------------------------ helpers
    @property
    def mode(self) -> str:
        return "paper" if self.live else "dry-run"

    def etf(self) -> set[str]:
        if self._etf is None:
            self._etf = signals.etf_set()
        return self._etf

    def universe(self) -> list[str]:
        if self._universe is None:
            self._universe = signals.universe()
        return self._universe

    def halted(self) -> bool:
        return (self.dir / "HALT").exists()

    def event(self, kind: str, msg: str, level: str = "info", **kw):
        rec = {"ts": self.now.isoformat(timespec="seconds"), "kind": kind, "level": level, "msg": msg, **kw}
        with open(self.dir / "events.jsonl", "a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
        if level in ("warn", "halt", "error"):
            self.alerts.append(rec)
        print(f"[{level}] {kind}: {msg}")

    def trading_days(self, start: date, end: date) -> list[date]:
        days = [d if isinstance(d, date) and not isinstance(d, datetime) else pd.Timestamp(d).date()
                for d in self.cal.calendar(start, end)]
        return sorted(set(days))

    def last_signal_day(self, before: date) -> date | None:
        """The latest weekly rebalance day strictly before `before` (exchange calendar)."""
        days = self.trading_days(before - timedelta(days=21), before + timedelta(days=14))
        for d in reversed([d for d in days if d < before]):
            if core.rebalance_due(days, d, signals.FREQ):
                return d
        return None

    def plan_path(self, signal_day: date) -> Path:
        return self.dir / "plans" / f"{signal_day:%Y-%m-%d}.json"

    def load_plan(self, signal_day: date) -> dict | None:
        p = self.plan_path(signal_day)
        return json.loads(p.read_text()) if p.exists() else None

    def save_plan(self, plan: dict):
        self.plan_path(date.fromisoformat(plan["signal_day"])).write_text(json.dumps(plan, indent=1, default=str))

    def marks(self) -> pd.DataFrame:
        p = self.dir / "marks.csv"
        return pd.read_csv(p) if p.exists() else pd.DataFrame()

    # ------------------------------------------------------------------ data + signal
    def sanity(self, bars: pd.DataFrame, signal_day: date) -> str | None:
        """DESIGN.md 3.2: skip (do not guess) when the last bar is not the signal day, SPY is missing, or > 10 % of
        the previous session's eligible names have no bar on the signal day."""
        if bars is None or bars.empty:
            return "no bars returned"
        C, V = signals.frames(bars)
        C, V = C.loc[:pd.Timestamp(signal_day)], V.loc[:pd.Timestamp(signal_day)]
        if C.empty or C.index[-1].date() != signal_day:
            return f"last bar {C.index[-1].date() if len(C) else None} is not the signal day {signal_day}"
        if "SPY" not in C.columns or not np.isfinite(C["SPY"].iloc[-1]):
            return "SPY has no bar on the signal day"
        if len(C) < 2:
            return "fewer than 2 sessions of bars"
        f = signals.features(C, V, self.etf())
        prev = f["elig"][-2]
        if prev.sum():
            miss = float(np.isnan(f["close"][-1][prev]).mean())
            if miss > self.cfg.get("max_missing_frac", 0.10):
                return f"{miss:.0%} of yesterday's {int(prev.sum())} eligible names have no bar on {signal_day}"
        return None

    def signal(self, signal_day: date) -> tuple[dict | None, str | None, pd.DataFrame]:
        start = signal_day - timedelta(days=int(self.cfg.get("history_days", 600)))
        syms = list(dict.fromkeys(self.universe() + ["SPY"]))
        bars = self.data.bars(syms, start, signal_day, adjustment="all")
        bad = self.sanity(bars, signal_day)
        if bad:
            return None, bad, bars
        sig = signals.compute(bars, signal_day, self.etf())
        if sig["reason"]:
            return None, sig["reason"], bars
        return sig, None, bars

    def latest_prices(self, symbols: list[str], since: date) -> dict[str, float]:
        if not symbols:
            return {}
        b = self.data.bars(symbols, since, self.today, adjustment="raw")
        if b is None or b.empty:
            return {}
        b = b.sort_values("date")
        return {str(s): float(g["close"].iloc[-1]) for s, g in b.groupby("symbol")}

    # ------------------------------------------------------------------ book
    def book(self) -> tuple[float, float, dict[str, dict]]:
        """(equity, cash, positions). Live: the long-hold paper account. Dry run: the shadow book (dry_book.json)."""
        if self.live:
            a = self.broker.account()
            if a.get("trading_blocked"):
                raise RuntimeError("long-hold account is trading-blocked")
            return a["equity"], a["cash"], self.broker.positions()
        d = self.load_book("dry")
        if d is None:
            cap = float(self.cfg.get("dry_capital", 100000))
            return cap, cap, {}
        pos = {s: {"qty": v["shares"], "market_value": v["shares"] * v["price"], "current_price": v["price"]}
               for s, v in d.pos.items()}
        return d.equity(), d.cash, pos

    def load_book(self, name: str) -> Book | None:
        p = self.dir / f"{name}_book.json"
        return Book.from_json(json.loads(p.read_text())) if p.exists() else None

    def save_book(self, name: str, b: Book):
        (self.dir / f"{name}_book.json").write_text(json.dumps(b.to_json(), indent=1))

    # ------------------------------------------------------------------ plan
    def build_plan(self, signal_day: date, exec_day: date, tif: str, kind: str) -> dict:
        plan = {"strategy": self.strategy, "kind": kind, "signal_day": str(signal_day), "exec_day": str(exec_day),
                "time_in_force": tif, "mode": self.mode, "created": self.now.isoformat(timespec="seconds"),
                "code_version": code_version(), "config_hash": config_hash(), "status": "planned",
                "targets": {}, "orders": [], "notes": [], "submissions": {}, "disclaimer": DISCLAIMER}
        reason = None
        if self.halted():
            reason = "manual halt (HALT file on the state branch)"
        if not reason:
            curve = self.marks()["equity"].tolist() if "equity" in self.marks() else []
            reason = core.kill_switch(curve, self.caps)
        if reason:
            plan.update(status="halted", skip_reason=reason)
            self.event("kill_switch", f"{signal_day}: {reason}; no orders, holdings kept", "halt")
            return plan
        sig, bad, _ = self.signal(signal_day)
        if bad:
            plan.update(status="skipped_data", skip_reason=bad)
            self.event("data_sanity", f"{signal_day}: {bad}; rebalance skipped", "warn")
            return plan
        plan["data_date"] = str(signal_day)
        plan["targets"] = sig["targets"]
        plan["eligible_count"] = len(sig["eligible"])
        plan["eligible"] = sig["eligible"]
        plan["ranked"] = sig["ranked"]
        errs = core.check_targets(sig["targets"], self.caps)
        if errs:
            plan.update(status="skipped_risk", skip_reason="; ".join(errs))
            self.event("risk", f"{signal_day}: {errs}; no orders", "warn")
            return plan
        equity, cash, pos = self.book()
        holdings = {s: p["market_value"] for s, p in pos.items()}
        plan.update(equity=round(equity, 2), cash=round(cash, 2), holdings_before=holdings)
        raw = core.diff_orders(sig["targets"], holdings, equity, self.strategy, signal_day,
                               band=float(self.cfg.get("band", 0.0)), min_notional=float(self.cfg.get("min_notional", 25)))
        need = sorted({o.symbol for o in raw})
        px = self.latest_prices(need, signal_day)
        for s in need:                                   # held names: the broker's last price if no bar
            if s not in px and pos.get(s, {}).get("current_price"):
                px[s] = pos[s]["current_price"]
        buffer = float(self.cfg.get("init_cash_buffer" if kind == "init" else "cash_buffer", 0.0025))
        orders, notes = size_orders(raw, px, {s: p["qty"] for s, p in pos.items()}, cash, equity, buffer,
                                    sig["targets"])
        if self.live:
            for o in [o for o in orders if o["side"] == "buy"]:
                try:
                    ok = self.broker.tradable(o["symbol"])
                except Exception as e:                   # unknown asset state: do not buy
                    ok = False
                    notes.append(f"{o['symbol']}: asset lookup failed ({type(e).__name__})")
                if not ok:
                    orders.remove(o)
                    notes.append(f"{o['symbol']}: not tradable, not bought (flagged)")
                    self.event("not_tradable", f"{o['symbol']} not tradable; buy skipped", "warn")
        if len(orders) > self.caps.max_daily_orders:
            plan.update(status="skipped_risk", skip_reason=f"{len(orders)} orders > {self.caps.max_daily_orders}")
            self.event("risk", plan["skip_reason"], "warn")
            return plan
        plan["orders"] = orders
        plan["notes"] = notes
        plan["prices"] = px
        plan["invested_after"] = round(sum(o["notional"] if o["side"] == "buy" else -o["notional"] for o in orders)
                                       + sum(holdings.values()), 2)
        return plan

    # ------------------------------------------------------------------ submit
    def submit_plan(self, plan: dict) -> dict:
        """Submit the plan's orders that are not at the broker yet (same deterministic ids). A duplicate-id reject
        means the order is already placed. Sells go first. Re-checks the HALT file right before submitting."""
        if plan.get("status") not in ("planned", "submitted", "partial"):
            return plan
        if not self.live:
            plan["status_detail"] = "dry run: no orders placed"
            return plan
        if self.halted():
            self.event("kill_switch", "HALT file present at submit time: nothing submitted", "halt")
            plan["status"] = "halted"
            plan["skip_reason"] = "manual halt at submit time"
            return plan
        sd = date.fromisoformat(plan["signal_day"])
        prefix = f"{core.PREFIX}{self.strategy}-{sd:%Y%m%d}-"
        after = datetime.combine(sd, time(0), ET)
        existing = {o["client_order_id"]: o for o in self.broker.orders(prefix, after)}
        subs = plan.setdefault("submissions", {})
        n_new = n_bad = 0
        for o in plan["orders"]:
            cid = o["client_order_id"]
            if cid in existing:
                subs[cid] = {"status": existing[cid]["status"], "note": "already at broker"}
                continue
            try:
                r = self.broker.submit(o["symbol"], o["qty"], o["side"], plan["time_in_force"], cid)
                subs[cid] = {"status": r.get("status", "submitted"), "at": self.now.isoformat(timespec="seconds")}
                n_new += 1
            except Exception as e:
                msg = str(e)
                low = msg.lower()
                if "duplicate" in low or ("client_order_id" in low and "unique" in low):
                    subs[cid] = {"status": "already placed", "note": "duplicate client_order_id"}
                else:
                    subs[cid] = {"status": "rejected", "error": msg[:300]}
                    n_bad += 1
                    self.event("order_reject", f"{cid}: {msg[:200]}", "warn")
        plan["status"] = "partial" if n_bad else "submitted"
        if n_new and not (self.dir / "LIVE").exists():
            (self.dir / "LIVE").write_text(f"first paper submission {self.now.isoformat(timespec='seconds')}\n")
        self.event("submit", f"{plan['signal_day']} ({plan['kind']}, {plan['time_in_force']}): {n_new} new, "
                   f"{len(plan['orders']) - n_new - n_bad} already placed, {n_bad} rejected")
        return plan

    # ------------------------------------------------------------------ commands
    def init(self, stage: str = "all") -> dict:
        """Initial portfolio (owner 2026-10-12): targets from the last weekly signal, bought today as whole-share
        market-on-close orders. Only on an empty book; re-runs submit only what is missing."""
        if self.today not in self.trading_days(self.today - timedelta(days=7), self.today + timedelta(days=7)):
            raise RuntimeError(f"{self.today} is not a trading day")
        cutoff = time.fromisoformat(self.cfg.get("moc_cutoff_et", "15:45"))
        sd = self.last_signal_day(self.today)
        if sd is None:
            raise RuntimeError("no weekly signal day found in the calendar")
        plan = self.load_plan(sd)
        if plan is not None and plan.get("mode") != self.mode and not plan.get("submissions"):
            self.event("plan", f"plan {sd} was written in {plan.get('mode')} mode; rebuilt for {self.mode}")
            plan = None                                  # a dry plan is sized on the dry capital: never reuse it live
        if plan is None:
            if stage == "submit":
                raise RuntimeError(f"no plan for {sd}: run the plan stage first")
            _, _, pos = self.book()
            if pos:
                raise RuntimeError(f"book already holds {len(pos)} positions: init is only for an empty account")
            plan = self.build_plan(sd, self.today, "cls", "init")
            self.save_plan(plan)
            self.event("plan", f"init plan for signal {sd}: {plan['status']}, {len(plan['orders'])} orders "
                       f"({plan.get('skip_reason') or 'ok'})")
        elif plan.get("kind") != "init":
            raise RuntimeError(f"plan {sd} exists and is not an init plan")
        if stage in ("submit", "all"):
            if self.now.time() >= cutoff:
                self.event("missed", f"init after the MOC cutoff ({cutoff} ET): nothing submitted", "warn")
            else:
                plan = self.submit_plan(plan)
                self.save_plan(plan)
        self.write_status(plan=plan)
        return plan


    # ------------------------------------------------------------------ weekly schedule
    def phase(self) -> str:
        t = self.now.time()
        if t < time(9, 28):
            return "morning"
        if t < time(16, 30):
            return "recon"
        return "evening"

    def next_session(self, d: date, days: list[date]) -> date:
        later = [x for x in days if x > d]
        if not later:
            raise ValueError("calendar must extend past the signal day")
        return later[0]

    def plans(self) -> list[dict]:
        return [json.loads(p.read_text()) for p in sorted((self.dir / "plans").glob("*.json"))]

    def run(self, stage: str = "all", phase: str | None = None) -> dict:
        """One scheduled run (idempotent). morning: submit the pending OPG plan before 09:28. recon: reconcile fills
        vs the official open, retry an unfilled OPG order once as a DAY order (-r). evening: reconcile, mark, and on
        the last session of the week build the plan; OPG orders are submitted from 19:00 ET (or by the morning run).
        stage 'plan' never submits; stage 'submit' never builds (the workflow commits the plan in between)."""
        phase = phase or self.phase()
        days = self.trading_days(self.today - timedelta(days=21), self.today + timedelta(days=14))
        out = {"phase": phase, "today": str(self.today), "trading_day": self.today in days}
        if self.today not in days:
            self.write_status()
            return out
        opg_from, opg_to = (time.fromisoformat(x) for x in self.cfg.get("opg_window_et", ["19:00", "09:28"]))
        if stage in ("submit", "all") and phase in ("morning", "recon"):
            self.topup_init()
        if phase == "morning" and stage in ("submit", "all"):
            sd = self.last_signal_day(self.today)
            plan = self.load_plan(sd) if sd else None
            if plan and plan.get("exec_day") == str(self.today) and plan.get("time_in_force") == "opg":
                if self.now.time() < opg_to:
                    plan = self.submit_plan(plan)
                    self.save_plan(plan)
                out["plan"] = plan.get("status")
        elif phase == "recon":
            self.reconcile(retry=stage in ("submit", "all"))
        elif phase == "evening":
            self.reconcile(retry=False)
            if stage in ("submit", "all"):
                self.topup_init()
            if stage in ("plan", "all"):
                out["mark"] = self.mark(days)
            if core.rebalance_due(days, self.today, signals.FREQ):
                plan = self.load_plan(self.today)
                if plan is None and stage in ("plan", "all"):
                    plan = self.build_plan(self.today, self.next_session(self.today, days), "opg", "weekly")
                    self.save_plan(plan)
                    self.event("plan", f"weekly plan {self.today}: {plan['status']}, {len(plan['orders'])} orders "
                               f"({plan.get('skip_reason') or 'ok'})")
                if plan and stage in ("submit", "all") and self.now.time() >= opg_from:
                    plan = self.submit_plan(plan)
                    self.save_plan(plan)
                out["plan"] = plan.get("status") if plan else None
        self.write_status()
        return out

    def topup_init(self):
        """Complete an initial (MOC) portfolio whose closing-auction orders ended short (2026-10-12: Alpaca paper
        filled 9 of 20 MOC orders fully, 4 partly, 7 not at all). Per order, at most two top-ups of the missing
        shares: first an OPG order for the next open (submitted 19:00-09:28 ET, id + '-t1'), then, if still short,
        a DAY market order during the session (09:31-15:30 ET, id + '-t2'). Deterministic ids keep it idempotent;
        HALT and the drawdown freeze stop it like any other order. Paper only."""
        if not self.live or self.halted() or self._frozen():
            return
        t = self.now.time()
        for plan in self.plans():
            if plan.get("kind") != "init" or plan.get("time_in_force") != "cls" or \
                    plan.get("status") not in ("submitted", "partial"):
                continue
            ed = date.fromisoformat(plan["exec_day"])
            if self.today < ed or (self.today == ed and t < time(16, 5)):
                continue
            sd = date.fromisoformat(plan["signal_day"])
            got = {o["client_order_id"]: o for o in self.broker.orders(f"{core.PREFIX}{self.strategy}-{sd:%Y%m%d}-",
                                                                       datetime.combine(sd, time(0), ET))}
            tops = plan.setdefault("topups", {})
            n_new = 0
            for o in plan["orders"]:
                if o["side"] != "buy":
                    continue
                cid = o["client_order_id"]
                ids = [cid] + tops.get(cid, [])
                if any(i not in got or got[i].get("status") not in self.TERMINAL for i in ids):
                    continue                                   # still working, or not visible yet
                short = int(o["qty"] - sum(float(got[i].get("filled_qty") or 0) for i in ids))
                n = len(ids) - 1
                if short < 1 or n >= 2:
                    continue
                if n == 0 and (t >= time(19, 0) or t < time(9, 28)):
                    tif = "opg"
                elif n == 1 and time(9, 31) <= t < time(15, 30):
                    tif = "day"
                else:
                    continue
                rid = topup_id(cid, n + 1)
                try:
                    self.broker.submit(o["symbol"], short, "buy", tif, rid)
                except Exception as e:
                    low = str(e).lower()
                    if not ("duplicate" in low or ("client_order_id" in low and "unique" in low)):
                        self.event("order_reject", f"top-up {rid}: {str(e)[:200]}", "warn")
                        continue
                tops.setdefault(cid, []).append(rid)
                plan["reconciled"] = None                      # reconcile again to record the top-up fills
                n_new += 1
                self.event("topup", f"{cid}: {short} missing shares as {tif.upper()} {rid}", "info")
            if n_new:
                self.save_plan(plan)

    def _frozen(self) -> bool:
        a = [x for x in self.health(self._status_for_health()) if x.get("kind") == "drawdown" and x.get("level") == "halt"]
        return bool(a)

    def _status_for_health(self) -> dict:
        p = self.dir / "status.json"
        return json.loads(p.read_text()) if p.exists() else {}

    # ------------------------------------------------------------------ reconciliation
    TERMINAL = {"filled", "canceled", "cancelled", "expired", "rejected", "done_for_day", "replaced", "stopped"}

    def reconcile(self, retry: bool = True):
        """Fills vs the official open (OPG / DAY retry) or official close (MOC) -> fills.csv, slippage in bps
        (positive = paid more than the auction print). An OPG order that ended unfilled is retried once as a DAY
        market order with the same id + '-r' during the exec session. Paper only; dry runs have nothing to reconcile."""
        if not self.live:
            return
        for plan in self.plans():
            if plan.get("status") not in ("submitted", "partial") or plan.get("reconciled"):
                continue
            ed = date.fromisoformat(plan["exec_day"])
            if self.today < ed or (self.today == ed and self.now.time() < time(9, 31)):
                continue
            sd = date.fromisoformat(plan["signal_day"])
            prefix = f"{core.PREFIX}{self.strategy}-{sd:%Y%m%d}-"
            got = {o["client_order_id"]: o for o in self.broker.orders(prefix, datetime.combine(sd, time(0), ET))}
            ref_field = "close" if plan.get("time_in_force") == "cls" else "open"
            refs = {}
            if not (ref_field == "close" and self.today == ed and self.now.time() < time(16, 5)):
                b = self.data.bars(sorted({o["symbol"] for o in plan["orders"]}), ed, ed, adjustment="raw")
                if b is not None and len(b):
                    refs = {str(r.symbol): float(getattr(r, ref_field)) for r in b.itertuples()}
            retries = plan.setdefault("retries", {})
            fills, done = [], True
            for o in plan["orders"]:
                cid = o["client_order_id"]
                tops = (plan.get("topups") or {}).get(cid, [])
                for oid, tif, ref_name in ((cid, plan.get("time_in_force"), ref_field), (retries.get(cid), "day", "open"),
                                           *((x, "topup", "open") for x in tops)):
                    if not oid:
                        continue
                    x = got.get(oid)
                    st = (x or {}).get("status")
                    if x is None or st not in self.TERMINAL:
                        done = False
                        continue
                    fq = float(x.get("filled_qty") or 0)
                    fp = x.get("filled_avg_price")
                    if fq > 0 and fp:
                        ref = refs.get(o["symbol"]) if ref_name == ref_field else None
                        if ref_name == "open" and ref_field != "open":
                            ref = None
                        sign = 1 if o["side"] == "buy" else -1
                        fills.append({"signal_day": plan["signal_day"], "exec_day": plan["exec_day"],
                                      "client_order_id": oid, "symbol": o["symbol"], "side": o["side"],
                                      "tif": tif, "qty": o["qty"], "filled_qty": fq, "fill_price": fp,
                                      "ref": ref_field if oid == cid else ("topup" if tif == "topup" else "day-retry"),
                                      "ref_price": ref,
                                      "slippage_bps": None if not ref else round(sign * (fp / ref - 1) * 1e4, 2),
                                      "model_cost_bps": None if not ref else round((0.01 / ref + 0.0001) * 1e4, 2),
                                      "notional": round(fq * fp, 2)})
                        if oid == cid and ref is None:
                            done = False                     # official print not available yet
                    if oid == cid and fq < float(o["qty"]) and st != "filled":
                        rid = retries.get(cid)
                        if (rid is None and retry and plan.get("time_in_force") == "opg" and self.today == ed
                                and time(9, 31) <= self.now.time() < time(15, 30) and not self.halted()):
                            rid = retry_id(cid)
                            try:
                                self.broker.submit(o["symbol"], int(o["qty"] - fq), o["side"], "day", rid)
                                retries[cid] = rid
                                done = False
                                self.event("retry", f"{cid} ended {st} ({fq:g}/{o['qty']} filled): retried as {rid}",
                                           "warn")
                            except Exception as e:
                                self.event("order_reject", f"retry {rid}: {str(e)[:200]}", "warn")
                        elif rid is None and not tops:
                            self.event("unfilled", f"{cid} ended {st}, {fq:g}/{o['qty']} filled, not retried", "warn")
            self._write_fills(fills)
            if done:
                plan["reconciled"] = self.now.isoformat(timespec="seconds")
                sl = [f["slippage_bps"] for f in fills if f["slippage_bps"] is not None]
                plan["slippage_bps_mean"] = round(float(np.mean(sl)), 2) if sl else None
                self.event("reconciled", f"{plan['signal_day']}: {len(fills)} fills, mean slippage "
                           f"{plan['slippage_bps_mean']} bps vs official {ref_field}")
            self.save_plan(plan)

    def _write_fills(self, rows: list[dict]):
        if not rows:
            return
        p = self.dir / "fills.csv"
        old = pd.read_csv(p) if p.exists() else pd.DataFrame()
        new = pd.DataFrame(rows)
        if len(old):
            new = pd.concat([old[~old["client_order_id"].isin(new["client_order_id"])], new], ignore_index=True)
        new.to_csv(p, index=False)

    # ------------------------------------------------------------------ marks
    def _session_bars(self, symbols: list[str], start: date, end: date, days: list[date]) -> dict:
        """{day: {sym: {prev_close, open, close}}} for sessions in (start, end], adjusted prices."""
        b = self.data.bars(sorted(set(symbols)), start, end, adjustment="all")
        if b is None or b.empty:
            return {}
        b = b.copy()
        b["symbol"] = b["symbol"].astype(str)
        b["date"] = pd.to_datetime(b["date"]).dt.normalize()
        idx = pd.DatetimeIndex([pd.Timestamp(d) for d in days if start <= d <= end])
        C = b.pivot(index="date", columns="symbol", values="close").reindex(idx)
        O = b.pivot(index="date", columns="symbol", values="open").reindex(idx)
        P = C.shift(1)
        out = {}
        for i, d in enumerate(idx[1:], start=1):
            if C.iloc[i].notna().sum() == 0:
                continue
            out[d.date()] = {s: {"prev_close": P.iat[i, j], "open": O.iat[i, j], "close": C.iat[i, j]}
                             for j, s in enumerate(C.columns)}
        return out

    def advance_books(self, days: list[date]) -> dict:
        """Bring the backtest-replay model (and the dry-run shadow book) up to today. Returns per-day model returns,
        SPY and EW-universe returns for the sessions processed."""
        plans = {p["exec_day"]: p for p in self.plans() if p.get("targets") and p.get("status") not in
                 ("skipped_data", "skipped_risk", "halted")}
        model, dry = self.load_book("model"), self.load_book("dry")
        starts = [date.fromisoformat(b.last_day) for b in (model, dry) if b is not None and b.last_day]
        first_exec = min((date.fromisoformat(d) for d in plans), default=None)
        past = [d for d in days if d <= self.today]
        prev_today = [d for d in past if d < self.today][-1]
        if starts:
            start = min(starts)
        elif first_exec is not None and first_exec <= self.today:
            start = [d for d in past if d < first_exec][-1]
        else:
            start = prev_today                                # benchmarks only
        start = min(start, prev_today)
        ew = []
        for p in sorted(self.plans(), key=lambda p: p["signal_day"]):
            ew = p.get("eligible") or ew
        syms = {"SPY"} | set(ew)
        for b in (model, dry):
            syms |= set(b.pos) if b else set()
        for p in plans.values():
            syms |= set(p["targets"]) | {o["symbol"] for o in p.get("orders", [])}
        bars = self._session_bars(sorted(syms), start, self.today, days)
        res = {}
        for d in [d for d in past if d > start]:
            bd = bars.get(d)
            spy = (bd or {}).get("SPY") or {}
            if not bd or not (spy.get("close") == spy.get("close")) or spy.get("close") is None:
                break                                         # session data not complete yet: stop here
            plan = plans.get(str(d))
            at = "close" if plan and plan.get("time_in_force") == "cls" else "open"
            if model is None and plan is not None:
                prev = [x for x in past if x < d][-1]
                model = Book(cash=float(plan.get("equity") or self.cfg.get("dry_capital", 100000)), last_day=str(prev),
                             costs=bool(self.cfg.get("model_costs", True)))
            if not self.live and dry is None and plan is not None:
                prev = [x for x in past if x < d][-1]
                dry = Book(cash=float(self.cfg.get("dry_capital", 100000)), last_day=str(prev), costs=False)
            r = {"spy_ret": _ret(spy)}
            ews = [_ret(bd.get(s) or {}) for s in ew]
            ews = [x for x in ews if x is not None]
            r["ew_ret"] = float(np.mean(ews)) if ews else None
            if model is not None and (model.last_day or "") < str(d):
                r["model_ret"] = model.step(str(d), bd, targets=plan["targets"] if plan else None, at=at)
                r["model_equity"] = model.equity()
                r["model_turnover"] = model.traded / 2 / max(model.equity(), 1e-9)
                r["model_cost"] = model.cost_paid
            if dry is not None and (dry.last_day or "") < str(d):
                dry.step(str(d), bd, orders=plan.get("orders") if plan else None, at=at)
                r["dry_turnover"] = dry.traded / 2 / max(dry.equity(), 1e-9)
            res[d] = r
        if model is not None:
            self.save_book("model", model)
        if dry is not None:
            self.save_book("dry", dry)
        return res

    def mark(self, days: list[date] | None = None) -> dict | None:
        """Daily mark: equity, cash, day P/L, vs SPY, vs the EW universe, vs the backtest replay (tracking error),
        drawdown from the high-water mark, turnover, alerts. Paper account when live, the shadow book in a dry run."""
        days = days or self.trading_days(self.today - timedelta(days=21), self.today + timedelta(days=14))
        if self.today not in days:
            return None
        bench = self.advance_books(days)
        equity, cash, pos = self.book()
        m = self.marks()
        if len(m):
            m = m[m["date"].astype(str) != str(self.today)]
        prev_eq = float(m["equity"].iloc[-1]) if len(m) else None
        if self.live:
            prev_eq = self.broker.account().get("last_equity", prev_eq)
        b = bench.get(self.today, {})
        if not b:
            self.event("data", f"no complete bars for {self.today} yet: benchmarks and the replay not updated", "warn")
        day_ret = None if not prev_eq else equity / prev_eq - 1
        model_ret = b.get("model_ret")
        turnover = b.get("dry_turnover")
        if self.live:
            fp = self.dir / "fills.csv"
            if fp.exists():
                f = pd.read_csv(fp)
                f = f[f["exec_day"].astype(str) == str(self.today)]
                turnover = float(f["notional"].sum()) / 2 / equity if len(f) and equity else 0.0
        row = {"date": str(self.today), "mode": self.mode, "equity": round(equity, 2), "cash": round(cash, 2),
               "invested": round(sum(p["market_value"] for p in pos.values()), 2), "positions": len(pos),
               "day_pl": None if prev_eq is None else round(equity - prev_eq, 2),
               "day_ret": _r(day_ret), "spy_ret": _r(b.get("spy_ret")), "ew_ret": _r(b.get("ew_ret")),
               "model_equity": None if b.get("model_equity") is None else round(b["model_equity"], 2),
               "model_ret": _r(model_ret),
               "te": _r(day_ret - model_ret) if day_ret is not None and model_ret is not None else None,
               "turnover": _r(turnover), "model_turnover": _r(b.get("model_turnover"))}
        m = pd.concat([m, pd.DataFrame([row])], ignore_index=True)
        hwm = float(pd.to_numeric(m["equity"]).max())
        row["hwm"] = round(hwm, 2)
        row["drawdown"] = round(equity / hwm - 1, 6) if hwm > 0 else 0.0
        te = pd.to_numeric(m.get("te"), errors="coerce").tail(20)
        row["te_20d"] = _r(float(te.sum())) if te.notna().any() else None
        for k in ("hwm", "drawdown", "te_20d"):
            m.loc[m.index[-1], k] = row[k]
        m.to_csv(self.dir / "marks.csv", index=False)
        self.write_status(mark=row, positions=pos)
        return row

    # ------------------------------------------------------------------ health + status
    def health(self, st: dict) -> list[dict]:
        """Standing alert conditions, re-derived on every run from the state (thresholds: config/longhold.yaml)."""
        a = self.cfg.get("alerts", {})
        out = []

        def add(kind, level, msg):
            out.append({"kind": kind, "level": level, "msg": msg})

        if self.halted():
            add("kill_switch", "halt", "HALT file present on the state branch: no orders until it is removed")
        mk = st.get("mark") or {}
        dd = mk.get("drawdown")
        if dd is not None and dd <= -self.caps.kill_drawdown:
            add("drawdown", "halt", f"drawdown {dd:.1%} beyond -{self.caps.kill_drawdown:.0%}: no new orders")
        elif dd is not None and dd <= -a.get("dd_warn", 0.15):
            add("drawdown", "warn", f"drawdown {dd:.1%} beyond -{a.get('dd_warn', 0.15):.0%}")
        if mk.get("te") is not None and abs(mk["te"]) > a.get("te_day", 0.01):
            add("tracking", "warn", f"tracking difference today {mk['te']:+.2%} vs the backtest replay "
                f"(limit {a.get('te_day', 0.01):.0%})")
        if mk.get("te_20d") is not None and abs(mk["te_20d"]) > a.get("te_20d", 0.03):
            add("tracking", "warn", f"20-session tracking difference {mk['te_20d']:+.2%} (limit {a.get('te_20d', 0.03):.0%})")
        plans = self.plans()
        if plans:
            p = plans[-1]
            if p.get("status") in ("skipped_data", "skipped_risk", "halted"):
                add("rebalance_skipped", "warn", f"rebalance {p['signal_day']} {p['status']}: {p.get('skip_reason')}")
            rej = [k for k, v in (p.get("submissions") or {}).items() if v.get("status") == "rejected"]
            if rej:
                add("order_reject", "warn", f"{len(rej)} order(s) rejected for {p['signal_day']}: {', '.join(rej[:5])}")
            sl = p.get("slippage_bps_mean")
            if sl is not None and abs(sl) > a.get("slippage_bps", 25):
                add("slippage", "warn", f"mean slippage {sl:+.1f} bps vs the auction print on {p['exec_day']}")
        try:
            missed = self.missed_rebalance()
        except Exception:
            missed = None
        if missed:
            add("missed_rebalance", "warn", missed)
        return out

    def missed_rebalance(self) -> str | None:
        days = self.trading_days(self.today - timedelta(days=21), self.today + timedelta(days=14))
        sd = self.last_signal_day(self.today + timedelta(days=1))
        if sd is None:
            return None
        if sd == self.today and self.now.time() < time(19, 30):
            sd = self.last_signal_day(self.today)                 # today's plan is not due yet
            if sd is None:
                return None
        plans = self.plans()
        if not plans or min(p["signal_day"] for p in plans) > str(sd):
            return None                                           # book started after that signal
        p = self.load_plan(sd)
        if p is None:
            return f"no plan for the {sd} rebalance"
        ed = date.fromisoformat(p["exec_day"])
        if (self.live and p.get("status") == "planned" and p.get("orders")
                and (self.today > ed or (self.today == ed and self.now.time() >= time(9, 28)))):
            return f"rebalance {sd}: orders were not submitted before the {ed} open"
        del days
        return None

    def next_rebalance(self) -> str | None:
        days = self.trading_days(self.today, self.today + timedelta(days=14))
        for d in days[:-1]:
            if d >= self.today and core.rebalance_due(days, d, signals.FREQ):
                return str(d)
        return None

    def entries(self) -> dict[str, str]:
        """Entry (exec) day per held name, from the plans."""
        e: dict[str, str] = {}
        for p in self.plans():
            if p.get("status") in ("skipped_data", "skipped_risk", "halted") or not p.get("orders"):
                continue
            if self.live and not p.get("submissions"):
                continue
            for o in p["orders"]:
                if o["side"] == "buy" and o["symbol"] not in e:
                    e[o["symbol"]] = p["exec_day"]
                if o["side"] == "sell" and p["targets"].get(o["symbol"], 0) == 0:
                    e.pop(o["symbol"], None)
        return e

    def snapshot(self) -> dict:
        """Intraday read-only snapshot for the dashboard (owner 2026-10-12: hourly is enough). Reads the account and
        positions (GET only), writes status.json -> intraday and the holdings table. No orders, no marks.csv row."""
        equity, cash, pos = self.book()
        prev = self.broker.account().get("last_equity") if self.live else None
        snap = {"asof": self.now.isoformat(timespec="seconds"), "equity": round(equity, 2), "cash": round(cash, 2),
                "last_equity": prev, "day_pl": None if not prev else round(equity - prev, 2),
                "day_ret": None if not prev else _r(equity / prev - 1), "positions": len(pos),
                "invested": round(sum(v.get("market_value") or 0 for v in pos.values()), 2)}
        st = self.write_status(positions=pos, weight_equity=equity)
        st["intraday"] = snap
        (self.dir / "status.json").write_text(json.dumps(st, indent=1, default=str))
        return snap

    def write_status(self, plan: dict | None = None, mark: dict | None = None, positions: dict | None = None,
                     weight_equity: float | None = None):
        p = self.dir / "status.json"
        st = json.loads(p.read_text()) if p.exists() else {}
        st.update({"strategy": self.strategy, "mode": self.mode,
                   "label": "paper" if self.live else "dry-run (no orders)", "disclaimer": DISCLAIMER,
                   "last_run": self.now.isoformat(timespec="seconds"), "halt_file": self.halted()})
        plans = self.plans()
        plan = plan or (plans[-1] if plans else None)
        if plan is not None:
            st["last_plan"] = {k: plan.get(k) for k in ("signal_day", "exec_day", "kind", "status", "skip_reason",
                                                          "time_in_force", "equity", "slippage_bps_mean",
                                                          "reconciled")}
            st["last_plan"]["orders"] = len(plan.get("orders", []))
            st["last_plan"]["targets"] = sorted(plan.get("targets", {}))
        if mark is not None:
            st["mark"] = mark
        if positions is not None:
            ent = self.entries()
            eq = weight_equity or (mark or {}).get("equity") or 0
            st["positions"] = {s: {"qty": v.get("qty"), "market_value": round(v.get("market_value") or 0, 2),
                                   "weight": round((v.get("market_value") or 0) / eq, 4) if eq else None,
                                   "avg_entry_price": v.get("avg_entry_price"), "price": v.get("current_price"),
                                   "unrealized_pl": v.get("unrealized_pl"), "entry_day": ent.get(s)}
                               for s, v in sorted(positions.items())}
        m = self.marks()
        if len(m):
            eq = pd.to_numeric(m["equity"])
            st["since_start"] = {"start": str(m["date"].iloc[0]), "sessions": int(len(m)),
                                 "return": _r(float(eq.iloc[-1] / eq.iloc[0] - 1)),
                                 "max_drawdown": _r(float((eq / eq.cummax() - 1).min()))}
            for col, name in (("spy_ret", "spy"), ("ew_ret", "ew_universe"), ("model_ret", "backtest_replay")):
                if col in m:
                    r = pd.to_numeric(m[col], errors="coerce").fillna(0.0)
                    st["since_start"][name] = _r(float((1 + r.iloc[1:]).prod() - 1)) if len(r) > 1 else 0.0
        st["next_rebalance"] = self._safe(self.next_rebalance)
        st["alerts_run"] = self.alerts
        st["alerts"] = self.health(st) + [x for x in self.alerts if x["kind"] in ("order_reject", "data_sanity",
                                                                                 "unfilled", "retry", "data")]
        p.write_text(json.dumps(st, indent=1, default=str))
        return st

    def _safe(self, fn):
        try:
            return fn()
        except Exception:
            return None

    # ------------------------------------------------------------------ weekly report
    def report(self) -> Path:
        """Weekly report (Saturday): equity vs SPY, the EW universe and the backtest replay; turnover; costs (model
        cost vs measured auction slippage); holdings; next rebalance; skipped rebalances and kill-switch events."""
        from .report import weekly_html

        st = self.write_status()
        out = self.dir / "reports" / f"weekly-{self.today}.html"
        out.parent.mkdir(exist_ok=True)
        fills = pd.read_csv(self.dir / "fills.csv") if (self.dir / "fills.csv").exists() else pd.DataFrame()
        ev = []
        if (self.dir / "events.jsonl").exists():
            ev = [json.loads(x) for x in (self.dir / "events.jsonl").read_text().splitlines() if x.strip()]
        out.write_text(weekly_html(self.marks(), fills, self.plans(), st, ev, self.today))
        st["weekly"] = {"date": str(self.today), "path": f"longhold/reports/{out.name}"}
        (self.dir / "status.json").write_text(json.dumps(st, indent=1, default=str))
        return out


def _ret(x: dict) -> float | None:
    a, b = x.get("prev_close"), x.get("close")
    if a is None or b is None or not (a == a and b == b) or a <= 0:
        return None
    return float(b / a - 1)


def _r(x) -> float | None:
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(float(x), 6)


def topup_id(cid: str, k: int) -> str:
    suf = f"-t{k}"
    if len(cid) + len(suf) <= 48:
        return cid + suf
    return cid[:36] + "-" + hashlib.sha1(cid.encode()).hexdigest()[:8] + suf


def retry_id(cid: str) -> str:
    if len(cid) + 2 <= 48:
        return cid + "-r"
    return cid[:37] + "-" + hashlib.sha1(cid.encode()).hexdigest()[:8] + "-r"
