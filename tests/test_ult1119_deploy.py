"""ultimate_1119 deploy (effective 2026-11-20, merged after the 2026-11-19 close): ETFDISP (owner decision) and the variants
admitted under the testing-admission rule (meets the top-10 standard, or debatable + derived) are each one new setup in
exactly one testing area (Testing A-F), never in Primary / On Deck / Graveyard, never beside a close sibling, with a
display name, a setup_order slot and one ledger entry. Educational only - not financial advice."""
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TESTING = ["testing2", "explore1", "livelab", "testingd", "testinge", "testingf"]
OTHER = ["default", "testing", "graveyard", "gen"]
ULT_1120 = {   # setup -> account (ledger 2026-11-20-ult1119-testing-admissions)
    "ETFDISP-late-dip-hidisp-long": "testingd",
    "ULT-HV2-shock-snap-etf-long-K": "testingd",
    "ULT-22-wb4-wide-etf-long": "livelab",
    "ULT-14-snap-long": "testingf",
    "ULT-14-snap-short": "testingf",
    "ULT-20-evr-ranker-long": "explore1",
    "ULT-20-evr-ranker-short": "explore1",
    "ULT-21-etf-rank-long": "livelab",
    "ULT-13-st7-sharp-long": "testing2",
    "ULT-25-ultracheap-long": "testingf",
    "ULT-25-ultracheap-short": "testingf",
    "ULT-16-costgeo-long": "testinge",
    "ULT-16-costgeo-short": "testinge",
    "ULT-01-gapdn-pop-fade-short": "testing2",
    "ULT-19-lrlite-long": "testing2",
    "ULT-19-lrlite-short": "testing2",
    "ULT-26-withgap-trend-long": "testingd",
    "ULT-26-withgap-trend-short": "testingd",
    "ULT-HV1-etf-late-pop-fade-short-X": "testing2",
    "ULT-05-withgap-cont-long": "testinge",
    "ULT-05-withgap-cont-short": "testinge",
    "ULT-09-failed-vwap-reclaim-short": "explore1",
    "ULT-07-pm-volatile-dip-long": "testingf",
}
SIBLINGS = ("ST7", "NM-ETF-late-dip", "L3-gap-slope", "RW3-", "RW5-", "CWT09-gapdn-vwaploss")
ETF_LONG = {"ETFDISP-late-dip-hidisp-long", "ULT-22-wb4-wide-etf-long", "ULT-21-etf-rank-long", "ULT-HV2-shock-snap-etf-long-K"}


def _raw(acct):
    return yaml.safe_load((ROOT / f"config/account_{acct}.yaml").read_text()) if acct != "default" else \
        yaml.safe_load((ROOT / "config/default.yaml").read_text())


def _on(raw):
    return {k for k, v in (raw.get("strategies") or {}).items() if isinstance(v, dict) and v.get("enabled")}


def test_each_new_setup_in_exactly_one_testing_area():
    for n, acct in ULT_1120.items():
        homes = [a for a in TESTING if n in _on(_raw(a))]
        assert homes == [acct], (n, homes)
        assert n in _raw(acct)["live"]["setup_order"]
        for a in OTHER:
            assert n not in (_raw(a).get("strategies") or {}), (n, a)


def test_no_close_sibling_and_no_etf_long_stack():
    for acct in TESTING:
        new = {n for n, a in ULT_1120.items() if a == acct}
        old = _on(_raw(acct)) - set(ULT_1120)
        for n in new:
            assert not (n == "ETFDISP-late-dip-hidisp-long" and any(o.startswith("NM-ETF-late-dip") for o in old)), acct
        assert len(new & ETF_LONG) <= 2, acct
    assert ULT_1120["ETFDISP-late-dip-hidisp-long"] not in ("testinge", "explore1")     # WB4 / WB1 homes


@pytest.mark.parametrize("acct", sorted(set(ULT_1120.values())))
def test_new_setups_build_under_the_live_loader(monkeypatch, acct):
    from mcf.config import load_config
    from mcf.strategies import setups as S

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    built = {s.name: s for s in S.build_strategies(load_config())}
    for n, a in ULT_1120.items():
        if a != acct:
            continue
        s = built[n]
        assert s.side == (1 if n.endswith(("-long", "-K")) else -1), n
        assert s.params.get("time_stop_min") == 45 and s.refire, n
        assert "spy_fo" in s.context, n
    if acct == "testingd":
        assert built["ETFDISP-late-dip-hidisp-long"].market_daily_cols == ("disp_prev",)


def test_names_assignments_ledger():
    names = yaml.safe_load((ROOT / "config/setup_names.yaml").read_text())
    d = json.loads((ROOT / "docs/live/assignments.json").read_text())
    for n, acct in ULT_1120.items():
        assert names[n]["account"] == acct and names[n]["name"]
        assert n in d["accounts"][acct], n
    led = [json.loads(x) for x in (ROOT / "research/ledger.jsonl").read_text().splitlines() if x.strip()]
    e = next(x for x in led if x["id"] == "2026-11-20-ult1119-testing-admissions")
    assert e["effective"] == "2026-11-20" and "owner" in e["approved_by"] and set(e["setups"]) == set(ULT_1120)
