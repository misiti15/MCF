from datetime import date

import pytest

from research.longhold import runner_core as rc


def test_rebalance_due_month_and_week():
    days = [date(2026, 9, 28), date(2026, 9, 29), date(2026, 9, 30), date(2026, 10, 1), date(2026, 10, 2),
            date(2026, 10, 5)]
    assert rc.rebalance_due(days, date(2026, 9, 30), "M")
    assert not rc.rebalance_due(days, date(2026, 9, 29), "M")
    assert rc.rebalance_due(days, date(2026, 10, 2), "W")          # Friday
    assert not rc.rebalance_due(days, date(2026, 10, 3), "W")      # Saturday: not a trading day
    # holiday: Thursday is the last trading day of the week when Friday is closed
    hol = [date(2026, 4, 1), date(2026, 4, 2), date(2026, 4, 6)]
    assert rc.rebalance_due(hol, date(2026, 4, 2), "W")


def test_diff_orders_band_sells_first_and_ids_are_deterministic():
    d = date(2026, 9, 30)
    tg = {"AAA": 0.5, "BBB": 0.5}
    hold = {"AAA": 5200.0, "CCC": 3000.0}                      # AAA inside the 20 % band, CCC leaves, BBB enters
    o = rc.diff_orders(tg, hold, 10000.0, "mom", d)
    assert [(x.symbol, x.side) for x in o] == [("CCC", "sell"), ("BBB", "buy")]
    assert o[1].notional == 5000.0
    assert o == rc.diff_orders(tg, hold, 10000.0, "mom", d)     # same inputs, same ids: a rerun is idempotent
    assert all(x.client_order_id.startswith("mcl-") and len(x.client_order_id) <= 48 for x in o)
    o2 = rc.diff_orders(tg, {"AAA": 3000.0, "BBB": 5000.0}, 10000.0, "mom", d)
    assert [(x.symbol, x.side, x.notional) for x in o2] == [("AAA", "buy", 2000.0)]


def test_diff_rejects_shorts_and_leverage():
    with pytest.raises(ValueError):
        rc.diff_orders({"A": -0.1}, {}, 1e4, "x", date(2026, 1, 30))
    with pytest.raises(ValueError):
        rc.diff_orders({"A": 0.7, "B": 0.6}, {}, 1e4, "x", date(2026, 1, 30))


def test_long_ids_are_truncated_with_hash():
    cid = rc.client_order_id("a-very-long-strategy-name-for-testing", date(2026, 1, 30), "BRK.B", "buy")
    assert len(cid) <= 48 and cid.startswith("mcl-")


def test_risk_caps_and_kill_switch():
    caps = rc.RiskCaps()
    assert rc.check_targets({f"S{i}": 0.05 for i in range(20)}, caps) == []
    assert rc.check_targets({"A": 0.5}, caps)
    assert rc.kill_switch([100, 120, 89], caps) is not None     # -25.8 % from the high-water mark
    assert rc.kill_switch([100, 120, 100], caps) is None
    assert rc.kill_switch([100], caps, halt_file_present=True) == "manual halt"
