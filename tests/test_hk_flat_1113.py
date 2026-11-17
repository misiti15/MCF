"""HK-FLAT-1113 (housekeeping, no setup/exit change): final push before the job limit, adoption of broker positions with
no journal lot, flatten retries to close + 5 min. Educational only - not financial advice."""
import json
from types import SimpleNamespace

import pandas as pd
import yaml

from mcf.execution import handover as ho
from mcf.execution import runner as R
from mcf.execution.session import FINAL_PUSH_LEAD_MIN, JOB_LIMIT_MIN, job_deadline
from tests.test_live_ready_lr import ROOT, Broker, _pos, _runner, at


# ------------------------------------------------------------------ 1) stop + push at limit - 20 min, then hand over
def test_slot_ends_20_min_before_the_job_limit():
    t0 = at("2026-11-13 08:35")
    now = at("2026-11-13 08:55")                       # mcf live starts after 20 min of install + prep
    assert job_deadline(now, {}) == now + pd.Timedelta(minutes=340)        # 14:35 > the 14:30 kill: old behaviour
    until = job_deadline(now, {}, str(t0.timestamp()))
    assert until == t0 + pd.Timedelta(minutes=JOB_LIMIT_MIN - FINAL_PUSH_LEAD_MIN) == at("2026-11-13 14:10")
    fast = at("2026-11-13 08:36")                      # quick start: max_job_minutes still wins when earlier
    assert job_deadline(fast, {"max_job_minutes": 60}, t0.timestamp()) == fast + pd.Timedelta(minutes=60)
    assert job_deadline(at("2026-11-14 10:00"), {}, t0.timestamp()) is None   # weekend


def test_successor_needed_when_the_job_stops_before_1550():
    own = [{"id": 1, "status": "in_progress"}]
    # limit 15:55 -> stops 15:35: a successor must cover the 15:55 flatten
    assert ho.decide_trade(at("15:27"), at("15:55"), "primary", own, {}, 1, 0, FINAL_PUSH_LEAD_MIN)["action"] == "dispatch"
    assert ho.decide_trade(at("15:50"), at("16:15"), "primary", own, {}, 1, 0, FINAL_PUSH_LEAD_MIN)["action"] == "none"
    wf = yaml.safe_load((ROOT / ".github/workflows/trade.yml").read_text())
    assert wf["jobs"]["session"]["timeout-minutes"] == JOB_LIMIT_MIN
    assert "default=28" in (ROOT / "mcf/execution/handover.py").read_text()


def test_run_hands_over_at_until(tmp_path, monkeypatch):
    times = [at("2026-11-13 14:08"), at("2026-11-13 14:08"), at("2026-11-13 14:10")]
    r, b = _runner(tmp_path, monkeypatch, Broker(times))
    phases, steps = [], []
    for name in ("reconcile", "what_if", "_check_positions", "_kill_check"):
        monkeypatch.setattr(r, name, lambda *a, **k: None)
    monkeypatch.setattr(r, "write_status", lambda now, phase: phases.append(phase))
    monkeypatch.setattr(r, "step", lambda now: steps.append(now))
    r.run(until=at("2026-11-13 14:10"))
    assert len(steps) == 1 and phases[-1] == "handover" and not r.session_done


# ------------------------------------------------------------------ 2) adopt broker positions with no journal lot
class PrefixBroker(Broker):
    def __init__(self, orders, **kw):
        super().__init__(**kw)
        self.orders = orders

    def orders_today_with_prefix(self, prefix, after):
        return [o for o in self.orders if o.client_order_id.startswith(prefix)]


def test_successor_adopts_orphan_positions_and_flattens_them(tmp_path, monkeypatch):
    pre = R.COID_PREFIX
    orders = [SimpleNamespace(symbol="AAA", client_order_id=f"{pre}S1-AAA-20261113"),
              SimpleNamespace(symbol="BBB", client_order_id=f"{pre}flatten-BBB-20261112155500"),
              SimpleNamespace(symbol="ZZZ", client_order_id="other-ZZZ")]
    held = {"AAA": _pos(10), "BBB": _pos(-4, side="short"), "ZZZ": _pos(7), "CCC": _pos(3)}
    b = PrefixBroker(orders, held=held, clock_times=[at("2026-11-13 15:55")] * 40)
    r, _ = _runner(tmp_path, monkeypatch, b)
    r.status_path = str(tmp_path / "status.json")
    r.restore(at("2026-11-13 10:00").date())
    assert set(r.lots) == {"AAA", "BBB"} and r.open_strategy["BBB"] == R.PaperRunner.ADOPTED
    lot = r.lots["BBB"][f"{pre}_adopted-BBB"]
    assert lot["side"] == -1 and lot["qty"] == 4 and lot["order_id"] is None
    assert r._expected_qty() == {"AAA": 10.0, "BBB": -4.0}                    # LR5 sees them as expected
    assert [a["kind"] for a in r.health["alerts"]] == ["adopted_positions"]
    assert json.loads((tmp_path / "adopted" / "2026-11-13.json").read_text()) == ["AAA", "BBB"]
    assert r.journal.open_orders(r.run_id).empty                             # never journaled -> no setup stats
    r._release_closed_lots()
    assert "BBB" in r.lots                                                   # no journal order: not released
    # a second successor the same day adopts again but does not alert again
    r2, _ = _runner(tmp_path, monkeypatch, b)
    r2.status_path = r.status_path
    r2.restore(at("2026-11-13 12:00").date())
    assert "BBB" in r2.lots and not r2.health.get("alerts")
    r2.flatten_mcf(retry_until=at("2026-11-13 16:05"))
    assert sorted(b.closes) == ["AAA", "BBB"] and set(b.held) == {"ZZZ", "CCC"}   # never anything else


# ------------------------------------------------------------------ 3) flatten retries until close + 5 min, logs leftovers
def test_retry_deadline_is_close_plus_5(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch)
    assert r._retry_deadline(at("2026-11-13 15:55")) == at("2026-11-13 16:05")


def test_flatten_retries_full_list_and_logs_each_leftover(tmp_path, monkeypatch, capsys):
    ts = [at("2026-11-13 15:55") + pd.Timedelta(seconds=20 * i) for i in range(80)]
    b = Broker(ts, held={"AAA": _pos(10), "BBB": _pos(5)}, close_fails=10 ** 6)
    r, _ = _runner(tmp_path, monkeypatch, b)
    late = []

    def lookup(prefix, after):                       # BBB only shows up in the order list later (state missed it)
        late.append(1)
        return [SimpleNamespace(symbol="AAA")] + ([SimpleNamespace(symbol="BBB")] if len(late) > 2 else [])

    b.orders_today_with_prefix = lookup
    r.flatten_mcf(retry_until=at("2026-11-13 16:05"))
    out = capsys.readouterr().out
    assert r.health["flatten_failed"] == ["AAA", "BBB"] and r.health["flatten_retry"]["retries"] >= 25
    assert "FLATTEN LEFTOVER AAA" in out and "FLATTEN LEFTOVER BBB" in out


# ------------------------------------------------------------------ 1b) a late successor (15:50 - 16:05 ET) only closes
def test_late_start_window_is_flatten_only():
    from mcf.execution.session import flatten_only

    for hm in ("15:50", "15:54", "16:04"):
        assert job_deadline(at(f"2026-11-13 {hm}"), {}) is not None and flatten_only(at(f"2026-11-13 {hm}"))
    assert job_deadline(at("2026-11-13 16:05"), {}) is None and not flatten_only(at("2026-11-13 15:49"))
    run = next(s for s in yaml.safe_load((ROOT / ".github/workflows/trade.yml").read_text())["jobs"]["session"]["steps"]
               if s.get("name") == "Window check")["run"]
    assert '-lt 1605' in run
    # a job stopping at 15:52 (before the flatten) gets a successor; one stopping at 15:55 does not
    own = [{"id": 1, "status": "in_progress"}]
    assert ho.decide_trade(at("15:40"), at("16:12"), "testingd", own, {}, 1, 0, FINAL_PUSH_LEAD_MIN)["action"] == "dispatch"
    assert ho.decide_trade(at("15:40"), at("16:15"), "testingd", own, {}, 1, 0, FINAL_PUSH_LEAD_MIN)["action"] == "none"


def test_late_successor_takes_no_entries_but_flattens_adopted_lots(tmp_path, monkeypatch):
    pre = R.COID_PREFIX
    orders = [SimpleNamespace(symbol="BBB", client_order_id=f"{pre}S1-BBB-20261112")]
    times = [at("2026-11-13 15:52"), at("2026-11-13 15:52"), at("2026-11-13 15:55:10")] + [at("2026-11-13 15:56")] * 20
    b = PrefixBroker(orders, clock_times=times, held={"BBB": _pos(-4, side="short")})
    r, _ = _runner(tmp_path, monkeypatch, b, account="testingd")
    r.flatten_only = True
    for name in ("reconcile", "what_if", "write_status", "_check_positions", "_kill_check", "fetch", "manage",
                 "scale_outs", "_escalate"):
        monkeypatch.setattr(r, name, lambda *a, **k: {})
    monkeypatch.setattr(r, "_check_data", lambda now, bars: False)
    monkeypatch.setattr(r, "_contexts", lambda *a: (_ for _ in ()).throw(AssertionError("evaluated entries")))
    r.run(poll_seconds=60)
    assert r.session_done and b.closes == ["BBB"] and not b.submitted and r.health["flatten_failed"] == []


def test_after_close_start_flattens_adopted_lots_from_earlier_days(tmp_path, monkeypatch):
    pre = R.COID_PREFIX
    b = PrefixBroker([SimpleNamespace(symbol="BBB", client_order_id=f"{pre}S1-BBB-20261112")],
                     clock_times=[at("2026-11-13 16:02")] * 10, held={"BBB": _pos(5)})
    r, _ = _runner(tmp_path, monkeypatch, b, account="gen")
    for name in ("reconcile", "what_if", "write_status"):
        monkeypatch.setattr(r, name, lambda *a, **k: None)
    real = b.orders_today_with_prefix
    b.orders_today_with_prefix = lambda prefix, after: real(prefix, after) if after.day != 13 else []  # none today
    r.run()
    assert b.closes == ["BBB"]


# ------------------------------------------------------------------ KILL-FLAT open (owner 2026-11-16): adopted lots at 09:30
def test_adopted_lots_close_at_the_open_only_on_the_set_date(tmp_path, monkeypatch):
    pre = R.COID_PREFIX
    orders = [SimpleNamespace(symbol="UNM", client_order_id=f"{pre}S1-UNM-20261113"),
              SimpleNamespace(symbol="AAA", client_order_id=f"{pre}S2-AAA-20261117")]
    b = PrefixBroker(orders, held={"UNM": _pos(12), "AAA": _pos(5)})
    r, _ = _runner(tmp_path, monkeypatch, b, account="graveyard")
    r.restore(at("2026-11-17 08:50").date())
    r.lots["AAA"] = {f"{pre}S2-AAA-20261117": {"strategy": "S2", "side": 1, "qty": 5, "order_id": "o1",
                                                 "coid": f"{pre}S2-AAA-20261117"}}   # a normal journal lot
    r.open_strategy["AAA"] = "S2"
    r._close_adopted_at_open(at("2026-11-17 09:31"))           # option off: nothing
    assert not b.closes
    r.cfg["account"]["close_adopted_at_open"] = "2026-11-18"   # another date: nothing
    r._close_adopted_at_open(at("2026-11-17 09:31"))
    r.cfg["account"]["close_adopted_at_open"] = "2026-11-17"
    r._close_adopted_at_open(at("2026-11-17 09:29"))           # before the open: nothing
    assert not b.closes
    r._close_adopted_at_open(at("2026-11-17 09:30"))
    r._close_adopted_at_open(at("2026-11-17 09:31"))           # once
    assert b.closes == ["UNM"] and "UNM" not in r.lots and "AAA" in r.lots and "AAA" in b.held
    assert [a["kind"] for a in r.health["alerts"]].count("adopted_closed_at_open") == 1
    assert r.health["adopted_closed_at_open"][0]["symbol"] == "UNM"
    assert r.journal.trades(run_id=r.run_id).empty                      # never in setup stats


def test_kill_flat_open_is_set_for_graveyard_and_gen_on_1117_only(monkeypatch):
    from mcf.config import load_config

    for acct in ("primary", "testing", "testing2", "graveyard", "gen", "livelab", "explore1", "testingd", "testinge",
                 "testingf"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        v = load_config()["account"].get("close_adopted_at_open")
        assert v == ("2026-11-17" if acct in ("graveyard", "gen") else None), acct
