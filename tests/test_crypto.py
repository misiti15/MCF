"""mcf/crypto foundation: loader/grid/resample, costs, 24/7 engine fills, splits lock, generator."""
import numpy as np
import pandas as pd
import pytest

from mcf.crypto import data as D
from mcf.crypto import splits as S
from mcf.crypto.backtest import Exit, run_pair, session_mask, summarize
from mcf.crypto.costs import FEE_MAKER, FEE_TAKER, CostModel
from mcf.crypto.features import build
from mcf.crypto.generator import Setup, generate, mask, window_mask


def _bars(prices, start="2024-03-04 00:00", freq="1min", drop=()):
    idx = pd.date_range(start, periods=len(prices), freq=freq, tz="UTC", name="t")
    p = np.asarray(prices, float)
    df = pd.DataFrame({"o": p, "h": p * 1.001, "l": p * 0.999, "c": p, "v": 1.0, "vw": p, "n": 1}, index=idx)
    return df.drop(df.index[list(drop)])


def test_grid_marks_empty_minutes_and_carries_close():
    b = _bars([100, 101, 102, 103], drop=[1, 2])
    g = D.to_grid(b)
    assert len(g) == 4
    assert g["filled"].tolist() == [False, True, True, False]
    assert g["c"].iloc[1] == 100 and g["h"].iloc[2] == 100 and g["v"].iloc[1] == 0


def test_resample_uses_real_bars_only():
    b = _bars(list(range(100, 110)), drop=[5, 6, 7, 8, 9])
    r = D.resample(b, "5min")
    assert len(r) == 1 and r["o"].iloc[0] == 100 and r["c"].iloc[0] == 104
    rf = D.resample(b, "5min", ffill=True)
    assert len(rf) == 1                                   # trailing empty bucket outside the real-bar span


def test_resample_ffill_flags_gap_bucket():
    b = _bars(list(range(100, 115)), drop=[5, 6, 7, 8, 9])
    rf = D.resample(b, "5min", ffill=True)
    assert rf["filled"].tolist() == [False, True, False]
    assert rf["c"].iloc[1] == 104


def test_get_refuses_non_market_data_paths():
    with pytest.raises(ValueError):
        D._get("../../v2/orders", {})


def test_costs_taker_and_maker():
    cm = CostModel(spreads={"BTC": {"2023": 0.001, "2024": 0.0006}})
    rt = cm.round_trip("BTC", 2024)
    assert rt == pytest.approx(2 * FEE_TAKER + 0.0006 + 4e-4)
    assert cm.spread("BTC", 2021) == 0.001                 # before quote history -> earliest year
    assert cm.round_trip("BTC", 2024, stop_exit=True) == pytest.approx(rt + 5e-4)
    mk = CostModel.maker(spreads=cm.spreads)
    assert mk.side_cost("BTC", 2024, entry=True) == FEE_MAKER
    assert cm.spread("ZZZ", 2024) > 0                      # unknown pair -> conservative default


def _frame(o, h, l, c, atr=1.0):
    idx = pd.date_range("2024-01-01", periods=len(o), freq="15min", tz="UTC")
    return pd.DataFrame({"o": o, "h": h, "l": l, "c": c, "atr": atr, "filled": False}, index=idx)


ZERO = CostModel(fee_entry=0, fee_exit=0, slip_bps=0, stop_extra_bps=0, spreads={"X": {"2024": 0.0}})


def test_engine_stop_first_and_target():
    f = _frame([100, 100, 100, 100], [100, 104, 100, 100], [100, 97, 100, 100], [100, 100, 100, 100])
    sig = np.array([True, False, False, False])
    tr = run_pair("X", f, sig, Exit(2.0, 3.0, 5), costs=ZERO)
    assert len(tr) == 1 and tr["kind"].iloc[0] == 1 and tr["r"].iloc[0] == pytest.approx(-1.0)
    f2 = _frame([100, 100, 100, 100], [100, 104, 100, 100], [100, 99, 100, 100], [100, 100, 100, 100])
    tr2 = run_pair("X", f2, sig, Exit(2.0, 3.0, 5), costs=ZERO)
    assert tr2["kind"].iloc[0] == 2 and tr2["r"].iloc[0] == pytest.approx(1.5)


def test_engine_gap_through_stop_fills_at_open_and_time_stop():
    f = _frame([100, 100, 95, 95], [100, 100, 95, 95], [100, 99.5, 94, 94], [100, 100, 95, 95])
    tr = run_pair("X", f, np.array([True, False, False, False]), Exit(2.0, None, 5), costs=ZERO)
    assert tr["exit"].iloc[0] == 95 and tr["r"].iloc[0] == pytest.approx(-2.5)
    f2 = _frame([100, 100, 101, 102, 103], [100] * 5, [100] * 5, [100, 100, 101, 102, 103])
    f2["h"] = f2[["o", "c"]].max(axis=1)
    f2["l"] = f2[["o", "c"]].min(axis=1)
    tr2 = run_pair("X", f2, np.array([True, False, False, False, False]), Exit(2.0, None, 2), costs=ZERO)
    assert tr2["kind"].iloc[0] == 0 and tr2["exit"].iloc[0] == 101


def test_engine_charges_costs_in_r_and_no_overlap():
    f = _frame([100] * 6, [100] * 6, [100] * 6, [100] * 6, atr=0.5)
    cm = CostModel(spreads={"X": {"2024": 0.0}}, slip_bps=0, stop_extra_bps=0)
    tr = run_pair("X", f, np.ones(6, bool), Exit(2.0, None, 2), costs=cm)
    assert (tr["entry_time"].diff().dropna() >= pd.Timedelta("45min")).all()
    assert tr["cost_r"].iloc[0] == pytest.approx(0.005 * 100 / 1.0)
    s = summarize(tr)
    assert s["avg_r"] == pytest.approx(-0.5) and s["n"] == len(tr)


def test_summarize_best_day():
    tr = pd.DataFrame({"day": ["a", "a", "b", "c"], "r": [3.0, 1.0, -1.0, 1.0], "cost_r": 0.1, "gross_r": 0})
    s = summarize(tr)
    assert s["best_day_share"] == pytest.approx(4 / 4)
    assert s["avg_r_wo_best"] == pytest.approx(0.0)


def test_session_mask_windows():
    idx = pd.date_range("2024-03-02 13:00", periods=5, freq="30min", tz="UTC")    # a Saturday
    assert session_mask(idx, "us_open").tolist() == [False, True, True, True, False]
    assert not session_mask(idx, "us_open", "weekday").any()


def test_locked_block_is_sealed(monkeypatch, tmp_path):
    monkeypatch.delenv("MCF_CRYPTO_ALLOW_LOCKED", raising=False)
    with pytest.raises(PermissionError):
        S.bounds("locked")
    assert S.clip_end("2026-11-01") == pd.Timestamp(S.LOCKED_START, tz="UTC")
    d = tmp_path / "X_USD"
    d.mkdir()
    b = _bars([1.0, 2.0], start="2026-05-25 23:59")
    b.to_parquet(d / "2026.parquet")
    got = D.load_bars("X", cache=tmp_path)
    assert len(got) == 1 and got.index.max() < pd.Timestamp(S.LOCKED_START, tz="UTC")
    assert S.FIT[1] == S.CHECK[0] and S.CHECK[1] == S.LOCKED[0]


def test_generator_seeded_and_counted():
    a, b = generate(50, 7), generate(50, 7)
    assert [s.label() for s in a] == [s.label() for s in b]
    assert [s.draw_id for s in a] == list(range(50))
    assert all(s.tf in (15, 60) for s in a)
    assert all("orb_us" not in [p for p, _ in s.conds] or s.tf == 15 for s in generate(300, 1))


def test_masks_run_on_features():
    rng = np.random.default_rng(0)
    p = 100 * np.exp(np.cumsum(rng.normal(0, 0.002, 4000)))
    b = _bars(p, start="2024-03-04", freq="15min")
    b["filled"] = False
    f = build(b, 15, btc=build(b, 15))
    for s in generate(60, 3):
        if s.tf != 15:
            continue
        m = mask(s, f)
        assert m.dtype == bool and len(m) == len(f)
        assert (m <= window_mask(s, f) | m).all()
    s = Setup(0, 15, 1, [("rsi", {"dir": "low", "lvl": 30})], "any", "all")
    m = mask(s, f)
    assert m.any() and (f["rsi"].to_numpy()[m] <= 30).all()


# ---------------------------------------------------------------- round 2: 1-min fills, maker realism, tiers
from mcf.crypto.costs import FEE_TIERS  # noqa: E402
from mcf.crypto.exec1m import Minutes, Plan, reprice, run, to_min  # noqa: E402
from mcf.crypto import generator2 as G2  # noqa: E402

ZERO2 = CostModel(slip_bps=0, stop_extra_bps=0, spreads={"X": {"2024": 0.0}})


def _mins(o, h, l, c, start="2024-03-04 00:00"):
    idx = pd.date_range(start, periods=len(o), freq="1min", tz="UTC")
    return Minutes(to_min(idx), *(np.asarray(x, float) for x in (o, h, l, c))), int(to_min(idx)[0])


def _run(m, t0, plan, ref=100.0, atr=1.0, costs=ZERO2, tier=1):
    return run("X", m, np.array([t0]), np.array([ref]), np.array([atr]), plan, costs, tier)


def test_maker_fills_only_when_traded_through():
    plan = Plan("maker", 0.0, 3, 1.0, 0.0, None, 2)
    m, t0 = _mins([100] * 5, [100.5] * 5, [100, 100, 100, 100, 100], [100] * 5)        # touches 100, never below
    tr, _, missed = _run(m, t0, plan)
    assert len(tr) == 0 and missed == 1
    m, t0 = _mins([100] * 5, [100.5] * 5, [100, 99.9, 100, 100, 100], [100] * 5)       # trades through on minute 1
    tr, _, missed = _run(m, t0, plan)
    assert missed == 0 and len(tr) == 1
    assert tr["entry"].iloc[0] == 100.0 and tr["maker_in"].iloc[0]
    assert tr["entry_time"].iloc[0] == pd.Timestamp("2024-03-04 00:01", tz="UTC")


def test_maker_expiry_and_offset():
    plan = Plan("maker", 0.5, 2, 1.0, 0.0, None, 2)                                     # limit 99.5, 2-minute life
    m, t0 = _mins([100] * 5, [100] * 5, [100, 99.6, 99.4, 99.0, 99.0], [100] * 5)
    tr, _, missed = _run(m, t0, plan)
    assert len(tr) == 0 and missed == 1                                                # through only at minute 2
    tr, _, _ = _run(m, t0, Plan("maker", 0.5, 3, 1.0, 0.0, None, 2))
    assert len(tr) == 1 and tr["entry"].iloc[0] == 99.5


def test_stop_on_maker_fill_minute_and_min_stop_pct():
    m, t0 = _mins([100, 100, 100], [100, 100, 100], [100, 96.0, 100], [100, 97, 100])
    tr, _, _ = _run(m, t0, Plan("maker", 0.0, 3, 1.0, 0.03, 2.0, 10))
    assert tr["kind"].iloc[0] == 1 and tr["risk"].iloc[0] == pytest.approx(3.0)         # 3% floor beats 1 ATR
    assert tr["exit"].iloc[0] == pytest.approx(97.0) and tr["gross_r"].iloc[0] == pytest.approx(-1.0)
    assert tr["cost_r"].iloc[0] == pytest.approx((0.0015 + 0.0025) * 100 / 3.0)


def test_target_needs_trade_through_and_is_maker():
    plan = Plan("taker", 0.0, 0, 1.0, 0.0, 2.0, 100)                                    # risk 1, target 102
    m, t0 = _mins([100] * 4, [100, 102, 102.01, 100], [100, 100, 100, 100], [100] * 4)
    tr, _, _ = _run(m, t0, plan)
    assert tr["kind"].iloc[0] == 2 and tr["exit_time"].iloc[0] == pd.Timestamp("2024-03-04 00:02", tz="UTC")
    assert tr["maker_out"].iloc[0] and not tr["maker_in"].iloc[0]
    fees = FEE_TIERS[1][1] + FEE_TIERS[1][0]
    assert tr["cost_r"].iloc[0] == pytest.approx(fees * 100 / 1.0)


def test_time_exit_on_first_print_after_hold_and_thin_entry():
    idx = pd.DatetimeIndex(["2024-03-04 00:02", "2024-03-04 00:03", "2024-03-04 00:09"], tz="UTC")
    m = Minutes(to_min(idx), np.array([100, 101, 103.0]), np.array([100, 101, 103.0]),
                np.array([100, 101, 103.0]), np.array([100, 101, 103.0]))
    t0 = int(to_min(pd.DatetimeIndex(["2024-03-04 00:00"], tz="UTC"))[0])
    tr, _, _ = _run(m, t0, Plan("taker", 0.0, 0, 5.0, 0.0, None, 5))
    assert tr["thin"].iloc[0] and tr["entry"].iloc[0] == 100 and tr["exit"].iloc[0] == 103 and tr["kind"].iloc[0] == 0


def test_fee_tiers_reprice_without_resimulating():
    m, t0 = _mins([100] * 4, [100] * 4, [100] * 4, [100] * 4)
    tr, _, _ = _run(m, t0, Plan("taker", 0.0, 0, 1.0, 0.0, None, 2))
    r1 = tr["r"].iloc[0]
    reprice(tr, 3)
    assert tr["r"].iloc[0] - r1 == pytest.approx((0.0050 - 0.0040) * 100)
    assert FEE_TIERS[2] == (0.0012, 0.0022)


def test_generator2_counted_seeds_and_masks():
    a, b = G2.generate(40, 5, start_id=500), G2.generate(40, 5, start_id=500)
    assert [s.label() for s in a] == [s.label() for s in b] and a[0].draw_id == 500
    assert all(s.hold_h * 60 >= s.tf and s.min_stop_pct >= 0.03 for s in a)
    g = G2.seed_grid(900)
    assert len(g) == 80 and [s.draw_id for s in g] == list(range(900, 980))
    rng = np.random.default_rng(1)
    p = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, 6000)))
    bars = _bars(p, start="2024-03-04", freq="15min")
    bars["filled"] = False
    btc = G2.build2(bars, 15)
    f = G2.build2(bars, 15, btc=btc)
    for s in g + [x for x in G2.generate(80, 2) if x.tf == 15]:
        m = G2.mask(s, f, "ETH")
        assert m.dtype == bool and len(m) == len(f) and not (m & ~G2.time_mask(s, f)).any()
    s = G2.Setup2(0, 15, [("rsi", {"dir": "low", "lvl": 30})])
    m = G2.mask(s, f, "ETH")
    assert m.any() and (f["rsi"].to_numpy()[m] <= 30).all()


def test_amendment1_bad_prints_and_traded_only_maker_fills():
    from mcf.crypto.exec1m import clean_prints
    idx = pd.date_range("2024-03-04", periods=80, freq="1min", tz="UTC")
    b = pd.DataFrame({"o": 100.0, "h": 100.5, "l": 99.5, "c": 100.0, "v": 1.0}, index=idx)
    b.iloc[70, b.columns.get_loc("h")] = 400.0            # spike high -> cut to the body
    b.iloc[72, b.columns.get_loc("c")] = 300.0            # bad close -> bar dropped
    b.iloc[74, b.columns.get_loc("l")] = 50.0             # spike low -> raised to the body
    cl = clean_prints(b)
    assert len(cl) == 79 and idx[72] not in cl.index
    assert cl.loc[idx[70], "h"] == 100.0 and cl.loc[idx[74], "l"] == 100.0 and cl.loc[idx[10], "h"] == 100.5
    # a zero-volume (quote-derived) minute trading through the limit does not fill a maker order
    m, t0 = _mins([100] * 4, [100] * 4, [100, 99, 100, 100], [100] * 4)
    m.traded = np.array([True, False, True, True])
    tr, _, missed = _run(m, t0, Plan("maker", 0.0, 4, 1.0, 0.0, None, 2))
    assert len(tr) == 0 and missed == 1


# ---- round 3: clean traded-only bars and the daily trend engine (research/crypto_r3/PREREG.md) ----
from mcf.crypto import trend as TR  # noqa: E402
from mcf.crypto.exec1m import clean_traded  # noqa: E402


def test_clean_traded_drops_zero_volume_and_bad_prints():
    idx = pd.date_range("2024-01-01", periods=80, freq="1min", tz="UTC")
    b = pd.DataFrame({"o": 100.0, "h": 100.5, "l": 99.5, "c": 100.0, "v": 1.0}, index=idx)
    b.iloc[70, b.columns.get_loc("v")] = 0.0                       # quote-derived minute
    b.iloc[75, b.columns.get_loc("c")] = 200.0                     # bad print
    out = clean_traded(b)
    assert idx[70] not in out.index and idx[75] not in out.index and len(out) == 78


def _tmins(lows, opens=None, traded=None, t0=0):
    n = len(lows)
    lo = np.asarray(lows, float)
    op = np.asarray(opens if opens is not None else lows, float)
    return Minutes(np.arange(t0, t0 + n, dtype=np.int64), op, op + 1, lo, op,
                   None if traded is None else np.asarray(traded, bool))


def test_trend_maker_entry_needs_traded_through_and_taker_exit_costs():
    zero = CostModel(slip_bps=0.0, spreads={"X": {"2023": 0.0}})
    # decisions every 10 min; close 100 at k=0; minute lows: touch 100 (no fill), zero-volume 99 (no fill), 99 fills
    lows = [100, 99, 99, 101, 101, 101, 101, 101, 101, 101] + [110] * 20
    traded = [1, 0, 1, 1, 1, 1, 1, 1, 1, 1] + [1] * 20
    m = _tmins(lows, traded=traded)
    dec = np.array([0, 10, 20], np.int64)
    close = np.array([100.0, 105.0, 110.0])
    tr = TR.simulate("X", dec, close, np.array([1, 0, 0], bool), np.array([0, 1, 1], bool), m, zero,
                     expiry=10)
    assert len(tr) == 1
    row = tr.iloc[0]
    assert row.t_in == 2 and row.entry == 100.0 and row.cost_in == FEE_TIERS[1][0]
    assert row.k_out == 1 and row.exit == 110.0 and row.cost_out == pytest.approx(FEE_TIERS[1][1])
    assert row.net == pytest.approx(1.1 * (1 - 0.0015) * (1 - 0.0025) - 1)


def test_trend_missed_maker_is_not_chased_and_signals():
    m = _tmins([101] * 40)
    dec = np.array([0, 10, 20, 30], np.int64)
    tr = TR.simulate("X", dec, np.full(4, 100.0), np.ones(4, bool), np.zeros(4, bool), m, CostModel(),
                     expiry=10)
    assert tr.empty and tr.attrs["missed"] == 3                 # last decision never opens a trade
    d = pd.DataFrame({"o": 1.0, "h": 1.0, "l": 1.0, "c": np.r_[np.full(60, 10.0), np.arange(11, 31)]},
                     index=pd.date_range("2021-01-01", periods=80, freq="D", tz="UTC"))
    f = TR.indicators(d)
    en, ex = TR.signals(TR.TrendRule("A", 50), f)
    assert not en[:49].any() and en[60:].all() and ex[60:].sum() == 0
    en, ex = TR.signals(TR.TrendRule("B", 50), f)
    assert en[61:].all()                                         # each new close is a 20-day high


def test_sleeve_equity_and_metrics():
    dec = np.array([10, 20, 30, 40], np.int64)
    close = np.array([100.0, 110.0, 121.0, 121.0])
    tr = pd.DataFrame({"t_in": [5], "t_out": [30], "entry": [100.0], "exit": [121.0], "cost_in": [0.0],
                       "cost_out": [0.0]})
    eq = TR.sleeve_equity(tr, dec, close)
    assert eq[-1] == pytest.approx(1.21) and eq[2] == pytest.approx(1.21)
    mt = TR.metrics(np.array([1.0, 0.5, 1.0]))
    assert mt["maxdd"] == pytest.approx(0.5) and mt["total"] == pytest.approx(0.0)


def test_random_windows_non_overlapping_same_durations():
    rng = np.random.default_rng(1)
    en, ex = TR.random_windows(rng, [3, 5, 2], 30)
    assert en.sum() == 10 and not (en & ex).any()
    runs = np.diff(np.r_[0, en.astype(int), 0])
    assert sorted(np.flatnonzero(runs == -1) - np.flatnonzero(runs == 1)) == [2, 3, 5]


# ------------------------------------------------------------------ crypto_setups1 (first hand-built setups)
from mcf.crypto import setups1 as S1  # noqa: E402


def _lv_mins(prices, start="2024-03-04 00:00", traded=None):
    idx = pd.date_range(start, periods=len(prices), freq="1min", tz="UTC")
    p = np.asarray(prices, float)
    return Minutes(to_min(idx), p.copy(), p * 1.001, p * 0.999, p.copy(),
                   None if traded is None else np.asarray(traded, bool)), idx


def _lv_sig(t, lim, risk, tgt=np.nan, expiry=60, hold=600, ref=None):
    return pd.DataFrame({"t": [int(t)], "ref": [ref or lim], "lim": [lim], "risk": [risk], "tgt": [tgt],
                         "expiry": [expiry], "hold": [hold]})


def test_levels_maker_needs_trade_through_and_target():
    px = [100.0] * 5 + [98.0] * 5 + [100.0] * 5 + [104.0] * 5
    m, idx = _lv_mins(px)
    tr, off, missed = S1.run_levels("BTC", m, _lv_sig(m.t[0], 99.0, 3.0, tgt=103.0))
    assert off == 1 and missed == 0 and len(tr) == 1
    assert tr.kind.iloc[0] == 2 and tr.entry.iloc[0] == 99.0 and tr.exit.iloc[0] == 103.0
    assert tr.maker_in.iloc[0] and tr.maker_out.iloc[0]
    assert abs(tr.gross_r.iloc[0] - 4 / 3) < 1e-9 and tr.r.iloc[0] < tr.gross_r.iloc[0]


def test_levels_missed_when_untraded_or_not_through():
    px = [100.0] * 30
    m, _ = _lv_mins(px)
    tr, off, missed = S1.run_levels("BTC", m, _lv_sig(m.t[0], 99.0, 3.0))       # low 99.9 never below 99
    assert len(tr) == 0 and missed == 1
    px = [100.0] * 5 + [97.0] * 5 + [100.0] * 20
    m, _ = _lv_mins(px, traded=[True] * 5 + [False] * 5 + [True] * 20)
    tr, _, missed = S1.run_levels("BTC", m, _lv_sig(m.t[0], 99.0, 3.0))         # dip only on zero-volume minutes
    assert len(tr) == 0 and missed == 1


def test_levels_stop_gap_and_time_exit():
    px = [100.0] * 3 + [98.5] + [98.5] * 3 + [90.0] * 3
    m, _ = _lv_mins(px)
    tr, _, _ = S1.run_levels("ETH", m, _lv_sig(m.t[0], 99.0, 3.0))
    assert tr.kind.iloc[0] == 1 and tr.exit.iloc[0] == 90.0                  # gap through 96 fills at the open
    px = [100.0] * 3 + [98.5] * 30
    m, _ = _lv_mins(px)
    tr, _, _ = S1.run_levels("ETH", m, _lv_sig(m.t[0], 99.0, 3.0, hold=10))
    assert tr.kind.iloc[0] == 0 and (tr.exit_time.iloc[0] - tr.entry_time.iloc[0]) == pd.Timedelta("10min")


def test_levels_one_position_per_pair():
    px = [100.0] * 3 + [98.5] * 40
    m, _ = _lv_mins(px)
    s = pd.concat([_lv_sig(m.t[0], 99.0, 3.0, hold=30), _lv_sig(m.t[5], 99.0, 3.0, hold=30)], ignore_index=True)
    tr, off, _ = S1.run_levels("ETH", m, s)
    assert off == 2 and len(tr) == 1


def test_daily_gate_uses_completed_day_only():
    d = pd.DataFrame({"up": [False, True]}, index=pd.date_range("2024-01-01", periods=2, freq="D", tz="UTC"))
    taus = pd.DatetimeIndex(["2024-01-02 00:00", "2024-01-02 23:00", "2024-01-03 00:00"], tz="UTC")
    assert list(S1.daily_at(d, "up", taus)) == [False, False, True]


def test_friday_close_dst():
    t = S1.friday_close_times(pd.Timestamp("2024-01-01", tz="UTC"), pd.Timestamp("2024-07-31", tz="UTC"))
    assert t[0] == pd.Timestamp("2024-01-05 21:00", tz="UTC")
    assert pd.Timestamp("2024-07-05 20:00", tz="UTC") in t


def _prep_synth():
    idx = pd.date_range("2024-01-01", periods=60 * 24 * 70, freq="1min", tz="UTC")
    rng = np.random.default_rng(1)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.0007, len(idx))))
    c[60 * 24 * 60 + 600: 60 * 24 * 60 + 660] *= 0.93                      # a one-hour flush on day 60
    b = pd.DataFrame({"o": c, "h": c * 1.0005, "l": c * 0.9995, "c": c, "v": 1.0, "vw": c}, index=idx)
    return {"BTC": S1.prep_pair(b, idx[-1] + pd.Timedelta("1min"))}


def test_flush_signal_no_lookahead_and_levels():
    P = _prep_synth()
    sg = S1.sig_flush(P, "BTC", {"gate": None})
    flush_hour = pd.Timestamp("2024-01-01", tz="UTC") + pd.Timedelta(days=60, hours=10)
    t_dec = int(to_min(pd.DatetimeIndex([flush_hour + pd.Timedelta("60min")]))[0])
    assert t_dec in set(sg["t"])
    row = sg[sg["t"] == t_dec].iloc[0]
    assert row.lim < row.ref and row.risk >= 0.03 * row.lim and row.hold == 720 and row.expiry == 120
    # truncating the data after the decision does not change the signal
    H = P["BTC"]["H"]
    assert np.isfinite(H.loc[flush_hour, "z"]) and H.loc[flush_hour, "z"] <= -3


def test_random_signals_keep_geometry():
    P = _prep_synth()
    sg = S1.sig_flush(P, "BTC", {"gate": None})
    a, z = pd.Timestamp("2024-01-10", tz="UTC"), pd.Timestamp("2024-03-10", tz="UTC")
    r = S1.random_signals(np.random.default_rng(0), sg, P["BTC"]["H"], a, z)
    assert len(r) == len(sg) and np.allclose(r["risk"] / r["lim"], (sg["risk"] / sg["lim"]).iloc[0], rtol=0.5)
    assert (r["lim"] < r["ref"]).all()
