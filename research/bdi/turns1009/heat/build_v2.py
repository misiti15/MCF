"""As-run (V2) and formula (V1) heat for every lab symbol on the open two-year history, from data/cache_hist/1Min.
The rule-19 locked block (2024-11-01..2025-02-28) is DROPPED from the 1-minute bars before any computation.
Output: data/v2/month=YYYY-MM/part-KKK.parquet (symbol, ts = 5-min bar start ET, heat_v0 check, heat_v1, heat_v2,
candleHeat (V1), V2 components *_ar), 09:50-15:00 bar closes only. One process. Educational only - not financial advice."""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from heat_lib import COMPONENTS, all_heats  # noqa: E402

CACHE = ROOT / "data" / "cache_hist" / "1Min"
OUT = HERE / "data" / "v2"
LOCKED = (pd.Timestamp("2024-11-01", tz="America/New_York"), pd.Timestamp("2025-03-01", tz="America/New_York"))
KEEP = ["heat_v0", "heat_v1", "heat_v2", "candleHeat"] + [k + "_ar" for k in COMPONENTS + ["candleHeat"]]


def one(sym):
    d = pd.read_parquet(CACHE / f"{sym}.parquet")
    d = d[(d.index < LOCKED[0]) | (d.index >= LOCKED[1])]
    m = d.index.hour * 60 + d.index.minute
    d = d[(m >= 570) & (m < 960)]
    if len(d) < 2000:
        return None
    d5 = d.resample("5min").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    d5 = d5.dropna(subset=["close"])
    h = all_heats(d5)
    h = h[(h.tod >= 950) & (h.tod <= 1500) & (h.index >= pd.Timestamp("2024-10-01", tz="America/New_York"))]
    x = h[KEEP].astype("float16").reset_index(names="ts")
    x.insert(0, "symbol", sym)
    return x


if __name__ == "__main__":
    syms = sorted(p.stem for p in CACHE.glob("*.parquet"))
    OUT.mkdir(parents=True, exist_ok=True)
    t0, buf, k = time.time(), [], 0

    def flush():
        global k
        if not buf:
            return
        x = pd.concat(buf, ignore_index=True)
        mon = x.ts.dt.strftime("%Y-%m")
        for mm, g in x.groupby(mon):
            p = OUT / f"month={mm}"
            p.mkdir(exist_ok=True)
            g.to_parquet(p / f"part-{k:03d}.parquet", index=False, compression="zstd")
        k += 1
        buf.clear()

    for i, s in enumerate(syms):
        try:
            x = one(s)
        except Exception as e:  # noqa: BLE001
            print("fail", s, e, flush=True)
            continue
        if x is not None:
            buf.append(x)
        if len(buf) >= 60:
            flush()
        if i % 100 == 0:
            print(f"{i}/{len(syms)} {time.time() - t0:.0f}s", flush=True)
    flush()
    print("done", time.time() - t0)
