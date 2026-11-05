"""Hunch (research-only next-bar guesser): bars, strict no-look-ahead, locked block, scoring. Synthetic data only."""
import numpy as np
import pandas as pd
import pytest

from mcf.hunch import data as D
from mcf.hunch import learners as Lr
from mcf.hunch import metrics as M
from mcf.hunch import replay as R


def _minutes(dates, seed=0, start=100.0):
    rng = np.random.default_rng(seed)
    idx = []
    for d in dates:
        t0 = pd.Timestamp(f"{d} 09:30", tz=D.TZ)
        idx += list(t0 + pd.to_timedelta(np.arange(390), "min"))
    idx = pd.DatetimeIndex(idx)
    c = start * np.exp(np.cumsum(rng.normal(0, 0.001, len(idx))))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.0005, len(idx)))
    lo = np.minimum(o, c) * (1 - rng.uniform(0, 0.0005, len(idx)))
    v = rng.integers(100, 5000, len(idx)).astype(float)
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c, "volume": v}, index=idx)


DATES = [str(d.date()) for d in pd.bdate_range("2026-03-02", periods=7)]


@pytest.fixture()
def cache(tmp_path):
    for i, s in enumerate(["SPY", "QQQ", "SMH", "IBIT", "AAA"]):
        _minutes(DATES, seed=i, start=100 + 10 * i).to_parquet(tmp_path / f"{s}.parquet")
    return tmp_path


def test_bars3_aggregates_1min():
    m1 = _minutes(DATES[:1])
    b = D.bars3(m1)
    assert len(b) == D.N_BUCKETS
    first = m1.iloc[:3]
    r = b.iloc[0]
    assert r["o"] == first["open"].iloc[0] and r["c"] == first["close"].iloc[-1]
    assert r["h"] == first["high"].max() and r["l"] == first["low"].min() and r["v"] == first["volume"].sum()
    assert b["filled"].sum() == 0


def test_features_never_look_ahead():
    """Changing every 1-min bar after bar b's close leaves every feature at bars <= b unchanged."""
    m1 = _minutes(DATES[:3])
    base = D.own_features(D.bars3(m1))
    day, b = pd.Timestamp(DATES[1]).date(), 40
    cut = pd.Timestamp(f"{DATES[1]} 09:30", tz=D.TZ) + pd.Timedelta(minutes=3 * (b + 1))
    m2 = m1.copy()
    later = m2.index >= cut
    m2.loc[later, ["open", "high", "low", "close"]] *= 1.37
    m2.loc[later, "volume"] *= 9
    pert = D.own_features(D.bars3(m2))
    upto = (base["date"] < day) | ((base["date"] == day) & (base["b"] <= b))
    cols = [f for f in D.FEATURES if f in base.columns] + ["atr", "range_med20"]
    pd.testing.assert_frame_equal(base.loc[upto, cols], pert.loc[upto, cols])
    assert not np.allclose(base.loc[~upto, "c"], pert.loc[~upto, "c"])


def _panel(cache):
    return D.build_panel(["SPY", "QQQ", "AAA"], cache=cache)


def test_label_is_next_bar_only(cache):
    p = _panel(cache).sort_values(["symbol", "date", "b"]).reset_index(drop=True)
    y = M.label(p, "M1")
    g = p.groupby(["symbol", "date"])
    expect = (g["c"].shift(-1) > p["c"]).astype(float).to_numpy()
    ok = np.isfinite(y)
    assert np.array_equal(y[ok], expect[ok])
    assert np.isnan(y[p["b"].to_numpy() == D.N_BUCKETS - 1]).all()  # the last bar has no next bar in the session
    assert "M0" in M.TRIVIAL and "M0" not in M.LADDER and M.ACTIVE == "M1"


def test_replay_never_uses_the_future(cache, monkeypatch):
    """Guesses up to step k are identical when every answer from step k on and every feature after step k change."""
    monkeypatch.setattr(R, "WARMUP_SESS", 2)
    monkeypatch.setattr(Lr, "REFIT_SESS", 2)
    p = _panel(cache)
    g = R.make_grid(p, "M1")
    cols = list(range(len(D.FEATURES)))
    a = R._walk(g, cols, True)
    k = int(np.flatnonzero(g.steps["sess"].to_numpy() == 4)[30])
    g2 = R.make_grid(p, "M1")
    rng = np.random.default_rng(1)
    g2.y[k:] = np.where(np.isfinite(g2.y[k:]), rng.integers(0, 2, g2.y[k:].shape), np.nan)
    g2.X[k + 1:] = rng.normal(size=g2.X[k + 1:].shape).astype(np.float32)
    b = R._walk(g2, cols, True)
    assert np.array_equal(a["P"][: k + 1], b["P"][: k + 1])
    assert a["P"].shape[2] == 3 + len(D.FEATURES)


def test_guess_window_and_warmup(cache):
    g = R.make_grid(_panel(cache), "M1")
    st = g.steps
    assert st["b"].min() == D.GUESS_FIRST and st["b"].max() == D.GUESS_LAST  # bars closing 09:51 .. 15:51
    first = st["date"] == st["date"].min()
    assert not g.mask[first.to_numpy()].any()  # the first session of a segment is an indicator warm-up


def test_locked_block_is_never_read(tmp_path):
    dates = ["2024-10-31", "2024-11-01", "2025-02-28", "2025-03-03"]
    _minutes(dates).to_parquet(tmp_path / "ZZZ.parquet")
    df = D.load_1min("ZZZ", tmp_path)
    days = set(str(d) for d in df.index.date)
    assert days == {"2024-10-31", "2025-03-03"}
    assert list(D.segment_of(["2024-10-31", "2025-03-03"])) == [0, 1]


def test_stats_and_bar():
    assert R.bar_for(1) == 1.5 and abs(R.bar_for(138) - np.sqrt(2 * np.log(138))) < 1e-12
    h = np.array([1, 0, 1, 1, 0, 1.0])
    day = np.array([1, 1, 2, 2, 3, 3])
    p, se, n = R.day_stats(h, day)
    assert p == pytest.approx(4 / 6) and n == 6 and se > 0
    r = R.paired(np.array([1, 1, 0, 1.0]), np.full(4, 0.5), np.array([1, 1, 2, 2]))
    assert r["diff"] == pytest.approx(0.25)


def test_pooled_logreg_learns_a_signal():
    rng = np.random.default_rng(0)
    m = Lr.LogReg(2, tod_col=1, n_groups=3)
    for _ in range(400):
        X = np.c_[rng.normal(size=30), rng.uniform(3, 390, 30)]
        y = (X[:, 0] + 0.3 * rng.normal(size=30) > 0).astype(float)
        m.update(X, y, rng.integers(0, 3, 30))
    X = np.c_[rng.normal(size=2000), rng.uniform(3, 390, 2000)]
    assert ((m.predict(X, rng.integers(0, 3, 2000))) == (X[:, 0] > 0)).mean() > 0.85


# ------------------------------------------------------------------ live shadow (no network: fake bars + fake clock)
from mcf.hunch import live as LV  # noqa: E402


def _seed_model(cache, tmp_path, monkeypatch):
    monkeypatch.setattr(R, "WARMUP_SESS", 2)
    monkeypatch.setattr(Lr, "REFIT_SESS", 2)
    p = D.build_panel(["SPY", "QQQ", "AAA"], cache=cache)
    p = p[p["date"].astype(str) < DATES[-1]]  # the replay ends the day before the "live" day
    g = R.make_grid(p, "M1")
    res = R._walk(g, list(range(len(D.FEATURES))), True, diag=False)
    path = tmp_path / "seed.npz"
    R.save_state(res, path, "M1", g.steps["date"].iloc[-1])
    return path


def _fake_bars(cache, symbols):
    full = {s: pd.read_parquet(cache / f"{s}.parquet") for s in set(symbols) | set(D.CONTEXT)}

    def fetch(syms, start, end):  # only bars that have closed by `end` exist, like the live feed
        return {s: full[s][(full[s].index >= start) & (full[s].index + pd.Timedelta(minutes=1) <= end)]
                for s in syms if s in full}
    return LV.Bars(symbols, fetch=fetch)


def test_live_guesses_never_change_with_later_data(cache, tmp_path, monkeypatch):
    seed = _seed_model(cache, tmp_path, monkeypatch)
    model = LV.load_model(seed)
    day = DATES[-1]
    bars = _fake_bars(cache, model["symbols"])
    early = pd.Timestamp(f"{day} 11:00:40", tz=D.TZ)
    bars.refresh(early)
    g1, _, done1 = LV.walk_day(model, D.build_panel(model["symbols"], loader=bars.loader), day, early)
    late = pd.Timestamp(f"{day} 16:01:00", tz=D.TZ)
    bars.refresh(late)
    g2, m2, done2 = LV.walk_day(model, D.build_panel(model["symbols"], loader=bars.loader), day, late)
    assert not done1 and done2 and len(g2) > len(g1) > 0
    k = ["b", "symbol"]
    a = g1.set_index(k)[["p_pooled", "p_own", "guess_pooled", "guess_own"]]
    b = g2.set_index(k).loc[a.index, ["p_pooled", "p_own", "guess_pooled", "guess_own"]]
    pd.testing.assert_frame_equal(a, b, check_dtype=False)
    assert g1["b"].max() == 29  # 11:00:40 -> the last closed bar is b = 29 (closes 11:00:00, + the 35 s lag)
    assert m2["tot_n"] > model["tot_n"]  # it learned from today's scored guesses
    assert model["pooled"].rows == LV.load_model(seed)["pooled"].rows  # walk_day never mutates its input


def test_live_loop_writes_frozen_guesses_and_final_state(cache, tmp_path, monkeypatch):
    seed = _seed_model(cache, tmp_path, monkeypatch)
    model = LV.load_model(seed)
    day = DATES[-1]
    t = {"now": pd.Timestamp(f"{day} 15:20:00", tz=D.TZ)}  # a late start (restart): earlier bars are recomputed

    def sleep(sec):
        t["now"] += pd.Timedelta(seconds=max(sec, 1))

    state = tmp_path / "state"
    why = LV.run_live(state, seed, bars=_fake_bars(cache, model["symbols"]), clock=lambda: t["now"], sleep=sleep,
                      max_minutes=1000)
    assert why == "day complete"
    g = pd.read_csv(state / "guesses" / f"{day}.csv")
    assert set(g["symbol"]) <= set(model["symbols"]) and g["b"].between(D.GUESS_FIRST, D.GUESS_LAST).all()
    assert g["outcome"].notna().mean() > 0.9 and (state / "scoreboard.md").exists()
    assert g.loc[g["b"] < 100, "backfill"].all() and not g.loc[g["b"] > 120, "backfill"].any()  # late start at 15:20
    sb = pd.read_csv(state / "scoreboard.csv")
    assert sb["scored"].iloc[0] < g["outcome"].notna().sum()
    assert LV.load_model(state / "state" / "model.npz")["last_date"] == day
    assert "Educational only" in (state / "scoreboard.md").read_text()
    # second start the same day: already finalized, nothing redone
    assert "already finalized" in LV.run_live(state, seed, bars=_fake_bars(cache, model["symbols"]),
                                              clock=lambda: t["now"], sleep=sleep)


def test_merge_frozen_keeps_the_first_guess():
    now = pd.Timestamp("2026-11-05 10:00:40", tz=D.TZ)
    old = pd.DataFrame({"date": ["2026-11-05"], "b": [6], "bar_close": ["09:51"], "symbol": ["SPY"],
                        "guessed_at": ["09:51:35"], "backfill": [0], "p_pooled": [0.6], "guess_pooled": [1],
                        "p_own": [0.4], "guess_own": [0], "same_last": [1.0], "mom20": [0.0], "base_rate": [0],
                        "outcome": [np.nan]})
    new = old.assign(p_pooled=0.3, guess_pooled=0, outcome=1.0, guessed_at="x")
    out = LV.merge_frozen(old, new, now)
    r = out.iloc[0]
    assert r["guess_pooled"] == 1 and r["guessed_at"] == "09:51:35" and r["backfill"] == 0 and r["hit_pooled"] == 1.0 and r["hit_own"] == 0.0


def test_live_imports_no_trading_code():
    import inspect

    src = inspect.getsource(LV)
    for bad in ("TradingClient", "submit_order", "mcf.execution", "config/"):
        assert bad not in src.replace("never touches trading config", "")
