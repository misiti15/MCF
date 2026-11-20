"""beginner_1120 deploy (owner 2026-11-20 "BEG-ORB yes" / "BEG-GNG yes", effective session 2026-11-23): BEG-ORB (BEG-01
ORB-15 in play, stop at the far side of OR15) and BEG-GNG (BEG-03 gap-and-go, long, as written) are each one new setup in
exactly one testing area, never beside their ORB / gap-continuation siblings, with a display name, a setup_order slot and
one ledger entry; the live classes keep the standing rules (entries >= 09:50, flat by 15:55, no shorts in inverse /
volatility funds). Educational only - not financial advice."""
import json
from datetime import date, time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from mcf.backtest.engine import simulate
from mcf.strategies.base import DayContext
from mcf.strategies.beginner_setups import BegGapAndGo, BegORB15, never_short

ROOT = Path(__file__).resolve().parents[1]
TESTING = ["testing2", "explore1", "livelab", "testingd", "testinge", "testingf"]
OTHER = ["default", "testing", "graveyard", "gen"]
BEG_1123 = {"BEG-ORB-orb15-inplay-stopOR": "testingf", "BEG-GNG-gap-and-go-long": "explore1"}
CLASSES = {"BEG-ORB-orb15-inplay-stopOR": "beg_orb15", "BEG-GNG-gap-and-go-long": "beg_gap_and_go"}
SIBLINGS = {"BEG-ORB-orb15-inplay-stopOR": ("orb20_a", "orb"), "BEG-GNG-gap-and-go-long": ("ULT-05-withgap-cont", "gap_and_go",
                                                                                       "gap_continuation")}
TZ = "America/New_York"


def _raw(acct):
    p = ROOT / ("config/default.yaml" if acct == "default" else f"config/account_{acct}.yaml")
    return yaml.safe_load(p.read_text())


def _on(raw):
    return {k for k, v in (raw.get("strategies") or {}).items() if isinstance(v, dict) and v.get("enabled")}


# ------------------------------------------------------------------------------------------------ placement / records
def test_each_new_setup_in_exactly_one_testing_area():
    for n, acct in BEG_1123.items():
        homes = [a for a in TESTING if n in _on(_raw(a))]
        assert homes == [acct], (n, homes)
        assert n in _raw(acct)["live"]["setup_order"]
        assert _raw(acct)["strategies"][n]["class"] == CLASSES[n]
        for a in OTHER:
            assert n not in (_raw(a).get("strategies") or {}), (n, a)


def test_not_beside_a_sibling_and_in_different_accounts():
    assert len(set(BEG_1123.values())) == 2
    for n, acct in BEG_1123.items():
        assert not any(o.startswith(SIBLINGS[n]) for o in _on(_raw(acct)) - {n}), (n, acct)


@pytest.mark.parametrize("acct", sorted(set(BEG_1123.values())))
def test_new_setups_build_under_the_live_loader(monkeypatch, acct):
    from mcf.config import load_config
    from mcf.strategies import setups as S

    monkeypatch.setenv("MCF_ACCOUNT", acct)
    built = {s.name: s for s in S.build_strategies(load_config())}
    assert not S.LOAD_FAILURES
    for n, a in BEG_1123.items():
        if a != acct:
            continue
        s = built[n]
        assert type(s).name == CLASSES[n] and s.params.get("scale_out_r") is None, n
    if acct == "testingf":
        assert built["BEG-ORB-orb15-inplay-stopOR"].params["be_at_r"] == 1.0
    if acct == "explore1":
        st = built["BEG-GNG-gap-and-go-long"]
        assert st.params["trail_r"] == 1.0 and st.params["trail_after_r"] == 1.0


def test_names_assignments_ledger_decisions():
    names = yaml.safe_load((ROOT / "config/setup_names.yaml").read_text())
    page = json.loads((ROOT / "docs/live/setup_names.json").read_text())
    d = json.loads((ROOT / "docs/live/assignments.json").read_text())
    for n, acct in BEG_1123.items():
        assert names[n]["account"] == acct and names[n]["name"] and page[n]["name"] == names[n]["name"]
        assert n in d["accounts"][acct], n
    led = [json.loads(x) for x in (ROOT / "research/ledger.jsonl").read_text().splitlines() if x.strip()]
    e = next(x for x in led if x["id"] == "2026-11-23-beg1120-testing-admissions")
    assert e["effective"] == "2026-11-23" and "owner" in e["approved_by"] and set(e["setups"]) == set(BEG_1123)
    assert "1 day" in e["setups"]["BEG-GNG-gap-and-go-long"]["stats"]
    dec = {x["code"]: x for x in json.loads((ROOT / "docs/live/decisions.json").read_text()) if "code" in x}
    for c in ("BEG-ORB", "BEG-GNG"):
        assert dec[c]["status"] == "answered" and dec[c]["answered"].startswith("yes")


# ------------------------------------------------------------------------------------------------ the live classes
def _bars(path, start="2026-11-23 09:30"):
    """path: list of (open, high, low, close, volume) per minute from 09:30."""
    idx = pd.date_range(start, periods=len(path), freq="1min", tz=TZ)
    return pd.DataFrame(path, columns=["open", "high", "low", "close", "volume"], index=idx)


def _ctx(bars, sym="ABC", prev_close=50.0, atr=2.0, rank20=5, avg=1000.0):
    return DayContext(symbol=sym, date=date(2026, 11, 23), bars=bars, prev_close=prev_close, prev_high=prev_close,
                      prev_low=prev_close, atr=atr, avg_dollar_volume=50e6, avg_cum_volume=np.full(390, avg),
                      rank_rvol20=rank20)


def _orb_day(up=True, n=120):
    """OR15 50.00-51.00 (candle up or down); flat 09:45-09:59; breakout of the OR15 extreme at 10:00."""
    rows = []
    for i in range(n):
        if i < 15:
            o, c = (50.2, 50.8) if up else (50.8, 50.2)
            h, l = (51.0 if i == 7 else 50.9), (50.0 if i == 3 else 50.1)
        elif i < 30:
            o = c = 50.5
            h, l = 50.6, 50.4
        elif i == 30:
            o, c = (50.5, 51.2) if up else (50.5, 49.8)
            h, l = (51.3, 50.5) if up else (50.5, 49.7)
        else:
            o = c = 51.2 if up else 49.8
            h, l = o + 0.05, o - 0.05
        rows.append((o, h, l, c, 1000.0))
    return _bars(rows)


def test_orb_long_signal_rule():
    b = _orb_day(up=True)
    sig = BegORB15(scale_out_r=None, be_at_r=1.0).signals(_ctx(b, avg=10.0))      # rvol 1000/10 cum -> in play
    assert len(sig) == 1
    s = sig[0]
    assert s.side == 1 and s.entry_type == "stop" and s.entry_price == 51.01 and s.stop == 50.0
    assert abs(s.target - (51.01 + 2 * 1.01)) < 1e-9 and s.be_at_r == 1.0 and s.exit_by == time(15, 55)
    assert b.index[s.bar_index].time() == time(9, 49) and s.entry_valid_bars == 100            # works 09:50-11:29
    t = simulate(s, b, time(15, 55), 0.0)
    assert t is not None


def test_orb_entries_never_before_0950_and_window_ends_1129():
    b = _orb_day(up=True)
    s = BegORB15().signals(_ctx(b, avg=10.0))[0]
    first_fill_bar = s.bar_index + 1
    assert b.index[first_fill_bar].time() == time(9, 50)
    last_bar = s.bar_index + s.entry_valid_bars
    assert (pd.Timestamp("2026-11-23 09:49") + pd.Timedelta(minutes=s.entry_valid_bars)).time() == time(11, 29)
    assert last_bar > first_fill_bar


def test_orb_filters():
    b = _orb_day(up=True)
    st = BegORB15()
    assert not st.signals(_ctx(b, avg=20000.0))                        # rvol < 2
    assert not st.eligible(_ctx(b, rank20=21))                          # not in the top 20 by rvol20
    assert not st.eligible(_ctx(b, atr=0.4))
    cheap = b.copy()
    cheap[["open", "high", "low", "close"]] /= 6.0                      # price < $10
    assert not st.signals(_ctx(cheap, avg=10.0))
    doji = b.copy()
    doji.iloc[0, doji.columns.get_loc("open")] = float(doji["close"].iloc[14])
    assert not st.signals(_ctx(doji, avg=10.0))
    assert not st.signals(_ctx(b.iloc[:19], avg=10.0))                  # before the 09:49 close: nothing decided


def test_orb_short_side_and_inverse_guard():
    b = _orb_day(up=False)
    s = BegORB15().signals(_ctx(b, avg=10.0))[0]
    assert s.side == -1 and s.entry_price == 49.99 and s.stop == 51.0
    for sym in ("SQQQ", "UVXY", "SVXY", "SOXS", "TSLQ", "VXX"):
        assert never_short(sym), sym
        assert not BegORB15().signals(_ctx(b, sym=sym, avg=10.0)), sym
    assert not never_short("AAPL") and not never_short("TQQQ")
    up = _orb_day(up=True)
    assert BegORB15().signals(_ctx(up, sym="SQQQ", avg=10.0))          # longs on inverse funds are kept


def _gng_day(above_vwap=True, n=180):
    """Gap +6% (prev 50 -> open 53); R20 52.8-53.5; consolidation; breakout above 53.51 at 10:10."""
    rows = []
    for i in range(n):
        if i < 20:
            o, c = 53.0, 53.2
            h, l = (53.5 if i == 10 else 53.3), (52.8 if i == 2 else 52.95)
        elif i < 40:
            base = 53.3 if above_vwap else 52.0
            o = c = base
            h, l = base + 0.05, base - 0.05
        elif i == 40:
            o, c, h, l = (53.3, 53.7, 53.75, 53.3) if above_vwap else (52.0, 52.0, 53.75, 52.0)   # spike, close back below
        else:
            o = c = 53.7 if above_vwap else 52.0
            h, l = o + 0.05, o - 0.05
        rows.append((o, h, l, c, 1000.0))
    return _bars(rows)


def test_gng_signal_rule_and_live_path():
    b = _gng_day()
    st = BegGapAndGo(scale_out_r=None, trail_r=1.0, trail_after_r=1.0)
    sig = st.signals(_ctx(b, prev_close=50.0, avg=10.0))
    assert len(sig) == 1
    s = sig[0]
    k = s.bar_index + 1
    assert b.index[k].time() == time(10, 10) and s.entry_valid_bars == 1 and s.side == 1
    assert s.entry_price == 53.51 and s.trail_r == 1.0 and s.trail_after_r == 1.0 and s.exit_by == time(12, 0)
    risk = s.entry_price - s.stop
    assert abs(s.target - (s.entry_price + 2 * risk)) < 1e-9 and 0.004 <= risk / s.entry_price <= 0.03
    assert s.time_stop_min == 12 * 60 - (10 * 60 + 10) - 1 and s.time_stop_min_r == 99.0     # clock exit 12:00
    # live: the runner sees the bars through the fill bar and needs bar_index = last - 1 with the cross on the latest bar
    live = st.signals(_ctx(b.iloc[: k + 1], prev_close=50.0, avg=10.0))
    assert live and live[0].bar_index == k - 1
    assert not st.signals(_ctx(b.iloc[:k], prev_close=50.0, avg=10.0))        # before the breakout: nothing to enter
    t = simulate(s, b, time(15, 55), 0.0)
    assert t is not None and b.index[k].time() >= time(9, 50)


def test_gng_filters():
    st = BegGapAndGo()
    b = _gng_day()
    assert not st.signals(_ctx(b, prev_close=52.0, avg=10.0))                 # gap < 3%
    assert not st.signals(_ctx(b, prev_close=50.0, avg=10000.0))              # rvol20 < 3
    assert not st.eligible(_ctx(b, prev_close=250.0))                          # price > $200
    assert not st.signals(_ctx(_gng_day(above_vwap=False), prev_close=50.0, avg=10.0))   # never armed below VWAP
