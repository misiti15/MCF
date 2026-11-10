"""top20 (2026-11-09): W60 15-min compass on the open two-year history, for the 2-year "R by compass at entry" split.

Same construction as research/bdi/hc1 (state15.hist() + comp15 W60): SPY / QQQ / IWM from data/cache_hist/1Min with the
locked block 2024-11-01..2025-02-28 filtered out before use, breadth_open from the lab context tables (lab universe;
the live card uses the 200 Hunch names, so this is the HC1 research approximation). Point-in-time: a mark T uses only
bars that start before T. Output: <scratch>/compass2y.parquet (date, T minutes, w60 level -2..2).

Usage: python compass_2y.py <scratch>. Display / research only - not a trading signal. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "hc1"))
import state15  # noqa: E402  (reads sys.argv[1] as its scratch; unused here)

S = Path(sys.argv[1])
st = state15.hist()
st = st[st.date >= "2024-09-16"].sort_values(["date", "T"]).reset_index(drop=True)
assert not ((st.date >= "2024-11-01") & (st.date <= "2025-02-28")).any()
sg = lambda x: np.nan_to_num(np.sign(np.asarray(x, float))).astype(int)
st["s"] = sg(st.fo)
base = st.s + sg(st.vw) + np.where(st.breadth_open > 0.5, 1, np.where(st.breadth_open < 0.5, -1, 0)) + \
    np.where((st.s == sg(st.qqq_fo)) & (st.s == sg(st.iwm_fo)), st.s, 0)
piv = st.pivot(index="date", columns="T", values="s")
pW = np.zeros(len(st), int); nm = np.zeros(len(st), int)
for T in sorted(st["T"].unique()):
    marks = [t for t in piv.columns if T - 60 < t <= T]
    sub = piv[marks]
    same = sub.eq(sub[T], axis=0).all(axis=1) & (sub[T] != 0)
    i = (st["T"] == T).values
    pW[i] = np.where(same.reindex(st.date[i]).values, piv[T].reindex(st.date[i]).values, 0)
    nm[i] = len(marks)
v = base.values + pW
st["w60"] = np.where((v >= 4) & (pW == 1) & (nm >= 2), 2, np.where(v >= 2, 1, np.where((v <= -4) & (pW == -1) & (nm >= 2), -2,
                     np.where(v <= -2, -1, 0))))
st[["date", "T", "w60"]].to_parquet(S / "compass2y.parquet")
print(len(st), st.date.nunique(), "days;", st.w60.value_counts().sort_index().to_dict())
