"""shorts_autopsy addendum B: D1 first-lot-per-symbol-per-day across the 6 gap-down short setups pooled (bench10, LIVE-L),
vs random removal of the same count and the constant cut; plus the live analogue (descriptive). Usage: python bench_dedupe.py WORK SCRATCH.
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
W = Path(sys.argv[1]); D = sys.argv[2]
x = pd.read_parquet(W / "bench_feat.parquet"); NS = {"FIT": 170, "CHECK": 276, "T2": 427}; rng = np.random.default_rng(1129)
for per in ("CHECK", "T2", "FIT"):
    y = x[(x.per == per) & (x.fam == "gapdn")].sort_values(["date", "em", "symbol"], kind="mergesort")
    first = ~y.duplicated(["date", "symbol"]); rem = y[~first]; days = NS[per]
    dr = rem.groupby("date").r.sum(); v = np.r_[dr.to_numpy(), np.zeros(days - len(dr))]
    gain = -v.mean(); t = gain / (v.std(ddof=1) / np.sqrt(days)); r = y.r.to_numpy()
    sims = np.array([-r[rng.choice(len(r), size=len(rem), replace=False)].sum() / days for _ in range(1000)])
    const = -(len(rem) / len(y)) * y.r.sum() / days
    ds = y.groupby("date").r.sum(); after = y[first].groupby("date").r.sum().reindex(ds.index, fill_value=0)
    print(f"{per}: lots {len(y)} removed {len(rem)} ({len(rem)/len(y):.1%}); avgR removed {rem.r.mean():+.3f} kept {y[first].r.mean():+.3f}; "
          f"dR/sess {gain:+.3f} (t {t:.2f}); pct vs random {(sims < gain).mean()*100:.1f}; const cut {const:+.3f}; "
          f"worst5 {ds.nsmallest(5).sum():.1f} -> {after.nsmallest(5).sum():.1f}; best-day share {(-dr).max()/max(1e-9,-dr.sum()):.2f}")
# live analogue: per account, gap-down family, first lot per symbol per day vs later lots
t = pd.read_parquet(f"{D}/live_feat.parquet"); t = t[t.fam == "short-gapdn-family"].sort_values(["account", "date", "et"])
t["first"] = ~t.duplicated(["account", "date", "symbol"])
for lab, z in (("all", t), ("ex 11-25", t[t.date != "2026-11-25"])):
    g = z.groupby("first").r.agg(["size", "mean", "sum"]).round(3); print(f"\nlive {lab}:"); print(g.to_string())
