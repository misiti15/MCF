"""Guild shared read helper (Lead lead-20261115-0900-1, Skeptic skeptic-20261115-1350-1; checklist: every new reader uses it).
data/cache_hist/1Min is the MCF's own store and DOES hold the locked block 2024-11-01..2025-02-28 (the owner's holdout); the guild
never reads it. These readers apply a pyarrow predicate that excludes the block AT READ (the rows never enter memory) and assert
that none came back. Optional start / end narrow the read further (inclusive dates, ET).
    read_1min(sym, start=None, end=None, columns=None) -> DataFrame, tz-aware America/New_York index, sorted, de-duplicated
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


def read_1min(sym: str, start=None, end=None, columns=None) -> pd.DataFrame:
    p = ROOT / "data/cache_hist/1Min" / f"{sym}.parquet"
    if not p.exists():
        return pd.DataFrame()
    f = (pds.field(IX) < _T0) | (pds.field(IX) >= _T1)
    if start is not None: f = f & (pds.field(IX) >= pd.Timestamp(start, tz=NY))
    if end is not None: f = f & (pds.field(IX) < pd.Timestamp(end, tz=NY) + pd.Timedelta(days=1))
    cols = None if columns is None else list(dict.fromkeys(list(columns) + [IX]))
    try:
        df = pds.dataset(str(p), format="parquet").to_table(filter=f, columns=cols).to_pandas()
    except Exception:                         # files whose index is stored under another name: read the schema, retry
        df = pds.dataset(str(p), format="parquet").to_table(filter=f).to_pandas()
    if IX in df.columns: df = df.set_index(IX)
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


if __name__ == "__main__":
    s = read_1min("SPY"); full = pds.dataset(str(ROOT / "data/cache_hist/1Min/SPY.parquet"), format="parquet").count_rows()
    s2 = read_1min("SPY", "2026-11-12", "2026-11-13", ["open", "close"])
    d = read_daily(columns=["symbol", "date", "close"])
    print(f"selftest: SPY rows on disk {full}, returned {len(s)} (block excluded at read: {full - len(s)} rows not loaded incl. dups); "
          f"window 11-12..11-13 rows {len(s2)} cols {list(s2.columns)}; daily rows {len(d)} ({d.date.min()}..{d.date.max()}); no block rows")
