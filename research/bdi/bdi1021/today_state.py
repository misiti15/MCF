"""bdi1021 descriptive (paper/live, 1 session): the S1-S4 / L1-L4 SPY state (PLAN.md) at each real entry of 10-21 in
the 5 accounts, and live R after costs in vs out of the state. Usage: python today_state.py <scratch-with-bars>
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
b = pd.read_parquet(S / "bars" / "SPY.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York")
b = b.between_time("09:30", "15:59")
tp = (b.high + b.low + b.close) / 3; vw = (tp * b.volume).cumsum() / b.volume.cumsum()
lo = b.low.cummin(); hi = b.high.cummax()
lo_t = pd.Series([b.low.iloc[:k + 1].idxmin() for k in range(len(b))], index=b.index)
hi_t = pd.Series([b.high.iloc[:k + 1].idxmax() for k in range(len(b))], index=b.index)
X = pd.read_csv(HERE / "per_trade_1021.csv")
X["m"] = pd.to_datetime("2026-10-21 " + X.entry_t).dt.tz_localize("America/New_York")
out = []
for r in X.itertuples():
    k = b.index.searchsorted(r.m) - 1          # last 1-min bar starting before the entry minute
    if k < 0: out.append({}); continue
    c = b.close.iloc[k]; e = (lo_t.iloc[k].hour * 60 + lo_t.iloc[k].minute) <= 630; eh = (hi_t.iloc[k].hour * 60 + hi_t.iloc[k].minute) <= 630
    if r.side == -1:
        a = c > vw.iloc[k]; x = (c / lo.iloc[k] - 1) * 100; ee = e
    else:
        a = c < vw.iloc[k]; x = (1 - c / hi.iloc[k]) * 100; ee = eh
    out.append({"g1": a and x >= 0.3 and ee, "g2": a and x >= 0.5 and ee, "g3": a and x >= 0.3, "g4": a and x >= 0.5})
G = pd.DataFrame(out).fillna(False)
X = pd.concat([X, G], axis=1)
for sd, nm in ((-1, "shorts (S1-S4)"), (1, "longs (L1-L4)")):
    Y = X[X.side == sd]
    print(f"== 10-21 {nm}: {len(Y)} trades, live R sum {Y.live.sum():.1f}, mean {Y.live.mean():+.3f}")
    for g in ("g1", "g2", "g3", "g4"):
        i = Y[Y[g]]; o = Y[~Y[g]]
        print(f"  {g}: in-state {len(i)} trades, mean {i.live.mean():+.3f} (sum {i.live.sum():+.1f}) | out {len(o)}, mean {o.live.mean():+.3f} (sum {o.live.sum():+.1f})")
print("Educational only - not financial advice.")
