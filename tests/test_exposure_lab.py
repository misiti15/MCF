"""Exposure Lab (owner 2026-11-09): set, runs, metrics. Pure functions only (no market data). Educational only - not
financial advice."""
import pandas as pd

from mcf.report import exposure_lab as X

D = "2026-11-09"


def _t(sym, strat, side, en, ex, entry, stop, r, shares=100):
    return {"symbol": sym, "strategy": strat, "side": side, "entry_time": f"{D} {en}-05:00",
            "exit_time": f"{D} {ex}-05:00", "entry": entry, "stop": stop, "shares": shares, "r": r}


def test_set_and_books():
    assert len(X.SETUPS) == 26 and sum(s.startswith("GEN-") for s in X.SETUPS) == 8
    assert set(X.PV0) | set(X.PV_BOOKS["PV2"]) <= set(X.SETUPS)
    assert len(X.PV_BOOKS["PV1"]) == 7 and "MF4-h40-open-flowsell" not in X.PV_BOOKS["PV1"]
    assert "NM-ETF-late-dip-di-long" in X.PV_BOOKS["PV2"] and "L3-gap-slope-rsi5hi-FD" not in X.PV_BOOKS["PV2"]
    r = X.runs()
    assert len(r) == 26 + 1 + 3 and r["together"] == list(X.SETUPS)


def test_r_path_and_drawdown():
    g = X.grid(D)
    idx = pd.date_range(f"{D} 09:30", f"{D} 15:59", freq="1min", tz=X.NY)
    closes = {"AAA": pd.Series(10.0, index=idx)}
    closes["AAA"].loc[f"{D} 10:00":f"{D} 10:30"] = 9.0          # long goes 1R under water, then recovers
    t = _t("AAA", "s", 1, "09:50:00", "11:00:00", 10.0, 9.0, 0.5)
    p = X.r_path([t], closes, g)
    assert p.loc[f"{D} 09:45"] == 0 and p.loc[f"{D} 10:15"] == -1.0 and p.iloc[-1] == 0.5
    s = X.book_stats([t], p)
    assert s["r"] == 0.5 and s["green"] and s["worst_intraday_dd_r"] == -1.0


def test_overlaps_and_pairwise():
    a = [_t("AAA", "a", -1, "10:00:00", "10:30:00", 10, 10.5, 1.0)]
    b = [_t("AAA", "b", 1, "10:15:00", "10:45:00", 10, 9.5, -1.0), _t("AAA", "b", -1, "11:00:00", "11:10:00", 10, 10.5, 0.2)]
    assert X.overlaps(a, b) == (1, 1)
    g = X.grid(D)
    paths = {"a": X.r_path(a, {}, g), "b": X.r_path(b, {}, g)}
    rows = X.pairwise({"a": a, "b": b}, paths)
    assert rows[0]["same_symbol_overlaps"] == 1 and rows[0]["opposite_side"] == 1


def test_crowding_diff():
    s = next(iter(X.SETUPS))
    rows = X.crowding({s: {"trades": 5, "r": 2.0}}, {"per_setup": {s: {"trades": 3, "r": 0.5}}}, {s: {"held_by_other": 2}})
    row = next(r for r in rows if r["id"] == s)
    assert row["diff_trades"] == -2 and row["diff_r"] == -1.5 and row["together_skips"] == {"held_by_other": 2}
