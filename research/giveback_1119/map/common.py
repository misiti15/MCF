"""Shared helpers for the giveback map. Educational only - not financial advice."""
import numpy as np, pandas as pd
CK = (5, 10, 15, 30, 45, 60, 90, 120)
STATES = ("below", "faded", "flat", "working", "other")

def state(mk, mf):
    """PLAN.md states, exclusive in this order."""
    return np.select([mk <= -0.5, (mf >= 0.5) & (mk <= 0), (mf < 0.25) & (mk > -0.5) & (mk < 0.25), mk >= 0.5],
                     list(STATES[:4]), default="other")

def dstat(x, r="r", date="date"):
    """mean, day-clustered t, n, days, avg w/o best day, best-day share of the total."""
    v = x[r].to_numpy(float); n = len(v)
    if n < 2: return dict(n=n, mean=np.nan, t=np.nan)
    g = x.groupby(date)[r].agg(["sum", "size"]); mu = v.mean()
    se = np.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / n if len(g) > 1 else np.nan
    b = g["sum"].idxmax(); tot = g["sum"].sum()
    return dict(n=n, days=len(g), mean=mu, t=mu / se if se and se > 0 else np.nan,
                wo_best=(tot - g.loc[b, "sum"]) / max(1, n - g.loc[b, "size"]), best_share=g.loc[b, "sum"] / tot if tot else np.nan)

def tod_bucket(m):
    return pd.cut(m, [0, 630, 720, 840, 2000], right=False, labels=["09:30-10:30", "10:30-12:00", "12:00-14:00", "14:00+"])

def hold_bucket(h):
    return pd.cut(h, [-1, 15, 60, 120, 240, 1e9], labels=["<=15m", "15-60m", "1-2h", "2-4h", ">4h"])

def md(df, fmt="{:.3f}"):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype.kind == "f": df[c] = df[c].map(lambda v: "" if pd.isna(v) else fmt.format(v))
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(out)
