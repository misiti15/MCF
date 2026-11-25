"""WT1 wide-target forward shadow (research/forward/wide_target, frozen 2026-11-25): synthetic lots. Educational only."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

P = Path(__file__).resolve().parents[1] / "research" / "forward" / "wide_target" / "shadow.py"
spec = importlib.util.spec_from_file_location("wide_target_shadow", P)
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def _bars(path, day="2026-11-24"):
    c = np.asarray(path, dtype=float)
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range(f"{day} 09:30", periods=len(c), freq="1min", tz="America/New_York")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + 0.01, "low": np.minimum(o, c) - 0.01, "close": c},
                        index=idx)


def test_family_and_wide_target():
    assert S.family_of("RW3-gapdn-rsi5pop-flowsell-short-FD") == "RW3"
    assert S.family_of("RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-RQa-1230") == "RW5"
    assert S.family_of("RW3S-gapdn-flowsell-short-FD") is None
    # short: signal 100, stop 101, target 99 -> wide 98.75 (1.25 x the 1.00 distance)
    assert abs(S.wide_target(101.0, 99.0, -1) - 98.75) < 1e-9
    assert abs(S.wide_target(99.0, 101.0, 1) - 101.25) < 1e-9


def test_walk_target_flatten_stop():
    fill = 60.0                                                     # live target filled in the 10:30 bar
    down = np.r_[np.full(61, 99.0), np.linspace(99.0, 98.0, 40), np.full(289, 98.0)]
    assert S.walk(_bars(down), -1, 101.0, 98.75, fill)[1] == "target"
    flat = np.r_[np.full(61, 99.0), np.full(329, 99.2)]
    px, why, m = S.walk(_bars(flat), -1, 101.0, 98.75, fill)
    assert why == "flatten" and m == S.FLAT_MIN
    up = np.r_[np.full(61, 99.0), np.linspace(99.0, 101.5, 30), np.full(299, 101.5)]
    assert S.walk(_bars(up), -1, 101.0, 98.75, fill)[1] == "stop"
    spy = _bars(np.r_[np.full(70, 600.0), np.full(320, 603.0)])     # SPY +0.5% after 10:40
    assert S.walk(_bars(flat), -1, 101.0, 98.75, fill, spy, 600.0, 0.40)[1] == "spy_exit"


def test_dups_and_score(tmp_path):
    t0 = pd.Timestamp("2026-11-24 10:00", tz="America/New_York")
    tr = pd.DataFrame({"account": ["primary", "primary", "testing2", "testing2"],
                       "strategy": ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
                                    "RW3-gapdn-rsi5pop-flowsell-short-FD-RQa-1230",
                                    "RW3-gapdn-rsi5pop-flowsell-short-FD-RQa-1230"],
                       "symbol": ["ABC", "ABC", "ABC", "XYZ"], "side": [-1, -1, -1, -1],
                       "sig": [t0, t0, t0 + pd.Timedelta(minutes=2), t0]})
    assert S.mark_dups(tr) == [0, 0, 1, 0]
    rows = []
    for i in range(22):
        d = f"2026-12-{i + 1:02d}"
        for j, fam in enumerate(["RW3", "RW5", "RW3"]):
            rows.append(dict(date=d, account="primary", family=fam, R_parent=1.0, R_wide=1.0 + 0.05 * (j + 1),
                             dR=0.05 * (j + 1) + 0.001 * i, live_reason="target", wide_reason="target",
                             status="done", dup=0))
    pd.DataFrame(rows).to_csv(tmp_path / "f.csv", index=False)
    pd.DataFrame({"date": [r["date"] for r in rows[::3]], "status": "done"}).to_csv(tmp_path / "d.csv", index=False)
    out = S.score("2026-12-01", path=tmp_path / "f.csv", days_path=tmp_path / "d.csv")
    assert out["sessions"] == 22 and out["trades"] == 66
    assert all(out["pass_checks"].values()) and out["verdict"].startswith("PASS")
