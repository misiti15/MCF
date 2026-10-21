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
    # moved from Testing 1 2026-10-20, then on to the separate Graveyard account 2026-10-21 (owner): off here
    grave = {"heat_fade_long", "RW2-exhaustion-noon-adv150-short-FD", "LIQ-orl-sweep-open15-s25-long"}
    assert st and all(isinstance(s, LabStrategy) for s in st)
    # CWT batch + near-misses (LD: longs1020) + testing setups placed here by the Testing 1/2 allocator (2026-10-21)
    placed = {k for k, v in cfg["strategies"].items() if isinstance(v, dict) and v.get("enabled")
              and not k.startswith(("CWT", "NM", "LD"))}
    assert placed <= {s.name for s in st}
    assert not (grave & {s.name for s in st})
    default = yaml.safe_load((ROOT / "config/default.yaml").read_text())["strategies"]
    primary = {k for k, v in default.items() if isinstance(v, dict) and v.get("enabled")}
    assert not any(cfg["strategies"][k].get("enabled") for k in primary)          # Primary's setups are off here
    testing1 = yaml.safe_load((ROOT / "config/account_testing.yaml").read_text())["strategies"]
    both = {s.name for s in st} & {k for k, v in testing1.items() if v.get("enabled")}
    assert all(cfg["strategies"][k].get("ticker_split") for k in both)           # only split-ticker copies run in both
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
    for wf in (tr, eod):                      # the matrix may grow (Setup Generator "gen", 2026-10-19)
        assert "account: [primary, testing, testing2" in wf
    for s in ("mt2-", "mcf-data-testing2", "mcf-trade-testing2", "ALPACA_TESTING2_API_KEY", "ALPACA_TESTING2_SECRET_KEY"):
        assert s in tr
    assert "mcf-data-testing2" in eod
    # without its keys the job must skip (it would otherwise fall back to the primary account's keys)
    assert '[ "$MCF_ACCOUNT" != "primary" ] && [ -z "$ALPACA_TRADE_API_KEY" ]' in tr


def test_structural_exit_uses_the_module_stop_and_no_target():
    """GEOM "S" (opt-in): stop from the module's stop_price, no target, flat 15:55; t-geometry modules unchanged."""
    from mcf.strategies.setups import _LAB_FRAMES, LabStrategy

    st = LabStrategy("A7T1", "research/bdi/cwt/live/CWT09-gapdn-vwaploss-g10-short.py", window=[1030, 1500])
    assert st.structural and st.mod.GEOM == "S"
    idx = pd.date_range("2026-10-12 09:30", periods=390, freq="1min", tz="America/New_York")
    # gap down 12%: dips, bounces above VWAP by 10:00 (high 91.5 at ~10:05), fades below VWAP after 10:30
    px = np.r_[np.linspace(88, 86, 15), np.linspace(86, 91, 20), np.linspace(91, 89.5, 30), np.linspace(89.5, 86, 325)]
    bars = pd.DataFrame({"open": px, "high": px + 0.05, "low": px - 0.05, "close": px, "volume": 10000.0}, index=idx)
    _LAB_FRAMES.clear()
    ctx = SimpleNamespace(symbol="A7TEST", date=idx[0].date(), bars=bars, prior5=None, atr=3.0, prev_close=100.0,
                          prev_high=101.0, prev_low=99.0, avg_dollar_volume=5e7)
    sig = st.generate(ctx)
    assert len(sig) == 1 and sig[0].side == -1 and sig[0].target is None
    end = bars.index[sig[0].bar_index] + pd.Timedelta(minutes=1)
    assert end.hour * 100 + end.minute >= 1030
    assert abs(sig[0].stop - (bars["high"].iloc[:60].max())) < 1e-9          # the 09:30-10:30 high
    geo = LabStrategy("B2", "research/bdi/cwt/live/CWT13-vwapstretch-z05-short.py")
    assert not geo.structural and (geo.up, geo.dn) == (1.0, 1.0)


def test_longs1020_and_m1_observation_setups(monkeypatch):
    """Owner 2026-10-20: LD1-LD8 (longs1020) + M1 (mf3swarm1020) run in Testing 2 as observation-only lab setups; the
    ETF ones pin their instrument, every one reads its context, the overlapping ones share a twin_group."""
    from mcf.backtest.engine import pinned_symbols
    from mcf.strategies.setups import build_strategies

    cfg = _cfg(monkeypatch)
    st = {s.name: s for s in build_strategies(cfg)}
    want = {"LD1-ns1-breadthup-t05s1-long": ("t05s1", ("breadth",), None),
            "LD2-qqq-dip015-breadthturn-tqqq-t05s1-long": ("t05s1", ("qqq_fo", "breadth"), {"TQQQ"}),
            "LD3-st2-idxturn-t05s1-long": ("t05s1", ("spy_fo",), None),
            "LD4-st4-breadthup-t1s05-long": ("t1s05", ("breadth",), None),
            "LD5-st2-breadthup-t05s1-long": ("t05s1", ("breadth",), None),
            "LD6-spy-dip020atr-breadthturn-spxl-holdtr-long": ("holdtr", ("spy_fo", "breadth"), {"SPXL"}),
            "LD7-ns1-idxturn-holdtr-long": ("holdtr", ("spy_fo",), None),
            "LD8-spy-dip030-breadthturn-spxl-holdtr-long": ("holdtr", ("spy_fo", "breadth"), {"SPXL"}),
            "NM-MF3-qqqdn-gapdn-FD": ("t1s1", ("qqq_fo",), None)}
    for n, (geom, ctx, syms) in want.items():
        s = st[n]
        assert (s.geom, s.context, s.symbols) == (geom, ctx, syms), n
        assert s.side == (-1 if n.startswith("NM-MF3") else 1) and not s.refire and s.params.get("scale_out_r") is None
        assert tuple(cfg["strategies"][n]["window"]) == tuple(getattr(s.mod, "WINDOW", None) or (950, 1500)), n
        if geom == "holdtr":
            assert s.params["trail_r"] == 1.0 and s.params["trail_after_r"] == 1.0
    assert {"SPXL", "TQQQ"} <= pinned_symbols(cfg)


def test_ld8_fires_on_a_live_shaped_day(monkeypatch):
    """LD8 through the live LabStrategy with peers: SPY dips 0.4% by 09:45, then breadth turns up 10+ points and SPY
    ticks up -> one SPXL long inside 09:50-10:30, stop 1R below, no target (holdtr)."""
    from mcf.strategies.lab_context import _CACHE
    from mcf.strategies.setups import _LAB_FRAMES, build_strategies

    (st,) = [s for s in build_strategies(_cfg(monkeypatch)) if s.name.startswith("LD8")]
    idx = pd.date_range("2026-10-12 09:30", periods=390, freq="1min", tz="America/New_York")
    m = np.arange(390)

    def bars(px):
        return pd.DataFrame({"open": px, "high": px + 0.01, "low": px - 0.01, "close": px, "volume": 1000.0}, index=idx)

    spy = np.where(m < 15, 100 - 0.4 * m / 15, np.where(m < 25, 99.6, 99.6 + 0.02 * (m - 25)))   # dip, flat, rally
    peers = {"SPY": bars(spy), "SPXL": bars(3 * spy - 200)}
    for k in range(10):          # stocks: sink below VWAP until ~09:55, then rally above it
        peers[f"S{k:02d}"] = bars(np.where(m < 25, 50 - 0.02 * m, 49.5 + 0.01 * (k + 1) * (m - 25)))
    _LAB_FRAMES.clear()
    _CACHE.clear()
    ctx = SimpleNamespace(symbol="SPXL", date=idx[0].date(), bars=peers["SPXL"], prior5=None, atr=4.0,
                          prev_close=100.0, prev_high=101.0, prev_low=99.0, avg_dollar_volume=4e8, peers=peers)
    assert st.eligible(ctx)
    sig = st.signals(ctx)
    assert len(sig) == 1 and sig[0].side == 1 and sig[0].target is None and sig[0].trail_r == 1.0
    end = idx[sig[0].bar_index] + pd.Timedelta(minutes=1)
    assert 950 <= end.hour * 100 + end.minute <= 1030
    ctx.symbol = "QQQ"
    assert not st.eligible(ctx)                                                    # SPXL only
