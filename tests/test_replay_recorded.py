"""Replay recorded live inputs (research/bdi/night1102/replay): journaled quotes replace the synthetic quote at their
symbol + minute, the live borrow answers override the flags, the store universe file widens the universe.
Educational only - not financial advice."""
import json
import sqlite3

import pandas as pd
import pytest

from mcf.replay import harness, store
from mcf.replay.broker import NS, SimClock, SimDataClient, SimMarket

from test_replay import DAY, NY, _cfg, _session


def _mkt():
    bars, _ = _session(("AAA", "SPY"))
    return SimMarket(pd.Timestamp(DAY).date(), bars), bars


def test_recorded_quote_wins_at_its_minute_only():
    mkt, bars = _mkt()
    clock = SimClock(pd.Timestamp(f"{DAY} 10:00:03", tz=NY))       # minute k = 30
    q = SimDataClient(clock, mkt, 2.0, None, recorded={"AAA": {31: (40.00, 40.20, 4.0)}})
    got = q.get_stock_latest_quote(NS(symbol_or_symbols=["AAA"]))["AAA"]
    assert (got.bid_price, got.ask_price) == (40.00, 40.20)              # k+1 is within the +-1 minute tolerance
    assert (clock.now - pd.Timestamp(got.timestamp).tz_convert(NY)).total_seconds() == pytest.approx(4.0)
    assert q._bps("AAA", 30) == pytest.approx(0.2 / 40.1 * 1e4)
    clock.now = pd.Timestamp(f"{DAY} 11:00:03", tz=NY)                   # no recording -> the model (2 bps)
    got = q.get_stock_latest_quote(NS(symbol_or_symbols=["AAA"]))["AAA"]
    assert (got.ask_price - got.bid_price) / ((got.ask_price + got.bid_price) / 2) * 1e4 < 3.0
    assert q.used == {"recorded": 1, "model": 1}


def _journal(path, rows):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE signals (id INTEGER PRIMARY KEY, run_id INT, day TEXT, ts TEXT, symbol TEXT, strategy TEXT, "
                "side INT, status TEXT, reason TEXT, info TEXT)")
    for r in rows:
        con.execute("INSERT INTO signals (run_id, day, ts, symbol, strategy, side, status, reason, info) VALUES "
                    "(?,?,?,?,?,?,?,?,?)", r)
    con.commit()
    con.close()


def test_recorded_inputs_quotes_and_own_borrow_first(tmp_path):
    d = "2026-11-02"
    q = json.dumps({"bid": 10.0, "ask": 10.1, "spread_bps": 99.5, "quote_age_s": 0.4})
    _journal(tmp_path / "p.db", [(1, d, f"{d}T09:50:10-05:00", "AAA", "S1", 1, "submitted", "ok", q),
                                 (1, d, f"{d}T10:05:10-05:00", "BBB", "S1", -1, "skipped", "not shortable/ETB", "{}"),
                                 (2, d, f"{d}T10:06:10-05:00", "CCC", "S1", -1, "skipped", "not shortable/ETB", "{}")])
    _journal(tmp_path / "t.db", [(1, d, f"{d}T10:07:10-05:00", "BBB", "S2", -1, "submitted", "ok", q),
                                 (1, d, f"{d}T10:08:10-05:00", "DDD", "S2", -1, "submitted", "ok", q)])
    rec = store.recorded_inputs(d, "primary", journals={"primary": tmp_path / "p.db", "testing": tmp_path / "t.db"})
    assert rec["quotes"]["AAA"] == {20: (10.0, 10.1, 0.4)}
    assert rec["quotes"]["DDD"] == {38: (10.0, 10.1, 0.4)}
    assert rec["borrow"] == {"BBB": False, "DDD": True}               # own answer wins; run_id 2 (what-if) ignored


def test_store_universe_file(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", tmp_path)
    assert store.symbols("2026-11-02") == store.symbols()
    (tmp_path / "universe").mkdir()
    (tmp_path / "universe" / "2026-11-02.txt").write_text("AAA\nZZZZ\n")
    assert store.symbols("2026-11-02") == ["AAA", "ZZZZ"]
    assert store.symbols("2026-10-30") == store.symbols()


def test_recorded_wide_quotes_skip_entries_end_to_end(tmp_path):
    bars, priors = _session()
    cfg = _cfg(tmp_path, "long")
    base = harness.run_session(cfg, DAY, bars, priors, check=0, log=lambda m: None)
    wide = {s: {k: (float(b.close.iloc[max(0, k - 1)]) * 0.99, float(b.close.iloc[max(0, k - 1)]) * 1.01, 1.0)
                for k in range(390)} for s, b in bars.items() if s == "AAA"}
    rec = harness.run_session(cfg, DAY, bars, priors, check=0, recorded={"quotes": wide, "borrow": {}},
                              log=lambda m: None)
    a0 = base["signals"][(base["signals"].symbol == "AAA") & (base["signals"].status == "submitted")]
    a1 = rec["signals"][rec["signals"].symbol == "AAA"]
    assert len(a0) > 0
    assert (a1.status != "submitted").all() and a1.reason.str.startswith("spread").any()
    assert rec["stats"]["quotes"]["recorded"] > 0
    # the other symbols signal at the same minutes (their take/skip may differ: AAA no longer uses up the caps)
    other = lambda r: r["signals"][r["signals"].symbol != "AAA"][["symbol", "strategy", "bar_index"]].reset_index(drop=True)  # noqa
    pd.testing.assert_frame_equal(other(base), other(rec))
