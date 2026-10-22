"""regime1022 step 1: live-shaped signals of every covered live lab setup (Primary, Testing 1, Testing 2, Graveyard)
on the open two-year frames, with production R (x3 extended tier), market state at entry and the 5-minute exit bar for
EVERY setup (gates1021 had exit bars for its two Part A setups only). Also saves SPY/QQQ bar rows (VWAP side).
Reuses gates1021/scripts/scan.py functions unchanged. Educational only - not financial advice.

    python research/bdi/regime1022/scripts/scan.py 3     # -> $G21SCR/sig/<month>.parquet, idx/<month>.parquet
"""
from __future__ import annotations

import shutil
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from rc import G21SCR, HERE, SCR, g21c, lib, no_locked
import scan as g21s  # gates1021/scripts/scan.py
from rsetups import live_setups


def unique_setups() -> pd.DataFrame:
    df = live_setups()
    df = df[df["covered"]].copy()
    df["key"] = df["module"] + "|" + df["window"].astype(str) + "|" + df["min_adv"].astype(str) + "|" + \
        df["refire"].astype(str) + "|" + df["cooldown"].astype(str) + "|" + df["geom"].astype(str)
    g = df.groupby("key", sort=False).agg(setup=("setup", "first"), accounts=("account", lambda x: ",".join(x)),
                                          names=("setup", lambda x: ",".join(sorted(set(x)))),
                                          module=("module", "first"), window=("window", "first"),
                                          min_adv=("min_adv", "first"), refire=("refire", "first"),
                                          cooldown=("cooldown", "first"), geom=("geom", "first"),
                                          side=("side", "first")).reset_index()
    g["skey"] = ["k%02d" % i for i in range(len(g))]
    return g


def month_job(args):
    month, sts = args
    t0 = time.time()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    spy_prev = pd.read_parquet(SCR / "spy_prev.parquet").set_index("date")["spy_prev"]
    f = f.merge(g21s.context_extra(month, spy_prev), on=["date", "tod"], how="left")
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    idx_rows = f[f["symbol"].isin(["SPY", "QQQ", "IWM"])][["symbol", "date", "tod", "close", "vwapDistPct", "fromOpen"]]
    idx_rows.to_parquet(SCR / "idx" / f"{month}.parquet")
    tod = f["tod"].to_numpy()
    adv = f["adv20"].fillna(0).to_numpy()
    atr_ok = f["atr_d"].to_numpy(float) > 0
    rows = []
    for s in sts:
        try:
            m = g21c.load_mod(s["setup"], s["module"])
            lo, hi = s["window"]
            with np.errstate(invalid="ignore", divide="ignore"):
                mk = np.asarray(m.mask(f), bool)
        except Exception as e:  # noqa: BLE001
            rows.append(pd.DataFrame({"skey": [s["skey"]], "error": [repr(e)[:200]]}))
            continue
        side, geom = s["side"], s["geom"]
        ok = mk & (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s["min_adv"]) & atr_ok \
            & np.isfinite(f[f"r_{side}_{geom}"].to_numpy(float))
        hit = np.flatnonzero(ok)
        if not len(hit):
            continue
        pos = g21c.chain(f["symbol"].to_numpy()[hit], f["date"].to_numpy()[hit], tod[hit], s["refire"], s["cooldown"])
        idx = hit[pos]
        out = pd.DataFrame({"skey": s["skey"], "symbol": f["symbol"].to_numpy()[idx], "date": f["date"].to_numpy()[idx],
                            "tod": tod[idx], "r": g21s.prod_r_tier(f, idx, side, geom),
                            "win": f[f"win_{side}_{geom}"].to_numpy(float)[idx]})
        for k in ("spy_fo", "qqq_fo", "breadth", "d2", "spy_prev", "fromOpen", "close", "gap", "adv20"):
            out[k] = f[k].to_numpy(float)[idx]
        et, kd = g21s.exit_bars(f, idx, side, geom)
        out["exit_tod"], out["exit_kind"] = et, kd
        rows.append(out)
    res = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    res.to_parquet(SCR / "sig" / f"{month}.parquet")
    return month, len(res), round(time.time() - t0, 1)


def main():
    for d in ("sig", "idx"):
        (SCR / d).mkdir(parents=True, exist_ok=True)
    shutil.copy(G21SCR / "spy_prev.parquet", SCR / "spy_prev.parquet")
    us = unique_setups()
    us.drop(columns="key").to_csv(HERE / "setups_scored.csv", index=False)
    sts = us.to_dict("records")
    months = lib.months()
    if len(sys.argv) > 2:
        months = sys.argv[2].split(",")
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    with Pool(workers) as p:
        for r in p.imap_unordered(month_job, [(m, sts) for m in months]):
            print(r, flush=True)


if __name__ == "__main__":
    main()
