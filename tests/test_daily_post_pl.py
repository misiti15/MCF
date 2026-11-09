"""PL1109: the post's account dollars = Alpaca equity close-to-close + the explicit broker-glitch table.
Educational only — not financial advice."""
import mcf.report.daily_post as dp
import mcf.report.reconcile_pl as rp


def _status(session, equity, last_equity, history, phase="closed"):
    return {"session_date": session, "phase": phase,
            "account": {"equity": equity, "last_equity": last_equity, "day_pl": round(equity - last_equity, 2)},
            "today": {"trades": 5, "pnl": 1.0, "alpaca_day_pl": round(equity - last_equity, 2)}, "history": history}


def _patch(monkeypatch, statuses, closes):
    monkeypatch.setattr(dp, "_show", lambda br, path: statuses.get(br) if path == "status.json" else None)
    monkeypatch.setattr(dp, "equity_closes", lambda br, st=None: dict(closes.get(br, {}), **(
        {st["session_date"]: st["account"]["equity"]} if st and st.get("phase") == "closed" and st["session_date"] not in closes.get(br, {}) else {})))
    monkeypatch.setattr(rp, "equity_history", lambda acct: {})


def test_today_is_alpaca_close_to_close_not_runner_day_pl(monkeypatch):
    # Testing 1 11-09: runner day_pl (equity - last_equity) -122.83; Alpaca close-to-close vs the 11-06 close -133.30
    h = [{"date": "2026-11-06", "trades": 92, "pnl": 16.36, "alpaca_day_pl": -40.79},
         {"date": "2026-11-09", "trades": 65, "pnl": 0.41, "alpaca_day_pl": -122.83}]
    g = [{"date": "2026-11-06", "trades": 623, "pnl": 536.28, "alpaca_day_pl": 514.66},
         {"date": "2026-11-09", "trades": 512, "pnl": -528.13, "alpaca_day_pl": -528.13}]
    st = {"mcf-data-testing": _status("2026-11-09", 95491.39, 95614.22, h),
          "mcf-data-graveyard": _status("2026-11-09", 92555.89, 93084.02, g)}
    _patch(monkeypatch, st, {"mcf-data-testing": {"2026-11-06": 95624.69}, "mcf-data-graveyard": {"2026-11-06": 93105.64}})
    a = {x["k"]: x for x in dp.accounts("2026-11-09", since="2026-11-06")}
    assert a["testing"]["today"] == -133.30 and a["testing"]["source"] == "alpaca_close"
    assert a["graveyard"]["today"] == -549.75
    assert a["testing"]["trades"] == 5                      # trades still from today's status
    assert a["testing"]["since"] == round(-40.79 - 133.30, 2)   # first day has no prior close: keeps its Alpaca day P/L


def test_close_to_close_only_when_both_closes_known():
    rows = [{"date": "2026-11-04", "pnl": 1.0}, {"date": "2026-11-05", "pnl": 2.0}, {"date": "2026-11-06", "pnl": 3.0}]
    out = dp.close_to_close(rows, {"2026-11-05": 100.0, "2026-11-06": 90.5})
    assert [r["pnl"] for r in out] == [1.0, 2.0, -9.5]
    assert out[2]["pnl_source"] == "alpaca_close" and out[2]["pnl_day_pl"] == 3.0


def test_mtum_glitch_excluded_from_primary_since_and_last5(monkeypatch):
    h = [{"date": "2026-11-04", "trades": 40, "pnl": -140.0, "alpaca_day_pl": -145.76, "avg_r": 0.0},
         {"date": "2026-11-05", "trades": 30, "pnl": -363.32, "alpaca_day_pl": -11824.02, "avg_r": -0.1},
         {"date": "2026-11-06", "trades": 52, "pnl": -1057.07, "alpaca_day_pl": -1242.21, "avg_r": -0.4},
         {"date": "2026-11-09", "trades": 36, "pnl": -172.26, "alpaca_day_pl": -172.26, "avg_r": -0.4}]
    _patch(monkeypatch, {"mcf-data": _status("2026-11-09", 81638.08, 81810.34, h)}, {"mcf-data": {}})
    p = next(x for x in dp.accounts("2026-11-09", since="2026-11-04") if x["k"] == "primary")
    by = {x["date"]: x["pnl"] for x in p["history"]}
    assert by["2026-11-05"] == -367.71                       # trading-only, bogus split booking out
    assert by["2026-11-06"] == round(-1242.21 + 183.92, 2)   # phantom marks out
    assert p["since"] == round(-145.76 - 367.71 + (-1242.21 + 183.92) + (81638.08 - 81810.34), 2)
    assert {x["date"] for x in p["adjusted"]} == {"2026-11-05", "2026-11-06"}
    html = dp._last5([p], "2026-11-09")
    assert "11,824" not in html and "367.71" in html
    assert "Excluded: Primary 11-05: MTUM" in dp._adj_note([p])


def test_adjustment_table_is_explicit_and_glitch_only():
    assert {(a, d) for a, d, *_ in dp.PL_ADJUSTMENTS} == {("primary", "2026-11-05"), ("primary", "2026-11-06")}
    assert all(k in ("set", "add") and "MTUM" in label for _, _, k, _, label in dp.PL_ADJUSTMENTS)
    # other accounts / days untouched
    assert dp._adjust("testing", {"date": "2026-11-05", "pnl": -1.0}) == {"date": "2026-11-05", "pnl": -1.0}
