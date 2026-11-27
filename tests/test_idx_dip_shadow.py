"""Index open-dip forward shadow (research/forward/idx_dip, frozen 2026-11-27): synthetic sessions. Educational only."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

P = Path(__file__).resolve().parents[1] / "research" / "forward" / "idx_dip" / "shadow.py"
spec = importlib.util.spec_from_file_location("idx_dip_shadow", P)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
CELLS = {"*|market": [6.0, 0.04], "*|stop": [4.5, 0.07], "*|target": [2.0, 0.09]}


def _bars(path, day="2026-11-17"):
    c = np.asarray(path, dtype=float)
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=len(c), freq="1min", tz="America/New_York")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0001, "low": np.minimum(o, c) * 0.9999,
                         "close": c, "volume": 1000.0}, index=idx)


def _dip_day(depth=0.02, after=0.03, n=390):
    """QQQ falls `depth` by 09:45, bounces by 09:52, then drifts up by `after` over the day."""
    p = np.full(n, 600.0)
    p[0:15] = np.linspace(600, 600 * (1 - depth), 15)
    p[15:22] = np.linspace(600 * (1 - depth), 600 * (1 - depth / 2), 7)
    p[22:] = 600 * (1 - depth / 2) * (1 + np.linspace(0, after, n - 22))
    return p


def _lev(p, base=50.0):
    return base * (1 + 3 * (p / p[0] - 1))


def test_idx6_signal_trail_and_costs():
    q = _dip_day()
    out = S.evaluate(_bars(q), _bars(_lev(q)), "IDX6", CELLS)
    assert out["signal"] == "yes" and out["status"] == "done"
    assert out["trigger_time"] == "09:50" and out["entry_time"] == "09:50"
    assert out["R_gross"] > 1 and out["R_livel"] < out["R_gross"]
    risk = out["entry"] - out["stop"]
    c_l, _, _ = S.costs(out["entry"], out["exit"], risk, {"market": 0, "stop": 1}[out["kind"]], 950, CELLS)
    assert abs(out["R_livel"] - (out["R_gross"] - c_l)) < 1e-3
    assert out["R_s12"] != ""


def test_no_signal_shallow_dip_and_iwm_window():
    q = _dip_day(depth=0.01)                       # 1% < 1.5% for IDX6
    assert S.evaluate(_bars(q), _bars(_lev(q)), "IDX6", CELLS)["signal"] == "no"
    out = S.evaluate(_bars(q), _bars(_lev(q)), "IWM45", CELLS)   # 1% >= 0.75% by 09:45 -> IWM45 fires
    assert out["signal"] == "yes" and out["status"] == "done"


def test_half_day_flat_at_close_minus_5():
    q = _dip_day(after=0.0, n=210)                 # 13:00 close
    out = S.evaluate(_bars(q), _bars(_lev(q)), "IDX6", CELLS)
    assert out["status"] == "done" and out["exit_time"] == "12:55" and out["kind"] == "market"


def test_idempotent_upsert_score_and_lock(tmp_path):
    q = _dip_day()
    bars = {"QQQ": _bars(q, "2026-11-17"), "TQQQ": _bars(_lev(q), "2026-11-17"),
            "IWM": _bars(q / 3, "2026-11-17"), "TNA": _bars(_lev(q, 40), "2026-11-17")}
    f = tmp_path / "forward.csv"
    S.run("2026-11-17", f, bars)
    S.run("2026-11-17", f, bars)
    S.run("2026-11-18", f, {})
    d = pd.read_csv(f)
    assert len(d) == 4 and list(d.date.unique()) == ["2026-11-17", "2026-11-18"]
    sc = S.score(f)
    assert sc["book_livel"]["days"] == 1 and sc["verdict"].startswith("WAITING")
    with pytest.raises(AssertionError):
        S.run("2024-12-02", f, {})
