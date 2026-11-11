"""Latch-counting check 2026-11-10 (Team reconciliation flag: RW3 / RW5 entries taken after the setups 'appeared past -2R').
The live per-setup latch (mcf/execution/risk.py latch_setup_losses, runner.reconcile) adds each reconciled trade's journal
`r_multiple` (gross fill R, before the journal cost adjustment) in exit order and latches at <= -2. This script compares, per
setup-day: (a) latch time on gross r_multiple, (b) on after-cost R (pnl_adj / $ risk), (c) entries between (b) and (a), (d)
entries within 90 s after (a) (one-poll lag), (e) RW3 / RW5 realized vs mark-to-market R at the flagged times, and checks
partial-fill duplicates (same broker order id). Usage: python latch_count.py <scratch with <acct>/journal.db and bars/>
Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); TZ = "America/New_York"
def load(a, since):
    t = pd.read_sql(f"select * from trades where date>='{since}' and run_id=1", sqlite3.connect(S / a / "journal.db"))
    for c in ("exit_time", "entry_time"): t[c] = pd.to_datetime(t[c], utc=True, format="mixed").dt.tz_convert(TZ)
    t["risk"] = (t.entry - t.stop).abs() * t.shares; t["radj"] = t.pnl_adj / t.risk; return t
for a, since in (("p", "2026-10-29"), ("gy", "2026-10-22")):
    t = load(a, since); A = []; L = []
    print(f"== {a}: {t.date.nunique()} sessions since {since}, {len(t)} trades, duplicate broker order ids {int(t.broker_order_id.duplicated().sum())}")
    for (d, k), g in t.groupby(["date", "strategy"]):
        g = g.sort_values("exit_time"); cr = g.r_multiple.cumsum(); ca = g.radj.cumsum()
        lt = g.exit_time[cr <= -2].min(); la = g.exit_time[ca <= -2].min()
        if pd.notna(la):
            end = lt if pd.notna(lt) else g.entry_time.max() + pd.Timedelta("1s")
            x = g[(g.entry_time > la) & (g.entry_time <= end)]
            if len(x): A.append((d, k, len(x), x.radj.sum(), "gross later" if pd.notna(lt) else "gross never"))
        if pd.notna(lt):
            y = g[(g.entry_time > lt) & (g.entry_time <= lt + pd.Timedelta(seconds=90))]
            if len(y): L.append((d, k, len(y), y.radj.sum()))
    print(f"   entries after the after-cost R crossed -2 but before the gross latch: {sum(x[2] for x in A)}, {sum(x[3] for x in A):+.2f}R")
    for x in A: print(f"      {x[0]} {x[1]} {x[2]} {x[3]:+.2f}R ({x[4]})")
    print(f"   entries <= 90 s after the gross latch (poll lag): {sum(x[2] for x in L)}, {sum(x[3] for x in L):+.2f}R")
    for x in L: print(f"      {x[0]} {x[1]} {x[2]} {x[3]:+.2f}R")
t = load("p", "2026-11-10"); t = t[t.date == "2026-11-10"]
for s in ("RW3-", "RW5-"):
    g = t[t.strategy.str.startswith(s)]
    for hh in ("11:30", "11:50", "11:55", "12:15", "12:35"):
        T = pd.Timestamp(f"2026-11-10 {hh}", tz=TZ); real = g[g.exit_time <= T].radj.sum(); op = g[(g.entry_time <= T) & (g.exit_time > T)]; m = 0.0
        for _, r in op.iterrows():
            b = pd.read_parquet(S / "bars" / f"{r.symbol}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
            b = b[b.index <= T - pd.Timedelta(minutes=1)]; m += r.side * (b.close.iloc[-1] - r.entry) / abs(r.entry - r.stop)
        print(f"P {s[:-1]} {hh}: realized {real:+.2f}R, open {len(op)} lots marked {m:+.2f}R, total {real + m:+.2f}R")
print("Educational only - not financial advice.")
