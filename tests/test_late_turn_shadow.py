"""Late-turn forward shadow (research/forward/late_turn, frozen 2026-11-16): synthetic sessions. Educational only."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

P = Path(__file__).resolve().parents[1] / "research" / "forward" / "late_turn" / "shadow.py"
spec = importlib.util.spec_from_file_location("late_turn_shadow", P)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def _bars(path, day="2026-11-17", n=390):
    """1-minute bars from a close path (open = previous close, high/low +-0.01%)."""
    c = np.asarray(path[:n], dtype=float)
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=len(c), freq="1min", tz="America/New_York")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0001, "low": np.minimum(o, c) * 0.9999,
                         "close": c, "volume": 1000.0}, index=idx)


def _late_turn_path(after=0.001):
    """SPY flat 600 to 10:55, a 0.3% dip to 11:05, back above the 10:55 price by 11:20, then drifts by `after`."""
    p = np.full(390, 600.0)
    p[85:95] = np.linspace(600.0, 598.2, 10)       # 10:55-11:04 new low ~30 bps under the 09:50 price
    p[95:110] = np.linspace(598.2, 600.6, 15)      # reclaim by the 11:19 bar close
    p[110:] = 600.6 * (1 + np.linspace(0, after, 280))
    return p


def test_signal_and_R_after_costs():
    spy = _late_turn_path(0.002)
    spxl = 150 * (1 + 3 * (spy / spy[0] - 1))
    out = S.evaluate(S.grid(_bars(spy)), S.grid(_bars(spxl)))
    assert out["setup"] == "yes" and out["signal_time"] == "11:20" and out["status"] == "done"
    assert out["exit_time"] == "12:50" and out["stopped"] is False
    ent, ex = out["entry"], out["exit"]
    cost = 0.02 + 1e-4 * (ent + ex)
    assert abs(out["R_after_costs"] - (ex - ent - cost) / (ent - out["stop"])) < 1e-3
    assert out["R_after_costs"] > 0


def test_stop_out_and_no_setup_days():
    spy = _late_turn_path(0.0)
    spy[120:] = 595.0                                   # collapses after entry
    spxl = 150 * (1 + 3 * (spy / spy[0] - 1))
    out = S.evaluate(S.grid(_bars(spy)), S.grid(_bars(spxl)))
    assert out["setup"] == "yes" and out["stopped"] is True and out["R_after_costs"] < -1
    flat = np.full(390, 600.0)
    assert S.evaluate(S.grid(_bars(flat)), S.grid(_bars(flat / 4)))["setup"] == "no"
    early = flat.copy(); early[30:40] = 590.0           # the low is at 10:00-10:10: no new low in the window
    assert "no new" in S.evaluate(S.grid(_bars(early)), None)["status"]


def test_pending_before_exit_and_idempotent_upsert(tmp_path):
    spy = _late_turn_path(0.002)
    spxl = 150 * (1 + 3 * (spy / spy[0] - 1))
    part = S.evaluate(S.grid(_bars(spy, n=150)), S.grid(_bars(spxl, n=150)))   # data only to 12:00
    assert part["setup"] == "yes" and part["status"].startswith("pending")
    f = tmp_path / "forward.csv"
    S.upsert({"date": "2026-11-17", **part}, f)
    S.upsert({"date": "2026-11-17", **S.evaluate(S.grid(_bars(spy)), S.grid(_bars(spxl)))}, f)
    S.upsert({"date": "2026-11-16", "setup": "no", "status": "no setup"}, f)
    d = pd.read_csv(f)
    assert list(d.date) == ["2026-11-16", "2026-11-17"] and d.status.iloc[1] == "done"
