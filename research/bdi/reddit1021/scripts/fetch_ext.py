"""reddit1021: read-only fetch of EXTENDED-HOURS SIP bars (04:00-20:00 ET) from Alpaca Market Data.

The 2-year cache (data/cache_hist/1Min) is regular-hours only, so the premarket ("London" proxy) and after-hours
("Asia" proxy) levels need a separate fetch. Market-data GET only (https://data.alpaca.markets/v2/stocks/bars), the
same raw-HTTP approach as research/history2y/download.py. Keys come from ALPACA_API_KEY / ALPACA_SECRET_KEY in the
environment and are never written or printed. No order or account endpoint is touched.

The rule-19 locked block (2024-11-01..2025-02-28) is never requested: two date ranges are fetched,
2024-09-09..2024-10-31 and 2025-03-01..END, and every saved row is asserted to be outside the block.

    python fetch_ext.py --timeframe 1Min --symbols SPY,QQQ
    python fetch_ext.py --timeframe 30Min --symbols-file <file> --workers 4
Output: <scratch>/ext_<timeframe>/<SYM>.parquet (tz America/New_York index = bar start, open/high/low/close/volume).
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SCR, assert_open  # noqa: E402

URL = "https://data.alpaca.markets/v2/stocks/bars"
RANGES = [("2024-09-09T00:00:00Z", "2024-11-01T04:00:00Z"), ("2025-03-01T05:00:00Z", None)]
A: dict = {}


def _get(sess, params):
    wait = 1.0
    r = None
    for _ in range(8):
        try:
            r = sess.get(URL, params=params, timeout=60)
        except requests.RequestException:
            time.sleep(wait); wait = min(wait * 2, 60); continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(wait); wait = min(wait * 2, 60); continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"gave up (status {getattr(r, 'status_code', 'n/a')})")


def fetch(sym: str):
    out = Path(A["out"]) / f"{sym}.parquet"
    if out.exists():
        return sym, "skip", 0
    sess = requests.Session()
    sess.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    rows = []
    try:
        for start, end in RANGES:
            params = {"symbols": sym, "timeframe": A["tf"], "start": start, "end": end or A["end"], "feed": "sip",
                      "adjustment": "split", "limit": 10000}
            while True:
                j = _get(sess, params)
                rows += (j.get("bars") or {}).get(sym, [])
                tok = j.get("next_page_token")
                if not tok:
                    break
                params["page_token"] = tok
    except Exception as e:  # noqa: BLE001
        return sym, f"failed: {type(e).__name__}", 0
    if not rows:
        return sym, "empty", 0
    df = pd.DataFrame({k: [b[s] for b in rows] for k, s in
                       (("open", "o"), ("high", "h"), ("low", "l"), ("close", "c"), ("volume", "v"))},
                      index=pd.DatetimeIndex(pd.to_datetime([b["t"] for b in rows], utc=True)).tz_convert("America/New_York"))
    df = df[~df.index.duplicated()].sort_index()
    hm = df.index.hour * 100 + df.index.minute
    df = df[(hm >= 400) & (hm < 2000)]
    assert_open(df.index.date)
    tmp = out.with_suffix(".tmp")
    df.to_parquet(tmp)
    tmp.replace(out)
    return sym, "ok", len(df)


def fetch_batch(syms: list[str]):
    """Several symbols per request (bars come back grouped by symbol); for the 30-minute stock fetch."""
    outdir = Path(A["out"])
    todo = [s for s in syms if not (outdir / f"{s}.parquet").exists()]
    if not todo:
        return ",".join(syms[:1]), "skip", 0
    sess = requests.Session()
    sess.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    got: dict[str, list] = {s: [] for s in todo}
    try:
        for start, end in RANGES:
            params = {"symbols": ",".join(todo), "timeframe": A["tf"], "start": start, "end": end or A["end"],
                      "feed": "sip", "adjustment": "split", "limit": 10000}
            while True:
                j = _get(sess, params)
                for s, b in (j.get("bars") or {}).items():
                    got.setdefault(s, []).extend(b)
                tok = j.get("next_page_token")
                if not tok:
                    break
                params["page_token"] = tok
    except Exception as e:  # noqa: BLE001
        return todo[0], f"failed: {type(e).__name__}", 0
    n = 0
    for s, rows in got.items():
        if not rows:
            continue
        df = pd.DataFrame({k: [b[c] for b in rows] for k, c in
                           (("open", "o"), ("high", "h"), ("low", "l"), ("close", "c"), ("volume", "v"))},
                          index=pd.DatetimeIndex(pd.to_datetime([b["t"] for b in rows], utc=True)).tz_convert("America/New_York"))
        df = df[~df.index.duplicated()].sort_index()
        hm = df.index.hour * 100 + df.index.minute
        df = df[(hm >= 400) & (hm < 2000)]
        assert_open(df.index.date)
        df.to_parquet(outdir / f"{s}.parquet")
        n += 1
    return todo[0], "ok", n


def _init(a):
    A.update(a)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeframe", default="1Min")
    ap.add_argument("--symbols", default="")
    ap.add_argument("--symbols-file", default="")
    ap.add_argument("--end", default="2026-10-21T04:00:00Z")   # through the 2026-10-20 session
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--batch", type=int, default=1)
    a = ap.parse_args()
    syms = [s for s in a.symbols.split(",") if s] or Path(a.symbols_file).read_text().split()
    out = SCR / f"ext_{a.timeframe}"
    out.mkdir(parents=True, exist_ok=True)
    t0, bad = time.time(), []
    with Pool(a.workers, initializer=_init, initargs=({"out": str(out), "tf": a.timeframe, "end": a.end},)) as pool:
        jobs = syms if a.batch <= 1 else [syms[i:i + a.batch] for i in range(0, len(syms), a.batch)]
        for i, (s, st, n) in enumerate(pool.imap_unordered(fetch if a.batch <= 1 else fetch_batch, jobs), 1):
            if st not in ("ok", "skip"):
                bad.append(f"{s}\t{st}")
            if i % 5 == 0 or len(jobs) < 10:
                print(f"{i}/{len(jobs)} {s} {st} {n} ({time.time() - t0:.0f}s)", flush=True)
    (out / "failed.txt").write_text("\n".join(bad) + "\n")
    print(f"done {len(syms)} symbols, {len(bad)} not ok, {time.time() - t0:.0f}s", flush=True)
