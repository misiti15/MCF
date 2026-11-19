"""ICCSET-3 - does setup FAMILY explain ICC? (better shrink target for thin / new setups). Descriptive, 0 configs.
Family = name prefix before the first '-' (GEN-* -> GEN; heat_fade_*; exhaustion_*), side = long / short by majority.
Weighted (1/se^2) between-group test: Q_between vs chi2(groups-1); share of tau^2 explained.
    python -I family.py <iccset_shrunk.csv>        Educational only - not financial advice."""
import sys, re, numpy as np, pandas as pd
from math import erf, sqrt
D = pd.read_csv(sys.argv[1])
def fam(s):
    if s.startswith("GEN"): return "GEN"
    m = re.match(r"([A-Za-z]+\d*)", s); f = m.group(1) if m else s
    return {"heat": "heat_fade", "exhaustion": "exhaustion", "intraday": "momentum"}.get(f.split("_")[0], f)
D["family"] = D.setup.map(fam); D["sidec"] = np.where(D.side > 0.5, "long", "short"); D["wt"] = 1 / D.se ** 2
def chi2_sf(q, k):        # Wilson-Hilferty approximation
    z = ((q / k) ** (1 / 3) - (1 - 2 / (9 * k))) / sqrt(2 / (9 * k)); return 0.5 * (1 - erf(z / sqrt(2)))
mu = np.average(D.icc, weights=D.wt); Qt = (D.wt * (D.icc - mu) ** 2).sum()
for g in ("family", "sidec"):
    G = D.groupby(g).apply(lambda x: pd.Series({"n": len(x), "icc_w": np.average(x.icc, weights=x.wt), "W": x.wt.sum()}), include_groups=False)
    Qb = (G.W * (G.icc_w - mu) ** 2).sum(); k = len(G) - 1
    print(f"\nby {g}: Q_between {Qb:.1f} of Q_total {Qt:.1f} ({Qb / Qt:.0%}), df {k}, p ~ {chi2_sf(Qb, k):.4f}")
    print(G.sort_values("icc_w").round(3).to_string())
print("\nEducational only - not financial advice.")

# ---- coarse groups (fixed by setup design, not by ICC): fewer groups -> a fair test of 'family explains ICC'
def coarse(f):
    if f.startswith("CWT"): return "CWT structure (level breaks, coils, VWAP stretch, flush, gap bounce)"
    if re.match(r"(RW|MF|NS|L3|ST)\d*", f): return "flow / gap-day (RW, MF, NS, L3, ST)"
    if f == "GEN": return "GEN"
    if f in ("heat_fade", "exhaustion", "momentum"): return "heat / exhaustion / momentum"
    return "other (NM, LIQ)"
D["coarse"] = D.family.map(coarse)
G = D.groupby("coarse").apply(lambda x: pd.Series({"n": len(x), "icc_w": np.average(x.icc, weights=x.wt), "W": x.wt.sum(),
                                                    "icc_s_median": x.icc_s.median()}), include_groups=False)
Qb = (G.W * (G.icc_w - mu) ** 2).sum(); k = len(G) - 1
print(f"\nby coarse group: Q_between {Qb:.1f} of {Qt:.1f} ({Qb / Qt:.0%}), df {k}, p ~ {chi2_sf(Qb, k):.6f}")
print(G.sort_values("icc_w").round(3).to_string())
# within-group residual heterogeneity: what is left after the group mean
D["grp_mu"] = D.coarse.map(G.icc_w); Qw = (D.wt * (D.icc - D.grp_mu) ** 2).sum()
print(f"residual Q_within {Qw:.1f} on df {len(D) - len(G)} -> residual tau^2 ~ {max(0, (Qw - (len(D) - len(G))) / (D.wt.sum() - (D.wt ** 2).sum() / D.wt.sum())):.4f}")
