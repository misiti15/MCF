"""Time-in-trade profile for heat_fade_long baseline exits (train by default; valid descriptive only after finalists fixed).
Educational only — not financial advice."""
import sys
import numpy as np, pandas as pd
from research.exits import harness as H
from mcf.strategies.base import Signal
SETUP = "heat_fade_long"
SPLIT = sys.argv[1] if len(sys.argv) > 1 else "train"
assert SPLIT in ("train", "valid")
NOTGT = len(sys.argv) > 2 and sys.argv[2] == "notarget"
sigs = H.load(); lo, hi = H.SPLITS[SPLIT]
CK = (5, 10, 15, 30, 45, 60, 90, 120, 180)
rows = []
for s in sigs:
    if s["sig"]["strategy"] != SETUP or not (lo <= s["date"] <= hi): continue
    d = {k: v for k, v in s["sig"].items() if k in H._SIG_FIELDS}
    if NOTGT: d["target"] = None
    bars = H._day(s["symbol"], s["date"])
    if bars.empty or d["bar_index"] >= len(bars): continue
    tr = H.simulate(Signal(**d), bars, H._flat, H._costs)
    if tr is None: continue
    mins = (tr.exit_time - tr.entry_time).total_seconds() / 60
    side = d["side"]; ei = bars.index.get_indexer([tr.entry_time], method="bfill")[0]
    c = bars["close"].to_numpy(); h = bars["high"].to_numpy(); l = bars["low"].to_numpy()
    fill = tr.entry; rk = side * (fill - d["stop"])
    mtm, mfe = {}, {}
    for m in CK:
        k = ei + m - 1
        if m <= mins and k < len(c):
            mtm[m] = side * (c[k] - fill) / rk
            seg = h[ei:k+1] if side == 1 else l[ei:k+1]
            mfe[m] = (side * (seg - fill)).max() / rk
    rows.append(dict(date=s["date"], r=tr.r_multiple, reason=tr.exit_reason, mins=mins, entry=tr.entry_time.time(),
                     **{f"mtm{m}": mtm.get(m) for m in CK}, **{f"mfe{m}": mfe.get(m) for m in CK}))
df = pd.DataFrame(rows)
print(SPLIT, "notarget" if NOTGT else "baseline", "n", len(df), "mean R", round(df.r.mean(), 4))
df["bucket"] = pd.cut(df.mins, [0, 5, 15, 30, 60, 120, 240, 999])
print(df.groupby("bucket", observed=True).agg(n=("r", "size"), meanR=("r", "mean"), win=("r", lambda x: (x > 0).mean())).round(3))
print(df.groupby("reason").agg(n=("r", "size"), meanR=("r", "mean"), med_min=("mins", "median"), p25=("mins", lambda x: x.quantile(.25)), p75=("mins", lambda x: x.quantile(.75))).round(2))
for m in (15, 30, 45, 60, 90, 120, 180):
    op = df[df.mins > m]
    if len(op) < 10: continue
    print(f"\nstill open at {m}m: n={len(op)}, final meanR={op.r.mean():.3f}, mtm@{m}={op[f'mtm{m}'].mean():.3f} (holding adds {op.r.mean()-op[f'mtm{m}'].mean():+.3f}R)")
    for a, b in ((-9, 0.1), (0.1, 0.3), (0.3, 0.6), (0.6, 9)):
        g = op[(op[f"mfe{m}"] >= a) & (op[f"mfe{m}"] < b)]
        if len(g): print(f"   mfe@{m} in [{a},{b}): n={len(g)} finalR={g.r.mean():.3f} mtm={g[f'mtm{m}'].mean():.3f}")
