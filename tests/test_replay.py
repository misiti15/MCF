"""Replay harness (mcf/replay): a synthetic session end-to-end through the real PaperRunner with the simulated broker;
fast path == exact path; deterministic; broker fill rules. Educational only - not financial advice."""

import numpy as np
import pandas as pd
import pytest

from mcf.data.priors import Prior
from mcf.replay import harness
from mcf.replay.broker import SimClock, SimMarket, SimTradingClient

NY = "America/New_York"
DAY = "2026-09-15"

MODULE = '''
SIDE = "{side}"
GEOM = "t1s1"
LAYERS = ["tod in (1000, 1100, 1300)"]
def mask(f):
    return f["tod"].isin([1000, 1100, 1300]).to_numpy()
'''


def _walk(seed, start=50.0, n=390, vol=0.0015):
    rng = np.random.default_rng(seed)
    c = start * np.exp(np.cumsum(rng.normal(0, vol, n)))
    o = np.r_[start, c[:-1]]
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.001, n))
    lo = np.minimum(o, c) * (1 - rng.uniform(0, 0.001, n))
    return o.round(2), h.round(2), lo.round(2), c.round(2), rng.integers(20_000, 80_000, n).astype(float)


def _session(syms=("AAA", "BBB", "CCC", "SPY")):
    idx = pd.date_range(pd.Timestamp(f"{DAY} 09:30", tz=NY), periods=390, freq="1min")
    bars, priors = {}, {}
    for i, s in enumerate(syms):
        o, h, lo, c, v = _walk(i + 1, 40.0 + 10 * i)
        b = pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "volume": v}, index=idx)
        if s == "CCC":
            b = b.drop(b.index[[100, 101, 250]])                  # a thin name: minutes without a bar
        bars[s] = b
        pidx = pd.date_range(pd.Timestamp("2026-09-14 10:55", tz=NY), periods=60, freq="5min")
        tail = pd.DataFrame({"open": o[0], "high": o[0] * 1.001, "low": o[0] * 0.999, "close": o[0],
                             "volume": 200_000.0}, index=pidx)
        priors[s] = Prior(prev_close=float(o[0]) * 0.995, prev_high=float(o[0]) * 1.01, prev_low=float(o[0]) * 0.98,
                          atr=float(o[0]) * 0.03, adv=500e6, avg_volume=5e6,
                          avg_cum=np.linspace(50_000, 20e6, 390), avg_move=None, tail5=tail, sma20=float(o[0]))
    return bars, priors


def _cfg(tmp_path, side="long"):
    mod = tmp_path / f"replay_test_{side}.py"
    mod.write_text(MODULE.format(side=side))
    cfg = harness.account_config("primary")
    cfg = harness.add_setup(cfg, "RPLTEST", str(mod), alone=True, block={"min_adv": 0, "refire": True})
    cfg["live"]["no_entry_before"] = "09:50"
    return cfg


def _key(res):
    s = res["signals"][["symbol", "strategy", "status", "reason", "bar_index"]].astype(str)
    t = res["trades"][["symbol", "strategy", "entry", "exit", "exit_reason", "r_multiple"]].round(6).astype(str)
    return s.to_csv(index=False), t.to_csv(index=False)


@pytest.mark.parametrize("side", ["long", "short"])
def test_synthetic_session_end_to_end_fast_equals_exact(tmp_path, side):
    bars, priors = _session()
    cfg = _cfg(tmp_path, side)
    shortable = {s: (True, True) for s in bars}
    fast = harness.run_session(cfg, DAY, bars, priors, shortable=shortable, check=8, log=lambda m: None)
    exact = harness.run_session(cfg, DAY, bars, priors, shortable=shortable, exact=True, log=lambda m: None)
    sig, tr = fast["signals"], fast["trades"]
    assert len(sig) >= 6, sig                                    # 3 decision bars x 4 symbols (CCC may miss a bar)
    assert set(sig.status) <= {"submitted", "skipped", "shadow"}
    assert (sig.status == "submitted").sum() >= 4
    assert len(tr) == (sig.status == "submitted").sum()         # every entry closed by 15:55 and reconciled
    assert set(tr.exit_reason) <= {"stop", "target", "flatten", "trail", "timestop"}
    assert _key(fast) == _key(exact)                            # the fast path changes speed, not decisions
    chk = fast["stats"]["fast_check"]
    assert chk["samples"] > 0 and chk["frame_diff"] == 0 and chk["mask_diff"] == 0
    # entries at the open of the bar after the decision bar, with costs against us
    t0 = tr.iloc[0]
    k = int((pd.Timestamp(t0.entry_time).tz_convert(NY) - pd.Timestamp(f"{DAY} 09:30", tz=NY)).total_seconds() // 60)
    raw = bars[t0.symbol]["open"].iloc[k] if t0.symbol != "CCC" else None
    if raw is not None:
        side_ = int(t0.side)
        assert abs(t0.entry - (raw * (1 + side_ * 1e-4) + side_ * 0.01)) < 1e-6
    assert fast["summary"].trades.sum() == len(tr)


def test_deterministic(tmp_path):
    bars, priors = _session()
    cfg = _cfg(tmp_path)
    sh = {s: (True, True) for s in bars}
    a = harness.run_session(cfg, DAY, bars, priors, shortable=sh, check=0, log=lambda m: None)
    b = harness.run_session(cfg, DAY, bars, priors, shortable=sh, check=0, log=lambda m: None)
    assert _key(a) == _key(b)


def _client(fills="costs", limit_fill="through"):
    idx = pd.date_range(pd.Timestamp(f"{DAY} 09:30", tz=NY), periods=390, freq="1min")
    b = pd.DataFrame({"open": 10.0, "high": 10.05, "low": 9.95, "close": 10.0, "volume": 1e5}, index=idx)
    b.iloc[31, [1]] = 10.50                                       # 10:01 bar touches 10.50 exactly
    b.iloc[33, [1]] = 10.52                                       # 10:03 bar trades through
    clock = SimClock(pd.Timestamp(f"{DAY} 10:00:03", tz=NY))
    c = SimTradingClient(clock, SimMarket(DAY, {"XYZ": b}), {"slippage_bps": 1.0, "slippage_per_share": 0.01,
                                                             "stop_slippage_per_share": 0.02}, fills, limit_fill)
    return c, clock


def _bracket(c, target=10.50, stop=9.00):
    from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest, StopLossRequest, TakeProfitRequest

    return c.submit_order(MarketOrderRequest(symbol="XYZ", qty=10, side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
                                             client_order_id="mcf-T-XYZ-20260915", order_class=OrderClass.BRACKET,
                                             stop_loss=StopLossRequest(stop_price=stop),
                                             take_profit=TakeProfitRequest(limit_price=target)))


def test_broker_trade_through_vs_touch():
    c, clock = _client("costs", "through")
    o = _bracket(c)
    assert o.status == "filled" and abs(float(o.filled_avg_price) - (10.0 * 1.0001 + 0.01)) < 1e-9
    clock.sleep(60 * 5)
    c.advance()
    tgt = next(leg for leg in o.legs if leg.order_type == "limit")
    assert tgt.status == "filled" and float(tgt.filled_avg_price) == 10.50
    assert c.mkt.minute(pd.Timestamp(tgt.filled_at).tz_convert(NY)) == 33       # 10:01 only touched
    assert [t["minute"] for t in c.touches] == [31]
    stop = next(leg for leg in o.legs if leg.order_type == "stop")
    assert stop.status == "canceled" and "XYZ" not in c.pos
    c2, clock2 = _client("paper", "touch")
    o2 = _bracket(c2)
    assert float(o2.filled_avg_price) == 10.0
    clock2.sleep(60 * 5)
    c2.advance()
    tgt2 = next(leg for leg in o2.legs if leg.order_type == "limit")
    assert c2.mkt.minute(pd.Timestamp(tgt2.filled_at).tz_convert(NY)) == 31


def test_broker_stop_gap_and_shares_held():
    c, clock = _client()
    c.mkt.arr["XYZ"][40] = [9.50, 9.52, 9.40, 9.45, 1e5]             # 10:10 gaps through the 9.80 stop
    o = _bracket(c, target=11.0, stop=9.80)
    pos = c.get_all_positions()[0]
    assert float(pos.qty) == 10 and float(pos.qty_available) == 0      # the bracket legs hold the shares
    with pytest.raises(RuntimeError):
        c.close_position("XYZ")
    clock.sleep(60 * 15)
    c.advance()
    stop = next(leg for leg in o.legs if leg.order_type == "stop")
    assert stop.status == "filled"
    assert abs(float(stop.filled_avg_price) - (9.50 * (1 - 1e-4) - 0.03)) < 1e-9   # open, minus slippage + stop extra
