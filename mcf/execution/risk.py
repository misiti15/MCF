"""Pre-trade risk checks shared by the paper and live runners."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..strategies.base import Signal


@dataclass
class RiskState:
    realized_r: float = 0.0
    trades_today: int = 0
    open_symbols: set[str] = field(default_factory=set)
    open_by_strategy: dict[str, int] = field(default_factory=dict)
    # Per-lot stacking (live.max_lots_per_symbol > 1): symbol -> [(setup, side), ...] for each open or pending lot.
    # A lot is one setup's bracket on a symbol. Empty / max_lots 1 = one position per symbol (pre-2026-10-13 behaviour).
    lots: dict[str, list[tuple[str, int]]] = field(default_factory=dict)
    # symbol -> how many of its lots are residuals (live.lot_cap_ignore_residual_frac): not counted toward the lot cap
    residual: dict[str, int] = field(default_factory=dict)
    halted: bool = False
    # setup -> net realized R today (account.max_setup_daily_loss_r, owner 2026-10-19 evening)
    realized_r_by_strategy: dict[str, float] = field(default_factory=dict)
    # setups that reached the limit today: stopped for the rest of the day, even if a later winner lifts their net R
    # back above it (owner 2026-10-22 LL-LATCH; before, the stop re-armed)
    setup_stopped: set[str] = field(default_factory=set)


def twin_key(name: str | None, groups: dict[str, str] | None = None) -> str:
    """A setup and its full-day copy are twins: same name once a trailing '-FD' is stripped. A setup with a
    `twin_group:` (owner 2026-10-20: overlapping filtered copies of one signal, e.g. two ST2 filters) uses that group
    instead, so two setups of one group never hold the same symbol in one account."""
    n = str(name or "")
    if groups and n in groups:
        return "group:" + groups[n]
    return n[:-3] if n.endswith("-FD") else n


def twin_groups(cfg: dict) -> dict[str, str]:
    """setup -> twin_group for every setup block that sets one (config `strategies:`)."""
    return {str(k): str(v["twin_group"]) for k, v in (cfg.get("strategies") or {}).items()
            if isinstance(v, dict) and v.get("twin_group")}


class RiskManager:
    def __init__(self, cfg: dict, equity: float):
        self.a = cfg["account"]
        self.min_price = cfg["costs"]["min_price"]
        self.equity = equity
        live = cfg.get("live") or {}
        self.max_lots = max(1, int(live.get("max_lots_per_symbol", 1) or 1))
        # owner 2026-10-14: a setup may add a lot on a symbol it already holds when the signal is new (a later bar);
        # the runner guarantees "new" (never the same setup/symbol/bar twice). false = one lot per setup per symbol.
        self.same_setup_reentry = bool(live.get("same_setup_reentry", True))
        # owner 2026-10-16 (option B, paper): a lot whose remaining quantity after a partial target fill is below this
        # fraction of its original quantity no longer counts toward max_lots_per_symbol. 0 = every lot counts.
        self.residual_frac = float(live.get("lot_cap_ignore_residual_frac", 0.0) or 0.0)
        # owner 2026-10-19 evening: no second lot on a symbol already held (or pending) by this setup's twin
        self.block_twin = bool(live.get("block_twin_same_symbol", True))
        self.twin_groups = twin_groups(cfg)      # optional per-setup `twin_group:` (owner 2026-10-20)
        # owner 2026-10-19 evening: a setup takes no new entries today once its net realized R <= -limit (absent = off)
        lim = self.a.get("max_setup_daily_loss_r")
        self.setup_loss_limit = float(lim) if lim else None
        self.state = RiskState()

    def latch_setup_losses(self, by: dict[str, float] | None = None):
        """Stop for the day every setup whose net realized R today is at or below -max_setup_daily_loss_r (`by`: a
        running total to check, e.g. after each restored trade; default the current totals). Latched: never undone."""
        if self.setup_loss_limit is None:
            return
        for k, v in (self.state.realized_r_by_strategy if by is None else by).items():
            if v <= -self.setup_loss_limit:
                self.state.setup_stopped.add(k)

    def open_lots(self) -> int:
        """Slots in use: every lot counts (a symbol held without lot detail counts as one)."""
        s = self.state
        return sum(max(1, len(s.lots.get(sym, ()))) for sym in s.open_symbols)

    def size(self, sig: Signal, ref_price: float) -> int:
        per_share = abs(ref_price - sig.stop)
        if per_share <= 0:
            return 0
        from ..backtest.engine import slot_notional

        risk = self.equity * self.a["risk_per_trade_pct"] / 100
        cap = slot_notional({**self.a, "equity": self.equity})
        return int(min(risk / per_share, cap / ref_price))

    def check(self, sig: Signal, ref_price: float) -> tuple[bool, str]:
        s = self.state
        if s.halted:
            return False, "halted"
        if ref_price < self.min_price:
            return False, "price below minimum"
        if s.realized_r <= -self.a["max_daily_loss_r"]:
            s.halted = True
            return False, "daily loss limit"
        if self.setup_loss_limit is not None:
            self.latch_setup_losses()
            if sig.strategy in s.setup_stopped:
                return False, "setup daily loss limit"
        if s.trades_today >= self.a["max_trades_per_day"]:
            return False, "max trades/day"
        if (len(s.open_symbols) if self.max_lots <= 1 else self.open_lots()) >= self.a["max_concurrent_positions"]:
            return False, "max concurrent positions"
        if s.open_by_strategy.get(sig.strategy, 0) >= self.a.get("max_positions_per_strategy", 10**9):
            return False, "max positions for this setup"
        if sig.symbol in s.open_symbols:
            lots = s.lots.get(sig.symbol) or []
            tk = twin_key(sig.strategy, self.twin_groups)
            if self.block_twin and any(st != sig.strategy and twin_key(st, self.twin_groups) == tk
                                       and (self.max_lots <= 1 or side == sig.side) for st, side in lots):
                return False, "twin held"
            if self.max_lots <= 1:
                return False, "already in symbol"
            lots = s.lots.get(sig.symbol) or []
            if not lots or (not self.same_setup_reentry and any(st == sig.strategy for st, _ in lots)):
                return False, "already in symbol"       # holder unknown, or this setup already holds a lot here
            if any(side != sig.side for _, side in lots):
                return False, "opposite side held"
            if len(lots) - s.residual.get(sig.symbol, 0) >= self.max_lots:
                return False, "lot cap"
        if sig.side * (ref_price - sig.stop) <= 0:
            return False, "price already through stop"
        if sig.target is not None and sig.side * (sig.target - ref_price) <= 0:
            return False, "price already through target"
        return True, "ok"
