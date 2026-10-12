"""Loss types (10-09 precedence minus news) and opposite-side 1R/1R check for today's losers."""
import sys, pandas as pd, numpy as np
pd.set_option("display.width", 250)
S = sys.argv[1]
T = pd.read_csv(f"{S}/trades_all.csv")
for c in ("entry_time", "exit_time"): T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
EOD = pd.Timestamp("2026-10-12 15:55", tz="America/New_York")
cache = {}
def first_hit(b, side, entry, up, dn):
    for ts, x in b.iterrows():
        if side == 1:
            if x.low <= dn: return "stop"
            if x.high >= up: return "target"
        else:
            if x.high >= dn: return "stop"
            if x.low <= up: return "target"
    return "none"
out = []
for r in T.itertuples():
    b = cache.setdefault(r.symbol, pd.read_parquet(f"{S}/bars/{r.symbol}.parquet").between_time("09:30", "15:59"))
    o = b.open.iloc[0]
    pre = b[b.index < r.entry_time.floor("min")]
    from_open = (pre.close.iloc[-1] / o - 1) * 100 if len(pre) else 0
    after = b[(b.index > r.entry_time.floor("min")) & (b.index <= EOD)]
    rk = r.risk
    opp = first_hit(after, -r.side, r.entry, r.entry - r.side * rk, r.entry + r.side * rk)
    lt = None
    if r.pnl < 0:
        post = b[(b.index > r.exit_time.floor("min")) & (b.index <= EOD)]
        rev = r.exit_reason == "stop" and r.target == r.target and len(post) and ((post.high.max() >= r.target) if r.side == 1 else (post.low.min() <= r.target))
        if rev: lt = "stopped then reversed"
        elif abs(from_open) >= 3 and opp == "target": lt = "wrong side after big swing"
        elif r.mfe >= 0.5: lt = "gave back gains"
        elif r.exit_reason == "flatten": lt = "late hold"
        elif r.mfe < 0.15: lt = "never worked"
        else: lt = "small MFE then failed (0.15-0.5R)"
    out.append((r.Index, from_open, opp, lt))
O = pd.DataFrame(out, columns=["i", "from_open", "opp", "loss_type"]).set_index("i")
T = T.join(O)
T.to_csv(f"{S}/trades_typed.csv", index=False)
L = T[T.pnl < 0]
print(L.groupby(["acct", "loss_type"]).agg(n=("pnl", "size"), pnl=("pnl", "sum")).round(1).to_string())
for a in ("p", "t1", "t2"):
    d = T[T.acct == a]
    print(a, "opp 1R/1R target-first: losers", (d[d.pnl < 0].opp == "target").sum(), "/", (d.pnl < 0).sum(), " winners", (d[d.pnl > 0].opp == "target").sum(), "/", (d.pnl > 0).sum())
print(L[L.acct == "t2"].groupby(["strategy", "loss_type"]).size().unstack(fill_value=0).to_string())
# patterns.csv rows (same format) for today
rows = []
nm = {"p": "primary", "t1": "testing", "t2": "testing2"}
for r in L.itertuples():
    rows.append(f"2026-10-12,{nm[r.acct]},{r.symbol},{r.strategy},{'long' if r.side == 1 else 'short'},{r.loss_type},nightly1012 autopsy; r {r.r_multiple:.2f}; mfe {r.mfe:.2f}")
open(f"{S}/patterns_1012.csv", "w").write("\n".join(rows) + "\n")
print(len(rows), "pattern rows")
