"""Friday 11-27 safety switches (mcf/execution/safety.py, config `risk:`): LATCH-OPEN, HS-SCALE, SHOCK-V, B8 shadow.
Every switch defaults OFF in every account; none ever flattens. Educational only - not financial advice."""
import json

import pandas as pd
import pytest

from mcf.config import load_config
from mcf.execution import safety as S
from mcf.execution.risk import RiskManager
from mcf.strategies.base import Signal
from tests.test_live_ready_lr import CTX, NY, _runner

ACCTS = ["primary", "testing", "testing2", "gen", "graveyard", "livelab", "explore1", "testingd", "testinge", "testingf"]


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


def test_default_off_is_a_noop_on_check():
    """Default config: an open loss far past every new threshold changes nothing the loss stops decide."""
    rm = _rm()
    rm.state.open_r, rm.state.open_r_by_strategy = -60.0, {"S1": -50.0}
    rm.state.realized_r, rm.state.realized_r_by_strategy = -1.0, {"S1": -1.0}
    assert rm.check(_sig(), 50.0) == (True, "ok")


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
    assert rm.check(_sig(setup="S1"), 50.0) == (False, "setup daily loss limit")
    assert rm.check(_sig("BBB", setup="S2"), 50.0) == (True, "ok")
    rm.state.open_r_by_strategy = {"S1": +5.0}           # latched: a recovery does not undo it
    assert rm.check(_sig("CCC", setup="S1"), 50.0)[1] == "setup daily loss limit"


def test_latch_open_off_counts_closed_only():
    rm = _rm({"latch_counts_open": False})
    rm.state.realized_r_by_strategy, rm.state.open_r_by_strategy = {"S1": -1.0}, {"S1": -5.0}
    assert rm.check(_sig(), 50.0) == (True, "ok")


def test_latch_open_minus_3r_and_other_accounts():
    rm = _rm({"latch_counts_open": True, "latch_open_r": 3})
    rm.state.realized_r_by_strategy, rm.state.open_r_by_strategy = {"S1": -1.0}, {"S1": -1.5}
    assert rm.check(_sig(), 50.0) == (True, "ok")         # -2.5 > -3
    rm.state.open_r_by_strategy = {"S1": -2.0}
    assert rm.check(_sig(), 50.0)[1] == "setup daily loss limit"
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


def test_shock_v_carries_lots_gone_before_reconcile(tmp_path, monkeypatch):
    """A losing lot that goes flat at the broker leaves self.lots before reconcile books its R: no false fall."""
    r, _ = _runner(tmp_path, monkeypatch)
    r.shock = S.ShockV({"enabled": True}, "primary")
    t0 = at("2026-11-27 11:00")
    st = r.risk.state
    r._lot_marks, st.open_r = {"c1": -10.0}, -10.0
    r._shock_poll(t0, stale=False)
    r._lot_marks, st.open_r = {}, 0.0                    # lot gone, reconcile not yet run: carried at -10
    r._shock_poll(t0 + pd.Timedelta(minutes=1), stale=False)
    assert r.shock.last["r"] == -10.0
    st.realized_r = -10.0                                # reconcile booked it
    r._shock_after_reconcile()
    for i in (2, 3):
        r._shock_poll(t0 + pd.Timedelta(minutes=i), stale=False)
    assert r.shock.last["r"] == -10.0 and r.shock.fired is None and not st.halted
