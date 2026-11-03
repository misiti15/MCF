"""night1102/regime: the same session states as days.py (SPY only) for the two-year history, from the SIP 1-minute
SPY cache (data/cache_hist/1Min/SPY.parquet). Locked block dates (2024-11-01..2025-02-28) are dropped before any
use. The 20-day range median is computed on the continuous series (range only, no outcome). Educational only."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[5]
SCR = Path(sys.argv[1])
b = pd.read_parquet(ROOT / "data" / "cache_hist" / "1Min" / "SPY.parquet")
b.index = pd.to_datetime(b.index).tz_convert("America/New_York")
b = b[(b.index.time >= pd.Timestamp("09:30").time()) & (b.index.time < pd.Timestamp("16:00").time())].copy()
b["date"] = b.index.date
b["tod"] = b.index.hour * 100 + b.index.minute + 1
b["tod"] = np.where(b["tod"] % 100 == 60, b["tod"] + 40, b["tod"])
g = b.groupby("date")
D = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last()})
D["o2c"] = (D.close / D.open - 1) * 100
D["rng"] = (D.high - D.low) / D.open * 100
D["med20"] = D.rng.shift(1).rolling(20, min_periods=10).median()
D["eod3"] = np.where(D.o2c >= 0.25, "up", np.where(D.o2c <= -0.25, "down", "quiet"))
tp = (b.high + b.low + b.close) / 3
b["vw"] = (tp * b.volume).groupby(b.date).cumsum() / b.volume.groupby(b.date).cumsum()
b["fo"] = (b.close / b.date.map(D.open) - 1) * 100
b["vwd"] = (b.close / b.vw - 1) * 100
for t in (950, 1000, 1030):
    x = b[b.tod == t].set_index("date")
    D[f"fo_SPY@{t}"] = x["fo"]
    D[f"vw_SPY@{t}"] = x["vwd"]
for t in (950, 1030):
    y = b[b.tod <= t].groupby("date")
    D[f"rngr@{t}"] = (y.high.max() - y.low.min()) / D.open * 100 / D.med20
s = pd.Series(D.index.astype(str), index=D.index)
D = D[~((s >= "2024-11-01") & (s <= "2025-02-28"))]
D = D[s.reindex(D.index) <= "2026-10-05"]
D.to_parquet(SCR / "days2y.parquet")
print(len(D), D.eod3.value_counts().to_dict())
print(D[["rngr@950", "rngr@1030"]].describe().round(2))
