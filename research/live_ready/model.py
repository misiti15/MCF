# LIVE-READY 2026-11-11: proposed live-like cost model, applied on top of broker paper P/L (research only, not wired in).
import pandas as pd, numpy as np
SEC=20.60/1e6; TAF=0.000195; TAFCAP=9.79; CAT=0.00005
def apply(t):
    t=t.copy()
    px_x=t.exit; q=t.shares
    # exit categories
    stop=t.exit_reason.isin(['stop','scaled+breakeven']); tgt=t.exit_reason.isin(['target','scaled+target']); mkt=t.exit_reason.isin(['flatten','timestop'])
    # 1 stop extra: max($0.02, 4 bps of price)
    stop_x=np.where(stop, np.maximum(0.02, 4e-4*t.exit), 0.0)
    # 2 target: no price improvement beyond the limit (a resting live limit fills at its price)
    imp=np.where(tgt, np.clip(t.side*(t.exit-t.target),0,None), 0.0)
    # 3 market exits (flatten / timestop): max($0.01, 1 bp)
    mkt_x=np.where(mkt, np.maximum(0.01, 1e-4*t.exit), 0.0)
    # 4 entry latency: 1 bp
    ent_x=1e-4*t.entry
    # 5 fees: sells = long exit or short entry
    sell_px=np.where(t.side>0, t.exit, t.entry)
    sec=SEC*sell_px*q
    taf=np.minimum(TAF*q, TAFCAP)
    cat=CAT*2*q
    t['c_stop']=stop_x*q; t['c_tgt']=imp*q; t['c_mkt']=mkt_x*q; t['c_ent']=ent_x*q; t['c_fees']=sec+taf+cat
    t['c_new']=t[['c_stop','c_tgt','c_mkt','c_ent','c_fees']].sum(axis=1)
    risk=t.risk_ps*q
    t['R_new']=np.where(risk>0,(t.pnl-t.c_new)/risk,t.R_cur)
    for c in ['c_stop','c_tgt','c_mkt','c_ent','c_fees']:
        t['R_'+c[2:]]=np.where(risk>0,t[c]/risk,0)
    return t
