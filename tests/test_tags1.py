"""TAGS1 (owner yes 2026-11-18): journal-only would-skip tags - point-in-time conditions and the frozen rules on a
synthetic session; the scorer refuses before 20 fresh sessions. Educational only - not financial advice."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _mod(name):
    spec = importlib.util.spec_from_file_location(f"tags1_{name}", ROOT / "research/tags1" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


T = _mod("tags1")
DAY = "2026-11-19"


def _bars():
    t0 = pd.Timestamp(f"{DAY} 09:30", tz="America/New_York").tz_convert("UTC")
    rows = []
    for k in range(120):
        ts = t0 + pd.Timedelta(minutes=k)
        rows.append(dict(symbol="SPY", ts=ts, open=600.0, high=600.5, low=599.5, close=600.0 + (0.5 if k > 60 else 0.1), volume=1e5))
        rows.append(dict(symbol="AAA", ts=ts, open=52.0, high=52.2, low=51.8, close=52.0 - k * 0.01, volume=1e4))
    return pd.DataFrame(rows)


def _daily():
    days = pd.bdate_range("2026-10-01", DAY, tz="America/New_York")
    rows = []
    for i, d in enumerate(days):
        for s, px in (("SPY", 600.0), ("AAA", 50.0)):
            rows.append(dict(symbol=s, ts=d.tz_convert("UTC"), open=px, high=px * 1.01, low=px * 0.99, close=px, volume=1e6))
    return pd.DataFrame(rows)


def _dec():
    base = dict(symbol="AAA", date=DAY, entry=52.0, stop=52.5, shares=10, pnl=1.0, pnl_adj=0.8, r_multiple=0.2,
                exit_reason="target", run_id=1, source="live")
    return pd.DataFrame([
        {**base, "id": 1, "acct": "primary", "strategy": "MF2-open-rsimidhi-flowsell-FD", "side": -1,
         "signal_time": f"{DAY}T10:00:00-05:00", "entry_time": f"{DAY}T10:00:30-05:00", "exit_time": f"{DAY}T11:30:00-05:00"},
        {**base, "id": 2, "acct": "primary", "strategy": "RW3-gapdn-rsi5pop-flowsell-short-FD", "side": -1,
         "signal_time": f"{DAY}T10:30:00-05:00", "entry_time": f"{DAY}T10:30:30-05:00", "exit_time": f"{DAY}T11:00:00-05:00"},
        {**base, "id": 3, "acct": "testing2", "strategy": "L3-gap-slope-fromopen-FD", "side": -1,
         "signal_time": f"{DAY}T10:40:00-05:00", "entry_time": f"{DAY}T10:40:30-05:00", "exit_time": f"{DAY}T11:00:00-05:00"},
    ])


def test_conditions_are_point_in_time_and_rules_fire():
    out = T.build(_dec(), _bars(), _daily(), DAY)
    assert len(out) == 3 and {"tod", "gap", "spy_now", "vwap", "or30", "FLAT25", "MFGAP", "STACK1_L3X"} <= set(out)
    r1 = out[out.id == 1].iloc[0]
    assert r1.tod == pytest.approx(30.0) and r1.gap == pytest.approx(4.0)        # open 52 vs prior close 50
    assert r1.MFGAP and r1.FLAT25                                               # MF short on a +4% gap; SPY +0.02% at 10:00
    r2 = out[out.id == 2].iloc[0]
    assert r2.STACK1_L3X                                                        # MF2 Primary lot still open on AAA at 10:30
    assert not out[out.id == 3].iloc[0].FLAT25                                  # Primary scope only
    # point-in-time: changing a bar AFTER the 10:00 signal does not change row 1's conditions
    b = _bars()
    b.loc[(b.symbol == "AAA") & (b.ts > pd.Timestamp(f"{DAY} 10:00", tz="America/New_York")), "close"] = 99.0
    r1b = T.build(_dec(), b, _daily(), DAY).query("id == 1").iloc[0]
    assert r1b.price == pytest.approx(r1.price) and r1b.vwap == pytest.approx(r1.vwap)


def test_rules_are_frozen_and_scorer_refuses_early(tmp_path):
    r = json.loads((ROOT / "research/tags1/rules.json").read_text())
    assert r["frozen"] == "2026-11-18" and r["sessions_to_score"] == 20 and r["score_on_or_after"] == "2026-12-17"
    assert set(r["rules"]) == {"FLAT25", "STACK1_L3X", "MFGAP", "W4_HFL_VWAP", "W4_NS3_PDAY", "W4_L3_PM", "W4_RW3_GAP2"}
    S = _mod("score")
    T.build(_dec(), _bars(), _daily(), DAY).to_csv(tmp_path / f"{DAY}.csv.gz", index=False)
    with pytest.raises(SystemExit):
        S.main(["--tags", str(tmp_path)])
    res = S.score(S.load(tmp_path))                                             # the function itself works on the frame
    assert res["MFGAP"]["n"] == 1
