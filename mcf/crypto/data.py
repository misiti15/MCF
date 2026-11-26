"""Alpaca crypto 1-minute bars: download, cache, load, resample.

Data source: Alpaca's PUBLIC crypto market-data endpoint (GET only, no keys):
    https://data.alpaca.markets/v1beta3/crypto/us/bars
Never send keys here; never call a trading or account endpoint (this module has no code for either).

Cache: data/crypto/1Min/<BASE>_USD/<YEAR>.parquet (gitignored), float32 prices, one file per symbol-year, so a
download can resume and the current year is re-fetched only from its last stored minute.

Gaps and zero-volume minutes: Alpaca's own crypto venue is thin; a minute with no trade has NO bar. `load_bars`
returns the raw (gappy) bars; `to_grid` reindexes onto a full 1-minute grid, forward-fills the close into
o/h/l/c of empty minutes and sets volume 0 and `filled=True`, so a signal can require real prints
(`filled == False`) and a backtest never "fills" on a minute where nobody traded at a fabricated price without
knowing it. Resampling uses only real bars (empty buckets stay NaN unless `ffill=True`).

Educational only — not financial advice.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path(os.environ.get("MCF_CRYPTO_CACHE", ROOT / "data" / "crypto" / "1Min"))
BASE_URL = "https://data.alpaca.markets/v1beta3/crypto/us"
ALLOWED_PATHS = ("bars", "latest/orderbooks", "latest/quotes", "latest/trades", "latest/bars", "quotes", "trades")
SIZE_CAP_BYTES = int(1.5 * 1024**3)
START = "2021-01-01T00:00:00Z"

# USD pairs Alpaca listed with a live print on 2026-11-26 (stablecoins excluded), majors first so a size cap
# keeps the most useful ones. Survivorship: pairs delisted earlier (MATIC, NEAR, ALGO, TRX, MKR) are left out.
PAIRS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "LTC", "BCH", "LINK", "AVAX", "DOT", "UNI", "AAVE", "ADA", "SHIB",
         "PEPE", "CRV", "SUSHI", "GRT", "BAT", "XTZ", "YFI", "FIL", "LDO", "ARB", "POL", "RENDER", "ONDO", "SKY",
         "TRUMP", "HYPE"]
COLS = ["o", "h", "l", "c", "v", "vw", "n"]


def _get(path: str, params: dict, tries: int = 6) -> dict:
    """GET on the public market-data API only (allow-listed paths, no auth headers)."""
    if path not in ALLOWED_PATHS:
        raise ValueError(f"path not allowed: {path}")
    url = f"{BASE_URL}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "mcf-research"})
    for k in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception:  # noqa: BLE001 - network hiccups / 429: back off and retry
            if k == tries - 1:
                raise
            time.sleep(2 * (k + 1))
    raise RuntimeError("unreachable")


def symbol_dir(base: str, cache: Path | None = None) -> Path:
    return (cache or CACHE) / f"{base}_USD"


def cache_bytes(cache: Path | None = None) -> int:
    c = cache or CACHE
    return sum(p.stat().st_size for p in c.rglob("*.parquet")) if c.exists() else 0


def bars_json_to_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=COLS, index=pd.DatetimeIndex([], tz="UTC", name="t"))
    df = pd.DataFrame(rows)
    df["t"] = pd.to_datetime(df["t"], utc=True)
    df = df.set_index("t").sort_index()
    for c in COLS:
        if c not in df:
            df[c] = np.nan
    out = df[COLS].astype({"o": "float64", "h": "float64", "l": "float64", "c": "float64", "v": "float64",
                           "vw": "float64"})
    out["n"] = df["n"].fillna(0).astype("int32")
    return out[~out.index.duplicated(keep="last")]


def _write_year(base: str, year: int, df: pd.DataFrame, cache: Path | None) -> None:
    d = symbol_dir(base, cache)
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{year}.parquet"
    if f.exists():
        df = pd.concat([pd.read_parquet(f), df])
        df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.astype({c: "float32" for c in ["o", "h", "l", "c", "v", "vw"]})
    df.to_parquet(f, compression="zstd")


def last_stored(base: str, cache: Path | None = None) -> pd.Timestamp | None:
    d = symbol_dir(base, cache)
    files = sorted(d.glob("*.parquet")) if d.exists() else []
    if not files:
        return None
    return pd.read_parquet(files[-1], columns=["c"]).index.max()


def download(base: str, start: str = START, end: str | None = None, cache: Path | None = None,
             cap_bytes: int = SIZE_CAP_BYTES, log=print) -> int:
    """Fetch BASE/USD 1-min bars from `start` (or the last stored minute) to `end`; returns rows written."""
    last = last_stored(base, cache)
    if last is not None:
        start = (last + pd.Timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {"symbols": f"{base}/USD", "timeframe": "1Min", "start": start, "limit": 10000, "sort": "asc"}
    if end:
        params["end"] = end
    buf: list[dict] = []
    total = 0
    token = None
    while True:
        if token:
            params["page_token"] = token
        js = _get("bars", params)
        buf.extend(js.get("bars", {}).get(f"{base}/USD", []) or [])
        token = js.get("next_page_token")
        if len(buf) >= 200_000 or not token:
            df = bars_json_to_frame(buf)
            buf = []
            for y, g in df.groupby(df.index.year):
                _write_year(base, int(y), g, cache)
            total += len(df)
            if len(df):
                log(f"{base}: +{len(df)} rows to {df.index.max()}")
            if cache_bytes(cache) > cap_bytes:
                log(f"size cap {cap_bytes} reached; stopping at {base}")
                raise MemoryError("crypto cache size cap reached")
        if not token:
            return total


def load_bars(base: str, start=None, end=None, cache: Path | None = None) -> pd.DataFrame:
    """Raw stored 1-min bars for BASE/USD (UTC index, only minutes that traded), start inclusive, end exclusive.

    The end is always clipped at the LOCKED block start (mcf/crypto/splits.py) unless the lock is opened."""
    from .splits import clip_end
    e = clip_end(end)
    s = None
    if start is not None:
        s = pd.Timestamp(start)
        s = s.tz_localize("UTC") if s.tzinfo is None else s
    d = symbol_dir(base, cache)
    files = sorted(d.glob("*.parquet")) if d.exists() else []
    y0 = s.year if s is not None else 0
    files = [f for f in files if y0 <= int(f.stem) <= e.year]
    if not files:
        return bars_json_to_frame([])
    df = pd.concat([pd.read_parquet(f) for f in files]).sort_index()
    if s is not None:
        df = df[df.index >= s]
    df = df[df.index < e]
    return df.astype({c: "float64" for c in ["o", "h", "l", "c", "v", "vw"]})


def to_grid(bars: pd.DataFrame, freq: str = "1min") -> pd.DataFrame:
    """Full minute grid between the first and last bar. Empty minutes: o=h=l=c=last close, v=0, filled=True."""
    if bars.empty:
        out = bars.copy()
        out["filled"] = pd.Series(dtype=bool)
        return out
    idx = pd.date_range(bars.index[0].floor(freq), bars.index[-1].floor(freq), freq=freq, tz="UTC", name="t")
    g = bars.reindex(idx)
    filled = g["c"].isna()
    c = g["c"].ffill()
    for k in ("o", "h", "l"):
        g[k] = g[k].where(~filled, c)
    g["c"] = c
    g["vw"] = g["vw"].where(~filled, c)
    g["v"] = g["v"].fillna(0.0)
    g["n"] = g["n"].fillna(0).astype("int32")
    g["filled"] = filled.to_numpy()
    return g


def resample(bars: pd.DataFrame, rule: str, ffill: bool = False) -> pd.DataFrame:
    """OHLCV resample from real 1-min bars (left-labelled, left-closed). Empty buckets are dropped unless ffill."""
    real = bars[~bars["filled"]] if "filled" in bars else bars
    pv = (real["vw"].fillna(real["c"]) * real["v"])
    agg = pd.DataFrame({
        "o": real["o"].resample(rule).first(),
        "h": real["h"].resample(rule).max(),
        "l": real["l"].resample(rule).min(),
        "c": real["c"].resample(rule).last(),
        "v": real["v"].resample(rule).sum(),
        "n": real["n"].resample(rule).sum(),
        "pv": pv.resample(rule).sum(),
    })
    agg["vw"] = np.where(agg["v"] > 0, agg["pv"] / agg["v"].where(agg["v"] > 0, 1), agg["c"])
    agg = agg.drop(columns="pv")
    if ffill:
        c = agg["c"].ffill()
        empty = agg["o"].isna()
        for k in ("o", "h", "l", "vw"):
            agg[k] = agg[k].where(~empty, c)
        agg["c"] = c
        agg["filled"] = empty
        return agg
    return agg.dropna(subset=["o"])


def coverage(cache: Path | None = None) -> pd.DataFrame:
    """One row per cached pair: first / last minute, bars, share of minutes with a real bar, MB."""
    rows = []
    for d in sorted((cache or CACHE).glob("*_USD")):
        files = sorted(d.glob("*.parquet"))
        if not files:
            continue
        idx = pd.concat([pd.read_parquet(f, columns=["v"]) for f in files]).index
        span = (idx.max() - idx.min()).total_seconds() / 60 + 1
        rows.append({"pair": d.name.replace("_", "/"), "first": idx.min(), "last": idx.max(), "bars": len(idx),
                     "fill_share": len(idx) / span, "mb": sum(f.stat().st_size for f in files) / 1e6})
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Download Alpaca crypto 1-min bars (public data, GET only)")
    ap.add_argument("pairs", nargs="*", default=PAIRS)
    ap.add_argument("--start", default=START)
    ap.add_argument("--end", default=None)
    ap.add_argument("--coverage", action="store_true")
    a = ap.parse_args(argv)
    if a.coverage:
        print(coverage().to_string())
        return 0
    for p in a.pairs:
        try:
            download(p, a.start, a.end)
        except MemoryError:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
