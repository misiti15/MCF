"""Move-hunt LONG evidence: pre-declared grid over the fit-half table from movehunt_long_build.py.
Every bucket / combo below is one counted configuration (x 1 primary outcome r_g1; r_g2 and r_t30 reported alongside,
not used to pick). Day-clustered t. fitA = sessions < 2025-06-01, fitB = 2025-06-01..2025-09-30 (both inside the fit half).
    python research/ultimate_1119/movehunt_long_analyze.py /dev/shm/mh_long.parquet > out.txt
Educational only - not financial advice.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

D = pd.read_parquet(sys.argv[1])
D = D[(D["tod"] >= 950) & (D["tod"] <= 1515)].reset_index(drop=True)
# Cost top-up to be at least the LR8 basis (mcf/costs.py lot_costs + config/default.yaml live_model): the builder
# charges each stop exit 1bp+$0.03/sh and the entry 1bp+$0.01; LR8 charges stops max($0.02, 4bp) and entry 1bp, so on
# names above ~$133 the builder is short. Top up stop exits (r <= -1 net) by the shortfall; add SEC/FINRA ~0.25bp on
# every exit. Target exits stay over-charged (LR8 charges a limit fill nothing) -> figures understate, by design.
_R = D["R_pct"].astype(float) / 100 * D["px"].astype(float)
_px = D["px"].astype(float)
_short = np.maximum(0.0, np.maximum(0.02, 4e-4 * _px) - (0.04 + 1e-4 * _px)) / _R
_fee = 0.25e-4 * _px / _R
for _c in ("r_g1", "r_g2"):
    D[_c] = D[_c] - _fee - np.where(D[_c] <= -1, _short, 0.0)
D["r_t30"] = D["r_t30"] - _fee
D["cost_r"] = D["cost_r"] + _fee + _short
D["half"] = np.where(D["date"] < "2025-06-01", "A", "B")
D["todb"] = pd.cut(D["tod"], [949, 1030, 1200, 1400, 1515], labels=["0950-1030", "1030-1200", "1200-1400", "1400-1515"])
NCFG = 0
BASE = {}


def stats(x: pd.DataFrame, col="r_g1") -> dict:
    if len(x) == 0:
        return dict(n=0)
    g = x.groupby("date")[col].agg(["sum", "count"])
    n, S = g["count"].sum(), g["sum"].sum()
    m = S / n
    k = len(g)
    # ratio-estimator day-clustered SE
    resid = g["sum"] - m * g["count"]
    se = np.sqrt((resid ** 2).sum() * k / max(k - 1, 1)) / n
    best = g["sum"].max()
    wob = (S - best) / (n - g.loc[g["sum"].idxmax(), "count"]) if n > g["count"].max() else np.nan
    # tod-matched baseline: expected r_g1 of random bars with the same time-of-day mix
    exp = (x["todb"].map(BASE["tod"]).astype(float)).mean()
    hA = x.loc[x.half == "A", col].mean()
    hB = x.loc[x.half == "B", col].mean()
    return dict(n=n, sess=k, per_sess=n / k, avgR=m, t=m / se if se > 0 else np.nan, lift=m - exp,
                hit1=(x["mfe45"] >= 1).mean(), win=(x["r_g1"] > 0.5).mean(), g2=x["r_g2"].mean(), t30=x["r_t30"].mean(),
                totR=S, woBest=wob, bestShare=best / S if S > 0 else np.nan, A=hA, B=hB, costR=x["cost_r"].median(),
                gross=(x[col] + x["cost_r"]).mean(),
                PASS=bool(m > 0 and se > 0 and m / se >= 2 and hA > 0 and hB > 0 and np.isfinite(wob) and wob > 0
                          and (best / S if S > 0 else 1) < 0.5))


def show(rows, title):
    print(f"\n## {title}\n")
    df = pd.DataFrame(rows).set_index("cfg")
    with pd.option_context("display.width", 250, "display.max_columns", 30, "display.float_format", "{:.3f}".format):
        print(df.to_string())


def run(name, mask, base=None, rows=None):
    global NCFG
    NCFG += 1
    x = (base if base is not None else D)[mask]
    r = stats(x)
    r["cfg"] = name
    rows.append(r)


def dedupe(x: pd.DataFrame, cool=45) -> pd.DataFrame:
    """first trigger per symbol-day, then the next only after `cool` minutes (non-overlapping 45-min holds)."""
    x = x.sort_values(["symbol", "date", "tod"])
    mins = (x["tod"] // 100) * 60 + x["tod"] % 100
    keep = np.zeros(len(x), bool)
    last_key, last_t = None, -999
    for i, (s, d, t) in enumerate(zip(x["symbol"].values, x["date"].values, mins.values)):
        k = (s, d)
        if k != last_key or t - last_t >= cool:
            keep[i] = True
            last_key, last_t = k, t
    return x[keep]


# ---------------- baseline
BASE["tod"] = D.groupby("todb", observed=True)["r_g1"].mean().to_dict()
rows = []
r = stats(D); r["cfg"] = "ALL random bars"; rows.append(r)
for b in D["todb"].cat.categories:
    r = stats(D[D.todb == b]); r["cfg"] = f"tod {b}"; rows.append(r)
show(rows, "Baseline: random entries (every 5-min bar, universe px>=5, ADV20>=$20M)")

# ---------------- Stage 1: univariate, pre-declared buckets
rows = []
grid = {
    "fo_atr": [(-0.5, 99), (-1, -0.5), (-1.5, -1), (-2, -1.5), (-99, -2)],
    "hod_atr": [(-1, 0.5), (0.5, 1), (1, 1.5), (1.5, 2), (2, 99)],
    "rsi2": [(-1, 5), (5, 10), (10, 25), (25, 101)],
    "rsi5": [(-1, 15), (15, 25), (25, 35), (35, 101)],
    "vwap_z": [(-1, 99), (-2, -1), (-3, -2), (-99, -3)],
    "gap": [(-99, -3), (-3, -1), (-1, 1), (1, 3), (3, 999)],
    "spy_fo": [(-99, -1), (-1, -0.3), (-0.3, 0.3), (0.3, 99)],
    "spy_r30": [(-99, -0.3), (-0.3, 0.3), (0.3, 99)],
    "adv20": [(2e7, 5e7), (5e7, 2e8), (2e8, 1e9), (1e9, 1e13)],
    "atr_pct": [(0, 2), (2, 4), (4, 99)],
    "ret15_atr": [(-99, -0.5), (-0.5, -0.25), (-0.25, 0.25), (0.25, 99)],
}
for k, bs in grid.items():
    for lo, hi in bs:
        run(f"{k} [{lo},{hi})", (D[k] >= lo) & (D[k] < hi), rows=rows)
run("vr4>=3 (vol spike last 20m)", D.vr4 >= 3, rows=rows)
run("or_reclaim", D.or_reclaim == 1, rows=rows)
run("vwap_reclaim", D.vwap_reclaim == 1, rows=rows)
run("at LOD (lod_atr<0.05)", D.lod_atr < 0.05, rows=rows)
run("higher low: lod_age 5-20m & up bar", (D.lod_age.between(5, 20)) & (D.up_bar == 1), rows=rows)
show(rows, "Stage 1: univariate precursors (all bars, overlapping)")

# ---------------- Stage 2: within washout base
W = D[(D.fo_atr <= -1.0) | (D.hod_atr >= 1.5)]
rows = []
r = stats(W); r["cfg"] = "W = fo_atr<=-1 or hod_atr>=1.5"; rows.append(r); NCFG += 1
conds = {
    "up_bar (green 5m bar)": W.up_bar == 1,
    "rsi2<=10": W.rsi2 <= 10,
    "rsi2<=10 & up_bar": (W.rsi2 <= 10) & (W.up_bar == 1),
    "rsi2>=50 (already bouncing)": W.rsi2 >= 50,
    "vwap_z<=-2": W.vwap_z <= -2,
    "vwap_z<=-2 & up_bar": (W.vwap_z <= -2) & (W.up_bar == 1),
    "vr4>=3": W.vr4 >= 3,
    "cap-HL: vr4>=3 & lod_age 5-20 & up": (W.vr4 >= 3) & W.lod_age.between(5, 20) & (W.up_bar == 1),
    "higher low: lod_age 10-30 & lod_atr 0.1-0.4": W.lod_age.between(10, 30) & W.lod_atr.between(0.1, 0.4),
    "at LOD (lod_atr<0.05)": W.lod_atr < 0.05,
    "or_reclaim": W.or_reclaim == 1,
    "vwap_reclaim": W.vwap_reclaim == 1,
    "tod 0950-1030": W.todb == "0950-1030",
    "tod 1030-1200": W.todb == "1030-1200",
    "tod 1200-1400": W.todb == "1200-1400",
    "tod 1400-1515": W.todb == "1400-1515",
    "spy_r30>=-0.1 (tape not falling)": W.spy_r30 >= -0.1,
    "spy_r30<-0.3 (tape falling)": W.spy_r30 < -0.3,
    "spy_fo>0": W.spy_fo > 0,
    "spy_lod>=0.3 (SPY off its low)": W.spy_lod >= 0.3,
    "gap>=+1 (gap-up washed out)": W.gap >= 1,
    "gap<=-1 (gap-down extending)": W.gap <= -1,
    "pc_atr<=-1.3 (down >1.3 ATR vs prior close)": W.pc_atr <= -1.3,
    "ret60_atr<=-1 (fast fall)": W.ret60_atr <= -1,
    "adv20>=2e8": W.adv20 >= 2e8,
    "atr_pct>=4": W.atr_pct >= 4,
    "cost_r<=0.10": W.cost_r <= 0.10,
}
for k, m in conds.items():
    run(k, m, base=W, rows=rows)
show(rows, "Stage 2: confirmations inside the washout base W (overlapping bars)")

# pre-declared pass rule (applies to every row): net avgR > 0, day-clustered t >= 2, both fit sub-halves > 0,
# avg R without best day > 0, best-day share < 50%. Passing here is fit-half evidence only (check half untouched).
# ---------------- Stage 3: pre-declared combos, deduped (non-overlapping 45-min holds)
WO = (D.fo_atr <= -1.0) | (D.hod_atr >= 1.5)
combos = {
    "C1 W & rsi2<=10 & up_bar": WO & (D.rsi2 <= 10) & (D.up_bar == 1),
    "C2 W & vwap_z<=-2 & up_bar": WO & (D.vwap_z <= -2) & (D.up_bar == 1),
    "C3 cap-HL: fo<=-0.75 & vr4>=3 & lod_age 5-20 & up": (D.fo_atr <= -0.75) & (D.vr4 >= 3) & D.lod_age.between(5, 20) & (D.up_bar == 1),
    "C4 W & or_reclaim": WO & (D.or_reclaim == 1),
    "C5 hod>=1.5 & vwap_reclaim": (D.hod_atr >= 1.5) & (D.vwap_reclaim == 1),
    "C6 W & up_bar & spy_r30>=-0.1": WO & (D.up_bar == 1) & (D.spy_r30 >= -0.1),
    "C7 C1 & tod>=1030": WO & (D.rsi2 <= 10) & (D.up_bar == 1) & (D.tod >= 1030),
    "C8 vwap_z<=-3 (any)": D.vwap_z <= -3,
    "C9 W & higher low (lod_age 10-30, lod_atr .1-.4) & up & spy_r30>=-0.1": WO & D.lod_age.between(10, 30) & D.lod_atr.between(0.1, 0.4) & (D.up_bar == 1) & (D.spy_r30 >= -0.1),
    "C10 C6 & cost_r<=0.10": WO & (D.up_bar == 1) & (D.spy_r30 >= -0.1) & (D.cost_r <= 0.10),
}
rows = []
for k, m in combos.items():
    NCFG += 1
    x = dedupe(D[m])
    r = stats(x); r["cfg"] = k; rows.append(r)
show(rows, "Stage 3: pre-declared combos, deduped (one live position per symbol at a time)")
print(f"\nconfigurations counted: {NCFG}")
