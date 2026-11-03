"""BETA1 (owner 2026-11-03): "Avg R ex-market" = intercept of per-trade R on SPY's same-window % move, merged exactly
across accounts; shown in the scorecard leaderboard, dashboard, daily post, EOD report and gates.summary.
Educational only - not financial advice."""
from pathlib import Path

import numpy as np
import pandas as pd

from mcf.analytics import market_beta as M

ROOT = Path(__file__).resolve().parents[1]


def _spy(day="2026-11-03", start=600.0, step=0.1):
    idx = pd.date_range(f"{day} 09:30", f"{day} 15:59", freq="1min", tz="America/New_York")
    return pd.DataFrame({"close": start + step * np.arange(len(idx))}, index=idx)


def test_fit_recovers_intercept_and_beta():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 0.5, 400)
    y = 0.1 + 0.8 * x + rng.normal(0, 0.05, 400)
    f = M.fit(M.sums(x, y))
    assert abs(f["exmkt_r"] - 0.1) < 0.02 and abs(f["beta"] - 0.8) < 0.03
    # exact merge: two halves summed give the same fit as the whole
    a, b = M.sums(x[:150], y[:150]), M.sums(x[150:], y[150:])
    assert M.fit(M.merge([a, b])) == f
    assert M.fit(M.sums(x[:4], y[:4]))["exmkt_r"] is None          # under MIN_N
    assert M.fit(M.sums(np.zeros(10), y[:10]))["exmkt_r"] is None   # no spread in SPY's move


def test_spy_moves_same_window():
    spy = _spy()
    t = pd.DataFrame({"entry_time": pd.to_datetime(["2026-11-03 10:00", "2026-11-02 10:00"]).tz_localize("America/New_York"),
                      "exit_time": pd.to_datetime(["2026-11-03 11:00", "2026-11-02 11:00"]).tz_localize("America/New_York")})
    x = M.spy_moves(t, spy)
    exp = ((600 + 0.1 * 90) / (600 + 0.1 * 30) - 1) * 100
    assert abs(x.iloc[0] - exp) < 1e-9 and np.isnan(x.iloc[1])     # no SPY bars that day -> left out


def test_scorecard_leaderboard_carries_exmkt():
    from mcf.report import scorecard

    spy = _spy()
    n = 12
    ent = pd.date_range("2026-11-03 10:00", periods=n, freq="10min", tz="America/New_York")
    ext = ent + pd.to_timedelta(np.arange(1, n + 1) * 3, unit="min")
    x = M.spy_moves(pd.DataFrame({"entry_time": ent, "exit_time": ext}), spy).to_numpy()
    r = 0.2 + 2.0 * x
    t = pd.DataFrame({"strategy": "S", "date": "2026-11-03", "entry_time": ent, "exit_time": ext, "r_multiple": r,
                      "pnl": r * 10, "symbol": "X"})
    rows = scorecard.leaderboard(t, {"strategies": {"S": {"enabled": True}}}, "testing", spy=spy)
    row = rows[0]
    assert row["mkt_n"] == n and abs(row["exmkt_r"] - 0.2) < 1e-3 and abs(row["beta"] - 2.0) < 1e-3
    rows = scorecard.leaderboard(t, {"strategies": {"S": {"enabled": True}}}, "testing")   # no SPY bars
    assert rows[0]["mkt_n"] == 0 and rows[0]["exmkt_r"] is None


def test_daily_post_merge_and_gates_summary():
    from mcf.report.daily_post import _merge
    from mcf.research.gates import summary

    rng = np.random.default_rng(1)
    x = rng.normal(0, 0.4, 60)
    y = -0.05 - 1.2 * x
    a, b = M.sums(x[:30], y[:30]), M.sums(x[30:], y[30:])
    base = {"trades": 30, "n_win": 10, "total_r": 1.0, "pnl": 1.0, "r_sq_sum": 5.0, "win_r_sum": 3, "loss_r_sum": 2,
            "win_pnl": 1, "loss_pnl": 1, "days": [], "daily": []}
    m = _merge([{**base, **a}, {**base, **b}])
    assert abs(m["exmkt_r"] + 0.05) < 1e-6 and abs(m["beta"] + 1.2) < 1e-6
    s = summary(pd.DataFrame({"date": ["d1"] * 30 + ["d2"] * 30, "r": y, "spy_move": x}))
    assert abs(s["ex_market_r"] + 0.05) < 1e-6 and "ex_best_day" in s


def test_dashboard_and_reports_show_column():
    html = (ROOT / "docs/live/index.html").read_text()
    assert '["exmkt_r", "Avg R ex-market"]' in html and "const exMkt" in html
    assert "Avg R ex-market" in (ROOT / "mcf/report/eod.py").read_text()
    assert "Avg R ex-market" in (ROOT / "mcf/report/daily_post.py").read_text()
