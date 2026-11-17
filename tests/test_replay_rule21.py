"""Rule 21 replay-vs-live audit (owner "RULE21-DB yes", 2026-11-17): trades match on the live signal's DECISION bar
(client order id HHMM), never the broker fill minute; guards >= 95% match, avg R gap within +-0.03R and never
optimistic, fresh sessions only. Educational only — not financial advice."""
import importlib.util
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("replay_cal_score", ROOT / "research" / "replay_cal" / "score.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def _lot(setup, sym, day, hhmm, fill_time, r=0.1):
    return dict(strategy=setup, symbol=sym, side=1, date=day, entry_time=fill_time, entry=10.0, stop=9.0, shares=10,
                pnl=r * 10, broker_order_id=f"{sym}-{hhmm}", target=None,
                meta=f'{{"coid": "mcf-{setup}-{sym}-{day.replace("-", "")}-{hhmm}"}}')


def test_lots_use_decision_bar_not_fill_minute():
    # decision bar 10:15, filled 10:16:41 (the fill lands +1/+2 min after the decision bar)
    L = S.lots(pd.DataFrame([_lot("A", "XYZ", "2026-11-12", "1015", "2026-11-12 10:16:41-05:00")]))
    assert L.iloc[0]["min"] == 10 * 60 + 15
    # replay filled in the decision minute itself: still an exact match on the decision bar
    R = S.lots(pd.DataFrame([_lot("A", "XYZ", "2026-11-12", "1015", "2026-11-12 10:15:20-05:00")]))
    assert S.match(L, R, 0) == [(0, 0)]
    R2 = S.lots(pd.DataFrame([_lot("A", "XYZ", "2026-11-12", "1016", "2026-11-12 10:16:41-05:00")]))
    assert S.match(L, R2, 0) == []                         # same fill minute, different decision bar -> no match


def _summ(match=0.96, bias=-0.01, se=0.005, live=0.10, rep=0.09, days=("2026-11-12", "2026-11-13")):
    return dict(match=match, bias=bias, bias_se=se, live_avg_r=live, replay_avg_r=rep, days=list(days))


def test_rule21_guards():
    fit = "2026-10-30"
    assert S.rule21(_summ(), fit)["pass"]
    assert not S.rule21(_summ(match=0.94), fit)["pass"]                       # < 95% match
    assert not S.rule21(_summ(bias=-0.04), fit)["pass"]                       # matched gap outside +-0.03R
    assert not S.rule21(_summ(rep=0.06), fit)["pass"]                         # all-trade avg R gap -0.04R
    v = S.rule21(_summ(bias=0.02, se=0.005, rep=0.12), fit)                   # +0.02R, significantly optimistic
    assert v["gap_ok"] and not v["no_optimism"] and not v["pass"]
    assert S.rule21(_summ(bias=0.005, se=0.01, rep=0.105), fit)["pass"]       # within noise, not optimistic
    v = S.rule21(_summ(days=("2026-10-30", "2026-11-12")), fit)               # a fit session is not fresh
    assert not v["fresh"] and not v["pass"]
    assert not S.rule21(_summ(bias=float("nan")), fit)["pass"]
    assert S.R21 == {"match": 0.95, "gap": 0.03, "z": 1.645}


def test_fresh_days_drop_fit_sessions():
    assert S.fresh_days(["2026-10-29", "2026-10-30", "2026-11-02"], "2026-10-30") == ["2026-11-02"]
    assert S.fresh_days(["2026-10-29"], None) == ["2026-10-29"]


def test_rule_text_says_decision_bar():
    t = (ROOT / "docs" / "RESEARCH_RULES.md").read_text()
    i = t.index("Replays must first pass an audit against live")
    rule = t[i:i + 1200]
    assert "decision bar" in rule and "fresh" in rule and "fill minute" in rule and not math.isnan(S.R21["gap"])
