"""Download ~2 years of SIP 1-minute bars for the lab universe into data/cache_hist/1Min/<SYM>.parquet.

Same format as data/cache (mcf.data.store.BarStore: tz America/New_York index = bar start, open/high/low/close/volume,
regular trading hours only, split-adjusted). Raw HTTP instead of alpaca-py (the SDK's per-bar objects are ~10x slower).
Resumable: a symbol whose parquet exists is skipped; failures are listed in data/cache_hist/failed.txt and retried on
the next run. Stops by STOP_UTC so the live 08:35 ET job keeps its rate budget. Backs off on HTTP 429.

    python research/history2y/download.py [--start 2024-09-16] [--end 2026-10-08] [--workers 6]
Educational only - not financial advice. Keys come from ALPACA_API_KEY / ALPACA_SECRET_KEY (never logged).
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import normalize, rth  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402

URL = "https://data.alpaca.markets/v2/stocks/bars"
STOP_UTC = datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
OUT = ROOT / "data" / "cache_hist"
ARGS: dict = {}


def _get(sess, params):
    wait = 1.0
    for attempt in range(8):
        try:
            r = sess.get(URL, params=params, timeout=60)
        except requests.RequestException:
            time.sleep(wait); wait = min(wait * 2, 60); continue
        if r.status_code == 429 or r.status_code >= 500:
            reset = r.headers.get("X-Ratelimit-Reset")
            time.sleep(max(wait, (int(reset) - time.time()) if reset and reset.isdigit() else 0) if r.status_code == 429 else wait)
            wait = min(wait * 2, 60)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"gave up after retries (last status {getattr(r, 'status_code', 'n/a')})")


def fetch(sym: str):
    store = BarStore(OUT)
    p = store.path(sym)
    if p.exists():
        return sym, "skip", 0
    if datetime.now(timezone.utc) >= STOP_UTC:
        return sym, "stopped", 0
    sess = requests.Session()
    sess.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    params = {"symbols": sym, "timeframe": "1Min", "start": ARGS["start"], "end": ARGS["end"], "feed": "sip",
              "adjustment": "split", "limit": 10000}
    ts, o, h, l, c, v = [], [], [], [], [], []
    try:
        while True:
            j = _get(sess, params)
            bars = (j.get("bars") or {}).get(sym, [])
            ts += [b["t"] for b in bars]; o += [b["o"] for b in bars]; h += [b["h"] for b in bars]
            l += [b["l"] for b in bars]; c += [b["c"] for b in bars]; v += [b["v"] for b in bars]
            tok = j.get("next_page_token")
            if not tok:
                break
            params["page_token"] = tok
    except Exception as e:  # noqa: BLE001
        return sym, f"failed: {type(e).__name__}: {str(e)[:120]}", 0
    if not ts:
        return sym, "empty", 0
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v},
                      index=pd.DatetimeIndex(pd.to_datetime(ts, utc=True)))
    df = rth(normalize(df))
    tmp = p.with_suffix(".tmp")
    df.to_parquet(tmp)
    tmp.replace(p)
    return sym, "ok", len(df)


def _init(a):
    ARGS.update(a)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2024-09-16")
    ap.add_argument("--end", default="2026-10-08")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--symbols", default=str(ROOT / "research" / "lab_symbols.txt"))
    a = ap.parse_args()
    syms = Path(a.symbols).read_text().split()
    OUT.mkdir(parents=True, exist_ok=True)
    t0, done, failed = time.time(), 0, []
    args = {"start": f"{a.start}T00:00:00Z", "end": f"{a.end}T00:00:00Z"}
    with Pool(a.workers, initializer=_init, initargs=(args,)) as pool:
        for sym, status, n in pool.imap_unordered(fetch, syms):
            done += 1
            if status.startswith("failed") or status in ("empty", "stopped"):
                failed.append(f"{sym}\t{status}")
            if done % 25 == 0 or status.startswith("failed"):
                print(f"{done}/{len(syms)} {sym} {status} {n} bars ({time.time() - t0:.0f}s)", flush=True)
    (OUT / "failed.txt").write_text("\n".join(failed) + ("\n" if failed else ""))
    print(f"finished {done} symbols, {len(failed)} not ok, {time.time() - t0:.0f}s", flush=True)
