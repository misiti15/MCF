# LR6 2026-11-11 (research only): the recommended wide-spread leg (spread >= 10 bps: limit at signal +/-10 bps, cancel 300 s)
# by market condition / ticker / style, train and valid separately (descriptive; no further selection).
import sys; sys.argv = [sys.argv[0], '.']
import numpy as np, pandas as pd
import analyze as A
T = A.T; wide = T.spread_b.isin(['10-20', '20+']).values
rows = []
for dim in ['spy_cond', 'compass_b', 'vol_regime', 'tod', 'style', 'side_s', 'price_b', 'adv_q', 'asset', 'spread_b', 'mom_b']:
    for k in sorted(set(map(str, T[dim].tolist()))):
        for spl, sm in [('train', A.tr), ('valid', A.va)]:
            m = wide & (T[dim].astype(str) == k).values & sm
            if m.sum() < 40: continue
            o = A.summary('O10_W300', m, A.days)
            rows.append(dict(dim=dim, seg=k, sample=spl, n=o['n'], fill=o['fill'], dR_sig=o['dR_sig'], exec_value=o['exec_value'],
                             exec_t_day=o['exec_t_day'], R_mkt_missed=o['R_mkt_of_missed'], R_mkt_filled=o['R_mkt_of_filled']))
d = pd.DataFrame(rows); d.round(4).to_csv('wide_leg_robustness.csv', index=False)
p = d.pivot_table(index=['dim', 'seg'], columns='sample', values=['n', 'fill', 'exec_value', 'dR_sig'])
pd.set_option('display.width', 250); print(p.round(3).to_string())
