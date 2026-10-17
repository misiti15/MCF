"""Build the L3 + ST1-ST8 superset from the OPEN 2-year frames (locked block never loaded: lib.load_month refuses it).
Rows: (adv20 >= 95M and any ST Stage-A point fires) or (gap <= -2 and sma20_slope_pct > 0.2, any adv: the loosest L3
core). Each row carries one bool column per ST Stage-A point, the features of the filter library, production-cost R for
both sides x 3 geoms, and per-(date, bar) context: SPY fromOpen, breadth (share of adv>=95M names above their open),
same-minute random baselines b95 (adv>=95M names) and b0 (all names). Educational only - not financial advice.
    python build.py <scratch_dir>"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from mcf.research.gates import prod_r  # noqa: E402
from research.history2y import lib  # noqa: E402
from stcore import ST, Frame, points  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
FEAT = ["close", "atr_d", "adv20", "vwapDistPct", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr", "dist_pdl_atr",
        "emaDiff", "rsi", "rsi5", "sma50_dist_pct", "sma20_slope_pct", "volumeRatio", "fromOpen", "gap", "buyPressure",
        "macdPct", "flow3", "atrPct", "heat"]
KEEP = ["vwapDistPct", "dist_hod_atr", "dist_lod_atr", "rsi", "rsi5", "sma20_slope_pct", "volumeRatio", "fromOpen", "gap",
        "buyPressure", "atrPct", "heat", "adv20", "close", "atr_d"]
SG = [(s, g) for s in ("short", "long") for g in ("t1s1", "t05s1", "t1s05")]
OUTC = [f"{k}_{s}_{g}" for s, g in SG for k in ("r", "win")]
MIN_ADV = 95e6
APTS = [(p, th) for p in ST for th in points(p)]
json.dump([[p, repr(th)] for p, th in APTS], open(OUT / "apoints.json", "w"))

sup, ctx = [], []
for m in lib.months():
    t = time.time()
    d = lib.load_month(m, ["symbol", "date", "tod"] + FEAT + OUTC)
    key = d.symbol.astype(str).to_numpy() + "|" + d.date.astype(str).to_numpy()
    new = np.r_[True, key[1:] != key[:-1]]
    del key
    cols = {c: d[c].to_numpy(float) for c in FEAT + ["tod"]}
    fr = Frame(cols, new)
    ok = cols["atr_d"] > 0
    big = ok & (cols["adv20"] >= MIN_ADV)
    P = {}
    for s, g in SG:
        r = d[f"r_{s}_{g}"].to_numpy(float)
        v = ok & np.isfinite(r)
        pr = np.full(len(d), np.nan, dtype=np.float32)
        pr[v] = prod_r(r[v], d[f"win_{s}_{g}"].to_numpy(float)[v], cols["close"][v], cols["atr_d"][v], g,
                       tod=cols["tod"][v])
        P[f"p_{s}_{g}"] = pr
    A = np.zeros((len(d), len(APTS)), dtype=bool)
    for j, (p, th) in enumerate(APTS):
        A[:, j] = fr.st(p, th) & big
    anyst = A.any(axis=1)
    with np.errstate(invalid="ignore"):
        l3 = ok & (cols["gap"] <= -2.0) & (cols["sma20_slope_pct"] > 0.2)
    keep = anyst | l3
    # context per (date, tod)
    base = pd.DataFrame({"date": d.date, "tod": d.tod, "big": big, "ok": ok, "up": cols["fromOpen"] > 0, **P})
    g0 = base[base.ok].groupby(["date", "tod"])
    c0 = g0[[f"p_{s}_{g}" for s, g in SG]].mean()
    c0.columns = [f"b0_{s}_{g}" for s, g in SG]
    g9 = base[base.big].groupby(["date", "tod"])
    c9 = g9[[f"p_{s}_{g}" for s, g in SG]].mean()
    c9.columns = [f"b95_{s}_{g}" for s, g in SG]
    c9["breadth"] = g9["up"].mean()
    c9["n_univ"] = g9.size()
    c = c0.join(c9, how="outer").reset_index()
    spy = d.loc[d.symbol == "SPY", ["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    c = c.merge(spy, on=["date", "tod"], how="left")
    ctx.append(c)
    del base
    s_ = d.loc[keep, ["symbol", "date", "tod"]].reset_index(drop=True)
    for k in KEEP:
        s_[k] = cols[k][keep].astype(np.float32)
    for k, v in P.items():
        s_[k] = v[keep]
    s_["big"] = big[keep]
    s_["l3"] = l3[keep]
    sup.append((s_, A[keep]))
    print(m, len(d), int(keep.sum()), int(anyst.sum()), int(l3.sum()), round(time.time() - t, 1), flush=True)
    del d, cols, fr, A, P
ctx = pd.concat(ctx, ignore_index=True)
S = pd.concat([x[0] for x in sup], ignore_index=True)
AM = np.concatenate([x[1] for x in sup])
S = S.merge(ctx, on=["date", "tod"], how="left", sort=False)
assert len(S) == len(AM)
S.to_parquet(OUT / "superset.parquet")
np.save(OUT / "apoints.npy", np.packbits(AM, axis=1))
ctx.to_parquet(OUT / "ctx.parquet")
print("done", len(S), AM.shape, AM.sum(axis=0).min(), AM.sum(axis=0).max())
