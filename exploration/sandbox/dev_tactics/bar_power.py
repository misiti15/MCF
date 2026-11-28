"""Overfitting bar vs power. Null max-|t| over N configs (independent approx), and the chance a REAL edge of size e
passes the lineage bar t >= 4.3 on a 2-year bench, vs a two-stage design (bench screen t >= 2.5, then a pre-registered
paired forward with a one-sided t >= 2). Per-trade SD 0.77R (live median), bench trades per setup given. Educational only."""
import numpy as np
from scipy import stats
for N in (1000, 9363, 32_900_000):
    # two-sided: P(max |t| > x) = 0.5 -> x
    x = stats.norm.isf(0.25 / N * 2 / 2)  # median of max |z| over N independent
    x05 = stats.norm.isf(0.05 / N / 2)
    print(f'N={N:>10,}: median null max|t| {x:.2f}; Bonferroni 5% bar {x05:.2f}')
sd = 0.77
for n_tr in (500, 2000, 5000):
    for e in (0.03, 0.05, 0.10):
        m = e / (sd / np.sqrt(n_tr))
        p43 = stats.norm.sf(4.3 - m); p25 = stats.norm.sf(2.5 - m)
        print(f'bench {n_tr:5d} trades, true edge +{e:.2f}R: mean t {m:4.1f}; P(pass t>=4.3) {p43:5.1%}; P(pass screen t>=2.5) {p25:5.1%}')
print('two-stage false-pass count at N=9,363 nulls: screen t>=2.5 two-sided keeps %.0f; forward one-sided 5%% keeps %.1f'
      % (9363 * 2 * stats.norm.sf(2.5), 9363 * 2 * stats.norm.sf(2.5) * 0.05))
