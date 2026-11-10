"""Compass conditional stats (owner 2026-11-10): observations, cells, nightly append, lookup. Display only.
Educational only — not financial advice."""
import gzip
import json

import numpy as np
import pandas as pd

from mcf.report import compass_cond as cc


def _spy(day, pct_path, base=100.0):
    idx = pd.date_range(f"{day} 09:30", f"{day} 15:59", freq="1min", tz=cc.NY)
    m = idx.hour * 60 + idx.minute
    kx, ky = zip(*pct_path)
    c = base * (1 + np.interp(m, kx, ky) / 100)
    o = np.r_[base, c[:-1]]
    return pd.DataFrame({"open": o, "high": np.maximum(o, c), "low": np.minimum(o, c), "close": c, "volume": 1.0}, index=idx)


def test_day_obs_point_in_time_and_outcomes():
    b = _spy("2026-11-06", [(570, 0), (630, 0.3), (960, 0.6)])
    rows = cc.day_obs(b, "2026-11-06", prev_close=99.0)
    assert [r["T"] for r in rows][:2] == ["10:00", "10:10"] and rows[-1]["T"] == "15:50" and len(rows) == 36
    r = rows[0]
    assert abs(r["px"] - b.close[b.index < pd.Timestamp("2026-11-06 10:00", tz=cc.NY)].iloc[-1]) < 1e-9   # bars closed by T
    assert r["eod_open"] == 1 and r["eod_prev"] == 1 and r["vs_prev"] == 1 and abs(r["gap"] - (100 / 99 - 1)) < 1e-9
    assert r["next5"] == 1 and rows[-1]["next30"] is None and rows[-1]["next10"] == 1
    assert cc.bucket(0.003) == "+0.2..+0.4%" and cc.bucket(-0.0001) == "-0.2..0%" and cc.bucket(-0.01) == "< -0.4%"
    assert cc.gap_cat(0.003) == "gap up" and cc.gap_cat(None) == "unknown"


def test_update_appends_idempotent_and_chains_previous_close(tmp_path, monkeypatch):
    monkeypatch.setattr(cc, "SEED", tmp_path / "none.csv.gz")
    days = {"2026-11-05": [(570, 0), (960, -0.5)], "2026-11-06": [(570, 0), (630, 0.3), (960, 0.6)]}
    fn = lambda day, log=print: _spy(day, days[day])
    assert cc.update(tmp_path, "2026-11-05", spy_fn=fn, log=lambda *_: None) == 36
    assert cc.update(tmp_path, "2026-11-06", spy_fn=fn, log=lambda *_: None) == 36
    assert cc.update(tmp_path, "2026-11-06", spy_fn=fn, log=lambda *_: None) == 36        # rerun replaces, no duplicate
    o = pd.read_csv(tmp_path / "compass" / "cond_obs.csv", dtype={"date": str})
    assert len(o) == 72 and o[o.date == "2026-11-05"].prev_close.isna().all()
    assert np.allclose(o[o.date == "2026-11-06"].prev_close, 99.5, atol=0.01)
    j = json.loads((tmp_path / "compass" / "cond_stats.json").read_text())
    assert j["asof_date"] == "2026-11-06" and j["sessions"] == 2 and abs(j["last_close"] - 100.6) < 0.01
    assert j["disclaimer"] == "Educational only — not financial advice."
    c = cc.lookup(j, 11 * 60 + 35, 0.003, 100.8)
    assert c["T"] == "11:30" and c["side"] == "above prev close" and c["n"] == 1 and c["same_side_open"] == 1.0
    # holiday / no data: tables refreshed, nothing appended
    assert cc.update(tmp_path, "2026-11-09", spy_fn=lambda d, log=print: None, log=lambda *_: None) == 0


def test_seed_baseline_is_used_and_has_no_locked_block():
    with gzip.open(cc.SEED, "rt") as f:
        o = pd.read_csv(f, dtype={"date": str})
    assert not o.date.between("2024-11-01", "2025-02-28").any()
    assert o.date.nunique() > 400 and list(o.columns) == cc.OBS_COLS
    C = cc.cells(o.head(36 * 30))
    assert {"same_side_open", "same_side_prev", "to_close_med", "next60_hit", "n"} <= set(C.columns)


def test_display_only():
    src = (cc.ROOT / "mcf/report/compass_cond.py").read_text()
    for bad in ("execution", "submit_order", "TradingClient", "paper-api"):
        assert bad not in src
    assert "store._fetch_bars" in src
