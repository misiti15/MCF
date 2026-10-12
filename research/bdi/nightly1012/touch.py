import sys, pandas as pd, numpy as np
S = sys.argv[1]
T = pd.read_csv(f"{S}/trades_all.csv")
for c in ("entry_time", "exit_time"): T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
cache = {}
out = []
for r in T[T.target.notna() & (T.exit_reason != "target")].itertuples():
    b = cache.setdefault(r.symbol, pd.read_parquet(f"{S}/bars/{r.symbol}.parquet"))
    w = b[(b.index >= r.entry_time.ceil("min")) & (b.index < r.exit_time.floor("min"))]   # full bars strictly inside the hold
    if w.empty: continue
    thr = r.target + r.side * 0.01
    hit = (w.high >= thr) if r.side == 1 else (w.low <= thr)
    sh = (w.low <= r.stop - 0.01) if r.side == 1 else (w.high >= r.stop + 0.01)
    if hit.any():
        out.append((r.acct, r.symbol, r.strategy, r.entry_time.strftime("%H:%M"), r.exit_reason, round(r.r_multiple, 2), hit.idxmax().strftime("%H:%M"), round(r.pnl, 2)))
    if sh.any() and r.exit_reason != "stop":
        print("STOP crossed but exit", r.exit_reason, r.acct, r.symbol, r.strategy, sh.idxmax().strftime("%H:%M"), r.exit_time.strftime("%H:%M"))
print(len(out), "trades whose target was traded through by >=1c inside the hold without a target exit")
for o in out: print(o)
