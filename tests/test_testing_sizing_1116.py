"""TSZ1 (owner 2026-11-16, effective 2026-11-17): testing-account sizing change — Testing A-F only, R comparable, $ not.
On Deck (testing), Primary (default) and Graveyard (and Gen) sizing must be unchanged. Educational only - not financial advice."""
from pathlib import Path

import yaml

from mcf.backtest.engine import lot_shares, slot_notional

ROOT = Path(__file__).resolve().parents[1]
TESTING = {"testing2": (800, 0.95), "explore1": (400, 1.0), "livelab": (400, 1.0), "testingd": (400, 1.0),
           "testinge": (400, 1.0), "testingf": (400, 1.0)}
KEYS = ("starting_equity", "slots", "buying_power_multiple", "risk_per_trade_pct", "max_position_notional_pct",
        "max_concurrent_positions", "max_positions_per_strategy", "max_daily_loss_r", "max_setup_daily_loss_r",
        "max_trades_per_day", "min_shares", "min_shares_notional_pct")
# account blocks as they stood before TSZ1 (only keys set in each file; absent = inherited / None)
UNCHANGED = {
    "default": {"starting_equity": 100000, "slots": 77, "buying_power_multiple": 3.2, "risk_per_trade_pct": 0.25,
                "max_position_notional_pct": 10, "max_concurrent_positions": 77, "max_positions_per_strategy": 30,
                "max_daily_loss_r": 20, "max_setup_daily_loss_r": 2.0, "max_trades_per_day": 1000},
    "account_testing": {"slots": 400, "buying_power_multiple": 3.8, "max_concurrent_positions": 400,
                        "max_positions_per_strategy": 150, "max_daily_loss_r": 300, "max_setup_daily_loss_r": None,
                        "max_trades_per_day": 3000},
    "account_graveyard": {"starting_equity": 100000, "slots": 300, "buying_power_multiple": 1.6,
                          "max_concurrent_positions": 300, "max_positions_per_strategy": 75, "max_daily_loss_r": 120,
                          "max_setup_daily_loss_r": 2.0, "max_trades_per_day": 1500},
}


def _acct(name):
    return yaml.safe_load((ROOT / f"config/{name}.yaml").read_text()).get("account") or {}


def test_on_deck_primary_graveyard_unchanged():
    for name, want in UNCHANGED.items():
        a = _acct(name)
        for k in KEYS:
            assert a.get(k) == want.get(k), (name, k)


def test_testing_accounts_resized():
    for acct, (slots, pct) in TESTING.items():
        a = _acct(f"account_{acct}")
        assert a["slots"] == a["max_concurrent_positions"] == slots, acct
        assert a["risk_per_trade_pct"] == 0.125 and a["max_positions_per_strategy"] == 100, acct
        assert a["min_shares"] == 3 and a["min_shares_notional_pct"] == pct, acct
        assert a["max_daily_loss_r"] == 300, acct                                      # catastrophe halt kept
        live = yaml.safe_load((ROOT / f"config/account_{acct}.yaml").read_text())["live"]
        assert live["max_stop_cost_r"] == 0.15, acct                                   # cost filter kept
        full = {"starting_equity": 100000, "max_position_notional_pct": 10, **a}
        old_slot = 100000 * a["buying_power_multiple"] / (slots // 2)
        assert abs(slot_notional(full) - old_slot / 2) < 1                             # half the $ per lot
        assert abs(100000 * pct / 100 - old_slot) < 1                                 # floor ceiling = old slot


def test_lot_shares_floor():
    a = {"min_shares": 3, "min_shares_notional_pct": 1.0}
    assert lot_shares({}, 1e5, 125, 1.0, 50.0, 500) == 10                              # no floor key: unchanged rule
    assert lot_shares(a, 1e5, 125, 1.0, 50.0, 500) == 10                               # above the floor: untouched
    assert lot_shares(a, 1e5, 125, 5.0, 300.0, 500) == 3                               # 1 share -> 3 ($900 <= $1,000)
    assert lot_shares(a, 1e5, 125, 5.0, 600.0, 500) == 1                               # 0 -> 1 (only 1 fits $1,000)
    assert lot_shares(a, 1e5, 125, 5.0, 1200.0, 500) == 0                              # over the old slot: still skipped
    assert lot_shares(a, 1e5, 8, 5.0, 300.0, 500) == 1                                 # risk budget caps the floor
