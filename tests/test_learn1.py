"""LEARN1 (owner 2026-11-17): new point-in-time inputs never look ahead, the live model extension keeps today's guesses,
missed sessions are learned / appended, and the daily skill metric. Synthetic data only, no network.
Educational only - not financial advice."""
import json

import numpy as np
import pandas as pd
import pytest

from mcf.hunch import data as D
from mcf.hunch import learners as Lr
from mcf.hunch import live as LV
from mcf.hunch import replay as R
from mcf.report import compass_cond as CC
from mcf.report import compass_live as CL
from mcf.report import skill as SK

from tests.test_hunch import DATES, _fake_bars, _minutes, _seed_model, cache  # noqa: F401


def test_extra_inputs_never_look_ahead(tmp_path):
    """Changing every 1-min bar of EVERY name after bar b's close leaves all LEARN1 inputs at bars <= b unchanged."""
    syms = ["SPY", "QQQ", "SMH", "IBIT", "AAA", "BBB"]
    full = {s: _minutes(DATES[:6], seed=i, start=50 + 7 * i) for i, s in enumerate(syms)}
    day, b = DATES[4], 40
    cut = pd.Timestamp(f"{day} 09:30", tz=D.TZ) + pd.Timedelta(minutes=3 * (b + 1))
    pert = {}
    for s, m in full.items():
        m2 = m.copy()
        late = m2.index >= cut
        m2.loc[late, ["open", "high", "low", "close"]] *= 0.71
        m2.loc[late, "volume"] *= 13
        pert[s] = m2
    p1 = D.build_panel(["AAA", "BBB", "SPY"], loader=full.get)
    p2 = D.build_panel(["AAA", "BBB", "SPY"], loader=pert.get)
    d = pd.Timestamp(day).date()
    upto = ((p1["date"] < d) | ((p1["date"] == d) & (p1["b"] <= b))).to_numpy()
    for k in D.EXTRA:
        assert k in p1.columns
        pd.testing.assert_series_equal(p1.loc[upto, k].reset_index(drop=True), p2.loc[upto, k].reset_index(drop=True),
                                       check_names=False)
    assert p1["breadth_open"].between(0, 1).all() and p1["vol_tod"].notna().any() and p1["roll_spread"].dropna().ge(0).all()
    assert D.ALL_FEATURES[:len(D.FEATURES)] == D.FEATURES and len(D.ALL_FEATURES) == len(D.FEATURES) + 5


def test_extend_model_keeps_guesses_then_learns(cache, tmp_path, monkeypatch):
    seed = _seed_model(cache, tmp_path, monkeypatch)
    m = LV.load_model(seed)
    m2 = LV.extend_model(m, D.ALL_FEATURES)
    assert m2["feats"] == D.ALL_FEATURES and m["feats"] == D.FEATURES   # input unchanged
    bars = _fake_bars(cache, m["symbols"])
    day = DATES[-1]
    bars.refresh(pd.Timestamp(f"{day} 10:30:40", tz=D.TZ))
    panel = D.build_panel(m["symbols"], loader=bars.loader)
    now = pd.Timestamp(f"{day} 10:30:40", tz=D.TZ)
    g1, _, _ = LV.walk_day(m, panel, day, now)
    g2, after, _ = LV.walk_day(m2, panel, day, now)
    first = g1["b"] == g1["b"].min()   # the first guess of the day: same model, zero weight on the new inputs
    np.testing.assert_allclose(g1.loc[first, "p_pooled"], g2.loc[first, "p_pooled"])
    np.testing.assert_allclose(g1.loc[first, "p_own"], g2.loc[first, "p_own"])
    F = len(D.FEATURES)
    assert np.any(after["pooled"].w[F:F + 5] != 0) and after["pooled"].sc.n[F:].sum() > 0   # learning the new inputs
    p = tmp_path / "x.npz"
    LV.save_model(after, p, day)
    assert LV.load_model(p)["feats"] == D.ALL_FEATURES


def test_catch_up_learns_a_missed_session(cache, tmp_path, monkeypatch):
    seed = _seed_model(cache, tmp_path, monkeypatch)
    m = LV.extend_model(LV.load_model(seed), D.ALL_FEATURES)
    missed = m["last_date"]
    m = {**m, "last_date": DATES[-3]}            # pretend the session after DATES[-3] was never finalised
    bars = _fake_bars(cache, m["symbols"])
    today = DATES[-1]
    bars.refresh(pd.Timestamp(f"{today} 09:52:00", tz=D.TZ))
    panel = D.build_panel(m["symbols"], loader=bars.loader)
    m2, days = LV.catch_up(m, panel, today)
    assert days == [missed] and m2["last_date"] == missed and m2["tot_n"] > m["tot_n"]
    assert LV.catch_up(m2, panel, today)[1] == []   # nothing left to learn; today is never learned early


def _spy_day(day, drift, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.Timestamp(f"{day} 09:30", tz=CL.NY) + pd.to_timedelta(np.arange(390), "min")
    c = 100 * np.exp(np.cumsum(rng.normal(drift, 0.0004, 390)))
    return pd.DataFrame({"open": np.r_[100, c[:-1]], "high": c * 1.0002, "low": c * 0.9998, "close": c,
                         "volume": np.full(390, 1e5)}, index=idx)


def test_compass_cond_catches_up_missed_sessions(tmp_path):
    days = [str(d.date()) for d in pd.bdate_range("2026-11-09", "2026-11-13")]
    out = tmp_path
    for d in days[:2]:
        CC.update(out, d, spy_fn=lambda x, log=None: _spy_day(x, 0.0001), log=lambda *a: None)
    # 11-11 and 11-12 were missed; the run for 11-13 appends them first
    assert CC.missing_days(out, days[-1]) == days[2:4]
    n = CC.catch_up(out, days[-1], spy_fn=lambda x, log=None: _spy_day(x, -0.0001), log=lambda *a: None)
    obs = pd.read_csv(out / "compass" / "cond_obs.csv", dtype={"date": str})
    assert n == 2 * len(CC.MARKS) and set(days[:4]) <= set(obs.date) and CC.missing_days(out, days[-1]) == []


def test_compass_extras_are_recorded_not_voted():
    day = "2026-11-10"
    bars = {s: _spy_day(day, 0.0002 * (1 if i % 2 else -1), seed=i) for i, s in
            enumerate(["SPY", "QQQ", "IWM", "AAA", "BBB", "CCC", "XLK", "XLF"])}
    now = pd.Timestamp(f"{day} 12:01", tz=CL.NY)
    rows = CL.compute(bars, day, now, ["AAA", "BBB", "CCC"])
    r = rows[-1]
    for k in CL.EXTRA:
        assert k in r and k in CL.COLS
    assert 0 <= r["breadth_vwap"] <= 1 and 0 <= r["sector_up"] <= 1 and np.isnan(rows[0]["breadth_15"] or np.nan)
    # point in time: later bars do not change a mark's extras
    cut = pd.Timestamp(f"{day} 11:00", tz=CL.NY)
    b2 = {s: b.assign(close=np.where(b.index >= cut, b.close * 1.3, b.close)) for s, b in bars.items()}
    r1 = [x for x in rows if x["T"] == "11:00"][0]
    r2 = [x for x in CL.compute(b2, day, now, ["AAA", "BBB", "CCC"]) if x["T"] == "11:00"][0]
    assert all(r1[k] == r2[k] for k in CL.EXTRA) and r1["votes"] == r2["votes"]


def test_day_skill_and_ci():
    y = np.array([1, 1, 0, 1.0])
    r = SK._day(np.array([0.9, 0.8, 0.2, 0.7]), y, np.full(4, 0.4))
    assert r["hit"] == 1.0 and r["base_hit"] == 0.25 and r["skill_hit"] == 0.75
    assert r["brier"] == pytest.approx(np.mean([0.01, 0.04, 0.04, 0.09])) and r["bss"] > 0
    flat = SK._day(np.full(4, 0.4), y, np.full(4, 0.4))
    assert flat["skill_hit"] == 0 and flat["bss"] == pytest.approx(0)
    c = SK.ci([0.01, 0.02, 0.015, 0.012])
    assert c["lo"] > 0 and SK.verdict(c) == "skill above base"
    assert SK.verdict(SK.ci([0.01, -0.02, 0.015])) == "no skill shown (CI includes 0)"
    assert SK.verdict(SK.ci([0.01])) == "too few sessions"


def test_hunch_skill_from_guess_files(tmp_path):
    g = tmp_path / "guesses"
    g.mkdir()
    rng = np.random.default_rng(0)
    for d in ("2026-11-19", "2026-11-20", "2026-11-21"):
        y = rng.integers(0, 2, 400).astype(float)
        p = np.clip(0.5 + (y - 0.5) * 0.2 + rng.normal(0, 0.05, 400), 0, 1)   # informative
        pd.DataFrame({"outcome": y, "backfill": 0, "p_pooled": p, "p_own": np.full(400, 0.5), "base_rate": 1}
                     ).to_csv(g / f"{d}.csv", index=False)
    js = SK.build(tmp_path, None, now="test")
    m = js["models"]["hunch_pooled"]
    assert m["since_learn1"]["sessions"] == 3 and m["verdict_since_learn1"] == "skill above base"
    assert m["today"]["date"] == "2026-11-21" and m["days"][0]["running"] is not None
    assert js["models"]["hunch_own"]["since_learn1"]["bss"]["mean"] <= 0.01
    assert "Educational only" in js["disclaimer"] and json.dumps(js)


def test_compass_cal_is_walk_forward():
    days = [str(d.date()) for d in pd.bdate_range("2026-06-01", periods=70)]
    obs = pd.DataFrame([r for i, d in enumerate(days) for r in CC.day_obs(_spy_day(d, 0.0001 * (1 if i % 3 else -1), i), d, None)])
    rows = SK.compass_cal_days(obs, min_prior=60)
    assert [r["date"] for r in rows] == days[60:] and all(r["source"] == "replay" for r in rows)
    # changing a later session never changes an earlier session's score
    obs2 = obs.copy()
    last = obs2.date == days[-1]
    obs2.loc[last, "close"] = obs2.loc[last, "close"] * 0.9
    rows2 = SK.compass_cal_days(obs2, min_prior=60)
    assert rows[:-1] == rows2[:-1]


def test_skill_module_is_display_only():
    import inspect

    src = inspect.getsource(SK)
    for bad in ("TradingClient", "submit_order", "mcf.execution", "config/"):
        assert bad not in src
