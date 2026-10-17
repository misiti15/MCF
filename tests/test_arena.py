"""Arena (mcf/research/arena): point-in-time correctness of the indicator library on synthetic bars, live-frame parity,
the combiner and the lab-module writer. Educational only - not financial advice."""
import importlib.util
from datetime import date

import numpy as np
import pandas as pd
import pytest

from mcf.research.arena import combine as CB
from mcf.research.arena.indicators import FRAME_COLS, INDICATORS, compute, tod_slot

TODS = [h * 100 + m for h in range(9, 16) for m in range(0, 60, 5) if 935 <= h * 100 + m <= 1555]


def _synthetic(symbols=("AAA", "BBB", "SPY", "QQQ", "IWM"), days=(date(2026, 1, 5), date(2026, 1, 6)), seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for s in symbols:
        px = 50.0 + rng.uniform(0, 50)
        for d in days:
            for t in TODS:
                px *= 1 + rng.normal(0, 0.003)
                rows.append({"symbol": s, "date": d, "tod": t, "close": px, "high": px * (1 + abs(rng.normal(0, 0.002))),
                             "low": px * (1 - abs(rng.normal(0, 0.002)))})
    df = pd.DataFrame(rows)
    for c in FRAME_COLS:
        if c not in df:
            df[c] = rng.normal(0, 1, len(df))
    df["atr_d"] = df["close"] * 0.02
    df["fromOpen"] = rng.normal(0, 1, len(df))
    df["gap"] = rng.normal(0, 1, len(df))
    df["dist_hod_atr"] = np.abs(rng.normal(0, 0.3, len(df)))
    df["dist_hod_atr"] = np.where(rng.uniform(size=len(df)) < 0.1, 0.0, df["dist_hod_atr"])
    df["dist_lod_atr"] = np.abs(rng.normal(0, 0.3, len(df)))
    df["vwapDistPct"] = rng.normal(0, 0.5, len(df))
    return df.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)


def test_registry_size_and_families():
    assert len(INDICATORS) >= 60
    assert {i.family for i in INDICATORS.values()} == {"mom", "mr", "trend", "vol", "flow", "struct", "ctx", "time"}


def test_slots_and_out_of_range_rows_are_nan():
    assert list(tod_slot([945, 950, 955, 1500, 1505])) == [-1, 0, 1, 62, -1]
    df = _synthetic()
    x = compute(df)
    out = ~df["tod"].between(950, 1500).to_numpy()
    assert np.isnan(x.to_numpy()[out]).all()
    assert x.shape[1] == len(INDICATORS)


def test_point_in_time_no_future_rows():
    """Each row's value equals the value computed when every later row (all symbols) is removed."""
    df = _synthetic()
    full = compute(df)
    key = pd.to_datetime(df["date"].astype(str)) + pd.to_timedelta(df["tod"] // 100 * 60 + df["tod"] % 100, unit="m")
    for cut_d, cut_t in ((date(2026, 1, 5), 950), (date(2026, 1, 5), 1105), (date(2026, 1, 6), 1000), (date(2026, 1, 6), 1340)):
        ck = pd.Timestamp(str(cut_d)) + pd.Timedelta(minutes=cut_t // 100 * 60 + cut_t % 100)
        keep = (key <= ck).to_numpy()
        part = compute(df[keep])
        at = keep & (key == ck).to_numpy()
        a = full.to_numpy()[at]
        b = part.loc[df.index[at]].to_numpy()
        np.testing.assert_allclose(a, b, rtol=1e-6, atol=1e-6, equal_nan=True)


def test_changing_future_bars_does_not_change_past_values():
    df = _synthetic()
    x0 = compute(df)
    df2 = df.copy()
    late = df2["tod"] > 1200
    for c in ("close", "high", "low", "vwapDistPct", "fromOpen", "dist_hod_atr"):
        df2.loc[late, c] = df2.loc[late, c] * 3.7 + 1
    x1 = compute(df2)
    early = (~late).to_numpy()
    np.testing.assert_allclose(x0.to_numpy()[early], x1.to_numpy()[early], rtol=1e-6, atol=1e-6, equal_nan=True)


def test_live_frame_parity_one_symbol():
    """The live LabStrategy frame (DatetimeIndex, no symbol/date columns, 09:35.. bars) gives the history values."""
    df = _synthetic()
    one = df[(df["symbol"] == "AAA") & (df["date"] == date(2026, 1, 6))].copy()
    hist = compute(df)
    idx = pd.DatetimeIndex([pd.Timestamp("2026-01-06 00:00") + pd.Timedelta(minutes=int(t // 100 * 60 + t % 100) - 5)
                            for t in one["tod"]], tz="America/New_York")
    live = one.drop(columns=["symbol", "date"]).set_index(idx)
    names = [n for n, i in INDICATORS.items() if i.live]
    lx = compute(live, names=names, context=False)
    np.testing.assert_allclose(hist.loc[one.index, names].to_numpy(), lx.to_numpy(), rtol=1e-6, atol=1e-6, equal_nan=True)


def test_known_values():
    df = _synthetic(symbols=("AAA",), days=(date(2026, 1, 5),))
    c = df["close"].to_numpy()
    x = compute(df, names=["ret1", "or_high_dist_atr", "tod_min", "dow"])
    i = int(np.flatnonzero(df["tod"].to_numpy() == 1000)[0])
    assert x["ret1"].iloc[i] == pytest.approx((c[i] / c[i - 1] - 1) * 100, rel=1e-5)
    assert np.isnan(x["ret1"].iloc[int(np.flatnonzero(df["tod"].to_numpy() == 950)[0])])     # 09:45 bar not used
    i950 = int(np.flatnonzero(df["tod"].to_numpy() == 950)[0])
    orh = c[i950] + df["dist_hod_atr"].iloc[i950] * df["atr_d"].iloc[i950]
    assert x["or_high_dist_atr"].iloc[i] == pytest.approx((c[i] - orh) / df["atr_d"].iloc[i], rel=1e-4)
    assert x["tod_min"].iloc[i] == 30 and x["dow"].iloc[i] == 0
    up = pd.DataFrame({"tod": [950, 955, 1000, 1005], "close": [1.0, 2, 3, 4], "high": [1.0, 2, 3, 4], "low": [1.0, 2, 3, 4],
                       "atr_d": 1.0, "fromOpen": 0.0, "gap": 0.0, "vwapDistPct": 0.0, "dist_hod_atr": 0.0, "dist_lod_atr": 0.0})
    assert compute(up, names=["rsi2"])["rsi2"].iloc[-1] == 100


def _arena(df):
    rng = np.random.default_rng(1)
    A = df[df["tod"].between(950, 1500)].copy()
    ind = compute(A)
    A = pd.concat([A[["symbol", "date", "tod"]], ind], axis=1)
    for o in ("long_t1s1", "short_t1s1"):
        A[f"r_{o}"] = rng.normal(0.05, 1, len(A))
        A[f"c_{o}"] = 0.0
    A["split"] = np.where(pd.to_datetime(A["date"].astype(str)) < "2026-01-06", "train", "valid")
    return A.reset_index(drop=True)


def test_combine_and_module_roundtrip(tmp_path):
    df = _synthetic()
    A = _arena(df)
    conds = [("rsi2", ">=", 50.0), ("day_pos", "between", (0.2, 0.9))]
    reg = pd.DataFrame({"regime": ["up", "down"]}, index=[date(2026, 1, 5), date(2026, 1, 6)])
    res = CB.evaluate_combo(A, conds, "long", "t1s1", window=(950, 1500), n_lineage=100, regimes=reg)
    t = CB.trades(A, conds, "long", "t1s1", (950, 1500))
    assert res["all"]["n"] == len(t) == t.groupby(["symbol", "date"]).ngroups
    assert res["t_required"] == pytest.approx(np.sqrt(2 * np.log(100)), abs=1e-3)
    assert res["quality_pass"] is False                     # tiny synthetic sample cannot pass n >= 200
    p = CB.write_module(conds, "long", "t1s1", (950, 1500), tmp_path / "AR-test.py", name="AR-test", doc="unit test")
    spec = importlib.util.spec_from_file_location("ar_test", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.SIDE == "long" and mod.GEOM == "t1s1" and len(mod.LAYERS) == 3
    one = df[(df["symbol"] == "BBB") & (df["date"] == date(2026, 1, 6))]
    idx = pd.DatetimeIndex([pd.Timestamp("2026-01-06") + pd.Timedelta(minutes=int(t // 100 * 60 + t % 100) - 5)
                            for t in one["tod"]], tz="America/New_York")
    live = one.drop(columns=["symbol", "date"]).set_index(idx)
    m_live = mod.mask(live)
    hist = A[(A["symbol"] == "BBB") & (A["date"] == date(2026, 1, 6))]
    m_hist = CB.combo_mask(hist, conds, (950, 1500))
    assert np.array_equal(m_live[one["tod"].between(950, 1500).to_numpy()], m_hist)
    assert not m_live[~one["tod"].between(950, 1500).to_numpy()].any()
    with pytest.raises(ValueError):
        CB.write_module([("breadth_vwap", ">=", 0.6)], "long", "t1s1", (950, 1500), tmp_path / "x.py", name="x")


def test_screen_cell_stats_match_gates_summary():
    from mcf.research import gates
    from mcf.research.arena.screen import bins_for, cell_stats, first_rows

    rng = np.random.default_rng(3)
    n = 3000
    cell = rng.integers(0, 3, n)
    day = rng.integers(0, 40, n)
    R = rng.normal(0.02, 1, (n, 2))
    st = cell_stats(cell, day, np.zeros(n, int), np.zeros(n, int), R, R - 0.01)
    for c in range(3):
        s = gates.summary(pd.DataFrame({"date": day[cell == c], "r": R[cell == c, 0]}))
        assert st["exp"][c, 0] == pytest.approx(s["exp_r"], abs=1e-4)
        assert st["t"][c, 0] == pytest.approx(s["t"], abs=0.01)
        assert st["exc"][c, 0] == pytest.approx(s["exp_r"] - 0.01, abs=1e-4)
    sd = np.array([0, 0, 0, 1, 1, 2])
    assert list(first_rows(sd, np.array([False, True, True, True, False, False]))) == [1, 3]
    v = np.r_[np.arange(100, dtype=float), np.nan]
    labs = [b[0] for b in bins_for(v, "cont")]
    assert labs[:2] == ["d01", "d02"] and "ge_q95" in labs and len(labs) == 14
