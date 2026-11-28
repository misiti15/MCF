"""Score the live what-if pairs (live_rwtgt.py replay). Paired delta d = R_v - R_p (same engine both arms); variant live R
= journal LR8 R + d. Day-clustered t, sign-flip p (10,000, seed 20261128), weeks, best-day share of the gain, avg R w/o
best day for both arms, per setup. Usage: python live_score.py WORK. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
W = sys.argv[1]
t = pd.read_parquet(f"{W}/live_pairs.parquet"); t = t[t.ok.astype(bool)].copy()
t["d"] = t.rg_v - t.rg_p
t["r_var"] = t.r_live + t.d
t["cal"] = ((t.rg_p - t.r_live).abs() <= 0.10)
t["wk"] = pd.to_datetime(t.date).dt.to_period("W")
rng = np.random.default_rng(20261128)
def tstat(z):
    dd = z.groupby("date").d.sum(); n = len(z)
    e = (z.d - z.d.mean()).groupby(z.date).sum(); se = np.sqrt((e ** 2).sum()) / n
    return z.d.mean() / se if se > 0 else np.nan
def flip(z):
    dd = z.groupby("date").d.sum().to_numpy(); obs = dd.sum()
    s = rng.choice([-1, 1], size=(10000, len(dd))) @ dd
    return (np.abs(s) >= abs(obs)).mean()
def wo_best(z, col):
    day = z.groupby("date")[col].sum(); b = day.idxmax(); tot = day.sum()
    return z.loc[z.date != b, col].mean(), (day.max() / tot if tot > 0 else np.nan), b
print("live RW3/RW5 Primary 2026-10-23..11-27, run 1, LR8; paired replay on Alpaca 1-min SIP")
print(f"replay calibration: parent arm within 0.10R of journal R on {t.cal.mean():.0%}; mean rg_p - r_live {(t.rg_p - t.r_live).mean():+.3f}; "
      f"journal exit target {(t.exit_reason=='target').mean():.0%} vs replay {(t.kind_p=='target').mean():.0%}")
for name, z in [("RW3", t[t.strategy.str.startswith("RW3")]), ("RW5", t[t.strategy.str.startswith("RW5")]), ("both", t),
                ("both ex 11-25", t[t.date != "2026-11-25"]), ("both calibrated", t[t.cal])]:
    gain = z.groupby("date").d.sum(); bs = gain.max() / gain.sum() if gain.sum() > 0 else np.nan
    wk = z.groupby("wk").d.sum()
    pw, ps, pb = wo_best(z, "r_live"); vw, vs, vb = wo_best(z, "r_var")
    print(f"{name:16s} n {len(z):3d} days {z.date.nunique():2d} | live avg {z.r_live.mean():+.3f} (w/o best {pw:+.3f}, share {ps:.0%} {pb}) -> "
          f"var {z.r_var.mean():+.3f} (w/o best {vw:+.3f}, share {vs:.0%}) | d {z.d.mean():+.4f} t {tstat(z):+.2f} flip p {flip(z):.3f} "
          f"total {z.d.sum():+.1f}R better/worse {(z.d>1e-9).sum()}/{(z.d<-1e-9).sum()} weeks up {(wk>0).sum()}/{len(wk)} best-day share of gain {bs:.0%}")
x = pd.crosstab(t.kind_p, t.kind_v); print("parent exit x variant exit (replay):\n", x)
g = t[(t.kind_p == "target")]
print("parent-target trades: reach 1.25x", int((g.kind_v == "target").sum()), f"avg d {g[g.kind_v=='target'].d.mean():+.3f}",
      "| flattened", int((g.kind_v == "market").sum()), f"avg d {g[g.kind_v=='market'].d.mean():+.3f}",
      "| to stop", int((g.kind_v == "stop").sum()), f"avg d {g[g.kind_v=='stop'].d.mean():+.3f}")
print("weekly d sums:", {str(k): round(v, 2) for k, v in t.groupby("wk").d.sum().items()})
print("daily d top/bottom:", t.groupby("date").d.sum().sort_values().round(2).iloc[[0, 1, 2, -3, -2, -1]].to_dict())
for lo, hi, lab in [("2026-10-23", "2026-11-17", "inside original window (10-23..11-17, in-sample)"), ("2026-11-18", "2026-11-27", "after original window (11-18..11-27, out-of-sample)")]:
    z = t[(t.date >= lo) & (t.date <= hi)]
    print(f"{lab}: n {len(z)} d {z.d.mean():+.4f} t {tstat(z):+.2f} total {z.d.sum():+.1f}R")
