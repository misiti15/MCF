"""cov-long round 2 (pre-declared before scoring): late-day intraday momentum in index/sector ETFs (Gao, Han, Li, Zhou
2018: the first half-hour return predicts the last half-hour). Long, non-inverse ETFs only, entry 14:55/15:00 bar close,
t1s1, flat 15:55. Educational only - not financial advice."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

INV = {"PSQ", "QID", "RWM", "SDOW", "SDS", "SPDN", "SPXS", "SPXU", "SQQQ", "SOXS", "TZA", "LABD", "ERY"}
ETF = set(json.load(open(Path(__file__).parent / "etfs.json"))) - INV
ADV = 20e6


def _first30(df, col_fo, col_gap):
    """value at the 10:00 bar close broadcast to the symbol-day: (1+gap)(1+fo@10:00)-1, in %."""
    key = df["symbol"].astype(str) + "|" + df["date"].astype(str)
    at = df["tod"].to_numpy(int) == 1000
    v = ((1 + df[col_gap].astype(float) / 100) * (1 + df[col_fo].astype(float) / 100) - 1) * 100
    s = pd.Series(np.where(at, v, np.nan), index=df.index)
    return s.groupby(key.values).transform("max").to_numpy()


def e(spy_first, spy_now):
    def m(df):
        t = df["tod"].to_numpy(int)
        etf = df["symbol"].astype(str).isin(ETF).to_numpy()
        ok = etf & (t >= 1455) & (t <= 1500) & (df["fromOpen"].to_numpy(float) > 0)
        if spy_first is None:
            ok &= _first30(df, "fromOpen", "gap") >= 0.25
        else:
            ok &= _first30(df, "spy_fo2", "spy_gap") >= spy_first
            ok &= _first30(df, "fromOpen", "gap") >= 0.25 if spy_now is None else df["spy_fo2"].to_numpy(float) > spy_now
        return ok
    return m


CANDS = {"E1-etfmom-own": e(None, None), "E2-etfmom-own-spy": e(0.25, None), "E3-etfmom-spy-now": e(0.25, 0.0)}
