"""Skeptic: how many setups look promotable by luck as more setups get live reps? Live noise from FASTDEC/obs-verdicts:
per-trade sd 0.87R, same-day ICC 0.19, ~10 trades per setup-session. Each setup: 20 sessions. 'Promote-ready' = FASTDEC
review flag P(avg R > 0) >= 0.90 (session-clustered z >= 1.28) AND avg R w/o best session > 0. True edge mu per setup.
python promo_luck.py      Educational only - not financial advice."""
import numpy as np
rng = np.random.default_rng(11)
SD, ICC, M, S = 0.87, 0.19, 10, 20
def sim(mu, K, reps=400):
    hits = []
    for _ in range(reps):
        day = rng.normal(0, SD * np.sqrt(ICC), (K, S))                       # setup-day shock
        x = mu + day[..., None] + rng.normal(0, SD * np.sqrt(1 - ICC), (K, S, M))
        sm = x.mean(2); tot = x.sum(2)
        z = sm.mean(1) / (sm.std(1, ddof=1) / np.sqrt(S))
        wob = (tot.sum(1) - tot.max(1)) / (M * (S - 1))
        hits.append(((z >= 1.28) & (wob > 0)).sum())
    return np.mean(hits)
for K in (10, 50, 100, 200):
    f = sim(0.0, K); t = sim(0.10, K)
    print(f"K {K:3d} setups x 20 sessions: zero-edge flagged {f:5.1f} ({f / K:.0%}); if all had +0.10R edge flagged {t:5.1f} ({t / K:.0%})")
print("Educational only - not financial advice.")
