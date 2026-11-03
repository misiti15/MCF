"""eu1103/preopen: the 09:30-09:35 opening bar per symbol-day from the two-year SIP 1-minute cache (open, close,
$ volume). The rule-19 locked block is dropped at read time (pyarrow filter, asserted), as eu1103/open/build_early.py.
    python build_o5.py <scratch>  -> <scratch>/o5_hist.parquet
Educational only - not financial advice."""
import os, sys
from pathlib import Path
import pandas as pd, pyarrow.dataset as pds

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
S = Path(sys.argv[1]); CACHE = Path("/home/user/MCF/data/cache_hist/1Min"); TZ = "America/New_York"
LK0, LK1 = pd.Timestamp("2024-11-01", tz=TZ), pd.Timestamp("2025-03-01", tz=TZ)
out = []
for p in sorted(CACHE.glob("*.parquet")):
    ix = "__index_level_0__"
    df = pds.dataset(str(p), format="parquet").to_table(filter=(pds.field(ix) < LK0) | (pds.field(ix) >= LK1)).to_pandas()
    if ix in df.columns:
        df = df.set_index(ix)
    if df.empty:
        continue
    assert not ((df.index >= LK0) & (df.index < LK1)).any()
    m = df.index.hour * 60 + df.index.minute
    df = df[(m >= 570) & (m < 575)]
    df = df[~df.index.duplicated(keep="last")].sort_index()
    g = df.groupby(df.index.date)
    o = pd.DataFrame({"o5_open": g.open.first(), "o5_close": g.close.last(), "o5_dvol": (df.close * df.volume).groupby(df.index.date).sum()})
    o["symbol"] = p.stem; o["date"] = o.index.astype(str)
    out.append(o.reset_index(drop=True))
pd.concat(out, ignore_index=True).to_parquet(S / "o5_hist.parquet", index=False)
print("ok", sum(len(x) for x in out))
