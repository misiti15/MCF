"""Reviewer check (review_regime_filters): day-clustered t of the non-size (neutral) part, same-day neutral, TT-control bias. Usage: run from a dir holding lots.parquet + common.py/q2_budget.py/q2b_on_latch.py: python rv_neutral_check.py <scratch>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import load, dayt
import q2_budget as Q, q2b_on_latch as B
S=sys.argv[1]; t=load(S); t=t[t.L.notna()].reset_index(drop=True)
for pe in ["DISC","HOLD"]:
    x0=t[(t.book=="arena")&(t.period==pe)].reset_index(drop=True); x=x0[~B.latch_mask(x0)].reset_index(drop=True)
    for kind,f,lab in [("BS",.30,"BS30"),("SIDE",.20,"SIDE20")]:
        blk,trig=Q.block_mask(x,kind,f)
        # neutral with full-period acct mean (as track) and with acct-day mean (strict: within-day selection only)
        m_acc=x.groupby("account").r.transform("mean"); m_ad=x.groupby(["account","date"]).r.transform("mean")
        for nm,m in [("acct-mean",m_acc),("acct-day-mean",m_ad)]:
            v=-(x.r-m).where(blk,0); dd=v.groupby(x.date).sum()
            print(pe,lab,nm,f"neutral {dd.sum():+.1f} day t {dayt(dd):.2f} best share {dd.max()/dd.sum() if dd.sum()>0 else np.nan:.2f} days>0 {(dd>0.05).sum()}/{(dd.abs()>0.05).sum()}")
        if pe=="DISC":
            for a,b in [("2026-10-23","2026-11-16"),("2026-11-17","2026-11-27")]:
                s=(x.date>=a)&(x.date<=b); v=-(x.r-m_ad).where(blk&s,0).groupby(x.date).sum(); v=v[(x.groupby('date').date.first()>=a)&(x.groupby('date').date.first()<=b)]
                print("   ",a,b,"acct-day neutral",f"{v.sum():+.1f} t {dayt(v):.2f} saved {-x.r[blk&s].sum():+.1f}")
        # TT bias check: mean R/lot after median trigger time on trigger vs non-trigger days (book-level trig only)
        if kind=="BS":
            td=set(trig); tau=np.median(list(trig.values()))
            late=x[x.emin>tau]; isT=[(a,d) in td for a,d in zip(late.account,late.date)]
            print("   late-lot R/lot trigger days",round(late.r[np.array(isT)].mean(),3),"non-trigger days",round(late.r[~np.array(isT)].mean(),3),"tau",tau)
