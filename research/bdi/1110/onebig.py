"""One-big-day check (owner 2026-10-25) for the day's best / worst setups, own-account live record (run 1, R = pnl_adj / $ risk).
Usage: python onebig.py <scratch with <acct>/journal.db>. Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1])
L = [("p", "L3-gap-slope-fromopen-FD"), ("p", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"), ("p", "RW3-gapdn-rsi5pop-flowsell-short-FD"),
     ("p", "MF2-open-rsimidhi-flowsell-FD"), ("p", "MF4-h40-open-flowsell-FD"), ("t1", "RW7-gapdn-bounce-early-short-FD"), ("t2", "RW3S-gapdn-flowsell-short-FD"),
     ("gy", "CWT14-failbrk-orl-p05-lowvol-long"), ("gy", "CWT14-failbrk-orl-p05-long"), ("gy", "CWT14-failbrk-orl-p10-lowvol-long"),
     ("gen", "GEN-261027-06-ORBfailUp-BarsSinceLODle5-MID-BRoplt0p35-holdtr-long"), ("gen", "GEN-261028-02-VWAPxDn-NewLOD-AM-QQQgt0p6-t1s1-long"),
     ("gen", "GEN-261020-10-BBpctge0p81-ORBfailDn-AM-BRvwlt0p3-hold-short"), ("ll", "NM-ETF-late-dip-di-long")]
for a, s in L:
    t = pd.read_sql("select date, entry, stop, shares, pnl_adj from trades where run_id=1 and strategy=?", sqlite3.connect(S / a / "journal.db"), params=(s,))
    t["R"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares); d = t.groupby("date").R.sum()
    if not len(d): print(a, s, "no trades"); continue
    b = d.idxmax(); wo = t[t.date != b].R.mean(); sh = d.max() / d.sum() if d.sum() > 0 else float("nan")
    print(f"{a} {s}: {len(t)} trades / {len(d)} sessions ({d.index.min()}..{d.index.max()}), avg {t.R.mean():+.3f}R, w/o best day ({b} {d.max():+.2f}R) {wo:+.3f}R"
          f"{'' if sh != sh else f', best day share {sh:.0%}'}{' `1 day`' if sh == sh and sh >= 0.5 else ''}; today {d.get('2026-11-10', 0):+.2f}R")
print("Educational only - not financial advice.")
