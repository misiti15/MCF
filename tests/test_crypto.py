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
