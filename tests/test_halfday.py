"""Half-day / holiday handling outside the trading runner (inspector 11-27 #2, #3 + the assignments holiday finding):
Hunch, Compass and compass_cond end a 13:00 early-close session at the calendar close (no after-hours bars, no marks
after the close), past half days are purged from the compass_cond seed, and assignments.next_session skips holidays.
Synthetic half-day fixtures only. Educational only - not financial advice."""
import gzip
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from mcf.data import bars as B
from mcf.execution import market_calendar as mc
from mcf.hunch import data as D
from mcf.report import assignments as A
from mcf.report import compass_cond as cc
from mcf.report import compass_live as cl

HALF = "2025-11-28"            # a past NYSE 13:00 early close (offline list; no calendar call for a past day)
NY = "America/New_York"


def _day_1min(day, end="15:59", start=100.0, seed=0):
    """1-min bars 09:30..`end` (an Alpaca-style half day carries after-hours prints to 15:59)."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range(f"{day} 09:30", f"{day} {end}", freq="1min", tz=NY)
    c = start * np.exp(np.cumsum(rng.normal(0, 0.001, len(idx))))
    o = np.r_[c[0], c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.0002, "low": np.minimum(o, c) * 0.9998, "close": c,
                         "volume": rng.integers(100, 5000, len(idx)).astype(float)}, index=idx)


# ------------------------------------------------------------------------------------------------ calendar
def test_calendar_half_days_and_holidays():
    assert mc.close_minutes(HALF, use_http=False) == 780 and mc.close_minutes("2025-11-26", use_http=False) == 960
    for d in ("2025-07-03", "2025-11-28", "2025-12-24"):
        assert mc.PAST_EARLY_CLOSES[d].hour == 13
        assert mc.session_close(d, use_http=False).hour == 16      # the runner / replay path is unchanged
    assert mc.close_minutes("2026-11-27", use_http=False) == 780 and mc.close_minutes("2026-12-24", use_http=False) == 780
    assert not mc.is_trading_day("2026-11-26") and not mc.is_trading_day("2026-11-28") and mc.is_trading_day("2026-11-27")
    assert str(mc.next_trading_day("2026-11-25")) == "2026-11-27"
    assert str(mc.next_trading_day("2026-11-27", -1)) == "2026-11-25"
    assert str(mc.next_trading_day("2026-12-24")) == "2026-12-28"
    assert B.close_min(HALF) == 780 and HALF in B.early_close_days()


def test_cap_at_close_drops_after_hours_only_on_half_days():
    two = pd.concat([_day_1min("2025-11-26"), _day_1min(HALF)])
    out = B.cap_at_close(two)
    reg, half = out[out.index.date == pd.Timestamp("2025-11-26").date()], out[out.index.date == pd.Timestamp(HALF).date()]
    assert len(reg) == 390 and len(half) == 210 and half.index.max().strftime("%H:%M") == "12:59"


# ------------------------------------------------------------------------------------------------ assignments
def test_next_session_skips_holidays():
    et = ZoneInfo(NY)
    assert A.next_session(datetime(2026, 11, 25, 18, 0, tzinfo=et)) == "2026-11-27"     # Wed evening -> not Thanksgiving
    assert A.next_session(datetime(2026, 11, 26, 21, 40, tzinfo=et)) == "2026-11-27"    # on the holiday itself
    assert A.next_session(datetime(2026, 11, 26, 10, 0, tzinfo=et)) == "2026-11-27"
    assert A.next_session(datetime(2026, 11, 27, 10, 0, tzinfo=et)) == "2026-11-27"     # the half day is a session
    assert A.next_session(datetime(2026, 12, 24, 17, 0, tzinfo=et)) == "2026-12-28"     # Christmas + weekend
    assert A.sessions_around("2026-11-25 18:00 ET") == ("2026-11-25", "2026-11-27")
    assert A.sessions_around("2026-11-27 07:00 ET") == ("2026-11-25", "2026-11-27")
    assert A.sessions_around("2026-11-30 07:00 ET") == ("2026-11-27", "2026-11-30")


def test_assignments_file_has_no_holiday_sessions():
    import json

    d = json.loads(A.OUT.read_text())
    assert mc.is_trading_day(d["asof_session"])
    for k, v in d["setups"].items():
        for f in ("first_session", "last_old_session"):
            if v.get(f):
                assert mc.is_trading_day(v[f]), (k, f, v[f])


# ------------------------------------------------------------------------------------------------ Hunch
def test_hunch_bars3_stops_at_half_day_close():
    m1 = pd.concat([_day_1min("2025-11-26"), _day_1min(HALF)])
    b = D.bars3(m1, close_for=B.close_min)
    n = b.groupby("date").size()
    assert list(n) == [130, 70]                                   # 13:00 close -> buckets 0..69 only
    h = b[b["date"].astype(str) == HALF]
    assert h["b"].max() == 69 and h["filled"].sum() == 0
    assert len(D.bars3(m1)) == 260                                 # the frozen replay grid is unchanged
    assert D.n_buckets(960) == 130 and D.n_buckets(780) == 70


def test_hunch_walk_day_half_day_completes_at_close():
    from mcf.hunch import live as LV

    days = [str(d.date()) for d in pd.bdate_range("2025-11-17", periods=10) if str(d.date()) != "2025-11-27"]
    assert days[-1] == HALF
    m1 = {s: pd.concat([_day_1min(d, seed=i * 10 + k, start=100 + 10 * i) for k, d in enumerate(days)])
          for i, s in enumerate(["SPY", "QQQ", "SMH", "IBIT", "AAA"])}
    assert LV.guess_last(HALF) == 66 and LV.guess_last("2025-11-26") == D.GUESS_LAST
    feats = D.ALL_FEATURES
    S = ["SPY", "QQQ", "AAA"]
    pooled = LV.Lr.LogReg(len(feats), feats.index("tod"), n_groups=len(S))
    model = {"metric": "M1", "last_date": days[-2], "symbols": S, "feats": feats, "pooled": pooled,
             "ticker": LV.Lr.PerTicker(len(S), len(feats), feats.index("tod")), "yes_n": 0.0, "tot_n": 0.0}
    panel = D.build_panel(S, loader=m1.get, close_for=B.close_min)
    g, m_after, done = LV.walk_day(model, panel, HALF, pd.Timestamp(f"{HALF} 12:54:40", tz=NY))
    assert done and g["b"].max() == 66 and g["bar_close"].max() == "12:51"   # last guess 12:51, scored at 12:54
    assert g["outcome"].notna().all() and m_after["tot_n"] > 0
    g2, m2, _ = LV.walk_day(model, panel, HALF, pd.Timestamp(f"{HALF} 16:01", tz=NY))
    assert len(g2) == len(g) and m2["tot_n"] == m_after["tot_n"]           # nothing after the close is learned
    # after-hours prints change nothing: the same session without them gives identical guesses
    cut = {s: v[(v.index.strftime("%Y-%m-%d") != HALF) | (v.index.hour < 13)] for s, v in m1.items()}
    g3, _, _ = LV.walk_day(model, D.build_panel(S, loader=cut.get, close_for=B.close_min), HALF,
                           pd.Timestamp(f"{HALF} 16:01", tz=NY))
    k = ["b", "symbol"]
    pd.testing.assert_frame_equal(g2.set_index(k)[["p_pooled", "p_own", "outcome"]],
                                  g3.set_index(k)[["p_pooled", "p_own", "outcome"]])
    assert not LV.walk_day(model, panel, HALF, pd.Timestamp(f"{HALF} 12:50", tz=NY))[2]


# ------------------------------------------------------------------------------------------------ Compass
def _compass_bars(day):
    out = {}
    for i, s in enumerate(["SPY", "QQQ", "IWM"] + [f"N{j}" for j in range(5)]):
        out[s] = _day_1min(day, seed=i, start=100 + i)
    return out


def test_compass_no_marks_after_half_day_close(tmp_path):
    names = [f"N{j}" for j in range(5)]
    assert cl.marks_for(HALF)[-1] == 12 * 60 + 45 and len(cl.marks_for(HALF)) == 13
    assert cl.marks_for("2025-11-26") == cl.MARKS
    rows = cl.compute(_compass_bars(HALF), HALF, pd.Timestamp(f"{HALF} 16:05", tz=NY), names)
    assert [r["T"] for r in rows][-1] == "12:45" and len(rows) == 13

    def fake(day, syms, now, log=print):                         # a feed that still prints until 16:00
        return {k: v[v.index < now] for k, v in _compass_bars(day).items()}

    assert cl.update(tmp_path, HALF, pd.Timestamp(f"{HALF} 15:46", tz=NY), bars_fn=fake, names=names,
                     log=lambda *_: None) == 13
    assert cl.update(tmp_path, HALF, pd.Timestamp(f"{HALF} 16:05", tz=NY), bars_fn=fake, names=names,
                     log=lambda *_: None) == 0
    assert cl.latest(HALF, cl.read_rows(tmp_path / "compass" / f"{HALF}.csv"),
                     pd.Timestamp(f"{HALF} 13:05", tz=NY))["phase"] == "closed"


def test_compass_fetches_cap_at_calendar_close(monkeypatch):
    from mcf.replay import store

    seen = []

    def fake_fetch(syms, start, end, tf):
        seen.append(pd.Timestamp(end).tz_convert(NY))
        b = _day_1min(HALF)
        return pd.DataFrame({"ts": b.index.tz_convert("UTC"), "symbol": "SPY", **{c: b[c].to_numpy() for c in b}})

    monkeypatch.setattr(store, "_fetch_bars", fake_fetch)
    got = cl.fetch(HALF, ["SPY"], pd.Timestamp(f"{HALF} 15:30", tz=NY), log=lambda *_: None)
    assert seen[-1].strftime("%H:%M") == "13:00" and got["SPY"].index.max().strftime("%H:%M") == "12:59"
    spy = cc.fetch_spy(HALF, log=lambda *_: None)
    assert seen[-1].strftime("%H:%M") == "13:00" and spy.index.max().strftime("%H:%M") == "12:59"


# ------------------------------------------------------------------------------------------------ compass_cond
def test_cond_half_day_not_stored_and_purged(tmp_path, monkeypatch):
    monkeypatch.setattr(cc, "SEED", tmp_path / "none.csv.gz")
    full = lambda d: cc.day_obs(_day_1min(d, seed=1), d, 99.0)
    obs = pd.DataFrame(full("2025-11-26") + full(HALF) + full("2025-12-01"))[cc.OBS_COLS]
    (tmp_path / "compass").mkdir()
    obs.to_csv(tmp_path / "compass" / "cond_obs.csv", index=False)
    o = cc.read_obs(tmp_path / "compass" / "cond_obs.csv")
    assert set(o.date) == {"2025-11-26", "2025-12-01"}
    assert o[o.date == "2025-12-01"][cc.PREV_COLS].isna().all().all()          # no previous close across a half day
    assert o[o.date == "2025-11-26"].prev_close.notna().all()
    # a capped half day (bars to 12:59) is not a full session: nothing appended
    capped = lambda d, log=print: B.cap_at_close(_day_1min(d))
    assert cc.update(tmp_path, HALF, spy_fn=capped, log=lambda *_: None) == 0
    assert HALF not in set(pd.read_csv(tmp_path / "compass" / "cond_obs.csv", dtype={"date": str}).date)
    assert HALF not in cc.missing_days(tmp_path, "2025-12-02")


def test_seed_has_no_half_days():
    with gzip.open(cc.SEED, "rt") as f:
        o = pd.read_csv(f, dtype={"date": str})
    assert not o.date.isin(cc.EARLY_CLOSE_DAYS).any()
    assert not (o.date.isin(cc.AFTER_EARLY_CLOSE) & o.prev_close.notna()).any()


@pytest.mark.parametrize("mod", ["mcf/report/compass_live.py", "mcf/report/compass_cond.py", "mcf/hunch/live.py"])
def test_display_modules_import_no_trading_code(mod):
    src = (cl.ROOT / mod).read_text()
    assert "mcf.execution" not in src and "submit_order" not in src
