"""Live Lab + Explore 1 + Explore 2 paper accounts (owner 2026-11-03). Wired like the Graveyard / Setup Generator: each
overlay runs only its own setups (none yet), ~$1,000 constant notional lots (200 slots, buying power x 2.0), up to 10
lots per setup, the per-setup daily stop off and the Testing 120R account backstop; each routes to its own keys / order
prefix / state branch, skips cleanly without keys (and while no setup is enabled), sends no EOD email and shows on the
dashboard. Educational only - not financial advice."""
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
NEW = {"livelab": ("Live Lab", "mll-", "LIVELAB"), "explore1": ("Explore 1", "mx1-", "EXPLORE1"),
       "explore2": ("Explore 2", "mx2-", "EXPLORE2")}
OLD = {"primary": ("mcf-", "mcf-data", "mcf-trade", None), "testing": ("mct-", "mcf-data-testing", "mcf-trade-testing", "TESTING"),
       "testing2": ("mt2-", "mcf-data-testing2", "mcf-trade-testing2", "TESTING2"),
       "gen": ("mcg-", "mcf-data-gen", "mcf-trade-gen", "GEN"),
       "graveyard": ("mgy-", "mcf-data-graveyard", "mcf-trade-graveyard", "GRAVEYARD")}
EXPECT = {**OLD, **{k: (p, f"mcf-data-{k}", f"mcf-trade-{k}", s) for k, (_, p, s) in NEW.items()}}
MATRIX = "account: [primary, testing, testing2, gen, graveyard, livelab, explore1, explore2]"


def _cfg(monkeypatch, acct):
    from mcf.config import load_config

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    return load_config()


def _eval(expr: str, acct: str):
    """Evaluate a GitHub Actions `a == 'x' && v || ...` chain for one matrix value (non-empty dummy secrets)."""
    py = expr.replace("&&", " and ").replace("||", " or ")
    py = re.sub(r"matrix\.account == ('[^']*')", lambda m: f"(acct == {m.group(1)})", py)
    py = re.sub(r"secrets\.(\w+)", lambda m: repr("<" + m.group(1) + ">"), py)
    return eval(py, {}, {"acct": acct})   # noqa: S307 - test-only, on our own workflow text


def _expr(wf: str, key: str) -> str:
    m = re.search(rf"^\s+{key}: \$\{{\{{ (.*) \}}\}}$", wf, re.M)
    assert m, key
    return m.group(1)


@pytest.mark.parametrize("acct", sorted(NEW))
def test_overlay_sizing_and_no_setups_yet(monkeypatch, acct):
    from mcf.backtest.engine import slot_notional
    from mcf.strategies.setups import build_strategies

    raw = yaml.safe_load((ROOT / f"config/account_{acct}.yaml").read_text())
    assert raw["strategies_exclusive"] is True and not raw.get("strategies")
    cfg = _cfg(monkeypatch, acct)
    a, live = cfg["account"], cfg["live"]
    assert cfg["account_name"] == acct
    assert a["slots"] == 200 and a["max_concurrent_positions"] == 200 and a["buying_power_multiple"] == 2.0
    assert a["max_positions_per_strategy"] == 10 and a["max_setup_daily_loss_r"] is None
    t1 = _cfg(monkeypatch, "testing")["account"]
    assert a["max_daily_loss_r"] == t1["max_daily_loss_r"] == 120                  # the Testing account backstop
    assert a["risk_per_trade_pct"] == t1["risk_per_trade_pct"]
    assert live["setup_order"] == [] and live["scale_out_max_per_day"] == 0 and live["block_twin_same_symbol"] is False
    monkeypatch.setenv("MCF_ACCOUNT", acct)
    assert build_strategies(cfg) == []                                             # nothing from default.yaml leaks in
    assert abs(slot_notional(a) - 1_000) < 1e-6                                   # ~$1,000 constant notional per lot


def test_trade_workflow_routes_every_account():
    tr = (ROOT / ".github/workflows/trade.yml").read_text()
    wd = (ROOT / ".github/workflows/watchdog.yml").read_text()
    eod = (ROOT / ".github/workflows/eod.yml").read_text()
    for wf in (tr, wd, eod):
        assert MATRIX in wf
    for acct, (pre, br, grp, sec) in EXPECT.items():
        for wf in (tr, wd):
            assert _eval(_expr(wf, "MCF_COID_PREFIX"), acct) == pre, acct
            assert _eval(_expr(wf, "ALPACA_TRADE_API_KEY"), acct) == (f"<ALPACA_{sec}_API_KEY>" if sec else ""), acct
            assert _eval(_expr(wf, "ALPACA_TRADE_SECRET_KEY"), acct) == (f"<ALPACA_{sec}_SECRET_KEY>" if sec else ""), acct
        for wf in (tr, wd, eod):
            assert _eval(_expr(wf, "STATE_BRANCH"), acct) == br, acct
        assert _eval(_expr(tr, "group"), acct) == grp, acct
    for acct in NEW:                                                               # skipped until BOTH secrets are set
        assert f'[ "$MCF_ACCOUNT" = "{acct}" ]' in tr
    assert "steps.setups.outputs.run == 'true'" in tr.split("- name: Trade")[1]   # and while no setup is enabled
    assert "matrix.account != 'primary' && '--no-send'" in eod                    # no EOD email


def test_session_guard_and_longhold_know_the_accounts(tmp_path):
    from mcf.execution import session_guard as G
    from mcf.longhold.broker import KEY_ENVS_FORBIDDEN

    sg = (ROOT / ".github/workflows/session-guard.yml").read_text()
    lh = (ROOT / ".github/workflows/longhold.yml").read_text()
    for acct, (_, _, s) in NEW.items():
        assert acct in G.ACCOUNTS
        assert f"secrets.ALPACA_{s}_API_KEY != '' && secrets.ALPACA_{s}_SECRET_KEY != ''" in sg
        assert f'accts="$accts,{acct}"' in sg
        assert f"ALPACA_{s}_API_KEY" in KEY_ENVS_FORBIDDEN and f"secrets.ALPACA_{s}_API_KEY" in lh
        assert G.has_setups(acct) is False                                        # empty: trade.yml skips, guard does not chase it
    for acct in ("primary", "testing", "testing2", "gen", "graveyard"):
        assert G.has_setups(acct) is True
    (tmp_path / "account_x.yaml").write_text("strategies_exclusive: true\nstrategies:\n  s1: {enabled: true}\n")
    assert G.has_setups("x", tmp_path) is True
    assert G.has_setups("missing", tmp_path) is True                              # unreadable: keep guarding


def test_prefixes_unique_and_watchdog_accepts_them():
    from mcf.execution.outage import MCF_PREFIXES, check_prefix

    for _, pre, _ in NEW.values():
        assert pre in MCF_PREFIXES
        check_prefix(pre)
    assert len(set(MCF_PREFIXES)) == len(MCF_PREFIXES) and "mcl-" not in MCF_PREFIXES   # long-hold book never touched
    assert not any(a != b and a.startswith(b) for a in MCF_PREFIXES for b in MCF_PREFIXES)


def test_reports_and_dashboard_list_the_accounts():
    import json

    from mcf.replay import export, harness
    from mcf.report import assignments as A
    from mcf.report import daily_post as P

    html = (ROOT / "docs/live/index.html").read_text()
    rep = (ROOT / "docs/live/report.html").read_text()
    d = json.loads(A.OUT.read_text())
    post = {k: br for k, _, br, _ in P.ACCOUNTS}
    for acct, (label, _, _) in NEW.items():
        assert A.ACCOUNTS[acct] == label and d["labels"][acct] == label and d["accounts"][acct] == []
        assert post[acct] == f"mcf-data-{acct}" and acct in P.LB_ACCOUNTS and acct in P.COLORS
        assert acct in export.ACCOUNTS and harness.data_branch(acct) == f"origin/mcf-data-{acct}"
        assert f'k: "{acct}", name: "{label}"' in html                           # all-accounts card
        assert f'{acct}: ["{label}", "mcf-data-{acct}", "?account={acct}"]' in html   # account switch
        assert f'["{acct}", "{label}", "mcf-data-{acct}", "?account={acct}"]' in html
        assert f'{acct}: "mcf-data-{acct}"' in rep and f'?account={acct}">{label}</a>' in html


def test_post_skips_accounts_not_started(monkeypatch):
    from mcf.report import daily_post as P

    monkeypatch.setattr(P, "_show", lambda br, path: {"session_date": "2026-11-03"} if br in ("mcf-data", "mcf-data-testing") else None)
    got = [a["k"] for a in P.accounts("2026-11-03")]
    assert not set(got) & set(NEW) and got[:2] == ["primary", "testing"]
