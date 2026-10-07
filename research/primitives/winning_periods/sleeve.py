"""Sleeve-level (per setup) profit lock / give-back stop: the 10-06 question 'heat_fade_short alone was +$130 open
at 10:31'. Trigger on the sleeve's marked P/L at a minute close; flatten that sleeve at the next minute's marked
price and block its new entries for the day. Train -> valid, day-clustered. Educational only - not financial advice."""
import itertools
import numpy as np
import pandas as pd

OUT = "research/primitives/winning_periods/"
tr = pd.read_csv(OUT + "trades_with_features.csv")
mark = np.load(OUT + "minute_marks.npy").astype(float)
tr["date"] = pd.to_datetime(tr["date"]).dt.date
V0 = pd.Timestamp("2026-08-26").date()
NM = mark.shape[1]


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 and x.std(ddof=1) > 0 else np.nan


rows = []
days = sorted(tr.date.unique())
for s in sorted(tr.strategy.unique()):
    rules = [("lock", X, 0) for X in (50, 100, 200)] + [("giveback", A, G) for A, G in itertools.product((50, 100, 200), (0.3, 0.5))]
    for kind, A, G in rules:
        diffs, isv = [], []
        for d in days:
            ix = tr.index[(tr.date == d) & (tr.strategy == s)]
            if not len(ix):
                diffs.append(0.0); isv.append(d >= V0); continue
            sub = tr.loc[ix]
            p = np.nansum(mark[ix], axis=0)
            pk = np.maximum.accumulate(p)
            hit = np.flatnonzero(p >= A) if kind == "lock" else np.flatnonzero((pk >= A) & (p <= pk * (1 - G)))
            new = sub.pnl.sum()
            if len(hit):
                k = hit[0]
                new = 0.0
                for j, (_, r) in enumerate(sub.iterrows()):
                    if r.m0 > k:
                        continue
                    new += r.pnl if r.m1 <= k + 1 else mark[ix[j], min(k + 1, NM - 1)]
            diffs.append(new - sub.pnl.sum()); isv.append(d >= V0)
        diffs, isv = np.array(diffs), np.array(isv)
        rows.append(dict(rule=f"sleeve-{kind}-{A}-{G}-{s}", train_gain=round(diffs[~isv].sum(), 1), train_t=round(tstat(diffs[~isv]), 2),
                         valid_gain=round(diffs[isv].sum(), 1), valid_t=round(tstat(diffs[isv]), 2)))
df = pd.DataFrame(rows)
df.to_csv(OUT + "sleeve_grid.csv", index=False)
pd.set_option("display.width", 200)
print(df.to_string())
