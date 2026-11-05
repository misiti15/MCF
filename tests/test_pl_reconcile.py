"""P/L reconcile (owner 2026-11-05): one dollar truth = Alpaca everywhere; the modelled stop slippage only inside R.
Educational only - not financial advice."""
import json
import sqlite3
from pathlib import Path

from mcf.report import daily_post as dp
from mcf.report import live_status as ls
from mcf.report import reconcile_pl as rp

HTML = (Path(__file__).resolve().parents[1] / "docs" / "live" / "index.html").read_text()


def _fill(sym, side, qty, px):
    return {"activity_type": "FILL", "symbol": sym, "side": side, "qty": str(qty), "price": str(px)}


def test_fill_check_matches_symbols_and_lists_fees():
    acts = [_fill("AAA", "buy", 10, 10.0), _fill("AAA", "sell", 10, 11.0),          # +10
            _fill("BBB", "sell_short", 5, 20.0), _fill("BBB", "buy", 5, 21.0),       # -5
            _fill("CCC", "buy", 3, 5.0),                                              # still held: not P/L
            {"activity_type": "FEE", "net_amount": "-1.25", "description": "REG fee ... on 2026-11-05"}]
    fc = rp.fill_check(acts, {"AAA": 10.0, "BBB": -2.0})
    assert fc["fills"] == 5 and fc["not_flat"] == ["CCC"] and fc["fees"] == -1.25
    assert fc["unmatched"] == [{"symbol": "BBB", "alpaca": -5.0, "journal": -2.0, "diff": -3.0}]


def test_fees_posted_next_day_belong_to_their_session(monkeypatch):
    monkeypatch.setattr(rp, "_keys", lambda a: ("k", "s"))
    pages = {"2026-11-04": [_fill("AAA", "buy", 1, 1.0),
                            {"id": "f0", "activity_type": "FEE", "date": "2026-11-03", "net_amount": "-3", "description": "REG fee on 2026-11-03"}],
             "2026-11-05": [{"id": "f1", "activity_type": "FEE", "date": "2026-11-04", "net_amount": "-4.34", "description": "REG fee for proceed on 2026-11-04 by X"}]}
    monkeypatch.setattr(rp, "_activities", lambda a, d, fills=True: [x for x in pages.get(d, []) if fills or x["activity_type"] != "FILL"])
    acts = rp.alpaca_activities("primary", "2026-11-04")
    assert [a.get("id") for a in acts if a["activity_type"] == "FEE"] == ["f1"] and sum(a["activity_type"] == "FILL" for a in acts) == 1


def test_reconcile_flags_gap_over_tolerance(monkeypatch):
    monkeypatch.setattr(rp, "status_now", lambda a, sd=None: {"session_date": "2026-11-05", "today": {"pnl": -363.32}})
    monkeypatch.setattr(rp, "alpaca_closes", lambda a: {"2026-11-04": 94876.57, "2026-11-05": 94513.25})
    monkeypatch.setattr(rp, "alpaca_activities", lambda a, d: [])
    monkeypatch.setattr(rp, "journal_day", lambda a, d, sd=None: {"pnl": -363.32, "pnl_adj": -419.0, "trades": 61, "by_symbol": {}})
    r = rp.reconcile("2026-11-05", "primary")
    assert r["ok"] and r["alpaca_day_pl"] == -363.32 and r["journal_diff"] == 0 and r["residual"] == 0
    monkeypatch.setattr(rp, "journal_day", lambda a, d, sd=None: {"pnl": -340.0, "pnl_adj": -400.0, "trades": 61, "by_symbol": {}})
    r = rp.reconcile("2026-11-05", "primary")
    assert not r["ok"] and r["journal_diff"] == 23.32 and "journal +23.32 vs Alpaca" in r["flags"][0]
    assert rp.tolerance(-1000) == 20 and rp.tolerance(-50) == 10
    line = rp.fyi([r])
    assert line.startswith("P/L reconcile 2026-11-05: 1 of 1 accounts off") and "primary Alpaca -363.32" in line


def test_snapshot_closes_measure_first_session_from_paper_start():
    snaps = {"2026-11-05": {"account": {"equity": 100154.24}, "history": [{"date": "2026-11-05"}]}}
    rows = rp.day_rows(rp.snapshot_closes(snaps), "status_snapshot")
    assert rows["2026-11-05"]["alpaca_day_pl"] == 154.24


def test_status_equity_history_today_and_prior_close(monkeypatch):
    monkeypatch.setattr(rp, "equity_history", lambda a: {"2026-11-03": {"equity_close": 95022.33, "alpaca_day_pl": 142.76, "source": "alpaca"},
                                                         "2026-11-04": {"equity_close": 94880.96, "alpaca_day_pl": -141.37, "source": "status_snapshot"}})
    eqh = ls.equity_history({}, "primary", "2026-11-05", {"equity": 94513.25, "last_equity": 94876.57, "day_pl": -363.32})
    assert eqh["2026-11-05"] == {"equity_close": 94513.25, "alpaca_day_pl": -363.32, "source": "alpaca"}
    assert eqh["2026-11-04"]["equity_close"] == 94876.57 and eqh["2026-11-04"]["alpaca_day_pl"] == -145.76   # fees in
    hist = [dict(date="2026-11-04", pnl=-141.37, alpaca_day_pl=-145.76), dict(date="2026-11-05", pnl=-363.32)]
    assert ls._since_alpaca(hist) == {"alpaca_pnl": -509.08, "alpaca_days": 1, "sessions": 2}


def _db(rows):
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE runs (id INTEGER, kind TEXT)")
    db.execute("CREATE TABLE trades (run_id INT, strategy TEXT, entry REAL, stop REAL, shares REAL, pnl REAL, pnl_adj REAL, "
               "r_multiple REAL, date TEXT, exit_time TEXT)")
    db.execute("INSERT INTO runs VALUES (1, 'paper')")
    db.executemany("INSERT INTO trades VALUES (1,?,?,?,?,?,?,?,'2026-11-05','x')", rows)
    return db


def test_post_dollars_are_alpaca_and_r_keeps_the_allowance(monkeypatch):
    st = {"session_date": "2026-11-05", "account": {"equity": 94513.25},
          "today": {"pnl": -363.32, "pnl_adj": -419.0, "alpaca_day_pl": -367.71, "trades": 61},
          "history": [dict(date="2026-11-04", pnl=-141.37, pnl_adj=-208.63, trades=54, alpaca_day_pl=-145.76),
                      dict(date="2026-11-05", pnl=-363.32, pnl_adj=-419.0, trades=61)]}
    monkeypatch.setattr(dp, "_show", lambda br, path: st if br == "mcf-data" else None)
    monkeypatch.setattr(rp, "equity_history", lambda a: {})
    a = dp.accounts("2026-11-05", since="2026-11-04")[0]
    assert a["today"] == -367.71 and a["source"] == "alpaca"
    assert round(a["since"], 2) == round(-145.76 - 363.32, 2)          # 11-05 has no stored equity in history: journal pnl
    monkeypatch.setattr(dp, "_journal", lambda br: _db([("S1", 10.0, 9.0, 100, 50.0, 48.0, 0.5)]) if br == "mcf-data" else None)
    jd = dp.journal_day("2026-11-05", ["primary"])
    assert jd["S1"]["pnl"] == 50.0 and abs(jd["S1"]["r"] - 0.48) < 1e-9   # $ = fills, R = pnl_adj / risk


def test_dashboard_labels_the_dollar_truth():
    assert "P/L today (Alpaca)" in HTML and "Adj. (incl. modelled stop slippage)" in HTML
    assert "var alp = d => d == null ? null : (d.alpaca_day_pl ?? d.pnl);" in HTML
    assert "all.alpaca_pnl ?? all.pnl" in HTML


def test_backfill_file_shape():
    doc = json.loads(rp.EQUITY_HISTORY.read_text())
    assert "Educational only" in doc["disclaimer"]
    for acct, rows in doc["accounts"].items():
        assert acct in rp.BRANCH
        for d, r in rows.items():
            assert len(d) == 10 and r["source"] in ("alpaca", "status_snapshot") and "equity_close" in r
