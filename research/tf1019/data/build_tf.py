"""Multi-timeframe lab frames (decision bars of 1, 3, 5, 10, 15 minutes) for a liquid subset, with the SAME pipeline as
research/history2y/build_frames.py: data/cache_hist 1-minute -> mcf.data.bars.resample(df, f"{m}min") ->
mcf.research.setup_lab.build. One correction so `tod` means the same thing on every timeframe: heat_frame labels a bar
with its START + 5 minutes (right for 5-minute bars only), so the bars are passed with their index shifted by (m - 5)
minutes and `tod` comes out as the true bar-close HHMM (the 15:55 time exit inside the outcomes then uses true bar
closes too); `ts` is restored to the bar start. For m = 5 the shift is zero: identical to the existing frames.
Indicator lookbacks are counted in BARS (RSI 14, SMA 20/50, buyPressure 19, ...), so on 1-minute bars they span
5x less clock time than on 5-minute bars - "the same setup on another timeframe", as LabStrategy would compute it.

Rule 19: rows in the locked block (2024-11-01..2025-02-28) are dropped before anything is written; months before
2024-10 are dropped. Output (git-ignored, like the other history2y data):
  research/history2y/data/frames_tf/<m>min/month=YYYY-MM/part-<chunk>.parquet     (zstd; only the columns in KEEP)
  research/history2y/data/frames_tf/daily_forward.parquet   per symbol-day table (as daily.parquet) for 2026-10-08..
  research/history2y/data/frames_tf/symbols.txt (3/5/10/15 min), symbols_core.txt (also 1 min), build_report.json
Disk (2026-10-19, ~5 GB free): ~17 MB per symbol for all five timeframes even with byte-stream-split zstd, so the
default is the top 160 symbols by median open-history dollar volume (SPY/QQQ/IWM always included) for 3/5/10/15 minutes and the
top 80 "core" for 1 minute; like-for-like comparisons across all five timeframes use the core.
Read through mcf.research.timeframes.load_tf (same locked guard as research/history2y/lib.py).

    python research/tf1019/data/build_tf.py [--n 160] [--n1 80] [--workers 4] [--chunk 10] [--minutes 5,15,10,3,1]
Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
from build_frames import daily_table  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.timeframes import build_tf_frame  # noqa: E402

CACHE = ROOT / "data" / "cache_hist"
OUT = ROOT / "research" / "history2y" / "data" / "frames_tf"
LOCKED = ("2024-11-01", "2025-02-28")
FIRST = "2024-10-01"
FORWARD_START = "2026-10-08"     # sessions after research/history2y/data/daily.parquet (forward / valid side only)
MIN_FREE_GB = 1.5
OUTCOMES = [f"{k}_{s}_{g}" for g in ("t1s1", "t05s1", "t1s05") for k in ("win", "r") for s in ("long", "short")]
KEEP = (["symbol", "date", "tod", "open", "high", "low", "close", "volume", "adv20", "atr_d",
         "rsi", "rsi5", "fromOpen", "vwapDistPct", "sma50_dist_pct", "sma20_dist_pct", "sma20_slope_pct", "buyPressure",
         "gap", "heat", "rsiHeat", "momentumHeat", "priceActionHeat", "vwapHeat", "dist_pdh_atr", "dist_pdl_atr",
         "dist_hod_atr", "dist_lod_atr", "volumeRatio", "emaDiff", "macdPct", "flow3", "vol_climax", "bear_div",
         "bull_div"] + OUTCOMES)
ETFS = ["SPY", "QQQ", "IWM"]


def free_gb() -> float:
    return shutil.disk_usage(str(ROOT)).free / 1e9


def frame_tf(df1: pd.DataFrame, m: int, adv: pd.DataFrame, sym: str) -> pd.DataFrame:
    x = build_tf_frame(df1, m, sym)        # resample -> setup_lab.build with the true bar-close tod (see that function)
    if x is None or not len(x):
        return pd.DataFrame()
    x = x.reset_index(names="ts")
    x = x.merge(adv, on="date", how="left")             # ts (bar start) is not stored: bar start = close(tod) - m min
    ds = x["date"].astype(str)
    x = x[(ds >= FIRST) & ~((ds >= LOCKED[0]) & (ds <= LOCKED[1]))]
    x = x[[c for c in KEEP if c in x.columns]].copy()
    for c in x.columns:
        if c not in ("symbol", "date", "tod") and x[c].dtype.kind in "fi":
            x[c] = x[c].astype("float32")
    x["tod"] = x["tod"].astype("int16")
    return x


def write(df: pd.DataFrame, path: Path) -> None:
    """Lossless, ~35% smaller than plain zstd: byte-stream-split for float columns (no dictionary), zstd 6."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    t = pa.Table.from_pandas(df, preserve_index=False)
    fl = [f.name for f in t.schema if pa.types.is_floating(f.type)]
    pq.write_table(t, path, compression="zstd", compression_level=6,
                   use_dictionary=[c for c in t.column_names if c not in fl], use_byte_stream_split=fl)


def one_chunk(args):
    k, syms, minutes, syms1 = args
    store = BarStore(CACHE)
    acc = {m: [] for m in minutes}
    for s in syms:
        df = store.load(s)
        if df.empty:
            continue
        adv = daily_table(df, s)[["date", "adv20"]]
        for m in minutes:
            if m == 1 and s not in syms1:
                continue                                       # 1-minute frames: core subset only (disk)
            x = frame_tf(df, m, adv, s)
            if len(x):
                acc[m].append(x)
    written = {}
    for m in minutes:                                         # larger timeframes first; 1-min last
        if not acc[m]:
            continue
        if free_gb() < MIN_FREE_GB:
            written[m] = "skipped_low_disk"
            continue
        x = pd.concat(acc[m], ignore_index=True)
        acc[m] = None
        month = pd.to_datetime(x["date"]).dt.strftime("%Y-%m")
        for mo, g in x.groupby(month):
            p = OUT / f"{m}min" / f"month={mo}"
            p.mkdir(parents=True, exist_ok=True)
            write(g.reset_index(drop=True), p / f"part-{k:03d}.parquet")
        written[m] = len(x)
    return k, written


def daily_forward_one(sym: str) -> pd.DataFrame:
    df = BarStore(CACHE).load(sym)
    if df.empty:
        return pd.DataFrame()
    d = daily_table(df.loc[df.index >= pd.Timestamp("2026-09-01", tz=df.index.tz)], sym)
    return d[d["date"].astype(str) >= FORWARD_START]


def pick_symbols(n: int) -> list[str]:
    """Top-n by median daily dollar volume over the OPEN history (research/history2y/data/daily.parquet), plus SPY/QQQ/IWM,
    restricted to symbols whose cache reaches 2026-10-16 (the extension)."""
    d = pd.read_parquet(ROOT / "research" / "history2y" / "data" / "daily.parquet", columns=["symbol", "date", "dollar_volume"])
    s = d["date"].astype(str)
    d = d[(s >= FIRST) & ~((s >= LOCKED[0]) & (s <= LOCKED[1]))]
    rep = json.loads((ROOT / "research" / "tf1019" / "data" / "extend_report.json").read_text())
    bad = set(rep["not_extended"])
    med = d.groupby("symbol")["dollar_volume"].median().sort_values(ascending=False)
    top = [x for x in med.index if x not in bad][:n]
    return sorted(set(top) | (set(ETFS) - bad))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=160, help="symbols for 3/5/10/15-minute frames (top ADV + SPY/QQQ/IWM)")
    ap.add_argument("--n1", type=int, default=80, help="core subset (top ADV + ETFs) that also gets 1-minute frames")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--chunk", type=int, default=10)
    ap.add_argument("--minutes", default="5,15,10,3,1")
    ap.add_argument("--symbols", default=None, help="file with symbols (default: pick_symbols(--n))")
    a = ap.parse_args()
    minutes = [int(x) for x in a.minutes.split(",")]
    syms = Path(a.symbols).read_text().split() if a.symbols else pick_symbols(a.n)
    syms1 = set(pick_symbols(a.n1)) & set(syms)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "symbols.txt").write_text("\n".join(syms) + "\n")
    (OUT / "symbols_core.txt").write_text("\n".join(sorted(syms1)) + "\n")
    print(f"{len(syms)} symbols, minutes {minutes}, free {free_gb():.2f} GB", flush=True)
    # per symbol-day open/close for the forward sessions of the WHOLE lab universe (regime classes for 10-08..; the
    # tercile cut points stay those of the open history in daily.parquet)
    with Pool(a.workers) as pool:
        fwd = pd.concat(pool.map(daily_forward_one, BarStore(CACHE).symbols()), ignore_index=True)
    fwd.to_parquet(OUT / "daily_forward.parquet", index=False)
    print(f"daily_forward: {len(fwd)} rows, {fwd['date'].nunique()} sessions", flush=True)
    jobs = [(i // a.chunk, syms[i:i + a.chunk], minutes, syms1) for i in range(0, len(syms), a.chunk)]
    t0, tot = time.time(), {m: 0 for m in minutes}
    skipped = []
    with Pool(a.workers, maxtasksperchild=4) as pool:
        for k, w in pool.imap_unordered(one_chunk, jobs):
            for m, v in w.items():
                if isinstance(v, int):
                    tot[m] += v
                else:
                    skipped.append((k, m))
            print(f"chunk {k} {w} ({time.time() - t0:.0f}s, free {free_gb():.2f} GB)", flush=True)
    rep = {"symbols": len(syms), "core_symbols_1min": len(syms1), "minutes": minutes, "rows": tot, "skipped_low_disk": skipped,
           "seconds": round(time.time() - t0), "free_gb_end": round(free_gb(), 2),
           "columns": KEEP, "locked_block_excluded": LOCKED, "first": FIRST}
    (OUT / "build_report.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps({k: rep[k] for k in ("rows", "skipped_low_disk", "seconds", "free_gb_end")}), flush=True)
