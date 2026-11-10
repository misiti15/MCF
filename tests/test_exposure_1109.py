"""Owner 2026-11-09 exposure window (research/exposure_lab/NOTES.md): the setups in Primary's PV1 / PV2 / PV0 decision
(research/preval_1107/NOTES.md) plus the top 20 by total R over the last 15 sessions (10-19..11-06, all 7 accounts) get
the most exposure possible in the 11-09 and 11-10 sessions, then PV is reconfirmed after the 11-10 close.

Pin: until the 11-10 session is over, each of these setups stays enabled in its current home and in that account's
setup_order, and is not switched on anywhere else (no moves, no copies). After 2026-11-10 the pin lapses (test skips).
Educational only - not financial advice."""
import datetime as dt

import pytest

END = dt.date(2026, 11, 10)       # last session of the window
HOME = {
    # PV decision setups
    "RW3-gapdn-rsi5pop-flowsell-short-FD": "primary", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "primary",
    "L3-gap-slope-fromopen-FD": "primary", "ST7-rsi50dn-long-pm-t1s1-FD": "primary",
    "NS5-sma50-flush-oversold-long": "primary", "MF2-open-rsimidhi-flowsell-FD": "primary",
    "MF4-h40-open-flowsell-FD": "primary", "MF4-h40-open-flowsell": "primary", "NS1-rsidip-rsi5pop-long": "primary",
    "L3-gap-slope-rsi5hi-FD": "primary", "NM-ETF-late-dip-di-long": "livelab",
    # top 20 by total R, 15 sessions (those not already above)
    "RW7-gapdn-bounce-early-short-FD": "testing", "L3-gap-slope-lowdist-FD": "testing",
    "RW1-gapdn-bounce-flowsell-short-FD": "testing2", "NM-MF3-qqqdn-gapdn-FD": "testing2",
    "CWT09-gapdn-bounce-g5-lowerhalf-short": "graveyard", "CWT09-gapdn-vwaploss-g5-short": "graveyard",
    "CWT09-gapdn-vwaploss-g10-short": "livelab",
    "GEN-261020-10-BBpctge0p81-ORBfailDn-AM-BRvwlt0p3-hold-short": "gen",
    "GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long": "gen",
    "GEN-261028-06-RSI5le13-VWAPatrlem0p15-DayRngVsPrevle0p34-MID-BRoplt0p35-hold-short": "gen",
    "GEN-261022-07-Z12lem1p9-FlowShiftlem0p96-ATRdge3p6-AM-BRopgt0p5-t1s1-short": "gen",
    "GEN-261026-02-VolRatioge2-SMA20dlem0p58-BarsSinceLODle1-LATE-BRoplt0p35-t1s1-long": "gen",
    "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short": "gen",
    "GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short": "gen",
    "GEN-261019-03-Ret15mATRlem0p12-FromOpenATRlem0p34-SMA20slopege0p29-PM-BRoplt0p5-t05s1-long": "gen",
}
ACCOUNTS = ("primary", "testing", "testing2", "graveyard", "gen", "explore1", "livelab")


def _cfg(monkeypatch, acct):
    from mcf.config import load_config

    if acct == "primary":
        monkeypatch.delenv("MCF_ACCOUNT", raising=False)
    else:
        monkeypatch.setenv("MCF_ACCOUNT", acct)
    return load_config()


def _on(cfg):
    return {k for k, v in cfg["strategies"].items() if isinstance(v, dict) and v.get("enabled")}


def test_set_size():
    assert len(HOME) == 26 and sum(s.startswith("GEN-") for s in HOME) == 8


@pytest.mark.skipif(dt.date.today() > END, reason="exposure window 11-09..11-10 is over")
def test_exposure_set_enabled_in_home_only(monkeypatch):
    for acct in ACCOUNTS:
        cfg = _cfg(monkeypatch, acct)
        on = _on(cfg)
        order = set((cfg.get("live") or {}).get("setup_order") or [])
        for s, home in HOME.items():
            if home == acct:
                assert s in on, f"{s} must stay enabled in {acct} through {END}"
                if order:
                    assert s in order, f"{s} missing from {acct} setup_order"
            else:
                assert s not in on, f"{s} must not run outside {home} (promotion = move; no moves before {END})"
