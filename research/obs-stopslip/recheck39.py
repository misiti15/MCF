"""Checklist #39 recheck of OBS-STOPSLIP day-t (Observer 2026-11-14): pooled ratio estimator (sum over days / count over days)
with day-clustered SE from per-day residual sums, vs the original mean-of-daily-means t. Same data and filters as stopslip2.py
(side split: drop exits better than the original stop by > 0.02R). 0 configs. Educational only - not financial advice.
usage: python recheck39.py <dir of journals>"""
import sqlite3, sys, json, pandas as pd, numpy as np
D = sys.argv[1]; F = []
for nm, b in [('Primary','mcf-data'),('On Deck','mcf-data-testing'),('Testing A','mcf-data-testing2'),('Testing B','mcf-data-explore1'),
              ('Testing C','mcf-data-livelab'),('Graveyard','mcf-data-graveyard'),('Gen','mcf-data-gen')]:
    t = pd.read_sql("select date, side, entry, stop, exit, meta from trades where run_id=1 and date between '2026-10-20' and "
                    "'2026-11-11' and exit_reason='stop'", sqlite3.connect(f"{D}/{b}.db")); t["acct"] = nm; F.append(t)
t = pd.concat(F, ignore_index=True); t = t[(t.entry - t.stop).abs() > 0].copy()
t["slip"] = t.side * (t.stop - t.exit) / (t.entry - t.stop).abs(); t = t[t.slip >= -0.02]
t["sor"] = t.meta.map(lambda m: json.loads(str(m).split(";")[0]).get("spread_bps")).astype(float) / ((t.entry - t.stop).abs() / t.entry * 1e4)
def old_t(x):
    g = x.groupby("date").slip.mean(); return g.mean() / (g.std(ddof=1) / np.sqrt(len(g)))
def ratio(x):
    s = x.groupby("date").slip.sum(); n = x.groupby("date").slip.size(); m = s.sum() / n.sum()
    res = s - m * n; G = len(s); se = np.sqrt(G / (G - 1) * (res ** 2).sum()) / n.sum(); return m, m / se
print(f"{'cell':28s} {'n':>5s}  pooled mean  ratio day-t  old day-t")
cells = [("ALL", t)] + [(a, g) for a, g in t.groupby("acct")] + [(f"spread/stop Q{i+1}", g) for i, (_, g) in enumerate(t.groupby(pd.qcut(t.sor, 5), observed=True))]
for name, x in cells:
    if x.date.nunique() < 3: continue
    m, tr = ratio(x); print(f"{name:28s} {len(x):5d}  {m:+.4f}      {tr:+7.2f}      {old_t(x):+7.2f}")
