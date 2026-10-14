"""Journal exit (and entry) prices vs the SIP 1-min bar range at that minute (+-1 min). Flags fills outside the traded range.
Educational only."""
import sys, pandas as pd
S = sys.argv[1]
T = pd.read_csv("trades.csv")
for c in ("nt", "et"):
    T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
bars = {}
def rng(s, t):
    if s not in bars:
        b = pd.read_parquet(f"{S}/bars/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York"); bars[s] = b
    b = bars[s]; w = b[(b.index >= t.floor("1min") - pd.Timedelta("1min")) & (b.index <= t.floor("1min") + pd.Timedelta("1min"))]
    return (w.low.min(), w.high.max()) if len(w) else (None, None)
out = []
for r in T.itertuples():
    for k, px, t in (("exit", r.exit, r.et), ("entry", r.entry, r.nt)):
        lo, hi = rng(r.symbol, t)
        if lo is None:
            out.append(dict(acct=r.acct, symbol=r.symbol, strategy=r.strategy, leg=k, px=px, t=t, lo=None, hi=None, off=None, pnl=r.pnl, reason=r.exit_reason)); continue
        off = max(lo - px, px - hi, 0)
        if off > 0.002 * px:
            out.append(dict(acct=r.acct, symbol=r.symbol, strategy=r.strategy, leg=k, px=px, t=t, lo=lo, hi=hi, off=round(off, 3), pnl=r.pnl, reason=r.exit_reason))
o = pd.DataFrame(out); pd.set_option("display.width", 250)
print(o.to_string() if len(o) else "none"); o.to_csv("exitcheck.csv", index=False)
