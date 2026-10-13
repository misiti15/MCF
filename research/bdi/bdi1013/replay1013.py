"""Descriptive replay (not counted, not gated): which 2026-10-13 shorts the split-tape gates would have skipped.
Context = QQQ / IWM / SPY 1-minute bars of 2026-10-13 at the last completed minute before each entry.
    python replay1013.py <bars_dir>     Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
B = sys.argv[1]
T = pd.read_csv("research/bdi/nightly1013/trades.csv")
T = T[T.side == -1].copy()
T["nt"] = pd.to_datetime(T["entry_time"], utc=True, format="mixed").dt.tz_convert("America/New_York")
cx = {}
for e in ("QQQ", "IWM", "SPY"):
    b = pd.read_parquet(f"{B}/{e}.parquet").between_time("09:30", "15:59")
    tp = (b.high + b.low + b.close) / 3
    cx[e + "_fo"] = (b.close / b.open.iloc[0] - 1) * 100
    cx[e + "_vw"] = (b.close / ((tp * b.volume).cumsum() / b.volume.cumsum()) - 1) * 100
    cx[e + "_d30"] = (b.close / b.close.shift(30) - 1) * 100
X = pd.DataFrame(cx)
X.index = X.index + pd.Timedelta(minutes=1)          # value known at the minute's end
k = X.reindex(T.nt.dt.floor("min"), method="ffill")
for c in X.columns: T["x_" + c] = k[c].to_numpy()
G = {"G1-split": (T.x_QQQ_fo > 0) & (T.x_QQQ_vw > 0) & (T.x_IWM_fo < 0),
     "G6-div0.25": (T.x_QQQ_fo - T.x_IWM_fo) >= 0.25, "G7-div0.50": (T.x_QQQ_fo - T.x_IWM_fo) >= 0.50,
     "G8-div0.75": (T.x_QQQ_fo - T.x_IWM_fo) >= 0.75}
rows = []
for a in ("p", "t1", "t2"):
    d = T[T.acct == a]
    for g, m in G.items():
        mm = m[d.index]
        rows.append({"acct": a, "gate": g, "shorts": len(d), "pnl_all": round(d.pnl.sum(), 2), "blocked": int(mm.sum()),
                     "blocked_pnl": round(d.pnl[mm].sum(), 2), "blocked_avgR": round(d.r_multiple[mm].mean(), 3),
                     "kept_pnl": round(d.pnl[~mm].sum(), 2), "kept_avgR": round(d.r_multiple[~mm].mean(), 3)})
R = pd.DataFrame(rows); print(R.to_string(index=False))
R.to_csv("research/bdi/bdi1013/replay1013.csv", index=False)
print(X.resample("30min").last().round(2).to_string())
