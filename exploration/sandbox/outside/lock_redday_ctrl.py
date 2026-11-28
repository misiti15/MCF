"""Idea A follow-up (same 3+3 configs, no new configs): does the profit lock cut red days more than a random skip of
the same number of lots (live per account; bench CHECK / T2)? Also Primary detail and per-account effects.
Usage: python lock_redday_ctrl.py <scratch_dir> <cand.parquet>. Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import lock_mask, tstat
from bench_book import load, book_day

SCR, CAND = sys.argv[1], sys.argv[2]
rng = np.random.default_rng(3)
t = pd.read_parquet(f"{SCR}/live_acct.parquet")
t["em"] = t.et.dt.hour * 60 + t.et.dt.minute + t.et.dt.second / 60
t["xm"] = t.xt.dt.hour * 60 + t.xt.dt.minute + t.xt.dt.second / 60
t = t.sort_values(["account", "date", "em"]).reset_index(drop=True)
day = t.groupby(["account", "date"]).r.sum()
sd = {}
for a, s in day.groupby(level=0):
    s = s.droplevel(0); e = s.expanding().std().shift(1); cnt = s.expanding().count().shift(1)
    for d in s.index:
        sd[(a, d)] = e[d] if cnt[d] >= 5 else np.nan
elig = np.array([np.isfinite(sd[(a, d)]) for a, d in zip(t.account, t.date)])
print("LIVE (account-days with known sd only):")
for k in [0.25, 0.5]:
    keep = np.ones(len(t), bool)
    for (a, d), ix in t.groupby(["account", "date"]).indices.items():
        X = k * sd[(a, d)] if np.isfinite(sd[(a, d)]) else np.inf
        g = t.iloc[ix]; keep[ix] = lock_mask(g.em.to_numpy(), g.xm.to_numpy(), g.r.to_numpy(), X)
    ed = pd.Series(elig, index=t.index)
    base = t[elig].groupby(["account", "date"]).r.sum()
    new = t[elig & keep].groupby(["account", "date"]).r.sum().reindex(base.index, fill_value=0.0)
    nrem = (~keep & elig).sum()
    reds = []
    acc_n = t[~keep].groupby("account").size()
    for _ in range(500):
        kk = elig.copy()
        for a, n in acc_n.items():
            ix = np.flatnonzero(elig & (t.account.to_numpy() == a))
            kk[rng.choice(ix, n, replace=False)] = False
        nd = t[kk].groupby(["account", "date"]).r.sum().reindex(base.index, fill_value=0.0)
        reds.append(int((nd <= 0).sum()))
    reds = np.array(reds)
    print(f" k={k}: account-days {len(base)}, lots removed {nrem}, red days base {int((base<=0).sum())} -> lock {int((new<=0).sum())}; "
          f"random skip red days mean {reds.mean():.1f} [p5 {np.percentile(reds,5):.0f}, p95 {np.percentile(reds,95):.0f}]; lock below p5: {int((new<=0).sum()) < np.percentile(reds,5)}")
    pa = (new - base).groupby(level=0).sum()
    print(f"   accounts better {int((pa>0).sum())}, worse {int((pa<0).sum())}; by account: {pa.round(1).to_dict()}")
    pr = t[(t.account == "primary") & ~keep]
    print(f"   Primary: locked days {pr.date.nunique()}, lots removed {len(pr)}, removed avg R {pr.r.mean():+.3f} vs Primary avg {t[t.account=='primary'].r.mean():+.3f}; "
          f"removed R by day: {pr.groupby('date').r.sum().round(1).to_dict()}")

c = load(CAND)
days = c.groupby("date").indices; per = c.groupby("date").per.first()
bk = np.zeros(len(c), bool)
for d, ix in days.items():
    bk[ix], _ = book_day(c.iloc[ix])
bday = c[bk].groupby("date").r.sum().reindex(per.index, fill_value=0.0)
sd_fit = bday[per == "FIT"].std()
print("\nBENCH:")
for k in [0.25, 0.5]:
    keep = np.zeros(len(c), bool)
    for d, ix in days.items():
        keep[ix], _ = book_day(c.iloc[ix], X=k * sd_fit)
    nday = c[keep].groupby("date").r.sum().reindex(per.index, fill_value=0.0)
    for p in ["CHECK", "T2"]:
        m = (per == p).to_numpy(); pd_ = per.index[m]
        cand = np.flatnonzero(bk & (c.per == p).to_numpy())
        nrem = int((bk & ~keep & (c.per == p).to_numpy()).sum())
        reds = []
        for _ in range(500):
            kk = bk.copy(); kk[rng.choice(cand, nrem, replace=False)] = False
            nd = c[kk].groupby("date").r.sum().reindex(pd_, fill_value=0.0)
            reds.append(int((nd <= 0).sum()))
        reds = np.array(reds); rb, rn = int((bday[pd_] <= 0).sum()), int((nday[pd_] <= 0).sum())
        wk_b = bday[pd_].groupby(pd.to_datetime(pd_).to_period("W-FRI")).sum(); wk_n = nday[pd_].groupby(pd.to_datetime(pd_).to_period("W-FRI")).sum()
        print(f" k={k} {p}: days {len(pd_)}, lots removed {nrem}, red days {rb} -> {rn}; random skip mean {reds.mean():.1f} [p5 {np.percentile(reds,5):.0f}]; "
              f"red weeks {int((wk_b<=0).sum())} -> {int((wk_n<=0).sum())} of {len(wk_b)}; per-month red {rb/len(pd_)*21:.1f} -> {rn/len(pd_)*21:.1f}")
