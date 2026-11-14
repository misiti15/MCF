"""OBS-STOPSLIP refit (Skeptic 0450-1 / Lead 0500-1): side split instead of a symmetric trim. Keep every stop exit filled
at or worse than the ORIGINAL stop (adverse tail kept, however large); drop exits better than the stop by > 0.02R (moved
breakeven / trailing stops; trades.stop keeps the original stop). Report quantiles incl. p95/p99, the spread/stop fit,
and the fit by window (10-20..11-03, 11-04..11-06 sel, 11-09, 11-10..11-11 holdout). 0 configs.
Educational only - not financial advice. usage: python stopslip2.py <dir of journals>"""
import sqlite3, sys, json, pandas as pd, numpy as np
D = sys.argv[1]; F = []
for nm, b in [('Primary','mcf-data'),('On Deck','mcf-data-testing'),('Testing A','mcf-data-testing2'),('Testing B','mcf-data-explore1'),
              ('Testing C','mcf-data-livelab'),('Graveyard','mcf-data-graveyard'),('Gen','mcf-data-gen')]:
    t = pd.read_sql("select date, side, entry, stop, exit, meta from trades where run_id=1 and date between '2026-10-20' and "
                    "'2026-11-11' and exit_reason='stop'", sqlite3.connect(f"{D}/{b}.db")); t["acct"] = nm; F.append(t)
t = pd.concat(F, ignore_index=True); n0 = len(t)
t = t[(t.entry - t.stop).abs() > 0].copy()
t["slip"] = t.side * (t.stop - t.exit) / (t.entry - t.stop).abs()
t["sor"] = t.meta.map(lambda m: (lambda j: j.get("spread_bps"))(json.loads(str(m).split(";")[0]))).astype(float) / \
           ((t.entry - t.stop).abs() / t.entry * 1e4)
moved = t.slip < -0.02
print(f"stop exits {n0}; better than stop by >0.02R (moved stops, dropped) {moved.sum()} ({moved.mean():.1%}); by acct",
      {k: f"{g.mean():.1%}" for k, g in moved.groupby(t.acct)})
k = t[~moved].copy()
q = k.slip.quantile([.5, .75, .9, .95, .99]).round(3).to_dict()
print(f"kept {len(k)}: mean {k.slip.mean():+.4f} quantiles {q} max {k.slip.max():.2f}; share > 0.3R {(k.slip>0.3).mean():.1%}")
for a, g in k.groupby("acct"): print(f"  {a:10s} n {len(g):5d} mean {g.slip.mean():+.4f} p95 {g.slip.quantile(.95):.3f} p99 {g.slip.quantile(.99):.3f}")
def fit(x):
    X = np.c_[np.ones(len(x)), x.sor.clip(upper=0.5)]; return np.linalg.lstsq(X, x.slip, rcond=None)[0]
b = fit(k); print(f"fit (all kept): slip_R = {b[0]:+.4f} + {b[1]:.3f} x spread/stop")
print("by spread/stop quintile: mean / p95:", [(round(g.slip.mean(), 3), round(g.slip.quantile(.95), 3)) for _, g in k.groupby(pd.qcut(k.sor, 5), observed=True)])
W = {"10-20..11-03": ("2026-10-20", "2026-11-03"), "11-04..11-06 (sel)": ("2026-11-04", "2026-11-06"), "11-09": ("2026-11-09", "2026-11-09"),
     "11-10..11-11 (hold)": ("2026-11-10", "2026-11-11")}
for w, (a, z) in W.items():
    g = k[(k.date >= a) & (k.date <= z)]; bb = fit(g)
    print(f"  {w:20s} n {len(g):5d} mean {g.slip.mean():+.4f} med {g.slip.median():+.4f} p95 {g.slip.quantile(.95):.3f} fit {bb[0]:+.4f} + {bb[1]:.3f}x")
d = k.groupby("date").slip.mean(); print("per-day mean slip: min {:.3f} med {:.3f} max {:.3f}".format(d.min(), d.median(), d.max()))
