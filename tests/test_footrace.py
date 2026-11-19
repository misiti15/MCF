"""FOOTRACE (owner 2026-11-19): the stricter arena exit (FOOTRACE-EXIT, replaces the EXIT100 thresholds), the GY-LIFE
archive pick (up to 4, Compass exemptions kept) and the Graveyard foot race (15 leaders, whole-session rotation for the
rest, >= 1 session in 3, stale / missing plan -> every setup plays). Educational only - not financial advice."""
import json
from datetime import date

import pandas as pd
import yaml

from mcf.report import footrace as F

ROOT = F.ROOT


def _row(**k):
    r = {"n": 40, "avg_r": -0.10, "wo_avg_r": -0.12, "t_day": -2.0}
    r.update(k)
    return r


REPS = {"active_days": 20, "signals": 100}


def test_exit_thresholds():
    assert F.exit_flag(_row(), REPS)
    assert not F.exit_flag(_row(), {"active_days": 14, "signals": 100})            # < 15 active days
    assert not F.exit_flag(_row(n=29), REPS)                                         # < 30 trades
    assert not F.exit_flag(_row(avg_r=0.01), REPS)                                   # avg R > 0
    assert not F.exit_flag(_row(wo_avg_r=0.01), REPS)                                # w/o best day > 0
    assert not F.exit_flag(_row(t_day=-1.49), REPS)                                  # no clear losing streak
    assert F.exit_flag(_row(t_day=-1.5, avg_r=0.0, wo_avg_r=0.0), REPS)              # boundaries included
    assert not F.exit_flag(_row(), {"active_days": 20, "signals": 9})                # rare / day-gated
    assert not F.exit_flag(_row(), REPS, exempt=True)
    assert not F.exit_flag(_row(), None)
    # the old EXIT100 numbers are no longer needed: 40 trades is enough, and avg -0.30 with t -1.0 is not
    assert not F.exit_flag(_row(n=150, avg_r=-0.30, wo_avg_r=-0.30, t_day=-1.0), REPS)


def _trades(spec):
    rows = []
    for s, days in spec.items():
        for i, rs in enumerate(days):
            rows += [{"strategy": s, "date": f"2026-11-{i + 1:02d}", "r": r, "account": "testingf"} for r in rs]
    return pd.DataFrame(rows)


def test_stats_and_exit_review_exemptions():
    bad = [[-0.5, -0.4, 0.1]] * 12 + [[-0.3, 0.2, -0.2]] * 8
    t = F.setup_stats(_trades({"X-long": bad, "ULT-14-snap-long": bad, "Y-long-WB3": bad}))
    assert t.loc["X-long", "n"] == 60 and t.loc["X-long", "t_day"] < -1.5
    reps = {k: {"active_days": 20, "signals": 80} for k in t.index}
    reps["Y-long-WB3"] = {"active_days": 14, "signals": 80}
    out = F.exit_review(t, {k: "testingf" for k in t.index}, reps)
    assert [x["setup"] for x in out] == ["X-long"]          # 11-20 admissions and young Workbench copies untouched


def test_one_day_tag_and_wo_best_day():
    t = F.setup_stats(_trades({"A": [[10.0], [-1.0], [-1.0]]}))
    assert t.loc["A", "wo_total_r"] == -2.0 and bool(t.loc["A", "one_day"]) and t.loc["A", "best_share"] > 1


def _plan_inputs(n_good=20, n_bad=20):
    spec = {f"G{i:02d}": [[0.2 + i * 0.01] * 3] * 10 for i in range(n_good)}
    spec.update({f"B{i:02d}": [[-0.2 - i * 0.01] * 3] * 10 for i in range(n_bad)})
    spec["LOWREP"] = [[-1.0]] * 5
    t = F.setup_stats(_trades(spec))
    return list(t.index), t


def test_gy_leaders_and_rotation_min_one_in_three():
    members, t = _plan_inputs()
    load = {m: 10.0 for m in members}
    sessions = ["2026-11-20", "2026-11-23", "2026-11-24", "2026-11-25", "2026-11-27"]
    p = F.gy_plan(members + ["NEW"], t, load, sessions, slots=300)
    assert p["leaders"] == [f"G{i:02d}" for i in range(19, 4, -1)]       # top 15 by score
    assert "LOWREP" in p["always"] and "NEW" in p["always"]               # low-rep / new setups always play
    assert set(p["rotation"]) == {f"G{i:02d}" for i in range(5)} | {f"B{i:02d}" for i in range(20)}
    line = F.GY_SLOT_LINE * 300
    for d in sessions:
        play = set(p["schedule"][d])
        assert p["estimate"][d]["est_peak_lots"] <= line + 1e-9
        assert p["estimate"][d]["benched"] > 0
    for k in p["rotation"]:                                                # never benched 3 sessions in a row
        run = 0
        for d in sessions:
            run = 0 if k in p["schedule"][d] else run + 1
            assert run <= F.GY_MAX_BENCH_RUN, (k, d)
    # a very tight Graveyard still gives every rotating setup >= 1 session in 3 (the slot line yields)
    tight = F.gy_plan(members, t, {m: 60.0 for m in members}, sessions, slots=300)
    for k in tight["rotation"]:
        plays = [k in tight["schedule"][d] for d in sessions]
        assert all(any(plays[i:i + 3]) for i in range(len(plays) - 2)), k


def test_bench_runs_carry_over_between_plans():
    members, t = _plan_inputs()
    p = F.gy_plan(members, t, {m: 60.0 for m in members}, ["2026-11-20", "2026-11-23", "2026-11-24"], slots=300)
    runs = F.bench_runs(p, "2026-11-23")
    for k in p["rotation"]:
        exp = 0
        for d in ["2026-11-20", "2026-11-23"]:
            exp = 0 if k in p["schedule"][d] else exp + 1
        assert runs.get(k, 0) == exp
    q = F.gy_plan(members, t, {m: 60.0 for m in members}, ["2026-11-24"], slots=300, runs=runs)
    assert all(k in q["schedule"]["2026-11-24"] for k, r in runs.items() if r >= 2)
    assert F.bench_runs(None, "2026-11-23") == {}


def test_next_sessions_skip_weekend_and_holiday():
    assert F.next_sessions(date(2026, 11, 24), 3) == ["2026-11-25", "2026-11-27", "2026-11-30"]


def _cfg():
    return {"account_name": "graveyard", "gy_footrace": {"enabled": True, "from": "2026-11-20", "file": "fr.json"},
            "live": {"setup_order": ["A", "B", "L", "C"]},
            "strategies": {k: {"enabled": True} for k in "ABLC"}}


def test_apply_gy_benches_rotation_and_orders_leaders(tmp_path):
    plan = {"gy": {"asof": "2026-11-19", "leaders": ["L"], "rotation": ["A", "B"],
                   "schedule": {"2026-11-20": ["A"]}}}
    (tmp_path / "fr.json").write_text(json.dumps(plan))
    cfg = _cfg()
    out = F.apply_gy(cfg, "2026-11-20", root=tmp_path)
    assert out["applied"] and out["benched"] == ["B"]
    assert not cfg["strategies"]["B"]["enabled"] and cfg["strategies"]["C"]["enabled"]   # unknown setups play
    assert cfg["live"]["setup_order"][0] == "L" and cfg["rotation"]["footrace"]["benched"] == ["B"]


def test_apply_gy_stale_or_missing_plan_falls_back(tmp_path):
    plan = {"gy": {"leaders": ["L"], "rotation": ["A", "B"], "schedule": {"2026-11-20": ["A"]}}}
    (tmp_path / "fr.json").write_text(json.dumps(plan))
    for root, day in ((tmp_path, "2026-11-23"), (tmp_path / "none", "2026-11-20")):    # stale / missing
        cfg = _cfg()
        out = F.apply_gy(cfg, day, root=root)
        assert out["applied"] is False and all(v["enabled"] for v in cfg["strategies"].values())
        assert cfg["live"]["setup_order"] == ["A", "B", "L", "C"]
    cfg = _cfg()
    assert F.apply_gy(cfg, "2026-11-19", root=tmp_path) == {}                            # before `from`
    cfg["account_name"] = "testingf"
    assert F.apply_gy(cfg, "2026-11-20", root=tmp_path) == {}                            # Graveyard only


def test_freeze_setups_snapshot_logs_the_bench(tmp_path, monkeypatch):
    from mcf.execution.session import freeze_setups

    (tmp_path / "fr.json").write_text(json.dumps({"gy": {"leaders": ["L"], "rotation": ["A", "B"],
                                                         "schedule": {"2026-11-20": ["A"]}}}))
    monkeypatch.setattr(F, "ROOT", tmp_path)
    cfg = {**_cfg(), "exits": {}, "shorts": {}, "universe": {}}
    msg = freeze_setups(cfg, tmp_path / "state", pd.Timestamp("2026-11-20 09:00", tz="America/New_York"))
    snap = json.loads((tmp_path / "state" / "setups" / "2026-11-20.json").read_text())
    assert snap["strategies"]["B"]["enabled"] is False and snap["rotation"]["footrace"]["benched"] == ["B"]
    assert "GY foot race" in msg


def test_archive_review_max_four_and_compass_exemptions():
    gy, whole = {}, {}
    names = [f"R{i}" for i in range(6)] + list(F.COMPASS_EXEMPT) + ["BIG"]
    for i, s in enumerate(names):
        gy[s] = {"n": 120, "days": 12, "avg_r": -0.1, "wo_avg_r": -0.12}
        whole[s] = {"n": 200, "days": 12, "wo_avg_r": -0.1, "last10_r": -10.0 - i, "big_days": 0, "big_sum": 0.0}
    whole["BIG"].update({"n": 400, "big_days": 3, "big_sum": 45.0})          # high-volume big-day cluster
    whole["R0"]["last10_r"] = 1.0                                             # recovering: not archived
    out = F.archive_review(pd.DataFrame(gy).T, pd.DataFrame(whole).T, names, pending={"R1"})
    got = [x["setup"] for x in out]
    assert len(got) == 4 and not set(got) & (set(F.COMPASS_EXEMPT) | {"BIG", "R0", "R1"})


def test_graveyard_config_and_plan_file():
    y = yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text())
    assert y["gy_footrace"] == {"enabled": True, "from": "2026-11-20", "file": "docs/live/footrace.json"}
    d = json.loads((ROOT / "docs/live/footrace.json").read_text())
    g = d["gy"]
    assert len(g["leaders"]) == F.GY_LEADERS and g["schedule"] and "Educational only" in d["note"]
    assert not set(g["leaders"]) & set(g["rotation"])
