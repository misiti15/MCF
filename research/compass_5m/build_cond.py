"""COMPASS-5M: build the conditional-stats baseline (mcf/report/compass_cond.py) from SPY 1-minute history (locked block
filtered inside the read) + the live days 11-05..11-09 (research/compass_learn/fetch_live.py output). Usage:
    python build_cond.py <scratch>     -> conditional_obs.csv.gz, conditional_stats.csv (this folder)
After this, the nightly `python -m mcf.report.compass_cond --date D --push` appends one session per night on the
mcf-data-compass data branch. Educational only - not financial advice."""
import gzip
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from mcf.hunch import data as HD  # noqa: E402
from mcf.report import compass_cond as CC  # noqa: E402

S = Path(sys.argv[1])
h = HD.load_1min("SPY", Path("/home/user/MCF/data/cache_hist/1Min"))
h.index = pd.to_datetime(h.index)
h = (h.tz_localize(CC.NY) if h.index.tz is None else h.tz_convert(CC.NY))[["open", "high", "low", "close", "volume"]]
lv = pd.read_parquet(S / "live" / "live_bars.parquet")
lv = lv[lv.symbol == "SPY"].assign(ts=lambda x: pd.to_datetime(x.ts)).set_index("ts")[["open", "high", "low", "close", "volume"]]
lv.index = lv.index.tz_convert(CC.NY)
h = pd.concat([h, lv[lv.index > h.index.max()]]).sort_index()
assert not ((h.index >= pd.Timestamp("2024-11-01", tz=CC.NY)) & (h.index < pd.Timestamp("2025-03-01", tz=CC.NY))).any()
rows, prev = [], None
for d, g in h.groupby(h.index.strftime("%Y-%m-%d")):
    m = g.index.hour * 60 + g.index.minute
    g = g[(m >= 570) & (m < 960)]
    if not len(g) or (g.index.hour * 60 + g.index.minute).max() < 955:
        prev = None                                    # half day / partial: dropped, and no previous close across it
        continue
    pc = prev[1] if prev and (pd.Timestamp(d) - pd.Timestamp(prev[0])).days <= 5 else None
    rows += CC.day_obs(g, d, pc)
    prev = (d, float(g.close.iloc[-1]))
O = pd.DataFrame(rows)[CC.OBS_COLS]
with gzip.open(HERE / "conditional_obs.csv.gz", "wt") as f:
    O.to_csv(f, index=False, float_format="%.6g")
C = CC.cells(O)
C.to_csv(HERE / "conditional_stats.csv", index=False, float_format="%.4f")
print(O.date.nunique(), "sessions", O.date.min(), O.date.max(), len(O), "rows", len(C), "cells")
