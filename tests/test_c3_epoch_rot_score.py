"""C3 (owner yes 2026-11-18): BASE1 baseline twin (journal-only, Primary only), C3-ROT family caps and arena reps,
C3-SCORE scorecard / corrected what-if / capture buckets / epoch pairs, C3-NS5 lineup. Educational only - not
financial advice."""
import json
import sqlite3
from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from mcf import rotation as ROT
from mcf.config import load_config
from mcf.execution import shadow as SH
from mcf.report import arena_reps as AR
from mcf.report import c3score as C


# ------------------------------------------------------------------------------------------------- C3-NS5 / BASE1
def test_ns5_left_primary_and_runs_in_on_deck_only(monkeypatch):
    monkeypatch.delenv("MCF_ACCOUNT", raising=False)
    p = load_config(asof="2026-11-19")
    on = sorted(k for k, v in p["strategies"].items() if v.get("enabled"))
    assert "NS5-sma50-flush-oversold-long" not in on and len(on) == 4   # ST7-MOVE 2026-11-21: ST7 left Primary too
    assert "ST7-rsi50dn-long-pm-t1s1-FD" not in on
    assert "NS5-sma50-flush-oversold-long" not in p["live"]["setup_order"]
    monkeypatch.setenv("MCF_ACCOUNT", "testing")
    t = load_config(asof="2026-11-19")["strategies"]["NS5-sma50-flush-oversold-long"]
    assert t["enabled"] and t["window"] == [950, 1130] and t["former_primary"]["demoted"] == "2026-11-18"


def test_baseline_is_the_frozen_epoch0_book_and_primary_only(monkeypatch):
    monkeypatch.delenv("MCF_ACCOUNT", raising=False)
    cfg = load_config(asof="2026-11-19")
    b = cfg["baseline"]
    assert b["id"] == "BASE1" and b["account"] == "primary" and b["epoch_start"] == "2026-11-19"
    assert b["setup_order"] == ["NM-ETF-late-dip-di-long", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
                                "RW3-gapdn-rsi5pop-flowsell-short-FD", "ST7-rsi50dn-long-pm-t1s1-FD",
                                "L3-gap-slope-fromopen-FD", "NS5-sma50-flush-oversold-long"]
    # the five still in Primary carry exactly Primary's blocks (the baseline is a copy, not a variant), except for later
    # Primary epoch changes, which BASE1 never follows: AV50 burst_tight_stop on NM-ETF (epoch 3, from 2026-11-30;
    # ledger 2026-11-30-etf-stop50-av50) - BASE1's NM-ETF keeps the unchanged exit so the epoch pair measures AV50
    later = {"burst_tight_stop"}
    for k in b["setup_order"][:5]:
        live = {x: y for x, y in cfg["strategies"][k].items() if x != "enabled" and x not in later}
        assert b["setups"][k] == live, k
        assert not later & set(b["setups"][k]), k
    names = [s.name for s in SH.baseline_strategies(cfg)]
    assert names == [f"BASE1:{k}" for k in b["setup_order"]]
    monkeypatch.setenv("MCF_ACCOUNT", "testing")
    assert SH.baseline_strategies(load_config(asof="2026-11-19")) == []      # never outside Primary


def test_baseline_add_extras_runs_every_poll_and_places_no_orders():
    runner = SimpleNamespace(cfg={"shadow": {"enabled": True}}, strategies=[], watchlist=None, health={})
    book = SH.ShadowBook(runner, [])
    a, b = SimpleNamespace(name="BASE1:X"), SimpleNamespace(name="ONLY")
    assert book.add_extras([a], baseline=True) == 1 and book.add_extras([a, b]) == 1
    assert book.baseline == [a] and [s.name for s in book.extras] == ["BASE1:X", "ONLY"]
    seen = []
    book._scan_extras = lambda ctxs, strategies=None: seen.append(strategies)
    book._process = lambda now: None
    book.manage = lambda now, bars: None
    book.flush = lambda: None
    book._session_markers = lambda now: None
    book.every = 2
    for _ in range(2):
        book.poll(pd.Timestamp("2026-11-19 10:00", tz="America/New_York"), {}, {}, 100.0)
    assert seen == [[a], None]          # poll 1 (throttled): baseline only; poll 2: every extra


# ----------------------------------------------------------------------------------------------------- C3-ROT
def test_pick_round_robin_orders_by_reps_and_covers_everyone():
    m = [f"GEN-{i}" for i in range(10)]
    reps = {**{k: 5 for k in m}, "GEN-9": 0, "GEN-8": 1}
    d0 = date(2026, 11, 19)
    first = ROT.pick(m, 6, d0, d0, reps)
    assert {"GEN-9", "GEN-8"} <= set(first) and len(first) == 6
    played = set()
    for d in (19, 20, 23, 24):           # weekdays: the window moves every session
        played |= set(ROT.pick(m, 6, date(2026, 11, d), d0, reps))
    assert played == set(m)
    assert ROT.pick(m[:3], 6, d0, d0) == sorted(m[:3])


def test_family_caps_bench_over_cap_and_exempt_workbench_and_non_arena():
    st = {f"GEN-{i}": {"enabled": True} for i in range(8)}
    st["GEN-0-WB1"] = {"enabled": True}
    st["L3-x"] = {"enabled": True}
    rc = {"enabled": True, "from": "2026-11-19", "accounts": ["testing2"], "reps_file": "nope.json",
          "caps": {"GEN": {"prefix": "GEN-", "cap": 6, "scope": "account"}}}
    cfg = {"account_name": "testing2", "strategies": json.loads(json.dumps(st)), "arena_rotation": rc}
    out = ROT.family_caps(cfg, "2026-11-19")
    on = [k for k, v in cfg["strategies"].items() if v["enabled"]]
    assert len([k for k in on if k.startswith("GEN-") and "-WB" not in k]) == 6
    assert "GEN-0-WB1" in on and "L3-x" in on and len(out["GEN"]["benched"]) == 2
    assert cfg["rotation"]["family_benched"]["GEN"] == out["GEN"]["benched"]
    for acct in ("primary", "testing", "graveyard"):
        c2 = {**cfg, "account_name": acct, "strategies": json.loads(json.dumps(st))}
        assert ROT.family_caps(c2, "2026-11-19") == {}
    c3 = {**cfg, "strategies": json.loads(json.dumps(st))}
    assert ROT.family_caps(c3, "2026-11-18") == {}          # before `from`


def test_family_caps_arena_scope_is_consistent_across_accounts():
    rc = {"enabled": True, "from": "2026-11-19", "accounts": ["testing2", "testingd"], "reps_file": "nope.json",
          "caps": {"CWT14": {"prefix": "CWT14-", "cap": 2, "scope": "arena"}}}
    members = {"testing2": ["CWT14-a", "CWT14-b"], "testingd": ["CWT14-c", "CWT14-d"]}
    playing = set()
    for acct in members:
        cfg = {"account_name": acct, "arena_rotation": rc, "strategies": {k: {"enabled": True} for k in members[acct]}}
        ROT.family_caps(cfg, "2026-11-20", members_by_account=members)
        playing |= {k for k, v in cfg["strategies"].items() if v["enabled"]}
    assert len(playing) == 2


def test_arena_reps_active_days_shadow_column_and_triage(tmp_path):
    db = tmp_path / "j.db"
    c = sqlite3.connect(db)
    c.executescript("""CREATE TABLE runs (id INTEGER PRIMARY KEY, kind TEXT, label TEXT, created_at TEXT, config TEXT, summary TEXT);
    CREATE TABLE trades (id INTEGER PRIMARY KEY, run_id INT, symbol TEXT, strategy TEXT, side INT, date TEXT, exit_time TEXT);
    CREATE TABLE signals (id INTEGER PRIMARY KEY, run_id INT, day TEXT, strategy TEXT, status TEXT);
    INSERT INTO runs VALUES (1,'paper','live','',''  ,''),(3,'shadow','MCF shadow (no orders)','','','');
    INSERT INTO trades(run_id,symbol,strategy,side,date,exit_time) VALUES (1,'A','S1',1,'2026-11-17','x'),(3,'A','S1',1,'2026-11-18','x'),(3,'A','BASE1:S1',1,'2026-11-18','x');""")
    for i in range(12):
        c.execute("INSERT INTO signals(run_id,day,strategy,status) VALUES (1,'2026-11-17','S1',?)", ("skipped" if i < 9 else "submitted",))
    c.commit()
    snaps = {"testing2": {f"2026-11-{d:02d}": {"strategies": {"S1": {"enabled": True}, "S2": {"enabled": True},
                                                             "S3": {"enabled": False}}} for d in range(3, 19) if date(2026, 11, d).weekday() < 5}}
    r = AR.build(snaps, {"testing2": db}, until="2026-11-18")
    assert r["S1"]["active_days"] == 12 and r["S1"]["trades"] == 1 and r["S1"]["shadow_days"] == 1
    assert "blocked" in r["S1"]["triage"] and not r["S1"]["verdict_ready"]
    assert "zero-signal" in r["S2"]["triage"] and "S3" not in r and "BASE1:S1" not in r


# ---------------------------------------------------------------------------------------------------- C3-SCORE
def _tr(rows):
    return pd.DataFrame(rows, columns=["date", "symbol", "strategy", "entry", "stop", "shares", "pnl_adj", "pnl"])


def test_day_table_account_r_and_scorecard_line():
    t = _tr([("2026-11-16", "A", "S", 10.0, 9.0, 100, 100.0, 100.0),     # +1R, $100
             ("2026-11-17", "B", "S", 10.0, 9.0, 10, -20.0, -20.0),      # -2R, $-20
             ("2026-11-18", "C", "S", 10.0, 9.5, 100, 300.0, 300.0)])     # +6R, $300
    d = C.day_table(t, equity=100_000, risk_pct=0.25)
    assert list(d.dash_r.round(2)) == [1.0, -2.0, 6.0]
    assert list(d.acct_r.round(2)) == [0.4, -0.08, 1.2]                  # $ / $250
    sc = C.scorecard(d)
    assert sc["week"]["wo_best"] == -1.0 and sc["week"]["best_share"] == 1.2 and sc["week"]["one_day"]
    assert sc["green_pct_20"] == pytest.approx(66.7) and sc["days_le_m10_20"] == 0
    line = C.line(sc, tag="gap-up / 0950 up")
    assert "1 day" in line and "account" in line and "not financial advice" in line


def test_whatif_corrected_drops_unfillable_dupes_and_haircuts():
    w = pd.DataFrame([
        {"symbol": "A", "date": "d1", "entry": 10.0, "stop": 9.0, "shares": 100, "pnl_adj": 200.0, "pnl": 200.0,
         "reason": "max positions for this setup", "spread_bps": 10.0, "entry_time": 1},
        {"symbol": "A", "date": "d1", "entry": 10.0, "stop": 9.0, "shares": 100, "pnl_adj": 300.0, "pnl": 300.0,
         "reason": "max positions for this setup", "spread_bps": 10.0, "entry_time": 2},
        {"symbol": "B", "date": "d1", "entry": 10.0, "stop": 9.0, "shares": 100, "pnl_adj": 500.0, "pnl": 500.0,
         "reason": "spread 45bps > max", "spread_bps": 45.0, "entry_time": 1},
        {"symbol": "C", "date": "d1", "entry": 10.0, "stop": 9.0, "shares": 100, "pnl_adj": 100.0, "pnl": 100.0,
         "reason": "not shortable/ETB", "spread_bps": 5.0, "entry_time": 1}])
    r = C.whatif_corrected(w)
    assert r["raw_n"] == 4 and r["raw_r"] == 11.0
    assert r["dropped_unfillable"] == 2 and r["dropped_dupes"] == 1 and r["n"] == 1
    assert r["r"] == pytest.approx(2.0 - 0.01 - 0.05)


def test_capture_buckets_and_epoch_pairs():
    m = pd.DataFrame({"set": ["all"] * 4 + ["tradable"], "blackout": [True, False, False, "True", False],
                      "n_right": [0, 1, 0, 0, 1]})
    b = C.capture_buckets(m)
    assert b["headline"] == {"moves": 4, "caught": 1, "pct": 25.0}
    assert b["tradable"]["pct"] == 50.0 and b["earnings_blackout"]["moves"] == 2
    sh = _tr([("2026-11-19", "A", "L3", 10.0, 9.0, 100, 100.0, 100.0), ("2026-11-19", "A", "BASE1:L3", 10.0, 9.0, 100, 100.0, 100.0),
              ("2026-11-19", "B", "BASE1:NS5", 10.0, 9.0, 100, -100.0, -100.0),
              ("2026-11-20", "A", "L3", 10.0, 9.0, 100, 200.0, 200.0), ("2026-11-20", "C", "BASE1:L3", 10.0, 9.0, 100, 200.0, 200.0),
              ("2026-11-18", "Z", "BASE1:L3", 10.0, 9.0, 100, 900.0, 900.0)])
    e = C.epoch_pairs(sh, "BASE1", "2026-11-19")
    assert [r["diff"] for r in e["days"]] == [1.0, 0.0] and e["n"] == 2 and e["mean_diff"] == 0.5
    # a shadow-ONLY (non-baseline) lot is not part of the current book: only of_live lots count as "current"
    sh2 = sh.assign(meta="mode=of_live")
    extra = sh2.iloc[[0]].assign(strategy="X-only", meta="mode=only", pnl=500.0, pnl_adj=500.0)
    e2 = C.epoch_pairs(pd.concat([sh2, extra], ignore_index=True), "BASE1", "2026-11-19")
    assert [r["diff"] for r in e2["days"]] == [1.0, 0.0]


def test_day_type_tag_point_in_time():
    idx = pd.date_range("2026-11-19 09:30", periods=30, freq="1min", tz="America/New_York")
    spy = pd.DataFrame({"open": [101.0] * 30, "close": [101.0] * 19 + [101.5] + [90.0] * 10}, index=idx)
    assert C.day_type(spy, 100.0) == "gap-up / 0950 up"       # the 09:50+ crash is not known at 09:50
    assert C.day_type(spy.iloc[:0], 100.0) == "n/a"
