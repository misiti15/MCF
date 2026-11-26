"""REGSTEER-1126 parity: vectorised bench W60 (rs_states.py marks.parquet) vs mcf.report.compass_live.compute() itself on the
same cached bars (12 sample days, both caches), and bench (177-name proxy, cache bars) vs live compute() on Alpaca bars with
200 names (compass_rd_1126 backfill) on the overlap 10-06..11-04. Usage: python rs_parity.py STATES SCR. Educational only."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parents[1])); sys.path.insert(0, str(H))
import rs_states as S  # noqa: E402
from mcf.report import compass_live as CL  # noqa: E402

ST, SCR = Path(sys.argv[1]), Path(sys.argv[2])
M = pd.read_parquet(ST / "marks.parquet")
names = [n for n in CL.universe() if (S.HIST / f"{n}.parquet").exists() and (S.FRESH / f"{n}.parquet").exists()]
rng = np.random.default_rng(1126)
days = sorted(str(d) for d in rng.choice(sorted(M.date.unique()), 12, replace=False))
import pyarrow.dataset as pads


def day_bars(sym, src, d):
    f = pads.field("__index_level_0__")
    a = pd.Timestamp(d, tz=S.TZ)
    b = pads.dataset(str(src / f"{sym}.parquet"), format="parquet").to_table(
        filter=(f >= a) & (f < a + pd.Timedelta(days=1))).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(S.TZ)
    m = b.index.hour * 60 + b.index.minute
    return b[(m >= 570) & (m < 960)].sort_index()


agree = tot = 0
for d in days:
    src = S.FRESH if d <= S.T2_HI else S.HIST
    bars = {}
    for s in ["SPY", "QQQ", "IWM"] + names:
        S.no_locked([d])
        x = day_bars(s, src, d)
        if len(x):
            bars[s] = x[["open", "high", "low", "close", "volume"]].astype(float)
    rows = CL.compute(bars, d, pd.Timestamp(f"{d} 16:30", tz=CL.NY), names=names)
    lv = {int(r["T"][:-3]) * 60 + int(r["T"][-2:]): {v: k for k, v in CL.NAMES.items()}[r["w60"]] for r in rows}
    m = M[M.date == d].set_index("T").level
    for T, L in lv.items():
        tot += 1; agree += int(m.get(T, -99) == L)
print(f"vectorised vs compute(): {agree}/{tot} marks equal on {len(days)} days")
lm = pd.read_parquet(SCR / "live_compass_marks.parquet")
lm["level"] = lm.w60.map({v: k for k, v in CL.NAMES.items()}); lm["T"] = lm["m"].astype(int)
j = lm.merge(M, on=["date", "T"], suffixes=("_live", "_bench"))
side = lambda x: np.where(x == 2, 1, np.where(x == -2, -1, 0))  # noqa: E731
print(f"bench proxy vs live compute (overlap {j.date.nunique()} days, {len(j)} marks): level equal "
      f"{(j.level_live == j.level_bench).mean():.3f}, confirmed side equal {(side(j.level_live) == side(j.level_bench)).mean():.3f}")
