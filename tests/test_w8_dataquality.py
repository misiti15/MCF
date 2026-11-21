"""W8-DQ (crunch 2026-11-18): data and accounting quality fixes. Report-only except the reconcile fill export, which
feeds the runner's open marks. Educational only - not financial advice."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import pandas as pd
import pytest

from mcf import costs
from mcf.execution.reconcile import reconcile_day
from mcf.report import c3score as C
from mcf.report.live_status import _since_alpaca


class _J:
    def __init__(self, rows):
        self.rows = pd.DataFrame(rows)
        self.closed = []

    def open_orders(self, run_id):
        return self.rows

    def update_order_status(self, oid, st):
        self.closed.append(oid)


class _B:
    def __init__(self, orders):
        self.orders = orders

    def closed_orders_today(self, after):
        return self.orders


def _row(oid, sym, ref):
    return {"broker_order_id": oid, "symbol": sym, "strategy": "S", "side": -1, "stop": ref + 1.0, "target": ref - 1.0,
            "entry_ref": ref, "meta": "", "created_at": "2026-11-17T15:00:00+00:00"}


def test_reconcile_exports_entry_fills_of_open_and_closed_lots():
    t = datetime(2026, 11, 17, 15, 0, tzinfo=timezone.utc)
    working = NS(id="l1", filled_avg_price=None, filled_at=None, order_type="stop", status="new")
    open_lot = NS(id="p1", symbol="AA", filled_avg_price=37.63, filled_qty="93", filled_at=t, legs=[working], side="sell")
    done = NS(id="l2", filled_avg_price=9.0, filled_at=t + timedelta(minutes=5), order_type="limit", status="filled",
              filled_qty="10")
    closed_lot = NS(id="p2", symbol="BB", filled_avg_price=10.02, filled_qty="10", filled_at=t, legs=[done], side="sell")
    tr = reconcile_day(_B([open_lot, closed_lot]), _J([_row("p1", "AA", 37.70), _row("p2", "BB", 10.0)]), 1,
                       "2026-11-17")
    assert tr.attrs["fills"] == {"p1": 37.63, "p2": 10.02}      # the fill, not the 37.70 / 10.00 signal reference
    assert len(tr) == 1 and tr.iloc[0]["symbol"] == "BB"        # booking unchanged: only the closed lot is a trade


def test_whatif_corrected_reads_journal_rows():
    # journal what-if rows: shares 0, pnl 0, pnl_adj null, R in r_multiple, reason in meta
    w = pd.DataFrame([
        {"symbol": "A", "strategy": "S", "date": "d1", "entry": 10.0, "stop": 9.0, "shares": 0, "pnl": 0.0,
         "pnl_adj": None, "r_multiple": 1.0, "meta": "status=skipped;why=max positions for this setup", "entry_time": 1},
        {"symbol": "A", "strategy": "S", "date": "d1", "entry": 10.0, "stop": 9.0, "shares": 0, "pnl": 0.0,
         "pnl_adj": None, "r_multiple": 1.0, "meta": "status=skipped;why=max positions for this setup", "entry_time": 2},
        {"symbol": "B", "strategy": "S", "date": "d1", "entry": 10.0, "stop": 9.0, "shares": 0, "pnl": 0.0,
         "pnl_adj": None, "r_multiple": 2.0, "meta": "status=skipped;why=not shortable/ETB", "entry_time": 1}])
    r = C.whatif_corrected(w)
    assert r["raw_n"] == 3 and r["raw_r"] == 4.0
    assert r["dropped_unfillable"] == 1 and r["dropped_dupes"] == 1 and r["n"] == 1
    assert r["r"] == pytest.approx(1.0 - 0.05)


def test_daily_review_verdict_uses_corrected_whatif():
    from mcf.report import daily_review as DR

    tr = pd.DataFrame([{"symbol": "Z", "strategy": "S", "side": 1, "date": "2026-11-18", "entry": 10.0, "stop": 9.0,
                        "shares": 10, "pnl": 5.0, "pnl_adj": 4.0, "r_multiple": 0.5, "exit_reason": "target",
                        "entry_time": pd.Timestamp("2026-11-18 10:00", tz="America/New_York"), "meta": ""}])
    rows = []
    for k in range(12):        # one name re-signalled 12 times while blocked: +1R each raw, -1R once corrected
        rows.append({"symbol": "A", "strategy": "S", "side": 1, "date": "2026-11-18", "entry": 10.0, "stop": 9.0,
                     "shares": 0, "pnl": 0.0, "pnl_adj": None, "r_multiple": -1.0 if k == 0 else 1.0,
                     "entry_time": pd.Timestamp("2026-11-18 10:00", tz="America/New_York") + pd.Timedelta(minutes=k),
                     "meta": "status=skipped;why=max positions for this setup"})
    for k in range(15):
        rows.append({"symbol": f"E{k}", "strategy": "S", "side": -1, "date": "2026-11-18", "entry": 10.0, "stop": 11.0,
                     "shares": 0, "pnl": 0.0, "pnl_adj": None, "r_multiple": 1.0,
                     "entry_time": pd.Timestamp("2026-11-18 10:00", tz="America/New_York"),
                     "meta": "status=skipped;why=not shortable/ETB"})
    wi = pd.DataFrame(rows)

    class J:
        def trades(self, run_id=None, kind=None):
            return tr.copy() if run_id == 1 else wi.copy()

        def signals(self, run_id, day=None):
            return pd.DataFrame(columns=["status", "reason"])

        def get_or_create_run(self, kind, label):
            return 2

    rv = DR.build_review(J(), 1, "2026-11-18")
    d = {x["reason"]: x for x in rv["decisions"]}
    mp = d["max positions for this setup"]
    assert mp["whatif_raw_total_r"] == 10.0 and mp["whatif_n"] == 1 and mp["whatif_total_r"] == pytest.approx(-1.05)
    assert mp["verdict"] == "rule saved R today"
    assert d["not shortable/ETB"]["verdict"] == "not tradable (unfillable skip)"
    assert not any("would have made" in f for f in rv["findings"])


def test_since_start_trading_pnl_excludes_labelled_broker_glitch():
    by_day = [{"date": "2026-11-04", "alpaca_day_pl": -146.0}, {"date": "2026-11-05", "alpaca_day_pl": -11824.02},
              {"date": "2026-11-06", "alpaca_day_pl": -1238.60}]
    s = _since_alpaca(by_day, "primary")
    assert s["alpaca_pnl"] == pytest.approx(-13208.62)
    assert s["alpaca_pnl_trading"] == pytest.approx(-146.0 - 367.71 - 1238.60 + 183.92)
    assert [a["date"] for a in s["alpaca_adjustments"]] == ["2026-11-05", "2026-11-06"]
    assert "alpaca_pnl_trading" not in _since_alpaca(by_day, "testing")


def test_cost_r_lr8_restates_only_pre_model_rows():
    cfg = {"costs": {"stop_slippage_per_share": 0.02, "live_model": {
        "effective_from": "2026-11-12", "stop_min_per_share": 0.02, "stop_bps": 4.0, "entry_bps": 1.0,
        "market_exit_min_per_share": 0.01, "market_exit_bps": 1.0, "target_at_limit": True, "fees": {}}}}
    df = pd.DataFrame([
        {"date": "2026-11-10", "side": 1, "entry": 100.0, "stop": 99.0, "target": 102.0, "shares": 10, "exit": 99.0,
         "exit_reason": "stop", "pnl": -10.0, "pnl_adj": -10.2, "r_multiple": -1.0, "meta": ""},
        {"date": "2026-11-13", "side": 1, "entry": 100.0, "stop": 99.0, "target": 102.0, "shares": 10, "exit": 99.0,
         "exit_reason": "stop", "pnl": -10.0, "pnl_adj": -10.7, "r_multiple": -1.0, "meta": ""}])
    booked = costs.cost_r(df)
    r8 = costs.cost_r_lr8(df, cfg)
    assert booked.tolist() == pytest.approx([-1.02, -1.07])
    # pre-model row re-costed: stop max(0.02, 4bp x 99 = 0.0396) x 10 + entry 1bp x 100 x 10 = 0.396 + 0.1
    assert r8.iloc[0] == pytest.approx((-10.0 - 0.396 - 0.1) / 10.0)
    assert r8.iloc[1] == pytest.approx(-1.07)                  # on/after the model date: the booked value


def test_cost_r_lr8_raises_on_missing_columns_for_pre_model_rows():
    # QA 11-21 C1: live_trades dropped side/exit/target/meta and pre-11-12 rows silently kept the old cost
    cfg = {"costs": {"stop_slippage_per_share": 0.02, "live_model": {
        "effective_from": "2026-11-12", "stop_min_per_share": 0.02, "stop_bps": 4.0, "entry_bps": 1.0,
        "market_exit_min_per_share": 0.01, "market_exit_bps": 1.0, "target_at_limit": True, "fees": {}}}}
    df = pd.DataFrame([{"date": "2026-11-10", "entry": 100.0, "stop": 99.0, "shares": 10, "pnl": -10.0,
                        "pnl_adj": -10.2, "r_multiple": -1.0}])
    with pytest.raises(KeyError):
        costs.cost_r_lr8(df, cfg)
    post = df.assign(date="2026-11-13")            # post-model rows need no re-costing: no error
    assert costs.cost_r_lr8(post, cfg).iloc[0] == pytest.approx(-1.02)


def test_live_trades_reads_cost_columns():
    import inspect

    from mcf.report import footrace
    src = inspect.getsource(footrace.live_trades)
    for col in ("side", "target", "exit,", "exit_reason", "meta"):
        assert col in src
