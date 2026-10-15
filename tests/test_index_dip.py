"""Index open-dip bounce (owner 2026-10-15, research/bdi/idxdip1015): signal on the index ETF, trade on the index ETF or a
leveraged tracker, recovery-off-the-low trigger inside 09:50-10:05, exits from the traded symbol's own levels.
Educational only - not financial advice."""
from types import SimpleNamespace

import numpy as np
import pandas as pd

from mcf.backtest.engine import Costs, in_play_filter, pinned_symbols, simulate
from mcf.config import load_config
from mcf.data.bars import TZ
from mcf.execution import runner as R
from mcf.execution.risk import RiskManager
from mcf.strategies.base import DayContext, t
from mcf.strategies.index_dip import IndexDipBounce, find_trigger
from mcf.strategies.setups import REGISTRY, build_strategies

DAY = "2026-10-06"


def _path(points):
    """Piecewise-linear close path over the session from {minute_of_session: price}."""
    idx = pd.date_range(f"{DAY} 09:30", f"{DAY} 15:59", freq="1min", tz=TZ)
    xs, ys = zip(*sorted(points.items()))
    return idx, np.interp(np.arange(len(idx)), xs, ys)


def _bars(points, lev=1.0, base=100.0, drop_minutes=()):
    """1-minute bars; lev scales the index path's returns around `base` (a 2x / 3x tracker)."""
    idx, p = _path(points)
    p = base * (1 + lev * (p / 100.0 - 1))
    o = np.concatenate([[p[0]], p[:-1]])
    df = pd.DataFrame({"open": o, "high": np.maximum(o, p) + 0.0001 * base, "low": np.minimum(o, p) - 0.0001 * base,
                       "close": p, "volume": 1e5}, index=idx)
    return df.drop(df.index[list(drop_minutes)]) if drop_minutes else df


# index: open 100, falls to 98.9 (-1.1%) by 09:40 (minute 10), flat until 09:48, bounces to 99.6 by 10:00, drifts up
DIP = {0: 100.0, 10: 98.9, 18: 98.9, 30: 99.6, 120: 99.9, 389: 100.0}


def _ctx(sym, bars, peers=None):
    return DayContext(sym, pd.Timestamp(DAY).date(), bars, prev_close=100.0, prev_high=101.0, prev_low=99.0,
                      atr=1.0, avg_dollar_volume=3e10, peers=peers)


def _strat(**kw):
    p = dict(symbols=["SPY", "SSO"], signal_symbol="SPY", dip_pct=0.75, dip_by="09:45", trigger="recovery",
             recovery_frac=0.10, stop_buffer_frac=0.10, target="retrace", target_frac=0.5)
    p.update(kw)
    return IndexDipBounce(**p)


def test_registered_and_buildable():
    assert REGISTRY["index_dip_bounce"] is IndexDipBounce
    cfg = {"strategies": {"IDX-test": {"enabled": True, "class": "index_dip_bounce", "symbols": ["SSO"],
                                       "signal_symbol": "SPY", "trail_r": 1.0, "trail_after_r": 1.0}}}
    (st,) = build_strategies(cfg)
    assert st.name == "IDX-test" and st.params["signal_symbol"] == "SPY"
    sig = st.signals(_ctx("SSO", _bars(DIP, lev=2), {"SPY": _bars(DIP)}))[0]
    assert sig.trail_r == 1.0 and sig.strategy == "IDX-test"          # shared exit keys reach the signal


def test_trigger_first_bar_in_window_after_recovery():
    b = _bars(DIP)
    tr = find_trigger(b, 0.75, "09:45", "09:50", "10:05", "recovery", 0.10)
    assert tr is not None
    end = tr["ts"] + pd.Timedelta(minutes=1)
    assert t("09:50") <= end.time() <= t("10:05")
    assert tr["close"] >= tr["low"] + 0.10 * (tr["open"] - tr["low"])
    assert tr["drop_pct"] < -0.75
    # the bounce leg starts at 09:48; 10% of the 1.11 drop is first regained by the bar closing 09:51
    assert end.time() == t("09:51")
    prev = b.iloc[: b.index.get_loc(tr["ts"])]
    assert prev["close"].iloc[-1] < tr["low"] + 0.10 * (tr["open"] - tr["low"])     # the bar before did not qualify


def test_no_trigger_when_dip_too_small_or_too_late():
    small = {0: 100.0, 10: 99.5, 18: 99.5, 30: 99.9, 389: 100.0}               # -0.5%
    assert find_trigger(_bars(small), 0.75, "09:45", "09:50", "10:05") is None
    late = {0: 100.0, 20: 99.6, 26: 98.9, 30: 99.5, 389: 100.0}                  # -1.1% only at 09:56
    assert find_trigger(_bars(late), 0.75, "09:45", "09:50", "10:05") is None
    assert find_trigger(_bars(late), 0.75, "09:58", "09:50", "10:05") is not None


def test_no_trigger_when_bounce_only_after_window():
    slow = {0: 100.0, 10: 98.9, 36: 98.88, 45: 99.6, 389: 100.0}               # low keeps sliding until 10:06
    assert find_trigger(_bars(slow), 0.75, "09:45", "09:50", "10:05", "recovery", 0.20) is None


def test_alternative_triggers():
    b = _bars(DIP)
    assert find_trigger(b, 0.75, "09:45", "09:50", "10:05", "hi3") is not None
    vw = find_trigger(b, 0.75, "09:45", "09:50", "10:20", "vwap")
    assert vw is None or vw["close"] > 98.9


def test_signal_on_index_trade_on_leveraged_tracker_uses_its_own_levels():
    spy, sso = _bars(DIP), _bars(DIP, lev=2.0, base=50.0)
    st = _strat()
    s_spy = st.signals(_ctx("SPY", spy))[0]                                      # signal symbol traded itself
    s_sso = st.signals(_ctx("SSO", sso, {"SPY": spy}))[0]
    assert s_spy.bar_index == s_sso.bar_index and s_sso.side == 1 and s_sso.entry_type == "market"
    lo, o = sso["low"].iloc[: s_sso.bar_index + 1].min(), sso["open"].iloc[0]
    assert np.isclose(s_sso.stop, lo - 0.10 * (o - lo))
    assert np.isclose(s_sso.target, lo + 0.5 * (o - lo))
    # stop distance in % of price ~2x the index's: risk-based sizing gives about the same dollar risk
    px_spy, px_sso = spy["close"].iloc[s_spy.bar_index], sso["close"].iloc[s_sso.bar_index]
    pct_spy, pct_sso = (px_spy - s_spy.stop) / px_spy, (px_sso - s_sso.stop) / px_sso
    assert 1.8 < pct_sso / pct_spy < 2.2
    cfg = load_config()
    cfg["account"].update(max_position_notional_pct=100, buying_power_multiple=100, slots=1)   # risk-bound sizing
    rm = RiskManager(cfg, 100_000)
    d_spy = rm.size(s_spy, px_spy) * (px_spy - s_spy.stop)
    d_sso = rm.size(s_sso, px_sso) * (px_sso - s_sso.stop)
    assert abs(d_spy - d_sso) / d_spy < 0.05


def test_no_signal_without_index_bars_or_for_other_symbols():
    st = _strat()
    assert st.signals(_ctx("SSO", _bars(DIP, lev=2))) == []                     # peers missing -> nothing
    assert not st.eligible(_ctx("QQQ", _bars(DIP)))


def test_thin_tracker_maps_to_its_last_bar_before_the_trigger():
    spy = _bars(DIP)
    trig = find_trigger(spy, 0.75, "09:45", "09:50", "10:05", "recovery", 0.10)
    i = spy.index.get_loc(trig["ts"])
    thin = _bars(DIP, lev=2.0, base=200.0, drop_minutes=[i, i - 1])               # no prints at the trigger minutes
    sig = _strat(symbols=["SPUU"]).signals(_ctx("SPUU", thin, {"SPY": spy}))[0]
    assert thin.index[sig.bar_index] < trig["ts"] and thin.index[sig.bar_index + 1] > trig["ts"]


def test_targets_and_trailing_in_backtest():
    spy, sso = _bars(DIP), _bars(DIP, lev=2.0, base=50.0)
    costs = Costs(bps=1.0, per_share=0.01, stop_extra_per_share=0.02)
    for kw in ({"target_frac": 0.5}, {"target_frac": 1.0}, {"target": "vwap"}, {"target": None},
               {"target": None, "trail_r": 1.0, "trail_after_r": 1.0}, {"target": None, "exit_by": "10:30"}):
        st = _strat(**kw)
        (sig,) = st.signals(_ctx("SSO", sso, {"SPY": spy}))
        tr = simulate(sig, sso, t("15:55"), costs)
        assert tr is not None and tr.side == 1
        if kw.get("exit_by"):
            assert tr.exit_reason == "time" and tr.exit_time.strftime("%H:%M") == "10:30"
    # retrace target that is already behind the price: no trade
    assert _strat(target_frac=0.05).signals(_ctx("SSO", sso, {"SPY": spy})) == []


def test_pinned_symbols_include_signal_symbol_and_keep_thin_trackers():
    cfg = load_config()
    cfg["strategies"] = {"IDX": {"enabled": True, "class": "index_dip_bounce", "symbols": ["SPUU"], "signal_symbol": "SPY"}}
    assert pinned_symbols(cfg) == {"SPUU", "SPY"}
    thin = _ctx("SPUU", _bars(DIP, base=200.0))
    thin.avg_dollar_volume = 2e6                                               # extended tier, not in play
    other = _ctx("ZZZZ", _bars(DIP))
    other.avg_dollar_volume = 2e6
    kept, _ = in_play_filter([thin, other], [1.0, 1.0], cfg)
    assert [c.symbol for c in kept] == ["SPUU"]


class _Broker:
    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):
        return {}


def test_live_runner_enters_once_on_the_tracker_from_index_bars(tmp_path, monkeypatch):
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["strategies"] = {"IDX-sso": {"enabled": True, "class": "index_dip_bounce", "symbols": ["SSO"],
                                     "signal_symbol": "SPY", "dip_pct": 0.75, "dip_by": "09:45",
                                     "trigger": "recovery", "recovery_frac": 0.10, "target": None,
                                     "trail_r": 1.0, "trail_after_r": 1.0}}
    strats = build_strategies(cfg)
    spy, sso = _bars(DIP), _bars(DIP, lev=2.0, base=50.0)
    pri = {s: SimpleNamespace(prev_close=float(b["open"].iloc[0]), prev_high=0.0, prev_low=0.0, atr=1.0, adv=3e10,
                              avg_cum=None, avg_move=None) for s, b in (("SPY", spy), ("SSO", sso))}
    r = R.PaperRunner(cfg, strats, pri, dry_run=True, broker=_Broker())
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    seen = []
    monkeypatch.setattr(r, "_log", lambda sig, status, why, ref, now, *a, **k: seen.append((now, status, sig)))
    for m in pd.date_range(f"{DAY} 09:35:05", f"{DAY} 10:30:05", freq="1min", tz=TZ):
        monkeypatch.setattr(r, "fetch", lambda now: {s: b[b.index < now.floor("1min")] for s, b in
                                                     (("SPY", spy), ("SSO", sso))})
        r.step(m)
    assert len(seen) == 1
    now, status, sig = seen[0]
    assert status == "dry_run" and sig.symbol == "SSO" and sig.side == 1 and now.strftime("%H:%M") == "09:51"
    # same decision as the backtest on full-day bars
    full = strats[0].signals(_ctx("SSO", sso, {"SPY": spy}))[0]
    assert full.bar_index == sig.bar_index and np.isclose(full.stop, sig.stop)


def test_unquoted_yaml_times_are_read_as_clock_times():
    import yaml

    raw = yaml.safe_load("a: 10:05\nb: 09:45\n")            # YAML 1.1: 10:05 -> 605 (base 60), 09:45 -> '09:45'
    assert raw["a"] == 605
    b = _bars(DIP)
    assert find_trigger(b, 0.75, raw["b"], "09:50", raw["a"]) == find_trigger(b, 0.75, "09:45", "09:50", "10:05")


# ---- single-instrument choice (owner 2026-10-15): trade only the 3x candidate with the larger dollar volume so far
def _vol(b, early, late, cut="09:51"):
    """Volume `early` on bars starting before `cut` (bar-start time) and `late` after it."""
    b = b.copy()
    b["volume"] = np.where(b.index.time < t(cut), early, late)
    return b


def _cands(**kw):
    p = dict(trade_candidates=["SPXL", "UPRO"], pick="max_dollar_volume", signal_symbol="SPY", dip_pct=0.75,
             dip_by="09:45", trigger="recovery", recovery_frac=0.10, stop_buffer_frac=0.10, target=None,
             trail_r=1.0, trail_after_r=1.0)
    p.update(kw)
    return IndexDipBounce(**p)


def test_pick_trades_only_the_candidate_with_more_dollar_volume_so_far():
    spy = _bars(DIP)
    # SPXL: more dollars 09:30-09:50 (the trigger bar starts 09:50); UPRO: far more AFTER the decision -> must not count
    spxl = _vol(_bars(DIP, lev=3.0, base=150.0), 2e5, 1e3)
    upro = _vol(_bars(DIP, lev=3.0, base=90.0), 1e5, 1e8)
    peers = {"SPY": spy, "SPXL": spxl, "UPRO": upro}
    st = _cands()
    assert st.eligible(_ctx("SPXL", spxl)) and st.eligible(_ctx("UPRO", upro)) and not st.eligible(_ctx("SPY", spy))
    (sig,) = st.signals(_ctx("SPXL", spxl, peers))
    assert st.signals(_ctx("UPRO", upro, peers)) == []
    assert sig.symbol == "SPXL" and sig.meta["picked"] == "SPXL" and sig.meta["pick"] == "max_dollar_volume"
    assert sig.meta["dv_SPXL"] > sig.meta["dv_UPRO"] > 0 and sig.meta["candidates"] == "SPXL,UPRO"
    assert sig.trail_r == 1.0
    # same geometry as a fixed single-symbol setup on the chosen instrument
    fixed = _cands(trade_candidates=None, symbols=["SPXL"]).signals(_ctx("SPXL", spxl, peers))[0]
    assert fixed.bar_index == sig.bar_index and np.isclose(fixed.stop, sig.stop) and "picked" not in fixed.meta
    # flip the early volume -> UPRO is chosen
    peers2 = {"SPY": spy, "SPXL": _vol(spxl, 1e5, 1e8), "UPRO": _vol(upro, 3e5, 1e3)}
    assert st.signals(_ctx("SPXL", peers2["SPXL"], peers2)) == []
    assert st.signals(_ctx("UPRO", peers2["UPRO"], peers2))[0].meta["picked"] == "UPRO"


def test_pick_tie_goes_to_first_listed_and_missing_candidate_counts_zero():
    spy = _bars(DIP)
    a, b = _bars(DIP, lev=3.0, base=100.0), _bars(DIP, lev=3.0, base=100.0)
    st = _cands()
    assert len(st.signals(_ctx("SPXL", a, {"SPY": spy, "SPXL": a, "UPRO": b}))) == 1
    assert st.signals(_ctx("UPRO", b, {"SPY": spy, "SPXL": a, "UPRO": b})) == []
    assert st.signals(_ctx("UPRO", b, {"SPY": spy, "UPRO": b}))[0].symbol == "UPRO"      # SPXL bars absent today


def test_pick_rule_validation_and_pinned_candidates():
    import pytest

    with pytest.raises(ValueError):
        _cands(pick="max_volume_yesterday")
    cfg = load_config()
    cfg["strategies"] = {"IDX": {"enabled": True, "class": "index_dip_bounce", "trade_candidates": ["SPXL", "UPRO"],
                                 "pick": "max_dollar_volume", "signal_symbol": "SPY"}}
    assert pinned_symbols(cfg) == {"SPXL", "UPRO", "SPY"}
    (st,) = build_strategies(cfg)
    assert st.tradeable() == ["SPXL", "UPRO"]


def test_live_runner_trades_only_the_pick(tmp_path, monkeypatch):
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["strategies"] = {"IDX2-3x": {"enabled": True, "class": "index_dip_bounce", "trade_candidates": ["SPXL", "UPRO"],
                                     "pick": "max_dollar_volume", "signal_symbol": "SPY", "dip_pct": 0.75,
                                     "dip_by": "09:45", "trigger": "recovery", "recovery_frac": 0.10, "target": None,
                                     "trail_r": 1.0, "trail_after_r": 1.0}}
    strats = build_strategies(cfg)
    spy = _bars(DIP)
    spxl = _vol(_bars(DIP, lev=3.0, base=150.0), 1e5, 1e8)
    upro = _vol(_bars(DIP, lev=3.0, base=90.0), 3e5, 1e3)
    tape = (("SPY", spy), ("SPXL", spxl), ("UPRO", upro))
    pri = {s: SimpleNamespace(prev_close=float(b["open"].iloc[0]), prev_high=0.0, prev_low=0.0, atr=1.0, adv=3e10,
                              avg_cum=None, avg_move=None) for s, b in tape}
    r = R.PaperRunner(cfg, strats, pri, dry_run=True, broker=_Broker())
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    seen = []
    monkeypatch.setattr(r, "_log", lambda sig, status, why, ref, now, *a, **k: seen.append((now, status, sig)))
    for m in pd.date_range(f"{DAY} 09:35:05", f"{DAY} 10:30:05", freq="1min", tz=TZ):
        monkeypatch.setattr(r, "fetch", lambda now: {s: b[b.index < now.floor("1min")] for s, b in tape})
        r.step(m)
    assert len(seen) == 1
    now, status, sig = seen[0]
    assert sig.symbol == "UPRO" and sig.meta["picked"] == "UPRO" and now.strftime("%H:%M") == "09:51"
    # the backtest on full-day bars (UPRO's late volume is far smaller, SPXL's far larger) makes the same choice
    full = [s for c, b in (("SPXL", spxl), ("UPRO", upro))
            for s in strats[0].signals(_ctx(c, b, {"SPY": spy, "SPXL": spxl, "UPRO": upro}))]
    assert [s.symbol for s in full] == ["UPRO"] and full[0].bar_index == sig.bar_index
