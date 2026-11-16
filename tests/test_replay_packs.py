"""Live-session bar packs (mcf/replay/packs.py, store.py readers): synthetic data, no network."""
import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from mcf.replay import packs, store


def _bars(day="2026-11-13", syms=("AAA", "BBB", "BRK.B")):
    t = pd.date_range(f"{day} 09:30", f"{day} 15:59", freq="1min", tz="America/New_York").tz_convert("UTC")
    rows = []
    for i, s in enumerate(syms):
        px = 10 + i + np.arange(len(t)) * 0.01
        rows.append(pd.DataFrame({"symbol": s, "ts": t, "open": px, "high": px + .05, "low": px - .05,
                                  "close": px + .01, "volume": np.arange(len(t)) * 3 + 100}))
    return pd.concat(rows, ignore_index=True).sample(frac=1, random_state=0)      # unsorted on purpose


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", tmp_path)
    monkeypatch.setattr(store, "PACKS", tmp_path / "packs")
    return tmp_path


def test_write_read_roundtrip(tmp_store):
    df = _bars()
    p = store.write_pack(df, store.pack_path("2026-11-13"), {"universe": ["AAA", "BBB"], "session": "2026-11-13"})
    m = store.pack_meta(p)
    assert m["universe"] == ["AAA", "BBB"] and m["rows"] == len(df) and m["symbols"] == 3
    x = store.read_pack(p)
    assert list(x.columns) == store.PACK_COLS and len(x) == len(df)
    assert (x.groupby("symbol").ts.apply(lambda s: s.is_monotonic_increasing)).all()
    y = df.sort_values(["symbol", "ts"]).reset_index(drop=True)
    assert np.allclose(x.close.values, y.close.values) and (x.volume.values == y.volume.values).all()
    assert set(store.read_pack(p, ["BBB"]).symbol) == {"BBB"}


def test_reader_prefers_pack_and_lists_day(tmp_store):
    store.write_pack(_bars(), store.pack_path("2026-11-13"), {"universe": ["AAA"]})
    assert date(2026, 11, 13) in store.available_days()
    bars = store.load_day("2026-11-13", ["AAA", "BRK.B"])
    assert set(bars) == {"AAA", "BRK.B"}
    b = bars["AAA"]
    assert len(b) == 390 and str(b.index.tz) == "America/New_York" and b.index[0].hour == 9
    cl = store.StoreHistClient(date(2026, 11, 14))
    x = cl._day(date(2026, 11, 13), 5)
    assert len(x[x.symbol == "AAA"]) == 78


def test_pack_daily_and_lock(tmp_store):
    d = pd.DataFrame({"symbol": ["AAA", "AAA"], "ts": pd.to_datetime(["2026-11-12", "2026-11-13"], utc=True),
                      "open": 1.0, "high": 2.0, "low": .5, "close": 1.5, "volume": 10})
    store.write_pack(d, store.pack_path("2026-11-13", "1day"))
    assert len(store.pack_daily([date(2026, 11, 13)])) == 2
    locked = d.assign(ts=pd.to_datetime(["2024-12-02", "2024-12-03"], utc=True))
    with pytest.raises(ValueError):
        store.write_pack(locked, tmp_store / "x.parquet")


def test_fetch_pack_offline(tmp_store, monkeypatch):
    monkeypatch.setenv("MCF_REPLAY_PACKS", "0")
    assert store.fetch_pack("2026-11-13") is None
    assert store.fetch_pack("2026-09-01") is None            # before the first live session
    assert store.pull_packs([date(2026, 11, 13)]) == []
    assert store.pack_url("2026-11-13").endswith("/releases/download/bars-2026-11/1min-2026-11-13.parquet")


def test_build_session_and_capacity(tmp_path, monkeypatch):
    monkeypatch.setattr(packs, "day_universe", lambda d, b: (["AAA", "BBB", "BRK.B"], ["AAA", "BBB"], "test"))
    calls = []

    def fake(syms, start, end, tf, batch=100):
        calls.append(tf)
        if "BAD" in syms:
            import requests
            r = requests.Response()
            r.status_code = 400
            raise requests.HTTPError(response=r)
        if tf == "1Day":
            return pd.DataFrame({"symbol": list(syms), "ts": pd.Timestamp("2026-11-13", tz="UTC"), "open": 1.0,
                                 "high": 1.0, "low": 1.0, "close": 1.0, "volume": 5})
        x = _bars("2026-11-13", syms)
        pre = x.iloc[:1].assign(ts=pd.Timestamp("2026-11-13 13:05", tz="UTC"))        # pre-market: dropped
        return pd.concat([x, pre], ignore_index=True)

    monkeypatch.setattr(store, "_fetch_bars", fake)
    row = packs.build_session("2026-11-13", tmp_path)
    assert row["symbols"] == 3 and row["rows_1min"] == 3 * 390 and row["release"] == "bars-2026-11"
    assert store.pack_meta(tmp_path / "1min-2026-11-13.parquet")["universe"] == ["AAA", "BBB"]
    assert len(store.read_pack(tmp_path / "1day-2026-11-13.parquet")) == 3
    got = packs.fetch_safe(["AAA", "BAD", "BBB"], "a", "b", "1Day", log=lambda m: None)
    assert set(got.symbol) == {"AAA", "BBB"}
    rows = [json.loads(x) for x in (tmp_path / "manifest.jsonl").read_text().splitlines()]
    rel = [{"tag_name": "bars-2026-11", "assets": [{"name": "1min-2026-11-13.parquet", "size": 30_000_000},
                                                   {"name": "1day-2026-11-13.parquet", "size": 2_000_000}]}]
    cap = packs.capacity(rows, rel)
    assert cap["sessions_stored"] == 1 and cap["total_gb"] == 0.032 and cap["largest_asset_mb"] == 30.0
    assert "2 GB per file" in cap["headroom"] and cap["note"].startswith("Educational only")
    with pytest.raises(SystemExit):
        packs.main(["build", "--start", "2025-01-02", "--end", "2025-01-03", "--out", str(tmp_path)])


def test_two_year_tier_months_and_lock(tmp_store, monkeypatch):
    assert packs.tier("2026-10-06") == ("live", 1.0) and packs.tier("2025-06-02") == ("2y", 0.175)
    assert store.pack_weight("2025-06-02") == 0.175
    assert packs.month_bounds("2025-03", "2025-03") == (date(2025, 3, 1), date(2025, 3, 31))
    assert packs.month_bounds("2024-09-16", "2024-10") == (date(2024, 9, 16), date(2024, 10, 31))
    with pytest.raises(ValueError):
        packs.build_session("2024-12-02", tmp_store)
    asked = []
    monkeypatch.setattr(store, "fetch_pack", lambda d, kind="1min", log=print: asked.append((d, kind)) or None)
    store.pull_packs([date(2025, 6, 2), date(2024, 12, 2), date(2026, 11, 13)])
    assert [d for d, k in asked if k == "1min"] == [date(2026, 11, 13)]           # 2-year packs only on request
    asked.clear()
    store.pull_packs([date(2025, 6, 2), date(2024, 12, 2)], hist=True)
    assert [d for d, k in asked] == [date(2025, 6, 2)]                             # never the locked block
    rows = [{"session": "2025-06-02", "symbols": 3, "mb_1min": 30.0, "mb_1day": 2.0, "tier": "2y", "weight": 0.175}]
    cap = packs.capacity(rows, None)
    assert cap["progress"]["2y"]["stored"] == 1 and cap["progress"]["2y"]["weight"] == 0.175
    assert cap["progress"]["2y"]["weekdays"] > 300 and "2024-12" not in str(cap["progress"]["2y"]["months_done"])
