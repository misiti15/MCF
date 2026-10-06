"""Time-in-trade profile for intraday_momentum baseline exits (train by default; valid descriptive only, run after finalists fixed).
Mark-to-market R (gross, bar close, vs fill) at each minute after entry. Educational only — not financial advice."""
import sys
import numpy as np, pandas as pd
from research.exits import harness as H
from mcf.strategies.base import Signal
SPLIT = sys.argv[1] if len(sys.argv) > 1 else "train"
assert SPLIT in ("train", "valid")
sigs = H.load(); lo, hi = H.SPLITS[SPLIT]
rows = []
for s in sigs:
    if s["sig"]["strategy"] != "intraday_momentum" or not (lo <= s["date"] <= hi): continue
    d = {k: v for k, v in s["sig"].items() if k in H._SIG_FIELDS}
    bars = H._day(s["symbol"], s["date"])
    if bars.empty or d["bar_index"] >= len(bars): continue
    tr = H.simulate(Signal(**d), bars, H._flat, H._costs)
    if tr is None: continue
    side = d["side"]; ei = bars.index.get_indexer([tr.entry_time], method="bfill")[0]
    c = bars["close"].to_numpy(); h = bars["high"].to_numpy(); l = bars["low"].to_numpy()
    rk = side * (tr.entry - d["stop"])
    row = dict(date=s["date"], sym=s["symbol"], side=side, r=tr.r_multiple, reason=tr.exit_reason,
               entry=str(tr.entry_time.time()), exit=str(tr.exit_time.time()), risk_bps=1e4 * rk / tr.entry,
               mfe=(side * ((h if side == 1 else l)[ei:ei + 25] - tr.entry)).max() / rk,
               mae=(side * ((l if side == 1 else h)[ei:ei + 25] - tr.entry)).min() / rk)
    for m in (1, 5, 10, 15, 20, 24):
        k = ei + m - 1
        row[f"m{m}"] = side * (c[k] - tr.entry) / rk if k < len(c) else np.nan
    rows.append(row)
df = pd.DataFrame(rows)
print(SPLIT, "n", len(df), "days", df.date.nunique(), "mean R", round(df.r.mean(), 4))
print("entry times", df.entry.value_counts().to_dict(), "exit times", df.exit.value_counts().head(5).to_dict())
print("risk (stop distance) bps: median", round(df.risk_bps.median(), 1), "| MFE R median", round(df.mfe.median(), 3),
      "| MAE R median", round(df.mae.median(), 3), "| share MFE>=0.25R", round((df.mfe >= .25).mean(), 3), ">=0.5R", round((df.mfe >= .5).mean(), 3))
print("mean gross MTM R by minute:", {m: round(df[f"m{m}"].mean(), 4) for m in (1, 5, 10, 15, 20, 24)})
print("share in profit by minute:", {m: round((df[f"m{m}"] > 0).mean(), 3) for m in (1, 5, 10, 15, 20, 24)})
print("net R by side:", df.groupby("side").r.agg(["size", "mean"]).round(4).to_dict())
print("net R by symbol:", df.groupby("sym").r.agg(["size", "mean"]).round(4).to_dict())
for m in (5, 10, 15):
    for name, g in (("ahead", df[df[f"m{m}"] > 0]), ("behind", df[df[f"m{m}"] <= 0])):
        print(f" at {m}m {name}: n={len(g)} mtm={g[f'm{m}'].mean():.3f} -> final net R={g.r.mean():.3f} (gross change to m24 {(g.m24 - g[f'm{m}']).mean():+.3f})")
daily = df.groupby("date").r.sum()
print("day-clustered: days", len(daily), "mean R/trade", round(df.r.mean(), 4),
      "day-cluster SE of mean/trade", round(daily.std(ddof=1) * np.sqrt(len(daily)) / len(df), 4))
