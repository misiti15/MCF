"""Daily post images (owner 2026-10-24): merge and streak math match the dashboard. Educational only - not financial advice."""
from mcf.report.daily_post import _merge, streak


def test_merge_sums_like_dashboard():
    a = dict(setup="X", trades=2, n_win=1, total_r=1.0, pnl=10.0, r_sq_sum=4.25, win_r_sum=2.0, loss_r_sum=1.0,
             win_pnl=20.0, loss_pnl=10.0, days=["d1"], daily=[["d1", 2, 1.0, 10.0]])
    b = dict(setup="X", trades=2, n_win=2, total_r=2.0, pnl=30.0, r_sq_sum=2.0, win_r_sum=2.0, loss_r_sum=0.0,
             win_pnl=30.0, loss_pnl=0.0, days=["d1", "d2"], daily=[["d1", 1, 1.0, 10.0], ["d2", 1, 1.0, 20.0]])
    m = _merge([a, b])
    assert m["trades"] == 4 and m["win_rate"] == 0.75 and m["avg_r"] == 0.75 and m["pnl"] == 40.0
    assert m["sessions_traded"] == 2 and abs(m["breakeven_wr"] - 3 / 7) < 1e-9 and m["profit_factor"] == 5.0
    assert m["daily"] == [["d1", 3, 2.0, 20.0], ["d2", 1, 1.0, 20.0]]


def test_streak_counts_green_days_to_date():
    h = [dict(date="d1", trades=3, pnl=5), dict(date="d2", trades=3, pnl=-1), dict(date="d3", trades=2, pnl=4), dict(date="d4", trades=1, pnl=2)]
    assert streak({"history": h}, "d4") == (2, 3, 4)
    assert streak({"history": h}, "d2") == (0, 1, 2)


def test_best_day_metric():
    from mcf.report.daily_post import best_day
    r = dict(trades=12, total_r=2.24, daily=[["d1", 4, 4.06, 0], ["d2", 2, 0.13, 0], ["d3", 5, -2.45, 0], ["d4", 1, 0.5, 0]])
    ex, d, share = best_day(r)
    assert d == "d1" and abs(ex - (2.24 - 4.06) / 8) < 1e-9 and share > 1     # the best day is bigger than the whole record
    assert best_day(dict(trades=3, total_r=1.0, daily=[["d1", 3, 1.0, 0]])) == (None, None, None)


def test_green_streaks(monkeypatch):
    from mcf.report import daily_post as dp
    sess = ["2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"]
    accts = [dict(full_history=[dict(date=d, trades=5) for d in sess])]
    sc = {"leaderboard": [
        {"setup": "A", "trades": 4, "daily": [[d, 1, 0.5, 10.0] for d in sess]},                       # 4 in a row
        {"setup": "B", "trades": 3, "daily": [["2026-10-21", 1, 0.5, 5.0], ["2026-10-22", 1, 0.5, 5.0],
                                              ["2026-10-23", 1, 0.5, 5.0]]},                           # 3 in a row
        {"setup": "C", "trades": 3, "daily": [["2026-10-20", 1, 0.5, 5.0], ["2026-10-22", 1, 0.5, 5.0],
                                              ["2026-10-23", 1, 0.5, 5.0]]},                           # gap on 10-21
    ]}
    monkeypatch.setattr(dp, "_show", lambda br, path: sc if br == "mcf-data" else None)
    monkeypatch.setattr(dp, "_local", lambda path: {})
    gs = dp.green_streaks("2026-10-23", accts)
    assert [(x["setup"], x["run"]) for x in gs["current"]] == [("A", 4), ("B", 3)]
    assert gs["record"][0]["setup"] == "A" and gs["record"][0]["run"] == 4
    assert "A: 4 in a row" in "\n".join(dp._streak_lines(gs))
