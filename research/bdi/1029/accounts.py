"""Compact per-account session review 2026-10-29 (BDI step 0): P/L after costs, trades, win% vs break-even win%,
avg R, best / worst setup. Peak vs close comes from research/bdi/nightly1029/daily_peak.csv (not recomputed).
Usage: python accounts.py <scratch>. Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); D = "2026-10-29"
pk = pd.read_csv("/home/user/MCF/research/bdi/nightly1029/daily_peak.csv").set_index("acct")
for a in ("p", "t1", "t2", "gy", "gen"):
    t = pd.read_sql("select strategy, side, entry, stop, shares, pnl_adj from trades where date=? and run_id=1",
                    sqlite3.connect(S / a / "journal.db"), params=(D,))
    t["R"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares).replace(0, np.nan)
    w, l = t[t.pnl_adj > 0], t[t.pnl_adj <= 0]
    be = l.R.abs().mean() / (w.R.mean() + l.R.abs().mean()) if len(w) and len(l) else np.nan
    g = t.groupby("strategy").agg(n=("R", "size"), R=("R", "sum"), pl=("pnl_adj", "sum")).sort_values("pl")
    sd = t.groupby("side").agg(n=("R", "size"), R=("R", "mean"), pl=("pnl_adj", "sum"))
    print(f"\n## {a}: P/L {t.pnl_adj.sum():+.2f} | trades {len(t)} | win {len(w) / len(t):.0%} vs break-even {be:.0%} | "
          f"avgR {t.R.mean():+.3f} | peak {pk.loc[a, 'peak']:+.0f} ({pk.loc[a, 'peak_t']}) -> close {pk.loc[a, 'close']:+.0f}")
    print("   sides: " + "; ".join(f"{'long' if k == 1 else 'short'} {r.n} {r.R:+.3f}R ${r.pl:+.0f}" for k, r in sd.iterrows()))
    print("   best:  " + "; ".join(f"{k} {r.n} {r.R:+.1f}R ${r.pl:+.0f}" for k, r in g.tail(2)[::-1].iterrows()))
    print("   worst: " + "; ".join(f"{k} {r.n} {r.R:+.1f}R ${r.pl:+.0f}" for k, r in g.head(2).iterrows()))
