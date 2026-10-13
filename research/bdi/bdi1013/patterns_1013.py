"""Loss types for 2026-10-13 trades (same classifier as nightly1012/ltype.py), merged into research/bdi/patterns.csv.
Educational only - not financial advice.  Usage: python patterns_1013.py <bars_dir>"""
import sys, pandas as pd
bars = sys.argv[1]
T = pd.read_csv("research/bdi/nightly1013/trades.csv")
for c in ("entry_time", "exit_time"): T[c] = pd.to_datetime(T[c], utc=True, format="mixed").dt.tz_convert("America/New_York")
EOD = pd.Timestamp("2026-10-13 15:55", tz="America/New_York")
cache = {}
def first_hit(b, side, up, dn):
    for x in b.itertuples():
        if side == 1:
            if x.low <= dn: return "stop"
            if x.high >= up: return "target"
        else:
            if x.high >= dn: return "stop"
            if x.low <= up: return "target"
    return "none"
def bars_of(s):
    if s not in cache:
        b = pd.read_parquet(f"{bars}/{s}.parquet")
        b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York") if b.index.tz is None or str(b.index.tz) != "America/New_York" else b.index
        cache[s] = b.between_time("09:30", "15:59")
    return cache[s]
L = T[T.pnl < 0]
rows, nm = [], {"p": "primary", "t1": "testing", "t2": "testing2"}
for r in L.itertuples():
    b = bars_of(r.symbol); o = b.open.iloc[0]
    pre = b[b.index < r.entry_time.floor("min")]
    from_open = (pre.close.iloc[-1] / o - 1) * 100 if len(pre) else 0
    after = b[(b.index > r.entry_time.floor("min")) & (b.index <= EOD)]
    rk = r.risk
    opp = first_hit(after, -r.side, r.entry - r.side * rk, r.entry + r.side * rk)
    post = b[(b.index > r.exit_time.floor("min")) & (b.index <= EOD)]
    mfe = r.mfe if r.mfe == r.mfe else 0.0
    rev = r.exit_reason == "stop" and r.target == r.target and len(post) and ((post.high.max() >= r.target) if r.side == 1 else (post.low.min() <= r.target))
    if rev: lt = "stopped_then_reversed"
    elif abs(from_open) >= 3 and opp == "target": lt = "wrong_side_after_big_swing"
    elif mfe >= 0.5: lt = "gave_back_gains"
    elif r.exit_reason == "flatten": lt = "late_hold"
    elif mfe < 0.15: lt = "never_worked"
    else: lt = "small MFE then failed (0.15-0.5R)"
    rows.append(f"2026-10-13,{nm[r.acct]},{r.symbol},{r.strategy},{'long' if r.side == 1 else 'short'},{lt},nightly1013 autopsy; r {r.r_multiple:.2f}; mfe {mfe:.2f}; lot {r.lot_no}")
P = open("research/bdi/patterns.csv").read().rstrip("\n").split("\n")
P = [p for p in P if not p.startswith("2026-10-13,")]  # idempotent merge
open("research/bdi/patterns.csv", "w").write("\n".join(P + rows) + "\n")
D = pd.DataFrame([r.split(",")[:6] for r in rows], columns=["date", "acct", "sym", "setup", "side", "lt"])
print(len(rows), "rows"); print(D.groupby(["acct", "lt"]).size().unstack(fill_value=0).to_string())
