"""Leaderboard break-even win rate + t-stat, and the Generator Lab summary (owner 2026-10-19). Educational only."""
import json

import pandas as pd

from mcf.report import scorecard
from mcf.research.generator import summary


def test_leaderboard_breakeven_and_t():
    t = pd.DataFrame({"strategy": ["A"] * 4, "date": ["2026-10-19"] * 4, "pnl": [5, 5, 5, -10],
                      "r_multiple": [0.5, 0.5, 0.5, -1.0]})
    r = scorecard.leaderboard(t, {"strategies": {"A": {"enabled": True}}}, "testing")[0]
    assert r["avg_win_r"] == 0.5 and r["avg_loss_r"] == 1.0
    assert r["breakeven_wr"] == 0.667          # 1 / (0.5 + 1): wins 75% but needs 67%
    assert r["t_stat"] == 0.33


def test_leaderboard_breakeven_none_without_losses():
    t = pd.DataFrame({"strategy": ["A"], "date": ["2026-10-19"], "pnl": [5], "r_multiple": [0.5]})
    r = scorecard.leaderboard(t, {"strategies": {"A": {"enabled": True}}}, "testing")[0]
    assert r["breakeven_wr"] is None and r["t_stat"] is None


def test_generator_lab_summary_is_brief():
    d = summary.build()
    assert set(d) >= {"generated", "runs", "setups_generated", "live_in_gen", "promoted", "specs_screened"}
    assert all("picked" in r and "median_valid_r" in r for r in d["runs"])
    assert "picks" not in json.dumps(d)         # trends only, no setup list
