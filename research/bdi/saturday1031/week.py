"""Week scorecard 2026-10-26..10-30 for the 5 intraday accounts (paper, costs in: journal pnl_adj; R = pnl_adj / $ risk),
plus the twin-exposure cap and per-setup 2R loss-limit what-ifs for the week (journal what-if run 2, production cost
model as in nightly1028/caps.py). Peak -> close per day from research/bdi/nightly10xx/daily_peak.csv.
Usage: python week.py <scratch>  (expects <scratch>/<acct>/journal.db). Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
DAYS = ["2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30"]
PREV = ["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"]
AC = {"p": "Primary", "t1": "Testing 1", "t2": "Testing 2", "gy": "Graveyard", "gen": "Gen"}
out = []; P = lambda *x: out.append(" ".join(str(y) for y in x))
def load(a, days):
    c = sqlite3.connect(S / a / "journal.db")
    q = f"select date, symbol, strategy, side, entry, stop, shares, pnl, pnl_adj, exit_reason, entry_time from trades where run_id=1 and date in ({','.join('?'*len(days))})"
    t = pd.read_sql(q, c, params=days)
    t["risk"] = ((t.entry - t.stop).abs() * t.shares).replace(0, np.nan)
    t["R"] = t.pnl_adj / t.risk
    return t
def be(t):
    w, l = t[t.pnl_adj > 0], t[t.pnl_adj <= 0]
    return l.R.abs().mean() / (w.R.mean() + l.R.abs().mean()) if len(w) and len(l) else np.nan
rows = []
P("# Week 2026-10-26..10-30 scorecard (paper, costs in)")
for a, nm in AC.items():
    t = load(a, DAYS); tp = load(a, PREV)
    d = t.groupby("date").agg(n=("R", "size"), R=("R", "sum"), pl=("pnl_adj", "sum"))
    g = t.groupby("strategy").agg(n=("R", "size"), R=("R", "sum"), avgR=("R", "mean"), pl=("pnl_adj", "sum")).sort_values("R")
    rows.append(dict(acct=nm, trades=len(t), sumR=t.R.sum(), avgR=t.R.mean(), win=(t.pnl_adj > 0).mean(), be=be(t),
                     pl=t.pnl_adj.sum(), pl_before=t.pnl.sum(), green=int((d.pl > 0).sum()), days=len(d),
                     prevR=tp.R.sum(), prev_pl=tp.pnl_adj.sum(), prev_n=len(tp),
                     long_R=t[t.side == 1].R.sum(), short_R=t[t.side != 1].R.sum()))
    P(f"\n## {nm}: {t.R.sum():+.1f}R | {len(t)} trades | avg {t.R.mean():+.3f}R | win {(t.pnl_adj>0).mean():.0%} vs BE {be(t):.0%} | "
      f"P/L {t.pnl_adj.sum():+.2f} after costs ({t.pnl.sum():+.2f} before) | green {int((d.pl>0).sum())}/{len(d)} | "
      f"longs {t[t.side==1].R.sum():+.1f}R n{int((t.side==1).sum())} shorts {t[t.side!=1].R.sum():+.1f}R n{int((t.side!=1).sum())}")
    P("   by day:", "; ".join(f"{k[5:]} {r.n} tr {r.R:+.1f}R ${r.pl:+.0f}" for k, r in d.iterrows()))
    P(f"   prev week (10-19..10-23): {len(tp)} tr {tp.R.sum():+.1f}R ${tp.pnl_adj.sum():+.0f}")
    P("   best setups: " + "; ".join(f"{k} {int(r.n)} tr {r.R:+.1f}R ({r.avgR:+.3f}) ${r.pl:+.0f}" for k, r in g.tail(3)[::-1].iterrows()))
    P("   worst setups: " + "; ".join(f"{k} {int(r.n)} tr {r.R:+.1f}R ({r.avgR:+.3f}) ${r.pl:+.0f}" for k, r in g.head(3).iterrows()))
    # one-big-day: week R without best day
    if len(d) > 1:
        P(f"   w/o best day: {d.R.sum() - d.R.max():+.1f}R (best {d.R.idxmax()[5:]} {d.R.max():+.1f}R)")
    g.to_csv(OUT / f"week_by_setup_{a}.csv")
pd.DataFrame(rows).round(4).to_csv(OUT / "week_scorecard.csv", index=False)
P("\n" + pd.DataFrame(rows).round(3).to_string(index=False))
# caps what-ifs
P("\n# Twin-exposure cap and per-setup 2R loss limit, what-if of blocked signals (net of production costs)")
for a, nm in AC.items():
    c = sqlite3.connect(S / a / "journal.db")
    w = pd.read_sql(f"select date, strategy, entry, stop, exit, exit_reason, r_multiple, meta from trades where run_id=2 and date in ({','.join('?'*5)})", c, params=DAYS)
    w["why"] = w.meta.fillna("").str.extract(r"why=(.*)$")[0]
    R = (w.entry - w.stop).abs()
    cps = (0.01 + w.entry * 1e-4) + np.where(w.exit_reason == "target", 0.0, 0.01 + w.exit * 1e-4) + np.where(w.exit_reason == "stop", 0.02, 0.0)
    w["net"] = w.r_multiple - np.where(R > 0, cps / R, 0.0)
    for rsn in ("twin held", "setup daily loss limit"):
        x = w[w.why == rsn]
        if len(x):
            byd = x.groupby("date").net.sum()
            P(f"  {nm:9s} {rsn:23s}: n {len(x):4d} net {x.net.sum():+7.1f}R avg {x.net.mean():+.3f} | by day " +
              " ".join(f"{k[5:]} {v:+.1f}" for k, v in byd.items()) + f" | worst setups {x.groupby('strategy').net.sum().sort_values().head(2).round(1).to_dict()}")
        else:
            P(f"  {nm:9s} {rsn:23s}: none blocked")
# peak -> close
P("\n# Marked intraday peak -> close ($, costs in; nightly daily_peak.csv)")
for D in DAYS:
    k = pd.read_csv(f"/home/user/MCF/research/bdi/nightly{D[5:7]}{D[8:]}/daily_peak.csv").set_index("acct")
    P(f"  {D[5:]}: " + " | ".join(f"{AC[a]} {k.loc[a,'peak']:+.0f} ({k.loc[a,'peak_t']}) -> {k.loc[a,'close']:+.0f}" for a in AC))
open(OUT / "week_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n")
print("\n".join(out))
