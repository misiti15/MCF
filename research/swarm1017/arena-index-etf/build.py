"""Build compact ETF arena rows per open month into scratch (see PLAN.md).

Per month: full frame -> production R for all rows (arena.data.outcomes) -> controls c_* (mean over the full adv20 >=
$95M universe at the same date/minute) and e_* (same, ETF universe only) -> keep ETF rows -> live arena indicators
(compute(context=False) on the ETF rows; all are per symbol-day). Locked block never read (data.months excludes it,
lib.load_month refuses it). Educational only - not financial advice."""
import gc
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ETFS, LIVE  # noqa: E402

from mcf.research.arena import data as D  # noqa: E402
from mcf.research.arena.indicators import compute  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
for m in D.months("all"):
    f = OUT / f"month={m}.parquet"
    if f.exists():
        continue
    t0 = time.time()
    df = D._lib().load_month(m)
    tod = df["tod"].to_numpy()
    uni = (df["adv20"].to_numpy(float) >= 95e6) & (tod >= 950) & (tod <= 1500)
    isetf = df["symbol"].astype(str).isin(ETFS).to_numpy()
    out = D.outcomes(df)
    key = pd.MultiIndex.from_arrays([pd.Index(df["date"]), tod])
    keep = uni & isetf
    res = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[keep], "date": df["date"].to_numpy()[keep],
                        "tod": tod[keep].astype(np.int16)})
    for o, v in out.items():
        res[f"r_{o}"] = v[keep]
        for pre, sel in (("c", uni), ("e", keep)):
            ctl = pd.Series(np.where(sel, v, np.nan), index=key).groupby(level=[0, 1]).mean()
            res[f"{pre}_{o}"] = ctl.reindex(key[keep]).to_numpy(np.float32)
    sub = df[isetf].reset_index(drop=True)
    del df, out
    gc.collect()
    ind = compute(sub, names=LIVE, context=False)
    k2 = (sub["adv20"].to_numpy(float) >= 95e6) & (sub["tod"].to_numpy() >= 950) & (sub["tod"].to_numpy() <= 1500)
    ind = ind[k2].reset_index(drop=True)
    assert len(ind) == len(res) and (sub["symbol"].astype(str).to_numpy()[k2] == res["symbol"].to_numpy()).all()
    res = pd.concat([res, ind], axis=1)
    res.to_parquet(f, index=False, compression="zstd")
    print(m, len(res), res["symbol"].nunique(), f"{time.time()-t0:.0f}s", flush=True)
    del sub, ind, res
    gc.collect()
