"""Testing D / E / F paper accounts (owner 2026-11-11; ledger 2026-11-11-testing-def-accounts). Wired like Testing B / C
(explore1 / livelab): each overlay is exclusive and starts with NO setup enabled (trade.yml's Setup check skips it until the
after-close build assigns setups), ~$1,000 lots, 10 lots per setup, no -2R per-setup stop, full universe; each routes to its
own keys / order prefix / state branch / concurrency group, and - unlike every other account - its jobs can use its OWN keys
for market data (ALPACA_API_KEY / ALPACA_SECRET_KEY mapped per account, repo variable MCF_DEF_OWN_DATA_KEYS) once they have SIP.
Educational only - not financial advice."""
import json
from pathlib import Path

import pytest
import yaml

from tests.test_new_accounts_1103 import EXPECT, _cfg, _eval, _expr

ROOT = Path(__file__).resolve().parents[1]
DEF = {"testingd": ("Testing D", "mtd-", "TESTINGD"), "testinge": ("Testing E", "mte-", "TESTINGE"),
       "testingf": ("Testing F", "mtf-", "TESTINGF")}
ALL = {**EXPECT, **{k: (p, f"mcf-data-{k}", f"mcf-trade-{k}", s) for k, (_, p, s) in DEF.items()}}
MATRIX = "account: [primary, testing, testing2, gen, graveyard, livelab, explore1, testingd, testinge, testingf]"
WF = ROOT / ".github/workflows"


@pytest.mark.parametrize("acct", sorted(DEF))
def test_overlay_loads_with_its_own_setups(monkeypatch, acct):
    """Started empty (11-11); the 2026-11-11 after-close build assigned 10 setups each (ledger 2026-11-12-testing-areas-fill)."""
    from mcf.backtest.engine import slot_notional
    from mcf.execution import session_guard as G
    from mcf.strategies.setups import build_strategies

    raw = yaml.safe_load((ROOT / f"config/account_{acct}.yaml").read_text())
    assert raw["strategies_exclusive"] is True
    own = {k for k, v in raw["strategies"].items() if v.get("enabled")}
    assert len(own) == 10 and sorted(raw["live"]["setup_order"]) == sorted(own)          # every setup has a priority
    cfg = _cfg(monkeypatch, acct)
    a, live = cfg["account"], cfg["live"]
    b = _cfg(monkeypatch, "explore1")                                             # Testing B: the base rules
    assert cfg["account_name"] == acct
    for k in ("slots", "max_concurrent_positions", "buying_power_multiple", "max_positions_per_strategy", "max_daily_loss_r",
              "max_setup_daily_loss_r", "max_trades_per_day", "risk_per_trade_pct"):
        assert a[k] == b["account"][k], k
    assert a["max_setup_daily_loss_r"] is None                                    # no -2R per-setup stop (testing areas)
    for k in ("max_stop_cost_r", "block_twin_same_symbol", "scale_out_max_per_day"):
        assert live[k] == b["live"][k], k
    assert not (cfg.get("universe") or {}).get("top_n")                           # full universe (not Testing A's top-500)
    assert abs(slot_notional(a) - 1_000) < 1e-6
    monkeypatch.setenv("MCF_ACCOUNT", acct)
    assert {s.name for s in build_strategies(cfg)} == own                         # nothing from default.yaml leaks in
    assert G.has_setups(acct) is True                                             # the session guard now chases it


def test_workflows_route_every_account():
    tr, wd, eod = ((WF / f).read_text() for f in ("trade.yml", "watchdog.yml", "eod.yml"))
    for wf in (tr, wd, eod):
        assert MATRIX in wf
    for acct, (pre, br, grp, sec) in ALL.items():
        for wf in (tr, wd):
            assert _eval(_expr(wf, "MCF_COID_PREFIX"), acct) == pre, acct
        for wf in (tr, wd, eod):
            assert _eval(_expr(wf, "ALPACA_TRADE_API_KEY"), acct) == (f"<ALPACA_{sec}_API_KEY>" if sec else ""), acct
            assert _eval(_expr(wf, "ALPACA_TRADE_SECRET_KEY"), acct) == (f"<ALPACA_{sec}_SECRET_KEY>" if sec else ""), acct
            assert _eval(_expr(wf, "STATE_BRANCH"), acct) == br, acct
            # market data: with repo variable MCF_DEF_OWN_DATA_KEYS == 'true', Testing D / E / F use their own keys; unset
            # (default: their keys had no SIP plan on 11-11), everyone uses the shared SIP keys; other accounts always do
            for on in (True, False):
                own = on and acct in DEF
                for kind in ("API", "SECRET"):
                    ex = _expr(wf, f"ALPACA_{kind}_KEY").replace("vars.MCF_DEF_OWN_DATA_KEYS == 'true'", repr(on))
                    want = f"<ALPACA_{sec}_{kind}_KEY>" if own else f"<ALPACA_{kind}_KEY>"
                    assert _eval(ex, acct) == want, (acct, kind, on)
        assert _eval(_expr(tr, "group"), acct) == grp, acct
    for acct in DEF:                                                              # skipped until BOTH secrets are set
        assert f'[ "$MCF_ACCOUNT" = "{acct}" ]' in tr
    assert "steps.setups.outputs.run == 'true'" in tr.split("- name: Trade")[1]


def test_guard_longhold_account_check_know_the_accounts():
    from mcf.execution import session_guard as G
    from mcf.longhold.broker import KEY_ENVS_FORBIDDEN

    sg, lh, ac = ((WF / f).read_text() for f in ("session-guard.yml", "longhold.yml", "account-check.yml"))
    for acct, (_, _, s) in DEF.items():
        assert acct in G.ACCOUNTS                                                 # handover.py staggers by this list
        assert f"secrets.ALPACA_{s}_API_KEY != '' && secrets.ALPACA_{s}_SECRET_KEY != ''" in sg
        assert f'accts="$accts,{acct}"' in sg
        assert f"ALPACA_{s}_API_KEY" in KEY_ENVS_FORBIDDEN and f"secrets.ALPACA_{s}_API_KEY" in lh
        assert _eval(_expr(ac, "ALPACA_TRADE_API_KEY").replace("inputs.account", "matrix.account"), acct) == f"<ALPACA_{s}_API_KEY>"
        assert acct in ac.split("options:")[1].split("\n")[0]
    assert "/orders" not in ac and "-X POST" not in ac and "DELETE" not in ac       # the account check stays read-only


def test_prefixes_unique():
    from mcf.execution.outage import MCF_PREFIXES, check_prefix

    for _, pre, _ in DEF.values():
        assert pre in MCF_PREFIXES
        check_prefix(pre)
    assert len(set(MCF_PREFIXES)) == len(MCF_PREFIXES) and "mcl-" not in MCF_PREFIXES
    assert not any(a != b and a.startswith(b) for a in MCF_PREFIXES for b in MCF_PREFIXES)
    assert len({p for p, *_ in ALL.values()}) == len(ALL)


def test_labels_reports_and_dashboard():
    from mcf.replay import export, harness
    from mcf.report import assignments as A
    from mcf.report import daily_post as P
    from mcf.report import inactive, intraday, reconcile_pl, team
    from mcf.research import allocate

    html = (ROOT / "docs/live/index.html").read_text()
    rep = (ROOT / "docs/live/report.html").read_text()
    d = json.loads(A.OUT.read_text())
    post = {k: br for k, _, br, _ in P.ACCOUNTS}
    for acct, (label, _, s) in DEF.items():
        br = f"mcf-data-{acct}"
        assert A.ACCOUNTS[acct] == label and d["labels"][acct] == label and len(d["accounts"][acct]) == 10   # filled 11-12
        assert post[acct] == br and acct in P.LB_ACCOUNTS and acct in P.COLORS and acct in P.TOTALS_EXCLUDED
        assert team.ACCOUNT_TAG[acct] == label and team.ACCOUNT_BRANCH[acct] == br and allocate.LABEL[acct] == label
        assert br in inactive.BRANCHES and intraday.BRANCH[acct] == br
        assert reconcile_pl.BRANCH[acct] == br and reconcile_pl.KEYS[acct] == f"ALPACA_{s}"
        assert acct in export.ACCOUNTS and harness.data_branch(acct) == f"origin/{br}"
        assert f'k: "{acct}", name: "{label}"' in html
        assert f'{acct}: ["{label}", "{br}", "?account={acct}"]' in html
        assert f'["{acct}", "{label}", "{br}", "?account={acct}"]' in html
        assert f'{acct}: "{br}"' in rep and f'?account={acct}">{label}</a>' in html


def test_ledger_entry():
    rows = [json.loads(x) for x in (ROOT / "research/ledger.jsonl").read_text().splitlines() if x.strip()]
    e = [r for r in rows if r["id"] == "2026-11-11-testing-def-accounts"]
    assert len(e) == 1 and e[0]["effective"] == "2026-11-12" and e[0]["kind"] == "process"
