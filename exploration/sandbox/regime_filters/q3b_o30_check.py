"""Q3b (post-hoc look at the strongest Q3 book-level cell, 2 looks): R/lot of lots entered from 10:00 by side and SPY
open->10:00 bucket; per book, per half, ex-11-25, HOLD, and per-day spread. Usage: python q3b_o30_check.py <scratch>.
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import load, dayt
S = sys.argv[1]; t = load(S); D = pd.read_csv(f"{S}/spyday.csv", index_col=0)
t = t.join(D[["o30"]], on="date"); t = t[t.emin >= 600].copy()
t["o30b"] = np.where(t.o30 < -0.2, "dn", np.where(t.o30 > 0.2, "up", "flat"))
t["half"] = np.where(t.period == "HOLD", "HOLD", np.where(t.date < "2026-11-10", "H1", "H2"))
for bk in ["primary", "arena"]:
    x = t[t.book == bk]
    print(f"\n=== {bk}: R/lot (lots, days) for entries from 10:00 ===")
    print(x.groupby(["half", "sidel", "o30b"]).agg(n=("r", "size"), avg=("r", "mean"), days=("date", "nunique")).round(3).unstack("o30b").to_string())
    y = x[(x.period == "DISC") & (x.date != "2026-11-25")]
    print("  DISC ex-11-25:", y.groupby(["sidel", "o30b"]).r.mean().round(3).to_dict())
    # day-level: per side, daily R/lot; t of (flat days) vs (moving days)
    for s in ["long", "short"]:
        dd = x[(x.sidel == s) & (x.period == "DISC")].groupby(["date", "o30b"]).r.mean().reset_index()
        f = dd[dd.o30b == "flat"].r; m = dd[dd.o30b != "flat"].r
        se = np.sqrt(f.var() / len(f) + m.var() / len(m))
        print(f"  {s}: day-avg R/lot flat-open {f.mean():+.3f} ({len(f)} d) vs moving-open {m.mean():+.3f} ({len(m)} d), welch t {(f.mean()-m.mean())/se:+.2f}")
# day list
x = t[(t.book == "arena") & (t.period == "DISC")]
print("\narena DISC per day (from 10:00): o30, long R/lot, short R/lot")
print(x.groupby(["date"]).apply(lambda g: pd.Series({"o30": g.o30.iloc[0], "L": g.r[g.sidel == "long"].mean(), "S": g.r[g.sidel == "short"].mean(), "nS": (g.sidel == "short").sum()})).round(2).to_string())
