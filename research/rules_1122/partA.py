"""Part A: per-setup daily -2R latch replayed on EVERY setup's whole live record (all accounts, run 1, LR8 cost-R).
Latch = live Primary rule: no new entries by that setup in that account for the rest of the day once its realized
(closed-trade) cost-R <= -2. Open marks are NOT included (no 1-minute bars after 2026-11-04 in this checkout; the live
per-setup latch is realized-only too). In latched account-days (Primary from 10-29, Graveyard, Testing 1/2 10-19..10-22)
the 'no latch' record adds back the journal's what-if rows skipped for 'setup daily loss limit' (E4 what-if, costed with
the setup's median live cost gap + 0.05R haircut, one lot at a time per symbol). Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).parent))
from common import LATCHED, family, ts, whatif_cost_adjust, one_lot_at_a_time, day_wobd

W = Path(sys.argv[1]); OUT = Path(__file__).parent
live = pd.read_parquet(W / "live.parquet")
live = live[~live.dup].copy()
live["et"], live["xt"] = ts(live.entry_time), ts(live.exit_time)
live["src"] = "live"
w = pd.read_parquet(W / "whatif.parquet")
w = w[w.why == "setup daily loss limit"].copy()
w["et"], w["xt"] = ts(w.entry_time), ts(w.exit_time)
w = w[w.et.notna() & w.xt.notna() & w.r_multiple.notna()]
w = one_lot_at_a_time(w)
w["r"] = whatif_cost_adjust(w, live)
w["src"] = "whatif"
cols = ["account", "strategy", "symbol", "side", "date", "et", "xt", "r", "src"]
base = pd.concat([live[cols], w[cols]], ignore_index=True)
base["latched_acct_day"] = [LATCHED.get(a, ("9", "9"))[0] <= d <= LATCHED.get(a, ("9", "9"))[1] for a, d in zip(base.account, base.date)]


def latch(df, lim=-2.0):
    """returns keep mask and per account/setup/day the latch time (NaT if never)."""
    keep = pd.Series(True, index=df.index)
    fires = []
    for k, g in df.groupby(["account", "strategy", "date"], sort=False):
        g = g.sort_values("xt")
        c = g.r.cumsum()
        hit = c[c <= lim + 1e-12]
        if not len(hit):
            continue
        T = g.loc[hit.index[0], "xt"]
        blk = g.index[g.et > T]
        keep[blk] = False
        fires.append(k + (T, len(blk)))
    return keep, pd.DataFrame(fires, columns=["account", "strategy", "date", "t_latch", "blocked"])



def run(base, TAG):
    print("=" * 30, "VERSION", TAG, "=" * 30)
    keep, fires = latch(base)
    base["kept"] = keep
    fires.to_csv(OUT / f"A{TAG}_latch_fires.csv", index=False)
    rows = []
    for s, g in base.groupby("strategy"):
        gl = g[g.kept]
        b = g[~g.kept]
        fam = family(s, int(np.sign(g.side.mean())))
        rows.append(dict(setup=s, family=fam, accounts="/".join(sorted(g.account.unique())),
                         trades_nolatch=len(g), whatif_added=int((g.src == "whatif").sum()), trades_latch=len(gl),
                         days=g.date.nunique(), R_nolatch=g.r.sum(), R_latch=gl.r.sum(), dR=gl.r.sum() - g.r.sum(),
                         wobd_nolatch=day_wobd(g), wobd_latch=day_wobd(gl),
                         fire_days=int(((fires.strategy == s)).sum()),
                         fire_days_with_blocks=int(((fires.strategy == s) & (fires.blocked > 0)).sum()),
                         win_blocked_n=int((b.r > 0).sum()), win_blocked_R=b.r[b.r > 0].sum(),
                         loss_avoided_n=int((b.r <= 0).sum()), loss_avoided_R=b.r[b.r <= 0].sum(),
                         latched_share=float(g.latched_acct_day.mean())))
    A = pd.DataFrame(rows).sort_values("dR")
    A.round(3).to_csv(OUT / f"A{TAG}_per_setup.csv", index=False)
    
    # family table (remedy rule): setups better / worse / unchanged, and by how much
    F = []
    for f, g in A.groupby("family"):
        ch = g[g.dR.abs() > 1e-9]
        F.append(dict(family=f, setups=len(g), touched=len(ch), better=int((ch.dR > 0).sum()), worse=int((ch.dR < 0).sum()),
                      dR_better=ch.dR[ch.dR > 0].sum(), dR_worse=ch.dR[ch.dR < 0].sum(), dR_total=g.dR.sum(),
                      R_nolatch=g.R_nolatch.sum(), R_latch=g.R_latch.sum(), trades=g.trades_nolatch.sum(),
                      blocked=int((g.trades_nolatch - g.trades_latch).sum()),
                      median_dR_touched=ch.dR.median() if len(ch) else 0.0))
    F = pd.DataFrame(F).sort_values("dR_total")
    F.round(2).to_csv(OUT / f"A{TAG}_per_family.csv", index=False)
    
    # alternative latch levels per family (pattern check, not per-setup tuning): -1, -3, -4, none
    L = []
    for lim in (-1.0, -1.5, -2.0, -3.0, -4.0):
        k2, f2 = latch(base, lim)
        x = base.assign(k=k2)
        for f, g in x.assign(fam=x.strategy.map(dict(zip(A.setup, A.family)))).groupby("fam"):
            L.append(dict(family=f, latch=lim, R=g.r[g.k].sum(), dR=g.r[g.k].sum() - g.r.sum(), blocked=int((~g.k).sum())))
        L.append(dict(family="ALL", latch=lim, R=x.r[x.k].sum(), dR=x.r[x.k].sum() - x.r.sum(), blocked=int((~x.k).sum())))
    L = pd.DataFrame(L)
    L.round(2).to_csv(OUT / f"A{TAG}_latch_levels.csv", index=False)
    
    # date concentration: dR by date
    base["k"] = keep
    fam = base.strategy.map(dict(zip(A.setup, A.family)))
    fd = (base.r.where(~base.k, 0.0) * -1).groupby([fam, base.date]).sum()   # dR per family-date (blocked R removed)
    fd = fd[fd.abs() > 1e-9]
    conc = []
    for f, g in fd.groupby(level=0):
        g = g.droplevel(0)
        top = g.abs().idxmax()
        n = len(g)
        t = g.mean() / (g.std(ddof=1) / np.sqrt(n)) if n > 2 and g.std(ddof=1) > 0 else np.nan
        conc.append(dict(family=f, dates=n, dR=g.sum(), top_date=top, top_dR=g[top], dR_wo_top=g.sum() - g[top],
                         dates_better=int((g > 0).sum()), dates_worse=int((g < 0).sum()), t_by_date=t,
                         dR_1112_1120=g[g.index.isin(["2026-11-12", "2026-11-20"])].sum()))
    pd.DataFrame(conc).round(2).to_csv(OUT / f"A{TAG}_family_dates.csv", index=False)
    print(pd.DataFrame(conc).round(1).to_string(index=False))
    dd = base[~base.k].groupby("date").r.agg(["size", "sum"]).rename(columns={"size": "blocked", "sum": "blocked_R"})
    dd.round(2).to_csv(OUT / f"A{TAG}_by_date.csv")
    
    # split by observed (live) vs what-if add-back, and by account latched/not
    print("TOTAL no-latch R %.1f (%d trades, %d what-if adds) | latch R %.1f | dR %+.1f" % (
        base.r.sum(), len(base), int((base.src == "whatif").sum()), base.r[base.k].sum(), base.r[base.k].sum() - base.r.sum()))
    for lab, m in (("unlatched account-days", ~base.latched_acct_day), ("latched account-days", base.latched_acct_day)):
        g = base[m]
        print(f"  {lab}: trades {len(g)}, R nolatch {g.r.sum():.1f}, latch {g.r[g.k].sum():.1f}, dR {g.r[g.k].sum()-g.r.sum():+.1f}, "
              f"blocked {int((~g.k).sum())} (whatif {int(((~g.k)&(g.src=='whatif')).sum())})")
    print("live-only blocked in latched account-days:", int(((~base.k) & base.latched_acct_day & (base.src == 'live')).sum()))
    print(F.round(1).to_string(index=False))
    print(L.pivot(index="family", columns="latch", values="dR").round(1).to_string())
    print(dd.sort_values("blocked_R").round(1).to_string())


# L = live (observed) trades only; W = live + what-if add-back of latch-skipped signals in latched account-days
run(base[base.src == "live"].copy(), "L")
run(base.copy(), "W")
