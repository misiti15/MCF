"""Claude's Team (shadow) - mcf/report/team.py and its dashboard card (owner 2026-11-05). No network: the simulation itself
needs Alpaca market data and is exercised by the backfill demo (research/shadow_primary/README.md).
Educational only — not financial advice."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

from mcf.report import team

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "docs/live/index.html").read_text()
PICKS = ROOT / "research/shadow_primary/picks/2026-11-06.json"


def _rep(**kw):
    rep = {"date": "2026-11-06", "run_at": "2026-11-06 11:00 ET", "label": None, "phase": "intraday",
           "asof": "2026-11-06 11:00 ET", "setups": [{"id": "A", "name": "A", "account_tag": "Primary", "r": 1.5,
                                                       "trades": 2}],
           "totals": {"trades": 2, "open": 1, "r": 1.5, "pnl": 120.0, "vs_primary_r": 0.5},
           "primary": {"r": 1.0, "pnl_journal": 80.0, "pnl_alpaca": 75.5}}
    rep.update(kw)
    return rep


def test_picks_file_shape():
    d = json.loads(PICKS.read_text())
    assert d["date"] == "2026-11-06" and d["rationale"] and isinstance(d["weights"], dict)
    assert 1 <= len(d["setups"]) <= 30
    sides = {s["side"] for s in d["setups"]}
    assert sides == {"long", "short"}, "never a one-sided book (11-05 lesson)"
    for s in d["setups"]:
        assert s["id"] and s["account"] in team.ACCOUNT_BRANCH and s["why"] and "notes" in s
    assert "Educational only — not financial advice" in d["disclaimer"]


def test_picks_carry_over_and_explicit_file():
    assert team.picks_path("2026-11-06") == PICKS
    assert team.picks_path("2026-11-09") == PICKS            # latest before the date carries over
    assert team.picks_path("2026-11-05") is None              # nothing before the first Team
    assert team.load_picks("2026-11-05", "research/shadow_primary/picks/2026-11-06.json")["date"] == "2026-11-06"


def test_team_config_is_primary_rules_with_only_the_picks():
    import yaml

    picks = team.load_picks("2026-11-06")
    cfg = team.team_config(picks, "2026-11-06")
    prim = yaml.safe_load((ROOT / "config/default.yaml").read_text())
    assert set(cfg["strategies"]) == {s["id"] for s in picks["setups"]}
    assert all(v["enabled"] for v in cfg["strategies"].values())
    a = cfg["account"]
    assert a["risk_per_trade_pct"] == prim["account"]["risk_per_trade_pct"] == 0.25
    assert a["max_setup_daily_loss_r"] == prim["account"]["max_setup_daily_loss_r"] == 2.0
    assert a["slots"] == prim["account"]["slots"]
    assert cfg["costs"] == prim["costs"] and cfg["universe"] == prim["universe"]
    assert cfg["live"]["setup_order"][:1] and set(cfg["live"]["setup_order"]) == set(cfg["strategies"])
    # each setup keeps its own exits / geometry (the module and window of its home account)
    for s in picks["setups"]:
        assert cfg["strategies"][s["id"]].get("module")


def test_phase_of():
    ny = "America/New_York"
    assert team.phase_of("2026-11-06", pd.Timestamp("2026-11-06 09:00", tz=ny)) == ("pre-open", None)
    ph, cut = team.phase_of("2026-11-06", pd.Timestamp("2026-11-06 11:30:40", tz=ny))
    assert ph == "intraday" and cut == pd.Timestamp("2026-11-06 11:30", tz=ny)
    assert team.phase_of("2026-11-06", pd.Timestamp("2026-11-06 16:10", tz=ny)) == ("closed", None)
    assert team.phase_of("2026-11-05", pd.Timestamp("2026-11-06 08:00", tz=ny)) == ("closed", None)
    assert team.phase_of("2026-11-06", pd.Timestamp("2026-11-05 20:55", tz=ny)) == ("pre-open", None)   # the evening before


def test_pre_open_build_lists_picks_and_starts(monkeypatch):
    monkeypatch.setattr(team, "fetch_branches", lambda b: (_ for _ in ()).throw(AssertionError("no fetch pre-open")))
    rep = team.build("2026-11-06", now=pd.Timestamp("2026-11-06 08:30", tz="America/New_York"))
    assert rep["phase"] == "pre-open" and rep["note"].startswith("starts 11-06")
    assert len(rep["setups"]) == len(json.loads(PICKS.read_text())["setups"])
    assert all(s["account_tag"] and s["name"] for s in rep["setups"])
    assert rep["shadow"] == "Shadow — simulated independently; no orders"
    assert rep["disclaimer"] == "Educational only — not financial advice."


def test_summarize_per_setup_r():
    picks = {"setups": [{"id": "A", "account": "primary", "side": "short"}, {"id": "B", "account": "gen", "side": "long"}]}
    trades = [{"strategy": "A", "r": 1.0, "pnl": 30.0, "open": False}, {"strategy": "A", "r": -0.5, "pnl": -15.0, "open": True},
              {"strategy": "B", "r": float("nan"), "pnl": 0.0, "open": False}]
    sig = pd.DataFrame({"strategy": ["A", "A", "A", "B"]})
    rows = {r["id"]: r for r in team.summarize(picks, trades, sig)}
    assert rows["A"]["r"] == 0.5 and rows["A"]["trades"] == 2 and rows["A"]["open"] == 1 and rows["A"]["signals"] == 3
    assert rows["A"]["account_tag"] == "Primary" and rows["B"]["account_tag"] == "Generator" and rows["B"]["r"] == 0


def test_r_definition():
    assert team._r(50.0, 10.0, 9.5, 100) == 1.0
    assert team._r(-25.0, 10.0, 10.5, 100) == -0.5
    assert team._r(1.0, 10.0, 10.0, 100) != team._r(1.0, 10.0, 10.0, 100)   # zero risk -> nan


def test_scoreboard_append_and_text(tmp_path):
    p = tmp_path / "scoreboard.csv"
    team.append_scoreboard(_rep(), p)
    team.append_scoreboard(_rep(phase="closed"), p)
    rows = list(csv.DictReader(p.open()))
    assert [r["phase"] for r in rows] == ["intraday", "closed"] and list(rows[0]) == team.SCOREBOARD_COLS
    assert rows[1]["team_r"] == "1.5" and rows[1]["primary_pnl_alpaca"] == "75.5"
    t = team.text(_rep())
    assert "+1.50R" in t and "Primary +1.00R" in t and "Educational only — not financial advice" in t and "no orders" in t


def test_write(tmp_path):
    p = team.write(_rep(), tmp_path)
    assert p == tmp_path / "team" / "2026-11-06.json" and json.loads(p.read_text())["totals"]["r"] == 1.5


def test_harness_until_keep_signature():
    import inspect

    from mcf.replay import harness

    sig = inspect.signature(harness.run_session)
    assert sig.parameters["until"].default is None and sig.parameters["keep"].default is False


# --------------------------------------------------------------------------------------------- dashboard card
def _card():
    i = HTML.index('<div class="card" id="team-card"')
    return HTML[i:HTML.index("</script>", i)]


def test_team_card_present_and_labelled():
    c = _card()
    assert "<h2>Claude's Team (shadow)" in c
    assert "Shadow — simulated independently; no orders" in c and "Educational only — not financial advice" in c
    for i in ("team-asof", "team-label", "team-tiles", "team-tab"):
        assert f'id="{i}"' in c
    for k in ("Team R today (after costs)", "Team P/L today (after costs)", "Primary R today", "Primary P/L today",
              "Team R", "Account", "last update", "starts "):
        assert k in c, k


def test_team_card_reads_the_team_data_branch():
    c = _card()
    assert 'TEAM = RAW + "mcf-data-team/"' in c and '"team/latest.json"' in c and '"picks/latest.json"' in c
    assert "research/shadow_primary/picks/" in c        # before the first push: the picks on the main branch
    assert "localStorage" not in c


def test_team_card_does_not_touch_other_cards():
    # the card sits between the End of day card and the next script; the other cards keep their places
    assert HTML.index('id="eod-card"') < HTML.index('id="team-card"') < HTML.index('<section id="live"')
    assert HTML.count('id="team-card"') == 1
