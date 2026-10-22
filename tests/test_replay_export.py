"""Replay dashboard data (python -m mcf.replay export): replay.json + pipeline.json from run folders, live journals,
configs and backtest expectations. Educational only - not financial advice."""

import json

import pandas as pd

from mcf.replay import export


def _run(root, label, account, rows, as_live=False, setup=None):
    acct = root / label / account
    for day, rs in rows.items():
        d = acct / day
        d.mkdir(parents=True)
        pd.DataFrame(rs, columns=["strategy", "r_multiple"]).assign(symbol="X").to_csv(d / "trades.csv.gz", index=False)
        pd.DataFrame({"strategy": [r[0] for r in rs], "status": "submitted"}).to_csv(d / "signals.csv.gz", index=False)
        (d / "stats.json").write_text("{}")
    (root / label / f"{account}-run.json").write_text(json.dumps(
        {"label": label, "account": account, "fills": "costs", "limit_fill": "through", "as_live": as_live,
         "setup": setup}))


def test_setup_stats_day_clustered_t():
    t = pd.DataFrame({"r_multiple": [1.0, -0.5, 1.0, 0.5, -1.0, 1.0], "session": ["a", "a", "b", "b", "c", "c"]})
    s = export.setup_stats(t)
    assert s["trades"] == 6 and s["sessions"] == 3 and s["total_r"] == 2.0
    assert s["win_rate"] == round(4 / 6, 3) and s["avg_r"] == round(1 / 3, 3)
    per = pd.Series([0.5, 1.5, 0.0])
    assert s["t"] == round(per.mean() / (per.std(ddof=1) / 3 ** 0.5), 2)
    assert export.setup_stats(t.iloc[:0])["trades"] == 0


def test_export_writes_replay_and_pipeline(tmp_path):
    runs = tmp_path / "runs"
    _run(runs, "t2-live", "testing2", {"2026-10-14": [("A", 1.0), ("B", -1.0)], "2026-10-15": [("A", -0.5)]},
         as_live=True)
    _run(runs, "new-setup", "testing2", {"2026-09-01": [("NEW", 0.4)], "2026-09-02": [("NEW", 0.2)]}, setup="NEW")
    live = pd.DataFrame({"strategy": ["A", "A", "B"], "date": ["2026-10-14", "2026-10-15", "2026-10-14"],
                         "r_multiple": [0.9, -0.6, -1.0], "account": "testing2", "symbol": "X"})
    out = tmp_path / "docs"
    p1, p2 = export.export(runs, out, live=live, enabled={"A": ["testing2"], "B": ["testing2"]},
                           expected={"NEW": 0.05, "OLD": 0.1}, universe={"X"})
    rep = json.loads(p1.read_text())
    assert set(rep["setups"]) == {"A", "B", "NEW"} and "generated" in rep
    a = rep["setups"]["A"]
    assert {"date", "sessions", "trades", "win_rate", "avg_r", "t", "total_r"} <= set(a)
    assert a["sessions"] == 2 and a["trades"] == 2 and a["date"] == "2026-10-15"
    assert rep["system_agreement"]["testing2"]["replay_trades"] == 3
    pipe = json.loads(p2.read_text())
    assert pipe["A"]["stage"] == "live" and pipe["NEW"]["stage"] == "replay" and pipe["OLD"]["stage"] == "backtest"
    assert pipe["NEW"]["backtest"] == {"expected_r": 0.05} and pipe["NEW"]["replay"]["trades"] == 2
    assert pipe["A"]["live"]["trades"] == 2 and pipe["A"]["agreement"]["testing2"]["live_trades"] == 2
    assert all(not k.startswith("_") for k in pipe)
