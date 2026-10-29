"""Out-of-account live check (paper) of the side brake 'after N short stops today, new short lots at half size' (and the
long mirror) on Testing 1, Testing 2, Graveyard and the Setup Generator journals (run 1, every session), after costs.
R = pnl_adj / $ risk. Usage: python other_accts.py <scratch-pr29>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); TZ = "America/New_York"
pd.set_option("display.width", 220)
for a in ("p", "testing", "testing2", "graveyard", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select id,date,symbol,strategy,side,entry_time,exit_time,entry,stop,shares,pnl_adj,exit_reason from trades where run_id=1", c)
    t["nt"] = pd.to_datetime(t.entry_time, utc=True, format="mixed"); t["xt"] = pd.to_datetime(t.exit_time, utc=True, format="mixed")
    t["risk"] = (t.entry - t.stop).abs() * t.shares; t = t[(t.risk > 0) & t.xt.notna()].copy(); t["R"] = t.pnl_adj / t.risk
    t = t.sort_values("nt").reset_index(drop=True)
    # side stops realized before each entry (same day, same side)
    ss = np.zeros(len(t), int)
    for d, g in t.groupby("date"):
        for side in (-1, 1):
            gs = g[g.side == side]; stops = np.sort(gs[gs.exit_reason == "stop"].xt.values)
            ss[gs.index] = np.searchsorted(stops, gs.nt.values, side="right")
    t["side_stops"] = ss
    res = []
    for n in (3, 4):
        for side in (-1,):
            w = np.where((t.side == side) & (t.side_stops >= n), 0.5, 1.0)
            day0 = t.groupby("date").R.sum(); day1 = (t.R * w).groupby(t.date).sum()
            dd = day1 - day0
            res.append(dict(acct=a, rule=f"short stops>={n} half", sessions=t.date.nunique(), trades=len(t), affected=int((w < 1).sum()),
                            affected_avgR=t.R[w < 1].mean(), unaffected_short_avgR=t.R[(w == 1) & (t.side == side)].mean(),
                            totR0=day0.sum(), totR1=day1.sum(), worst0=day0.min(), worst1=day1.min(), red0=int((day0 < 0).sum()), red1=int((day1 < 0).sum()),
                            days_better=int((dd > 1e-9).sum()), days_worse=int((dd < -1e-9).sum()),
                            t_day=dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))) if dd.std() > 0 else np.nan))
    print(pd.DataFrame(res).round(3).to_string(index=False))
