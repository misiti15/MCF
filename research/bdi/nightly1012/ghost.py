"""Simulate the submitted-but-unreconciled bracket orders on SIP 1-min bars (stop-first inside a bar, flat 15:55)."""
import sys, sqlite3, pandas as pd, numpy as np
S, a = sys.argv[1], sys.argv[2]
c = sqlite3.connect(f"{S}/{a}/journal.db")
O = pd.read_sql("""select o.created_at, o.symbol, o.strategy, o.side, o.qty, o.entry_ref, o.stop, o.target, o.broker_order_id from orders o
 where o.created_at like '2026-10-12%' and o.status='submitted'""", c)
O["t"] = pd.to_datetime(O.created_at, utc=True).dt.tz_convert("America/New_York")
res = []
for r in O.itertuples():
    f = f"{S}/bars/{r.symbol}.parquet"
    try: b = pd.read_parquet(f)
    except Exception:
        import subprocess; res.append((r.symbol, None, None, None)); continue
    w = b[(b.index > r.t.floor("min")) & (b.index <= pd.Timestamp("2026-10-12 15:55", tz="America/New_York"))]
    e = r.entry_ref; out, why, when = None, "flat", None
    for ts, x in w.iterrows():
        if r.side == 1:
            if x.low <= r.stop: out, why = min(r.stop, x.open), "stop"
            elif r.target == r.target and x.high >= r.target: out, why = max(r.target, x.open), "target"
        else:
            if x.high >= r.stop: out, why = max(r.stop, x.open), "stop"
            elif r.target == r.target and x.low <= r.target: out, why = min(r.target, x.open), "target"
        if out is not None: when = ts; break
    if out is None: out = w.close.iloc[-1] if len(w) else e; when = w.index[-1] if len(w) else None
    pnl = r.side * (out - e) * r.qty
    res.append((r.symbol, r.strategy, why, round(pnl, 2), when.strftime("%H:%M") if when is not None else None))
R = pd.DataFrame(res, columns=["sym", "strategy", "exit", "pnl", "when"])
print(a, "orders", len(R), "sim pnl", round(R.pnl.sum(), 2)); print(R.exit.value_counts().to_dict())
print(R.groupby("exit").pnl.agg(["size", "sum"]).round(2).to_string())
print(R.sort_values("pnl").head(5).to_string())
