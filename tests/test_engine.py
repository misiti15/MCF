import numpy as np
import pandas as pd
import pytest

from mcf.analytics.metrics import breakdowns, summarize
from mcf.backtest.engine import Backtester, Costs, SymbolHistory, simulate
from mcf.config import load_config
from mcf.data.bars import TZ
from mcf.data.synthetic import make_universe
from mcf.strategies.base import Signal
from mcf.strategies.setups import REGISTRY, build_strategies


def day_bars(prices, start="2025-03-03 09:30"):
    idx = pd.date_range(start, periods=len(prices), freq="1min", tz=TZ)
    p = np.asarray(prices, float)
    o = np.concatenate([[p[0]], p[:-1]])
    return pd.DataFrame({"open": o, "high": np.maximum(o, p) + 0.01, "low": np.minimum(o, p) - 0.01,
                         "close": p, "volume": 1000.0}, index=idx)


FLAT = pd.Timestamp("15:55").time()


def test_market_entry_next_bar_and_target():
    bars = day_bars([100, 100, 101, 102, 103, 104])
    sig = Signal("X", "t", 1, bar_index=0, stop=99.0, target=102.5)
    tr = simulate(sig, bars, FLAT, 0.0)
    assert tr.entry == 100  # next bar open
    assert tr.exit_reason == "target" and tr.exit == 102.5
    assert tr.r_multiple == pytest.approx(2.5)


def test_stop_first_when_both_in_bar():
    bars = day_bars([100, 100, 100])
    bars.iloc[2, bars.columns.get_loc("high")] = 105
    bars.iloc[2, bars.columns.get_loc("low")] = 95
    tr = simulate(Signal("X", "t", 1, 0, stop=99, target=104), bars, FLAT, 0.0)
    assert tr.exit_reason == "stop" and tr.r_multiple == pytest.approx(-1)


def test_stop_entry_and_short():
    bars = day_bars([100, 99.5, 99, 98, 97, 96])
    sig = Signal("X", "t", -1, 0, stop=100.5, entry_type="stop", entry_price=99.2)
    tr = simulate(sig, bars, FLAT, 0.0)
    assert tr.entry == pytest.approx(99.2)
    assert tr.exit_reason == "eod" and tr.r_multiple > 0


def test_costs_reduce_r():
    bars = day_bars([100, 100, 101, 102, 103, 104])
    sig = Signal("X", "t", 1, 0, stop=99.0, target=102.5)
    free = simulate(sig, bars, FLAT, Costs(0, 0, 0))
    paid = simulate(sig, bars, FLAT, Costs(2, 0.01, 0.02))
    assert paid.r_multiple < free.r_multiple


def test_time_exit():
    bars = day_bars([100] * 10, start="2025-03-03 15:50")
    tr = simulate(Signal("X", "t", 1, 0, stop=99), bars, FLAT, 0.0)
    assert tr.exit_reason == "time" and str(tr.exit_time.time()) == "15:55:00"


def test_full_backtest_runs_and_no_lookahead():
    cfg = load_config()
    cfg["universe"]["min_avg_dollar_volume"] = 0
    for s in cfg["strategies"].values():
        s["enabled"] = True
    data = make_universe(["SPY", "QQQ", "AAA", "BBB", "CCC", "DDD"], days=40)
    trades = Backtester(build_strategies(cfg), cfg).run(data)
    assert not trades.empty
    assert (pd.to_datetime(trades.entry_time) >= pd.to_datetime(trades.signal_time)).all()
    assert (pd.to_datetime(trades.exit_time) >= pd.to_datetime(trades.entry_time)).all()
    assert (pd.to_datetime(trades.exit_time).dt.time <= pd.Timestamp("15:55").time()).all()
    s = summarize(trades)
    assert 0 <= s["win_rate"] <= 1 and s["trades"] == len(trades)
    assert "strategy" in breakdowns(trades)
    # prior-day stats only: truncating future days must not change earlier trades
    cut = {k: v[v.index < v.index[0] + pd.Timedelta(days=30)] for k, v in data.items()}
    early = Backtester(build_strategies(cfg), cfg).run(cut)
    later = trades[pd.to_datetime(trades.date) <= pd.to_datetime(early.date).max()]
    key = ["symbol", "strategy", "entry_time"]
    assert set(map(tuple, early[key].astype(str).values)) <= set(map(tuple, later[key].astype(str).values))


def test_registry_complete():
    assert {"orb", "noise_band_momentum", "intraday_momentum"} <= set(REGISTRY)


def test_marcoflow_client_blocks_action_endpoints():
    from mcf import marcoflow

    for bad in ("/api/agent/tick", "/api/paper/tick", "/api/agent/heartbeat", "/api/agent/daily-brief"):
        with pytest.raises(PermissionError):
            marcoflow.get(bad)
    with pytest.raises(PermissionError):
        marcoflow.get("/api/observations", key="x")


def test_scale_out_then_breakeven_is_a_small_win():
    # entry 100 at bar1, risk 1 (stop 99). Rally to 101 (=1R) -> half off, stop to 100, then fall back
    bars = day_bars([100, 100, 100.6, 101.2, 100.5, 99.5, 99.0])
    sig = Signal("X", "t", 1, 0, stop=99.0, scale_out_r=1.0, scale_out_frac=0.5)
    tr = simulate(sig, bars, FLAT, 0.0)
    assert tr.exit_reason == "scaled+breakeven"
    assert tr.r_multiple == pytest.approx(0.5)


def test_scale_out_keeps_runner():
    bars = day_bars([100, 100, 101.5, 103, 104, 105])
    sig = Signal("X", "t", 1, 0, stop=99.0, target=104.0, scale_out_r=1.0)
    tr = simulate(sig, bars, FLAT, 0.0)
    assert tr.exit_reason == "scaled+target"
    assert tr.r_multiple == pytest.approx(0.5 * 1 + 0.5 * 4)


def test_success_is_first_touch_independent_of_exit():
    # long, risk 1: price goes +1R first, then collapses through the stop -> trade loses, signal succeeded
    bars = day_bars([100, 100, 101.2, 100.2, 98.5, 98.0])
    tr = simulate(Signal("X", "t", 1, 0, stop=99.0), bars, FLAT, 0.0)
    assert tr.r_multiple < 0 and tr.success == 1
    bars = day_bars([100, 100, 99.5, 98.8, 101.5, 102])
    tr = simulate(Signal("X", "t", 1, 0, stop=98.0), bars, FLAT, 0.0)   # risk 2: -1R = 98 not hit, +1R = 102 hit
    assert tr.success == 1
    tr = simulate(Signal("X", "t", 1, 0, stop=99.0), day_bars([100, 100, 99.5, 98.9, 101.5]), FLAT, 0.0)
    assert tr.success == 0


def test_gate_requires_sustained_months():
    from mcf.analytics.metrics import gate_check

    gates = {"min_months": 3, "min_positive_month_rate": 0.67}
    # one big month carries three losing ones: totals look fine, sustainability fails
    dates = ["2026-01-05"] * 10 + ["2026-02-05", "2026-03-05", "2026-04-05"]
    r = [3.0] * 10 + [-1.0] * 3
    tr = pd.DataFrame({"date": dates, "r_multiple": r, "pnl": [x * 100 for x in r]})
    s = summarize(tr)
    assert s["months"] == 4 and s["positive_month_rate"] == 0.25
    ok, fails = gate_check(s, gates)
    assert not ok and any("positive months" in f for f in fails)


def test_extended_tier_only_when_in_play():
    from types import SimpleNamespace

    from mcf.backtest.engine import in_play_filter, universe_ok

    cfg = load_config()
    u = cfg["universe"]
    mk = lambda adv, atr=1.0: SimpleNamespace(symbol="XYZ", prev_close=20.0, atr=atr, avg_dollar_volume=adv)
    core, ext, thin = mk(u["min_avg_dollar_volume"] * 2), mk(u["extended_min_avg_dollar_volume"] * 2), mk(1.0)
    assert universe_ok(core, cfg) and universe_ok(ext, cfg) and not universe_ok(thin, cfg)
    assert not universe_ok(mk(core.avg_dollar_volume, atr=0.05), cfg)  # T-bill-like: no movement
    ctxs, orv = in_play_filter([core, ext, ext], [0.5, 1.0, u["extended_min_rvol"]], cfg)
    assert ctxs == [core, ext] and orv == [0.5, u["extended_min_rvol"]]


def test_job_window():
    from mcf.execution.session import job_deadline

    live = {"start_from": "08:00", "max_job_minutes": 340}
    ts = lambda s: pd.Timestamp(s, tz="America/New_York")
    assert job_deadline(ts("2026-10-06 07:35"), live) is None          # too early (EST-only cron line)
    assert job_deadline(ts("2026-10-06 08:35"), live) == ts("2026-10-06 14:15")
    assert job_deadline(ts("2026-10-06 16:15"), live) is None          # after the session
    assert job_deadline(ts("2026-10-10 10:00"), live) is None          # Saturday


def test_rule_strategy_matches_layer_definition():
    from mcf.data.bars import resample
    from mcf.layers import layer_frame, rule_mask
    from mcf.strategies.setups import RuleStrategy

    cfg = load_config()
    cfg["universe"]["min_avg_dollar_volume"] = 0
    data = make_universe(["AAA"], days=30)
    hist = SymbolHistory("AAA", data["AAA"])
    day = sorted(hist.by_day)[-1]
    ctx = hist.context(day)
    layers = ["above VWAP", "within 2% of open"]
    sigs = RuleStrategy("rule_t", layers, "long").generate(ctx)
    d5 = resample(ctx.bars, "5min")
    rv = ctx.rvol().to_numpy()[[min(ctx.bars.index.searchsorted(x + pd.Timedelta(minutes=4)), len(ctx.bars) - 1) for x in d5.index]]
    hits = np.flatnonzero(rule_mask(layer_frame(d5, ctx.prior5, ctx.prev_close, rv), layers))
    if len(hits):
        assert sigs and ctx.bars.index[sigs[0].bar_index] == d5.index[hits[0]] + pd.Timedelta(minutes=4)
        assert sigs[0].stop < ctx.bars["close"].iloc[sigs[0].bar_index]
    else:
        assert not sigs


def test_discovery_mines_synthetic():
    from mcf.data.bars import resample
    from mcf.discovery import build_frame, mine, wilson_lb

    cfg = load_config()
    cfg["discovery"].update(min_train=20, min_test=5, max_layers=2)
    data = {s: resample(df, "5min") for s, df in make_universe(["AAA", "BBB", "CCC"], days=40).items()}
    x = build_frame(data, cfg, log=lambda *_: None)
    assert len(x) and {"succ_long", "r_short", "rsi", "rvol"} <= set(x.columns)
    assert x.tod.min() >= 950                       # owner's 9:30-9:50 caution respected
    res, meta = mine(x, cfg)
    assert meta["rules_tried"] > 0
    assert 0 <= wilson_lb(5, 10) < 0.5


def test_pinned_symbols_bypass_universe_filters():
    from types import SimpleNamespace

    from mcf.backtest.engine import pinned_symbols, universe_ok

    cfg = load_config()
    assert {"SPY", "QQQ"} <= pinned_symbols(cfg)
    spy = SimpleNamespace(symbol="SPY", prev_close=770.0, atr=7.2, avg_dollar_volume=3e10)   # ATR 0.93% < 1%
    other = SimpleNamespace(symbol="XYZ", prev_close=770.0, atr=7.2, avg_dollar_volume=3e10)
    assert universe_ok(spy, cfg) and not universe_ok(other, cfg)


def test_daily_review_compares_days(tmp_path):
    from mcf.journal import Journal
    from mcf.report.daily_review import build_review, to_markdown

    j = Journal(tmp_path / "j.db")
    rid = j.get_or_create_run("paper", "MCF Update (live paper)")
    row = dict(symbol="AAA", strategy="orb", side=1, signal_time="2026-10-05T10:00:00-04:00",
               entry_time="2026-10-05T10:01:00-04:00", entry=10.0, stop=9.9, target=None,
               exit_time="2026-10-05T15:55:00-04:00", exit=10.2, exit_reason="flatten", mae_r=None, mfe_r=None,
               success=1, shares=100, meta="", slip_bps=4.0, pnl_adj=20.0)
    j.add_trades(rid, pd.DataFrame([{**row, "date": "2026-10-05", "r_multiple": 2.0, "pnl": 20.0},
                                    {**row, "date": "2026-10-06", "r_multiple": -1.0, "pnl": -10.0, "slip_bps": 25.0}]))
    rv = build_review(j, rid, "2026-10-06")
    assert rv["today"]["trades"] == 1 and rv["yesterday"]["exp_r"] == 2.0
    assert rv["beat_rolling5"]["exp_r"] is False
    assert any("slippage" in f for f in rv["findings"])
    assert "daily review" in to_markdown(rv)


def test_heat_strategy_runs_on_context():
    from mcf.strategies.setups import HeatStrategy

    data = make_universe(["AAA"], days=30)
    hist = SymbolHistory("AAA", data["AAA"])
    ctx = hist.context(sorted(hist.by_day)[-1])
    st = HeatStrategy("heat_original", "research/heat/candidates/_original.py")
    for s in st.generate(ctx):
        assert s.side in (1, -1) and (s.stop < s.target if s.side == 1 else s.stop > s.target)


def test_research_setups_run_in_backtester():
    cfg = load_config()
    cfg["universe"]["min_avg_dollar_volume"] = 0
    research = ["orb20_a", "orb20_b", "gap_continuation", "gap_sma20", "index_gap_fill", "close_momentum",
                "eod_reversal", "vwap_pullback"]
    for name, st in cfg["strategies"].items():
        st["enabled"] = name in research
    strats = build_strategies(cfg)
    assert sorted(s.name for s in strats) == sorted(research)
    data = make_universe(["SPY", "QQQ", "AAA", "BBB", "CCC"], days=40)
    trades = Backtester(strats, cfg).run(data)
    if len(trades):
        et = pd.to_datetime(trades.entry_time)
        assert (et.dt.time >= pd.Timestamp("09:50").time()).all()   # every research setup respects 09:50


def test_setup_freeze_ignores_intraday_edits(tmp_path):
    from mcf.execution.session import freeze_setups

    now = pd.Timestamp("2026-10-07 09:00", tz="America/New_York")
    cfg = load_config()
    assert "snapshot written" in freeze_setups(cfg, tmp_path, now)
    edited = load_config()
    edited["strategies"]["orb"]["enabled"] = not cfg["strategies"]["orb"]["enabled"]
    note = freeze_setups(edited, tmp_path, now.replace(hour=13))
    assert "ignoring intraday edits to: strategies" in note
    assert edited["strategies"]["orb"]["enabled"] == cfg["strategies"]["orb"]["enabled"]


def test_restore_from_broker_recovers_unsaved_orders(tmp_path):
    from types import SimpleNamespace

    from mcf.execution.runner import PaperRunner

    leg = SimpleNamespace(stop_price=99.0, limit_price=None)
    order = SimpleNamespace(client_order_id="mcf-heat_fade_short-AMD-20261006", id="abc", side="sell", qty="3",
                            filled_avg_price="100.0", legs=[leg])
    broker = SimpleNamespace(orders_today_with_prefix=lambda p, a: [order], positions=lambda: {"AMD": object()},
                             equity=lambda: 100000.0)
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    r = PaperRunner(cfg, [], {}, broker=broker)
    r.restore(pd.Timestamp("2026-10-06").date())
    assert ("AMD", "heat_fade_short") in r.fired and r.open_strategy["AMD"] == "heat_fade_short"
    assert "AMD" in r.risk.state.open_symbols
    assert r.journal.open_orders(r.run_id).broker_order_id.tolist() == ["abc"]


def test_eod_report_top_losers_and_chart(tmp_path):
    from mcf.journal import Journal
    from mcf.report import eod

    j = Journal(tmp_path / "j.db")
    rid = j.get_or_create_run("paper", "MCF Update (live paper)")
    base = dict(strategy="orb20_a", date="2026-10-06", signal_time="2026-10-06T10:00:00-04:00", stop=9.0, target=None,
                exit_reason="stop", mae_r=None, mfe_r=None, success=0, shares=10, meta="")
    rows = [dict(base, symbol=f"S{i}", side=1, entry_time="2026-10-06T10:01:00-04:00", entry=10.0,
                 exit_time=f"2026-10-06T1{1 + i % 4}:05:00-04:00", exit=10.0 - 0.1 * i, r_multiple=-0.1 * i,
                 pnl=-1.0 * i) for i in range(12)]
    j.add_trades(rid, pd.DataFrame(rows))
    idx = pd.date_range("2026-10-06 09:30", "2026-10-06 15:59", freq="1min", tz="America/New_York")
    spy = pd.DataFrame({"close": np.linspace(700, 705, len(idx))}, index=idx)
    rep = eod.build(j, rid, "2026-10-06", spy, {"findings": ["x"]})
    assert rep["png"][:4] == b"\x89PNG" and rep["html"].count("<tr><td>S") == 10
    assert "S11" in rep["html"] and "S1<" not in rep["html"]   # worst 10 by % lost, best losers dropped
    eod.save(rep, tmp_path / "reports", "2026-10-06")
    assert (tmp_path / "reports" / "2026-10-06.csv").exists()


def _path_bars(prices):
    idx = pd.date_range("2026-10-06 10:00", periods=len(prices), freq="1min", tz="America/New_York")
    p = np.array(prices, dtype=float)
    return pd.DataFrame({"open": p, "high": p + 0.05, "low": p - 0.05, "close": p, "volume": 1000.0}, index=idx)


def test_time_stop_cuts_trades_that_never_work():
    bars = _path_bars([100.0] * 60)
    sig = Signal("X", "t", 1, 0, stop=99.0, time_stop_min=20, time_stop_min_r=0.3)
    tr = simulate(sig, bars, pd.Timestamp("15:55").time(), 0.0)
    assert tr.exit_reason == "timestop" and abs(tr.r_multiple) < 0.1


def test_breakeven_and_trail_protect_winners():
    up_then_down = [100 + 0.1 * i for i in range(30)] + [103 - 0.2 * i for i in range(30)]
    bars = _path_bars(up_then_down)
    plain = simulate(Signal("X", "t", 1, 0, stop=99.0), bars, pd.Timestamp("15:55").time(), 0.0)
    trailed = simulate(Signal("X", "t", 1, 0, stop=99.0, trail_r=1.0, trail_after_r=1.0), bars, pd.Timestamp("15:55").time(), 0.0)
    be = simulate(Signal("X", "t", 1, 0, stop=99.0, be_at_r=1.0), bars, pd.Timestamp("15:55").time(), 0.0)
    assert trailed.r_multiple > plain.r_multiple and trailed.exit_reason == "trail"
    assert be.r_multiple > -0.2 > plain.r_multiple   # gap through the breakeven stop fills at the open


def test_runner_manage_time_stop_and_trail(tmp_path):
    from types import SimpleNamespace

    from mcf.execution.runner import PaperRunner

    calls = []
    broker = SimpleNamespace(positions=lambda: {"AAA": 1, "BBB": 1}, equity=lambda: 1e5,
                             orders_today_with_prefix=lambda p, a: [],
                             close_mcf_position=lambda s, p: calls.append(("close", s)) or True,
                             move_stop=lambda s, px, p: calls.append(("move", s, px)))
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    r = PaperRunner(cfg, [], {}, broker=broker)
    t0 = pd.Timestamp("2026-10-07 10:00", tz="America/New_York")
    r.managed = {"AAA": dict(side=1, entry=100.0, risk=1.0, stop=99.0, t0=t0, be_at_r=None, trail_r=None, trail_after_r=1.0,
                             time_stop_min=30, time_stop_min_r=0.3, best=0.0),
                 "BBB": dict(side=1, entry=50.0, risk=1.0, stop=49.0, t0=t0, be_at_r=1.0, trail_r=1.0, trail_after_r=1.0,
                             time_stop_min=None, time_stop_min_r=0.0, best=0.0)}
    idx = pd.date_range(t0, periods=35, freq="1min")
    flat = pd.DataFrame({"open": 100.0, "high": 100.1, "low": 99.9, "close": 100.0, "volume": 1.0}, index=idx)
    up = pd.DataFrame({"open": 50.0, "high": np.linspace(50, 52.5, 35), "low": 49.9, "close": 50.0, "volume": 1.0}, index=idx)
    r.manage(t0 + pd.Timedelta(minutes=35), {"AAA": flat, "BBB": up})
    assert ("close", "AAA") in calls                                   # stale trade cut
    moves = [c for c in calls if c[0] == "move" and c[1] == "BBB"]
    assert moves and moves[-1][2] == 51.5                               # trail 1R behind +2.5R best


def test_lab_gap_prefilter_skips_names_that_cannot_qualify():
    from types import SimpleNamespace

    from mcf.strategies.setups import LabStrategy

    st = LabStrategy("g", "research/primitives/layering/finalists/L3-gapV1+sma20slopepctV20+rsi5hi-short-W4-t05s1.py",
                     window=[1300, 1430], prefilter="gap_le:-2.65")
    idx = pd.date_range("2026-10-07 09:30", periods=215, freq="1min", tz="America/New_York")   # last bar 13:04 -> 13:05 close
    bars = pd.DataFrame({"open": 97.0, "high": 97.5, "low": 96.5, "close": 97.0, "volume": 1000.0}, index=idx)
    down = SimpleNamespace(avg_dollar_volume=1e9, bars=bars, prev_close=100.0)
    flat = SimpleNamespace(avg_dollar_volume=1e9, bars=bars, prev_close=97.5)
    assert len(bars) % 5 == 0 and st.eligible(down) and not st.eligible(flat)
