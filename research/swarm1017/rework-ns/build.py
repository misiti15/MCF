"""Build the NS-family superset from the OPEN 2-year frames (locked block never loaded: lib.load_month refuses it).
Rows: adv20 >= 95M, bar close 09:50-15:00, and any loose NS core (PLAN.md). Adds prev-bar values (same symbol-day),
production-cost R for both sides x 3 geoms, and per-(date, bar) context: SPY fromOpen, breadth, same-minute random
baseline (mean production R of all min_adv names). Educational only - not financial advice.
    python build.py <scratch_dir>"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.research.gates import prod_r  # noqa: E402
from research.history2y import lib  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
FEAT = ["rsi", "rsi5", "fromOpen", "gap", "vwapDistPct", "sma50_dist_pct", "sma20_slope_pct", "volumeRatio", "atrPct",
        "heat", "buyPressure", "dist_hod_atr", "dist_lod_atr", "close", "atr_d", "adv20"]
SG = [(s, g) for s in ("short", "long") for g in ("t1s1", "t05s1", "t1s05")]
OUTC = [f"{k}_{s}_{g}" for s, g in SG for k in ("r", "win")]
MIN_ADV = 95e6

sup, ctx = [], []
for m in lib.months():
    t = time.time()
    d = lib.load_month(m, ["symbol", "date", "tod"] + FEAT + OUTC)
    d = d[(d.tod >= 950) & (d.tod <= 1500)].reset_index(drop=True)
    key = d.symbol.astype(str).to_numpy() + "|" + d.date.astype(str).to_numpy()
    first = np.r_[True, key[1:] != key[:-1]]
    for c in ("rsi", "sma50_dist_pct", "vwapDistPct"):
        x = d[c].to_numpy(float)
        p = np.r_[np.nan, x[:-1]]
        p[first] = np.nan
        d["p_" + c] = p.astype("float32")
    spy = d.loc[d.symbol == "SPY", ["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    e = d[(d.adv20 >= MIN_ADV) & (d.atr_d > 0)].copy()
    del d
    for s, g in SG:
        r = e[f"r_{s}_{g}"].to_numpy(float)
        ok = np.isfinite(r)
        pr = np.full(len(e), np.nan)
        pr[ok] = prod_r(r[ok], e[f"win_{s}_{g}"].to_numpy(float)[ok], e.close.to_numpy(float)[ok],
                        e.atr_d.to_numpy(float)[ok], g, tod=e.tod.to_numpy(float)[ok])
        e[f"p_{s}_{g}"] = pr.astype("float32")
    pc = [f"p_{s}_{g}" for s, g in SG]
    e["_up"] = (e.fromOpen > 0).astype(float)
    c = e.groupby(["date", "tod"]).agg(**{f"b_{k[2:]}": (k, "mean") for k in pc},
                                        breadth=("_up", "mean"), n_univ=("symbol", "size")).reset_index()
    c = c.merge(spy, on=["date", "tod"], how="left")
    ctx.append(c)
    rsi, prsi, r5, fo = e.rsi, e.p_rsi, e.rsi5, e.fromOpen
    sx, psx, vx, pvx = e.sma50_dist_pct, e.p_sma50_dist_pct, e.vwapDistPct, e.p_vwapDistPct
    smaup = (sx > 0) & (psx <= 0)
    smadn = (sx < 0) & (psx >= 0)
    vwup = (vx > 0) & (pvx <= 0)
    loose = (((rsi <= 45) & (prsi > 35) & (r5 >= 70) & (fo > 1))
             | (smaup & (rsi >= 50) & (fo > 1))
             | (vwup & (fo < -1))
             | (vwup & (rsi <= 40) & (fo > 1))
             | (smadn & (rsi <= 35) & (fo < -1)))
    s = e.loc[loose, ["symbol", "date", "tod"] + FEAT + ["p_rsi", "p_sma50_dist_pct", "p_vwapDistPct"] + pc]
    sup.append(s)
    print(m, len(e), len(s), round(time.time() - t, 1), flush=True)
    del e
ctx = pd.concat(ctx, ignore_index=True)
sup = pd.concat(sup, ignore_index=True).merge(ctx, on=["date", "tod"], how="left")
sup = sup.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
sup.to_parquet(OUT / "superset.parquet")
ctx.to_parquet(OUT / "ctx.parquet")
print("done", len(sup), len(ctx))
