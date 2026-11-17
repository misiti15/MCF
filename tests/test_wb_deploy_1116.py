"""Workbench copies deployed after the 2026-11-16 close (owner "Yes to all 15 WB copies"): each copy is in exactly one
testing account (Testing A-F), never beside its parent, parents unchanged, modules load, display names present, and the
ORB20 `min_price` part defaults to the old behaviour. Educational only - not financial advice."""
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from mcf.strategies.base import DayContext
from mcf.strategies.research_setups import ORB20

ROOT = Path(__file__).resolve().parents[1]
TESTING = ["testing2", "explore1", "livelab", "testingd", "testinge", "testingf"]
COPIES = {   # copy -> (account, parent)
    "MF2-open-rsimidhi-flowsell-FD-WB3": ("testing2", "MF2-open-rsimidhi-flowsell-FD"),
    "RW6G1-ns2-up3-vwap2sd-short-FD-WB3": ("testing2", "RW6G1-ns2-up3-vwap2sd-short-FD"),
    "NM-ETF-late-dip-di-long-WB1": ("explore1", "NM-ETF-late-dip-di-long"),
    "L3-gap-slope-rsi5hi-FD-WB4": ("explore1", "L3-gap-slope-rsi5hi-FD"),
    "GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short-WB4":
        ("explore1", "GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short"),
    "RW3-gapdn-rsi5pop-flowsell-short-FD-WB3": ("livelab", "RW3-gapdn-rsi5pop-flowsell-short-FD"),
    "ST7-rsi50dn-long-pm-t1s1-FD-WB1": ("livelab", "ST7-rsi50dn-long-pm-t1s1-FD"),
    "orb20_a-WB3": ("livelab", "orb20_a"),
    "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3": ("testingd", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"),
    "RW1-gapdn-bounce-flowsell-short-FD-WB3": ("testingd", "RW1-gapdn-bounce-flowsell-short-FD"),
    "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long-WB5":
        ("testingd", "GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long"),
    "RW7-gapdn-bounce-early-short-FD-WB3": ("testinge", "RW7-gapdn-bounce-early-short-FD"),
    "NM-RWN5-ns3-mon-weakrs-short-WB3": ("testinge", "NM-RWN5-ns3-mon-weakrs-short"),
    "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short-WB1":
        ("testinge", "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short"),
    "L3-gap-slope-lowdist-FD-WB4": ("testingf", "L3-gap-slope-lowdist-FD"),
    "CWT14-failbrk-pdl-p10-lowvol-long-WB3": ("testingf", "CWT14-failbrk-pdl-p10-lowvol-long"),
    "CWT09-gapdn-vwaploss-g10-short-WB4": ("testingf", "CWT09-gapdn-vwaploss-g10-short"),
}


def _acct(a):
    return yaml.safe_load((ROOT / f"config/account_{a}.yaml").read_text())


def _on(block):
    return isinstance(block, dict) and block.get("enabled")


def test_each_copy_in_one_testing_account_not_beside_parent():
    cfgs = {a: _acct(a) for a in TESTING + ["testing", "graveyard", "gen"]}
    cfgs["primary"] = yaml.safe_load((ROOT / "config/default.yaml").read_text())
    for copy, (acct, parent) in COPIES.items():
        homes = [a for a, c in cfgs.items() if _on((c.get("strategies") or {}).get(copy))]
        assert homes == [acct], (copy, homes)
        assert not _on(cfgs[acct]["strategies"].get(parent)), (copy, "beside its parent")
        assert copy in cfgs[acct]["live"]["setup_order"], copy
        assert "workbench" in cfgs[acct]["strategies"][copy].get("tags", []), copy


def test_copy_modules_exist_and_names_present():
    names = yaml.safe_load((ROOT / "config/setup_names.yaml").read_text())
    for copy, (acct, _) in COPIES.items():
        b = _acct(acct)["strategies"][copy]
        if b.get("module"):
            assert (ROOT / b["module"]).exists(), copy
        assert copy in names and names[copy].get("account") == acct, copy


def test_copies_build_from_config():
    import os

    from mcf.config import load_config
    from mcf.strategies.setups import build_strategies

    for acct in sorted({a for a, _ in COPIES.values()}):
        old = os.environ.get("MCF_ACCOUNT")
        os.environ["MCF_ACCOUNT"] = acct
        try:
            built = {s.name for s in build_strategies(load_config())}
        finally:
            if old is None:
                os.environ.pop("MCF_ACCOUNT", None)
            else:
                os.environ["MCF_ACCOUNT"] = old
        want = {c for c, (a, _) in COPIES.items() if a == acct}
        assert want <= built, (acct, sorted(want - built))


def _ctx(prev_close):
    idx = pd.date_range("2026-11-16 09:30", periods=30, freq="1min", tz="America/New_York")
    bars = pd.DataFrame({"open": prev_close, "high": prev_close, "low": prev_close, "close": prev_close,
                         "volume": 1e5}, index=idx)
    return DayContext("X", date(2026, 11, 16), bars, prev_close, prev_close, prev_close, atr=2.0,
                      avg_dollar_volume=1e9, rank_rvol20=3, avg_cum_volume=np.ones(390))


def test_orb20_min_price_defaults_to_old_floor():
    base = ORB20(top_n=20)
    assert base.eligible(_ctx(10.0)) and not base.eligible(_ctx(4.0))       # unchanged: $5 floor from _liquid
    wb = ORB20(top_n=10, min_price=20.0)
    assert not wb.eligible(_ctx(10.0)) and wb.eligible(_ctx(25.0))
