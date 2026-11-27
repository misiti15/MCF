"""ARENASTARS-1127: check of the t2ctx.py breadth method against the lab context table on a T1 month (2025-10), using
a random 150-name subset of data/cache_hist/1Min. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as pads
sys.path.insert(0, "research/arenastars_1127")
import t2ctx as T  # noqa: E402
H = Path("/home/user/MCF/data/cache_hist/1Min")
ps = sorted(H.glob("*.parquet")); rng = np.random.default_rng(1); ps = [ps[i] for i in rng.choice(len(ps), 150, replace=False)]
parts = []
for p in ps:
    f = pads.field("__index_level_0__")
    b = pads.dataset(str(p)).to_table(filter=(f >= pd.Timestamp("2025-10-01", tz=T.TZ)) & (f < pd.Timestamp("2025-11-01", tz=T.TZ))).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    if not len(b):
        continue
    tmp = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/as_w/_chk.parquet"); b.to_parquet(tmp)
    x = T.job(tmp)
    if x is not None:
        parts.append(x)
x = pd.concat(parts).groupby(["date", "tod"]).agg(b=("a", "mean"), bo=("o", "mean")).reset_index()
c = pd.read_parquet("/home/user/MCF/research/history2y/data/context/month=2025-10.parquet")
c["date"] = c.date.astype(str)
m = x.merge(c, on=["date", "tod"])
m = m[(m.tod >= 950) & (m.tod <= 1500)]
print(len(ps), "names; rows", len(m), "corr breadth %.3f breadth_open %.3f" % (m.b.corr(m.breadth), m.bo.corr(m.breadth_open)),
      "mean diff %.3f / %.3f" % ((m.b - m.breadth).mean(), (m.bo - m.breadth_open).mean()),
      "agree <0.3: %.3f, <0.35 (open): %.3f, >0.7: %.3f" % (((m.b < 0.3) == (m.breadth < 0.3)).mean(),
      ((m.bo < 0.35) == (m.breadth_open < 0.35)).mean(), ((m.b > 0.7) == (m.breadth > 0.7)).mean()))
