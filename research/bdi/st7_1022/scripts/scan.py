"""st7_1022 step 1: every ST7-family candidate bar (superset of P0 and of the C threshold rows) on the open two-year
frames with its entry features, the frames' lab outcomes, and 3 same-minute random partners (adv20 >= 95M, other
symbols). Educational only - not financial advice.

    python research/bdi/st7_1022/scripts/scan.py 4      # -> $W/cand/<month>.parquet, $W/part/<month>.parquet
"""
from __future__ import annotations

import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from sc import W, lib, no_locked

FEATS = ["close", "atr_d", "gap", "fromOpen", "rsi", "rsi5", "buyPressure", "vwapDistPct", "volumeRatio", "emaDiff",
         "sma20_slope_pct", "sma50_dist_pct", "adv20", "spy_fo", "qqq_fo", "breadth", "breadth_open",
         "r_long_t1s1", "win_long_t1s1", "r_long_t05s1", "win_long_t05s1", "r_long_t1s05", "win_long_t1s05"]
PFEATS = ["close", "atr_d", "gap", "r_long_t1s1", "win_long_t1s1", "r_long_t05s1", "win_long_t05s1", "r_long_t1s05",
          "win_long_t1s05"]


def month_job(month):
    t0 = time.time()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    c = lib.load_context(month).sort_values(["date", "tod"]).reset_index(drop=True)
    b = c["breadth"].to_numpy(float)
    same = np.r_[False, False, c["date"].to_numpy()[2:] == c["date"].to_numpy()[:-2]]
    c["d2"] = np.where(same & (c["tod"].to_numpy() >= 1000), b - np.r_[np.nan, np.nan, b[:-2]], np.nan)
    f = f.merge(c[["date", "tod", "d2"]], on=["date", "tod"], how="left")
    ix = f[f["symbol"].isin(["SPY", "QQQ"])].pivot_table(index=["date", "tod"], columns="symbol", values="vwapDistPct")
    ix.columns = [f"{x.lower()}_vwap" for x in ix.columns]
    f = f.merge(ix.reset_index(), on=["date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    sym = f["symbol"].to_numpy()
    dat = f["date"].astype(str).to_numpy()
    key = np.char.add(np.char.add(sym.astype(str), "|"), dat.astype(str))
    newk = np.r_[True, key[1:] != key[:-1]]
    tod = f["tod"].to_numpy()
    rsi = f["rsi"].to_numpy(dtype=float)
    prsi = np.r_[np.nan, rsi[:-1]]
    prsi[newk] = np.nan
    fo = f["fromOpen"].to_numpy(dtype=float)
    bp = f["buyPressure"].to_numpy(dtype=float)
    adv = f["adv20"].fillna(0).to_numpy()
    atr = f["atr_d"].to_numpy(float)
    fin = np.isfinite(f["r_long_t1s1"].to_numpy(float))
    base = (adv >= 95e6) & (atr > 0) & fin & (tod >= 950) & (tod <= 1500)
    with np.errstate(invalid="ignore"):
        cand = base & (prsi >= 45) & (rsi < 45) & (rsi <= 36) & (fo < -0.8) & (bp > 0)
    idx = np.flatnonzero(cand)
    out = pd.DataFrame({"symbol": sym[idx], "date": dat[idx], "tod": tod[idx].astype(int), "prsi": prsi[idx],
                        "d2": f["d2"].to_numpy(float)[idx],
                        "spy_vwap": f["spy_vwap"].to_numpy(float)[idx] if "spy_vwap" in f else np.nan,
                        "qqq_vwap": f["qqq_vwap"].to_numpy(float)[idx] if "qqq_vwap" in f else np.nan})
    for k in FEATS:
        out[k] = f[k].to_numpy(float)[idx]
    # signals in the same bar (P0 definition) - crowding
    # random same-minute partners
    rng = np.random.default_rng(int(month.replace("-", "")) + 7)
    bi = np.flatnonzero(base)
    bk = pd.Series(bi).groupby(dat[bi] + "|" + tod[bi].astype(str)).apply(np.asarray).to_dict()
    prow = []
    for j, i in enumerate(idx):
        g = bk.get(dat[i] + "|" + str(tod[i]))
        if g is None:
            continue
        g = g[sym[g] != sym[i]]
        if not len(g):
            continue
        for p in rng.choice(g, size=min(3, len(g)), replace=False):
            prow.append((j, p))
    pr = pd.DataFrame(prow, columns=["cj", "pi"])
    part = pd.DataFrame({"cid": [f"{month}:{j}" for j in pr["cj"]], "symbol": sym[pr["pi"]], "date": dat[pr["pi"]],
                         "tod": tod[pr["pi"]].astype(int)})
    for k in PFEATS:
        part[k] = f[k].to_numpy(float)[pr["pi"].to_numpy()]
    out["cid"] = [f"{month}:{j}" for j in range(len(out))]
    out.to_parquet(W / "cand" / f"{month}.parquet")
    part.to_parquet(W / "part" / f"{month}.parquet")
    return month, len(out), len(part), round(time.time() - t0, 1)


def main():
    for d in ("cand", "part"):
        (W / d).mkdir(parents=True, exist_ok=True)
    months = lib.months()
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    with Pool(workers) as p:
        for r in p.imap_unordered(month_job, months):
            print(r, flush=True)


if __name__ == "__main__":
    main()
