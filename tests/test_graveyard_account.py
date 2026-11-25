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
            "CWT14-failbrk-pdh-p10-lowvol-short",   # owner 2026-10-22 (N6)
            "CWT13-vwapstretch-z05-short",   # owner 2026-10-22 (D1), effective 2026-10-23
            "CWT09-gapdn-vwaploss-g5-short",   # owner 2026-10-25 (D2), effective 2026-10-26
            "CWT12-coil-k4-long",   # owner 2026-10-28 (K4-2), effective 2026-10-29
            "CWT14-failbrk-pdl-p05-lowvol-long",   # owner 2026-10-30 (D2), effective 2026-10-30
            "NS3-failed-vwap-reclaim-short-FD", "RW4-ns3-adv150-short-FD",   # owner 2026-11-01 (DM-NS3), effective 2026-11-02
            "MF5-flowsell-vwapup-rsi5hi-FD",   # owner 2026-11-02 (DM-MF), effective 2026-11-03
            "NS5-sma50-flush-oversold-long-FD"}   # owner 2026-11-03 (DM-N3), split copy, effective 2026-11-04
MOVED_T1 = {"CWT14-failbrk-pdh-p05-lowvol-short",   # owner 2026-10-22 (N6)
            "CWT14-failbrk-pdh-p10-short",   # owner 2026-10-22 (P0), effective 2026-10-23
            "CWT12-coil-k6-long",   # owner 2026-10-26 (D3), effective 2026-10-27
            "CWT14-failbrk-pdl-p05-long",   # owner 2026-10-30 (D1), effective 2026-10-30
            "MF3-open-flowsell-rsi5hi-FD",   # owner 2026-11-02 (DM-MF), effective 2026-11-03
            "ST4-emadn-long-am-t1s05-FD", "RW6G1-ns2-up3-vwap2sd-short-FD",   # owner 2026-11-03 (DM-N3), effective 2026-11-04
            "RW6-ns2-up3-short-FD", "NS2-sma50break-overbought-short-FD", "heat_fade_long-FD", "ST1-ordn-long-pm-t05s1-FD",
            "MF1-945-flowsell-vwapup-FD", "heat_fade_short-FD", "ST2-slope20up-long-am-t05s1-FD",
            "NS2-sma50break-overbought-short", "heat_fade_short"}
# moved in from the testing arena (owner RW3S-GY drop 2026-11-13, effective 2026-11-16): off in Testing E
MOVED_TE = {"RW3S-gapdn-flowsell-short-FD"}
# moved out of the Graveyard to the testing arena (owner GY-RW6/ST4 arena 2026-11-12, effective 2026-11-13): block kept, disabled
MOVED_OUT = {"RW6-ns2-up3-short-FD": "livelab"}   # ST4-emadn-long-am-t1s05-FD came back 2026-11-25 (GYH V1)
# GY-ARCHIVE-20 (owner yes 2026-11-18, from 2026-11-19): archived residents stay in the file (enabled false + marker)
ARCHIVED = {k for k, v in (yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text())["strategies"] or {}).items()
            if isinstance(v, dict) and v.get("archived")}
# C3-EXIT100 (owner yes 2026-11-18, effective 2026-11-19; ledger 2026-11-19-c3-exit100): setup -> home it left
MOVED_C3 = {
    "GEN-261022-09-Ret15mATRlem0p16-BarRngATRge0p11-ADX7ge64-AM-BRvwlt0p3-hold-short": "gen",
    "CWT14-failbrk-pdl-p10-long": "testing2",
    "GEN-261029-08-Ret15mlem0p36-Flow3lem0p54-RSI14ge65-AM-SPYgt0p5-hold-short": "gen",
    "GEN-261019-05-RSIslopelem9-PDLdistle0p14-EMAdifflem0p46-OPEN-SPYltm0p5-t1s1-long": "testingd",
    "MF4-h40-open-flowsell-FD": "testing",
    "CWT14-failbrk-pdl-p10-lowvol-long": "testingd",
    "GEN-261020-07-RSIslopege19-LowWickge0p33-ATRdge4p4-AM-BRvwgt0p7-hold-long": "testinge",
    "GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long": "gen",
    "CWT13-vwapstretch-z05-long": "testing2",
    "MF2-open-rsimidhi-flowsell-FD": "testing",
    "GEN-261028-09-FlowShiftlem0p65-ADX7le23-AM-BRoplt0p35-t05s1-long": "testinge",
    "GEN-261021-07-VWAPxUp-ORBfailUp-AM-SPYgt0p5-hold-long": "gen",
    "GEN-261028-08-Ret5mge0p21-SMA20dlem0p16-Compress6le0p11-LUNCH-BRoplt0p35-holdtr-long": "explore1",
    "GEN-261027-05-VolRatioge1p5-ORLdistge0p41-ATRdge6-MID-BRvwgt0p7-t05s1-long": "livelab",
    "GEN-261022-01-ORBfailUp-ATRdge7p9-Eff6ge0p55-AM-SPYdn-hold-long": "gen",
    "GEN-261020-05-ORBfailDn-VWAPcrossesge4-SMA20dlem0p31-LUNCH-SPYgt0p25-holdtr-long": "testingf",
    "NS1-rsidip-rsi5pop-long-FD": "testinge",
    "exhaustion_short-FD": "testing2",
    "MF5-flowsell-vwapup-rsi5hi": "testing2",
    "GEN-261028-02-VWAPxDn-NewLOD-AM-QQQgt0p6-t1s1-long": "gen",
}
# FOOTRACE-EXIT (owner FOOTRACE 2026-11-19, applied at the Friday review 2026-11-20, effective 2026-11-23; ledger
# 2026-11-23-friday-review-1120): arena setup -> home it left
MOVED_FR = {
    "GEN-261020-03-MACDhge0p079-BarsSinceLODle5-MID-BRvwlt0p3-t05s05-long": "explore1",
    "CWT14-failbrk-pdl-p05-R2A-long": "testing2",
    "GEN-261029-02-RSI2le0-VWAPcrossesge9-DayRngVsPrevle0p52-MID-BRvwlt0p4-hold-long": "explore1",
    "GEN-261022-06-NewLOD-ORBfailUp-BuyPresslem0p49-PM-SPYltm0p5-t1s1-long": "testingf",
    "intraday_momentum": "testingf",
    "GEN-261027-09-ORBfailDn-Gapge2-Slope6ge0p03-LAM-BRvwlt0p5-t05s05-short": "livelab",
    "GEN-261020-01-MACDhge0p12-RSI5le25-PM-BRvwgt0p6-t1s05-long": "gen",
    "CWT13-vwapstretch-z075-short": "testing2",
    "CWT14-failbrk-pdl-p05-R2A-short": "testing2",
    "GEN-261026-10-ORBfailDn-EMAdChglem0p051-PM-BRopgt0p65-t1s1-long": "livelab",
    "GEN-261019-03-Ret15mATRlem0p12-FromOpenATRlem0p34-SMA20slopege0p29-PM-BRoplt0p5-t05s1-long": "testing2",
    "GEN-261022-08-EMAdChglem0p094-Flow3ge1-RVolDayle0p59-AM-SPYgt0p25-holdtr-short": "testinge",
    # QA-EXIT2 (owner 2026-11-21, FOOTRACE-EXIT on the corrected LR8 cost basis; ledger 2026-11-23-st7-move-qa-exit2)
    "CWT05-flush-m05-v3-long": "testingf",
    "GEN-261027-06-ORBfailUp-BarsSinceLODle5-MID-BRoplt0p35-holdtr-long": "livelab",
}
# GYH V1 (owner 2026-11-25, Graveyard floor, effective 2026-11-27; ledger 2026-11-27-gyh-v1-v3): setup -> home it left
MOVED_GYH = {
    "CWT13-vwapstretch-z075-long": "explore1",
    "GEN-261019-04-EMAdChgge0p15-RSI14le22-MID-BRoplt0p5-t1s1-long": "gen",
    "GEN-261023-04-EMAdChglem0p028-PDHdistle0p074-EMAdifflem0p46-PM-QQQltm0p6-t1s1-long": "explore1",
    "GEN-261026-02-VolRatioge2-SMA20dlem0p58-BarsSinceLODle1-LATE-BRoplt0p35-t1s1-long": "testingd",
    "GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long": "livelab",
    "GEN-261027-03-NewLOD-DayPosle0p19-SMA20dlem0p59-LAM-SPYgt0p5-hold-long": "testingd",
    "GEN-261027-07-RSI14le35-FromOpenge2-AM-BRvwlt0p5-t1s1-short": "testinge",
    "GEN-261029-03-MACDhlem0p12-Ret5mlem0p062-Gapge2-PM-QQQup-hold-long": "explore1",
    "ST4-emadn-long-am-t1s05-FD": "explore1",
}
# RETIRE-R3 (owner 2026-11-20, applied at the Friday review 2026-11-20, effective 2026-11-23): terminal, block kept
# (enabled false + retired marker), out of setup_order
RETIRED = {k for k, v in (yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text())["strategies"] or {}).items()
           if isinstance(v, dict) and v.get("retired")}
# combined live win rate > 50% on 2026-10-20 (owner rule): stayed in Testing 1 (exhaustion_short-FD later left by C3-EXIT100)
STAYED_T1 = {"L3-gap-slope-lowdist-FD"}   # L3-gap-slope-fromopen-FD: promoted to Primary 2026-10-21
# exhaustion_short-FD: single home Testing A from 2026-11-12 (ONDECK dual-home fix) - still a testing account, never the Graveyard


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
    # REPV-11 / REPV-12 (owner 2026-11-11, from session 2026-11-12): smaller lots, more slots, per-setup cap 75 - was
    # half of Testing 2's 400 slots / 50 per setup at x3.8
    assert a["slots"] == a["max_concurrent_positions"] == 300 and a["buying_power_multiple"] == 1.6
    assert a["max_positions_per_strategy"] == 75
    assert a["max_trades_per_day"] < t2["max_trades_per_day"]
    # TSZ1 2026-11-17: Testing A-F moved to 0.125% (ledger 2026-11-16-tsz1-testing-sizing); the Graveyard stays with On Deck
    assert a["risk_per_trade_pct"] == _cfg(monkeypatch, "testing")["account"]["risk_per_trade_pct"] == 0.25
    assert a["max_setup_daily_loss_r"] == 2.0 and a["max_daily_loss_r"] == 120
    assert live["block_twin_same_symbol"] is True
    assert live["scale_out_max_per_day"] == 0
    for k, v in cfg["strategies"].items():
        if k in _on(cfg):
            assert not v.get("live_scale_out") and not v.get("ticker_split"), k   # no live scale-out, no split copies


def test_only_its_own_setups_run(monkeypatch):
    from mcf.strategies.setups import build_strategies

    cfg = _cfg(monkeypatch)
    raw = yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text())["strategies"]
    guests = {k for k, v in raw.items() if v.get("guest")}                   # GY-BENCH guests (11-18..11-24 only)
    own = set(raw) - guests
    rot = cfg["rotation"]
    on = _on(cfg)
    assert own == MOVED_T1 | MOVED_T2 | MOVED_TE | set(MOVED_C3) | set(MOVED_FR) | set(MOVED_GYH)
    assert on == (own - set(MOVED_OUT) - ARCHIVED - RETIRED - set(rot["benched"])) | set(rot["guests"])
    assert len(RETIRED) == 11 and not (RETIRED & ARCHIVED)
    assert len(ARCHIVED) == 36   # GY-ARCHIVE-20 18 (2026-11-19) + GYH V3 18 (2026-11-27)
    st = build_strategies(cfg)
    assert {s.name for s in st} == on
    assert sorted(cfg["live"]["setup_order"]) == sorted((own - set(MOVED_OUT) - RETIRED) | guests)   # every setup has a priority (retired: none)


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
    assert STAYED_T1 <= t1 | t2
    for acct, on in (("testing", t1), ("testing2", t2)):
        order = _cfg(monkeypatch, acct)["live"]["setup_order"]
        assert not ((MOVED_T1 | MOVED_T2) & set(order)), acct
    te = _cfg(monkeypatch, "testinge")                                        # RW3S-GY: off in Testing E
    assert not (MOVED_TE & _on(te)) and not (MOVED_TE & set(te["live"]["setup_order"]))
    for k, acct in MOVED_C3.items():    # C3-EXIT100: off at home, out of its order, on in the Graveyard
        c = _cfg(monkeypatch, acct)
        assert k not in _on(c) and k not in c["live"]["setup_order"], k
    for k, acct in MOVED_FR.items():    # FOOTRACE-EXIT: off at home, out of its order, on in the Graveyard
        c = _cfg(monkeypatch, acct)
        assert k not in _on(c) and k not in c["live"]["setup_order"], k
    for k, acct in MOVED_GYH.items():   # GYH V1: off at home, out of its order, on in the Graveyard
        c = _cfg(monkeypatch, acct)
        assert k not in _on(c) and k not in c["live"]["setup_order"], k
    gy_on = _on(_cfg(monkeypatch))
    assert set(MOVED_GYH) <= gy_on and not (ARCHIVED & gy_on)
    assert set(MOVED_FR) - ARCHIVED <= gy_on and not (RETIRED & gy_on)
    for acct in ("testing", "testing2", "explore1", "livelab", "testingd", "testinge", "testingf", "gen"):
        assert not (RETIRED & _on(_cfg(monkeypatch, acct))), acct                # retired: out of every account
    assert "exhaustion_short" not in _on(_cfg(monkeypatch, "testingf"))       # RETIRE-R3 (its only home)
    for k, acct in MOVED_OUT.items():   # one home: on in the arena account, off in the Graveyard
        assert k in _on(_cfg(monkeypatch, acct)) and k in _cfg(monkeypatch, acct)["live"]["setup_order"], k
    grave = yaml.safe_load((ROOT / "config/account_graveyard.yaml").read_text())["strategies"]
    for k in ("heat_fade_long", "heat_fade_short", "NS2-sma50break-overbought-short"):
        assert grave[k]["former_primary"]                                     # markers kept
    assert "# moved to Graveyard 2026-10-21 (owner)" in (ROOT / "config/account_graveyard.yaml").read_text()


def test_workflows_route_graveyard_to_its_own_account():
    tr = (ROOT / ".github/workflows/trade.yml").read_text()
    eod = (ROOT / ".github/workflows/eod.yml").read_text()
    wd = (ROOT / ".github/workflows/watchdog.yml").read_text()
    for wf in (tr, eod, wd):
        assert "account: [primary, testing, testing2, gen, graveyard" in wf          # the matrix may grow (livelab, explore1, explore2, 2026-11-03)
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
    assert 'graveyard: ["Graveyard", "mcf-data-graveyard"], livelab:' in html   # leaderboard (+ 3 accounts 2026-11-03)
    assert A.ACCOUNTS.get("graveyard") == "Graveyard"
    d = json.loads(A.OUT.read_text())
    st = A._strategies(d.get("asof_session"))["graveyard"]                   # GY-BENCH: resolved for the file's session
    bench = set(A.resting({"graveyard": st}, d.get("asof_session")))
    guests = {k for k, v in st.items() if isinstance(v, dict) and v.get("guest") and v.get("enabled")}
    assert d["labels"]["graveyard"] == "Graveyard" and set(d["accounts"]["graveyard"]) == \
        ((MOVED_T1 | MOVED_T2 | MOVED_TE | set(MOVED_C3) | set(MOVED_FR) | set(MOVED_GYH)) - set(MOVED_OUT) - ARCHIVED - RETIRED - bench) | guests
