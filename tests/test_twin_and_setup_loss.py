"""Owner 2026-10-19 evening: twin-exposure cap (live.block_twin_same_symbol) and per-setup daily loss limit
(account.max_setup_daily_loss_r). Educational only - not financial advice."""

import pandas as pd

from mcf.config import load_config
from mcf.execution.risk import RiskManager, twin_key
from mcf.report.playing_time import classify
from mcf.strategies.base import Signal


def _rm(max_lots=3, setup_limit=None, **live):
    cfg = load_config()
    cfg["live"]["max_lots_per_symbol"] = max_lots
    cfg["live"].update(live)
    if setup_limit is not None:
        cfg["account"]["max_setup_daily_loss_r"] = setup_limit
    else:
        cfg["account"].pop("max_setup_daily_loss_r", None)
    return RiskManager(cfg, 100000)


def _sig(strategy, side=-1, sym="XYZ"):
    return Signal(sym, strategy, side, 10, stop=55.0 if side == -1 else 53.0)


def _hold(rm, sym, *lots):
    rm.state.open_symbols.add(sym)
    rm.state.lots[sym] = list(lots)


def test_twin_key():
    assert twin_key("heat_fade_short-FD") == twin_key("heat_fade_short") == "heat_fade_short"
    assert twin_key("MF3-open-flowsell-rsi5hi-FD") == "MF3-open-flowsell-rsi5hi"


def test_twin_refused_stacked():
    rm = _rm(3)
    _hold(rm, "XYZ", ("MF3-open-flowsell-rsi5hi", -1))
    assert rm.check(_sig("MF3-open-flowsell-rsi5hi-FD"), 54.0) == (False, "twin held")
    rm2 = _rm(3)
    _hold(rm2, "XYZ", ("heat_fade_short-FD", -1))
    assert rm2.check(_sig("heat_fade_short"), 54.0) == (False, "twin held")


def test_twin_refused_one_lot_per_symbol():
    rm = _rm(1)
    _hold(rm, "XYZ", ("heat_fade_short-FD", 0))
    assert rm.check(_sig("heat_fade_short"), 54.0) == (False, "twin held")
    rm.state.lots["XYZ"] = [("NS2-sma50break-overbought-short", 0)]
    assert rm.check(_sig("heat_fade_short"), 54.0) == (False, "already in symbol")


def test_non_twin_allowed_and_other_symbol_allowed():
    rm = _rm(3)
    _hold(rm, "XYZ", ("MF3-open-flowsell-rsi5hi", -1))
    assert rm.check(_sig("MF5-flowsell-vwapup-rsi5hi-FD"), 54.0) == (True, "ok")
    assert rm.check(_sig("MF3-open-flowsell-rsi5hi-FD", sym="ABC"), 54.0) == (True, "ok")
    rm.state.lots["XYZ"].append(("MF3-open-flowsell-rsi5hi-FD", -1))   # same setup re-entry is not a twin
    assert rm.check(_sig("MF3-open-flowsell-rsi5hi-FD"), 54.0) == (False, "twin held")


def test_opposite_side_unaffected():
    rm = _rm(3)
    _hold(rm, "XYZ", ("NS1-rsidip-rsi5pop-long", 1))
    assert rm.check(_sig("MF3-open-flowsell-rsi5hi"), 54.0) == (False, "opposite side held")
    assert rm.check(_sig("NS2-sma50break-overbought-short", side=1), 54.0) == (True, "ok")


def test_twin_flag_off():
    rm = _rm(3, block_twin_same_symbol=False)
    _hold(rm, "XYZ", ("heat_fade_short-FD", -1))
    assert rm.check(_sig("heat_fade_short"), 54.0) == (True, "ok")


def test_setup_loss_two_losses_halt_setup_only():
    rm = _rm(3, setup_limit=2.0)
    rm.state.realized_r_by_strategy = {"A": -1.0}
    assert rm.check(_sig("A"), 54.0)[0]
    rm.state.realized_r_by_strategy["A"] -= 1.0
    assert rm.check(_sig("A"), 54.0) == (False, "setup daily loss limit")
    assert rm.check(_sig("B"), 54.0) == (True, "ok")          # per-setup isolation
    assert not rm.state.halted


def test_setup_loss_win_adds_room():
    rm = _rm(3, setup_limit=2.0)
    rm.state.realized_r_by_strategy = {"A": -1.0 + 1.5 - 1.0 - 1.0}    # loss, win, loss, loss: net -1.5
    assert rm.check(_sig("A"), 54.0) == (True, "ok")


def test_setup_loss_off_when_absent():
    rm = _rm(3)
    rm.state.realized_r_by_strategy = {"A": -9.0}
    assert rm.check(_sig("A"), 54.0) == (True, "ok")


def test_accounts_config(monkeypatch):
    assert "max_setup_daily_loss_r" not in load_config()["account"]
    assert load_config()["account"]["max_daily_loss_r"] == 20
    for acct in ("testing", "testing2", "gen"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        a = load_config()["account"]
        assert a["max_setup_daily_loss_r"] == 2.0 and a["max_daily_loss_r"] == 120


def test_playing_time_buckets():
    assert classify("skipped", "twin held") == "held_by_other"
    assert classify("skipped", "setup daily loss limit") == "daily_loss"


def test_runner_restore_groups_realized_by_setup(tmp_path, monkeypatch):
    from tests.test_no_stacking import _runner
    r, _ = _runner(tmp_path, monkeypatch)
    r.dry_run = True
    today = pd.Timestamp.now(tz="America/New_York").date()
    done = pd.DataFrame({"date": [str(today)] * 3 + ["2000-01-01"], "strategy": ["A", "A", "B", "A"],
                         "r_multiple": [-1.0, -1.0, 0.5, -5.0]})
    monkeypatch.setattr(r.journal, "trades", lambda **k: done)
    r.restore(today)
    assert r.risk.state.realized_r_by_strategy == {"A": -2.0, "B": 0.5}


def test_twin_group_blocks_same_group_only():
    """Owner 2026-10-20: setups with the same `twin_group:` never hold the same symbol in one account."""
    from mcf.execution.risk import twin_groups

    cfg = {"strategies": {"LD3": {"twin_group": "LD-ST2"}, "LD5": {"twin_group": "LD-ST2"},
                          "LD1": {"twin_group": "LD-NS1"}, "plain": {"enabled": True}, "off": {"enabled": False}}}
    g = twin_groups(cfg)
    assert g == {"LD3": "LD-ST2", "LD5": "LD-ST2", "LD1": "LD-NS1"}
    assert twin_key("LD3", g) == twin_key("LD5", g) != twin_key("LD1", g)
    assert twin_key("heat_fade_short-FD", g) == "heat_fade_short"            # no group: the old '-FD' rule
    rm = _rm(3)
    rm.twin_groups = g
    _hold(rm, "XYZ", ("LD3", 1))
    assert rm.check(_sig("LD5", side=1), 54.0) == (False, "twin held")
    assert rm.check(_sig("LD1", side=1), 54.0) == (True, "ok")               # other group
    assert rm.check(_sig("LD5", side=1, sym="ABC"), 54.0) == (True, "ok")    # other symbol
    rm1 = _rm(1)
    rm1.twin_groups = g
    _hold(rm1, "XYZ", ("LD5", 0))
    assert rm1.check(_sig("LD3", side=1), 54.0) == (False, "twin held")


def test_twin_groups_wired_from_testing2_config(monkeypatch):
    from mcf.config import load_config

    monkeypatch.setenv("MCF_ACCOUNT", "testing2")
    rm = RiskManager(load_config(), 100000)
    groups: dict[str, set] = {}
    for k, v in rm.twin_groups.items():
        groups.setdefault(v, set()).add(k)
    assert groups == {
        "LD-ST2": {"LD3-st2-idxturn-t05s1-long", "LD5-st2-breadthup-t05s1-long"},
        "LD-NS1": {"LD1-ns1-breadthup-t05s1-long", "LD7-ns1-idxturn-holdtr-long"},
        "LD-SPXL": {"LD6-spy-dip020atr-breadthturn-spxl-holdtr-long", "LD8-spy-dip030-breadthturn-spxl-holdtr-long"},
        "NS3-T2": {"NS3V1-am-widestop-short", "NS3-failed-vwap-reclaim-short-FD"},   # owner 2026-10-22 (V1)
    }
    _hold(rm, "SPXL", ("LD6-spy-dip020atr-breadthturn-spxl-holdtr-long", 1))
    assert rm.check(Signal("SPXL", "LD8-spy-dip030-breadthturn-spxl-holdtr-long", 1, 10, stop=53.0), 54.0) \
        == (False, "twin held")
    # owner 2026-10-22 (V1): NS3V1 and NS3-FD never hold the same symbol in Testing 2; each may add its own refire lot
    _hold(rm, "XYZ", ("NS3V1-am-widestop-short", -1))
    assert rm.check(Signal("XYZ", "NS3-failed-vwap-reclaim-short-FD", -1, 10, stop=55.0), 54.0) == (False, "twin held")
    assert rm.check(Signal("XYZ", "NS3V1-am-widestop-short", -1, 12, stop=55.0), 54.0)[0]
