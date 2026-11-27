"""Month-end rebalancing forward shadow (research/forward/month_end, frozen 2026-11-27): synthetic data, offline.
Educational only - not financial advice."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

P = Path(__file__).resolve().parents[1] / "research" / "forward" / "month_end" / "shadow.py"
spec = importlib.util.spec_from_file_location("month_end_shadow", P)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
CELLS = {"*|market": [6.0, 0.04], "*|stop": [4.5, 0.07]}


def _minute(days, day_path=None, n=390, day=None):
    """Flat 1-minute SPY sessions (range 2.0 a day -> ATR14 = 2.0); `day` gets `day_path` (n bars from 09:30)."""
    out = []
    for d in days:
        idx = pd.date_range(f"{d} 09:30", periods=390, freq="1min", tz="America/New_York")
        c = np.full(390, 600.0)
        f = pd.DataFrame({"open": c, "high": c + 1.0, "low": c - 1.0, "close": c}, index=idx)
        out.append(f)
    if day is not None:
        c = np.asarray(day_path, float)
        o = np.r_[c[0], c[:-1]]
        idx = pd.date_range(f"{day} 09:30", periods=len(c), freq="1min", tz="America/New_York")
        out.append(pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.01, "low": np.minimum(o, c) - 0.01,
                                 "close": c}, index=idx))
    return pd.concat(out)


def _daily(days, spy_mtd, tlt_mtd, base):
    """SPY/TLT closes: 100 on `base`, then the MTD move reached on the last listed day."""
    idx = [base] + list(days)
    return pd.DataFrame({"SPY": [100.0] + [100 * (1 + spy_mtd)] * len(days),
                         "TLT": [100.0] + [100 * (1 + tlt_mtd)] * len(days)}, index=idx)


PRIOR = [str(d.date()) for d in pd.bdate_range("2026-10-08", "2026-10-29")]   # 16 sessions before 10-30


def test_month_end_calendar():
    assert S.is_month_end("2026-10-30") and not S.is_month_end("2026-10-29")
    assert S.is_month_end("2026-11-30") and not S.is_month_end("2026-11-27")   # Nov 2026: Mon 11-30, not a half day
    assert S.is_month_end("2025-11-28")                                         # a half-day month-end
    assert S.is_month_end("2026-12-31") and not S.is_month_end("2026-12-25")
    with pytest.raises(RuntimeError):
        S.is_month_end("2028-01-31")                                            # calendar list ends 2027


def test_signal_long_trade_exit_1555_and_costs():
    p = np.full(390, 600.0)
    p[270:] = np.linspace(600, 601, 120)          # drifts up from 14:00
    day = "2026-10-30"
    r = S.evaluate(day, _daily(PRIOR, 0.01, 0.03, "2026-09-30"), _minute(PRIOR, p, day=day), CELLS, close_m=960)
    assert r["signal"] == "yes" and abs(r["S_pct"] + 2.0) < 1e-6
    assert r["base_date"] == "2026-09-30" and r["prev_date"] == "2026-10-29"
    assert abs(r["atr14"] - 2.02) < 0.05 and r["entry_time"] == "14:00" and r["exit_time"] == "15:55"
    assert r["kind"] == "market" and r["R_gross"] > 0 and r["R_livel"] < r["R_gross"]
    risk = r["entry"] - r["stop"]
    c_l, c_8, _ = S.costs(r["entry"], r["exit"], risk, 0, 1400, CELLS)
    assert abs(r["R_livel"] - (r["R_gross"] - c_l)) < 1e-3 and abs(r["R_lr8"] - (r["R_gross"] - c_8)) < 1e-3
    assert r["R_s12"] != "" and r["R_s12"] < r["R_livel"]
    assert r["status"].startswith("done (seed")                     # before 2026-11-30: never scored


def test_stop_and_no_signal_control():
    p = np.full(390, 600.0)
    p[280:] = 598.0                                # falls through 0.25 x ATR after entry
    day = "2026-10-30"
    r = S.evaluate(day, _daily(PRIOR, 0.01, 0.03, "2026-09-30"), _minute(PRIOR, p, day=day), CELLS, close_m=960)
    assert r["kind"] == "stop" and r["R_gross"] <= -1.0
    c = S.evaluate(day, _daily(PRIOR, 0.03, 0.01, "2026-09-30"), _minute(PRIOR, p, day=day), CELLS, close_m=960)
    assert c["signal"] == "no" and c["R_livel"] == "" and c["ctrl_R_livel"] != ""


@pytest.mark.parametrize("day", ["2025-11-28"])
def test_half_day_month_end_no_trade_after_hours_ignored(day):
    prior = [str(d.date()) for d in pd.bdate_range("2025-11-05", "2025-11-26") if str(d.date()) != "2025-11-27"]
    p = np.full(390, 600.0)
    p[210:] = 630.0                                # after-hours prints 13:00-16:00 must never be traded
    r = S.evaluate(day, _daily(prior, -0.01, 0.01, "2025-10-31"), _minute(prior, p, day=day), CELLS)
    assert r["signal"] == "yes" and r["entry"] == "" and r["status"].startswith("no trade: half day")


def test_run_only_on_month_end_idempotent_and_lock(tmp_path):
    out = tmp_path / "f.csv"
    p = np.full(390, 600.0)
    data = (_daily(PRIOR, 0.01, 0.03, "2026-09-30"), _minute(PRIOR, p, day="2026-10-30"))
    assert S.run("2026-10-29", out, data) is None and not out.exists()
    S.run("2026-10-30", out, data)
    S.run("2026-10-30", out, data)
    assert len(pd.read_csv(out)) == 1
    assert S.score(out)["signal_trades"] == 0      # the seed row is in-sample, not scored
    with pytest.raises(AssertionError):
        S.run("2024-11-29", out, data)
