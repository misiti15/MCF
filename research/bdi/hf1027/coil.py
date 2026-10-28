"""hf1027 task 3: where Coil Under the High (4 bars) CWT12-coil-k4-long's live loss comes from (Testing 2, 349 paper
trades, 12 sessions 2026-10-12..10-27). Costs in: rc = journal pnl_adj / $ risk; 'model' = replay.py's backtest cost
model on the same trade. Usage: python coil.py <scratch> -> coil_out.txt   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
T = pd.read_parquet(S / "all_trades.parquet"); X = pd.read_parquet(S / "replay.parquet")
c = T[(T.strategy == "CWT12-coil-k4-long") & (T.date >= "2026-10-09")].copy()
c = c.merge(X[["id", "acct", "live", "live_gross", "t050", "t075", "t100", "mfe_full", "cost_frac"]], on=["id", "acct"], how="left")
c["poll"] = c.nt.dt.floor("5min"); c["burst"] = c.groupby(["date", "poll"]).id.transform("size")
c["day_rank"] = c.groupby("date").nt.rank(method="first")
L = []; P = L.append
n = len(c); aw = c.rc[c.rc > 0].mean(); al = -c.rc[c.rc <= 0].mean()
P(f"CWT12-coil-k4-long live: n {n}, sessions {c.date.nunique()}, win {c.win.mean():.3f}, avg R after costs {c.rc.mean():+.3f} "
  f"(sum {c.rc.sum():+.1f}R), avg win {aw:+.3f} / avg loss {-al:+.3f} -> break-even win {al/(aw+al):.3f}")
P(f"target actually set: median {c.tgt_r.median():.3f}R of the fill-to-stop risk (design 0.5R from the signal price; the fill is "
  f"{c.slip_bps.median():.1f} bps above the signal price at the median, which shrinks the target and widens the risk)")
P("\n1. Cost drag (R per trade):")
P(f"   journal: entry slip vs signal {c.slip_r.mean():+.3f}R + stop-exit extra {c.stopx_r.mean():+.3f}R = {c.cost_r.mean():+.3f}R; "
  f"before those {c.gross_r.mean():+.3f}R")
P(f"   backtest cost model on the same trades: {(c.live_gross - c.live).mean():+.3f}R per trade (gross {c.live_gross.mean():+.3f} -> net {c.live.mean():+.3f}); "
  f"entry-side cost alone = {c.cost_frac.mean():.3f}R (median {c.cost_frac.median():.3f})")
P(f"   at a 0.5R target, a winner keeps {aw:.3f}R; costs of ~{c.cost_r.mean() + 0.0:.2f}-{(c.live_gross - c.live).mean():.2f}R per trade are "
  f"{100*c.cost_r.mean()/aw:.0f}-{100*(c.live_gross - c.live).mean()/aw:.0f}% of an average win")
P("\n2. By session (R after costs):")
d = c.groupby("date").agg(n=("rc", "size"), win=("win", "mean"), R=("rc", "sum"), avgR=("rc", "mean")).round(3); P(d.to_string())
w2 = d.R.nsmallest(2)
P(f"   two worst sessions {list(w2.index)} = {w2.sum():+.1f}R on {d.n[w2.index].sum()} trades; the other {len(d)-2} sessions "
  f"{d.R.sum()-w2.sum():+.1f}R on {d.n.sum()-d.n[w2.index].sum()} trades ({(d.R.sum()-w2.sum())/(d.n.sum()-d.n[w2.index].sum()):+.3f}R/trade). "
  f"Best day {d.R.idxmax()} {d.R.max():+.1f}R; without it {(c.rc.sum()-d.R.max())/(n-d.n[d.R.idxmax()]):+.3f}R/trade")
P("\n3. Target what-if (replay on SIP 1-min bars from the live fill and live stop, model costs, scale-out ignored):")
for k in ("live", "t050", "t075", "t100"):
    g = c[k]; dd = c.groupby("date")[k].sum()
    P(f"   {k}: {g.mean():+.3f}R, win {(g>0).mean():.3f}, sum {g.sum():+.1f}R, without 10-16 & 10-26 {c[~c.date.isin(w2.index)][k].mean():+.3f}R")
P(f"   trades whose price reached +1R before the stop (or by 15:55): {(c.mfe_full>=1).mean():.3f}; +0.75R: {(c.mfe_full>=0.75).mean():.3f}; "
  f"losers that never reached +0.2R: {((c.rc<=0)&(c.mfe_full<0.2)).sum()} of {(c.rc<=0).sum()}")
P("\n4. Repeat entries: every coil-k4 trade is the first coil-k4 trade in its symbol that day "
  f"(max seq {c.seq.max()}, max concurrent lots {c.lot_no.max()}). The 29/session count is breadth (many symbols), not re-entry.")
P("   By entry order within the session (1 = the day's first coil trade):")
c["rk"] = pd.cut(c.day_rank, [0, 10, 20, 40, 999], labels=["1-10", "11-20", "21-40", "41+"])
P(c.groupby("rk", observed=True).agg(n=("rc", "size"), win=("win", "mean"), avgR=("rc", "mean"), sessions=("date", "nunique")).round(3).to_string())
P("   By burst size (coil-k4 entries in the same 5-minute poll):")
c["bb"] = pd.cut(c.burst, [0, 1, 4, 9, 999], labels=["1", "2-4", "5-9", "10+"])
P(c.groupby("bb", observed=True).agg(n=("rc", "size"), win=("win", "mean"), avgR=("rc", "mean"), sessions=("date", "nunique")).round(3).to_string())
P("\n5. Time window (entry time):")
c["tw"] = pd.cut(c.hhmm, [0, 1014, 1044, 1114, 2400], labels=["09:50-10:14", "10:15-10:44", "10:45-11:14", "11:15-11:30"])
P(c.groupby("tw", observed=True).agg(n=("rc", "size"), win=("win", "mean"), avgR=("rc", "mean"), sessions=("date", "nunique")).round(3).to_string())
P("\n6. Tight stops: entry-side cost (1c + 1 bp) as a share of R, and stop width in bps:")
c["cf"] = pd.cut(c.cost_frac, [0, 0.03, 0.05, 0.08, 0.12, 9])
P(c.groupby("cf", observed=True).agg(n=("rc", "size"), win=("win", "mean"), avgR=("rc", "mean"), model=("live", "mean"),
    stop_bps=("stop_bps", "median"), price=("entry", "median")).round(3).to_string())
for th in (0.05, 0.08, 0.10):
    k = c.cost_frac <= th
    P(f"   keep cost/R <= {th:.2f}: n {k.sum()} avg {c.rc[k].mean():+.3f}R (dropped {(~k).sum()} at {c.rc[~k].mean():+.3f}R)")
txt = "\n".join(L) + "\n\nEducational only - not financial advice.\n"
open(HERE / "coil_out.txt", "w").write(txt); print(txt)
