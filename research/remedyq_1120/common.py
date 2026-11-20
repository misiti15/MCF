"""REMEDY-Q (2026-11-20) shared helpers: stats on R-after-costs trade tables. Educational only - not financial advice."""
import math

import numpy as np
import pandas as pd

TRIO = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]
SHORT = {"L3-gap-slope-fromopen-FD": "L3", "RW3-gapdn-rsi5pop-flowsell-short-FD": "RW3",
         "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD": "RW5"}
CUTOFFS = [1200, 1215, 1230, 1245, 1300, 1305, 1315, 1330, 1345, 1400, 1415, 1430, 1500]   # 1500 = no cut (window end)


def clustered_t(r, d):
    r, d = pd.Series(np.asarray(r, float)), pd.Series(np.asarray(d))
    if len(r) < 3:
        return float("nan")
    m = r.mean()
    e = (r - m).groupby(d.values).sum()
    se = math.sqrt(float((e ** 2).sum())) / len(r)
    return float(m / se) if se > 0 else float("nan")


def st(t):
    """t: DataFrame with r, date."""
    if not len(t):
        return dict(n=0, days=0, avg=np.nan, tot=0.0, wo_best=np.nan, tot_wo_top2=0.0, best_share=np.nan, t_day=np.nan)
    day = t.groupby("date").r.sum().sort_values(ascending=False)
    tot = float(t.r.sum())
    best = day.index[0]
    top2 = list(day.index[:2])
    rest = t[t.date != best]
    return dict(n=int(len(t)), days=int(day.size), avg=round(float(t.r.mean()), 4), tot=round(tot, 2),
                wo_best=round(float(rest.r.mean()), 4) if len(rest) else np.nan,
                tot_wo_top2=round(float(t[~t.date.isin(top2)].r.sum()), 2),
                best_share=round(float(day.iloc[0] / tot), 3) if tot > 0 else np.nan,
                t_day=round(clustered_t(t.r, t.date), 2))


def paired_day_t(base, alt, days):
    """day-paired t of (alt - base) day R over the given sessions (0 R on days without trades)."""
    a = alt.groupby("date").r.sum().reindex(days, fill_value=0.0)
    b = base.groupby("date").r.sum().reindex(days, fill_value=0.0)
    d = a - b
    if d.std(ddof=1) == 0 or len(d) < 3:
        return float("nan")
    return float(d.mean() / (d.std(ddof=1) / math.sqrt(len(d))))
