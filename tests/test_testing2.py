"""Testing 2 account (owner 2026-10-12): the overlay runs only its own CWT batch, every module loads and runs through
the live LabStrategy, and the workflows route it to its own keys, prefix and state branch. Educational only."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _cfg(monkeypatch):
    from mcf.config import load_config

    monkeypatch.setenv("MCF_ACCOUNT", "testing2")
    return load_config()


def test_overlay_runs_only_the_cwt_batch(monkeypatch):
    from mcf.strategies.setups import LabStrategy, build_strategies

    cfg = _cfg(monkeypatch)
    assert cfg["account_name"] == "testing2"
    st = build_strategies(cfg)
    assert st and all(isinstance(s, LabStrategy) for s in st)
    assert all(s.name.startswith("CWT") for s in st)
    default = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    assert not any(cfg["strategies"][k].get("enabled") for k in default)      # primary + library all off
    testing1 = yaml.safe_load((ROOT / "config/account_testing.yaml").read_text())["strategies"]
    assert not ({s.name for s in st} & {k for k, v in testing1.items() if v.get("enabled")})
    order = cfg["live"]["setup_order"]
    assert sorted(order) == sorted(s.name for s in st)                          # every setup has a priority


def test_every_module_runs_in_the_live_lab_strategy(monkeypatch):
    from mcf.strategies.setups import _LAB_FRAMES, build_strategies

    st = build_strategies(_cfg(monkeypatch))
    idx = pd.date_range("2026-10-12 09:30", periods=390, freq="1min", tz="America/New_York")
    rng = np.random.default_rng(0)
    px = 100 + np.cumsum(rng.normal(0, 0.08, 390))
    bars = pd.DataFrame({"open": px, "high": px + 0.06, "low": px - 0.06, "close": px,
                         "volume": rng.integers(500, 5000, 390).astype(float)}, index=idx)
    for n in (25, 120, 390):
        _LAB_FRAMES.clear()
        ctx = SimpleNamespace(symbol="T2TEST", date=idx[0].date(), bars=bars.iloc[:n], prior5=None, atr=1.5,
                              prev_close=100.0, prev_high=100.8, prev_low=99.2, avg_dollar_volume=2e8)
        for s in st:
            for sig in s.generate(ctx):
                assert sig.side == s.side and sig.stop != sig.target


def test_workflows_route_testing2_to_its_own_account():
    tr = (ROOT / ".github/workflows/trade.yml").read_text()
    eod = (ROOT / ".github/workflows/eod.yml").read_text()
    assert "account: [primary, testing, testing2]" in tr and "account: [primary, testing, testing2]" in eod
    for s in ("mt2-", "mcf-data-testing2", "mcf-trade-testing2", "ALPACA_TESTING2_API_KEY", "ALPACA_TESTING2_SECRET_KEY"):
        assert s in tr
    assert "mcf-data-testing2" in eod
    # without its keys the job must skip (it would otherwise fall back to the primary account's keys)
    assert '[ "$MCF_ACCOUNT" != "primary" ] && [ -z "$ALPACA_TRADE_API_KEY" ]' in tr
