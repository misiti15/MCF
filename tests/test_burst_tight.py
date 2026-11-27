"""AV50 burst tight stop (owner ETF-STOP50 yes 2026-11-24, variant AV50; skeptic cleared 2026-11-27; effective session
2026-11-30; mcf/burst_tight.py). Burst count by decision bar (never wall clock), the SPY-below-VWAP gate, the tight
bracket stop with shares and R on the ORIGINAL stop, the shadow book's of_live lots, and the scope: Primary's
NM-ETF-late-dip-di-long only. Educational only - not financial advice."""
import json
import os
from types import SimpleNamespace as NS

import numpy as np
import pandas as pd
import pytest

from mcf import burst_tight as BT
from mcf.config import load_config
from mcf.execution import runner as R
from mcf.strategies.base import Signal

from test_lots import FakeAlpaca, _runner

NY = "America/New_York"
DAY = "2026-10-13"
SETUP = "NM-ETF-late-dip-di-long"
ON = {"enabled": True, "stop_frac": 0.5, "burst_k": 4, "burst_window_min": 10, "index_gate": "spy_below_vwap",
      "spy_max_stale_min": 3}


def T(hhmm, s=0):
    return pd.Timestamp(f"{DAY} {hhmm[:2]}:{hhmm[2:]}:{s:02d}", tz=NY)


# ------------------------------------------------------------------------------------------------ the rule
def test_settings_default_off_and_validation():
    assert BT.settings({}) is None and BT.settings({"burst_tight_stop": {"enabled": False}}) is None
    s = BT.settings({"burst_tight_stop": {"enabled": True}})
    assert s == {"stop_frac": 0.5, "burst_k": 4, "burst_window_min": 10.0, "index_gate": "spy_below_vwap",
                 "spy_max_stale_min": 3.0}
    with pytest.raises(ValueError):
        BT.settings({"burst_tight_stop": {"enabled": True, "index_gate": "spy_below_open"}})
    with pytest.raises(ValueError):
        BT.settings({"burst_tight_stop": {"enabled": True, "stop_frac": 1.0}})


def test_decision_time_is_the_end_of_the_5min_bucket():
    assert BT.decision_time(T("1404")) == T("1405")
    assert BT.decision_time(T("1406")) == T("1405")      # bucket 14:00 missed its 4th minute: decided by 14:06
    assert BT.decision_time(T("1409")) == T("1410")
    assert BT.decision_time(T("1354")) == T("1355")


def test_burst_count_by_decision_bar_not_wall_clock():
    """A counts lots with decision time in (m - 10, m): on the 5-minute grid only bar m-5."""
    m = T("1405")
    booked = [T("1350"), T("1355"), T("1400"), T("1400"), T("1405")]
    assert BT.booked_before(booked, m, 10) == 2            # 13:55 (= m-10) and 14:05 (= m) are out
    s = BT.settings({"burst_tight_stop": ON})
    spy_dn = _spy(below=True)
    tight, tag = BT.decide(s, 10.0, 9.0, m, prior=2, n_now=2, spy=spy_dn)
    assert tight == pytest.approx(9.5) and tag["burst_tight"] and tag["burst_count"] == 4 and tag["stop_tight"] == 9.5
    tight, tag = BT.decide(s, 10.0, 9.0, m, prior=2, n_now=1, spy=spy_dn)
    assert tight is None and tag == {"burst_tight": False, "burst_count": 3, "burst_decision": "14:05",
                                     "spy_vs_vwap": None}
    assert BT.decide(s, 10.0, 9.0, m, prior=0, n_now=0, spy=spy_dn)[1]["burst_count"] == 1   # the lot itself counts


def _spy(below=True, last="1404", stale_min=0, start="0930"):
    """SPY 1-minute bars start .. last (- stale_min): flat at 600 with volume, the last 30 bars at 598 (below VWAP)
    or 602 (above)."""
    idx = pd.date_range(T(start), T(last) - pd.Timedelta(minutes=stale_min), freq="1min")
    c = np.full(len(idx), 600.0)
    c[-30:] = 598.0 if below else 602.0
    return pd.DataFrame({"open": c, "high": c + 0.1, "low": c - 0.1, "close": c, "volume": 1e6}, index=idx)


def test_spy_gate_below_vwap_point_in_time_and_stale():
    m = T("1405")
    c, vw = BT.spy_vs_vwap(_spy(True), m, 3)
    assert c == 598.0 and c < vw
    c, vw = BT.spy_vs_vwap(_spy(False), m, 3)
    assert c == 602.0 and c > vw
    # only bars before m: a later SPY bar (14:05, above) is never read
    late = pd.concat([_spy(True), _spy(False, last="1410").loc[T("1405"):]])
    assert BT.spy_vs_vwap(late, m, 3)[0] == 598.0
    # VWAP from 09:30 regular hours only (a pre-market bar is ignored)
    pre = pd.concat([pd.DataFrame({"open": [900.0], "high": [900.0], "low": [900.0], "close": [900.0], "volume": [1e9]},
                                  index=[T("0900")]), _spy(True)])
    assert BT.spy_vs_vwap(pre, m, 3) == BT.spy_vs_vwap(_spy(True), m, 3)
    assert BT.spy_vs_vwap(_spy(True, stale_min=3), m, 3) is not None     # last bar 14:01: 3 minutes older than m-1
    assert BT.spy_vs_vwap(_spy(True, stale_min=4), m, 3) is None         # 4 minutes: stale -> gate false
    assert BT.spy_vs_vwap(None, m, 3) is None and BT.spy_vs_vwap(_spy(True).iloc[:0], m, 3) is None
    s = BT.settings({"burst_tight_stop": ON})
    assert BT.decide(s, 10.0, 9.0, m, 3, 1, _spy(True, stale_min=4))[0] is None   # burst, SPY stale: normal stop
    assert BT.decide(s, 10.0, 9.0, m, 3, 1, _spy(False))[0] is None             # burst, SPY above VWAP: normal stop


def test_tight_stop_both_sides():
    assert BT.tight_stop(10.0, 9.0, 0.5) == pytest.approx(9.5)
    assert BT.tight_stop(10.0, 11.0, 0.5) == pytest.approx(10.5)


# ------------------------------------------------------------------------------------------------ live runner
class Fires:
    """A lab-like setup: a market long on the latest bar when its decision bar (HHMM) is in `at`; stop 9, target 10.5."""

    def __init__(self, name=SETUP, at=(), bt=ON):
        self.name, self.at = name, set(at)
        self.params = {"burst_tight_stop": dict(bt)} if bt else {}
        self.calls = 0

    def eligible(self, ctx):
        return True

    def signals(self, ctx):
        self.calls += 1
        last = len(ctx.bars) - 1
        if f"{ctx.bars.index[last]:%H%M}" not in self.at:
            return []
        return [Signal(ctx.symbol, self.name, 1, last, stop=9.0, target=10.5)]


def _bars_to(now):
    idx = pd.date_range(T("0930"), now.floor("1min") - pd.Timedelta(minutes=1), freq="1min")
    return pd.DataFrame({"open": 10.0, "high": 10.02, "low": 9.98, "close": 10.0, "volume": 1e5}, index=idx)


def _poll(r, monkeypatch, now, syms, spy):
    bars = {s: _bars_to(now) for s in syms}
    seen = {**bars, **({"SPY": spy} if spy is not None else {})}
    monkeypatch.setattr(r, "fetch", lambda now: seen)
    monkeypatch.setattr(r, "_contexts", lambda b, today: [NS(symbol=s, bars=bars[s], avg_dollar_volume=5e8)
                                                          for s in syms])
    r.step(now)
    r._sync_open()


def _stops(c):
    """entry coid -> broker stop-leg price."""
    return {o.client_order_id: float(next(l.stop_price for l in o.legs if l.order_type == "stop"))
            for o in c.orders if o.legs}


def _sub(r):
    s = r.journal.signals(r.run_id)
    s = s[s.status == "submitted"]
    return {x.symbol: (x.stop, json.loads(x.info)) for x in s.itertuples()}


def test_runner_spy_on_watchlist_only_when_enabled(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch, strategies=[Fires(at={"1404"})])
    assert r.burst_tight and "SPY" in r.watchlist
    r2, _ = _runner(tmp_path, monkeypatch, strategies=[Fires(at={"1404"}, bt=None)], journal="j2.db")
    assert not r2.burst_tight and "SPY" not in r2.watchlist


def test_runner_four_signals_one_bar_tight_stops_sized_on_original(tmp_path, monkeypatch):
    st = Fires(at={"1404"})
    r, c = _runner(tmp_path, monkeypatch, strategies=[st])
    syms = ["AAA", "BBB", "CCC", "DDD"]
    _poll(r, monkeypatch, T("1405", 5), syms, _spy(True))
    stops = _stops(c)
    assert len(stops) == 4 and set(stops.values()) == {9.5}           # bracket stop = 10 - 0.5 x (10 - 9)
    sub = _sub(r)
    for sym in syms:
        stop, info = sub[sym]
        assert stop == 9.0                                             # journal stop = the original (R basis)
        assert info["burst_tight"] is True and info["burst_count"] == 4 and info["stop_tight"] == 9.5
        assert info["spy_vs_vwap"] < 0 and info["burst_decision"] == "14:05"
    # sized from the ORIGINAL stop: same qty as a normal lot of the same signal
    r2, c2 = _runner(tmp_path, monkeypatch, strategies=[Fires(at={"1404"}, bt=None)], journal="j2.db")
    _poll(r2, monkeypatch, T("1405", 5), syms, _spy(True))
    assert sorted(float(o.qty) for o in c.orders) == sorted(float(o.qty) for o in c2.orders)
    assert set(_stops(c2).values()) == {9.0}
    assert st.calls == 4                                               # the B pre-count reuses its signals


def test_runner_three_signals_no_burst_and_gate_off_keep_normal_stop(tmp_path, monkeypatch):
    r, c = _runner(tmp_path, monkeypatch, strategies=[Fires(at={"1404"})])
    _poll(r, monkeypatch, T("1405", 5), ["AAA", "BBB", "CCC"], _spy(True))
    assert set(_stops(c).values()) == {9.0}
    assert {i["burst_count"] for _, i in _sub(r).values()} == {3}
    assert not any(i["burst_tight"] for _, i in _sub(r).values())
    for spy in (_spy(False), None, _spy(True, stale_min=5)):           # above VWAP / missing / stale SPY
        r, c = _runner(tmp_path, monkeypatch, strategies=[Fires(at={"1404"})], journal=f"j{id(spy)}.db")
        _poll(r, monkeypatch, T("1405", 5), ["AAA", "BBB", "CCC", "DDD"], spy)
        assert len(_stops(c)) == 4 and set(_stops(c).values()) == {9.0}


def test_runner_burst_window_counts_bars_not_wall_clock(tmp_path, monkeypatch):
    """Lots of bar m-10 never count, even when they entered (wall clock) within 10 minutes; lots of bar m-5 do."""
    st = Fires(at={"1354", "1359", "1404"})
    r, c = _runner(tmp_path, monkeypatch, strategies=[st])
    _poll(r, monkeypatch, T("1355", 40), ["AAA", "BBB"], _spy(True, last="1354"))   # decision 13:55, entered 13:55:40
    _poll(r, monkeypatch, T("1405", 5), ["CCC", "DDD"], _spy(True))                 # 14:05:05: 9m25s later (wall clock)
    assert len(_stops(c)) == 4 and len(r._burst[SETUP]) == 4                       # BRAKE-BURST's wall clock sees all 4
    assert r._burst_count(SETUP, T("1405", 5)) == 4
    sub = _sub(r)
    assert sub["CCC"][1]["burst_count"] == 2 and not sub["CCC"][1]["burst_tight"]
    assert set(_stops(c).values()) == {9.0}
    # bar m-5 counts: 2 lots at 14:00 + 2 signals at 14:05 = 4
    r, c = _runner(tmp_path, monkeypatch, strategies=[Fires(at={"1359", "1404"})], journal="j2.db")
    _poll(r, monkeypatch, T("1400", 5), ["AAA", "BBB"], _spy(True, last="1359"))
    _poll(r, monkeypatch, T("1405", 5), ["CCC", "DDD"], _spy(True))
    st2 = _stops(c)
    assert st2["mcf-%s-AAA-20261013-1359" % SETUP] == 9.0 and st2["mcf-%s-CCC-20261013-1404" % SETUP] == 9.5
    assert _sub(r)["DDD"][1]["burst_count"] == 4
    # restart: A is rebuilt from today's entries (client ids carry the decision bar)
    r3 = R.PaperRunner(r.cfg, [Fires(at={"1404"})], {}, broker=r.broker, dry_run=True)
    r3.restore(pd.Timestamp(DAY).date())
    assert len(r3._bt_booked(SETUP, pd.Timestamp(DAY).date())) == 4


def test_runner_rule_applies_only_to_the_setup_with_it(tmp_path, monkeypatch):
    nm, other = Fires(at={"1404"}), Fires(name="OTHER", at={"1404"}, bt=None)
    r, c = _runner(tmp_path, monkeypatch, strategies=[nm, other])
    _poll(r, monkeypatch, T("1405", 5), ["AAA", "BBB", "CCC", "DDD"], _spy(True))
    st = _stops(c)
    assert {v for k, v in st.items() if f"-{SETUP}-" in k} == {9.5}
    assert {v for k, v in st.items() if "-OTHER-" in k} == {9.0}
    info = {(x.strategy, x.symbol): json.loads(x.info) for x in r.journal.signals(r.run_id).itertuples()}
    assert all("burst_tight" not in i for (s, _), i in info.items() if s == "OTHER")


def test_runner_r_stays_in_original_risk_units(tmp_path, monkeypatch):
    """A tight lot stopped at 9.50 books -0.5R (risk = entry - ORIGINAL stop), never -1R."""
    r, c = _runner(tmp_path, monkeypatch, strategies=[Fires(at={"1404"})])
    _poll(r, monkeypatch, T("1405", 5), ["AAA", "BBB", "CCC", "DDD"], _spy(True))
    coid = f"mcf-{SETUP}-AAA-20261013-1404"
    c.fill(coid, 10.0)
    c.hit(coid, "stop", 9.5)
    r.reconcile(pd.Timestamp(DAY).date())
    t = r.journal.trades(run_id=r.run_id)
    assert len(t) == 1 and t.iloc[0].exit_reason == "stop"
    assert t.iloc[0].stop == pytest.approx(9.0)
    assert t.iloc[0].r_multiple == pytest.approx(-0.5, abs=0.01)
    o = r.journal.open_orders(r.run_id)
    assert set(o.stop.round(2)) == {9.0}                               # the orders' R basis too


# ------------------------------------------------------------------------------------------------ shadow book
class _Broker:
    def __init__(self):
        self.stops = {}

    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):
        return {}

    def submit_bracket(self, sig, qty, coid):
        self.stops[coid] = sig.stop
        return NS(id=f"o{len(self.stops)}")

    def __getattr__(self, name):
        raise AttributeError(name)


def test_shadow_of_live_lots_get_the_tight_stop_and_keep_r_basis(tmp_path, monkeypatch):
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["shadow"] = {"enabled": True, "of_live": True, "budget_frac": 0.10, "latency_bps": 0.0}
    cfg["shadow_setups"] = []
    r = R.PaperRunner(cfg, [Fires(at={"1404"})], {}, broker=_Broker())
    r.restore(pd.Timestamp(DAY).date())
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px, quote=None: (True, "ok", {}))
    monkeypatch.setattr(r, "_quote", lambda sym: (9.99, 10.01))
    monkeypatch.setattr(r.shadow, "fetch_quotes", lambda syms: {s: (9.99, 10.01, None) for s in syms})
    monkeypatch.setattr(r, "_check_data", lambda now, bars: False)
    _poll(r, monkeypatch, T("1405", 5), ["AAA", "BBB", "CCC", "DDD"], _spy(True))
    assert set(r.broker.stops.values()) == {9.5}
    lots = list(r.shadow.lots.values())
    assert len(lots) == 4 and {l["stop"] for l in lots} == {9.5} and {l["stop0"] for l in lots} == {9.0}


# ------------------------------------------------------------------------------------------------ scope (config)
def test_config_primary_nmetf_only(monkeypatch):
    """Owner ETF-STOP50 / AV50: Primary's NM-ETF-late-dip-di-long only; no other setup in any account, BASE1 frozen."""
    for acct in ("primary", "testing", "testing2", "livelab", "explore1", "graveyard", "gen", "testingd",
                 "testinge", "testingf"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        cfg = load_config()
        on = sorted(k for k, v in (cfg.get("strategies") or {}).items()
                    if isinstance(v, dict) and v.get("enabled", True) and BT.settings(v))
        assert on == ([SETUP] if acct == "primary" else []), acct
        if acct == "primary":
            assert BT.settings(cfg["strategies"][SETUP]) == {**{k: v for k, v in ON.items() if k != "enabled"},
                                                             "burst_window_min": 10.0, "spy_max_stale_min": 3.0}
            assert BT.KEY not in cfg["baseline"]["setups"][SETUP]   # BASE1 is the frozen control (never edited)
