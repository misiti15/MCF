"""Power of a paired (shadow-twin) test vs a split-account A/B, on the real live record (10-23..11-27, all accounts,
LR8 R). Example rule (illustration only, NOT a proposal): exit at -0.75R when MAE reaches it (mae_r <= -0.75), else
unchanged (costs of the original lot kept). Paired: both arms on the same trades -> per-day mean difference.
Split: each day's trades randomly halved into two 'accounts', one per arm (200 draws). Reports the day-clustered SE and
the sessions needed for t = 2 at a +0.05R/trade effect. Read-only. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load
t = load(sys.argv[1]); t = t[(t.date >= '2026-10-23') & t.mae_r.notna()].copy()
cost = t.gross - t.r
t['alt'] = np.where(t.mae_r <= -0.75, -0.75 - cost, t.r)
t['d'] = t.alt - t.r
nd = t.date.nunique()
def se_days(x):
    return x.std(ddof=1) / np.sqrt(len(x))
pd_ = t.groupby('date').d.mean()
se_p = se_days(pd_)
rng = np.random.default_rng(3); ses = []
for _ in range(200):
    u = rng.random(len(t)) < 0.5
    a = t[u].groupby('date').alt.mean(); b = t[~u].groupby('date').r.mean()
    ses.append(se_days((a - b).dropna()))
se_s = float(np.median(ses))
print(f'trades {len(t)}, sessions {nd}; example effect {t.d.mean():+.3f} R/trade')
print(f'paired: per-trade SD of difference {t.d.std():.3f}; SE over {nd} sessions {se_p:.4f}; t {pd_.mean()/se_p:+.2f}')
print(f'split A/B: SE over {nd} sessions {se_s:.4f}; t {t.d.mean()/se_s:+.2f}')
for eff in (0.03, 0.05, 0.10):
    np_ = (2 * se_p * np.sqrt(nd) / eff) ** 2; ns = (2 * se_s * np.sqrt(nd) / eff) ** 2
    print(f'  sessions to t=2 for +{eff}R/trade on the whole 10-account flow: paired {np_:.1f}, split {ns:.0f}, ratio {ns/np_:.0f}x')
# single-setup scale: a setup with ~6 trades/session
k = 6
sp = t.d.std() ; ss = t.r.std() * np.sqrt(2)
for eff in (0.05, 0.10):
    print(f'  one setup at {k} trades/session, +{eff}R: paired ~{(2*sp/eff)**2/k:.0f} sessions, split ~{(2*ss/eff)**2/k:.0f} sessions (iid approx)')
