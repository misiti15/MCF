"""Moved to `mcf/longhold/core.py` (2026-10-12) when the long-hold runner was built; re-exported here so the
original tests and notes keep working. Educational only - not financial advice."""
from mcf.longhold.core import (PREFIX, Order, RiskCaps, check_targets, client_order_id, diff_orders,  # noqa: F401
                               kill_switch, rebalance_due)
