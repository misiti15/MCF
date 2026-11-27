"""SPREADFLOOR shadow logger (mcf/execution/spreadfloor.py, research/spreadfloor_1127): log only.
Proves (1) the full-poll golden run of the Friday switches is unchanged with the logger on, with real quote fields, and
with the logger crashing; (2) the fields are written to the journaled signal and order meta; (3) the report summarizes
them per setup. Educational only - not financial advice."""
import json

import pandas as pd
import pytest

from mcf.execution import runner as R
from mcf.execution import spreadfloor as SF
from mcf.report import spreadfloor as REP
from tests.test_friday_switches import GOLDEN, _golden_run

SPREAD = {"AAA": 0.05, "BBB": 0.03, "CCC": 0.02, "DDD": 0.0}     # stop is 0.20 away: 4 / 6.67 / 10 spreads / locked


def _quoted_realism(sig, ctx, px, quote=None):
    s = SPREAD[sig.symbol]
    return True, "ok", {"bid": round(px - s / 2, 4), "ask": round(px + s / 2, 4), "spread_bps": 0.0}


class _MP:
    """monkeypatch proxy: swaps the golden run's {}-info _realism for one that carries a two-sided quote."""

    def __init__(self, mp):
        self.mp = mp

    def setattr(self, obj, name, value, *a, **k):
        if name == "_realism":
            value = _quoted_realism
        return self.mp.setattr(obj, name, value, *a, **k)


def _want():
    with open(GOLDEN) as f:
        return json.load(f)


def _got(res):
    return json.loads(json.dumps(res, default=str))


# ------------------------------------------------------------------------------------------------ pure fields
def test_fields_math_and_floors():
    f = SF.fields(19.99, 20.02, 20.0, 19.80)
    assert f["quote"] and f["spread_c"] == pytest.approx(3.0) and f["stop_c"] == pytest.approx(20.0)
    assert f["stop_spreads"] == pytest.approx(6.67, abs=0.01) and f["stop_bps"] == pytest.approx(100.0)
    assert f["would_skip_6"] is False and f["would_skip_8"] is True
    g = SF.fields(10.00, 10.05, 10.0, 10.20)              # short: 4 spreads
    assert g["would_skip_6"] and g["would_skip_8"] and g["stop_spreads"] == pytest.approx(4.0)
    assert SF.fields(None, 20, 20, 19.8) == {"quote": False}
    assert SF.fields(20.1, 20.0, 20, 19.8) == {"quote": False}          # crossed
    locked = SF.fields(20.0, 20.0, 20.0, 19.8)
    assert locked["stop_spreads"] is None and not locked["would_skip_6"] and not locked["would_skip_8"]


# ------------------------------------------------------------------------------------------------ trading no-op
def test_logger_on_no_quote_matches_golden(tmp_path, monkeypatch):
    calls = []
    orig = R.PaperRunner._spreadfloor_tag
    monkeypatch.setattr(R.PaperRunner, "_spreadfloor_tag", lambda self, *a: (calls.append(1), orig(self, *a))[1])
    assert _got(_golden_run(tmp_path, monkeypatch)) == _want()
    assert len(calls) == 12                               # it ran at every entry of the golden scenario


def test_logger_on_with_quotes_matches_golden_and_writes_fields(tmp_path, monkeypatch):
    got = _got(_golden_run(tmp_path, _MP(monkeypatch)))
    assert got == _want()                                 # decisions, orders, risk state identical
    from mcf.journal import Journal
    j = Journal(str(tmp_path / "j.db"))
    run = j.db.execute("SELECT id FROM runs WHERE kind='paper' ORDER BY id LIMIT 1").fetchone()[0]
    sig = j.signals(run)
    sub = sig[sig.status == "submitted"]
    assert len(sub) == 12
    for x in sub.itertuples():
        t = json.loads(x.info)[SF.KEY]
        assert t["quote"] is True and t["stop_c"] == pytest.approx(20.0, abs=0.01)
        exp = SPREAD[x.symbol]
        if exp:
            assert t["stop_spreads"] == pytest.approx(0.2 / exp, abs=0.02)
            assert t["would_skip_6"] is (0.2 / exp < 6) and t["would_skip_8"] is (0.2 / exp < 8)
    skipped = sig[sig.status != "submitted"]
    assert not any(SF.KEY in (x or "") for x in skipped["info"])   # entries only, never on skips
    om = pd.read_sql("SELECT meta FROM orders WHERE run_id=?", j.db, params=[run])["meta"]
    assert len(om) == 12 and all(SF.KEY in json.loads(m) for m in om)
    sh = pd.read_sql("SELECT meta FROM orders WHERE run_id<>?", j.db, params=[run])["meta"]
    assert not any(SF.KEY in (m or "") for m in sh)       # shadow book untouched


def test_logger_crash_is_swallowed_and_matches_golden(tmp_path, monkeypatch, capsys):
    def boom(*a, **k):
        raise RuntimeError("spreadfloor boom")
    monkeypatch.setattr(SF, "fields", boom)
    assert _got(_golden_run(tmp_path, _MP(monkeypatch))) == _want()
    assert "spreadfloor log failed: RuntimeError" in capsys.readouterr().out


def test_kill_switch_off_writes_nothing_and_matches_golden(tmp_path, monkeypatch):
    def off(cfg):
        cfg["live"]["spreadfloor_log"] = False
    assert _got(_golden_run(tmp_path, _MP(monkeypatch), mutate=off)) == _want()
    from mcf.journal import Journal
    j = Journal(str(tmp_path / "j.db"))
    assert not any(SF.KEY in (x or "") for x in pd.read_sql("SELECT info FROM signals", j.db)["info"])


def test_tag_never_touches_other_info_keys(tmp_path, monkeypatch):
    from types import SimpleNamespace
    r = SimpleNamespace(live={})
    info = {"bid": 9.99, "ask": 10.01, "cap_qty": 7}
    R.PaperRunner._spreadfloor_tag(r, SimpleNamespace(stop=9.9), info, 10.0)
    assert info["cap_qty"] == 7 and info["bid"] == 9.99 and set(info) == {"bid", "ask", "cap_qty", SF.KEY}
    assert info[SF.KEY]["stop_spreads"] == pytest.approx(5.0) and info[SF.KEY]["would_skip_6"] is True
    assert "bracket" not in info[SF.KEY]
    info2 = {"bid": 9.99, "ask": 10.01}
    R.PaperRunner._spreadfloor_tag(r, SimpleNamespace(stop=9.8), info2, 10.0, 9.95)   # AV50-style tight bracket stop
    assert info2[SF.KEY]["stop_spreads"] == pytest.approx(10.0)
    assert info2[SF.KEY]["bracket"]["stop_spreads"] == pytest.approx(2.5) and info2[SF.KEY]["bracket"]["would_skip_6"]


# ------------------------------------------------------------------------------------------------ report
def test_report_summarizes_per_setup(tmp_path, monkeypatch, capsys):
    _golden_run(tmp_path, _MP(monkeypatch))
    path = str(tmp_path / "j.db")
    from mcf.journal import Journal
    j = Journal(path)
    run = j.db.execute("SELECT id FROM runs WHERE kind='paper' ORDER BY id LIMIT 1").fetchone()[0]
    sub = j.signals(run)
    sub = sub[sub.status == "submitted"]
    rows = []
    for k, x in enumerate(sub.itertuples()):
        rows.append({"symbol": x.symbol, "strategy": x.strategy, "side": x.side, "date": "2026-11-27",
                     "entry": 20.0, "stop": 19.8, "r_multiple": -1.0 if x.symbol == "AAA" else 0.5, "shares": 10,
                     "broker_order_id": x.broker_order_id})
    j.add_trades(run, pd.DataFrame(rows))
    j.db.close()
    out = tmp_path / "sf.json"
    assert REP.main([path, "--json", str(out)]) == 0
    res = json.loads(out.read_text())
    assert res["entries"] == 12 and res["with_quote"] == 12 and "Educational only" in res["disclaimer"]
    n = sub.symbol.value_counts()
    assert res["would_skip_6"] == n.get("AAA", 0)                       # 4 spreads; BBB is 6.67
    assert res["would_skip_8"] == n.get("AAA", 0) + n.get("BBB", 0)
    assert sum(s["n"] for s in res["setups"]) == 12
    for s in res["setups"]:
        assert {"skip6_n", "skip8_n", "skip6_avgR", "kept6_avgR", "med_stop_spreads", "closed"} <= set(s)
        assert s["closed"] == s["n"]
        if s["skip6_n"]:
            assert s["skip6_avgR"] == pytest.approx(-1.0)                # AAA lots carry -1R in this fixture
    assert "SPREADFLOOR log" in capsys.readouterr().out


def test_report_empty_journal(tmp_path):
    from mcf.journal import Journal
    p = str(tmp_path / "e.db")
    Journal(p).db.close()
    assert REP.summarize(REP.load(p))["entries"] == 0
