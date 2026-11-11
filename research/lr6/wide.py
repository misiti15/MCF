# LR6 2026-11-11 (research only): split of ruleset (d) "by spread" (train-picked) into its wide- and tight-spread parts on
# valid, and the variant "(d-wide)": wide spreads keep their train pick, tight spreads get the LR6 collar. Run after analyze.py
# with the same environment (imports its state).
import sys; sys.argv = [sys.argv[0], '.']
import numpy as np, pandas as pd
import analyze as A
T, tr, va, Rm, days = A.T, A.tr, A.va, A.Rm, A.days
ch = pd.read_csv('ruleset_choices.csv'); ch = ch[ch.ruleset == '(d) by spread'].set_index('seg').policy
wide = T.spread_b.isin(['10-20', '20+']).values
rows = []
assign_d = A.RS['(d) by spread']
assign_dw = np.where(wide, assign_d, 'P_LR6')
assign_w20 = np.where(wide, 'O20_W300', 'P_LR6')
for nm, a in [('(d) by spread', assign_d), ('(d-wide) wide: train pick, tight: LR6 collar', assign_dw), ('(d-wide20) wide: +20bps/300s, tight: LR6 collar [post-hoc]', assign_w20)]:
    for spl, m in [('train', tr), ('valid', va)]:
        for part, pm in [('all', np.ones(len(T), bool)), ('wide >=10bps', wide), ('tight <10bps', ~wide)]:
            o, fill, R = A.score(a, m & pm, nm); o.update(sample=spl, part=part); rows.append(o)
    fill, R = A.policy_mix(a); price = A.policy_mix.price
    for ac in sorted(T.account.unique()):
        for spl, m0 in [('train', tr), ('valid', va), ('all', np.ones(len(T), bool))]:
            m = m0 & (T.account == ac).values
            if m.sum() < 20: continue
            ns = len(set(days[m]))
            rows.append(dict(ruleset=nm, sample=spl, part='account:' + ac, n=int(m.sum()), fill=fill[m].mean(),
                             reps_lost_per_session=(1 - fill[m]).sum() / ns, trades_per_session_now=m.sum() / ns,
                             R_mkt=Rm[m].mean(), R_sig=R[m].mean(), dR_sig=(R - Rm)[m].mean(),
                             exec_value=(price - (1 - fill) * (Rm - Rm[m].mean()))[m].mean(), d_price=price[m].mean()))
d = pd.DataFrame(rows)
d.round(4).to_csv('ruleset_spread_split.csv', index=False)
pd.set_option('display.width', 250)
print(d[['ruleset', 'sample', 'part', 'n', 'fill', 'reps_lost_per_session', 'dR_sig', 't_day', 'dR_wo_best_day', 'exec_value', 'exec_t_day', 'exec_wo_best_day', 'exec_best_day_share', 'd_price', 'fam_improve', 'fam_worse', 'fam_worst']].round(4).to_string())
