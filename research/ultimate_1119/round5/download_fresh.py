"""Round-5 FRESH window: SIP 1-minute bars 2022-10-03 (warm-up) .. 2024-09-13 into /home/user/MCF/data/cache_fresh.

Copy of research/history2y/download.py with only paths / dates / guards changed (FRESH_PLAN.md sec. 2.1, 4, 7):
  * same request + format: feed=sip, adjustment=split, RTH only, mcf.data.store.BarStore layout
    (tz America/New_York index = bar start, open/high/low/close/volume float);
  * hard range guard: start >= 2022-10-03, end <= 2024-09-14T00:00Z, so the LOCKED block 2024-11-01..2025-02-28 and the
    2-year cache are never requested;
  * PRE-REGISTRATION GUARD: refuses to fetch any fresh byte unless round5/FREEZE_HUNT.json exists and FRESH_PLAN.md still
    matches FRESH_PLAN.sha256 (FRESH_PLAN sec. 4.7: the FREEZE_HUNT timestamp must be earlier than the first fresh
    file's mtime; sec. 2.6: parity check before the first fresh byte);
  * rate budget: <= 4 workers, 429/5xx backoff, stops at --stop-utc (default 2026-11-19 13:15Z = 08:15 ET) so the live
    job keeps the Alpaca data quota; resumable (existing parquet skipped), not-done symbols in cache_fresh/missing.txt;
  * disk guard: stops when free space < 1.0 GB;
  * --retained-only writes only round5/symbols_retained.txt names (the 1,201-name list does not fit on disk: ~3.5 MB/sym);
    the other names are meant to be streamed by fresh_bt.py via fetch_bars() (in memory, never written);
  * every fetched symbol (written or not) also gets its daily row table in cache_fresh/daily/<SYM>.parquet
    (open/high/low/close/volume/dollar_volume/adv20, adv20 = prior 20 sessions' RTH $ volume, min 5 - same as
    research/history2y/build_frames.daily_table). Point in time; no returns are computed or read here.

    python research/ultimate_1119/round5/download_fresh.py [--retained-only] [--workers 4] [--stop-utc 2026-11-19T13:15]
Educational only - not financial advice. Keys come from ALPACA_API_KEY / ALPACA_SECRET_KEY (never printed or logged).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import normalize, rth  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402

URL = "https://data.alpaca.markets/v2/stocks/bars"
OUT = Path("/home/user/MCF/data/cache_fresh")
MIN_START = "2022-10-03"
MAX_END = "2024-09-14"          # exclusive (T00:00Z) -> last session 2024-09-13
MAX_WORKERS = 4
MIN_FREE_GB = 1.0
ARGS: dict = {}


def prereg_ok() -> tuple[bool, str]:
    if not (HERE / "FREEZE_HUNT.json").exists():
        return False, "round5/FREEZE_HUNT.json does not exist (hunt stage not frozen) - FRESH_PLAN sec. 4.7 / 7"
    want = (HERE / "FRESH_PLAN.sha256").read_text().split()[0]
    have = hashlib.sha256((HERE / "FRESH_PLAN.md").read_bytes()).hexdigest()
    if want != have:
        return False, "FRESH_PLAN.md sha256 mismatch"
    return True, "ok"


def free_gb() -> float:
    return shutil.disk_usage("/home/user").free / 1e9


def _get(sess, params):
    wait = 1.0
    r = None
    for _ in range(8):
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


def fetch_bars(sym: str, start: str = MIN_START, end: str = MAX_END) -> pd.DataFrame:
    """In-memory 1-minute bars (BarStore format) for one symbol; used by the downloader and for streaming."""
    assert start >= MIN_START and end <= MAX_END, "fresh range guard"
    sess = requests.Session()
    sess.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    params = {"symbols": sym, "timeframe": "1Min", "start": f"{start}T00:00:00Z", "end": f"{end}T00:00:00Z",
              "feed": "sip", "adjustment": "split", "limit": 10000}
    ts, o, h, l, c, v = [], [], [], [], [], []
    while True:
        j = _get(sess, params)
        bars = (j.get("bars") or {}).get(sym, [])
        ts += [b["t"] for b in bars]; o += [b["o"] for b in bars]; h += [b["h"] for b in bars]
        l += [b["l"] for b in bars]; c += [b["c"] for b in bars]; v += [b["v"] for b in bars]
        tok = j.get("next_page_token")
        if not tok:
            break
        params["page_token"] = tok
    if not ts:
        return pd.DataFrame()
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v},
                      index=pd.DatetimeIndex(pd.to_datetime(ts, utc=True)))
    df = rth(normalize(df))
    d = df.index.date
    assert d.min() >= pd.Timestamp(MIN_START).date() and d.max() < pd.Timestamp(MAX_END).date()
    return df


def daily_table(df: pd.DataFrame, sym: str) -> pd.DataFrame:
    """As research/history2y/build_frames.daily_table (adv20 = prior 20 sessions, min 5)."""
    g = df.groupby(df.index.date)
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(),
                      "volume": g["volume"].sum(), "dollar_volume": (df["close"] * df["volume"]).groupby(df.index.date).sum()})
    d["adv20"] = d["dollar_volume"].shift(1).rolling(20, min_periods=5).mean()
    d.index.name = "date"
    d = d.reset_index()
    d.insert(0, "symbol", sym)
    d["n_minutes"] = g.size().values
    return d


def fetch(sym: str):
    store = BarStore(OUT)
    p = store.path(sym)
    dp = OUT / "daily" / f"{p.stem}.parquet"
    write_bars = sym in ARGS["retained"]
    if dp.exists() and (p.exists() or not write_bars):
        return sym, "skip", 0
    if datetime.now(timezone.utc) >= ARGS["stop"]:
        return sym, "stopped", 0
    if free_gb() < MIN_FREE_GB:
        return sym, "stopped_disk", 0
    try:
        df = fetch_bars(sym, ARGS["start"], ARGS["end"])
    except Exception as e:  # noqa: BLE001  (message never contains the keys: they are only in request headers)
        return sym, f"failed: {type(e).__name__}: {str(e)[:120]}", 0
    if df.empty:
        return sym, "empty", 0
    if write_bars:
        tmp = p.with_suffix(".tmp")
        df.to_parquet(tmp)
        tmp.replace(p)
    tmp = dp.with_suffix(".tmp")
    daily_table(df, sym).to_parquet(tmp)
    tmp.replace(dp)
    return sym, "ok" if write_bars else "ok_daily_only", len(df)


def _init(a):
    ARGS.update(a)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=MIN_START)
    ap.add_argument("--end", default=MAX_END)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--stop-utc", default="2026-11-19T13:15")
    ap.add_argument("--symbols", default=str(HERE / "symbols_download_all.txt"))
    ap.add_argument("--retained-only", action="store_true", help="fetch only symbols_retained.txt names")
    a = ap.parse_args()
    assert a.start >= MIN_START and a.end <= MAX_END, "fresh range guard (never the 2-year cache / locked block)"
    ok, why = prereg_ok()
    if not ok:
        sys.exit(f"REFUSED: {why}. No fresh byte fetched.")
    retained = set((HERE / "symbols_retained.txt").read_text().split())
    syms = Path(a.symbols).read_text().split()
    if a.retained_only:
        syms = [s for s in syms if s in retained]
    for first in ("QQQ", "SPY"):            # SPY, QQQ first (FRESH_PLAN sec. 2.1)
        if first in syms:
            syms.remove(first); syms.insert(0, first)
    (OUT / "1Min").mkdir(parents=True, exist_ok=True)
    (OUT / "daily").mkdir(parents=True, exist_ok=True)
    stop = datetime.fromisoformat(a.stop_utc).replace(tzinfo=timezone.utc)
    t0, done, notok = time.time(), 0, []
    args = {"start": a.start, "end": a.end, "stop": stop, "retained": retained}
    with Pool(min(a.workers, MAX_WORKERS), initializer=_init, initargs=(args,)) as pool:
        for sym, status, n in pool.imap_unordered(fetch, syms):
            done += 1
            if not status.startswith(("ok", "skip")):
                notok.append(f"{sym}\t{status}")
            if done % 25 == 0 or status.startswith("failed"):
                print(f"{done}/{len(syms)} {sym} {status} {n} bars ({time.time() - t0:.0f}s, free {free_gb():.2f} GB)", flush=True)
    (OUT / "missing.txt").write_text("\n".join(notok) + ("\n" if notok else ""))
    print(f"finished {done} symbols, {len(notok)} not done (see missing.txt), {time.time() - t0:.0f}s", flush=True)
