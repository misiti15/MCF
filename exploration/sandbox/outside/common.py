"""Shared helpers for track 6 (outside). Educational only - not financial advice."""
import numpy as np
import pandas as pd


def tstat(s):
    s = pd.Series(s).dropna()
    return s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 and s.std() > 0 else float("nan")


def lock_mask(et_min, xt_min, r, X):
    """Profit lock on one account-day. Arrays sorted by entry. Returns keep mask (bool).
    Blocks every entry at or after the first entry time at which closed R (xt <= entry time) >= X."""
    keep = np.ones(len(r), bool)
    if not np.isfinite(X):
        return keep
    for i in range(len(r)):
        closed = r[:i][xt_min[:i] <= et_min[i]].sum()
        if closed >= X - 1e-12:
            keep[i:] = False
            break
    return keep


def summarize(base_day, new_day):
    """base_day/new_day: Series indexed by day-unit. Returns dict of book metrics."""
    d = new_day - base_day
    best = d.max() if len(d) else 0.0
    return dict(n_days=len(d), base_R=base_day.sum(), new_R=new_day.sum(), dR_day=d.mean(), t=tstat(d),
                red_base=int((base_day <= 0).sum()), red_new=int((new_day <= 0).sum()),
                green_base=int((base_day > 0).sum()), green_new=int((new_day > 0).sum()),
                w5_base=base_day.nsmallest(5).sum(), w5_new=new_day.nsmallest(5).sum(),
                dR_wo_best=(d.sum() - best) / max(len(d) - 1, 1),
                best_share=(best / d.sum()) if d.sum() > 0 else float("nan"))
