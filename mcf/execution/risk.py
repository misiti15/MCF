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
    halted: bool = False


class RiskManager:
    def __init__(self, cfg: dict, equity: float):
        self.a = cfg["account"]
        self.min_price = cfg["costs"]["min_price"]
        self.equity = equity
        self.state = RiskState()

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
        if s.trades_today >= self.a["max_trades_per_day"]:
            return False, "max trades/day"
        if len(s.open_symbols) >= self.a["max_concurrent_positions"]:
            return False, "max concurrent positions"
        if s.open_by_strategy.get(sig.strategy, 0) >= self.a.get("max_positions_per_strategy", 10**9):
            return False, "max positions for this setup"
        if sig.symbol in s.open_symbols:
            return False, "already in symbol"
        if sig.side * (ref_price - sig.stop) <= 0:
            return False, "price already through stop"
        if sig.target is not None and sig.side * (sig.target - ref_price) <= 0:
            return False, "price already through target"
        return True, "ok"
