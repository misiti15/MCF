"""OBS-HALTFLIP (Observer 2026-11-12 early): how fragile is Graveyard's per-setup -2R latch (max_setup_daily_loss_r 2.0,
raw realized R, latched on touch)? Live journal only, run 1, 2026-11-04..11-11. Per setup-day: realized-R path ordered by
exit_time (r_multiple). 'Barely latched' = the crossing trade took cum R from > -2 to within [-2.25, -2]; 'barely missed' =
the day's minimum cum R in (-2, -1.75]. Either flips if replay R differs by <= 0.25R. Also: R of closed trades on latched
setup-days and the skips the latch caused. 0 configs. Educational only - not financial advice.
usage: python haltflip.py <journal.db of mcf-data-graveyard>"""
import sqlite3, sys, pandas as pd, numpy as np
c = sqlite3.connect(sys.argv[1])
t = pd.read_sql("select date, strategy, exit_time, r_multiple r from trades where run_id=1 and date between '2026-11-04' and '2026-11-11' "
                "and exit_time is not null", c).sort_values(["date", "strategy", "exit_time"])
sk = pd.read_sql("select day date, strategy, count(*) n from signals where run_id=1 and day between '2026-11-04' and '2026-11-11' "
                 "and reason='setup daily loss limit' group by 1,2", c)
rows = []
for (d, s), g in t.groupby(["date", "strategy"]):
    cum = g.r.cumsum().values; prev = np.r_[0.0, cum[:-1]]
    hit = np.where(cum <= -2.0)[0]
    if len(hit):
        i = hit[0]; rows.append(dict(date=d, strategy=s, latched=True, barely=cum[i] >= -2.25, cross_from=prev[i], cross_to=cum[i],
                                     day_R=cum[-1], n=len(g)))
    else:
        rows.append(dict(date=d, strategy=s, latched=False, barely=cum.min() > -2.0 and cum.min() <= -1.75, cross_from=np.nan,
                         cross_to=cum.min(), day_R=cum[-1], n=len(g)))
x = pd.DataFrame(rows).merge(sk, how="left", on=["date", "strategy"]).fillna({"n_y": 0})
L, N = x[x.latched], x[~x.latched]
print(f"setup-days {len(x)} on {x.date.nunique()} sessions, {x.strategy.nunique()} setups")
print(f"latched {len(L)} ({len(L)/len(x):.0%}); barely latched (crossing landed in [-2.25,-2]) {L.barely.sum()} ({L.barely.mean():.0%} of latched)")
print(f"not latched {len(N)}; barely missed (min cum R in (-2,-1.75]) {N.barely.sum()}")
print(f"flip-able setup-days (<=0.25R from the other outcome): {L.barely.sum()+N.barely.sum()} = {(L.barely.sum()+N.barely.sum())/len(x):.0%} of all")
print(f"latch skips: {int(L.n_y.sum())} signals on latched setup-days ({int(x[x.barely & x.latched].n_y.sum())} on barely-latched ones)")
print(f"crossing trade R: median {(L.cross_to-L.cross_from).median():+.2f}; cum R before it: median {L.cross_from.median():+.2f}")
print("matched-trade R diff replay-live (FWDCAL holdout Graveyard) is +0.010 mean; per-trade |diff| not on mcf-guild.")
# knife edge: crossing value distribution
print("crossing cum R (latched) histogram:", pd.cut(L.cross_to, [-9, -2.5, -2.25, -2.1, -2.05, -2.0001, -2.0]).value_counts().sort_index().to_dict())
print(f"latched with crossing in [-2.10,-2.00]: {((L.cross_to>=-2.10)).sum()} of {len(L)}")
