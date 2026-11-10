"""Skeptic check of research/xapbo/pbo.py: PBO when every config shares the same real edge (+0.12 sd/day, 448 days, 8 configs),
correlated or independent, vs correlated noise. 10 draws each, 2,000 CSCV splits. Educational only - not financial advice.
run from research/xapbo:  python ../skeptic-20261109/pbo_check.py"""
import sys, numpy as np
sys.path.insert(0, "."); import pbo as P
rng = np.random.default_rng(7)
def run(make, k=10):
    v = [P.pbo(make(), 16, "sharpe", max_splits=2000, seed=i) for i in range(k)]
    return round(np.mean([x["pbo"] for x in v]), 3), round(np.std([x["pbo"] for x in v]), 3), round(np.mean([x["p_oos_loss"] for x in v]), 3)
cases = {"shared edge, correlated": lambda: rng.normal(0.12, 1, (448, 1)) + rng.normal(0, 0.3, (448, 8)),
         "shared edge, independent": lambda: rng.normal(0.12, 1, (448, 8)),
         "noise, correlated": lambda: rng.normal(0, 1, (448, 1)) + rng.normal(0, 0.3, (448, 8))}
for nm, fn in cases.items(): print(nm, "PBO mean, sd, p_oos_loss:", run(fn))
