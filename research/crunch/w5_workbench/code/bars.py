"""W5 Part D: stream 1-min release packs (public release assets), keep only the demo symbol-days, delete each pack."""
import os, subprocess, pickle, numpy as np, pandas as pd
S = "<scratch>"
SET = ["RW7-gapdn-bounce-early-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
       "RW1-gapdn-bounce-flowsell-short-FD", "L3-gap-slope-rsi5hi-FD"]
t = pd.read_pickle(f"{S}/trades.pkl"); x = t[t.strategy.isin(SET)].copy(); x.to_pickle(f"{S}/demo_trades.pkl")
need = x.groupby("date").symbol.apply(set)
paths = {}
for d, syms in need.items():
    assert not ("2024-11-01" <= d <= "2025-02-28")
    f = f"{S}/pack.parquet"
    url = f"https://github.com/misiti15/MCF/releases/download/bars-{d[:7]}/1min-{d}.parquet"
    r = subprocess.run(["curl", "-sSfL", "-o", f, url], capture_output=True)
    if r.returncode: print(d, "no pack"); continue
    m = pd.read_parquet(f, filters=[("symbol", "in", sorted(syms))]); os.remove(f)
    m["ts"] = pd.to_datetime(m.ts, utc=True).dt.tz_convert("America/New_York")
    m = m[(m.ts.dt.strftime("%H:%M") >= "09:30") & (m.ts.dt.strftime("%H:%M") < "16:00")]
    for s, b in m.groupby("symbol", observed=True):
        b = b.sort_values("ts")
        paths[(d, str(s))] = dict(m=((b.ts.dt.hour * 60 + b.ts.dt.minute) - 570).to_numpy(), o=b.open.to_numpy(),
                                  h=b.high.to_numpy(), l=b.low.to_numpy(), c=b.close.to_numpy())
    print(d, len(syms), flush=True)
pickle.dump(paths, open(f"{S}/paths.pkl", "wb"))
print("symbol-days", len(paths), "of", int(need.apply(len).sum()))
