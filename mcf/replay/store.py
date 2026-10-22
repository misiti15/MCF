"""Replay data: one file of 1-minute bars per session, daily bars, and the live priors rebuilt per session.

    data/replay/1Min/<YYYY-MM-DD>.parquet   long table (symbol, ts, open, high, low, close, volume), RTH, split-adjusted
    data/replay/daily.parquet               Alpaca SIP daily bars (split-adjusted), as the live prep reads them
    data/replay/priors/<YYYY-MM-DD>.pkl.gz  mcf.data.priors.build_priors output for that session (live code path)

Sources, in order: data/cache_hist/1Min (the 2-year lab-universe history, research/history2y; ends 2026-10-16),
data/cache/1Min, and a read-only Alpaca market-data fetch for sessions after the cache (`fetch_1min`). Only market data
is read; no trading endpoint is ever called. Keys come from ALPACA_API_KEY / ALPACA_SECRET_KEY and are never logged.

The rule-19 locked block (2024-11-01..2025-02-28) is never read: every reader filters it out at read time and
`check_dates` refuses sessions whose priors would need it. Educational only - not financial advice.
"""

from __future__ import annotations

import gzip
import os
import pickle
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ROOT
from ..data.bars import TZ, normalize, rth

STORE = Path(os.environ.get("MCF_REPLAY_STORE", ROOT / "data" / "replay"))
_DATA = (ROOT / "data" / "cache").resolve().parent        # a worktree links data/cache to the main checkout's data/
HIST = [Path(os.environ["MCF_REPLAY_HIST"])] if os.environ.get("MCF_REPLAY_HIST") else []
HIST += [ROOT / "data" / "cache_hist" / "1Min", _DATA / "cache_hist" / "1Min", ROOT / "data" / "cache" / "1Min"]
LOCK_A, LOCK_B = date(2024, 11, 1), date(2025, 2, 28)
LOOKBACK_DAYS = 50          # calendar days of history the live prep reads (daily bars); 5-minute profiles use 24
SYMBOLS_FILE = ROOT / "research" / "lab_symbols.txt"


def _d(x) -> date:
    return pd.Timestamp(x).date()


def check_dates(days) -> list[date]:
    """Sessions whose replay never touches the locked block (the session and its LOOKBACK_DAYS of priors)."""
    out = []
    for d in map(_d, days):
        if os.environ.get("MCF_HIST_ALLOW_LOCKED") != "1" and (d - timedelta(days=LOOKBACK_DAYS + 10)) <= LOCK_B \
                and d >= LOCK_A:
            raise ValueError(f"{d}: the session or its priors fall in the locked block {LOCK_A}..{LOCK_B} (rule 19)")
        out.append(d)
    return out


def sessions(start, end) -> list[date]:
    """NYSE sessions in [start, end] (weekdays minus the exchange holidays pandas-market-calendars would give; we use
    the sessions present in the store / cache, so a holiday simply has no file)."""
    days = pd.bdate_range(_d(start), _d(end))
    return [d.date() for d in days]


def symbols() -> list[str]:
    return SYMBOLS_FILE.read_text().split()


def day_path(d) -> Path:
    return STORE / "1Min" / f"{_d(d)}.parquet"


def available_days() -> list[date]:
    return sorted(_d(p.stem) for p in (STORE / "1Min").glob("*.parquet"))


# ---------------------------------------------------------------------------------------------- building the store
def _read_hist(args):
    sym, lo, hi = args
    import pyarrow.parquet as pq

    assert lo > LOCK_B or hi < LOCK_A, "locked block"
    parts = []
    for base in HIST:                 # cache_hist first; data/cache only adds sessions the history lacks
        f = base / f"{sym}.parquet"
        if not f.exists():
            continue
        names = pq.read_schema(f).names
        col = "__index_level_0__" if "__index_level_0__" in names else "timestamp"
        a, b = pd.Timestamp(lo, tz=TZ), pd.Timestamp(hi + timedelta(days=1), tz=TZ)
        df = pq.read_table(f, filters=[(col, ">=", a), (col, "<", b)]).to_pandas()   # row filter at read time
        if col in df.columns:
            df = df.set_index(col)
        if len(df):
            df = rth(normalize(df))
            if parts:
                df = df[~np.isin(df.index.date, list(set(parts[0].index.date)))]
            parts.append(df)
    if not parts:
        return sym, None
    df = pd.concat(parts).sort_index()
    dd = df.index.date
    assert not ((dd >= LOCK_A) & (dd <= LOCK_B)).any()
    return sym, df


def build_from_cache(start, end, syms: list[str] | None = None, workers: int = 4, log=print) -> list[date]:
    """Write data/replay/1Min/<day>.parquet for every session in [start, end] found in the local bar caches."""
    from multiprocessing import Pool

    lo, hi = _d(start), _d(end)
    if lo <= LOCK_B and hi >= LOCK_A:
        raise ValueError("the range overlaps the locked block (rule 19)")
    syms = syms or symbols()
    (STORE / "1Min").mkdir(parents=True, exist_ok=True)
    by_day: dict[date, list] = {}
    with Pool(workers) as pool:
        for i, (sym, df) in enumerate(pool.imap_unordered(_read_hist, [(s, lo, hi) for s in syms], chunksize=8)):
            if df is not None:
                for d, g in df.groupby(df.index.date):
                    by_day.setdefault(d, []).append(g.assign(symbol=sym))
            if (i + 1) % 200 == 0:
                log(f"store: read {i + 1}/{len(syms)} symbols")
    written = []
    for d, parts in sorted(by_day.items()):
        _write_day(d, pd.concat(parts))
        written.append(d)
    log(f"store: wrote {len(written)} sessions {written[0] if written else ''}..{written[-1] if written else ''}")
    return written


def _write_day(d, df: pd.DataFrame):
    x = df.rename_axis("ts").reset_index()[["symbol", "ts", "open", "high", "low", "close", "volume"]]
    x["symbol"] = x["symbol"].astype("category")
    tmp = day_path(d).with_suffix(".tmp")
    x.to_parquet(tmp, compression="zstd", index=False)
    tmp.replace(day_path(d))


def _session():
    import requests

    s = requests.Session()
    s.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
                      "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    return s


def _get(sess, url, params):
    import time

    wait = 1.0
    for _ in range(8):
        try:
            r = sess.get(url, params=params, timeout=60)
        except Exception:
            time.sleep(wait)
            wait = min(wait * 2, 60)
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(wait)
            wait = min(wait * 2, 60)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("market data request failed after retries")


def _fetch_bars(syms, start: str, end: str, timeframe: str, batch: int = 100) -> pd.DataFrame:
    """Read-only Alpaca market data (SIP, split-adjusted), multi-symbol, paged. Columns symbol + OHLCV, index UTC."""
    url = "https://data.alpaca.markets/v2/stocks/bars"
    sess = _session()
    rows = []
    for i in range(0, len(syms), batch):
        params = {"symbols": ",".join(syms[i:i + batch]), "timeframe": timeframe, "start": start, "end": end,
                  "feed": "sip", "adjustment": "split", "limit": 10000}
        while True:
            j = _get(sess, url, params)
            for sym, bars in (j.get("bars") or {}).items():
                rows += [(sym, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bars]
            tok = j.get("next_page_token")
            if not tok:
                break
            params["page_token"] = tok
        params.pop("page_token", None)
    df = pd.DataFrame(rows, columns=["symbol", "ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def fetch_1min(days, syms: list[str] | None = None, log=print) -> list[date]:
    """Sessions after the local caches: read-only fetch of 1-minute SIP bars into the store."""
    syms = syms or symbols()
    out = []
    for d in check_dates(days):
        if day_path(d).exists():
            continue
        df = _fetch_bars(syms, f"{d}T13:00:00Z", f"{d}T21:00:00Z", "1Min")
        if df.empty:
            log(f"fetch: {d} no bars (holiday?)")
            continue
        df = df.set_index("ts")
        df.index = df.index.tz_convert(TZ)
        df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
        (STORE / "1Min").mkdir(parents=True, exist_ok=True)
        _write_day(d, df)
        out.append(d)
        log(f"fetch: {d} {df.symbol.nunique()} symbols {len(df)} bars")
    return out


def fetch_daily(start, end, syms: list[str] | None = None, log=print) -> Path:
    """Daily SIP bars (split-adjusted) for the priors, as the live prep reads them. Never inside the locked block."""
    lo = max(_d(start), LOCK_B + timedelta(days=1))
    syms = syms or symbols()
    df = _fetch_bars(syms, f"{lo}T00:00:00Z", f"{_d(end) + timedelta(days=1)}T00:00:00Z", "1Day")
    p = STORE / "daily.parquet"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        old = pd.read_parquet(p)
        df = pd.concat([old, df]).drop_duplicates(["symbol", "ts"], keep="last")
    df.sort_values(["symbol", "ts"]).to_parquet(p, compression="zstd", index=False)
    log(f"daily: {df.symbol.nunique()} symbols {df.ts.min()}..{df.ts.max()}")
    return p


# ---------------------------------------------------------------------------------------------- reading
def load_day(d, syms=None) -> dict[str, pd.DataFrame]:
    """symbol -> RTH 1-minute bars of session d (tz America/New_York, bar start)."""
    d = check_dates([d])[0]
    p = day_path(d)
    if not p.exists():
        return {}
    x = pd.read_parquet(p)
    if syms is not None:
        x = x[x.symbol.isin(set(syms))]
    out = {}
    ts = pd.DatetimeIndex(x["ts"]).tz_convert(TZ)
    x = x.drop(columns="ts").set_index(ts)
    for sym, g in x.groupby("symbol", observed=True):
        out[str(sym)] = g[["open", "high", "low", "close", "volume"]].astype(float)
    return out


class _Bars:
    def __init__(self, df):
        self.df = df


class StoreHistClient:
    """A StockHistoricalDataClient stand-in for mcf.data.priors.build_priors: daily bars from data/replay/daily.parquet
    (the Alpaca daily bars the live prep reads; falls back to RTH aggregation of the 1-minute store when a symbol has
    none), 5-minute and 1-minute bars from the 1-minute store. Bars are only served strictly before `upto`."""

    def __init__(self, upto: date, daily: pd.DataFrame | None = None, cache: dict | None = None):
        self.upto = upto
        self.daily = daily
        self.cache = cache if cache is not None else {}

    def _day(self, d: date, minutes: int) -> pd.DataFrame | None:
        k = (d, minutes)
        if k not in self.cache:
            if not day_path(d).exists() or (LOCK_A <= d <= LOCK_B):
                self.cache[k] = None
            else:
                x = pd.read_parquet(day_path(d))
                x["ts"] = pd.DatetimeIndex(x["ts"]).tz_convert(TZ)
                if minutes > 1:
                    x["ts"] = x["ts"].dt.floor(f"{minutes}min")
                    x = x.sort_values(["symbol", "ts"], kind="mergesort").groupby(["symbol", "ts"], observed=True).agg(
                        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
                        volume=("volume", "sum")).reset_index()
                x["symbol"] = x["symbol"].astype(str)
                self.cache[k] = x
            if len(self.cache) > 80:
                self.cache.pop(next(iter(self.cache)))
        return self.cache[k]

    def get_stock_bars(self, req):
        syms = req.symbol_or_symbols
        syms = [syms] if isinstance(syms, str) else list(syms)
        start, end = _d(req.start), min(_d(req.end), self.upto)
        tf = req.timeframe
        unit = str(getattr(tf.unit, "value", tf.unit)).lower()
        if unit.startswith("day"):
            df = self._daily(syms, start, end)
        else:
            mins = int(tf.amount)
            parts = []
            for d in pd.bdate_range(start, end - timedelta(days=1)):
                x = self._day(d.date(), mins)
                if x is not None:
                    parts.append(x[x.symbol.isin(syms)])
            df = pd.concat(parts) if parts else pd.DataFrame(columns=["symbol", "ts"])
        if df.empty:
            return _Bars(pd.DataFrame())
        df = df.rename(columns={"ts": "timestamp"}).set_index(["symbol", "timestamp"]).sort_index()
        return _Bars(df[["open", "high", "low", "close", "volume"]])

    def _daily(self, syms, start, end) -> pd.DataFrame:
        have = set()
        parts = []
        if self.daily is not None and len(self.daily):
            dd = self.daily
            t = pd.DatetimeIndex(dd["ts"]).tz_convert(TZ)
            m = dd["symbol"].isin(syms) & (t.date >= start) & (t.date < end)
            x = dd[m].copy()
            have = set(x["symbol"])
            parts.append(x)
        miss = [s for s in syms if s not in have]
        if miss:   # RTH aggregation of the 1-minute store (labelled fallback: no auction / extended-hours volume)
            rows = []
            for d in pd.bdate_range(start, end - timedelta(days=1)):
                x = self._day(d.date(), 1)
                if x is None:
                    continue
                x = x[x.symbol.isin(miss)]
                g = x.groupby("symbol").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"),
                                            close=("close", "last"), volume=("volume", "sum")).reset_index()
                g["ts"] = pd.Timestamp(d.date(), tz=TZ)
                rows.append(g)
            if rows:
                parts.append(pd.concat(rows))
        return pd.concat(parts) if parts else pd.DataFrame(columns=["symbol", "ts"])


def priors_path(d) -> Path:
    return STORE / "priors" / f"{_d(d)}.pkl.gz"


def build_priors_for(d, syms: list[str], exact_symbols=(), cache: dict | None = None, daily=None, log=print) -> dict:
    """The live prep's priors (mcf.data.priors.build_priors, unchanged) for session d, from the store. Cached."""
    from ..data.priors import build_priors

    d = check_dates([d])[0]
    p = priors_path(d)
    if p.exists():
        with gzip.open(p, "rb") as f:
            return pickle.load(f)
    if daily is None and (STORE / "daily.parquet").exists():
        daily = pd.read_parquet(STORE / "daily.parquet")
    cl = StoreHistClient(d, daily, cache)
    pri = build_priors(list(syms), d, feed="sip", exact_symbols=list(exact_symbols), client=cl, log=lambda m: None)
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p.with_suffix(".tmp"), "wb", compresslevel=3) as f:
        pickle.dump(pri, f)
    p.with_suffix(".tmp").replace(p)
    return pri


def live_universe(d, branch: str = "origin/mcf-data") -> set[str] | None:
    """The live universe.csv of session d (latest version committed on or before d on the account's data branch),
    or None when the branch has none that old."""
    import io
    import subprocess

    r = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H %ad", "--date=short", branch, "--", "universe.csv"],
                       capture_output=True, text=True)
    for line in r.stdout.splitlines():
        sha, day = line.split()
        if _d(day) <= _d(d):
            csv = subprocess.run(["git", "-C", str(ROOT), "show", f"{sha}:universe.csv"], capture_output=True,
                                 text=True).stdout
            try:
                u = pd.read_csv(io.StringIO(csv))
                if _d(str(u["built_at"].iloc[0])[:10]) < _d(d) - timedelta(days=4):
                    return None
            except Exception:
                return None
            return set(u["symbol"].astype(str))
    return None


def earnings_blackout(d, branch: str = "origin/mcf-data") -> set[str] | None:
    """Symbols the live earnings blackout removed on session d (state earnings/<d>.json), None when not recorded."""
    import json
    import subprocess

    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{branch}:earnings/{_d(d)}.json"], capture_output=True,
                       text=True)
    if r.returncode:
        return None
    try:
        return set(json.loads(r.stdout).get("symbols", {}))
    except ValueError:
        return None


def frozen_setups(d, branch: str = "origin/mcf-data") -> dict | None:
    """The account's frozen setup config of session d (state setups/<d>.json: strategies, exits, shorts, live,
    universe), None when not recorded."""
    import json
    import subprocess

    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{branch}:setups/{_d(d)}.json"], capture_output=True,
                       text=True)
    if r.returncode:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def build_spreads(branches=("origin/mcf-data", "origin/mcf-data-testing", "origin/mcf-data-testing2",
                             "origin/mcf-data-graveyard", "origin/mcf-data-gen")) -> Path:
    """The live SIP quote spreads the runner journaled at decision time (signals.info spread_bps, every account) ->
    data/replay/spreads.json {symbol: [bps, ...], "_all": [...]}: the replay's quote model samples from them."""
    import json
    import sqlite3
    import subprocess
    import tempfile

    by: dict[str, list] = {}
    for br in branches:
        r = subprocess.run(["git", "-C", str(ROOT), "show", f"{br}:journal.db"], capture_output=True)
        if r.returncode or not r.stdout:
            continue
        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            f.write(r.stdout)
            f.flush()
            con = sqlite3.connect(f.name)
            rows = con.execute("SELECT symbol, info FROM signals WHERE info LIKE '%spread_bps%'").fetchall()
            con.close()
        for sym, info in rows:
            try:
                v = float(json.loads(info)["spread_bps"])
            except (ValueError, KeyError, TypeError):
                continue
            by.setdefault(sym, []).append(v)
    by["_all"] = sorted(v for k, x in by.items() for v in x)
    p = STORE / "spreads.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(by))
    return p


def load_spreads() -> dict | None:
    import json

    p = STORE / "spreads.json"
    return json.loads(p.read_text()) if p.exists() else None


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description="build the replay store (1-minute packs, daily bars, priors)")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--fetch", action="store_true", help="read-only Alpaca fetch for sessions the caches lack")
    ap.add_argument("--daily", action="store_true", help="fetch Alpaca daily bars for the priors")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    build_from_cache(a.start, a.end, workers=a.workers)
    if a.fetch:
        have = set(available_days())
        fetch_1min([d for d in sessions(a.start, a.end) if d not in have and d <= date.today()])
    if a.daily:
        fetch_daily(_d(a.start) - timedelta(days=LOOKBACK_DAYS + 30), a.end)


if __name__ == "__main__":
    main()
