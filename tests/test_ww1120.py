"""Owner 2026-11-20 "What works" decisions: WW-CLUSTER (day-clustered t + avg R w/o top 2 days in every review table)
and RETIRE-R3 (terminal RETIRED at the Friday-after-close review, owner condition: >= 20 active sessions AND >= 150
trades, w/o best day <= -0.10, last-10-session R <= 0; never Primary; Compass exemptions kept).
Educational only - not financial advice."""
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from mcf.analytics import robust as RB
from mcf.report import blueprint as B
from mcf.report import daily_post as DP
from mcf.report import footrace as F

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------------------------------------ WW-CLUSTER
def test_robust_helpers():
    days = RB.by_day([["d1", 2, 10.0, 0], ["d2", 2, 4.0, 0], ["d3", 3, -3.0, 0], ["d1", 1, 2.0, 0]])
    assert days == {"d1": [3, 12.0], "d2": [2, 4.0], "d3": [3, -3.0]}
    assert RB.wo_top_days(days, 2) == -1.0                       # only d3 left: -3R / 3 trades
    assert RB.wo_top_days(days, 1) == pytest.approx(1 / 5)
    assert RB.wo_top_days({"a": [1, 1.0], "b": [1, 2.0]}, 2) is None
    assert RB.day_t([1.0, 2.0]) == 0.0 and RB.day_t([1.0, 1.0, 1.0]) == 0.0
    assert RB.day_t([1.0, 2.0, 3.0]) == pytest.approx(2.0 / (1.0 / 3 ** 0.5))
    assert RB.day_t_daily(days) == pytest.approx(RB.day_t([4.0, 2.0, -1.0]))
    assert RB.day_t_daily({"a": [1, 1.0]}) is None


def _trades(spec, acct="testingf"):
    rows = []
    for s, days in spec.items():
        for i, rs in enumerate(days):
            rows += [{"strategy": s, "date": f"2026-10-{i + 1:02d}", "r": r, "account": acct} for r in rs]
    return pd.DataFrame(rows)


def test_footrace_stats_wo_top2_and_review_rows():
    t = F.setup_stats(_trades({"A": [[10.0], [5.0], [-1.0, -1.0]], "B": [[1.0], [2.0]]}))
    assert t.loc["A", "wo_avg_r"] == pytest.approx(1.0) and t.loc["A", "wo2_avg_r"] == -1.0
    assert t.loc["A", "wo2_total_r"] == -2.0 and pd.isna(t.loc["B", "wo2_avg_r"])
    bad = [[-0.5, -0.4, 0.1]] * 12 + [[-0.3, 0.2, -0.2]] * 8
    t = F.setup_stats(_trades({"X-long": bad}))
    out = F.exit_review(t, {"X-long": "testingf"}, {"X-long": {"active_days": 20, "signals": 80}})
    assert out[0]["wo2_avg_r"] is not None and "t_day" in out[0]


def test_daily_post_and_blueprint_show_cluster_figures():
    r = dict(trades=7, total_r=13.0, daily=[["d1", 3, 12.0, 0], ["d2", 2, 4.0, 0], ["d3", 2, -3.0, 0]])
    wo2, td = DP.cluster(r)
    assert wo2 == -1.5 and td == pytest.approx(RB.day_t([4.0, 2.0, -1.5]))
    src = Path(DP.__file__).read_text()
    assert '"Avg R w/o best day", "Avg R w/o top 2 days"' in src and '"Confidence (t)", "Day t"' in src
    s = B.summarize([dict(date=d, acct="primary", r=r, pnl=0) for d, r in
                     [("d1", 3.0), ("d2", 1.0), ("d3", -1.0), ("d3", -1.0)]])
    assert s["avg_wo_top2"] == -1.0 and s["t_day"] is not None


def test_dashboard_leaderboard_columns():
    html = (ROOT / "docs/live/index.html").read_text()
    assert '["exbest_r", "Avg R w/o best day"], ["exbest2_r", "Avg R w/o top 2 days"]' in html
    assert '["t_stat", "Confidence (t)"], ["t_day", "Day t"]' in html
    assert "Object.assign(m, clusterR(tr.flatMap(r => r.daily || [])));" in html
    assert '"Avg R w/o top 2 days":' in html and '"Day t":' in html


# ------------------------------------------------------------------------------------------------ RETIRE-R3
def _whole(**over):
    base = {"n": 200, "days": 25, "total_r": -40.0, "avg_r": -0.2, "wo_avg_r": -0.15, "wo2_avg_r": -0.18,
            "t_day": -2.5, "last10_r": -5.0, "one_day": False, "big_days": 0, "big_sum": 0.0}
    base.update(over)
    return base


def test_retire_flag_thresholds():
    assert F.retire_flag(_whole())
    assert F.retire_flag(_whole(days=20, n=150, wo_avg_r=-0.10, last10_r=0.0))       # boundaries included
    assert not F.retire_flag(_whole(days=19))                                         # < 20 active sessions
    assert not F.retire_flag(_whole(n=149))                                           # < 150 trades
    assert not F.retire_flag(_whole(wo_avg_r=-0.099))
    assert not F.retire_flag(_whole(last10_r=0.1))                                    # recovering lately


def test_retire_review_exemptions():
    rows = {"A": _whole(), "P": _whole(), "LOW": _whole(n=40, days=30), "BIG": _whole(n=600, big_days=3, big_sum=45.0),
            "OK": _whole(wo_avg_r=0.02), F.COMPASS_EXEMPT[0]: _whole(), F.COMPASS_EXEMPT[1]: _whole()}
    whole = pd.DataFrame(rows).T
    accts = {k: ["graveyard"] for k in rows}
    accts["A"] = ["testingd", "gen"]
    accts["OFF"] = []
    out = F.retire_review(whole, accts, primary={"P"})
    assert [x["setup"] for x in out] == ["A"]                   # Primary, low-activity, Compass and positive setups kept
    x = out[0]
    assert x["accounts"] == ["gen", "testingd"] and x["sessions"] == 25 and x["trades"] == 200
    assert x["wo2_avg_r"] == -0.18 and x["t_day"] == -2.5 and x["state"].startswith("RETIRED")


def test_retire_review_on_trades():
    good = [[0.5, -0.2]] * 25
    bad = [[-0.4, -0.3, 0.2, -0.5, -0.1, 0.3, -0.2]] * 25          # 175 trades over 25 sessions, all losing days
    t = F.setup_stats(_trades({"BAD-short": bad, "GOOD-long": good, "SHORTREC-long": bad[:15]}))
    out = F.retire_review(t, {k: ["graveyard"] for k in t.index})
    assert [x["setup"] for x in out] == ["BAD-short"]


def test_footrace_json_build_carries_retire_review(monkeypatch):
    """build() lists retire_review next to exit_review / archive_review (what the Friday review reads)."""
    def fake_enabled(acct, asof):
        st = {"primary": {"P": {"enabled": True}}, "graveyard": {"BAD-short": {"enabled": True}},
              "testingd": {"P": {"enabled": True}}}.get(acct, {})
        return {"strategies": st, "account": {"slots": 300}}
    monkeypatch.setattr(F, "_enabled", fake_enabled)
    bad = [[-0.4, -0.3, 0.2, -0.5, -0.1, 0.3, -0.2]] * 25
    tr = _trades({"BAD-short": bad, "P": bad}, acct="graveyard")
    doc = F.build(tr, {}, pd.Timestamp("2026-11-20").date())
    assert [x["setup"] for x in doc["retire_review"]] == ["BAD-short"] and "RETIRE-R3" in doc["note"]


def test_rule_docs_and_ledger():
    rr = (ROOT / "docs/RESEARCH_RULES.md").read_text()
    assert "RETIRE-R3" in rr and ">= 20 active sessions" in rr
    led = [json.loads(x) for x in (ROOT / "research/ledger.jsonl").read_text().splitlines() if x.strip()]
    ids = {e["id"] for e in led}
    for i in ("2026-11-23-ww-protect", "2026-11-23-ww-cluster", "2026-11-23-brake-burst", "2026-11-23-brake-watchdog",
              "2026-11-20-retire-r3"):
        assert i in ids, i
    cl = (ROOT / "CLAUDE.md").read_text()
    assert "docs/PROTECTED.md" in cl and re.search(r"w/o top 2 days", cl)
