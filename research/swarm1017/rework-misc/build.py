"""Build per-month supersets for the rework-misc families (PLAN.md) from the OPEN 2-year frames.
Usage: python build.py <month> <outdir>. Locked block never loaded (lib.load_month refuses it).
Outputs (<outdir>/<family>/<month>.parquet): ctx (per date+bar baselines, breadth, SPY fromOpen), hs, hl, orb, im, liq.
Educational only - not financial advice."""
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE / "modules"))
from mcf.research.gates import prod_r  # noqa: E402
from research.history2y import lib  # noqa: E402
import liqx  # noqa: E402

liqx.use_numba()
month, OUT = sys.argv[1], Path(sys.argv[2])
assert month not in lib.LOCKED_MONTHS
SG = [(s, g) for s in ("short", "long") for g in ("t1s1", "t05s1", "t1s05")]
OUTC = [f"{k}_{s}_{g}" for s, g in SG for k in ("r", "win")]
PC = [f"p_{s}_{g}" for s, g in SG]
HEATC = ["rsiHeat", "priceActionHeat", "momentumHeat", "vwapHeat"]
FEAT = ["tod", "close", "high", "low", "atr_d", "adv20", "gap", "fromOpen", "vwapDistPct", "volumeRatio", "atrPct",
        "sma20_slope_pct", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr", "dist_pdl_atr", "sma50_dist_pct", "rsi"]
KEEP = ["symbol", "date"] + FEAT + PC
LIQ_SETS = list(itertools.product(("OR", "PD"), ("low", "high"), (0.05, 0.10, 0.15, 0.25), ("open", "lvl"), (5, 15)))
IM_E = (1030, 1100, 1200, 1300, 1400, 1500)

t0 = time.time()
d = lib.load_month(month, ["symbol", "date"] + FEAT + HEATC + OUTC)
d = d[(d.tod >= 950) & (d.tod <= 1500) & (d.adv20 >= 95e6) & (d.atr_d > 0)].reset_index(drop=True)
for s, g in SG:
    r = d[f"r_{s}_{g}"].to_numpy(float)
    ok = np.isfinite(r)
    pr = np.full(len(d), np.nan)
    pr[ok] = prod_r(r[ok], d[f"win_{s}_{g}"].to_numpy(float)[ok], d.close.to_numpy(float)[ok],
                    d.atr_d.to_numpy(float)[ok], g, tod=d.tod.to_numpy(float)[ok])
    d[f"p_{s}_{g}"] = pr
d = d.drop(columns=OUTC)
sd = (d.symbol.astype(str) + "|" + d.date.astype(str)).to_numpy()
newseg = np.r_[True, sd[1:] != sd[:-1]]
seg = np.cumsum(newseg) - 1


def save(fam, df):
    p = OUT / fam
    p.mkdir(parents=True, exist_ok=True)
    num = [c for c in df.columns if df[c].dtype.kind == "f"]
    df.astype({c: "float32" for c in num}).to_parquet(p / f"{month}.parquet", index=False)


# ---- ctx: same-minute baselines (95M and 125M populations), breadth, SPY fromOpen
big = d.adv20 >= 125e6
c95 = d.groupby(["date", "tod"]).agg(**{f"b95_{k[2:]}": (k, "mean") for k in PC},
                                     breadth=("fromOpen", lambda x: float((x > 0).mean())), n95=("symbol", "size"))
c125 = d[big].groupby(["date", "tod"]).agg(**{f"b125_{k[2:]}": (k, "mean") for k in PC})
spy = d[d.symbol == "SPY"].set_index(["date", "tod"])["fromOpen"].rename("spy_fo")
ctx = c95.join(c125).join(spy).reset_index()
# SPY r30 (prev close -> 10:00) per date
s10 = d[(d.symbol == "SPY") & (d.tod == 1000)]
ctx = ctx.merge(pd.DataFrame({"date": s10.date, "spy_r30": ((1 + s10.gap / 100) * (1 + s10.fromOpen / 100) - 1) * 100}),
                on="date", how="left")
save("ctx", ctx)

# ---- heat scores (regime_score base, no tod gate here)
g = lambda c: np.nan_to_num(d[c].to_numpy(float))
base = g("rsiHeat") + g("priceActionHeat") - g("momentumHeat") - g("vwapHeat")
cost100 = 8.0 / d.atr_d.to_numpy(float)
d["hs_score"] = -base - 8.0 * cost100
d["hl_score"] = base - 5.0 * np.clip(g("fromOpen"), -3, 3) - 4.0 * cost100
save("hs", d.loc[big & (d.hs_score >= 5), KEEP + ["hs_score"]])
save("hl", d.loc[big & (d.hl_score >= 30), KEEP + ["hl_score"]])

# ---- ORB: OR from the 09:50 bar, fresh crosses after 09:50
tod = d.tod.to_numpy()
c = d.close.to_numpy(float)
atr = d.atr_d.to_numpy(float)
at950 = np.where(tod == 950, 1.0, np.nan)
first = lambda v: pd.Series(v * at950).groupby(seg).transform("max").to_numpy(float)
first_min = lambda v: pd.Series(v * at950).groupby(seg).transform("min").to_numpy(float)
orhi = pd.Series(np.where(tod == 950, c + d.dist_hod_atr.to_numpy(float) * atr, np.nan)).groupby(seg).transform("max").to_numpy(float)
orlo = pd.Series(np.where(tod == 950, c - d.dist_lod_atr.to_numpy(float) * atr, np.nan)).groupby(seg).transform("max").to_numpy(float)
fo950 = pd.Series(np.where(tod == 950, d.fromOpen.to_numpy(float), np.nan)).groupby(seg).transform("max").to_numpy(float)
vw950 = pd.Series(np.where(tod == 950, d.vwapDistPct.to_numpy(float), np.nan)).groupby(seg).transform("max").to_numpy(float)
rv950 = pd.Series(np.where(tod == 950, d.volumeRatio.to_numpy(float), np.nan)).groupby(seg).transform("max").to_numpy(float)
prevc = np.r_[np.nan, c[:-1]]
prevc[newseg] = np.nan
with np.errstate(invalid="ignore"):
    up = (tod >= 955) & (c > orhi) & (prevc <= orhi)
    dn = (tod >= 955) & (c < orlo) & (prevc >= orlo)
o = d.loc[up | dn, KEEP].copy()
o["ev"] = np.where(up, 1, -1)[up | dn]
for nm, v in (("fo950", fo950), ("vw950", vw950), ("rv950", rv950)):
    o[nm] = v[up | dn]
save("orb", o)

# ---- IM: rows at entry bars with the stock's own r30
fo1000 = pd.Series(np.where(tod == 1000, d.fromOpen.to_numpy(float), np.nan)).groupby(seg).transform("max").to_numpy(float)
r30 = ((1 + d.gap.to_numpy(float) / 100) * (1 + fo1000 / 100) - 1) * 100
im = np.isin(tod, IM_E)
x = d.loc[im, KEEP].copy()
x["r30"] = r30[im]
save("im", x)

# ---- LIQ: 64 sweep event sets, bitmask per row
bits = np.zeros(len(d), np.int64)
for bi, (lev, sw, xx, trig, k) in enumerate(LIQ_SETS):
    f = liqx.flags(d, lev, sw, xx, trig, k)
    bits |= f.astype(np.int64) << bi
w = d["vwapDistPct"].to_numpy(float)
lq = d.loc[bits != 0, KEEP].copy()
lq["bits"] = bits[bits != 0]
save("liq", lq)
print(month, len(d), "hs", int((big & (d.hs_score >= 5)).sum()), "hl", int((big & (d.hl_score >= 30)).sum()),
      "orb", len(o), "im", len(x), "liq", len(lq), round(time.time() - t0, 1), flush=True)
