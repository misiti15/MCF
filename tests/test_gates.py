"""Tests for mcf/research/gates.py (rule 19 gates). Educational only - not financial advice."""
import math
from datetime import date, timedelta

import numpy as np
import pandas as pd

from mcf.research import gates as G


def _days(n, start=date(2025, 3, 3)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def test_t_required_grows_with_tries():
    assert G.t_required(1) == 1.5
    assert G.t_required(3) == 1.5                       # sqrt(2 ln 3) = 1.48 < floor
    assert G.t_required(1000) == round(math.sqrt(2 * math.log(1000)), 3)
    assert G.t_required(855_600) > G.t_required(7_374) > G.t_required(100)


def test_prod_r_charges_more_than_lab():
    # target win: entry side cost only; stop: both sides + 2c; R = 0.25 x 4 = $1
    r = G.prod_r([1.0 - 0.02, -1.0 - 0.02], [1, 0], [100.0, 100.0], [4.0, 4.0], "t1s1")
    assert np.isclose(r[0], 1.0 - (0.01 + 0.01))                  # 1c + 1bps of $100
    assert np.isclose(r[1], -1.0 - (0.02 + 0.02 + 0.02))           # both sides + stop extra
    # timed exit (not a stop, not a target): both sides, no stop extra
    r2 = G.prod_r([0.3 - 0.02], [0], [100.0], [4.0], "t1s1")
    assert np.isclose(r2[0], 0.3 - 0.04)


def test_lab_trades_first_bar_per_symbol_day():
    df = pd.DataFrame({"symbol": ["A", "A", "A", "B"], "date": [date(2025, 3, 3)] * 3 + [date(2025, 3, 3)],
                       "tod": [950, 955, 1000, 950], "close": [10.0] * 4, "atr_d": [1.0] * 4,
                       "r_short_t1s1": [0.98, -1.02, 0.5, -1.02], "win_short_t1s1": [1, 0, 0, 0]})
    t = G.lab_trades(df, [False, True, True, True], "short", "t1s1")
    assert list(t.tod) == [955, 950] and list(t.symbol) == ["A", "B"]


def test_summary_day_clustered_t():
    t = pd.DataFrame({"date": [date(2025, 3, 3)] * 2 + [date(2025, 3, 4)] * 2, "r": [1.0, 1.0, -1.0, 0.0]})
    s = G.summary(t)
    assert s["n"] == 4 and s["days"] == 2 and s["exp_r"] == 0.25
    # day sums 2 and -1, mean .25 -> residuals 2-.5=1.5, -1-.5=-1.5 -> se = sqrt(4.5)/4
    assert np.isclose(s["se"], round(math.sqrt(4.5) / 4, 4))


def test_session_regimes_terciles_and_exclusion():
    days = _days(9)
    rows = []
    for i, d in enumerate(days):
        for s in range(5):
            rows.append({"date": d, "symbol": f"S{s}", "open": 100.0, "close": 100.0 + (i - 4)})
    reg = G.session_regimes(pd.DataFrame(rows))
    assert list(reg.regime[:3]) == ["down"] * 3 and list(reg.regime[-3:]) == ["up"] * 3
    assert (reg.regime == "flat").sum() == 3
    # cut points from the first 3 days only (all negative): everything later is "up"
    reg2 = G.session_regimes(pd.DataFrame(rows), dates=days[:3])
    assert (reg2.regime[3:] == "up").all()


def test_regime_split_requires_up_and_down():
    days = _days(90)
    reg = pd.DataFrame({"regime": (["up", "flat", "down"] * 30)}, index=days)
    # positive in up, negative in down -> fails
    r = [0.2 if reg.regime[d] == "up" else -0.2 for d in days]
    t = pd.DataFrame({"date": days, "r": r})
    out = G.regime_split(t, reg, min_n=10)
    assert out["up"]["exp_r"] > 0 and out["down"]["exp_r"] < 0 and not out["pass"]
    t2 = pd.DataFrame({"date": days, "r": [0.1] * 90})
    assert G.regime_split(t2, reg, min_n=10)["pass"]
    assert not G.regime_split(t2, reg, min_n=31)["pass"]     # too few trades per regime


def test_walk_forward_folds_and_exclusion():
    days = pd.bdate_range("2025-01-01", "2025-12-31").date
    month = pd.PeriodIndex(pd.to_datetime(days), freq="M")
    r = np.where(month.month % 2 == 0, 0.1, -0.1)          # even months positive
    t = pd.DataFrame({"date": days, "r": r})
    wf = G.walk_forward(t, min_n=5)
    assert wf["n_folds"] == 9                               # 12 months - 3 train
    assert wf["share_positive"] == round(sum(1 for f in wf["folds"] if f["test_exp"] > 0) / 9, 3)
    assert {f["test"] for f in wf["folds"]} == {f"2025-{m:02d}" for m in range(4, 13)}
    wf2 = G.walk_forward(t, min_n=5, exclude_months=["2025-06"])
    assert all(f["test"] not in ("2025-06", "2025-07", "2025-08", "2025-09") for f in wf2["folds"])
    assert wf2["n_folds"] == 5


def test_walk_forward_skips_gaps_in_months():
    days = [d for d in pd.bdate_range("2025-01-01", "2025-08-31").date if d.month != 5]
    t = pd.DataFrame({"date": days, "r": [0.1] * len(days)})
    wf = G.walk_forward(t, min_n=5)                         # May missing: no fold may span it
    assert {f["test"] for f in wf["folds"]} == {"2025-04"}


def test_deflated_sharpe_penalises_tries():
    rng = np.random.default_rng(0)
    x = rng.normal(0.1, 1.0, 500)
    a, b = G.deflated_sharpe(x, 1), G.deflated_sharpe(x, 100_000)
    assert a["sr0"] < b["sr0"] and a["dsr"] > b["dsr"]


def test_verdict():
    ok = {"n": 500, "exp_r": 0.1, "t": 6.0}
    reg = {"up": {"n": 100, "exp_r": 0.1, "t": 3}, "down": {"n": 100, "exp_r": 0.1, "t": 3}, "pass": True}
    wf = {"share_positive": 0.7}
    assert G.verdict(ok, reg, wf, 1000)[0] == "keep"
    assert G.verdict({**ok, "t": 2.0}, reg, wf, 1000)[0] == "rework"
    bad = {"n": 500, "exp_r": -0.05, "t": -2.0}
    reg_bad = {"up": {"n": 100, "exp_r": -0.1, "t": -3}, "down": {"n": 100, "exp_r": 0.02, "t": 0.5}, "pass": False}
    assert G.verdict(bad, reg_bad, {"share_positive": 0.3}, 1000)[0] == "retire"
    reg_rescue = {**reg_bad, "down": {"n": 100, "exp_r": 0.15, "t": 2.5}}
    assert G.verdict(bad, reg_rescue, {"share_positive": 0.3}, 1000)[0] == "rework"


def test_time_of_day_entry_costs():
    import numpy as np

    from mcf.research.gates import prod_r, tod_cost_mult

    assert list(tod_cost_mult([930, 940, 1000, 1100, 1455])) == [3.8, 2.1, 1.4, 1.0, 1.0]
    a = prod_r([0.5], [1], [50.0], [2.0], "t1s1")
    b = prod_r([0.5], [1], [50.0], [2.0], "t1s1", tod=[1100])
    c = prod_r([0.5], [1], [50.0], [2.0], "t1s1", tod=[950])
    assert np.isclose(a, b).all() and (c < b).all()
