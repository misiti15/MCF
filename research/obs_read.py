"""Block-safe bar reader for Observer scripts (checklist #43). data/cache_hist/1Min paths are delegated to Builder's
research/guild_read.read_1min (the shared reader); other caches (e.g. data/cache_pm) keep the predicate below.
read_bars(path): reads a data/cache_hist or cache_pm parquet with a pyarrow predicate that EXCLUDES the locked block
(2024-11-01..2025-02-28 ET) on the time index, then asserts no block rows came back. Educational only - not financial advice."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pandas as pd, pyarrow as pa, pyarrow.parquet as pq, pyarrow.dataset as ds
B0, B1 = pd.Timestamp("2024-11-01", tz="America/New_York"), pd.Timestamp("2025-03-01", tz="America/New_York")
def read_bars(path):
    p = Path(path)
    if p.parent.name == "1Min" and p.parent.parent.name == "cache_hist":   # shared store -> the guild's shared reader (Lead 11-15)
        import guild_read
        return guild_read.read_1min(p.stem)
    sch = pq.read_schema(path); idx = (sch.pandas_metadata or {}).get("index_columns", ["__index_level_0__"])[0]
    f = ds.field(idx); unit_tz = sch.field(idx).type
    lo, hi = pa.scalar(B0.to_pydatetime(), type=unit_tz), pa.scalar(B1.to_pydatetime(), type=unit_tz)
    t = ds.dataset(str(path), format="parquet").to_table(filter=(f < lo) | (f >= hi)); d = t.to_pandas()
    assert not ((d.index >= B0) & (d.index < B1)).any(), f"rule 19: block rows returned from {path}"
    return d
if __name__ == "__main__":
    import sys; d = read_bars(sys.argv[1]); print(len(d), d.index.min(), d.index.max(), "no block rows")
