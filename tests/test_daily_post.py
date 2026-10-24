"""Daily post images (owner 2026-10-24): merge and streak math match the dashboard. Educational only - not financial advice."""
from mcf.report.daily_post import _merge, streak


def test_merge_sums_like_dashboard():
    a = dict(setup="X", trades=2, n_win=1, total_r=1.0, pnl=10.0, r_sq_sum=4.25, win_r_sum=2.0, loss_r_sum=1.0,
             win_pnl=20.0, loss_pnl=10.0, days=["d1"], daily=[["d1", 2, 1.0, 10.0]])
    b = dict(setup="X", trades=2, n_win=2, total_r=2.0, pnl=30.0, r_sq_sum=2.0, win_r_sum=2.0, loss_r_sum=0.0,
             win_pnl=30.0, loss_pnl=0.0, days=["d1", "d2"], daily=[["d1", 1, 1.0, 10.0], ["d2", 1, 1.0, 20.0]])
    m = _merge([a, b])
    assert m["trades"] == 4 and m["win_rate"] == 0.75 and m["avg_r"] == 0.75 and m["pnl"] == 40.0
    assert m["sessions_traded"] == 2 and m["breakeven_wr"] == 0.25 and m["profit_factor"] == 5.0
    assert m["daily"] == [["d1", 3, 2.0, 20.0], ["d2", 1, 1.0, 20.0]]


def test_streak_counts_green_days_to_date():
    h = [dict(date="d1", trades=3, pnl=5), dict(date="d2", trades=3, pnl=-1), dict(date="d3", trades=2, pnl=4), dict(date="d4", trades=1, pnl=2)]
    assert streak({"history": h}, "d4") == (2, 3, 4)
    assert streak({"history": h}, "d2") == (0, 1, 2)
