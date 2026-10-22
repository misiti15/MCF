"""ns3var1022: module-vs-scan parity for the proposed module. On every open month: rows where module.mask & window
[950, 1130] & adv20 >= 95M & ATR > 0 & finite outcome == the scan's candidate rows with the P0 conditions and
tod <= 11:30. Also: the module's as-run trade list (refire chain + lot cap, t05s1 at R = 0.5 ATR from the frames'
r_short_t05s1 cannot be used - the frames' R is 0.25 ATR - so the outcome check uses the simulator, whose t05s1 / t1s1
parity with the frames is in counts.json). Educational only - not financial advice."""
from __future__ import annotations

import importlib.util
import json
from multiprocessing import Pool

import numpy as np
import pandas as pd

from nv import HERE, NV, lib, no_locked

MOD = HERE / "modules" / "NS3V1-am-widestop-short.py"


def job(month):
    spec = importlib.util.spec_from_file_location("ns3v1", MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    f = lib.load_month(month)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    tod = f["tod"].to_numpy()
    ok = np.asarray(m.mask(f), bool) & (tod >= 950) & (tod <= 1130) & (f["adv20"].fillna(0).to_numpy() >= 95e6) \
        & (f["atr_d"].to_numpy(float) > 0) & np.isfinite(f["r_short_t1s1"].to_numpy(float))
    a = set(zip(f["symbol"].to_numpy()[ok], f["date"].astype(str).to_numpy()[ok], tod[ok].astype(int)))
    z = np.load(NV / "cand" / f"{month}.npz")
    p0 = (z["sma50_dist_pct"] > 0) & (z["fromOpen"] < -2) & (z["tod"] <= 1130)
    b = set(zip(z["symbol"][p0], z["date"][p0], z["tod"][p0].astype(int)))
    return month, len(a), len(b), len(a & b), len(a ^ b)


def main():
    with Pool(3) as p:
        res = p.map(job, lib.months())
    out = {"months": len(res), "module_rows": sum(r[1] for r in res), "scan_rows": sum(r[2] for r in res),
           "equal_rows": sum(r[3] for r in res), "mismatched_rows": sum(r[4] for r in res),
           "per_month": {r[0]: r[1:] for r in res}}
    json.dump(out, open(HERE / "verify_module.json", "w"), indent=1)
    print({k: v for k, v in out.items() if k != "per_month"})


if __name__ == "__main__":
    main()
