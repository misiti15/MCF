"""Time-in-trade profile for orb20_a baseline exits (train by default; valid descriptive only, after finalists were fixed). Educational only — not financial advice."""
import numpy as np, pandas as pd
from research.exits import harness as H
from mcf.strategies.base import Signal
import sys
SPLIT = sys.argv[1] if len(sys.argv) > 1 else "train"
assert SPLIT in ("train", "valid")
sigs = H.load(); lo, hi = H.SPLITS[SPLIT]
rows = []
for s in sigs:
    if s["sig"]["strategy"] != "orb20_a" or not (lo <= s["date"] <= hi): continue
    d = {k: v for k, v in s["sig"].items() if k in H._SIG_FIELDS}
    bars = H._day(s["symbol"], s["date"])
    if bars.empty or d["bar_index"] >= len(bars): continue
    tr = H.simulate(Signal(**d), bars, H._flat, H._costs)
    if tr is None: continue

    mins = (tr.exit_time - tr.entry_time).total_seconds() / 60
    # mark-to-market R at checkpoints (gross, close of bar) while still open
    side = d["side"]; ei = bars.index.get_indexer([tr.entry_time], method="bfill")[0]
    c = bars["close"].to_numpy(); h = bars["high"].to_numpy(); l = bars["low"].to_numpy()
    fill = tr.entry; rk = side * (fill - d["stop"])
    mtm = {}; mfe = {}
    for m in (15, 30, 60, 90, 120, 180):
        k = ei + m - 1
        if m <= mins and k < len(c):
            mtm[m] = side * (c[k] - fill) / rk
            seg = h[ei:k+1] if side == 1 else l[ei:k+1]
            mfe[m] = (side * (seg - fill)).max() / rk
    rows.append(dict(date=s["date"], r=tr.r_multiple, reason=tr.exit_reason, mins=mins, entry=tr.entry_time.time(),
                     **{f"mtm{m}": mtm.get(m) for m in (15,30,60,90,120,180)}, **{f"mfe{m}": mfe.get(m) for m in (15,30,60,90,120,180)}))
df = pd.DataFrame(rows)
print("n", len(df), "mean R", df.r.mean().round(4))
df["bucket"] = pd.cut(df.mins, [0, 15, 30, 60, 120, 240, 999])
print(df.groupby("bucket", observed=True).agg(n=("r","size"), meanR=("r","mean"), win=("r", lambda x: (x>0).mean())).round(3))
print(df.groupby("reason").agg(n=("r","size"), meanR=("r","mean"), med_min=("mins","median")).round(3))
for m in (30, 60, 90, 120):
    op = df[df.mins > m]
    if len(op) < 10: continue
    print(f"\nstill open at {m}m: n={len(op)}, final meanR={op.r.mean():.3f}, mtm@{m}={op[f'mtm{m}'].mean():.3f}  (holding on adds {op.r.mean()-op[f'mtm{m}'].mean():+.3f}R gross-ish)")
    for lo_, hi_ in ((-9, 0), (0, 0.5), (0.5, 9)):
        g = op[(op[f"mfe{m}"] >= lo_) & (op[f"mfe{m}"] < hi_)] if lo_ > -9 else op[op[f"mfe{m}"] < hi_]
        if len(g): print(f"   mfe@{m} in [{lo_},{hi_}): n={len(g)} finalR={g.r.mean():.3f} mtm={g[f'mtm{m}'].mean():.3f}")
