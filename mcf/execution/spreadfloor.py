"""SPREADFLOOR shadow logger (research/spreadfloor_1127, housekeeping, LOG ONLY).

Wave-3 lead (research/stopfloor_1127/REPORT.md, lead 1): live trades whose stop distance is under 6-8 quoted spreads
lose more (-0.31 vs -0.18 R) and a 6/8-spread skip beat same-share random skips live, but there is no spread history
to backtest it. This module records the evidence going forward: at each real entry the runner tags the journaled
signal and order meta with `spreadfloor_shadow` = the decision-time quoted spread, the stop distance in spreads / bp /
cents, and whether a 6- and an 8-spread floor WOULD have skipped it.

Never: an order, a size, an entry, an exit or a skip. Nothing in the runner reads these fields. Any error is swallowed
and printed (the runner wraps the call too). Kill switch: live.spreadfloor_log: false (default on; not in config/).
Educational only - not financial advice."""

from __future__ import annotations

import math

KEY = "spreadfloor_shadow"
FLOORS = (6, 8)          # spreads; the two floors of stopfloor_1127 lead 1


def fields(bid, ask, ref, stop, floors=FLOORS) -> dict:
    """Pure: the logged fields for one entry. Missing / one-sided quote -> {"quote": False} (no floor verdict)."""
    try:
        bid, ask, ref, stop = float(bid), float(ask), float(ref), float(stop)
    except (TypeError, ValueError):
        return {"quote": False}
    if not all(math.isfinite(x) for x in (bid, ask, ref, stop)) or bid <= 0 or ask <= 0 or ask < bid or ref <= 0:
        return {"quote": False}
    spread = ask - bid
    mid = (bid + ask) / 2
    risk = abs(ref - stop)
    out = {"quote": True, "spread_c": round(spread * 100, 2), "spread_bps": round(spread / mid * 1e4, 2),
           "stop_c": round(risk * 100, 2), "stop_bps": round(risk / ref * 1e4, 1)}
    if spread <= 0:                                  # locked quote: infinitely many spreads, no floor can bite
        out["stop_spreads"] = None
        out.update({f"would_skip_{f}": False for f in floors})
        return out
    ns = risk / spread
    out["stop_spreads"] = round(ns, 2)
    out.update({f"would_skip_{f}": bool(ns < f) for f in floors})
    return out
