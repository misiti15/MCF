"""SCOUT-1120 ASYM1 descriptive check (configs 1, pre-declared 2026-11-20 ~22:15 ET): prior-day SPY intraday asymmetry
A = ((H-O) - (O-L)) / (H-L); split sessions by A(t-1) < 0 vs >= 0 and compare session-t SPY open->close and the equal-weight
open->close of all lab names with adv20 >= $95M (a long-day proxy). 2-year open history, locked block never read
(lib.daily() excludes it). Not a setup test; it decides whether the gate is worth a trade-list test. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib  # noqa: E402
d = lib.daily(); d["oc"] = (d.close / d.open - 1) * 100
sp = d[d.symbol == "SPY"].sort_values("date").reset_index(drop=True)
sp["A"] = ((sp.high - sp.open) - (sp.open - sp.low)) / (sp.high - sp.low)
sp["A_prev"] = sp.A.shift(1); sp["gapday"] = sp.date.astype(str).shift(1)
# only consecutive open sessions (no jump across the locked block)
sp["ok"] = pd.to_datetime(sp.date).diff().dt.days.le(4)
ew = d[d.adv20 >= 95e6].groupby("date").oc.mean()
sp["ew"] = sp.date.map(ew)
s = sp[sp.ok & sp.A_prev.notna()]
out = []
for k, g in s.groupby(s.A_prev < 0):
    t = lambda x: x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
    out.append(f"A(t-1) {'< 0' if k else '>= 0'}: sessions {len(g)}, SPY o->c {g.oc.mean():+.3f}% (t {t(g.oc):.2f}), "
               f"EW names o->c {g.ew.mean():+.3f}% (t {t(g.ew):.2f}); by year SPY: " +
               ", ".join(f"{y} {v.oc.mean():+.3f} ({len(v)})" for y, v in g.groupby(pd.to_datetime(g.date).dt.year)))
out.append("Educational only - not financial advice.")
print("\n".join(out)); Path(__file__).with_name("asym_check_out.txt").write_text("\n".join(out) + "\n")
