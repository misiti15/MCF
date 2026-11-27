"""ARENASTARS-1127 post-hoc DESCRIPTIVE (not a config, no pass bar): how much of each candidate's history day R is the
market's own move after the entry window opens? Correlation of the day's book R with SPY's return from the window start
to 15:55 (signed by the setup's side), on CHECK + T2 days the candidate traded. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads
W = Path(sys.argv[1]); TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
def spy(src):
    f = pads.field("__index_level_0__")
    b = pads.dataset(str(src)).to_table(filter=(f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
    if "__index_level_0__" in b.columns: b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ); return b
b = pd.concat([spy("/home/user/MCF/data/cache_fresh/1Min/SPY.parquet"), spy("/home/user/MCF/data/cache_hist/1Min/SPY.parquet")])
b = b[~b.index.duplicated()].sort_index(); hm = b.index.hour * 100 + b.index.minute; day = b.index.date.astype(str)
assert not ((day >= LOCK[0]) & (day <= LOCK[1])).any()
for tag, side, w0 in (("G05", -1, 1255), ("G07", -1, 1255), ("G37", 1, 1125)):
    h = pd.read_parquet(W / f"hist_{tag}.parquet"); h = h[h.per.isin(["CHECK", "T2"])]
    d = h.groupby("date").agg(R=("r_livel", "sum"), n=("r_livel", "size"))
    s0 = pd.Series(b.open.values[hm == w0], index=day[hm == w0]); s1 = pd.Series(b.open.values[hm == 1555], index=day[hm == 1555])
    s0 = s0[~s0.index.duplicated()]; s1 = s1[~s1.index.duplicated()]
    d["spy"] = side * (s1 / s0 - 1).reindex(d.index) * 100
    d = d.dropna()
    top = d.sort_values("R").tail(5)
    print(tag, "days", len(d), "corr(dayR, signed SPY move) %.2f" % d.R.corr(d.spy),
          "R on days SPY moved >=0.5%% the setup's way: %.1f (%d days); other days %.1f" % (d.R[d.spy >= 0.5].sum(), (d.spy >= 0.5).sum(), d.R[d.spy < 0.5].sum()),
          "| top-5 days signed SPY %%:", top.spy.round(2).tolist())
