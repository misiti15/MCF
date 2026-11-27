"""SHORTCOST-1127 POST-HOC (not pre-registered; counted as config 6; cannot PASS): P6 = shorts only in names that were ETB
in all 26 universe snapshots (etb_rate == 1.0), after the live map showed ETB-marginal shorts at -0.265 vs -0.160 R.
History replay with the same engine and size-matched random removal (20 seeds). Caveat: etb_rate comes from 2026
snapshots, applied to T2/CHECK history (anachronistic). `python sc_posthoc.py SCRATCH` -> posthoc.json.
Educational only - not financial advice."""
import json, os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = sys.argv[:2]
import sc_hist as H  # noqa: E402
import sc_common as C  # noqa: E402
X = H.X
sk = (X.side.values < 0) & (X.symbol.map(H.ETB).fillna(0).values < 1.0)


def books(keep):
    b = H.run_book(X[keep], "r_ll")
    return b


def daily(b, per, tags=H.REAL):
    return b[(b.per == per) & b.tag.isin(tags)].groupby("date").r.sum().reindex(H.DAYS[per], fill_value=0.0)


base = books(np.ones(len(X), bool)); rule = books(~sk)
rnd = []
for s in range(20):
    rng = np.random.default_rng(2000 + s); keep = np.ones(len(X), bool)
    for (tg, p), idx in X.groupby(["tag", "per"]).indices.items():
        k = int(round(sk[idx].mean() * len(idx)))
        if k:
            keep[rng.choice(idx, k, replace=False)] = False
    rnd.append(books(keep))
out = {}
for per in ("FIT", "CHECK", "T2"):
    d0, d1 = daily(base, per), daily(rule, per)
    dr = np.mean([daily(b, per).values for b in rnd], axis=0); diff = d1.values - dr
    o = dict(base_R=float(d0.sum()), rule_R=float(d1.sum()), random_R=float(dr.sum()), gain_vs_random=float(diff.sum()),
             gain_t_day=C.day_t(diff), gain_best_day_share=float(diff.max() / diff.sum()) if diff.sum() > 0 else None,
             skip_share=float(sk[(X.per == per).values & X.tag.isin(H.REAL).values].mean()))
    ps = {}
    for tg in H.REAL:
        a = base[(base.per == per) & (base.tag == tg)].r; b = rule[(rule.per == per) & (rule.tag == tg)].r
        rr = np.mean([bb[(bb.per == per) & (bb.tag == tg)].r.sum() for bb in rnd])
        ps[tg] = dict(base_avg=float(a.mean()) if len(a) else None, rule_avg=float(b.mean()) if len(b) else None,
                      base_R=float(a.sum()), rule_R=float(b.sum()), gain_vs_random=float(b.sum() - rr))
    o["per_setup"] = ps; out[per] = o
    print(per, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in o.items() if k != "per_setup"})
    print(pd.DataFrame(ps).T.round(3).to_string())
json.dump(out, open(os.path.join(HERE, "posthoc.json"), "w"), indent=1, default=float)
