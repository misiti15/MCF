"""p1_1029: pre-open regime inputs per session (all known before 09:30 ET, except the overnight gap which uses the
09:30 open print and is known before any entry >= 09:50). Daily bars from research/history2y lib.daily() (locked
block excluded by the loader). A rolling window never spans the locked gap (segments). The gates1021 `spy_prev`
column (lookahead, regime1022) is not used.
Educational only - not financial advice.

    python research/bdi/p1_1029/regime_days.py      # -> research/bdi/p1_1029/regime_days.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib  # noqa: E402

OUT = Path(__file__).resolve().parent


def per_symbol(d, s):
    x = d[d.symbol == s].sort_values("date").reset_index(drop=True)
    dt = pd.to_datetime(x["date"])
    seg = (dt.diff().dt.days > 5).cumsum()
    g = x.groupby(seg)
    pc = g["close"].shift(1)  # prior close (d-1)
    tr = np.maximum(x["high"], pc) - np.minimum(x["low"], pc)
    x["tr_pct"] = tr / x["close"] * 100
    x["ret"] = x["close"] / pc - 1
    out = pd.DataFrame({"date": x["date"]})
    # values as of the prior session's close, shifted onto session d
    sma20 = g["close"].transform(lambda c: c.rolling(20).mean())
    atr14 = x.groupby(seg)["tr_pct"].transform(lambda c: c.rolling(14).mean())
    rv20 = x.groupby(seg)["ret"].transform(lambda c: c.rolling(20).std() * 100)
    ch5 = g["close"].transform(lambda c: c.pct_change(5) * 100)
    for k, v in {"above_sma20": (x["close"] > sma20).where(sma20.notna()), "ret": x["ret"] * 100, "atr14": atr14,
                 "rv20": rv20, "ch5": ch5}.items():
        out[f"{s}_{k}_prev"] = v.groupby(seg).shift(1)
    out[f"{s}_gap"] = (x["open"] / pc - 1) * 100
    return out.set_index("date")


def trail_pct(v, q, n=250, minn=60):
    """True where v[d] is above the q-quantile of the previous n non-NaN values (min minn); NaN if not enough history."""
    vals = v.to_numpy(float)
    out = np.full(len(vals), np.nan)
    hist = []
    for i, x in enumerate(vals):
        if np.isfinite(x) and len(hist) >= minn:
            out[i] = float(x > np.quantile(hist[-n:], q))
        if np.isfinite(x):
            hist.append(x)
    return out


def main():
    d = lib.daily()
    R = per_symbol(d, "SPY").join(per_symbol(d, "QQQ")).join(per_symbol(d, "VXX"))
    R = R.sort_index()
    for q in (0.7, 0.8, 0.9):
        R[f"hi_atr_{int(q*100)}"] = trail_pct(R["SPY_atr14_prev"], q)
        R[f"hi_rv_{int(q*100)}"] = trail_pct(R["SPY_rv20_prev"], q)
    R["hi_vxx5_80"] = trail_pct(R["VXX_ch5_prev"], 0.8)
    R.to_csv(OUT / "regime_days.csv")
    print(R.describe().T.round(3).to_string())
    print("sessions", len(R), "ungated (NaN) share:", R[["hi_atr_80", "hi_rv_80", "hi_vxx5_80", "SPY_above_sma20_prev"]].isna().mean().round(3).to_dict())


if __name__ == "__main__":
    main()
