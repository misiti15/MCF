"""night1102/regime step 5: live-shaped signals of every covered live lab setup (58, current docs/live/assignments.json,
first account's config when a name runs in two) on the OPEN two-year frames (locked block 2024-11..2025-02 never
read; frames refuse it), with production R (x3 extended tier, time-of-day entry cost) via gates1021 scan.prod_r_tier.
Refire chain as configured; NO per-symbol lot cap, no slots (simplification, stated in NOTES). Sessions after
2026-10-05 dropped so the 2-year set does not overlap the live window. One process, one month at a time.
Educational only - not financial advice.

    G21SCR=<scratch>/g21 python scan2y.py <scratch>
"""
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "regime1022" / "scripts"))
from rc import g21c, lib, no_locked  # noqa: E402
import scan as g21s  # noqa: E402  gates1021/scripts/scan.py

SCR = Path(sys.argv[1])
(SCR / "sig2y").mkdir(exist_ok=True)
U = pd.read_csv(SCR / "setups_now.csv")
U = U[U.covered].drop_duplicates("setup").reset_index(drop=True)
U["window"] = U["window"].map(lambda s: tuple(int(x) for x in s.strip("()").split(",")))
mods = {r.setup: g21c.load_mod(r.setup, r.module) for r in U.itertuples()}
for month in lib.months():
    out = SCR / "sig2y" / f"{month}.parquet"
    if out.exists():
        continue
    t0 = time.time()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    f = f[f["date"] <= pd.Timestamp("2026-10-05").date()]
    no_locked(f["date"].unique())
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    tod = f["tod"].to_numpy()
    adv = f["adv20"].fillna(0).to_numpy()
    atr_ok = f["atr_d"].to_numpy(float) > 0
    rows = []
    for s in U.itertuples():
        try:
            with np.errstate(invalid="ignore", divide="ignore"):
                mk = np.asarray(mods[s.setup].mask(f), bool)
        except Exception as e:  # noqa: BLE001
            print("ERR", s.setup, repr(e)[:150], flush=True)
            continue
        lo, hi = s.window
        ok = mk & (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s.min_adv) & atr_ok \
            & np.isfinite(f[f"r_{s.side}_{s.geom}"].to_numpy(float))
        hit = np.flatnonzero(ok)
        if not len(hit):
            continue
        pos = g21c.chain(f["symbol"].to_numpy()[hit], f["date"].to_numpy()[hit], tod[hit], bool(s.refire), int(s.cooldown))
        idx = hit[pos]
        rows.append(pd.DataFrame({"setup": s.setup, "side": 1 if s.side == "long" else -1,
                                  "symbol": f["symbol"].to_numpy()[idx], "date": f["date"].to_numpy()[idx],
                                  "tod": tod[idx], "R": g21s.prod_r_tier(f, idx, s.side, s.geom)}))
    res = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    res.to_parquet(out)
    print(month, len(res), round(time.time() - t0, 1), flush=True)
    del f
