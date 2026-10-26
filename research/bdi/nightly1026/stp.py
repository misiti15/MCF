"""ST-P (backlog st-a-1022-primary-setup-stop), live part: Primary's live paper trades since start, replayed with a
hypothetical per-setup daily stop that LATCHES (rule: once a setup's realized R(j) for the day, summed by exit time,
is <= -X, every later entry of that setup that day is dropped). Primary has no per-setup stop, so nothing was blocked
live and the live trades are the full candidate set; dropping trades frees slots, which this ignores (slot effects are
not modelled). R after costs = pnl_adj / $ risk. Configs: none, latch 1.5 / 2 / 3R (4, counted in the lineage).
Usage: python stp.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
c = sqlite3.connect(S / "p" / "journal.db")
T = pd.read_sql("select date, strategy, entry_time, exit_time, entry, stop, shares, pnl, pnl_adj, r_multiple from trades "
                "where run_id=1 and exit is not null", c)
T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
T["risk"] = (T.entry - T.stop).abs() * T.shares
T["rc"] = np.where(T.risk > 0, T.pnl_adj / T.risk, T.r_multiple)
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed"); T["et"] = pd.to_datetime(T.exit_time, utc=True, format="mixed")
def run(X):
    keep = []
    for (d, s), g in T.groupby(["date", "strategy"]):
        g = g.sort_values("nt"); taken = []
        for r in g.itertuples():
            real = sum(x.r_multiple for x in taken if x.et <= r.nt)
            latched = X is not None and any(sum(y.r_multiple for y in taken if y.et <= x.et) <= -X for x in taken if x.et <= r.nt)
            if latched:
                continue
            taken.append(r)
        keep += [x.Index for x in taken]
    return T.loc[keep]
rows, daily = [], {}
for name, X in (("none", None), ("latch1.5", 1.5), ("latch2", 2.0), ("latch3", 3.0)):
    k = run(X); d = k.groupby("date").agg(R=("rc", "sum"), usd=("pnl_adj", "sum"))
    daily[name] = d.R
    rows.append(dict(rule=name, trades=len(k), net_R=round(k.rc.sum(), 2), usd=round(k.pnl_adj.sum(), 2),
                     today_R=round(d.R.get("2026-10-26", 0), 2), best_day=d.R.idxmax(), best_day_R=round(d.R.max(), 2)))
R = pd.DataFrame(rows)
D = pd.DataFrame(daily).round(2)
for n in ("latch1.5", "latch2", "latch3"):
    diff = D[n] - D["none"]; k = len(diff)
    R.loc[R.rule == n, "vs_none_R"] = round(diff.sum(), 2)
    R.loc[R.rule == n, "days_better/worse"] = f"{(diff > 0.005).sum()}/{(diff < -0.005).sum()}"
    R.loc[R.rule == n, "t_day"] = round(diff.mean() / (diff.std(ddof=1) / k ** .5), 2) if diff.std(ddof=1) > 0 else np.nan
    R.loc[R.rule == n, "best_day_giveup_R"] = round((D[n] - D["none"]).loc[D["none"].idxmax()], 2)
txt = f"Primary sessions {D.index.min()}..{D.index.max()} ({len(D)})\n" + R.to_string(index=False) + "\n\nper day (R after costs)\n" + D.to_string()
open(OUT / "stp_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
