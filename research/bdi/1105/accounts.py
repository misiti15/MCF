"""BDI 2026-11-05 step 0: per-account session review. P/L: Alpaca $ = account equity change (status.json on the data
branch, last commit before 13:00 UTC vs final), journal pnl_adj $ and R (= pnl_adj / $ risk); trades, win% vs break-even,
avg R, peak vs close (nightly1105/daily_peak.csv, journal $), best / worst setup, skips (signals not submitted), stacks.
Usage: python accounts.py <journals dir with <acct>/journal.db>. Educational only - not financial advice."""
import json, sqlite3, subprocess, sys
from pathlib import Path
import numpy as np, pandas as pd
J = Path(sys.argv[1]); D = "2026-11-05"; HERE = Path(__file__).resolve().parent
BR = {"p": "mcf-data", "t1": "mcf-data-testing", "t2": "mcf-data-testing2", "gy": "mcf-data-graveyard", "gen": "mcf-data-gen",
      "ex1": "mcf-data-explore1", "ll": "mcf-data-livelab"}
NM = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2", "gy": "Graveyard", "gen": "Gen", "ex1": "Explore 1", "ll": "Live Lab"}
def eq(rev):
    r = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"{rev}:status.json"], capture_output=True, text=True)
    return json.loads(r.stdout)["account"]["equity"] if r.returncode == 0 and r.stdout.strip() else None
T = pd.read_csv(HERE.parent / "nightly1105" / "trades.csv"); T = T[T.run_id == 1]
pk = pd.read_csv(HERE.parent / "nightly1105" / "daily_peak.csv").set_index("acct")
rows = []
for a in NM:
    b = "origin/" + BR[a]; c0 = subprocess.run(["git", "-C", "/home/user/MCF", "rev-list", "-1", "--before=2026-11-05 13:00 +0000", b],
                                              capture_output=True, text=True).stdout.strip()
    e1 = eq(b); e0 = eq(c0) if c0 else None; e0 = e0 if e0 is not None else 100000.0
    t = T[T.acct == a]; w, l = t[t.pnl_adj > 0], t[t.pnl_adj <= 0]
    be = l.radj.abs().mean() / (w.radj.mean() + l.radj.abs().mean()) if len(w) and len(l) else np.nan
    g = t.groupby("strategy").agg(n=("radj", "size"), R=("radj", "sum"), pl=("pnl_adj", "sum")).sort_values("R")
    sg = pd.read_sql("select status, reason from signals where day=? and run_id=1", sqlite3.connect(J / a / "journal.db"), params=(D,))
    sk = sg[sg.status != "submitted"]; top_sk = sk.reason.fillna("?").str.split(r"[:(\d]").str[0].str.strip().value_counts().head(3)
    sd = t.groupby("side").agg(n=("radj", "size"), R=("radj", "sum"))
    print(f"\n## {NM[a]}: Alpaca ${e1 - e0:+.2f} | journal pnl_adj ${t.pnl_adj.sum():+.2f} | {t.radj.sum():+.2f}R | trades {len(t)} | "
          f"win {len(w) / max(len(t), 1):.0%} vs break-even {be:.0%} | avg R {t.radj.mean():+.3f} | peak ${pk.loc[a, 'peak']:+.0f} "
          f"({pk.loc[a, 'peak_t']}) -> close ${pk.loc[a, 'close']:+.0f} (journal $)")
    print("   sides: " + "; ".join(f"{'long' if k == 1 else 'short'} {r.n} {r.R:+.1f}R" for k, r in sd.iterrows()))
    print("   best:  " + "; ".join(f"`{k}` {r.n} {r.R:+.1f}R ${r.pl:+.0f}" for k, r in g.tail(2)[::-1].iterrows()))
    print("   worst: " + "; ".join(f"`{k}` {r.n} {r.R:+.1f}R ${r.pl:+.0f}" for k, r in g.head(2).iterrows()))
    print(f"   skips: {len(sk)} of {len(sg)} signals; top reasons " + "; ".join(f"{k} {v}" for k, v in top_sk.items()))
    rows.append(dict(acct=a, alpaca_usd=round(e1 - e0, 2), pnl_adj=round(t.pnl_adj.sum(), 2), R=round(t.radj.sum(), 2), trades=len(t),
                     win=round(len(w) / max(len(t), 1), 3), breakeven=round(be, 3), avgR=round(t.radj.mean(), 3), skips=len(sk)))
pd.DataFrame(rows).to_csv(HERE / "accounts.csv", index=False)
print("\nEducational only - not financial advice.")
