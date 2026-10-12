"""Book simulators for monitoring (no broker, no orders).

* **model** = the backtest replay: research/longhold/study.py `simulate()` step for step (old weights earn close->open,
  trade to the exact target weights at the open, cost 1c/share + 1 bps on every traded dollar, new weights earn
  open->close, weights drift between rebalances; a target name without an open print keeps its current holding). It is
  fed the same targets the runner computed, so `paper day return - model day return` is the tracking error.
* **dry** = the dry-run shadow book: the plan's whole-share orders filled at the official open (or close for the MOC
  init), no commission, no slippage.

Prices are split/dividend-adjusted closes and opens from the same fetch; returns between them are applied to the
stored marks, so a later re-adjustment of history does not jump the book. A missing bar is a 0 return (as the study).
Educational only - not financial advice.
"""
from __future__ import annotations

import math


def _cost(trade_abs: float, px: float, on: bool) -> float:
    return trade_abs * (0.01 / px + 0.0001) if on and px > 0 else 0.0


class Book:
    def __init__(self, cash: float = 0.0, pos: dict | None = None, last_day: str | None = None, costs: bool = True,
                 cost_paid: float = 0.0, traded: float = 0.0):
        self.cash = float(cash)
        self.pos = {s: dict(v) for s, v in (pos or {}).items()}   # sym -> {"shares", "price"}
        self.last_day = last_day
        self.costs = costs
        self.cost_paid = cost_paid
        self.traded = traded

    # ------------------------------------------------------------ persistence
    def to_json(self) -> dict:
        return {"cash": self.cash, "pos": self.pos, "last_day": self.last_day, "costs": self.costs,
                "cost_paid": self.cost_paid, "traded": self.traded}

    @classmethod
    def from_json(cls, d: dict) -> "Book":
        return cls(d["cash"], d["pos"], d.get("last_day"), d.get("costs", True), d.get("cost_paid", 0.0),
                   d.get("traded", 0.0))

    # ------------------------------------------------------------ valuation
    def value(self, sym: str) -> float:
        p = self.pos.get(sym)
        return p["shares"] * p["price"] if p else 0.0

    def equity(self) -> float:
        return self.cash + sum(self.value(s) for s in self.pos)

    def holdings(self) -> dict[str, float]:
        return {s: self.value(s) for s in self.pos}

    def _move(self, bars: dict, a: str, b: str):
        """Apply each name's return from field a (previous session) to field b."""
        for s, p in self.pos.items():
            x = bars.get(s) or {}
            pa, pb = x.get(a), x.get(b)
            if pa and pb and math.isfinite(pa) and math.isfinite(pb) and pa > 0:
                p["price"] *= pb / pa

    # ------------------------------------------------------------ one session
    def step(self, day: str, bars: dict, targets: dict | None = None, orders: list | None = None,
             at: str = "open") -> float:
        """Advance one session. `bars[sym]` = {"prev_close", "open", "close"} (adjusted). `targets` (model) or
        `orders` (dry: [{symbol, side, qty}]) are executed at the open (or the close when at='close').
        Returns the day's return."""
        e0 = self.equity()
        self.traded = 0.0
        trade_now = targets is not None or orders is not None
        if trade_now and at == "open":
            self._move(bars, "prev_close", "open")
            self._trade(bars, "open", targets, orders)
            self._move(bars, "open", "close")
        else:
            self._move(bars, "prev_close", "close")
            if trade_now:
                self._trade(bars, "close", targets, orders)
        self.last_day = day
        e1 = self.equity()
        return e1 / e0 - 1 if e0 > 0 else 0.0

    def _trade(self, bars: dict, field: str, targets: dict | None, orders: list | None):
        px = {s: (bars.get(s) or {}).get(field) for s in set(self.pos) | set(targets or {}) |
              {o["symbol"] for o in orders or []}}
        ok = {s: p for s, p in px.items() if p and math.isfinite(p) and p > 0}
        traded = cost = 0.0
        if targets is not None:
            E = self.equity()
            for s in sorted(set(self.pos) | set(targets)):
                if s not in ok:
                    continue                                   # no print: keep the holding as it is (study)
                cur = self.value(s)
                tgt = targets.get(s, 0.0) * E
                tr = tgt - cur
                c = _cost(abs(tr), ok[s], self.costs)
                self.cash -= tr + c
                cost += c
                traded += abs(tr)
                if tgt > 0:
                    self.pos[s] = {"shares": tgt / ok[s], "price": ok[s]}
                else:
                    self.pos.pop(s, None)
        for o in orders or []:
            s = o["symbol"]
            if s not in ok:
                continue
            p = self.pos.setdefault(s, {"shares": 0.0, "price": ok[s]})
            p["price"] = ok[s]
            q = min(float(o["qty"]), p["shares"]) if o["side"] == "sell" else float(o["qty"])
            sign = 1 if o["side"] == "buy" else -1
            p["shares"] += sign * q
            self.cash -= sign * q * ok[s]
            c = _cost(q * ok[s], ok[s], self.costs)
            self.cash -= c
            cost += c
            traded += q * ok[s]
            if p["shares"] <= 1e-9:
                self.pos.pop(s)
        self.cost_paid += cost
        self.traded = traded
