"""Idea A on live journals: daily profit lock per account (k * expanding sd of prior account days).
Plus the descriptive morning-vs-afternoon check. Usage: python lock_live.py <scratch_dir>
Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import tstat, lock_mask, summarize

SCR = sys.argv[1]
t = pd.read_parquet(f"{SCR}/live_acct.parquet")
t["em"] = t.et.dt.hour * 60 + t.et.dt.minute + t.et.dt.second / 60
t["xm"] = t.xt.dt.hour * 60 + t.xt.dt.minute + t.xt.dt.second / 60
t = t.sort_values(["account", "date", "em"]).reset_index(drop=True)
day = t.groupby(["account", "date"]).r.sum()

# expanding sd of prior days per account
sd = {}
for a, s in day.groupby(level=0):
    s = s.droplevel(0)
    e = s.expanding().std().shift(1)
    cnt = s.expanding().count().shift(1)
    for d in s.index:
        sd[(a, d)] = e[d] if cnt[d] >= 5 else np.nan

# descriptive: morning closed R (closed by 12:00) vs R of lots entered after 12:00
rows = []
for (a, d), g in t.groupby(["account", "date"]):
    am = g.loc[g.xm <= 720, "r"].sum(); pm = g.loc[g.em >= 720, "r"]
    if len(pm):
        rows.append((a, d, am, pm.sum(), pm.mean(), len(pm)))
dd = pd.DataFrame(rows, columns=["acct", "date", "am", "pm", "pm_avg", "pm_n"])
print("Descriptive: morning closed R vs afternoon-entered lots (account-days with PM lots):", len(dd))
print(f"  Spearman(am, pm_avg) = {dd[['am','pm_avg']].corr('spearman').iloc[0,1]:+.3f}")
for lab, m in [("AM green", dd.am > 0), ("AM red", dd.am <= 0)]:
    w = dd[m]
    print(f"  {lab}: account-days {len(w)}, PM lots {w.pm_n.sum()}, PM R/lot {w.pm.sum()/w.pm_n.sum():+.3f}, PM R total {w.pm.sum():+.1f}")
print("  per account Spearman:", dd.groupby("acct").apply(lambda w: round(w[['am','pm_avg']].corr('spearman').iloc[0,1], 2)).to_dict())

rng = np.random.default_rng(7)
out = []
for k in [0.25, 0.5, 1.0]:
    keep = np.ones(len(t), bool)
    for (a, d), idx in t.groupby(["account", "date"]).indices.items():
        X = k * sd[(a, d)] if np.isfinite(sd[(a, d)]) else np.inf
        g = t.iloc[idx]
        keep[idx] = lock_mask(g.em.to_numpy(), g.xm.to_numpy(), g.r.to_numpy(), X)
    t["keep"] = keep
    rem = t[~keep]
    new = t[keep].groupby(["account", "date"]).r.sum().reindex(day.index, fill_value=0.0)
    s = summarize(day, new)
    by_date = (new - day).groupby(level=1).sum()
    # control (i): same count removed at random over all of the account's lots (eligible days only = sd known)
    # control (ii): same count removed at random within the same account-day
    nrem = rem.groupby(["account", "date"]).size()
    elig = t[[np.isfinite(sd[(a, d)]) for a, d in zip(t.account, t.date)]]
    ra, rb = [], []
    acc_n = nrem.groupby(level=0).sum()
    groups = elig.groupby("account").indices
    dgroups = t.groupby(["account", "date"]).indices
    for _ in range(1000):
        tot = 0.0
        for a, n in acc_n.items():
            ix = rng.choice(groups[a], size=n, replace=False); tot -= t.r.to_numpy()[elig.index[ix]].sum() if False else elig.r.to_numpy()[ix].sum()
        ra.append(tot)
        tot2 = 0.0
        for (a, d), n in nrem.items():
            ix = rng.choice(dgroups[(a, d)], size=n, replace=False); tot2 -= t.r.to_numpy()[ix].sum()
        rb.append(tot2)
    dR = new.sum() - day.sum()
    p1 = (np.array(ra) < dR).mean() * 100; p2 = (np.array(rb) < dR).mean() * 100
    prim = summarize(day.loc["primary"], new.loc["primary"])
    out.append(dict(k=k, lots_removed=len(rem), share=len(rem) / len(t), locked_days=int(nrem.size), dR_total=dR,
                    removed_avgR=rem.r.mean(), all_avgR=t.r.mean(), t_dateclust=tstat(by_date),
                    red_base=s["red_base"], red_new=s["red_new"], w5_base=s["w5_base"], w5_new=s["w5_new"],
                    dR_wo_best=s["dR_wo_best"], best_share=s["best_share"], pct_vs_random=p1, pct_vs_sameday=p2,
                    prim_dR=prim["new_R"] - prim["base_R"], prim_red=f'{prim["red_base"]}->{prim["red_new"]}',
                    prim_locked=int(nrem.get("primary", pd.Series(dtype=int)).size)))
    print(f"\nk={k}: per account dR:", (new - day).groupby(level=0).sum().round(1).to_dict())
res = pd.DataFrame(out)
pd.set_option("display.width", 250)
print("\nLIVE profit lock (all 10 accounts, account-days as units):")
print(res.round(3).T.to_string())
