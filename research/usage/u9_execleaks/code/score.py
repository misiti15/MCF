"""U9 what-ifs (PLAN.md): W1 ETB-as-if-borrowable, W2 target-passed B1 (skip) / B2 (re-anchor). LR8 costs.
Simplified engine: signal stop/target, flat 15:55, 1-min bars from the minute after the signal; stop+target in one
bar = stop; gap through stop fills at the bar open. Trailing / time stops not modelled."""
import sys, glob, sqlite3
import numpy as np, pandas as pd
S = sys.argv[1]
rng = np.random.default_rng(9)
M = {}
for f in sorted(glob.glob(f"{S}/m1/*.parquet")):
    b = pd.read_parquet(f)
    b["t"] = pd.to_datetime(b.ts, utc=True).dt.tz_convert("America/New_York")
    b["mn"] = b.t.dt.hour * 60 + b.t.dt.minute
    b = b[(b.mn >= 570) & (b.mn < 960)]
    for s, g in b.groupby("symbol"):
        M[(f.split("/")[-1][:10], s)] = (g.mn.to_numpy(), g.open.to_numpy(), g.high.to_numpy(), g.low.to_numpy(), g.close.to_numpy())
FLAT = 955
def walk(key, m0, side, entry, stop, target):
    """R after LR8 costs for an entry at `entry` decided at minute m0 (walk starts at m0+1). None if no bars."""
    x = M.get(key)
    if x is None: return None
    mn, o, h, l, c = x
    risk = abs(entry - stop)
    if not risk > 0 or side * (entry - stop) <= 0: return None
    fill = entry * (1 + side * 1e-4) + side * 0.01
    i0 = np.searchsorted(mn, m0 + 1)
    j = max(0, min(len(mn) - 1, np.searchsorted(mn, m0) - 1))   # last completed bar before the decision minute
    if abs(c[j] / entry - 1) > 0.03: return None                  # price sanity (bar/journal mismatch): dropped
    ex = None
    for i in range(i0, len(mn)):
        if mn[i] >= FLAT:
            px = o[i]; ex = px * (1 - side * 1e-4) - side * (0.01 + max(0.01, px * 1e-4)); break
        if side * (o[i] - stop) <= 0:          # gapped through stop
            px = o[i]; ex = px * (1 - side * 1e-4) - side * (0.01 + max(0.02, 4e-4 * px)); break
        hit_s = (l[i] <= stop) if side == 1 else (h[i] >= stop)
        hit_t = target is not None and ((h[i] >= target) if side == 1 else (l[i] <= target))
        if hit_s:
            px = stop; ex = px * (1 - side * 1e-4) - side * (0.01 + max(0.02, 4e-4 * px)); break
        if hit_t:
            ex = target; break
    if ex is None:
        if i0 >= len(mn): return None
        px = c[-1]; ex = px * (1 - side * 1e-4) - side * (0.01 + max(0.01, px * 1e-4))
    return side * (ex - fill) / risk
def minute(ts):
    t = pd.Timestamp(ts).tz_convert("America/New_York"); return t.hour * 60 + t.minute
def tgt(v): return None if pd.isna(v) else float(v)
def rand(key, side, ref, stop, target, n=5):
    x = M.get(key)
    if x is None: return []
    mn, c = x[0], x[4]
    idx = np.where((mn >= 590) & (mn <= 900))[0]
    if len(idx) == 0: return []
    f = abs(ref - stop) / ref
    k = None if target is None else abs(target - ref) / abs(ref - stop)
    out = []
    for i in rng.choice(idx, size=min(n, len(idx)), replace=False):
        e = c[i]; st = e - side * f * e
        tg = None if k is None else e + side * k * f * e
        r = walk(key, mn[i], side, e, st, tg)
        if r is not None: out.append(r)
    return out
rows = []
for name in ("etb", "sub", "tgt"):
    W = pd.read_csv(f"{S}/w_{name}.csv")
    for r in W.itertuples():
        key = (r.day, r.symbol); m0 = minute(r.ts); side = int(r.side); t = tgt(r.target)
        base = dict(set=name, acct=r.acct, day=r.day, strategy=r.strategy, symbol=r.symbol, side=side, ts=r.ts,
                    oid=getattr(r, "broker_order_id", None))
        if name in ("etb", "sub"):
            rr = rand(key, side, r.ref_price, r.stop, t)
            rows.append({**base, "cfg": "W1" if name == "etb" else "W1-ref", "R": walk(key, m0, side, r.ref_price, r.stop, t),
                         "R_rand": np.mean(rr) if rr else None})
        else:
            sh = r.base - r.ref_price
            rows.append({**base, "cfg": "B1", "R": 0.0, "R_rand": None})
            rr = rand(key, side, r.base, r.stop + sh, None if t is None else t + sh)
            rows.append({**base, "cfg": "B2", "R": walk(key, m0, side, r.base, r.stop + sh, None if t is None else t + sh),
                         "R_rand": np.mean(rr) if rr else None})
            rows.append({**base, "cfg": "diag-bt-credit", "R": walk(key, m0, side, r.ref_price, r.stop, t), "R_rand": None})
out = pd.DataFrame(rows)
# live R of the submitted comparison trades (engine calibration)
L = []
for f in sorted(glob.glob(f"{S}/j/*.db")):
    c = sqlite3.connect(f)
    t = pd.read_sql("select broker_order_id oid, entry, stop, shares, pnl_adj, pnl from trades where broker_order_id is not null", c)
    L.append(t)
L = pd.concat(L)
L["R_live"] = L.pnl_adj.fillna(L.pnl) / ((L.entry - L.stop).abs() * L.shares)
L = L.groupby("oid").R_live.sum().reset_index()      # scale-outs: one lot, several rows
out = out.merge(L, on="oid", how="left")
out.to_csv(f"{S}/u9_whatif.csv.gz", index=False)
print(out.groupby("cfg").agg(n=("R", "count"), R=("R", "mean"), Rr=("R_rand", "mean"), live=("R_live", "mean"), nlive=("R_live", "count")))
