"""eu1103/universe step 5 (added AFTER the pre-declared rules were read; counted separately): is the S1/S3/S5
'smaller universe' gain a cost effect? Buckets by R in dollars per share (2y: 0.25 x daily ATR; live: |entry - stop|),
with an estimate of the cost share of R (production per-side 1c + 1 bps, 2c stop extra, ~1 losing exit), plus the
random-entry excess (vs_rand, which carries the same costs and so isolates setup skill from cost). One extra rule:
C1 'R >= $0.25 per share' (daily ATR >= $1.00). Usage: python cost_mech.py <scratch> -> cost_mech_out.txt.
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

S = Path(sys.argv[1])
HERE = Path(__file__).resolve().parent
sys.argv = [sys.argv[0], str(S)]
import importlib.util
spec = importlib.util.spec_from_file_location("a2", HERE / "analyze2y.py"); A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)


def dstat(x, col):
    ds = x.groupby("date")[col].agg(["sum", "size"]); mu = x[col].mean()
    se = np.sqrt(((ds["sum"] - ds["size"] * mu) ** 2).sum()) / len(x)
    return round(mu, 4), round(mu / se, 2)


T = A.load()
T = T[T.adv20 >= T.floor].copy()
T["exc"] = T.r - T.rc
T["Rps"] = 0.25 * T.atr_d
T["cost_est"] = (0.03 + 0.0002 * T.px + 0.02 * 0.5) / T.Rps
bins = [0, 0.05, 0.10, 0.15, 0.25, 0.40, 0.75, 1e9]
labs = ["<5c", "5-10c", "10-15c", "15-25c", "25-40c", "40-75c", ">75c"]
T["rb"] = pd.cut(T.Rps, bins, labels=labs)
lines = ["Educational only - not financial advice. Mechanism check (post hoc). 2y = two-year lab trades at the live floor "
         "(8 setups, costs in); cost_est = estimated round-trip cost in R; vs_rand = R minus same symbol-day random entry."]
rows = []
for (sp, b), x in T.groupby(["split", "rb"], observed=True):
    m, t = dstat(x, "r"); e, et = dstat(x, "exc")
    rows.append(dict(split=sp, R_per_share=b, n=len(x), avgR=m, t=t, cost_est=round(x.cost_est.median(), 3),
                     avgR_plus_cost=round(m + x.cost_est.mean(), 3), vs_rand=e, vs_rand_t=et))
lines.append("\n== 2y by R per share\n" + pd.DataFrame(rows).to_string(index=False))
rows = []
for sp in ("TRAIN", "VALID"):
    x = T[T.split == sp]
    for name, keep in (("C1 R >= $0.25/share", x.Rps >= 0.25), ("S1 top-500 dollar-ATR (for reference)", None)):
        if keep is None:
            continue
        k, d = x[keep], x[~keep]
        dd = pd.concat([k.groupby("date").r.mean().rename("k"), d.groupby("date").r.mean().rename("d")], axis=1).dropna()
        diff = dd.k - dd.d
        rows.append(dict(rule=name, split=sp, kept_share=round(keep.mean(), 3), base_R=round(x.r.mean(), 4), kept_R=dstat(k, "r")[0],
                         kept_t=dstat(k, "r")[1], dropped_R=round(d.r.mean(), 4), kd=round(diff.mean(), 4),
                         kd_t=round(diff.mean() / (diff.std() / np.sqrt(len(diff))), 2), kept_vs_rand=round(k.exc.mean(), 4),
                         dropped_vs_rand=round(d.exc.mean(), 4),
                         setups_better=int(sum(k[k.setup == s].r.mean() >= x[x.setup == s].r.mean() for s in x.setup.unique()))))
lines.append("\n== 2y rule C1 (pooled; setups_better = of 8)\n" + pd.DataFrame(rows).to_string(index=False))
# live
L = pd.read_parquet(S / "live_trades.parquet")
L["Rps"] = (L.entry - L.stop).abs()
L["rb"] = pd.cut(L.Rps, bins, labels=labs)
rows = []
for b, x in L.groupby("rb", observed=True):
    m, t = dstat(x, "R")
    rows.append(dict(R_per_share=b, n=len(x), avgR=m, t=t, exc=round(x.exc.mean(), 3), spread_bps=round(x.spread_bps.median(), 1),
                     spread_in_R=round((x.spread_bps / 1e4 * x.entry / x.Rps).median(), 3)))
lines.append("\n== LIVE (run_id 1, 5 accounts, 10-06..11-02) by R per share (|entry-stop|); exc = R minus setup-account mean; "
             "spread_in_R = median entry spread / risk per share\n" + pd.DataFrame(rows).to_string(index=False))
for scope, x0 in (("ALL", L), ("Primary", L[L.acct == "p"])):
    k, d = x0[x0.Rps >= 0.25], x0[x0.Rps < 0.25]
    dd = pd.concat([k.groupby("date").R.mean().rename("k"), d.groupby("date").R.mean().rename("d")], axis=1).dropna()
    diff = dd.k - dd.d
    gk = k.groupby("date").R.sum()
    lines.append(f"LIVE {scope} C1: kept n {len(k)} avg R {dstat(k,'R')} | dropped n {len(d)} avg R {dstat(d,'R')} | "
                 f"kd {diff.mean():.3f} t {diff.mean()/(diff.std()/np.sqrt(len(diff))):.2f} | kept exc {k.exc.mean():.3f} dropped exc {d.exc.mean():.3f} | "
                 f"green sessions kept {(gk>0).sum()}/{len(gk)} vs all {(x0.groupby('date').R.sum()>0).sum()}/{x0.date.nunique()}")
(HERE / "cost_mech_out.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
