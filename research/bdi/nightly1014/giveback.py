"""Account give-back after the intraday peak: lots open at the peak mark, their marked P/L at the peak vs final,
split by side / exit / setup. Educational only."""
import sys, pandas as pd
S, acct, hh = sys.argv[1], sys.argv[2], sys.argv[3]
T = pd.read_csv("trades.csv"); T = T[T.acct == acct].copy()
for c in ("nt", "et"):
    T[c] = pd.to_datetime(T[c], utc=True).dt.tz_convert("America/New_York")
t = pd.Timestamp(f"2026-10-14 {hh}", tz="America/New_York")
bars = {}
def px(s):
    if s not in bars:
        b = pd.read_parquet(f"{S}/bars/{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert("America/New_York"); bars[s] = b
    b = bars[s]; return b[b.index < t].close.iloc[-1]
o = T[(T.nt < t) & (T.et > t)].copy()
o["at_peak"] = [r.side * (px(r.symbol) - r.entry) * r.shares for r in o.itertuples()]
o["after"] = o.pnl - o.at_peak
late = T[T.nt >= t]
print(f"{acct}: {len(o)} lots open at {hh}: marked {o.at_peak.sum():.2f}, final {o.pnl.sum():.2f}, give-back {o.after.sum():.2f}; entries after {hh}: {len(late)} ({late.pnl.sum():.2f})")
print(o.groupby(["side", "exit_reason"]).agg(n=("pnl", "size"), at_peak=("at_peak", "sum"), final=("pnl", "sum"), after=("after", "sum")).round(2).to_string())
print(o.groupby("strategy").after.agg(["size", "sum"]).sort_values("sum").round(2).head(8).to_string())
