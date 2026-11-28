"""Near-duplicate setups on the live record (10-23..11-27): pairs whose trades hit the same symbol/date/side
(Jaccard of (symbol,date,side) sets) and whose daily R correlate. Read-only. Educational only - not financial advice."""
import sys, itertools, re
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load
t = load(sys.argv[1]); t = t[t.date >= '2026-10-23']
key = t.symbol + '|' + t.date + '|' + np.sign(t.side).astype(int).astype(str)
sets = t.assign(k=key).groupby('strategy').k.apply(set)
sets = sets[sets.apply(len) >= 20]
dr = t.pivot_table(index='date', columns='strategy', values='r', aggfunc='sum')
fam = lambda s: s.split('-', 1)[0]
pairs = []
for a, b in itertools.combinations(sets.index, 2):
    i = len(sets[a] & sets[b])
    if not i: continue
    j = i / len(sets[a] | sets[b])
    if j < 0.3: continue
    x = dr[[a, b]].dropna()
    c = x[a].corr(x[b]) if len(x) >= 8 else np.nan
    pairs.append((a, b, round(j, 2), round(c, 2), len(x)))
p = pd.DataFrame(pairs, columns=['a', 'b', 'jaccard', 'day_corr', 'common_days']).sort_values('jaccard', ascending=False)
print('setups with >=20 live trades:', len(sets), '| families:', len({fam(s) for s in sets.index}))
for th in (0.3, 0.5, 0.7):
    q = p[p.jaccard >= th]
    nodes = set(q.a) | set(q.b)
    # greedy clusters
    import collections
    par = {n: n for n in nodes}
    def f(n):
        while par[n] != n: n = par[n]
        return n
    for a, b in zip(q.a, q.b): par[f(a)] = f(b)
    cl = collections.Counter(f(n) for n in nodes)
    print(f'Jaccard>={th}: pairs {len(q)}, setups involved {len(nodes)}, clusters {len(cl)}, setups removable (keep 1 per cluster) {len(nodes)-len(cl)}')
print(p.head(15).to_string(index=False))
