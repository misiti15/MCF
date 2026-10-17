"""Build compact AM rows (bar close 09:50 <= tod < 11:00, live indicators only) per open month into scratch.
Uses mcf.research.arena.data.build_month (production-cost R, same-minute random control over the FULL universe).
The locked block is never read (data.months excludes it). Educational only - not financial advice."""
import sys
import time
from pathlib import Path

import numpy as np

from mcf.research.arena import data as D
from mcf.research.arena.indicators import INDICATORS

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
LIVE = [n for n, i in INDICATORS.items() if i.live]
for m in D.months("all"):
    f = OUT / f"month={m}.parquet"
    if f.exists():
        continue
    t0 = time.time()
    x = D.build_month(m, names=LIVE, context=False)
    x = x[(x["tod"] >= 950) & (x["tod"] < 1100)].reset_index(drop=True)
    drop = [c for c in x.columns if c.startswith(("r_short", "c_short"))]
    x = x.drop(columns=drop)
    for c in x.columns:
        if x[c].dtype == np.float64:
            x[c] = x[c].astype(np.float32)
    x.to_parquet(f, index=False, compression="zstd")
    print(m, len(x), f"{time.time()-t0:.0f}s", flush=True)
