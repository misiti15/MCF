"""Leaderboard rows carry a compact per-session record and the last session (owner 2026-10-21). Educational only."""
import json

import pandas as pd

from mcf.report import scorecard


def _t():
    return pd.DataFrame({"strategy": ["A", "A", "A", "B"], "date": ["2026-10-20", "2026-10-21", "2026-10-21", "2026-10-20"],
                         "pnl": [5.0, -10.0, 4.0, 3.0], "r_multiple": [0.5, -1.0, 0.4, 0.3]})


def test_daily_series_and_last_session():
    lb = {r["setup"]: r for r in scorecard.leaderboard(_t(), {"strategies": {"A": {"enabled": True}, "B": {"enabled": True}}}, "testing")}
    assert lb["A"]["daily"] == [["2026-10-20", 1, 0.5, 5.0], ["2026-10-21", 2, -0.6, -6.0]]
    assert lb["A"]["last_session"] == {"date": "2026-10-21", "trades": 2, "r": -0.6, "pnl": -6.0}
    # B did not trade in the account's last session: shown as "—" on the dashboard
    assert lb["B"]["last_session"] == {"date": "2026-10-21", "trades": 0, "r": None, "pnl": None}
    json.dumps(lb)


def test_enabled_setup_without_trades():
    r = scorecard.leaderboard(pd.DataFrame(columns=["strategy", "date", "pnl", "r_multiple"]),
                              {"strategies": {"C": {"enabled": True}}}, "testing")[0]
    assert r["daily"] == [] and r["last_session"] == {"date": None, "trades": 0, "r": None, "pnl": None}


def test_card_leaderboard_has_last_session():
    t = _t().assign(entry_time=["2026-10-20 10:00:00-04:00", "2026-10-21 10:00:00-04:00", "2026-10-21 11:00:00-04:00",
                                "2026-10-20 12:00:00-04:00"])
    card = scorecard.build(t, 4, cfg={"strategies": {"A": {"enabled": True}}}, account="testing")
    assert all("last_session" in r and "daily" in r for r in card["leaderboard"])
