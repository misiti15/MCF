"""Lab frames for the 2-year history, with the SAME pipeline as research/setups2 (the setups2 build: data/cache 1-minute
-> resample 5min -> mcf.research.setup_lab.build). Adds two point-in-time columns the old frames did not need:
  adv20   mean RTH dollar volume of the prior 20 sessions (min 5), from the 1-minute cache (as live min_adv tiers)
  (the daily table research/history2y/data/daily.parquet holds per symbol-day open/close/volume for the regime gate)

Output (git-ignored), partitioned by month:
  research/history2y/data/frames/month=YYYY-MM/part-<chunk>.parquet     open history
  research/history2y/data/locked/month=YYYY-MM/part-<chunk>.parquet     the rule-19 locked block (2024-11..2025-02)
Read them only through research/history2y/lib.py (refuses the locked block without MCF_HIST_ALLOW_LOCKED=1).

    python research/history2y/build_frames.py [--workers 4] [--chunk 40]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.setup_lab import build  # noqa: E402

CACHE = ROOT / "data" / "cache_hist"
DATA = ROOT / "research" / "history2y" / "data"
LOCKED = ("2024-11-01", "2025-02-28")          # RESEARCH_RULES rule 19 (seed 20261008)
FIRST = "2024-10-01"


def daily_table(df: pd.DataFrame, sym: str) -> pd.DataFrame:
    g = df.groupby(df.index.date)
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "volume": g["volume"].sum(), "dollar_volume": (df["close"] * df["volume"]).groupby(df.index.date).sum()})
    d["adv20"] = d["dollar_volume"].shift(1).rolling(20, min_periods=5).mean()
    d.index.name = "date"
    d = d.reset_index()
    d.insert(0, "symbol", sym)
    return d


def one_chunk(args):
    k, syms = args
    store = BarStore(CACHE)
    frames, dailies = [], []
    for s in syms:
        df = store.load(s)
        if df.empty:
            continue
        dd = daily_table(df, s)
        dailies.append(dd)
        x = build({s: resample(df, "5min")}, log=lambda *_: None)
        if x is None or not len(x):
            continue
        x = x.reset_index(names="ts")
        x = x.merge(dd[["date", "adv20"]], on="date", how="left")
        x["adv20"] = x["adv20"].astype("float32")
        frames.append(x)
    if not frames:
        return k, 0
    x = pd.concat(frames, ignore_index=True)
    x = x[x["date"].astype(str) >= FIRST]
    month = pd.to_datetime(x["date"]).dt.strftime("%Y-%m")
    ds = x["date"].astype(str)
    locked = (ds >= LOCKED[0]) & (ds <= LOCKED[1])
    for m, g in x.groupby(month):
        lk = locked.loc[g.index]
        for sub, root in ((g[~lk], "frames"), (g[lk], "locked")):
            if len(sub):
                p = DATA / root / f"month={m}"
                p.mkdir(parents=True, exist_ok=True)
                sub.to_parquet(p / f"part-{k:03d}.parquet", index=False, compression="zstd")
    pd.concat(dailies).to_parquet(DATA / "daily_parts" / f"part-{k:03d}.parquet", index=False)
    return k, len(x)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--chunk", type=int, default=40)
    a = ap.parse_args()
    syms = BarStore(CACHE).symbols()
    (DATA / "daily_parts").mkdir(parents=True, exist_ok=True)
    jobs = [(i // a.chunk, syms[i:i + a.chunk]) for i in range(0, len(syms), a.chunk)]
    t0, rows = time.time(), 0
    with Pool(a.workers) as pool:
        for k, n in pool.imap_unordered(one_chunk, jobs):
            rows += n
            print(f"chunk {k} done: {n} rows (total {rows}, {time.time() - t0:.0f}s)", flush=True)
    d = pd.concat([pd.read_parquet(p) for p in sorted((DATA / "daily_parts").glob("*.parquet"))])
    d.to_parquet(DATA / "daily.parquet", index=False)
    print(f"frames built: {rows} rows, {len(syms)} symbols, {time.time() - t0:.0f}s", flush=True)
