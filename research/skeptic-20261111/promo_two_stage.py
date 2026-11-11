"""Skeptic: two-stage promotion options at live noise (sd 0.87R, ICC 0.19, 10 trades/session). Stage 1 = FASTDEC flag
(session-clustered P(avg>0) >= 0.90, i.e. z >= 1.28) AND avg R w/o best session > 0, over 20 sessions. Stage 2 = a FRESH
sample after the move, of S2 sessions, with threshold z2 (and w/o best day > 0). Pass rates by true edge mu, and precision
for a 90% null / 10% +0.10R pool. python promo_two_stage.py      Educational only - not financial advice."""
import numpy as np
rng = np.random.default_rng(12)
SD, ICC, M = 0.87, 0.19, 10
def flag(mu, K, S, z0):
    day = rng.normal(0, SD * np.sqrt(ICC), (K, S))
    x = mu + day[..., None] + rng.normal(0, SD * np.sqrt(1 - ICC), (K, S, M))
    sm = x.mean(2); tot = x.sum(2)
    z = sm.mean(1) / (sm.std(1, ddof=1) / np.sqrt(S)); wob = (tot.sum(1) - tot.max(1)) / (M * (S - 1))
    return (z >= z0) & (wob > 0)
K = 20000
opts = [("stage 1 only", None, None), ("+ stage 2: 20 sess, P>=0.90", 20, 1.2816), ("+ stage 2: 20 sess, P>=0.80", 20, 0.8416),
        ("+ stage 2: 20 sess, P>=0.70", 20, 0.5244), ("+ stage 2: 10 sess, P>=0.80", 10, 0.8416)]
print(f"{'option':32s} " + " ".join(f"mu {m:+.2f}" for m in (0, .05, .10, .20)) + "   precision (90% null / 10% +0.10R)")
for name, s2, z2 in opts:
    rates = []
    for mu in (0, .05, .10, .20):
        f1 = flag(mu, K, 20, 1.2816)
        f = f1 if s2 is None else f1 & flag(mu, K, s2, z2)
        rates.append(f.mean())
    prec = 0.1 * rates[2] / (0.1 * rates[2] + 0.9 * rates[0])
    print(f"{name:32s} " + " ".join(f"{r:8.1%}" for r in rates) + f"   {prec:.0%}")
print("Educational only - not financial advice.")
