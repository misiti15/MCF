import numpy as np
import pandas as pd
import pytest

from mcf.analytics.metrics import breakdowns, summarize
from mcf.backtest.engine import Backtester, Costs, simulate
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
    mk = lambda adv, atr=1.0: SimpleNamespace(prev_close=20.0, atr=atr, avg_dollar_volume=adv)
    core, ext, thin = mk(u["min_avg_dollar_volume"] * 2), mk(u["extended_min_avg_dollar_volume"] * 2), mk(1.0)
    assert universe_ok(core, cfg) and universe_ok(ext, cfg) and not universe_ok(thin, cfg)
    assert not universe_ok(mk(core.avg_dollar_volume, atr=0.05), cfg)  # T-bill-like: no movement
    ctxs, orv = in_play_filter([core, ext, ext], [0.5, 1.0, u["extended_min_rvol"]], cfg)
    assert ctxs == [core, ext] and orv == [0.5, u["extended_min_rvol"]]
