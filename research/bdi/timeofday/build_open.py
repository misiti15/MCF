"""One pass over the 1-minute SIP cache (data/cache_hist/1Min), locked block dropped at load, before any computation:

  data/open/part-*.parquet   lab-pipeline rows for bar closes 09:35..10:30 (heat_frame + extra_features + lab t1s1
                             outcomes, R = 0.25 x daily ATR, exit by 15:55) - the exploratory opening-window study
                             (NOTES.md 0.6). The lab frames proper start at 09:50; these keep 09:35 / 09:40 / 09:45.
  data/block/part-*.parquet  (symbol, date, tod) of 09:50-15:00 bars where RW6G1's VWAP +2 SD band guard blocks a
                             short, computed by the live module's own vwap_band_block on full-day 5-minute bars.

    python research/bdi/timeofday/build_open.py [--workers 4] [--chunk 40]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.heat import heat_frame  # noqa: E402
from mcf.research.setup_lab import _outcomes_asym, extra_features  # noqa: E402

CACHE = ROOT / "data" / "cache_hist"
LOCKED = ("2024-11-01", "2025-02-28")
FIRST = "2024-10-01"
DATA = HERE / "data"
KEEP = ["close", "high", "low", "atr_d", "gap", "fromOpen", "vwapDistPct", "rsi", "rsi5", "emaDiff", "volumeRatio",
        "buyPressure", "momentum"]

_spec = importlib.util.spec_from_file_location("rw6g1", ROOT / "research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py")
RW6G1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RW6G1)


def one(args):
    k, syms = args
    store = BarStore(CACHE)
    opens, blocks = [], []
    for s in syms:
        m1 = store.load(s)
        if m1.empty:
            continue
        d = m1.index.strftime("%Y-%m-%d")
        m1 = m1[(d < LOCKED[0]) | (d > LOCKED[1])]          # rule 19: locked rows never enter a computation
        d5 = resample(m1, "5min")
        if len(d5) < 300:
            continue
        # point-in-time adv20 (as research/history2y/build_frames.daily_table)
        dv = (m1["close"] * m1["volume"]).groupby(m1.index.date).sum()
        adv20 = dv.shift(1).rolling(20, min_periods=5).mean()
        f = heat_frame(d5)
        f = f.join(extra_features(d5, f))
        o = _outcomes_asym(f, 0.25, 0.01, 1.0, 1.0)
        for kk, arr in o.items():
            f[f"{kk}_t1s1"] = arr
        f["date"] = f.index.date
        f["symbol"] = s
        f["adv20"] = f["date"].map(adv20).astype("float32")
        sel = (f.tod >= 935) & (f.tod <= 1030) & f.atr_d.notna() & f.rsi.notna() & (f["date"].astype(str) >= FIRST)
        cols = ["symbol", "date", "tod"] + KEEP + ["adv20", "r_long_t1s1", "win_long_t1s1", "r_short_t1s1", "win_short_t1s1"]
        opens.append(f.loc[sel, cols].reset_index(drop=True))
        b5 = d5.copy()
        b5["symbol"], b5["date"] = s, b5.index.date
        blk = RW6G1.vwap_band_block(b5)
        tod = (b5.index + pd.Timedelta(minutes=5)).hour * 100 + (b5.index + pd.Timedelta(minutes=5)).minute
        sel = blk & (tod >= 950) & (tod <= 1500)
        blocks.append(pd.DataFrame({"symbol": s, "date": b5["date"].to_numpy()[sel], "tod": np.asarray(tod)[sel]}))
    if opens:
        x = pd.concat(opens, ignore_index=True)
        num = [c for c in x.select_dtypes("number").columns if c != "tod"]
        x = x.astype({c: "float32" for c in num})
        x["date"] = x["date"].astype(str)
        x.to_parquet(DATA / "open" / f"part-{k:03d}.parquet", index=False)
        b = pd.concat(blocks, ignore_index=True)
        b["date"] = b["date"].astype(str)
        b.to_parquet(DATA / "block" / f"part-{k:03d}.parquet", index=False)
    return k, sum(len(z) for z in opens)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--chunk", type=int, default=40)
    a = ap.parse_args()
    for sub in ("open", "block"):
        (DATA / sub).mkdir(parents=True, exist_ok=True)
    syms = BarStore(CACHE).symbols()
    jobs = [(i // a.chunk, syms[i:i + a.chunk]) for i in range(0, len(syms), a.chunk)]
    t0 = time.time()
    with Pool(a.workers) as pool:
        for k, n in pool.imap_unordered(one, jobs):
            print(f"chunk {k}: {n} rows ({time.time() - t0:.0f}s)", flush=True)
    print("done", flush=True)
