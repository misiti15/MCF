"""Crypto cost model (Alpaca spot). Costs decide everything for intraday crypto, so they are modelled in full.

Per side, as a fraction of price:
  fee        Alpaca crypto spot, volume tier 1 (0-100k USD 30-day volume): maker 0.15%, taker 0.25%
             (docs.alpaca.markets/docs/crypto-fees, via WebSearch 2026-11-26; tiers took effect 2023-03-13;
             tier 2 0.12/0.22, tier 3 0.10/0.20). Research default = taker both sides (market entries and
             market / stop exits); `maker_entry=True` models a resting limit entry at maker fee and no spread
             crossing, which is only valid if the limit actually fills (no adverse-selection credit given).
  half-spread median quoted spread / 2 for the pair and year, sampled from Alpaca historical quotes
             (research/crypto_r1/spreads.json, built by research/crypto_r1/sample_spreads.py on FIT/CHECK
             windows only). Years before quote history exist use the pair's earliest sampled year; pairs with no
             sample use DEFAULT_SPREAD.
  slippage   SLIP_BPS per side on top of the half-spread, STOP_EXTRA_BPS more on stop exits (stops are market
             orders into a thin book), and THIN_MULT x slippage when the entry minute had no real print.

R accounting: R = (exit - entry) * side / (risk per unit) - round-trip cost / (risk per unit), i.e. costs are
charged in R using the trade's own stop distance, like the equity engine. Tight intraday stops therefore pay
several R in costs; the model makes that visible instead of hiding it.

Educational only — not financial advice.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

FEE_MAKER = 0.0015
FEE_TAKER = 0.0025
SLIP_BPS = 2.0
STOP_EXTRA_BPS = 5.0
THIN_MULT = 3.0
DEFAULT_SPREAD = 0.0030          # 30 bps quoted spread when a pair has no sample (conservative)
SPREADS_FILE = Path(__file__).resolve().parents[2] / "research" / "crypto_r1" / "spreads.json"


def load_spreads(path: Path = SPREADS_FILE) -> dict[str, dict[str, float]]:
    """{"BTC": {"2023": 0.0011, ...}, ...} median relative quoted spread (ask-bid)/mid per pair and year."""
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("median_rel_spread", {})


@dataclass
class CostModel:
    fee_entry: float = FEE_TAKER
    fee_exit: float = FEE_TAKER
    slip_bps: float = SLIP_BPS
    stop_extra_bps: float = STOP_EXTRA_BPS
    thin_mult: float = THIN_MULT
    maker_entry: bool = False
    spreads: dict = field(default_factory=load_spreads)

    @classmethod
    def maker(cls, **kw) -> "CostModel":
        return cls(fee_entry=FEE_MAKER, maker_entry=True, **kw)

    def spread(self, pair: str, year: int) -> float:
        tab = self.spreads.get(pair)
        if not tab:
            return DEFAULT_SPREAD
        ys = sorted(int(y) for y in tab)
        y = min(max(year, ys[0]), ys[-1])
        if str(y) not in tab:                      # missing middle year -> nearest earlier sampled year
            y = max(v for v in ys if v <= y)
        return float(tab[str(y)])

    def side_cost(self, pair: str, year: int, *, entry: bool, stop_exit: bool = False, thin: bool = False) -> float:
        half = self.spread(pair, year) / 2
        slip = self.slip_bps / 1e4 * (self.thin_mult if thin else 1.0)
        if entry:
            if self.maker_entry:
                return self.fee_entry                 # resting limit: no spread crossed, no slippage
            return self.fee_entry + half + slip
        extra = self.stop_extra_bps / 1e4 if stop_exit else 0.0
        return self.fee_exit + half + slip + extra

    def round_trip(self, pair: str, year: int, *, stop_exit: bool = False, thin: bool = False) -> float:
        """Round-trip cost as a fraction of entry price."""
        return (self.side_cost(pair, year, entry=True, thin=thin)
                + self.side_cost(pair, year, entry=False, stop_exit=stop_exit, thin=thin))

    def describe(self) -> str:
        return (f"fees {self.fee_entry*1e4:.0f}/{self.fee_exit*1e4:.0f} bps entry/exit"
                f"{' (maker entry)' if self.maker_entry else ' (taker)'}, half-spread per pair-year, "
                f"slippage {self.slip_bps:g} bps/side (+{self.stop_extra_bps:g} on stops, x{self.thin_mult:g} thin)")
