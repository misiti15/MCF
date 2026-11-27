"""Friday 11-27 safety switches (mcf/execution/safety.py, config `risk:`): LATCH-OPEN, HS-SCALE, SHOCK-V, B8 shadow.
Every switch defaults OFF in every account; none ever flattens. Educational only - not financial advice."""
import glob
import json
import os

import pandas as pd
import pytest

from mcf.config import load_config
from mcf.execution import safety as S
from mcf.execution.risk import RiskManager
from mcf.strategies.base import Signal
from tests.test_live_ready_lr import CTX, NY, _runner

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCTS = ["primary"] + sorted(os.path.basename(p)[len("account_"):-len(".yaml")]
                             for p in glob.glob(os.path.join(ROOT, "config", "account_*.yaml")))


def at(s):
    return pd.Timestamp(s, tz=NY)


def _sig(sym="AAA", setup="S1", side=1):
    return Signal(sym, setup, side, 4, stop=49.0 if side == 1 else 51.0, target=52.0 if side == 1 else 48.0)


def _rm(risk=None, account="primary", **acct):
    cfg = load_config()
    cfg["account_name"] = account
    cfg["account"].update(acct)
    if risk is not None:
        cfg["risk"] = {**cfg["risk"], **risk}
    return RiskManager(cfg, 100000)


# ------------------------------------------------------------------------------------------------ defaults: all OFF
@pytest.mark.parametrize("acct", ACCTS)
def test_every_switch_defaults_off_in_every_account(acct, monkeypatch):
    monkeypatch.setenv("MCF_ACCOUNT", acct)
    cfg = load_config()
    rk = cfg["risk"]
    assert rk["latch_counts_open"] is False
    for k in ("scaled_halt", "shock_v", "netbeta_shadow"):
        assert rk[k]["enabled"] is False, k
    rm = RiskManager(cfg, 100000)
    assert not rm.latch_counts_open and not rm.scaled.enabled
    assert not S.ShockV(rk["shock_v"], acct).enabled and not S.NetBetaShadow(rk["netbeta_shadow"], acct).enabled


def test_default_off_runner_noop(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
    assert not r.shock.enabled and not r.netbeta.enabled
    r.today = at("2026-11-27 10:00").date()
    r._enter(_sig(), 50.0, ("AAA", "S1"), CTX, at("2026-11-27 10:00"))
    assert len(b.submitted) == 1
    sig = r.journal.signals(r.run_id, str(r.today))
    assert "netbeta_shadow" not in str(sig["info"].iloc[-1])
    r.write_status(at("2026-11-27 10:01"), "trading")
    sf = r.health["risk_state"]["safety"]
    assert not any(sf[k]["enabled"] for k in ("latch_counts_open", "scaled_halt", "shock_v", "netbeta_shadow"))


# ------------------------------------------------------------------------------------------------ LATCH-OPEN
def test_latch_open_blocks_on_closed_plus_open():
    rm = _rm({"latch_counts_open": True})
    rm.state.realized_r_by_strategy = {"S1": -1.0}
    rm.state.open_r_by_strategy = {"S1": -1.2, "S2": -0.5}
    assert rm.check(_sig(setup="S1"), 50.0) == (False, "setup daily loss limit (open)")
    assert rm.check(_sig("BBB", setup="S2"), 50.0) == (True, "ok")
    rm.state.open_r_by_strategy = {"S1": +5.0}           # latched: a recovery does not undo it
    assert rm.check(_sig("CCC", setup="S1"), 50.0)[1] == "setup daily loss limit (open)"


def test_latch_open_off_counts_closed_only():
    rm = _rm({"latch_counts_open": False})
    rm.state.realized_r_by_strategy, rm.state.open_r_by_strategy = {"S1": -1.0}, {"S1": -5.0}
    assert rm.check(_sig(), 50.0) == (True, "ok")


def test_latch_open_minus_3r_and_other_accounts():
    rm = _rm({"latch_counts_open": True, "latch_open_r": 3})
    rm.state.realized_r_by_strategy, rm.state.open_r_by_strategy = {"S1": -1.0}, {"S1": -1.5}
    assert rm.check(_sig(), 50.0) == (True, "ok")         # -2.5 > -3
    rm.state.open_r_by_strategy = {"S1": -2.0}
    assert rm.check(_sig(), 50.0)[1] == "setup daily loss limit (open)"
    other = _rm({"latch_counts_open": True}, account="testing")   # accounts list = [primary]
    assert not other.latch_counts_open


def test_latch_open_missing_mark_falls_back_to_closed(capsys):
    rm = _rm({"latch_counts_open": True})
    rm.state.realized_r_by_strategy, rm.state.open_r_by_strategy = {"S1": -1.0}, {"S1": -3.0}
    rm.state.unmarked_setups = {"S1"}
    assert rm.check(_sig(), 50.0) == (True, "ok")
    assert "closed R only" in capsys.readouterr().out
    rm.state.unmarked_setups, rm.state.open_marks_ok = set(), False
    assert rm.check(_sig("BBB"), 50.0) == (True, "ok")
    rm.state.realized_r_by_strategy = {"S1": -2.0}       # the closed latch still fires
    assert rm.check(_sig("CCC"), 50.0)[1] == "setup daily loss limit"


def test_latch_open_respects_null_setup_limit():
    rm = _rm({"latch_counts_open": True, "latch_open_r": 3}, max_setup_daily_loss_r=None)
    rm.state.open_r_by_strategy = {"S1": -9.0}
    assert rm.check(_sig(), 50.0) == (True, "ok")


def test_open_marks_per_setup_and_unmarked(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch)
    r.lots = {"AAA": {"c1": {"strategy": "S1", "side": 1, "qty": 10, "order_id": "o1"}},
              "BBB": {"c2": {"strategy": "S2", "side": -1, "qty": 10, "order_id": "o2"}},
              "CCC": {"c3": {"strategy": "S3", "side": 1, "qty": 10, "order_id": "o3"}}}
    r._mtm_lot = {"c1": (50.0, 49.0), "c2": (50.0, 51.0), "c3": (20.0, 19.0)}
    bars = {s: pd.DataFrame({"close": [px]}) for s, px in (("AAA", 49.0), ("BBB", 49.0))}   # CCC: no bar
    tot = r._open_marks(bars)
    by = r.risk.state.open_r_by_strategy
    assert by["S1"] == pytest.approx(-1.01, abs=1e-6) and by["S2"] == pytest.approx(0.99, abs=1e-6)
    assert tot == pytest.approx(sum(by.values())) and r.risk.state.unmarked_setups == {"S3"}
    assert r.risk.state.open_marks_ok is True


# ------------------------------------------------------------------------------------------------ HS-SCALE
def test_scaled_level_formula():
    h = S.ScaledHalt({"enabled": True, "k": 4, "floor_per_setup": 2.5, "cap_per_setup": 8, "sigma_r": 5}, "primary")
    h.n = 4
    assert h.level() == (20.0, "k x sigma clipped")
    h.sigma = 1.0
    assert h.level()[0] == 10.0                           # floor 2.5 x 4
    h.sigma = 10.4
    assert h.level()[0] == 32.0                           # cap 8 x 4
    h.sigma = None
    assert h.level() == (32.0, "sigma missing: cap x N")
    h.n = 0
    assert h.level()[0] is None


def test_scaled_halt_blocks_entries_and_fixed_20_stays():
    rm = _rm({"scaled_halt": {"enabled": True, "sigma_r": 3.0}})   # X = clip(12, 10, 32) = 12 with N = 4
    rm.scaled.n = 4
    rm.state.realized_r, rm.state.open_r = -5.0, -6.0
    assert rm.check(_sig(), 50.0) == (True, "ok")
    rm.state.open_r = -7.0
    assert rm.check(_sig(), 50.0) == (False, "scaled loss limit")
    assert rm.check(_sig("BBB"), 50.0) == (False, "scaled loss limit")   # sticky
    big = _rm({"scaled_halt": {"enabled": True, "sigma_r": 50.0}})       # X = 32: the fixed -20R fires first
    big.scaled.n = 4
    big.state.realized_r = -20.0
    assert big.check(_sig(), 50.0) == (False, "daily loss limit")


def test_scaled_halt_failed_marks_use_closed_only():
    rm = _rm({"scaled_halt": {"enabled": True, "sigma_r": 3.0}})
    rm.scaled.n = 4
    rm.state.realized_r, rm.state.open_r, rm.state.open_marks_ok = -5.0, -30.0, False
    assert rm.check(_sig(), 50.0) == (True, "ok")


# ------------------------------------------------------------------------------------------------ SHOCK-V
def test_shock_v_confirms_on_two_polls_and_fires_once():
    v = S.ShockV({"enabled": True}, "primary")
    t0 = at("2026-11-27 11:00")
    assert v.update(t0, 0.0) is None
    assert v.update(t0 + pd.Timedelta(minutes=1), -9.0) is None          # V1 hit, 1st poll
    rec = v.update(t0 + pd.Timedelta(minutes=2), -9.5)                   # 2nd consecutive poll: fires
    assert rec and rec["rule"] == "V1"
    assert v.update(t0 + pd.Timedelta(minutes=3), -30.0) is None          # once only


def test_shock_v_slow_fall_and_skipped_samples():
    v = S.ShockV({"enabled": True}, "primary")
    t0 = at("2026-11-27 11:00")
    for i in range(10):                                                  # -1R a minute: V1 never, V2 after 12R
        assert v.update(t0 + pd.Timedelta(minutes=i), -float(i)) is None
    assert v.update(t0 + pd.Timedelta(minutes=10), None) is None and v.skipped == 1
    assert v.update(t0 + pd.Timedelta(minutes=11), -12.0) is None        # fall 11 in 10 min < 12
    v2 = S.ShockV({"enabled": True}, "primary")
    assert v2.thresholds(32.0) == (16.0, 24.0) and v2.thresholds(None) == (8.0, 12.0)


def test_shock_v_runner_halts_and_alerts_never_flattens(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
    r.shock = S.ShockV({"enabled": True}, "primary")
    flat = []
    monkeypatch.setattr(r, "flatten_mcf", lambda *a, **k: flat.append(1))
    t0 = at("2026-11-27 11:00")
    r.today = t0.date()
    for i, v in enumerate([0.0, -10.0, -11.0]):
        r.risk.state.open_r = v
        r._shock_poll(t0 + pd.Timedelta(minutes=i), stale=False)
    assert r.risk.state.halted and not flat and b.closes == []
    assert any(a["kind"] == "shock-v" for a in r.health["alerts"])
    r._enter(_sig(), 50.0, ("AAA", "S1"), CTX, t0 + pd.Timedelta(minutes=3))
    assert b.submitted == []
    assert r.journal.signals(r.run_id, str(r.today))["reason"].iloc[-1] == "shock-v failsafe"


def test_shock_v_stale_poll_is_skipped(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch)
    r.shock = S.ShockV({"enabled": True}, "primary")
    r.risk.state.open_r = -50.0
    r._shock_poll(at("2026-11-27 11:00"), stale=True)
    assert r.shock.skipped == 1 and not r.risk.state.halted


def test_restart_restores_new_halt_reasons(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch)
    sig = pd.DataFrame({"status": ["skipped"], "reason": ["shock-v failsafe"], "strategy": ["S1"], "symbol": ["AAA"]})
    r._restore_latches(sig)
    assert r.risk.state.halted


# ------------------------------------------------------------------------------------------------ B8 shadow
def test_shrunk_beta():
    import numpy as np
    rng = np.random.default_rng(0)
    spy = pd.Series(100 * np.cumprod(1 + rng.normal(0, 0.01, 80)))
    stock = pd.Series(50 * np.cumprod(1 + 2 * spy.pct_change().fillna(0)))
    assert S.shrunk_beta(stock, spy) == pytest.approx(0.67 * 2 + 0.33, abs=1e-6)
    assert S.shrunk_beta(stock.tail(10), spy.tail(10)) == 1.0             # < 20 obs


def test_netbeta_shadow_tags_but_never_blocks(tmp_path, monkeypatch):
    p = tmp_path / "betas.json"
    p.write_text(json.dumps({"AAA": 2.0, "BAD": "x"}))
    r, b = _runner(tmp_path, monkeypatch)
    r.netbeta = S.NetBetaShadow({"enabled": True, "budget_r_per_pct": 8, "betas_path": str(p)}, "primary")
    # 5 short lots: entry 50, risk 1/share, beta 1 -> each -0.5 R per +1% SPY; AAA beta 2 -> -1.0. NB = -3.0
    r.lots = {f"S{i}X": {f"c{i}": {"strategy": "S1", "side": -1, "qty": 10, "order_id": f"o{i}"}} for i in range(4)}
    r.lots["AAA"] = {"ca": {"strategy": "S1", "side": -1, "qty": 10, "order_id": "oa"}}
    r._mtm_lot = {**{f"c{i}": (50.0, 51.0) for i in range(4)}, "ca": (50.0, 51.0)}
    r.risk.state.open_symbols = set(r.lots)
    assert r.netbeta.net(r._netbeta_lots())[0] == pytest.approx(-3.0)
    r.netbeta.budget = 2.0
    r.today = at("2026-11-27 11:00").date()
    r._enter(_sig("ZZZ", "S2", side=-1), 50.0, ("ZZZ", "S2"), CTX, at("2026-11-27 11:00"))
    assert len(b.submitted) == 1                                         # not blocked
    assert r.netbeta.would_block == 1 and "netbeta_shadow" in r.journal.signals(r.run_id, str(r.today))["info"].iloc[-1]
    r._enter(_sig("YYY", "S2", side=1), 50.0, ("YYY", "S2"), CTX, at("2026-11-27 11:01"))   # long: same-direction? no
    assert len(b.submitted) == 2 and r.netbeta.would_block == 1


def test_netbeta_missing_file_and_unpriced_lots():
    nb = S.NetBetaShadow({"enabled": True, "betas_path": "/nonexistent.json"}, "primary")
    assert "unreadable" in nb.source and nb.beta("X") == 1.0
    assert nb.net([("A", 1, None, 49.0, 1.0), ("B", 1, 50.0, 50.0, 1.0), ("C", 1, 50.0, 49.0, 1.0)]) == (0.5, 2)



# ------------------------------------------------------------------------------------------------ review fixes
def test_latch_open_reason_is_distinct_and_restored(tmp_path, monkeypatch):
    rm = _rm({"latch_counts_open": True})
    rm.state.realized_r_by_strategy = {"S1": -2.5, "S2": -1.0}
    rm.state.open_r_by_strategy = {"S2": -1.5}
    assert rm.check(_sig(setup="S1"), 50.0)[1] == "setup daily loss limit"         # closed latch: old reason
    assert rm.check(_sig("B", setup="S2"), 50.0)[1] == "setup daily loss limit (open)"
    r, _ = _runner(tmp_path, monkeypatch)
    sig = pd.DataFrame({"status": ["skipped"], "reason": ["setup daily loss limit (open)"], "strategy": ["S2"],
                        "symbol": ["AAA"]})
    r._restore_latches(sig)
    assert r.risk.state.setup_stopped == {"S2"}
    from mcf.report.playing_time import classify
    assert classify("skipped", "setup daily loss limit (open)") == "daily_loss"


def test_reporting_knows_new_reasons():
    from mcf.execution.shadow import RESOURCE_REASONS
    from mcf.report.daily_post import INTENDED
    from mcf.research.shadow_calib import RESOURCE
    for why in ("scaled loss limit", "shock-v failsafe"):
        assert why in RESOURCE_REASONS and why in RESOURCE and any(k in why for k in INTENDED)
    assert any(k in "setup daily loss limit (open)" for k in INTENDED)
    from mcf.report.playing_time import classify
    assert classify("skipped", "scaled loss limit") == classify("skipped", "shock-v failsafe") == "daily_loss"


@pytest.mark.parametrize("acct", [a for a in ACCTS if a != "primary"])
def test_switches_refused_outside_cost_r_accounts(acct, monkeypatch, capsys):
    """Realized R is raw outside account.loss_stops_cost_r_accounts while open marks are R after costs: the switches that
    add the two stay off there (warning), even when switched on and listed for the account."""
    monkeypatch.setenv("MCF_ACCOUNT", acct)
    cfg = load_config()
    if acct in (cfg["account"].get("loss_stops_cost_r_accounts") or []):
        pytest.skip("cost-R account")
    cfg["risk"] = {**cfg["risk"], "latch_counts_open": True, "latch_counts_open_accounts": [acct],
                   "scaled_halt": {**cfg["risk"]["scaled_halt"], "enabled": True, "accounts": [acct]}}
    rm = RiskManager(cfg, 100000)
    assert not rm.latch_counts_open and not rm.scaled.enabled
    assert set(rm.safety_refused) == {"latch_counts_open", "scaled_halt"} and "WARNING" in capsys.readouterr().out


def test_cost_basis_primary_accepted():
    rm = _rm({"latch_counts_open": True, "scaled_halt": {"enabled": True}})
    assert rm.latch_counts_open and rm.scaled.enabled and not rm.safety_refused


def _shock_runner(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch)
    r.shock = S.ShockV({"enabled": True}, "primary")
    r.lots = {"AAA": {"c1": {"strategy": "S1", "side": 1, "qty": 10, "order_id": "o1"}}}
    return r


def test_shock_v_no_bar_poll_is_not_double_counted(tmp_path, monkeypatch):
    """Reviewer case: a lot without a bar for one poll keeps its last mark and is not carried, so its return does not
    double-count it."""
    r = _shock_runner(tmp_path, monkeypatch)
    st, t0 = r.risk.state, at("2026-11-27 11:00")
    seq = [({"c1": -10.0}, -10.0), ({}, 0.0), ({"c1": -10.0}, -10.0), ({"c1": -10.0}, -10.0)]
    for i, (marks, open_r) in enumerate(seq):
        r._lot_marks, st.open_r = marks, open_r
        r._shock_poll(t0 + pd.Timedelta(minutes=i), stale=False)
        assert r.shock.last["r"] == -10.0
    assert r.shock.fired is None and not st.halted and not r._shock_carry


def test_shock_v_carry_kept_until_exit_paired(tmp_path, monkeypatch):
    """A lot gone flat before reconcile stays carried across a reconcile that has not paired its exit (journal order
    still open), and leaves the carry once it is paired (order closed, R in closed R)."""
    r = _shock_runner(tmp_path, monkeypatch)
    st, t0 = r.risk.state, at("2026-11-27 11:00")
    open_ids = {"o1"}
    monkeypatch.setattr(r.journal, "open_orders",
                        lambda run_id: pd.DataFrame({"broker_order_id": sorted(open_ids)}))
    r._lot_marks, st.open_r = {"c1": +6.0}, 6.0
    r._shock_poll(t0, stale=False)
    r.lots, r._lot_marks, st.open_r = {}, {}, 0.0         # flat at the broker; exit not booked yet
    r._shock_poll(t0 + pd.Timedelta(minutes=1), stale=False)
    r._shock_after_reconcile()                           # reconcile ran but did not pair it: carry kept
    r._shock_poll(t0 + pd.Timedelta(minutes=2), stale=False)
    assert r.shock.last["r"] == 6.0 and "c1" in r._shock_carry
    open_ids.clear()
    st.realized_r = 6.0                                  # paired: booked in closed R
    r._shock_after_reconcile()
    r._shock_poll(t0 + pd.Timedelta(minutes=3), stale=False)
    assert r.shock.last["r"] == 6.0 and not r._shock_carry and r.shock.fired is None


def test_shock_v_released_in_reconcile_not_carried(tmp_path, monkeypatch):
    """A lot released by reconcile itself (paired in the same call) must not be carried on top of its closed R."""
    r = _shock_runner(tmp_path, monkeypatch)
    st, t0 = r.risk.state, at("2026-11-27 11:00")
    monkeypatch.setattr(r.journal, "open_orders", lambda run_id: pd.DataFrame({"broker_order_id": []}))
    r._lot_marks, st.open_r = {"c1": -10.0}, -10.0
    r._shock_poll(t0, stale=False)
    r.lots, st.realized_r = {}, -10.0                   # reconcile paired + released it
    r._shock_after_reconcile()
    r._lot_marks, st.open_r = {}, 0.0
    for i in (1, 2):
        r._shock_poll(t0 + pd.Timedelta(minutes=i), stale=False)
    assert r.shock.last["r"] == -10.0 and r.shock.fired is None


# ------------------------------------------------------------------------------------------------ flags-off golden run
# Full runner.step polls (4 symbols, 3 setups, prices falling until the Primary -20R halt fires on open marks). The golden
# file was produced by this same scenario on the PRE-CHANGE code (commit cde9a46c53): with every switch off the
# decisions, orders and status risk_state must be identical, and none of the new hooks may run.
from types import SimpleNamespace  # noqa: E402

from mcf.execution import runner as R  # noqa: E402

GOLDEN = os.path.join(ROOT, "tests", "data", "friday_switches_noop_golden.json")



class _GBroker:
    def __init__(self):
        self.submitted, self.held = [], {}

    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):
        return dict(self.held)

    def submit_bracket(self, sig, qty, coid):
        self.submitted.append(coid)
        self.held[sig.symbol] = SimpleNamespace(avg_entry_price=10.0)
        return SimpleNamespace(id=f"o{len(self.submitted)}")


class _GStrat:
    def __init__(self, name, side):
        self.name, self.side, self.params = name, side, {}

    def eligible(self, ctx):
        return True

    def signals(self, ctx):
        last = len(ctx.bars) - 1
        px = float(ctx.bars["close"].iloc[-1])
        return [Signal(ctx.symbol, self.name, self.side, last, stop=px - 0.2 * self.side)]


SYMS = ("AAA", "BBB", "CCC", "DDD")


def _bars(n, sym):
    idx = pd.date_range("2026-11-27 10:00", periods=n, freq="1min", tz=NY)
    k = SYMS.index(sym)
    close = [20.0 + k - 0.15 * i for i in range(n)]
    return pd.DataFrame({"open": close, "high": [c + 0.05 for c in close], "low": [c - 0.05 for c in close],
                         "close": close, "volume": 1e6}, index=idx)


def _golden_run(tmp_path, monkeypatch, mutate=None, polls=12):
    cfg = load_config()
    cfg["account_name"] = "primary"
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["account"].update(max_daily_loss_r=20, max_setup_daily_loss_r=2.0, max_concurrent_positions=77, max_positions_per_strategy=30, max_trades_per_day=1000, risk_per_trade_pct=0.25, loss_stops_cost_r_accounts=["primary"])
    cfg["live"].update(max_lots_per_symbol=3, same_setup_reentry=True, burst_max_entries=30, retry_after_release=False, longs_first_on_ties=False, no_entry_before="09:50", lot_cap_ignore_residual_frac=0.25)   # pinned: the golden's rules
    cfg["shadow_setups"] = []
    if mutate:
        mutate(cfg)
    b = _GBroker()
    strats = [_GStrat("LONGA", 1), _GStrat("LONGB", 1), _GStrat("SHORTC", -1)]
    r = R.PaperRunner(cfg, strats, {}, broker=b)
    r._sleep = lambda s: None
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px, quote=None: (True, "ok", {}))
    monkeypatch.setattr(r, "manage", lambda now, bars: None)
    state = {"n": 1}
    monkeypatch.setattr(r, "fetch", lambda now: {s: _bars(state["n"], s) for s in SYMS})
    monkeypatch.setattr(r, "_contexts", lambda bars, today: [SimpleNamespace(symbol=s, bars=bars[s], avg_dollar_volume=5e8)
                                                             for s in SYMS])
    r.today = pd.Timestamp("2026-11-27").date()
    for n in range(1, polls + 1):
        state["n"] = n
        now = pd.Timestamp("2026-11-27 10:00", tz=NY) + pd.Timedelta(minutes=n, seconds=5)
        r.step(now)
        r._sync_open()
    r.write_status(now, "trading")
    rows = [(x.symbol, x.strategy, x.status, x.reason, json.loads(x.info or "{}").get("netbeta_shadow"))
            for x in r.journal.signals(r.run_id).itertuples()]
    rs = {k: v for k, v in r.health["risk_state"].items() if k != "safety"}
    return {"rows": rows, "submitted": list(b.submitted), "risk_state": rs}


def test_flags_off_full_poll_matches_pre_change_golden(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("a Friday switch hook ran with every switch off")
    for name in ("_shock_poll", "_shock_value", "_shock_after_reconcile", "_netbeta_tag"):
        monkeypatch.setattr(R.PaperRunner, name, boom)
    monkeypatch.setattr(RiskManager, "_latch_open", boom)
    monkeypatch.setattr(RiskManager, "scaled_check", boom)
    got = json.loads(json.dumps(_golden_run(tmp_path, monkeypatch), default=str))
    with open(GOLDEN) as f:
        want = json.load(f)
    assert got == want
    assert want["risk_state"]["halted"] is True and len(want["submitted"]) == 12   # the scenario reaches the halt


# ------------------------------------------------------------------------------------------------ LATCH-OPEN mark carry
def test_open_marks_carry_last_mark_for_unmarked_held_lot(tmp_path, monkeypatch):
    """Inspector 11-27 #15: a held lot without a mark this poll keeps its last mark for LATCH-OPEN (per-setup marks),
    instead of the whole setup falling back to closed R; open_r (LR3 halt) still counts it 0, as before."""
    r, _ = _runner(tmp_path, monkeypatch)
    r.lots = {"AAA": {"c1": {"strategy": "S1", "side": 1, "qty": 10, "order_id": "o1"}},
              "BBB": {"c2": {"strategy": "S1", "side": 1, "qty": 10, "order_id": "o2"}}}
    r._mtm_lot = {"c1": (50.0, 49.0), "c2": (50.0, 49.0)}
    bar = lambda px: pd.DataFrame({"close": [px]})
    r._open_marks({"AAA": bar(48.0), "BBB": bar(49.0)})
    st = r.risk.state
    assert st.open_r_by_strategy["S1"] == pytest.approx(-2.01 - 1.01, abs=1e-6) and st.unmarked_setups == set()
    tot = r._open_marks({"BBB": bar(48.5)})                 # AAA: no bar this poll
    assert tot == pytest.approx(-1.51, abs=1e-6)            # LR3 open_r unchanged: the unmarked lot counts 0
    assert st.open_r_by_strategy["S1"] == pytest.approx(-2.01 - 1.51, abs=1e-6)   # AAA carried at its last mark
    assert st.unmarked_setups == set() and st.carried_marks == 1 and st.carried_marks_total == 1
    r._mtm_lot.pop("c2")                                    # no entry/stop any more: carried too
    r._open_marks({"AAA": bar(47.0)})
    assert st.open_r_by_strategy["S1"] == pytest.approx(-3.01 - 1.51, abs=1e-6) and st.carried_marks == 1
    r.lots["CCC"] = {"c3": {"strategy": "S2", "side": 1, "qty": 10, "order_id": "o3"}}   # never marked
    r._open_marks({"AAA": bar(47.0)})
    assert st.unmarked_setups == {"S2"} and "S2" not in st.open_r_by_strategy
    del r.lots["AAA"]                                       # gone lots leave the carry
    r._open_marks({})
    assert set(r._latch_last) == {"c2"} and st.carried_marks_total == 4


def test_latch_open_latches_with_carried_mark_and_counts_fallbacks(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch)
    rm = _rm({"latch_counts_open": True})
    r.risk = rm
    r.lots = {"AAA": {"c1": {"strategy": "S1", "side": 1, "qty": 10, "order_id": "o1"}}}
    r._mtm_lot = {"c1": (50.0, 49.0)}
    rm.state.realized_r_by_strategy = {"S1": -1.0}
    r._open_marks({"AAA": pd.DataFrame({"close": [48.5]})})            # -1.51
    r._open_marks({})                                                   # no bar: carried
    assert rm.check(_sig("BBB"), 50.0) == (False, "setup daily loss limit (open)")
    assert rm.latch_open_hits["S1"] == pytest.approx(-2.51, abs=1e-3)
    rm2 = _rm({"latch_counts_open": True})
    rm2.state.realized_r_by_strategy, rm2.state.unmarked_setups = {"S1": -1.0}, {"S1"}
    rm2.check(_sig(), 50.0)
    rm2.check(_sig("BBB"), 50.0)
    sf = rm2.safety_status()["latch_counts_open"]
    assert sf["fallbacks"] == {"S1": 2} and sf["fallbacks_total"] == 2 and sf["carried_marks_total"] == 0
    off = _rm({"latch_counts_open": False}).safety_status()["latch_counts_open"]
    assert "fallbacks" not in off                                      # flags off: status shape unchanged
