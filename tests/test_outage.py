"""Outage protection (owner 2026-10-16, steps 3-6) and the residual-lot cap rule. Educational only - not financial advice."""
from pathlib import Path
from types import SimpleNamespace as NS

import pandas as pd
import pytest
import yaml

from mcf.config import load_config
from mcf.execution import drill
from mcf.execution import runner as R
from mcf.strategies.base import Signal
from tests.test_lots import DAY, NY, LeakyAlpaca, _enter, _runner, _setups, _skips, _three_filled

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------- step 6: fire drills (steps 4 and 5 end to end)
@pytest.mark.parametrize("scenario", sorted(drill.SCENARIOS))
def test_fire_drill(scenario):
    log = drill.run_scenario(scenario)
    assert log and all(x.startswith("PASS") for x in log)


def test_drill_cli_all_pass(capsys):
    with pytest.raises(SystemExit) as e:
        drill.main(["--scenario", "all"])
    assert e.value.code == 0 and capsys.readouterr().out.count("PASSED") == 3


# ---------------------------------------------------------------- step 3: pre-entry cross-check
NOW = pd.Timestamp("2026-10-13 10:00:30", tz=NY)


def _xc_runner(tmp_path, monkeypatch, bid, ask, quote_age_s=2.0, bar_last="09:59"):
    r, c = _runner(tmp_path, monkeypatch)
    r._realism = R.PaperRunner._realism.__get__(r)                    # the real fill-realism + cross-check path
    r._quote = lambda sym: (r._quote_ts.__setitem__(sym, NOW.tz_convert("UTC") - pd.Timedelta(seconds=quote_age_s))
                            or (bid, ask))
    r._utcnow = lambda: NOW.tz_convert("UTC")
    r._now = NOW
    idx = pd.date_range(pd.Timestamp("2026-10-13 09:30", tz=NY), pd.Timestamp(f"2026-10-13 {bar_last}", tz=NY),
                        freq="1min")
    ctx = NS(bars=pd.DataFrame({"volume": 1e6}, index=idx), avg_dollar_volume=5e8)
    return r, c, ctx


def _go(r, ctx, ref=10.0):
    r._enter(Signal("XYZ", "A", 1, 10, stop=9.0, target=12.0), ref, ("XYZ", "A"), ctx, NOW)


def test_crosscheck_passes_normal_entry_and_logs_dev(tmp_path, monkeypatch):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 9.99, 10.01)
    _go(r, ctx, 10.02)
    s = r.journal.signals(r.run_id).iloc[0]
    assert s.status == "submitted" and len(c.orders) == 1
    info = __import__("json").loads(s["info"])
    assert info["quote_dev_pct"] == 0.2 and info["quote_age_s"] == 2.0 and info["bar_age_min"] == 1.5


@pytest.mark.parametrize("kw, ref, why", [
    ({"bid": 10.29, "ask": 10.31}, 10.0, "crosscheck: ref 10.00 vs quote mid 10.30 (2.91% > 2%)"),
    ({"bid": 9.99, "ask": 10.01, "quote_age_s": 400}, 10.0, "crosscheck: quote 400s old > 300s"),
    ({"bid": 9.99, "ask": 10.01, "bar_last": "09:45"}, 10.0, "crosscheck: bar 15.5 min old > 10 min"),
])
def test_crosscheck_rejects_and_journals_reason(tmp_path, monkeypatch, kw, ref, why):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, **kw)
    _go(r, ctx, ref)
    s = r.journal.signals(r.run_id).iloc[0]
    assert (s.status, s.reason) == ("skipped", why) and c.orders == []


def test_crosscheck_zero_disables(tmp_path, monkeypatch):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 10.29, 10.31, quote_age_s=900)
    r.xc_dev = r.xc_age = 0
    _go(r, ctx, 10.0)
    assert len(c.orders) == 1


def test_crosscheck_defaults_in_every_account(monkeypatch):
    for acct in ("primary", "testing", "testing2"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        live = load_config()["live"]
        assert (live["quote_crosscheck_max_dev_pct"], live["quote_crosscheck_max_age_s"],
                live["quote_crosscheck_max_bar_age_min"]) == (2.0, 300, 10)
        assert live["outage"] == {"enabled": True, "enter_pause_min": 5, "protect_min": 15, "flatten_min": 30,
                                  "watchdog_dead_min": 15}
        assert live["lot_cap_ignore_residual_frac"] == 0.25


# ---------------------------------------------------------------- step 4: escalation edge cases
def _frozen_runner(tmp_path, monkeypatch, **outage):
    r, c = _runner(tmp_path, monkeypatch)
    r.outage.update(outage)
    r._contexts = lambda bars, today: []
    return r, c


def _poll(r, hhmm, last):
    idx = pd.date_range(pd.Timestamp("2026-10-13 09:30", tz=NY), pd.Timestamp(f"2026-10-13 {last}", tz=NY), freq="1min")
    b = pd.DataFrame({"open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0, "volume": 1e5}, index=idx)
    r.fetch = lambda now: {s: b for s in ("XYZ", "ABC")}
    r.step(pd.Timestamp(f"2026-10-13 {hhmm}:05", tz=NY))


def test_no_escalation_in_normal_operation_or_short_outage(tmp_path, monkeypatch):
    r, c = _frozen_runner(tmp_path, monkeypatch)
    for m in range(10, 60):                                           # a full hour of fresh bars
        _poll(r, f"10:{m:02d}", f"10:{m - 1:02d}")
    assert r.health["outage_actions"] == []
    for m in range(0, 14):                                            # a 14-minute outage: pause only
        _poll(r, f"11:{m:02d}", "10:58")
    _poll(r, "11:14", "11:13")
    assert [a["action"] for a in r.health["outage_actions"]] == ["pause"] and c.replaced == []
    assert len(r.health["data_outages"]) == 1


def test_escalation_disabled_keeps_pause_only(tmp_path, monkeypatch):
    r, c = _frozen_runner(tmp_path, monkeypatch, enabled=False)
    for m in range(0, 50):
        _poll(r, f"11:{m:02d}", "10:58")
    assert r.health["outage_actions"] == [] and r.health["data_stale"] is not None


def test_protect_never_undone_by_trade_management(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    _three_filled(r, c, A={"be_at_r": 5.0})                            # A is managed (breakeven far away)
    c.price["XYZ"] = 10.5
    r._protect(pd.Timestamp("2026-10-13 11:00", tz=NY), 15, "test")
    act = r.health["outage_actions"][-1]
    assert act["action"] == "protect" and len(act["moved"]) == 3     # all three lots in profit -> breakeven
    m = next(m for m in r.managed.values() if m["strategy"] == "A")
    assert m["stop"] == 10.0


def test_run_loop_survives_clock_failures(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch)
    r.dry_run = True
    calls = {"n": 0}
    real = c.get_clock

    def clock():
        calls["n"] += 1
        if calls["n"] in (2, 3):
            raise ConnectionError("down")
        k = real()
        return NS(is_open=k.is_open, timestamp=pd.Timestamp("2026-10-13 15:56", tz=NY), next_open=k.next_open)

    c.get_clock = clock
    seen = []
    monkeypatch.setattr(r, "_broker_unreachable", lambda now, e: seen.append(str(e)))
    monkeypatch.setattr(r, "what_if", lambda day: None)
    r.run(until=pd.Timestamp.now(tz=NY) + pd.Timedelta(days=1))
    assert seen == ["down", "down"]
    assert r.health["outage_actions"] == []                           # _broker_unreachable patched; nothing recorded


# ---------------------------------------------------------------- step 5: watchdog workflow
def test_watchdog_workflow_is_dry_by_default_and_separate_from_trade():
    wf = yaml.safe_load(open(ROOT / ".github/workflows/watchdog.yml"))
    tr = yaml.safe_load(open(ROOT / ".github/workflows/trade.yml"))
    job = wf["jobs"]["watch"]
    assert "'dry'" in job["env"]["MCF_WATCHDOG_MODE"] and wf["permissions"] == {"contents": "read"}
    assert job["concurrency"]["group"].startswith("mcf-watchdog-") and "mcf-watchdog" not in tr["jobs"]["session"]["concurrency"]["group"]
    assert job["env"]["MCF_COID_PREFIX"] == tr["jobs"]["session"]["env"]["MCF_COID_PREFIX"]
    assert job["env"]["ALPACA_TRADE_API_KEY"] == tr["jobs"]["session"]["env"]["ALPACA_TRADE_API_KEY"]
    assert "SMTP" not in (ROOT / ".github/workflows/watchdog.yml").read_text()             # no emails


def test_watchdog_decide_thresholds():
    from mcf.execution.watchdog import decide

    now = pd.Timestamp("2026-10-13 12:00", tz=NY)
    st = lambda age, stale=None: {"asof": (now - pd.Timedelta(minutes=age)).isoformat(),  # noqa: E731
                                  "health": {"data_stale": {"since": str(now - pd.Timedelta(minutes=stale))} if stale else None}}
    live = {}
    assert decide(st(14), now, ["XYZ"], 2, live)["action"] == "none"
    assert decide(st(16), now, ["XYZ"], 2, live)["action"] == "flatten"
    assert decide(st(16), now, [], 0, live)["action"] == "none"
    assert decide(None, now, ["XYZ"], 0, live)["action"] == "flatten"
    assert decide(st(1, stale=29), now, ["XYZ"], 2, live)["action"] == "none"
    assert decide(st(1, stale=31), now, ["XYZ"], 2, live)["action"] == "flatten"
    assert decide(st(60), pd.Timestamp("2026-10-13 09:20", tz=NY), ["XYZ"], 2, live)["action"] == "none"
    assert decide(st(60), pd.Timestamp("2026-10-17 12:00", tz=NY), ["XYZ"], 2, live)["action"] == "none"   # Saturday


# ---------------------------------------------------------------- residual lots and the lot cap (option B)
def _residual_setup(tmp_path, monkeypatch, left, frac=0.25):
    """left = share of B's lot still open after a partial exit (sizing-independent)."""
    r, c = _runner(tmp_path, monkeypatch, client=LeakyAlpaca())
    r.risk.residual_frac = frac
    q = _three_filled(r, c)
    c.part_fill("mcf-B-XYZ-20261013-1000", 12.0, q["B"] - round(q["B"] * left))
    r.reconcile(DAY)
    r._sync_open()
    return r, c, q


def test_residual_lot_below_quarter_frees_a_lot_cap_slot(tmp_path, monkeypatch):
    r, c, q = _residual_setup(tmp_path, monkeypatch, left=0.20)      # 20% < 25%
    assert q["B"] >= 20 and r.risk.state.residual == {"XYZ": 1}
    _enter(r, "D")
    assert "D" in _setups(r) and len(c.orders) == 4                  # 4 lots on XYZ, one of them a residual
    _enter(r, "E")
    assert _skips(r)["E"][0] == "lot cap"                             # 3 full lots again: capped
    _enter(r, "S", side=-1, stop=11.0, target=9.0)
    assert _skips(r)["S"][0] == "opposite side held"                 # a residual still blocks the opposite side
    assert r.risk.open_lots() == 4                                    # and still uses a slot


def test_residual_at_or_above_quarter_still_counts(tmp_path, monkeypatch):
    r, c, _ = _residual_setup(tmp_path, monkeypatch, left=0.30)      # 30%
    assert r.risk.state.residual == {}
    _enter(r, "D")
    assert _skips(r)["D"][0] == "lot cap"


def test_residual_rule_off_when_frac_zero(tmp_path, monkeypatch):
    r, c, _ = _residual_setup(tmp_path, monkeypatch, left=0.20, frac=0.0)
    _enter(r, "D")
    assert _skips(r)["D"][0] == "lot cap"
