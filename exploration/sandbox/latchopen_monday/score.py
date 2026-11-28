"""Score LATCH-OPEN (closed + open R latch) vs closed-only latch, with an exposure-matched random control.
Input: a lot table with columns key (period / roster), lo (bool), date, lid, setup, r, taken.
Control (per draw): start from the closed-only book's taken lots; on each day remove as many lots as LATCH-OPEN removed that
day (net), chosen at random among that day's taken lots (ctrl-day) or among the same setup's taken lots that day (ctrl-setup), or the same total at random over the whole window (ctrl-any = plain size cut).
Static removal (freed slots not re-filled). 400 draws, seed 1127. LATCH-OPEN's percentile = share of draws it beats
(higher is better: more R saved, fewer bad days). Usage: python score.py LOTS.parquet OUT.txt
Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
T = pd.read_parquet(sys.argv[1]); OUT = open(sys.argv[2], "w")
ND = 400; rng = np.random.default_rng(1127)


def p(*a):
    print(*a); print(*a, file=OUT)


def stats(d):
    d = np.asarray(d, float); n = len(d); b = d.argmax()
    return dict(R_day=d.mean(), red=int((d < 0).sum()), le20=int((d <= -20).sum()), le10=int((d <= -10).sum()),
                worst5=np.sort(d)[:5].sum(), wo_best=np.delete(d, b).mean(), best_share=(d[b] / d.sum() if d.sum() > 0 else np.nan),
                worst=d.min(), n=n)


p("Educational only - not financial advice.")
for key, g in T.groupby("key", sort=False):
    days = sorted(g.date.unique())
    base = g[~g.lo]; lo = g[g.lo]
    bd = base[base.taken].groupby("date").r.sum().reindex(days, fill_value=0.0)
    ld = lo[lo.taken].groupby("date").r.sum().reindex(days, fill_value=0.0)
    sb, sl = stats(bd), stats(ld)
    nb = base.taken.sum(); nl = lo.taken.sum()
    p(f"\n== {key}: sessions {len(days)}, lots closed-only {nb}, LATCH-OPEN {nl} ({100 * (1 - nl / nb):.1f}% fewer)")
    for nm, s in (("closed-only", sb), ("LATCH-OPEN", sl)):
        p(f"  {nm:12s} R/day {s['R_day']:+6.2f}  red {s['red']:3d}/{s['n']}  <=-20R {s['le20']:3d}  <=-10R {s['le10']:3d}  "
          f"worst-5 {s['worst5']:+7.1f}  worst {s['worst']:+6.1f}  R/day w/o best day {s['wo_best']:+6.2f}")
    sav = ld - bd
    p(f"  saving R/day {sav.mean():+.3f} (day t {sav.mean() / (sav.std(ddof=1) / np.sqrt(len(sav))):+.2f}); best saving day "
      f"{sav.idxmax()} {sav.max():+.1f} = {100 * sav.max() / sav.sum() if sav.sum() > 0 else float('nan'):.0f}% of total; "
      f"saving w/o best day {(sav.sum() - sav.max()) / (len(sav) - 1):+.3f}/day")
    # exposure-matched controls (ctrl-day is the pre-stated one; ctrl-setup and ctrl-any are sensitivities)
    bt = base[base.taken]
    kd = (bt.groupby("date").size().reindex(days, fill_value=0) - lo[lo.taken].groupby("date").size().reindex(days, fill_value=0)).clip(lower=0)
    ks = (bt.groupby(["date", "setup"]).size() - lo[lo.taken].groupby(["date", "setup"]).size().reindex(bt.groupby(["date", "setup"]).size().index, fill_value=0)).clip(lower=0)
    grp_d = {d: x.r.to_numpy() for d, x in bt.groupby("date")}
    grp_s = {k: x.r.to_numpy() for k, x in bt.groupby(["date", "setup"])}
    allr = bt.r.to_numpy(); alld = bt.date.to_numpy(); K = int(kd.sum())
    for cname in ("ctrl-day", "ctrl-setup", "ctrl-any"):
        res = []
        for _ in range(ND):
            cut = pd.Series(0.0, index=days)
            if cname == "ctrl-day":
                for d, k in kd.items():
                    if k > 0:
                        cut[d] = grp_d[d][rng.choice(len(grp_d[d]), int(k), replace=False)].sum()
            elif cname == "ctrl-any":
                ix = rng.choice(len(allr), K, replace=False)
                cut = cut.add(pd.Series(allr[ix]).groupby(alld[ix]).sum(), fill_value=0.0)
            else:
                for (d, s), k in ks.items():
                    if k > 0:
                        cut[d] += grp_s[(d, s)][rng.choice(len(grp_s[(d, s)]), int(k), replace=False)].sum()
            res.append(stats(bd - cut))
        R = pd.DataFrame(res)
        pr = lambda c, v, hi=True: 100 * ((R[c] < v).mean() + 0.5 * (R[c] == v).mean()) if hi else 100 * ((R[c] > v).mean() + 0.5 * (R[c] == v).mean())
        p(f"  {cname} ({ND} draws, same lots removed per {dict(zip(('ctrl-day', 'ctrl-setup', 'ctrl-any'), ('day', 'day x setup', 'whole window (plain size cut)')))[cname]}): "
          f"R/day median {R.R_day.median():+.2f} [5-95% {R.R_day.quantile(.05):+.2f}..{R.R_day.quantile(.95):+.2f}] -> LO pct {pr('R_day', sl['R_day']):.0f}; "
          f"<=-20R median {R.le20.median():.0f} -> pct {pr('le20', sl['le20'], False):.0f}; "
          f"<=-10R median {R.le10.median():.0f} -> pct {pr('le10', sl['le10'], False):.0f}; "
          f"worst-5 median {R.worst5.median():+.1f} -> pct {pr('worst5', sl['worst5']):.0f}; "
          f"red median {R.red.median():.0f} -> pct {pr('red', sl['red'], False):.0f}")
p("\nEducational only - not financial advice.")
OUT.close()
