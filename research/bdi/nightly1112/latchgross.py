"""Nightly 2026-11-12: Primary -2R latch on the LIVE basis (cumulative gross r_multiple in exit order <= -2, as the runner
counts it; BDI 1110 latch_count). For each latched setup: lots open at the latch, their final R (costs in) vs their SIP
1-min mark at the latch minute (= loss taken AFTER the latch on already-open lots), SPY move latch -> 15:55, and the
signals the latch blocked. Ties to backlog nightly-1110-latch-closes-open-lots (second data point).
Usage: python latchgross.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
T = pd.read_csv(OUT / "trades.csv"); T["nt"] = pd.to_datetime(T.nt, utc=True).dt.tz_convert(TZ); T["et"] = pd.to_datetime(T.et, utc=True).dt.tz_convert(TZ)
def bars(s):
    b = pd.read_parquet(S / "bars" / f"{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ); return b
def px(s, t):
    b = bars(s); b = b[b.index <= t - pd.Timedelta(minutes=1)]; return float(b.close.iloc[-1])
spy = bars("SPY")
c = sqlite3.connect(S / "p" / "journal.db")
blk = pd.read_sql("select ts, strategy, symbol from signals where day='2026-11-12' and run_id=1 and reason='setup daily loss limit'", c)
P = T[T.acct == "p"]; out = []; rows = []
for s, g in P.groupby("strategy"):
    g = g.sort_values("et"); cum = g.r_multiple.cumsum(); hit = g[cum <= -2]
    if hit.empty: continue
    lt = hit.et.iloc[0]; op = g[(g.nt <= lt) & (g.et > lt)]
    mark = [r.side * (px(r.symbol, lt) - r.entry) / abs(r.entry - r.stop) for _, r in op.iterrows()]
    rows.append(dict(setup=s, latch=lt.strftime("%H:%M"), gross_at_latch=round(cum[cum <= -2].iloc[0], 2), open_lots=len(op),
                     final_R=round(op.radj.sum(), 2), mark_at_latch=round(np.nansum(mark), 2), after_latch=round(op.radj.sum() - np.nansum(mark), 2),
                     realized_before=round(g[g.et <= lt].radj.sum(), 2), day_R=round(g.radj.sum(), 2), blocked=int((blk.strategy == s).sum()),
                     spy_after_pct=round(100 * (spy.close.iloc[-1] / px("SPY", lt) - 1), 2)))
D = pd.DataFrame(rows); out.append(D.to_string())
out.append(f"TOTAL open lots {D.open_lots.sum()}, final {D.final_R.sum():+.2f}R vs marked at latch {D.mark_at_latch.sum():+.2f}R -> after-latch loss on open lots {D.after_latch.sum():+.2f}R; Primary day {P.radj.sum():+.2f}R")
out.append(f"blocked signals {len(blk)}: {blk.groupby('strategy').size().to_dict()}")
txt = "\n".join(out); (OUT / "latchgross_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
