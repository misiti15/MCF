"""Graveyard account (owner 2026-10-20, from session 2026-10-21): wired like the Setup Generator account. The overlay
runs only its own setups (lowest performers moved from Testing 1 / Testing 2, nothing deleted), with lower caps than
Testing; routes to its own keys / prefix / state branch, skips cleanly without keys, sends no EOD email, and shows on
the dashboard. Every moved setup is off at its source (promotion = move). Educational only."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MOVED_T2 = {"LIQ-orl-sweep-open15-s25-long", "RW2-exhaustion-noon-adv150-short-FD", "heat_fade_long",
            "CWT14-failbrk-orl-p10-lowvol-long", "CWT14-failbrk-orl-p10-long", "CWT14-failbrk-orl-p05-lowvol-long",
            "CWT14-failbrk-orl-p05-long",   # the 4 CWT14 orl longs moved 2026-10-21 (owner 2026-10-20 N4)
            "CWT09-gapdn-bounce-g5-lowerhalf-short",   # owner 2026-10-20 evening
            "CWT14-failbrk-pdh-p10-lowvol-short"}   # owner 2026-10-22 (N6)
MOVED_T1 = {"CWT14-failbrk-pdh-p05-lowvol-short",   # owner 2026-10-22 (N6)
            "RW6-ns2-up3-short-FD", "NS2-sma50break-overbought-short-FD", "heat_fade_long-FD", "ST1-ordn-long-pm-t05s1-FD",
            "MF1-945-flowsell-vwapup-FD", "heat_fade_short-FD", "ST2-slope20up-long-am-t05s1-FD",
            "NS2-sma50break-overbought-short", "heat_fade_short"}
# combined live win rate > 50% on 2026-10-20 (owner rule): stayed in Testing 1
STAYED_T1 = {"L3-gap-slope-lowdist-FD", "exhaustion_short-FD"}   # L3-gap-slope-fromopen-FD: promoted to Primary 2026-10-21


def _cfg(monkeypatch, acct="graveyard"):
    from mcf.config import load_config

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    return load_config()


def _on(cfg):
    return {k for k, v in cfg["strategies"].items() if isinstance(v, dict) and v.get("enabled")}


def test_caps_lower_than_testing(monkeypatch):
    cfg = _cfg(monkeypatch)
    a, live = cfg["account"], cfg["live"]
    t2 = yaml.safe_load((ROOT / "config/account_testing2.yaml").read_text())["account"]
    assert cfg["account_name"] == "graveyard"
    assert a["slots"] == t2["slots"] // 2 and a["max_concurrent_positions"] == t2["max_concurrent_positions"] // 2
    assert a["max_positions_per_strategy"] == t2["max_positions_per_strategy"] // 2
    assert a["max_trades_per_day"] < t2["max_trades_per_day"]
    assert a["risk_per_trade_pct"] == _cfg(monkeypatch, "testing2")["account"]["risk_per_trade_pct"]
    assert a["max_setup_daily_loss_r"] == 2.0 and a["max_daily_loss_r"] == 120
    assert live["block_twin_same_symbol"] is True
    assert live["scale_out_max_per_day"] == 0
    for k, v in cfg["strategies"].items():
        if k in _on(cfg):
            assert not v.get("live_scale_out") and not v.get("ticker_split"), k   # no live scale-out, no split copies


def test_only_its_own_setups_run(monkeypatch):
    from mcf.strategies.setups import build_strategies

    cfg = _cfg(monkeypatch)
    own = set(yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text())["strategies"])
    on = _on(cfg)
    assert on == own == MOVED_T1 | MOVED_T2
    st = build_strategies(cfg)
    assert {s.name for s in st} == on
    assert sorted(cfg["live"]["setup_order"]) == sorted(on)                  # every setup has a priority


def test_exclusive_switches_off_future_default_setups(monkeypatch, tmp_path):
    import mcf.config as C

    d = yaml.safe_load((ROOT / "config/default.yaml").read_text())
    d["strategies"]["brand_new_primary_setup"] = {"enabled": True, "type": "lab", "module": "x.py"}
    (tmp_path / "default.yaml").write_text(yaml.safe_dump(d))
    (tmp_path / "account_graveyard.yaml").write_text((ROOT / "config/account_graveyard.yaml").read_text())
    monkeypatch.setattr(C, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MCF_ACCOUNT", "graveyard")
    assert C.load_config()["strategies"]["brand_new_primary_setup"]["enabled"] is False


def test_moves_switched_off_at_source(monkeypatch):
    t1, t2 = _on(_cfg(monkeypatch, "testing")), _on(_cfg(monkeypatch, "testing2"))
    assert not (MOVED_T1 & t1) and not (MOVED_T2 & t2)
    assert STAYED_T1 <= t1
    for acct, on in (("testing", t1), ("testing2", t2)):
        order = _cfg(monkeypatch, acct)["live"]["setup_order"]
        assert not ((MOVED_T1 | MOVED_T2) & set(order)), acct
    grave = yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text())["strategies"]
    for k in ("heat_fade_long", "heat_fade_short", "NS2-sma50break-overbought-short"):
        assert grave[k]["former_primary"]                                     # markers kept
    assert "# moved to Graveyard 2026-10-21 (owner)" in (ROOT / "config/account_graveyard.yaml").read_text()


def test_workflows_route_graveyard_to_its_own_account():
    tr = (ROOT / ".github/workflows/trade.yml").read_text()
    eod = (ROOT / ".github/workflows/eod.yml").read_text()
    wd = (ROOT / ".github/workflows/watchdog.yml").read_text()
    for wf in (tr, eod, wd):
        assert "account: [primary, testing, testing2, gen, graveyard]" in wf
        assert "(matrix.account == 'graveyard' && 'mcf-data-graveyard'" in wf
    for wf in (tr, wd):
        assert "(matrix.account == 'graveyard' && 'mgy-'" in wf
        assert "secrets.ALPACA_GRAVEYARD_API_KEY" in wf and "secrets.ALPACA_GRAVEYARD_SECRET_KEY" in wf
    assert "mcf-trade-graveyard" in tr
    assert '[ "$MCF_ACCOUNT" != "primary" ] && [ -z "$ALPACA_TRADE_API_KEY" ]' in tr
    assert '[ "$MCF_ACCOUNT" = "graveyard" ]; } && [ -z "$ALPACA_TRADE_SECRET_KEY" ]' in tr
    assert "matrix.account != 'primary' && '--no-send'" in eod                # no EOD email


def test_prefix_and_key_separation():
    from mcf.execution.outage import MCF_PREFIXES
    from mcf.longhold.broker import KEY_ENVS_FORBIDDEN

    assert "mgy-" in MCF_PREFIXES and len(set(MCF_PREFIXES)) == len(MCF_PREFIXES)
    assert not any(a != b and a.startswith(b) for a in MCF_PREFIXES for b in MCF_PREFIXES)
    assert "ALPACA_GRAVEYARD_API_KEY" in KEY_ENVS_FORBIDDEN


def test_dashboard_and_assignments_know_the_graveyard():
    import json

    from mcf.report import assignments as A

    html = (ROOT / "docs/live/index.html").read_text()
    assert 'k: "graveyard", name: "Graveyard"' in html                         # all-accounts card
    assert 'graveyard: ["Graveyard", "mcf-data-graveyard", "?account=graveyard"]' in html   # account switch
    assert 'graveyard: ["Graveyard", "mcf-data-graveyard"] }' in html          # leaderboard
    assert A.ACCOUNTS.get("graveyard") == "Graveyard"
    d = json.loads(A.OUT.read_text())
    assert d["labels"]["graveyard"] == "Graveyard" and set(d["accounts"]["graveyard"]) == MOVED_T1 | MOVED_T2
