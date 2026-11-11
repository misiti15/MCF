"""LIVE-READY fixes approved by the owner 2026-11-11 ("All yes except for LR6"): LR1, LR2, LR3, LR4, LR5, LR7, LR8
(research/live_ready/NOTES.md). Educational only - not financial advice."""
import json
import subprocess
from datetime import time
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import yaml

from mcf import costs as C
from mcf.config import load_config
from mcf.execution import handover as ho
from mcf.execution import kill as K
from mcf.execution import market_calendar as mc
from mcf.execution import runner as R
from mcf.execution import session_guard as sg
from mcf.execution import watchdog as wd
from mcf.strategies.base import Signal

NY = "America/New_York"
ROOT = Path(__file__).resolve().parents[1]
CTX = SimpleNamespace(bars=pd.DataFrame({"volume": [1e6] * 5}), avg_dollar_volume=5e8)


def at(s):
    return pd.Timestamp(s, tz=NY)


class Broker:
    """Fake broker: positions, a scripted clock, closes that may fail."""

    def __init__(self, clock_times=None, held=None, close_fails=0, next_close=None):
        self.submitted, self.held = [], dict(held or {})
        self.times = list(clock_times or [])
        self.closes, self.cancels, self.close_fails = [], 0, close_fails
        self.next_close = next_close
        self.now = None

    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):
        return dict(self.held)

    def submit_bracket(self, sig, qty, coid):
        self.submitted.append(coid)
        return SimpleNamespace(id=f"o{len(self.submitted)}")

    def clock(self):
        if self.times:
            self.now = self.times.pop(0)
        ts = self.now
        close = self.next_close or ts.normalize() + pd.Timedelta(hours=16)
        is_open = ts.normalize() + pd.Timedelta(hours=9, minutes=30) <= ts < close
        nxt = ts.normalize() + pd.Timedelta(days=1, hours=9, minutes=30)
        return SimpleNamespace(timestamp=ts.tz_convert("UTC").to_pydatetime(), is_open=is_open,
                               next_open=nxt.tz_convert("UTC").to_pydatetime(),
                               next_close=close.tz_convert("UTC").to_pydatetime())

    def orders_today_with_prefix(self, prefix, after):
        return [SimpleNamespace(symbol=s) for s in self.held]

    def cancel_orders_with_prefix(self, prefix):
        self.cancels += 1

    def close_mcf_position(self, sym, prefix, sleep=None):
        if self.close_fails > 0:
            self.close_fails -= 1
            raise RuntimeError("insufficient qty available")
        self.closes.append(sym)
        self.held.pop(sym, None)
        return True


def _cfg(tmp_path, account="primary"):
    cfg = load_config()
    cfg["account_name"] = account
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    return cfg


def _runner(tmp_path, monkeypatch, broker=None, account="primary"):
    b = broker or Broker()
    r = R.PaperRunner(_cfg(tmp_path, account), [], {}, broker=b)
    r._sleep = lambda s: None
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    monkeypatch.setattr(r, "_restore_from_broker", lambda today: None)
    return r, b


# ------------------------------------------------------------------------------------------------ LR1 half-day close
@pytest.mark.parametrize("day", ["2026-11-27", "2026-12-24"])
def test_lr1_half_days_flatten_at_1255(day):
    close = mc.session_close(day, broker=SimpleNamespace())      # no calendar client -> the known early closes
    assert close == time(13, 0) and mc.is_early_close(close)
    assert mc.flatten_time("15:55", close, 5) == time(12, 55)
    assert mc.flatten_time("15:55", mc.session_close("2026-11-12", broker=SimpleNamespace())) == time(15, 55)


def test_lr1_calendar_answer_wins_over_the_table():
    cal = [SimpleNamespace(date="2026-11-27", close="13:00"), SimpleNamespace(date="2026-11-30", close="16:00")]
    client = SimpleNamespace(get_calendar=lambda *a, **k: cal)
    mc._cache.clear()
    assert mc.session_close("2026-11-27", broker=SimpleNamespace(client=client)) == time(13, 0)
    assert mc.session_close("2026-11-30", broker=SimpleNamespace(client=client)) == time(16, 0)
    mc._cache.clear()


@pytest.mark.parametrize("day", ["2026-11-27", "2026-12-24"])
def test_lr1_runner_flattens_before_the_half_day_close(tmp_path, monkeypatch, day):
    times = [at(f"{day} 12:50"), at(f"{day} 12:50"), at(f"{day} 12:54"), at(f"{day} 12:55:30")]
    b = Broker(times, held={"AAA": SimpleNamespace(qty="10", side="long")}, next_close=at(f"{day} 13:00"))
    r, _ = _runner(tmp_path, monkeypatch, b)
    flat, steps = [], []
    monkeypatch.setattr(r, "flatten_mcf", lambda retry_until=None: flat.append(retry_until))
    for name in ("reconcile", "what_if", "write_status", "_check_positions", "_kill_check"):
        monkeypatch.setattr(r, name, lambda *a, **k: None)
    monkeypatch.setattr(r, "step", lambda now: steps.append(now))
    r.run(poll_seconds=60)
    assert r.flatten == time(12, 55) and r.health["early_close"] and r.health["session_close"] == "13:00"
    assert len(flat) == 1 and flat[0] == at(f"{day} 12:59")      # LR7 retries until close - 1 min
    assert r.session_done and len(steps) == 2


def test_lr1_job_after_the_half_day_close_flattens_what_is_left(tmp_path, monkeypatch):
    b = Broker([at("2026-11-27 13:02")], held={"AAA": SimpleNamespace(qty="10", side="long")},
               next_close=at("2026-11-27 13:00"))
    r, _ = _runner(tmp_path, monkeypatch, b)
    flat = []
    monkeypatch.setattr(r, "flatten_mcf", lambda retry_until=None: flat.append(1))
    for name in ("reconcile", "what_if", "write_status"):
        monkeypatch.setattr(r, name, lambda *a, **k: None)
    r.run()
    assert flat == [1] and any(a["kind"] == "after_close_exposure" for a in r.health["alerts"])


def test_lr1_watchdog_guard_and_eod_follow_the_calendar_close():
    live = load_config()["live"]
    d = wd.decide({"asof": "2026-11-27T18:02:00+00:00"}, at("2026-11-27 13:03"), ["AAA"], 0, live, time(13, 0), time(12, 55))
    assert d["action"] == "flatten" and any(x.startswith("after_flatten") for x in d["reasons"])
    assert wd.decide(None, at("2026-11-27 13:10"), ["AAA"], 0, live, time(13, 0), time(12, 55))["action"] == "none"
    # a regular day keeps 16:05 as the end of the window
    assert wd.decide(None, at("2026-11-12 16:03"), ["AAA"], 0, live)["action"] == "flatten"
    g = sg.decide(at("2026-11-27 12:40"), True, [], {}, ["primary"], 0, time(13, 0))
    assert g["action"] == "none" and "12:30" in g["note"]
    assert sg.decide(at("2026-11-12 12:40"), True, [], {}, ["primary"], 0)["action"] == "dispatch"
    assert ho.decide_eod(at("2026-11-27 12:57"), True, [], {}, 1, [], 0, time(12, 55))["action"] == "dispatch"
    assert ho.decide_eod(at("2026-11-12 12:57"), True, [], {}, 1, [], 0, time(15, 55))["action"] == "none"


# ------------------------------------------------------------------------------------------------ LR2 R after costs
def _tr(**kw):
    base = dict(symbol="AAA", strategy="S1", side=1, date="2026-11-12", entry=100.0, stop=99.0, target=102.0, exit=99.0,
                exit_reason="stop", shares=10, pnl=-10.0, r_multiple=-1.0, pnl_adj=-11.0, meta="",
                entry_time="2026-11-12 10:00", exit_time="2026-11-12 10:30", signal_time="2026-11-12 10:00")
    base.update(kw)
    return base


def test_lr2_cost_r_uses_pnl_adj_and_keeps_raw():
    df = pd.DataFrame([_tr(), _tr(pnl_adj=None, r_multiple=0.5), _tr(stop=100.0, pnl_adj=-3.0, r_multiple=0.0)])
    out = C.with_cost_r(df)
    assert out["r_multiple"].round(3).tolist() == [-1.1, 0.5, 0.0]   # no pnl_adj / zero risk: r_multiple kept
    assert out["r_raw"].tolist() == [-1.0, 0.5, 0.0]
    assert C.with_cost_r(out) is out                                    # idempotent


def test_lr2_leaderboard_and_scorecard_show_r_after_costs():
    from mcf.report import scorecard

    df = pd.DataFrame([_tr(), _tr(exit=101.0, pnl=10.0, r_multiple=1.0, pnl_adj=9.5, exit_reason="target")])
    card = scorecard.build(C.with_cost_r(df), 4, cfg={"strategies": {"S1": {"enabled": True}}}, account="primary")
    row = card["leaderboard"][0]
    assert row["avg_r"] == pytest.approx((-1.1 + 0.95) / 2, abs=1e-3) and card["setups"][0]["avg_r"] == row["avg_r"]


def test_lr2_every_report_entry_point_uses_r_after_costs():
    for f in ("mcf/report/eod.py", "mcf/report/brief.py", "mcf/report/daily_review.py", "mcf/report/live_status.py",
              "mcf/report/intraday.py", "mcf/dashboard/build.py", "mcf/cli.py"):
        assert "with_cost_r" in (ROOT / f).read_text(), f
    assert "R after costs" in (ROOT / "mcf/report/trade_charts.py").read_text()


def test_lr2_live_status_closed_trades_carry_both(tmp_path, monkeypatch):
    from mcf.report.live_status import build_status

    r, _ = _runner(tmp_path, monkeypatch)
    r.dry_run = True
    r.journal.add_trades(r.run_id, pd.DataFrame([_tr()]))
    st = build_status(r, at("2026-11-12 11:00"), "trading")
    assert st["closed"][0]["r"] == -1.1 and st["closed"][0]["r_raw"] == -1.0 and st["today"]["avg_r"] == -1.1
    assert st["r_basis"] == "R after costs"


# ------------------------------------------------------------------------------------------------ LR3 cost-in loss stops
def _book(r, rows):
    r.journal.add_trades(r.run_id, pd.DataFrame(rows))


def test_lr3_primary_halt_and_latch_count_r_after_costs(tmp_path, monkeypatch):
    day = "2026-11-12"
    rows = [_tr(strategy="S1", date=day, exit_time=f"{day} 10:{i:02d}", entry_time=f"{day} 10:00",
                signal_time=f"{day} 10:00", r_multiple=-0.95, pnl=-9.5, pnl_adj=-10.5) for i in range(2)]
    r, _ = _runner(tmp_path, monkeypatch)
    _book(r, rows)
    r.restore(pd.Timestamp(day).date())
    assert r.cost_r_stops and r.risk.state.realized_r == pytest.approx(-2.1)   # raw would be -1.9: not latched
    assert "S1" in r.risk.state.setup_stopped
    r2, _ = _runner(tmp_path / "t", monkeypatch, account="testing")
    (tmp_path / "t").mkdir(exist_ok=True)
    _book(r2, rows)
    r2.restore(pd.Timestamp(day).date())
    assert not r2.cost_r_stops and r2.risk.state.realized_r == pytest.approx(-1.9)
    assert r2.risk.state.realized_cost_r == pytest.approx(-2.1)


def test_lr3_primary_halt_counts_open_marks(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
    now = at("2026-11-12 11:00")
    r.restore(now.date())
    r.risk.state.realized_r = -8.0
    r.lots = {"AAA": {"c1": {"strategy": "S1", "side": 1, "qty": 10, "order_id": "o1", "coid": "c1"}}}
    r._mtm_lot["c1"] = (100.0, 99.0)
    r._mtm_restored = True
    bars = {"AAA": pd.DataFrame({"close": [88.0]})}
    assert r._open_marks(bars) == pytest.approx((88.0 - 100.0 - 0.01) / 1.0)
    ok, why = r.risk.check(Signal("BBB", "S2", 1, 4, stop=49.0, target=52.0), 50.0)
    assert (ok, why) == (False, "daily loss limit")
    r2, _ = _runner(tmp_path / "x", monkeypatch, account="testing")
    r2.risk.state.realized_r, r2.risk.state.open_r = -8.0, -500.0
    assert r2.risk.check(Signal("BBB", "S2", 1, 4, stop=49.0, target=52.0), 50.0)[0]   # 120R backstop, realized only


# ------------------------------------------------------------------------------------------------ LR4 kill switch
def test_lr4_flag_update_and_scope():
    f = K.update({}, "primary", "no-new-entries", "owner", at("2026-11-12 10:00"))
    assert K.flag_for(f, "primary")["mode"] == "entries" and K.flag_for(f, "testing") is None
    f = K.update(f, "all", "flatten", "owner", at("2026-11-12 10:01"))
    assert K.flag_for(f, "testing")["mode"] == "flatten" and K.flag_for(f, "primary")["mode"] == "entries"
    assert K.flag_for(K.update(f, "all", "resume"), "primary") is None
    assert K.flag_for(K.update(f, "primary", "resume"), "primary")["scope"] == "all"


def test_lr4_runner_stops_entries_and_flattens_once(tmp_path, monkeypatch):
    halt = tmp_path / "HALT.json"
    monkeypatch.setenv("MCF_HALT_FILE", str(halt))
    r, b = _runner(tmp_path, monkeypatch)
    now = at("2026-11-12 11:00")
    r._kill_check(now)
    assert r.kill is None
    halt.write_text(json.dumps(K.update({}, "primary", "flatten", "owner", now)))
    flat = []
    monkeypatch.setattr(r, "flatten_mcf", lambda retry_until=None: flat.append(retry_until))
    r._kill_check(now)
    r._kill_check(now + pd.Timedelta(minutes=1))
    assert r.kill["mode"] == "flatten" and len(flat) == 1 and r.health["kill"]["scope"] == "primary"
    monkeypatch.setattr(r, "fetch", lambda now: {})
    monkeypatch.setattr(r, "_check_data", lambda now, bars: False)
    monkeypatch.setattr(r, "_contexts", lambda *a: (_ for _ in ()).throw(AssertionError("evaluated entries")))
    r.step(now)                                       # returns before any setup is evaluated
    halt.write_text(json.dumps(K.update(json.loads(halt.read_text()), "primary", "resume")))
    r._kill_check(now + pd.Timedelta(minutes=2))
    assert r.kill is None


def test_lr4_flag_read_through_git(tmp_path, monkeypatch):
    monkeypatch.delenv("MCF_HALT_FILE", raising=False)
    origin, work, state = tmp_path / "origin.git", tmp_path / "w", tmp_path / "state"
    run = lambda *a, cwd=None: subprocess.run(a, cwd=cwd, check=True, capture_output=True)
    run("git", "init", "-q", "--bare", str(origin))
    run("git", "clone", "-q", str(origin), str(state))
    K._last.update(sha=None, flags={})
    assert K.read_flag(str(state)) == {}                   # no mcf-control branch: no flag
    run("git", "init", "-q", str(work))
    (work / "HALT.json").write_text(json.dumps(K.update({}, "all", "entries", "owner", at("2026-11-12 10:00"))))
    run("git", "-C", str(work), "checkout", "-q", "-b", "mcf-control")
    run("git", "-C", str(work), "add", "HALT.json")
    run("git", "-C", str(work), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "halt")
    run("git", "-C", str(work), "push", "-q", str(origin), "mcf-control")
    assert K.flag_for(K.read_flag(str(state)), "gen")["mode"] == "entries"


def test_lr4_kill_flatten_dry_run_and_workflow():
    b = Broker(held={"AAA": object(), "BBB": object()})
    out = K.flatten("mcf-", broker=b, dry_run=True)
    assert out["would_flatten"] == ["AAA", "BBB"] and not b.closes
    wf = yaml.safe_load((ROOT / ".github/workflows/kill.yml").read_text())
    inputs = wf[True]["workflow_dispatch"]["inputs"]
    assert {"no-new-entries", "flatten"} <= set(inputs["mode"]["options"]) and "all" in inputs["account"]["options"]
    assert "primary" in inputs["account"]["options"] and "schedule" not in wf[True]
    readme = (ROOT / "README.md").read_text()
    assert "Kill switch" in readme and "kill.yml" in readme


# ------------------------------------------------------------------------------------------------ LR5 position check
def _pos(qty, side="long", px=100.0):
    return SimpleNamespace(qty=str(qty), side=side, avg_entry_price=str(px))


def test_lr5_mtum_like_split_is_flagged_and_blocks_entries(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
    now = at("2026-11-12 11:00")
    r.restore(now.date())
    r.open_strategy["MTUM"] = "S1"
    r.lots = {"MTUM": {"c1": {"strategy": "S1", "side": 1, "qty": 10, "order_id": "o1", "coid": "c1"}}}
    b.held = {"MTUM": _pos(40, px=60.0)}                 # fake 1:4 split: 4x the shares at 1/4 the price
    for i in range(r.pos_persist - 1):
        r._sync_open()
        r._check_positions(now + pd.Timedelta(minutes=i))
        assert not r.health["position_mismatch"] and "MTUM" not in r.mismatch_block   # transient: not yet
    r._sync_open()
    r._check_positions(now + pd.Timedelta(minutes=9))
    m = r.health["position_mismatch"][0]
    assert m["symbol"] == "MTUM" and m["kind"] == "corporate_action" and m["ratio"] == 4.0
    assert "MTUM" in r.mismatch_block and any(a["kind"] == "position_mismatch" for a in r.health["alerts"])
    r._enter(Signal("MTUM", "S2", 1, 4, stop=59.0, target=62.0), 60.0, ("MTUM", "S2"), CTX, now)
    assert not b.submitted and r.journal.signals(r.run_id, str(now.date())).iloc[-1].reason == "position mismatch"
    assert "MTUM" in b.held                               # never closed automatically


def test_lr5_soxx_like_phantom_is_flagged(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
    r.pos_persist = 1
    b.held = {"SOXX": _pos(-12, side="short")}           # carried short MCF has no lot for (T1X)
    r._sync_open()
    r._check_positions(at("2026-11-12 10:00"))
    m = r.health["position_mismatch"][0]
    assert (m["symbol"], m["kind"], m["broker_qty"], m["journal_qty"]) == ("SOXX", "unknown_symbol", -12.0, 0.0)
    assert r.mismatch_block == {"SOXX"}


def test_lr5_matching_and_pending_symbols_are_not_flagged(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
    r.pos_persist = 1
    r.open_strategy.update(AAA="S1", BBB="S1")
    r.lots = {"AAA": {"c1": {"strategy": "S1", "side": -1, "qty": 5, "order_id": "o1", "coid": "c1"},
                      "c2": {"strategy": "S2", "side": -1, "qty": 7, "order_id": "o2", "coid": "c2", "left": 3}},
              "BBB": {"c3": {"strategy": "S1", "side": 1, "qty": 9, "order_id": "o3", "coid": "c3"}}}
    b.held = {"AAA": _pos(-8, side="short")}
    r.pending["BBB"] = 1e18                               # entry submitted, not filled yet
    r._sync_open()
    r._check_positions(at("2026-11-12 10:00"))
    assert r.health["position_mismatch"] == [] and not r.mismatch_block


# ------------------------------------------------------------------------------------------------ LR7 flatten failure
def test_lr7_flatten_retries_until_it_closes(tmp_path, monkeypatch):
    ts = [at("2026-11-12 15:55") + pd.Timedelta(seconds=20 * i) for i in range(30)]
    b = Broker(ts, held={"AAA": _pos(10)}, close_fails=5)
    r, _ = _runner(tmp_path, monkeypatch, b)
    r.flatten_mcf(retry_until=at("2026-11-12 15:59"))
    assert b.closes == ["AAA"] and r.health["flatten_failed"] == [] and r.health["flatten_retry"]["retries"] >= 1


def test_lr7_flatten_failure_alerts_after_the_deadline(tmp_path, monkeypatch):
    ts = [at("2026-11-12 15:55") + pd.Timedelta(seconds=20 * i) for i in range(40)]
    b = Broker(ts, held={"AAA": _pos(10)}, close_fails=10 ** 6)
    r, _ = _runner(tmp_path, monkeypatch, b)
    r.flatten_mcf(retry_until=at("2026-11-12 15:59"))
    assert r.health["flatten_failed"] == ["AAA"] and r.health["flatten_retry"]["retries"] >= 10
    assert r.health["alerts"][-1]["kind"] == "flatten_failed"
    live = load_config()["live"]
    d = wd.decide({"asof": "2026-11-12T20:58:30+00:00", "health": {"flatten_failed": ["AAA"]}}, at("2026-11-12 16:02"),
                  ["AAA"], 0, live)
    assert d["action"] == "flatten" and any(x.startswith("flatten_failed") for x in d["reasons"])


def test_lr7_watchdog_acts_on_primary_until_1605():
    wf = (ROOT / ".github/workflows/watchdog.yml").read_text()
    assert "matrix.account == 'primary' && 'act' || 'dry'" in wf and "13-21 * * 1-5" in wf and "1606" in wf


# ------------------------------------------------------------------------------------------------ LR8 cost model
MODEL = load_config()["costs"]["live_model"]


def test_lr8_components():
    m = {k: v for k, v in MODEL.items() if k != "fees"}
    # stop: max($0.02, 4 bps): $20 -> $0.02; $250 -> $0.10 per share
    assert C.lot_costs(1, 20.0, 100, [(100, 19.5, "stop")], None, "2026-11-12", m)["stop"] == pytest.approx(2.0)
    assert C.lot_costs(1, 250.0, 10, [(10, 249.0, "stop")], None, "2026-11-12", m)["stop"] == pytest.approx(0.996)
    # target at the limit: a long target filled 3c better gives the 3c back; a short too
    assert C.lot_costs(1, 50.0, 10, [(10, 52.03, "target")], 52.0, "2026-11-12", m)["target"] == pytest.approx(0.3)
    assert C.lot_costs(-1, 50.0, 10, [(10, 47.96, "target")], 48.0, "2026-11-12", m)["target"] == pytest.approx(0.4)
    assert C.lot_costs(1, 50.0, 10, [(10, 52.0, "target")], 52.0, "2026-11-12", m)["target"] == 0
    # market exits max($0.01, 1 bp); entry 1 bp
    c = C.lot_costs(1, 300.0, 10, [(10, 301.0, "flatten")], None, "2026-11-12", m)
    assert c["market"] == pytest.approx(0.301) and c["entry"] == pytest.approx(0.3)


def test_lr8_fees_dated():
    f = C.fees(1, 100.0, 100, [(100, 100.0, "stop")], "2026-11-12", MODEL)
    assert f["sec"] == pytest.approx(20.60 * 10_000 / 1e6) and f["taf"] == pytest.approx(0.0195)
    assert f["cat"] == pytest.approx(0.00005 * 200)
    assert C.fees(1, 100.0, 100, [(100, 100.0, "stop")], "2026-03-01", MODEL)["sec"] == 0.0     # before 2026-04-04
    big = C.fees(-1, 10.0, 100_000, [(100_000, 10.0, "stop")], "2026-11-12", MODEL)            # short: entry is the sale
    assert big["taf"] == pytest.approx(9.79) and big["sec"] == pytest.approx(20.60)


def test_lr8_applies_forward_only():
    cfg = load_config()
    parts = [(10, 99.0, "stop")]
    old, tag = C.pnl_adj(-10.0, 1, 100.0, 10, parts, None, "2026-11-11", cfg)
    assert (old, tag) == (pytest.approx(-10.2), "flat")
    new, tag = C.pnl_adj(-10.0, 1, 100.0, 10, parts, None, "2026-11-12", cfg)
    assert tag == "lr8" and new < old


def test_lr8_reconcile_books_the_model(tmp_path):
    from mcf.execution.reconcile import reconcile_day
    from mcf.journal import Journal

    j = Journal(tmp_path / "j.db")
    rid = j.get_or_create_run("paper", "x")
    j.record_order(rid, "AAA", "S1", 1, 10, 100.0, 99.0, 102.0, "p1", "submitted", "")
    t0 = pd.Timestamp("2026-11-12 15:00", tz="UTC")
    leg_t = SimpleNamespace(id="t1", status="filled", order_type="limit", filled_avg_price="102.05", filled_qty="10",
                            filled_at=t0 + pd.Timedelta(minutes=5), client_order_id="u1", legs=None, symbol="AAA",
                            side="sell", replaces=None, canceled_at=None, order_class="simple")
    leg_s = SimpleNamespace(id="s1", status="canceled", order_type="stop", filled_avg_price=None, filled_qty="0",
                            filled_at=None, client_order_id="u2", legs=None, symbol="AAA", side="sell", replaces=None,
                            canceled_at=t0 + pd.Timedelta(minutes=5), order_class="simple")
    parent = SimpleNamespace(id="p1", status="filled", filled_avg_price="100.0", filled_qty="10", filled_at=t0,
                             client_order_id="mcf-S1-AAA-20261112-1000", legs=[leg_t, leg_s], symbol="AAA", side="buy",
                             replaces=None, order_type="market", order_class="bracket")
    broker = SimpleNamespace(closed_orders_today=lambda after: [parent])
    tr = reconcile_day(broker, j, rid, "2026-11-12", load_config())
    row = tr.iloc[0]
    assert row.pnl == pytest.approx(20.5) and "costs=lr8" in row.meta
    want = 20.5 - C.lot_costs(1, 100.0, 10, [(10, 102.05, "target")], 102.0, "2026-11-12", MODEL)["total"]
    assert row.pnl_adj == pytest.approx(want) and row.pnl_adj < 20.0     # target improvement given back


def test_glitch_checks_doc_lists_ten_checks():
    txt = (ROOT / "research/live_ready/GLITCH_CHECKS.md").read_text()
    import re

    assert sum(1 for line in txt.splitlines() if re.match(r"^\d+\. ", line)) == 10
