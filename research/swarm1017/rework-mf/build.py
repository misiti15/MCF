"""Build the MF-family superset (heat <= -20 & buyPressure < -0.15 & adv20 >= 95M) from the OPEN 2-year frames, with
production-cost R for both sides x 3 geoms, plus per-(date, bar) context: SPY fromOpen, breadth, and the same-minute
random baseline (mean production R of all min_adv names). Locked block never loaded (lib.load_month refuses it).
Educational only - not financial advice."""
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
FEAT = ["heat", "buyPressure", "vwapDistPct", "rsi", "rsi5", "gap", "fromOpen", "volumeRatio", "atrPct",
        "sma20_slope_pct", "dist_hod_atr", "sma50_dist_pct", "close", "atr_d", "adv20"]
SG = [(s, g) for s in ("short", "long") for g in ("t1s1", "t05s1", "t1s05")]
OUTC = [f"{k}_{s}_{g}" for s, g in SG for k in ("r", "win")]
MIN_ADV = 95e6

sup, ctx = [], []
for m in lib.months():
    t = time.time()
    d = lib.load_month(m, ["symbol", "date", "tod"] + FEAT + OUTC)
    d = d[(d.tod >= 950) & (d.tod <= 1500)]
    spy = d.loc[d.symbol == "SPY", ["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    e = d[(d.adv20 >= MIN_ADV) & (d.atr_d > 0)].copy()
    for s, g in SG:
        r = e[f"r_{s}_{g}"].to_numpy(float)
        ok = np.isfinite(r)
        pr = np.full(len(e), np.nan)
        pr[ok] = prod_r(r[ok], e[f"win_{s}_{g}"].to_numpy(float)[ok], e.close.to_numpy(float)[ok],
                        e.atr_d.to_numpy(float)[ok], g, tod=e.tod.to_numpy(float)[ok])
        e[f"p_{s}_{g}"] = pr.astype("float32")
    pc = [f"p_{s}_{g}" for s, g in SG]
    c = e.groupby(["date", "tod"]).agg(**{f"b_{k[2:]}": (k, "mean") for k in pc},
                                        breadth=("fromOpen", lambda x: float((x > 0).mean())),
                                        n_univ=("symbol", "size")).reset_index()
    c = c.merge(spy, on=["date", "tod"], how="left")
    ctx.append(c)
    s = e[(e.heat <= -20) & (e.buyPressure < -0.15)][["symbol", "date", "tod"] + FEAT + pc]
    sup.append(s)
    print(m, len(d), len(e), len(s), round(time.time() - t, 1), flush=True)
    del d, e
ctx = pd.concat(ctx, ignore_index=True)
sup = pd.concat(sup, ignore_index=True).merge(ctx, on=["date", "tod"], how="left")
sup = sup.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
sup.to_parquet(OUT / "superset.parquet")
ctx.to_parquet(OUT / "ctx.parquet")
print("done", len(sup), len(ctx))
