"""REMEDY-Q live cross-check of the after-cutoff salvage chosen on FIT (sal_cost08_1230: after 12:30 keep only entries with
stop cost R = (2 x (1c + 1 bp) + 2c) / |entry - stop| <= 0.08) and of (b)/(c) on the trio's live trades.
Usage: python live_salvage.py LIVE.parquet.  Educational only - not financial advice."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from common import SHORT, TRIO, st  # noqa: E402

t = pd.read_parquet(sys.argv[1])
t = t[t.strategy.isin(TRIO)].copy()
ts = pd.to_datetime(t.signal_time.fillna(t.entry_time).astype(str), utc=True, format="mixed").dt.tz_convert("America/New_York")
t["bar"] = ts.dt.hour * 100 + (ts.dt.minute // 5) * 5
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
t = t.drop_duplicates("k")
t["s"] = t.strategy.map(SHORT)
t["cost_r"] = (2 * (0.01 + t.entry * 1e-4) + 0.02) / (t.entry - t.stop).abs()
for s in ["L3", "RW3", "RW5", "pooled"]:
    x = t if s == "pooled" else t[t.s == s]
    pm = x[x.bar > 1230]
    print(s, "after 12:30 cost<=0.08:", st(pm[pm.cost_r <= 0.08]), "| cost>0.08:", st(pm[pm.cost_r > 0.08]))
    print(s, "cut_1230:", st(x[x.bar <= 1230]), "| sal_cost08_1230:", st(x[(x.bar <= 1230) | (x.cost_r <= 0.08)]))
