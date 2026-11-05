"""Owner 2026-11-04 low-rep rotation (ledger 2026-11-04-lowrep-explore1-livelab, research/ops/lowrep1104/NOTES.md).

Explore 1 and Live Lab hold setups with little or no live history (< 20 live trades from Testing 1/2, < 10 from the
Graveyard). Each move is a move: on in the new account, off (and out of setup_order) where it came from. Their setups
show on the leaderboard with the account tag (a Graveyard-origin setup stays off); the two accounts' totals never show
in the daily post. Educational only - not financial advice."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXPLORE1 = {"CWT04-backside-lh-a15-short", "CWT04-backside-vwaptest-a25-short", "CWT05-flush-m05-v5-long",
            "CWT09-gapdn-bounce-g10-lowerhalf-short", "CWT13-vwapstretch-z075-long", "IDX1-qqq100-0955-TQQQ-hold",
            "IDX2-spy075-0945-3x-trail", "IDX5-spy050-0945-3x-trail", "LD1-ns1-breadthup-t05s1-long",
            "LD3-st2-idxturn-t05s1-long", "LD4-st4-breadthup-t1s05-long",
            "LD8-spy-dip030-breadthturn-spxl-holdtr-long", "MF2-open-rsimidhi-flowsell",
            "NM-AMS-N1-quiet-morning-short", "NM-RWN3-ns3-spyup-early-short", "NM-RWN5-ns3-mon-weakrs-short",
            "NM-RWR4-ns2-up3-qqqup-slopedn-short", "NM1-cwt09-g10-vwaploss-short", "RW6G1-ns2-up3-vwap2sd-short",
            "ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD", "ST8-volspikedn-long-pm-t1s1-FD"}
LIVELAB = {"CWT04-backside-lh-a25-short", "CWT04-backside-vwaptest-a15-short", "CWT05-flush-m075-v3-long",
           "CWT05-flush-m075-v5-long", "CWT09-gapdn-vwaploss-g10-short", "CWT12-flag-s1-long",
           "IDX1-qqq100-0955-TQQQ-trail", "IDX3-spy075-0955-3x-trail", "LD2-qqq-dip015-breadthturn-tqqq-t05s1-long",
           "LD5-st2-breadthup-t05s1-long", "LD6-spy-dip020atr-breadthturn-spxl-holdtr-long",
           "LD7-ns1-idxturn-holdtr-long", "LIQ-pdl-sweep-open15-vwap-long", "NM-ETF-late-dip-di-long",
           "NM-PM-gapdn-above-pdh-rvol-short", "NM-RWN4-ns2-spyup05-notfri-short",
           "NM-RWR1-exh150-gapdn-spyup-pm-short", "NM-RWR3-ns3-qqqup-early-short", "ST3-rsi5up-short-pm-t1s1-FD",
           "ST5-pdbrkup-short-mid-t05s1-FD", "ST6-volspikeup-short-mid-t1s1-FD"}
INACT2 = {"IDX1-qqq100-0955-TQQQ-trail", "IDX1-qqq100-0955-TQQQ-hold", "IDX2-spy075-0945-3x-trail",
          "IDX3-spy075-0955-3x-trail", "IDX5-spy050-0945-3x-trail", "LD4-st4-breadthup-t1s05-long",
          "LD5-st2-breadthup-t05s1-long"}
# kept where they are: mid-observation by owner decision, or a Graveyard setup with >= 10 live trades
STAY = {"testing2": {"RW3S-gapdn-flowsell-short-FD", "CWT14-failbrk-pdl-p05-R2A-long", "CWT14-failbrk-pdl-p05-R2A-short"},
        "graveyard": {"ST4-emadn-long-am-t1s05-FD"}}


def _cfg(monkeypatch, acct):
    from mcf.config import load_config

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    return load_config()


def _on(cfg):
    return {k for k, v in cfg["strategies"].items() if isinstance(v, dict) and v.get("enabled")}


def test_moves_are_moves(monkeypatch):
    from mcf.strategies.setups import build_strategies

    assert not (EXPLORE1 & LIVELAB) and INACT2 <= EXPLORE1 | LIVELAB
    for acct, want in (("explore1", EXPLORE1), ("livelab", LIVELAB)):
        cfg = _cfg(monkeypatch, acct)
        assert _on(cfg) == want, acct
        assert sorted(cfg["live"]["setup_order"]) == sorted(want), acct      # every setup has a priority
        assert {s.name for s in build_strategies(cfg)} == want, acct
    for acct in ("testing", "testing2", "graveyard"):
        cfg = _cfg(monkeypatch, acct)
        assert not (_on(cfg) & (EXPLORE1 | LIVELAB)), acct                     # switched off where they came from
        assert not (set(cfg["live"]["setup_order"]) & (EXPLORE1 | LIVELAB)), acct
        assert STAY.get(acct, set()) <= _on(cfg), acct
    txt = (ROOT / "config/account_testing2.yaml").read_text()
    assert "moved to Explore 1 2026-11-04 (owner, low-rep rotation)" in txt
    assert "moved to Live Lab 2026-11-04 (owner, low-rep rotation)" in txt


def test_twins_split_across_the_two_accounts():
    for pair in (("IDX1-qqq100-0955-TQQQ-trail", "IDX1-qqq100-0955-TQQQ-hold"),
                 ("NM1-cwt09-g10-vwaploss-short", "CWT09-gapdn-vwaploss-g10-short"),
                 ("CWT04-backside-lh-a15-short", "CWT04-backside-lh-a25-short"),
                 ("CWT04-backside-vwaptest-a15-short", "CWT04-backside-vwaptest-a25-short"),
                 ("LD4-st4-breadthup-t1s05-long", "LD5-st2-breadthup-t05s1-long")):
        assert len({("x" if s in EXPLORE1 else "l") for s in pair}) == 2, pair


def test_twin_groups_never_share_an_account(monkeypatch):
    for acct in ("explore1", "livelab"):
        groups = [v.get("twin_group") for v in _cfg(monkeypatch, acct)["strategies"].values()
                  if isinstance(v, dict) and v.get("enabled") and v.get("twin_group")]
        assert len(groups) == len(set(groups)), acct


def test_assignments_and_ledger():
    d = json.loads((ROOT / "docs/live/assignments.json").read_text())
    assert set(d["accounts"]["explore1"]) == EXPLORE1 and set(d["accounts"]["livelab"]) == LIVELAB
    assert not any(v.get("no_leaderboard") for v in d["setups"].values())     # nothing came from the Graveyard
    led = [json.loads(x) for x in (ROOT / "research/ledger.jsonl").read_text().splitlines() if x.strip()]
    e = next(x for x in led if x["id"] == "2026-11-04-lowrep-explore1-livelab")
    assert e["effective"] == "2026-11-05" and "owner" in e["approved_by"]


def test_graveyard_origin_flag():
    from mcf.report.assignments import no_leaderboard

    assert no_leaderboard({"accounts": ["livelab"], "from": ["graveyard"]})
    assert no_leaderboard({"accounts": ["explore1"], "from": ["graveyard", "testing"]})
    assert not no_leaderboard({"accounts": ["explore1"], "from": ["testing2"]})
    assert not no_leaderboard({"accounts": ["graveyard"], "from": ["testing"]})       # Graveyard itself: as before
    assert not no_leaderboard({"accounts": ["testing"], "from": ["graveyard"]})       # back up to Testing: listed
    html = (ROOT / "docs/live/index.html").read_text()
    assert ".no_leaderboard) delete groups[sname]" in html


# ---------------------------------------------------------------- daily post
def _row(setup, n, r, pnl, day="2026-11-05"):
    return {"setup": setup, "name": setup, "trades": n, "n_win": n, "win_rate": 1.0, "avg_r": r / n, "total_r": r,
            "pnl": pnl, "days": [day], "sessions_traded": 1, "daily": [[day, n, r, pnl]]}


@pytest.fixture
def post(monkeypatch):
    from mcf.report import daily_post as P

    sc = {"mcf-data": [_row("P-SETUP", 3, 1.0, 100.0)],
          "mcf-data-explore1": [_row("X1-SETUP", 4, 6.0, 600.0)],
          "mcf-data-livelab": [_row("LL-SETUP", 2, 3.0, 300.0), _row("GY-ORIGIN", 9, 9.0, 900.0)]}
    status = {"session_date": "2026-11-05", "account": {"equity": 100500.0}, "today": {"pnl": 500.0, "trades": 4},
              "history": [{"date": "2026-11-05", "pnl": 500.0, "trades": 4}], "since_start": {"trades": 4, "avg_entry_slip_bps": 3.0}}

    def show(br, path):
        if path == "reports/scorecard.json":
            return {"leaderboard": sc.get(br, [])}
        if path == "status.json":
            return dict(status)
        return None

    asg = {"setups": {"P-SETUP": {"accounts": ["primary"]}, "X1-SETUP": {"accounts": ["explore1"], "from": ["testing"]},
                      "LL-SETUP": {"accounts": ["livelab"], "from": ["testing2"]},
                      "GY-ORIGIN": {"accounts": ["livelab"], "from": ["graveyard"], "no_leaderboard": True}}}
    monkeypatch.setattr(P, "_show", show)
    monkeypatch.setattr(P, "_local", lambda p: asg if p.endswith("assignments.json") else None)
    monkeypatch.setattr(P, "_journal", lambda br: None)                        # no journals: scorecard figures only
    return P


def test_post_leaves_out_new_account_totals(post):
    got = {a["k"] for a in post.accounts("2026-11-05")}
    assert got and not got & {"explore1", "livelab"}
    assert {"primary", "testing", "testing2", "gen", "graveyard"} == got


def test_new_account_setups_eligible_for_top2_and_leaderboard(post):
    top = [x["setup"] for x in post.top_of_day("2026-11-05", n=2)]
    assert top == ["GY-ORIGIN", "X1-SETUP"]                                    # top setups: any account
    lb = {x["setup"]: x["acct"] for x in post.leaderboard("2026-11-05")}
    assert lb["X1-SETUP"] == "Explore 1" and lb["LL-SETUP"] == "Live Lab"      # tagged with their account
    assert "GY-ORIGIN" not in lb                                               # Graveyard origin: off the leaderboard
