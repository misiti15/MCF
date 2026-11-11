# LIVE-READY 2026-11-11: writes research/live_ready/costs.csv from the modeled trades (python build_csv.py <repo>).
import json, pandas as pd, numpy as np, sys
W=sys.argv[1]
t=pd.read_pickle('modeled.pkl'); t=t[t.risk_ps>0].copy()
asg=json.load(open(f'{W}/docs/live/assignments.json'))['setups']
LBL={'primary':'Primary','testing':'On Deck','testing2':'Testing A','gen':'Setup Generator','graveyard':'Graveyard','livelab':'Testing C','explore1':'Testing B'}
# sensitivity: touch-only target misses (11.1% of target exits measured on 4 days with bars; half assumed unfilled live)
tgt=t.exit_reason.isin(['target','scaled+target'])
nt=t[~tgt].groupby('strategy').R_new.mean()
alt=t.strategy.map(nt).fillna(t.R_new[~tgt].mean())
t['R_touch']=np.where(tgt, 0.111*0.5*(t.R_new-alt), 0.0)
t['R_new_touch']=t.R_new-t.R_touch
def agg(g):
    best=g.groupby('date').R_new.sum(); bd=best.idxmax() if len(best) else None
    n=len(g); nb=(g.date==bd).sum()
    return pd.Series(dict(trades=n, sessions=g.date.nunique(),
        avgR_dashboard_raw=g.R_raw.mean(), avgR_current_pnl_adj=g.R_cur.mean(), avgR_proposed=g.R_new.mean(),
        delta_vs_current=g.R_new.mean()-g.R_cur.mean(), delta_vs_dashboard=g.R_new.mean()-g.R_raw.mean(),
        avgR_proposed_wo_best_day=(g.R_new.sum()-best.max())/(n-nb) if n-nb>0 else np.nan,
        avgR_proposed_touch_sens=g.R_new_touch.mean(),
        c_stop_R=g.R_stop.mean(), c_target_noimprove_R=g.R_tgt.mean(), c_mkt_exit_R=g.R_mkt.mean(), c_entry_R=g.R_ent.mean(), c_fees_R=g.R_fees.mean(),
        current_stop_allowance_R=(g.R_raw-g.R_cur).mean(),
        stop_exit_share=(g.exit_reason=='stop').mean(), target_exit_share=g.exit_reason.isin(['target','scaled+target']).mean(),
        median_price=g.entry.median(), median_risk_bps=(g.risk_ps/g.entry*1e4).median()))
rows=[]
for (s,a),g in t.groupby(['strategy','acct']):
    r=agg(g); r['setup']=s; r['account']=LBL[a]; rows.append(r)
for s,g in t.groupby('strategy'):
    if g.acct.nunique()>1:
        r=agg(g); r['setup']=s; r['account']='ALL'; rows.append(r)
d=pd.DataFrame(rows)
d['family']=d.setup.str.split('-').str[0]
d['assigned_now']=d.setup.map(lambda s:'+'.join(LBL.get(x,x) for x in (asg.get(s) or {}).get('accounts') or []) )
cols=['setup','family','account','assigned_now','trades','sessions','avgR_dashboard_raw','avgR_current_pnl_adj','avgR_proposed','delta_vs_current','delta_vs_dashboard',
      'avgR_proposed_wo_best_day','avgR_proposed_touch_sens','current_stop_allowance_R','c_stop_R','c_target_noimprove_R','c_mkt_exit_R','c_entry_R','c_fees_R',
      'stop_exit_share','target_exit_share','median_price','median_risk_bps']
d=d[cols].sort_values(['account','setup'])
for c in cols[6:]:
    d[c]=d[c].astype(float).round(4)
d.to_csv(f'{W}/research/live_ready/costs.csv',index=False)
t.to_pickle('modeled2.pkl')
print(len(d))
