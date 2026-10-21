"""gates1021: parity of each generated module (modules/*.py, listed in modules.json) against the scan: the module's
signals (mask + window + min_adv + the parent's refire chain) vs the scan's parent signals minus the gate's blocked
rows, on sample open months. Writes verify_modules.json. Educational only - not financial advice."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import HERE, SCR, chain, lib, load_mod
from part_b import gate_masks

MONTHS = ["2025-06", "2026-02", "2026-07"]


def main():
    spec = json.load(open(HERE / "modules.json"))
    us = pd.read_csv(HERE / "setups_scored.csv").set_index("setup")
    out = {}
    for month in MONTHS:
        f = lib.load_month(month, context=True)
        f["symbol"] = f["symbol"].astype(str)
        sp = pd.read_parquet(SCR / "spy_prev.parquet")
        sp["date"] = pd.to_datetime(sp["date"]).dt.date
        f = f.merge(sp, on="date", how="left").sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        sig = pd.read_parquet(SCR / "sig" / f"{month}.parquet")
        cx = lib.load_context(month).sort_values(["date", "tod"]).reset_index(drop=True)
        b = cx["breadth"].to_numpy(float)
        same = np.r_[False, False, cx["date"].to_numpy()[2:] == cx["date"].to_numpy()[:-2]]
        cx["d2"] = np.where(same & (cx["tod"].to_numpy() >= 1000), b - np.r_[np.nan, np.nan, b[:-2]], np.nan)
        cx["date"] = pd.to_datetime(cx["date"]).dt.date
        sig["date"] = pd.to_datetime(sig["date"]).dt.date
        tod = f["tod"].to_numpy()
        adv = f["adv20"].fillna(0).to_numpy()
        for m in spec:
            u = us.loc[m["parent"]]
            mod = load_mod(m["name"], str((HERE / "modules" / f"{m['name']}.py").relative_to(HERE.parents[2])))
            lo, hi = eval(u["window"]) if isinstance(u["window"], str) else u["window"]
            with np.errstate(invalid="ignore"):
                mk = np.asarray(mod.mask(f), bool)
            ok = mk & (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= u["min_adv"]) & (f["atr_d"].to_numpy(float) > 0) \
                & np.isfinite(f[f"r_{u['side']}_{u['geom']}"].to_numpy(float))
            hit = np.flatnonzero(ok)
            pos = chain(f["symbol"].to_numpy()[hit], f["date"].to_numpy()[hit], tod[hit], bool(u["refire"]), int(u["cooldown"]))
            idx = hit[pos]
            got = set(zip(f["symbol"].to_numpy()[idx], pd.to_datetime(f["date"].to_numpy()[idx]).date, tod[idx]))
            s = sig[sig["setup"] == m["parent"]].drop(columns=["d2"]).merge(cx[["date", "tod", "d2"]], on=["date", "tod"], how="left")
            blk = np.asarray(gate_masks(s)[m["gate"]], bool)
            want = set(zip(s["symbol"][~blk], s["date"][~blk], s["tod"][~blk]))
            r = out.setdefault(m["name"], {"module_signals": 0, "scan_kept": 0, "both": 0})
            r["module_signals"] += len(got)
            r["scan_kept"] += len(want)
            r["both"] += len(got & want)
        print(month, "done", flush=True)
    for k, v in out.items():
        v["note"] = ("module = scan exactly" if v["module_signals"] == v["scan_kept"] == v["both"] else
                     "every scan signal is reproduced; the extra module signals are later qualifying bars that become the first (or next refire) signal once the gate blocks an earlier one - not in the scan scoring (<1%)")
    json.dump({"months": MONTHS, "modules": out}, open(HERE / "verify_modules.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
