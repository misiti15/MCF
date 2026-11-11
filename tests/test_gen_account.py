"""Setup Generator account (owner 2026-10-19): the overlay runs only GEN-* setups, routes to its own keys / prefix /
state branch, skips cleanly without keys, sends no EOD email, and the dashboard keeps generated setups in their own
leaderboard. Educational only."""
import re
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _cfg(monkeypatch, acct="gen"):
    from mcf.config import load_config

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    return load_config()


def test_config_loads_with_300_equal_slots(monkeypatch):   # owner REPV-1 / REPV-5 2026-11-11 (was 200 x 3.8, cap 48; 80 before GX2)
    from mcf.backtest.engine import slot_notional
    from mcf.research.generator import apply as GA

    cfg = _cfg(monkeypatch)
    a = cfg["account"]
    assert cfg["account_name"] == "gen"
    assert a["slots"] == 300 and a["max_concurrent_positions"] == 300 and a["max_positions_per_strategy"] == 150
    assert a["buying_power_multiple"] == 1.8                                      # smaller lots: ~$540 at $89k
    testing = yaml.safe_load((ROOT / "config/account_testing.yaml").read_text())["account"]
    assert a["max_daily_loss_r"] == testing["max_daily_loss_r"] == 300           # the testing-area halt (was 120)
    assert abs(slot_notional({**a, "equity": 100000}) - 100000 * a["buying_power_multiple"] / 300) < 1e-6
    for k in ("slots", "buying_power_multiple", "max_concurrent_positions", "max_positions_per_strategy", "max_daily_loss_r"):
        assert GA.BASE["account"][k] == a[k], k                                   # the generator writes the same base


def test_only_gen_setups_run(monkeypatch):
    from mcf.strategies.setups import LabStrategy, build_strategies

    cfg = _cfg(monkeypatch)
    st = build_strategies(cfg)
    assert all(isinstance(s, LabStrategy) and s.name.startswith("GEN-") for s in st)
    on = {k for k, v in cfg["strategies"].items() if v.get("enabled")}
    assert all(k.startswith("GEN-") for k in on)
    for f in ("config/default.yaml", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "config").glob("account_*.yaml")
                                                if p.name != "account_gen.yaml")):
        other = yaml.safe_load((ROOT / f).read_text())["strategies"] or {}
        assert not (on & {k for k, v in other.items() if (v or {}).get("enabled")}), f   # one home: graduates are off here
    assert sorted(cfg["live"]["setup_order"]) == sorted(s.name for s in st)


def test_exclusive_switches_off_future_default_setups(monkeypatch, tmp_path):
    """A setup added to config/default.yaml later must not leak into the gen account."""
    import mcf.config as C

    d = yaml.safe_load((ROOT / "config/default.yaml").read_text())
    d["strategies"]["brand_new_primary_setup"] = {"enabled": True, "type": "lab", "module": "x.py"}
    (tmp_path / "default.yaml").write_text(yaml.safe_dump(d))
    (tmp_path / "account_gen.yaml").write_text((ROOT / "config/account_gen.yaml").read_text())
    monkeypatch.setattr(C, "CONFIG_DIR", tmp_path)
    monkeypatch.setenv("MCF_ACCOUNT", "gen")
    cfg = C.load_config()
    assert cfg["strategies"]["brand_new_primary_setup"]["enabled"] is False
    monkeypatch.setenv("MCF_ACCOUNT", "primary")
    assert C.load_config()["strategies"]["brand_new_primary_setup"]["enabled"] is True


def test_other_accounts_unchanged_by_the_loader(monkeypatch):
    for acct in ("primary", "testing", "testing2", "graveyard"):
        cfg = _cfg(monkeypatch, acct)
        assert not any(k.startswith("GEN-") for k in cfg["strategies"])
    # GEN-GRAD (owner 2026-11-11): graduates run only in the testing areas (never Primary / On Deck / Graveyard), off in Gen
    gen = _cfg(monkeypatch, "gen")["strategies"]
    for acct in ("explore1", "livelab", "testingd", "testinge", "testingf"):
        for k, v in _cfg(monkeypatch, acct)["strategies"].items():
            if k.startswith("GEN-") and v.get("enabled"):
                assert k in gen and not gen[k]["enabled"], (acct, k)


def test_every_gen_module_runs_in_the_live_lab_strategy(monkeypatch):
    from mcf.strategies.setups import _LAB_FRAMES, build_strategies

    st = build_strategies(_cfg(monkeypatch))
    idx = pd.date_range("2026-10-19 09:30", periods=390, freq="1min", tz="America/New_York")
    rng = np.random.default_rng(1)
    px = 100 + np.cumsum(rng.normal(0, 0.08, 390))
    bars = pd.DataFrame({"open": px, "high": px + 0.06, "low": px - 0.06, "close": px,
                         "volume": rng.integers(500, 5000, 390).astype(float)}, index=idx)
    spy = bars * 1.0
    for n in (25, 120, 390):
        _LAB_FRAMES.clear()
        ctx = SimpleNamespace(symbol="GENTEST", date=idx[0].date(), bars=bars.iloc[:n], prior5=None, atr=1.5,
                              prev_close=100.0, prev_high=100.8, prev_low=99.2, avg_dollar_volume=5e8,
                              peers={"GENTEST": bars.iloc[:n], "SPY": spy.iloc[:n], "QQQ": spy.iloc[:n]})
        for s in st:
            # every generated setup has a market-context filter (hand-added observation setups may not, pod1022)
            assert s.context or "observation" in (getattr(s, "tags", None) or []), s.name
            for sig in s.generate(ctx):
                assert sig.side == s.side and sig.stop != sig.target


def test_workflows_route_gen_to_its_own_account():
    tr = (ROOT / ".github/workflows/trade.yml").read_text()
    eod = (ROOT / ".github/workflows/eod.yml").read_text()
    wd = (ROOT / ".github/workflows/watchdog.yml").read_text()
    for wf in (tr, eod, wd):
        assert "account: [primary, testing, testing2, gen" in wf          # the matrix may grow (graveyard, 2026-10-21)
        assert "(matrix.account == 'gen' && 'mcf-data-gen'" in wf
    for wf in (tr, wd):
        assert "(matrix.account == 'gen' && 'mcg-'" in wf
        assert "secrets.ALPACA_GEN_API_KEY" in wf and "secrets.ALPACA_GEN_SECRET_KEY" in wf
    assert "mcf-trade-gen" in tr
    # skipped cleanly without its keys (never falls back to the primary keys)
    assert '[ "$MCF_ACCOUNT" != "primary" ] && [ -z "$ALPACA_TRADE_API_KEY" ]' in tr
    assert '[ "$MCF_ACCOUNT" = "gen" ]' in tr and '} && [ -z "$ALPACA_TRADE_SECRET_KEY" ]' in tr
    # market data stays on the primary SIP keys
    assert "ALPACA_API_KEY: ${{ secrets.ALPACA_API_KEY }}" in tr
    # no EOD email for gen: only primary sends
    assert "matrix.account != 'primary' && '--no-send'" in eod


def test_prefix_is_allowed_for_flatten_and_separate():
    from mcf.execution.outage import MCF_PREFIXES
    from mcf.longhold.broker import KEY_ENVS_FORBIDDEN

    assert "mcg-" in MCF_PREFIXES and len(set(MCF_PREFIXES)) == len(MCF_PREFIXES)
    assert not any(p != "mcg-" and p.startswith("mcg") for p in MCF_PREFIXES)
    assert "ALPACA_GEN_API_KEY" in KEY_ENVS_FORBIDDEN


def test_gen_setups_have_generated_display_names():
    names = yaml.safe_load((ROOT / "config/setup_names.yaml").read_text())
    st = yaml.safe_load((ROOT / "config/account_gen.yaml").read_text())["strategies"]
    for k, v in st.items():
        if "observation" in (v.get("tags") or []):
            # hand-added observation setups (owner 2026-10-23, pod1022): own id range and a plain display name
            assert re.match(r"^GEN-POD\d{4}-\d{2}-", k) and v["gen"].get("source")
            assert not names[k]["name"].startswith("Generated: ") and names[k]["what"]
        else:
            assert k.startswith("GEN-") and re.match(r"^GEN-\d{6}-\d{2}-", k)
            assert names[k]["name"].startswith("Generated: ") and names[k]["what"]
        sc = v["gen"]["screen"]
        assert {"train", "valid", "per_day"} <= set(sc)              # screen stats recorded, negative or not
    others = set()   # GEN-GRAD graduates (testing areas B-F) keep their generated id and display name
    for f in ("config/default.yaml", "config/account_testing.yaml", "config/account_testing2.yaml"):
        others |= set(yaml.safe_load((ROOT / f).read_text())["strategies"])
    assert not any(k.startswith("GEN-") for k in others)
    assert not any(names[k]["name"].startswith("Generated: ") for k in others if k in names)


def test_dashboard_keeps_generated_setups_separate():
    html = (ROOT / "docs/live/index.html").read_text()
    assert 'id="gen-card"' in html and "Generated setups leaderboard" in html
    assert 'k: "gen", name: "Setup Generator"' in html                  # all-accounts overview
    # main leaderboard drops GEN rows; the generated card keeps only GEN rows
    assert "!isGen(r.setup)" in html and "isGen(r.setup)" in html
    assert "GENERATED</span>" in html
