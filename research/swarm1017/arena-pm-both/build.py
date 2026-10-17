"""Build compact PM rows (bar close tod >= 14:00, both sides, only the searched indicators) per open month into
scratch, via mcf.research.arena.data.build_month (production-cost R; same-minute random control over the FULL universe).
Locked block never read (data.months excludes it). Educational only - not financial advice."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import needed_names  # noqa: E402

from mcf.research.arena import data as D  # noqa: E402

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
NAMES = needed_names()
print(len(NAMES), NAMES, flush=True)
for m in D.months("all"):
    f = OUT / f"month={m}.parquet"
    if f.exists():
        continue
    t0 = time.time()
    x = D.build_month(m, names=NAMES, context=True)
    x = x[x["tod"] >= 1400].reset_index(drop=True)
    for c in x.columns:
        if x[c].dtype == np.float64:
            x[c] = x[c].astype(np.float32)
    x.to_parquet(f, index=False, compression="zstd")
    print(m, len(x), f"{time.time()-t0:.0f}s", flush=True)
