"""GY-BENCH (owner 2026-11-16): date-scoped session rotation (mcf/rotation.py). Benched setups sit out their window and
come back by themselves; guests run only inside their window while their home block is benched away; the window pairs
stay consistent across accounts; benched sessions are logged in the frozen snapshot; guests keep their home limits."""
import json
import os

import pandas as pd
import pytest

from mcf import rotation as R
from mcf.config import load_config
from mcf.execution.risk import RiskManager, setup_cost_limits, setup_loss_limits
from mcf.report import assignments as A

W = {"from": "2026-11-18", "until": "2026-11-24"}


def _cfg():
    return {"strategies": {
        "busy": {"enabled": True, "benched": dict(W, reason="x")},
        "quiet": {"enabled": True},
        "guest": {"enabled": True, "guest": dict(W, home="testingd")},
        "home_away": {"enabled": True, "benched": dict(W, away="graveyard")},
        "off": {"enabled": False, "benched": dict(W)},
    }}


@pytest.mark.parametrize("day,on", [
    ("2026-11-17", {"busy", "quiet", "home_away"}),
    ("2026-11-18", {"quiet", "guest"}),
    ("2026-11-24", {"quiet", "guest"}),
    ("2026-11-25", {"busy", "quiet", "home_away"}),
])
def test_windows_inclusive_and_automatic_return(day, on):
    c = _cfg()
    log = R.apply(c, day)
    assert {k for k, v in c["strategies"].items() if v.get("enabled")} == on
    assert log["session"] == day
    if day in ("2026-11-18", "2026-11-24"):
        assert log["benched"] == ["busy"] and log["away"] == {"home_away": "graveyard"} and log["guests"] == {"guest": "testingd"}
    else:
        assert log["benched"] == [] and log["away"] == {} and log["guests"] == {}


def test_session_date_env(monkeypatch):
    monkeypatch.setenv("MCF_ASOF", "2026-11-20")
    assert str(R.session_date()) == "2026-11-20"
    assert str(R.session_date("2026-11-25")) == "2026-11-25"


def test_freeze_logs_benched_and_runner_skips_them(tmp_path, monkeypatch):
    from mcf.execution.session import freeze_setups
    from mcf.strategies.setups import build_strategies

    monkeypatch.setenv("MCF_ACCOUNT", "graveyard")
    cfg = load_config(asof="2026-11-18")
    note = freeze_setups(cfg, tmp_path, pd.Timestamp("2026-11-18 09:00", tz="America/New_York"))
    snap = json.loads((tmp_path / "setups" / "2026-11-18.json").read_text())
    rot = snap["rotation"]
    assert "CWT14-failbrk-orl-p05-long" in rot["benched"] and "benched" in note
    assert not snap["strategies"]["CWT14-failbrk-orl-p05-long"]["enabled"]          # not live: no per-session row
    assert "LIQ-pdl-sweep-open15-vwap-long" in rot["guests"]
    names = {s.name for s in build_strategies(cfg)}
    assert "CWT14-failbrk-orl-p05-long" not in names and "LIQ-pdl-sweep-open15-vwap-long" in names
    # after the window: the benched setups are back, the guests are home
    back = load_config(asof="2026-11-25")["strategies"]
    assert back["CWT14-failbrk-orl-p05-long"]["enabled"] and not back["LIQ-pdl-sweep-open15-vwap-long"]["enabled"]


def test_graveyard_bench_list_and_rules_untouched():
    """The 18 busy Graveyard setups (> 150 Graveyard trades to 2026-11-17) are benched 11-18..11-24 with rules unchanged."""
    os.environ["MCF_ACCOUNT"] = "graveyard"
    try:
        st = load_config(asof="2026-11-17")["strategies"]
    finally:
        os.environ.pop("MCF_ACCOUNT", None)
    benched = sorted(k for k, v in st.items() if isinstance(v, dict) and isinstance(v.get("benched"), dict))
    assert len(benched) == 18
    for k in benched:
        assert st[k]["benched"]["from"] == "2026-11-18" and st[k]["benched"]["until"] == "2026-11-24"
        assert "guest" not in st[k] and "max_stop_cost_r" not in st[k] and "max_setup_daily_loss_r" not in st[k]


def test_guest_pairs_consistent_across_accounts():
    by = A._strategies("2026-11-17")
    assert R.window_violations(by) == []
    g = R.guests(by["graveyard"])
    assert len(g) == 20 and all(x["home"] != "graveyard" for x in g.values())
    for k, x in g.items():                               # guests carry no Graveyard tag (not Graveyard-origin)
        assert "graveyard" not in (by["graveyard"][k].get("tags") or [])
    for day in ("2026-11-17", "2026-11-18", "2026-11-24", "2026-11-25"):
        acc = A.current(A._strategies(day))
        where: dict = {}
        for a, v in acc.items():
            for s in v:
                where.setdefault(s, []).append(a)
        assert all(len(where.get(k, [])) == 1 for k in g), day   # one home per setup on every date


def test_window_violation_detected():
    by = {"graveyard": {"S": {"enabled": True, "guest": dict(W, home="testingd")}},
          "testingd": {"S": {"enabled": True, "benched": {"from": "2026-11-18", "until": "2026-11-23", "away": "graveyard"}}}}
    assert R.window_violations(by)
    by["testingd"]["S"]["benched"]["until"] = "2026-11-24"
    assert R.window_violations(by) == []
    by["testingd"]["T"] = {"enabled": True, "benched": dict(W, away="graveyard")}
    assert R.window_violations(by)                       # away without a guest block


def test_guest_keeps_home_limits():
    cfg = load_config()
    cfg["account"]["max_setup_daily_loss_r"] = 2.0
    cfg["live"]["max_stop_cost_r"] = None
    cfg["strategies"] = {"G": {"enabled": True, "max_setup_daily_loss_r": None, "max_stop_cost_r": 0.15},
                         "H": {"enabled": True}}
    assert setup_loss_limits(cfg) == {"G": None} and setup_cost_limits(cfg) == {"G": 0.15}
    rm = RiskManager(cfg, 100000)
    assert rm.loss_limit_for("G") is None and rm.loss_limit_for("H") == 2.0
    rm.latch_setup_losses({"G": -5.0, "H": -2.5})
    assert rm.state.setup_stopped == {"H"}


def test_no_leaderboard_ignores_graveyard_guests():
    e = {"accounts": ["livelab"], "from": ["graveyard"]}
    assert A.no_leaderboard(e)
    assert not A.no_leaderboard({**e, "guest": {"account": "graveyard", "home": "livelab"}})


def test_daily_post_excludes_guest_pnl():
    from mcf.report.daily_post import _guest_out

    h = {"date": "2026-11-18", "pnl": -100.0, "trades": 50}
    out = _guest_out(h, {"2026-11-18": {"pnl": -30.0, "trades": 5}})
    assert out["pnl"] == -70.0 and out["pnl_unadjusted"] == -100.0 and out["trades"] == 45 and out["adjusted"]["delta"] == 30.0
    assert _guest_out(h, {}) == h
