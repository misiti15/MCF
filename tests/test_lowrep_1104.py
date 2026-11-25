"""Owner 2026-11-04 low-rep rotation (ledger 2026-11-04-lowrep-explore1-livelab, research/ops/lowrep1104/NOTES.md).

Explore 1 and Live Lab hold setups with little or no live history (< 20 live trades from Testing 1/2, < 10 from the
Graveyard). Each move is a move: on in the new account, off (and out of setup_order) where it came from. Their setups
show on the leaderboard with the account tag (a Graveyard-origin setup stays off); the two accounts' totals never show
in the daily post. Educational only - not financial advice."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# The 11-04 moves as made (historical sets; ledger 2026-11-04-lowrep-explore1-livelab).
MOVED_X1 = {"CWT04-backside-lh-a15-short", "CWT04-backside-vwaptest-a25-short", "CWT05-flush-m05-v5-long",
            "CWT09-gapdn-bounce-g10-lowerhalf-short", "CWT13-vwapstretch-z075-long", "IDX1-qqq100-0955-TQQQ-hold",
            "IDX2-spy075-0945-3x-trail", "IDX5-spy050-0945-3x-trail", "LD1-ns1-breadthup-t05s1-long",
            "LD3-st2-idxturn-t05s1-long", "LD4-st4-breadthup-t1s05-long",
            "LD8-spy-dip030-breadthturn-spxl-holdtr-long", "MF2-open-rsimidhi-flowsell",
            "NM-AMS-N1-quiet-morning-short", "NM-RWN3-ns3-spyup-early-short", "NM-RWN5-ns3-mon-weakrs-short",
            "NM-RWR4-ns2-up3-qqqup-slopedn-short", "NM1-cwt09-g10-vwaploss-short", "RW6G1-ns2-up3-vwap2sd-short",
            "ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD", "ST8-volspikedn-long-pm-t1s1-FD"}
MOVED_LL = {"CWT04-backside-lh-a25-short", "CWT04-backside-vwaptest-a15-short", "CWT05-flush-m075-v3-long",
           "CWT05-flush-m075-v5-long", "CWT09-gapdn-vwaploss-g10-short", "CWT12-flag-s1-long",
           "IDX1-qqq100-0955-TQQQ-trail", "IDX3-spy075-0955-3x-trail", "LD2-qqq-dip015-breadthturn-tqqq-t05s1-long",
           "LD5-st2-breadthup-t05s1-long", "LD6-spy-dip020atr-breadthturn-spxl-holdtr-long",
           "LD7-ns1-idxturn-holdtr-long", "LIQ-pdl-sweep-open15-vwap-long",
           # NM-ETF-late-dip-di-long left for Primary 2026-11-11 (owner Team yes 2026-11-10, ledger 2026-11-10-team6-primary)
           "NM-PM-gapdn-above-pdh-rvol-short", "NM-RWN4-ns2-spyup05-notfri-short",
           "NM-RWR1-exh150-gapdn-spyup-pm-short", "NM-RWR3-ns3-qqqup-early-short", "ST3-rsi5up-short-pm-t1s1-FD",
           "ST5-pdbrkup-short-mid-t05s1-FD", "ST6-volspikeup-short-mid-t1s1-FD"}
# Testing B (explore1) / Testing C (livelab) NOW: after the 2026-11-11 after-close build (ledger 2026-11-12-ondeck-build,
# 2026-11-12-testing-areas-fill): 4 of the 11-04 movers went up to On Deck, 15 moved on to Testing D / E / F.
EXPLORE1 = {"CWT04-backside-lh-a15-short", "CWT13-vwapstretch-z075-long", "IDX1-qqq100-0955-TQQQ-hold",
            "LD1-ns1-breadthup-t05s1-long", "LD3-st2-idxturn-t05s1-long", "MF2-open-rsimidhi-flowsell",
            "NM-RWN3-ns3-spyup-early-short", "NM-RWR4-ns2-up3-qqqup-slopedn-short", "NM1-cwt09-g10-vwaploss-short",
            "ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD", "ST8-volspikedn-long-pm-t1s1-FD"}
LIVELAB = {"CWT04-backside-vwaptest-a15-short", "CWT05-flush-m075-v3-long", "CWT12-flag-s1-long",
           "IDX1-qqq100-0955-TQQQ-trail", "LD2-qqq-dip015-breadthturn-tqqq-t05s1-long",
           "LD6-spy-dip020atr-breadthturn-spxl-holdtr-long", "LD7-ns1-idxturn-holdtr-long",
           "NM-PM-gapdn-above-pdh-rvol-short", "NM-RWR3-ns3-qqqup-early-short", "ST3-rsi5up-short-pm-t1s1-FD",
           "ST5-pdbrkup-short-mid-t05s1-FD"}
# 11-04 movers that qualified for On Deck at the 2026-11-11 build (OD-IN, or OD-FILL for CWT05-m05-v5)
TO_ONDECK = {"CWT09-gapdn-vwaploss-g10-short", "CWT09-gapdn-bounce-g10-lowerhalf-short", "ST6-volspikeup-short-mid-t1s1-FD",
             "CWT05-flush-m05-v5-long"}
# Graveyard -> arena 2026-11-12 after the close (owner GY-RW6/ST4 arena; from session 2026-11-13): no leaderboard (Graveyard origin)
FROM_GY = {"ST4-emadn-long-am-t1s05-FD": "explore1", "RW6-ns2-up3-short-FD": "livelab"}
# ROT1 arena rotation block 1 (2026-11-15, from session 2026-11-16): Setup Generator setups moved into the testing arena
_ROT1 = next(json.loads(x) for x in (ROOT / "research/ledger.jsonl").read_text().splitlines()
             if x.strip() and json.loads(x)["id"] == "2026-11-16-rot1-arena-block1")
FROM_GEN = {m.split(":")[0]: m.rsplit("(", 1)[1].split(")")[0] for m in _ROT1["moves"]}
# Workbench copies added 2026-11-17 (owner "Yes to all 15 WB copies", ledger 2026-11-16-wb-*): new setups, not moves
WB_1116 = {"NM-ETF-late-dip-di-long-WB1": "explore1", "L3-gap-slope-rsi5hi-FD-WB4": "explore1",
           "GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB4": "explore1",
           "RW3-gapdn-rsi5pop-flowsell-short-FD-WB4": "livelab", "ST7-rsi50dn-long-pm-t1s1-FD-WB1": "livelab",
           "orb20_a-WB3": "livelab"}
TESTING_AREAS = ("testing2", "explore1", "livelab", "testingd", "testinge", "testingf")
INACT2 = {"IDX1-qqq100-0955-TQQQ-trail", "IDX1-qqq100-0955-TQQQ-hold", "IDX2-spy075-0945-3x-trail",
          "IDX3-spy075-0955-3x-trail", "IDX5-spy050-0945-3x-trail", "LD4-st4-breadthup-t1s05-long",
          "LD5-st2-breadthup-t05s1-long"}
# kept where they are: mid-observation by owner decision, or a Graveyard setup with >= 10 live trades
# (RW3S-gapdn-flowsell-short-FD stayed on 11-04 and moved on to Testing E on 2026-11-12;
#  ST4-emadn-long-am-t1s05-FD stayed on 11-04 and moved on to Testing B on 2026-11-13, see FROM_GY)
# PDL-1a R2A legs stayed in Testing 2 at ROLL1 (11-04); FOOTRACE-EXIT moved them to the Graveyard (Friday review 2026-11-20, from 11-23)
STAY = {"graveyard": {"CWT14-failbrk-pdl-p05-R2A-short"}}   # the -long leg archived 2026-11-25 (GYH V3, from 11-27)


def _cfg(monkeypatch, acct):
    from mcf.config import load_config

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    return load_config()


# C3 2026-11-18 (effective 2026-11-19): C3-EXIT100 moved these to the Graveyard; C3-WB5 added a Workbench copy
C3_OUT = {"GEN-261028-08-Ret5mge0p21-SMA20dlem0p16-Compress6le0p11-LUNCH-BRoplt0p35-holdtr-long": "explore1", "GEN-261027-05-VolRatioge1p5-ORLdistge0p41-ATRdge6-MID-BRvwgt0p7-t05s1-long": "livelab"}
C3_IN = {"L3-gap-slope-rsi5hi-FD-WB5": "livelab"}
# FOOTRACE-EXIT (Friday review 2026-11-20, from session 2026-11-23): moved to the Graveyard
FR_OUT = {"GEN-261020-03-MACDhge0p079-BarsSinceLODle5-MID-BRvwlt0p3-t05s05-long": "explore1",
          "GEN-261029-02-RSI2le0-VWAPcrossesge9-DayRngVsPrevle0p52-MID-BRvwlt0p4-hold-long": "explore1",
          "GEN-261027-09-ORBfailDn-Gapge2-Slope6ge0p03-LAM-BRvwlt0p5-t05s05-short": "livelab",
          "GEN-261026-10-ORBfailDn-EMAdChglem0p051-PM-BRopgt0p65-t1s1-long": "livelab",
          # QA-EXIT2 2026-11-21 (from 11-23)
          "GEN-261027-06-ORBfailUp-BarsSinceLODle5-MID-BRoplt0p35-holdtr-long": "livelab",
          # GYH V1 2026-11-25 (owner, Graveyard floor; from 11-27; ledger 2026-11-27-gyh-v1-v3)
          "CWT13-vwapstretch-z075-long": "explore1",
          "GEN-261023-04-EMAdChglem0p028-PDHdistle0p074-EMAdifflem0p46-PM-QQQltm0p6-t1s1-long": "explore1",
          "GEN-261029-03-MACDhlem0p12-Ret5mlem0p062-Gapge2-PM-QQQup-hold-long": "explore1",
          "ST4-emadn-long-am-t1s05-FD": "explore1",
          "GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long": "livelab"}
GYH_V1 = {k: a for k, a in FR_OUT.items() if k in ("CWT13-vwapstretch-z075-long", "ST4-emadn-long-am-t1s05-FD",
          "GEN-261023-04-EMAdChglem0p028-PDHdistle0p074-EMAdifflem0p46-PM-QQQltm0p6-t1s1-long",
          "GEN-261029-03-MACDhlem0p12-Ret5mlem0p062-Gapge2-PM-QQQup-hold-long",
          "GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long")}
from tests.test_ult1119_deploy import ULT_1120  # noqa: E402  ultimate_1119 admissions, effective 2026-11-20
from tests.test_beg1120_deploy import BEG_1123  # noqa: E402  beginner_1120 admissions, effective 2026-11-23
from tests.test_remedyq_1120 import COPIES as RQ_1123  # noqa: E402  Remedy-Q (a) copies, effective 2026-11-23
# ROT block 2 (2026-11-19, from session 2026-11-20): arena moves, setup -> (from key, to key)
_KEY = {"Testing A": "testing2", "Testing B": "explore1", "Testing C": "livelab", "Testing D": "testingd", "Testing E": "testinge",
        "Testing F": "testingf", "Setup Generator": "gen"}
_ROT2 = next(json.loads(x) for x in (ROOT / "research/ledger.jsonl").read_text().splitlines()
             if x.strip() and json.loads(x)["id"] == "2026-11-20-rot-arena-block2")
ROT2 = {m.split(":")[0]: (_KEY[m.split(": ", 1)[1].split(" -> ")[0]], m.rsplit("(", 1)[1].rstrip(")")) for m in _ROT2["moves"]}


def _rot2(want: set, acct: str) -> set:
    return (want - {k for k, (f, t) in ROT2.items() if f == acct}) | {k for k, (f, t) in ROT2.items() if t == acct}


def _on(cfg):
    return {k for k, v in cfg["strategies"].items() if isinstance(v, dict) and v.get("enabled")}


def test_moves_are_moves(monkeypatch):
    from mcf.strategies.setups import build_strategies

    assert not (EXPLORE1 & LIVELAB) and not (MOVED_X1 & MOVED_LL) and INACT2 <= MOVED_X1 | MOVED_LL
    assert EXPLORE1 | LIVELAB <= MOVED_X1 | MOVED_LL and TO_ONDECK <= MOVED_X1 | MOVED_LL
    for acct, want in (("explore1", EXPLORE1), ("livelab", LIVELAB)):
        want = want | {k for k, a in FROM_GY.items() if a == acct} | {k for k, a in FROM_GEN.items() if a == acct}
        want = want | {k for k, a in WB_1116.items() if a == acct}
        want = (want - set(C3_OUT)) | {k for k, a in C3_IN.items() if a == acct}
        want = _rot2(want | {k for k, a in ULT_1120.items() if a == acct}, acct)
        want = want | {k for k, a in BEG_1123.items() if a == acct}
        want = want | {k for k, (_, a) in RQ_1123.items() if a == acct}
        want = want - set(FR_OUT)
        cfg = _cfg(monkeypatch, acct)
        assert _on(cfg) == want, acct
        assert sorted(cfg["live"]["setup_order"]) == sorted(want), acct      # every setup has a priority
        assert {s.name for s in build_strategies(cfg)} == want, acct
    for acct in ("testing", "testing2", "graveyard"):
        cfg = _cfg(monkeypatch, acct)
        back = TO_ONDECK if acct == "testing" else set()                       # On Deck from 2026-11-12
        guests = {k for k, v in cfg["strategies"].items() if isinstance(v, dict) and v.get("guest")}   # GY-BENCH 11-18..11-24
        gyh = set(GYH_V1) if acct == "graveyard" else set()                      # GYH V1 2026-11-25: Graveyard floor moves
        assert not (_on(cfg) & (MOVED_X1 | MOVED_LL) - back - guests - gyh), acct     # switched off where they came from
        assert not (set(cfg["live"]["setup_order"]) & (MOVED_X1 | MOVED_LL) - back - guests - gyh), acct
        assert back <= _on(cfg), acct
        assert STAY.get(acct, set()) <= _on(cfg), acct
    txt = (ROOT / "config/account_testing2.yaml").read_text()
    assert "moved to Explore 1 2026-11-04 (owner, low-rep rotation)" in txt
    assert "moved to Live Lab 2026-11-04 (owner, low-rep rotation)" in txt


def test_twins_split_across_the_two_accounts():
    """Twins never share an account (they were split Explore 1 / Live Lab on 11-04; since 2026-11-12 they may sit in
    On Deck or Testing A-F, still apart). Trimmed (INACT2) setups are never just switched off."""
    home = {}
    for k, v in json.loads((ROOT / "docs/live/assignments.json").read_text())["accounts"].items():
        for s in v:
            home.setdefault(s, set()).add(k)
    for s in INACT2:
        assert home.get(s) and home[s] <= set(TESTING_AREAS), s
    for pair in (("IDX1-qqq100-0955-TQQQ-trail", "IDX1-qqq100-0955-TQQQ-hold"),
                 ("NM1-cwt09-g10-vwaploss-short", "CWT09-gapdn-vwaploss-g10-short"),
                 ("CWT04-backside-lh-a15-short", "CWT04-backside-lh-a25-short"),
                 ("CWT04-backside-vwaptest-a15-short", "CWT04-backside-vwaptest-a25-short"),
                 ("LD4-st4-breadthup-t1s05-long", "LD5-st2-breadthup-t05s1-long")):
        assert home[pair[0]] and home[pair[1]] and not (home[pair[0]] & home[pair[1]]), pair


def test_twin_groups_never_share_an_account(monkeypatch):
    for acct in ("testing", *TESTING_AREAS):
        groups = [v.get("twin_group") for v in _cfg(monkeypatch, acct)["strategies"].values()
                  if isinstance(v, dict) and v.get("enabled") and v.get("twin_group")]
        assert len(groups) == len(set(groups)), acct


def test_assignments_and_ledger():
    d = json.loads((ROOT / "docs/live/assignments.json").read_text())
    for acct, base in (("explore1", EXPLORE1), ("livelab", LIVELAB)):
        assert {k for k, a in BEG_1123.items() if a == acct} <= set(d["accounts"][acct]), acct
        assert set(d["accounts"][acct]) - set(BEG_1123) - set(RQ_1123) == _rot2((base | {k for k, a in FROM_GY.items() if a == acct}
                                             | {k for k, a in FROM_GEN.items() if a == acct}
                                             | {k for k, a in WB_1116.items() if a == acct}) - set(C3_OUT)
                                            | {k for k, a in C3_IN.items() if a == acct}
                                            | {k for k, a in ULT_1120.items() if a == acct}, acct) - set(FR_OUT), acct
    assert {k for k, v in d["setups"].items() if v.get("no_leaderboard")} == set(FROM_GY) - set(GYH_V1)   # only the Graveyard-origin ones (ST4 back in the Graveyard, GYH V1)
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
    assert lb["X1-SETUP"] == "Testing B" and lb["LL-SETUP"] == "Testing C"      # tagged with their account
    assert "GY-ORIGIN" not in lb                                               # Graveyard origin: off the leaderboard
