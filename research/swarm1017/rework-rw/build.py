"""Build the RW-family superset from the OPEN 2-year frames (PLAN.md). Rows: adv20 >= 95M, bar close 09:50-15:00, and
any loose family mask (MF-type heat<=-10 & bp<-0.15 | exhaustion RSI5>80 & sma20>0.5 | VWAP cross-up & fo<-1 |
SMA50 cross-up & fo>2). Adds production-cost R (6 side-geoms), prev-bar crosses (within symbol-day), and per
(date, bar) context: same-minute random baseline, breadth, SPY/QQQ fromOpen, SPY gap.
Locked block never loaded (lib.load_month refuses it). Educational only - not financial advice."""
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
        "sma20_slope_pct", "dist_hod_atr", "dist_lod_atr", "sma50_dist_pct", "sma20_dist_pct", "bear_div",
        "close", "atr_d", "adv20"]
SG = [(s, g) for s in ("short", "long") for g in ("t1s1", "t05s1", "t1s05")]
OUTC = [f"{k}_{s}_{g}" for s, g in SG for k in ("r", "win")]
MIN_ADV = 95e6

sup, ctx = [], []
for m in lib.months():
    t = time.time()
    d = lib.load_month(m, ["symbol", "date", "tod"] + FEAT + OUTC)
    key = d.symbol.astype(str).to_numpy() + "|" + d.date.astype(str).to_numpy()
    first = np.r_[True, key[1:] != key[:-1]]
    for c in ("vwapDistPct", "sma50_dist_pct"):
        p = np.r_[np.nan, d[c].to_numpy(float)[:-1]]
        p[first] = np.nan
        d["p_" + c] = p.astype("float32")
    d = d[(d.tod >= 950) & (d.tod <= 1500)]
    idx = {}
    for sym in ("SPY", "QQQ"):
        x = d.loc[d.symbol == sym, ["date", "tod", "fromOpen", "gap"]]
        idx[sym] = x.rename(columns={"fromOpen": f"{sym.lower()}_fo", "gap": f"{sym.lower()}_gap"})
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
    e["_up"] = (e.fromOpen > 0).astype("float32")
    c = e.groupby(["date", "tod"]).agg(**{f"b_{k[2:]}": (k, "mean") for k in pc}, breadth=("_up", "mean"),
                                        n_univ=("symbol", "size")).reset_index()
    c = c.merge(idx["SPY"], on=["date", "tod"], how="left").merge(idx["QQQ"][["date", "tod", "qqq_fo"]], on=["date", "tod"], how="left")
    ctx.append(c)
    with np.errstate(invalid="ignore"):
        L_MF = (e.heat <= -10) & (e.buyPressure < -0.15)
        L_EX = (e.rsi5 > 80) & (e.sma20_dist_pct > 0.5)
        L_R4 = (e.vwapDistPct > 0) & (e.p_vwapDistPct <= 0) & (e.fromOpen < -1)
        L_R6 = (e.sma50_dist_pct > 0) & (e.p_sma50_dist_pct <= 0) & (e.fromOpen > 2)
    keep = L_MF | L_EX | L_R4 | L_R6
    s = e.loc[keep, ["symbol", "date", "tod"] + FEAT + ["p_vwapDistPct", "p_sma50_dist_pct"] + pc].copy()
    s["fam"] = (L_MF[keep].to_numpy() * 1 + L_EX[keep].to_numpy() * 2 + L_R4[keep].to_numpy() * 4
                + L_R6[keep].to_numpy() * 8).astype("int8")
    for k in FEAT:
        if s[k].dtype == "float64":
            s[k] = s[k].astype("float32")
    sup.append(s)
    print(m, len(e), len(s), round(time.time() - t, 1), flush=True)
    del e
ctx = pd.concat(ctx, ignore_index=True)
sup = pd.concat(sup, ignore_index=True).merge(ctx, on=["date", "tod"], how="left")
sup = sup.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
sup.to_parquet(OUT / "superset.parquet")
ctx.to_parquet(OUT / "ctx.parquet")
print("done", len(sup), len(ctx), sup.fam.value_counts().to_dict())
