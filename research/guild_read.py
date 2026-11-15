"""Guild shared read helper (Lead lead-20261115-0900-1, Skeptic skeptic-20261115-1350-1; checklist: every new reader uses it).
data/cache_hist/1Min is the MCF's own store and DOES hold the locked block 2024-11-01..2025-02-28 (the owner's holdout); the guild
never reads it. These readers apply a pyarrow predicate that excludes the block AT READ (the rows never enter memory) and assert
that none came back. Optional start / end narrow the read further (inclusive dates, ET).
    read_1min(sym, start=None, end=None, columns=None, path=None) -> DataFrame, tz-aware ET index, sorted, de-duplicated
        (path= reads another 1-min parquet store with the same guarantees, e.g. a premarket cache; index name from metadata)
    read_daily(start=None, end=None, columns=None)     -> research/history2y/data/daily.parquet rows, 'date' as YYYY-MM-DD str
Educational only - not financial advice."""
import datetime as dt
from pathlib import Path
import pandas as pd
import pyarrow.dataset as pds

ROOT = Path("/home/user/MCF"); NY = "America/New_York"
B0, B1 = "2024-11-01", "2025-02-28"
_T0, _T1 = pd.Timestamp(B0, tz=NY), pd.Timestamp("2025-03-01", tz=NY)
IX = "__index_level_0__"


def _index_name(ds) -> str:
    """the time-index column of a pandas-written parquet file, from its pandas metadata (Skeptic 11-15: not always
    __index_level_0__); falls back to __index_level_0__."""
    import json
    md = ds.schema.metadata or {}
    try:
        ic = json.loads(md[b"pandas"].decode())["index_columns"]
        if ic and isinstance(ic[0], str):
            return ic[0]
    except Exception:
        pass
    return IX


def read_1min(sym: str, start=None, end=None, columns=None, path=None) -> pd.DataFrame:
    p = Path(path) if path else ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists():
        return pd.DataFrame()
    ds = pds.dataset(str(p), format="parquet"); ix = _index_name(ds)
    f = (pds.field(ix) < _T0) | (pds.field(ix) >= _T1)
    if start is not None: f = f & (pds.field(ix) >= pd.Timestamp(start, tz=NY))
    if end is not None: f = f & (pds.field(ix) < pd.Timestamp(end, tz=NY) + pd.Timedelta(days=1))
    cols = None if columns is None else list(dict.fromkeys(list(columns) + [ix]))
    df = ds.to_table(filter=f, columns=cols).to_pandas()        # raises loudly if the predicate can't be applied
    if ix in df.columns: df = df.set_index(ix)
    df.index = pd.DatetimeIndex(df.index).tz_convert(NY)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    assert not ((df.index >= _T0) & (df.index < _T1)).any(), f"guild_read: block rows returned for {sym}"
    return df if columns is None else df[[c for c in columns if c in df.columns]]


def read_daily(start=None, end=None, columns=None) -> pd.DataFrame:
    f = (pds.field("date") < dt.date(2024, 11, 1)) | (pds.field("date") > dt.date(2025, 2, 28))
    if start is not None: f = f & (pds.field("date") >= pd.Timestamp(start).date())
    if end is not None: f = f & (pds.field("date") <= pd.Timestamp(end).date())
    d = pds.dataset(str(ROOT / "research/history2y/data/daily.parquet"), format="parquet").to_table(filter=f, columns=columns).to_pandas()
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    assert not ((d.date >= B0) & (d.date <= B1)).any(), "guild_read: block rows returned from daily"
    return d


def _edge_test():
    import tempfile, os
    idx = pd.DatetimeIndex(["2024-10-31 15:59", "2024-10-31 19:59", "2024-11-01 09:30", "2025-02-28 15:59", "2025-03-03 09:30"]).tz_localize(NY)
    d = pd.DataFrame({"open": range(5), "close": range(5)}, index=idx)
    with tempfile.TemporaryDirectory() as t:
        for name, frame in (("unnamed", d), ("named", d.rename_axis("ts")), ("utc", d.tz_convert("UTC").rename_axis("timestamp"))):
            f = os.path.join(t, name + ".parquet"); frame.to_parquet(f)
            got = read_1min("x", path=f)
            assert [str(x)[:16] for x in got.index] == ["2024-10-31 15:59", "2024-10-31 19:59", "2025-03-03 09:30"], (name, got.index)
    print("edge test ok: unnamed / named / UTC-stored index; block edges dropped, 2024-10-31 19:59 ET and 2025-03-03 kept")


if __name__ == "__main__":
    _edge_test()
    s = read_1min("SPY"); full = pds.dataset(str(ROOT / "data/cache_hist/1Min/SPY.parquet"), format="parquet").count_rows()
    s2 = read_1min("SPY", "2026-11-12", "2026-11-13", ["open", "close"])
    d = read_daily(columns=["symbol", "date", "close"])
    print(f"selftest: SPY rows on disk {full}, returned {len(s)} (block excluded at read: {full - len(s)} rows not loaded incl. dups); "
          f"window 11-12..11-13 rows {len(s2)} cols {list(s2.columns)}; daily rows {len(d)} ({d.date.min()}..{d.date.max()}); no block rows")
