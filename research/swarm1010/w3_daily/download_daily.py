"""W3 (swarm 2026-10-10): Alpaca SIP DAILY bars, split+dividend adjusted, 2016-01-01..today.

Universe: research/lab_symbols.txt + index ETFs + sector ETFs. One multi-symbol request per batch of 100 symbols,
paged; backs off on 429. Single process. Output: research/swarm1010/w3_daily/data/daily_2016.parquet (zstd), plus
coverage.csv. Keys from ALPACA_API_KEY / ALPACA_SECRET_KEY, never printed. Read-only market data endpoint.
Educational only - not financial advice.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
URL = "https://data.alpaca.markets/v2/stocks/bars"
EXTRA = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
         "SMH", "XBI", "KRE", "XHB", "XRT", "XME", "GDX", "IYR", "TLT", "GLD"]


def _get(sess, params):
    wait = 1.0
    for _ in range(10):
        try:
            r = sess.get(URL, params=params, timeout=90)
        except requests.RequestException:
            time.sleep(wait); wait = min(wait * 2, 60); continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(wait); wait = min(wait * 2, 60); continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("gave up")


def main(start="2016-01-01", end=None):
    end = end or pd.Timestamp.utcnow().strftime("%Y-%m-%d")
    syms = [s.strip() for s in (ROOT / "research" / "lab_symbols.txt").read_text().split() if s.strip()]
    syms = list(dict.fromkeys(syms + EXTRA))
    sess = requests.Session()
    sess.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    rows = []
    for i in range(0, len(syms), 100):
        batch = syms[i:i + 100]
        params = {"symbols": ",".join(batch), "timeframe": "1Day", "start": start, "end": end, "feed": "sip",
                  "adjustment": "all", "limit": 10000}
        while True:
            j = _get(sess, params)
            for s, bars in (j.get("bars") or {}).items():
                rows += [(s, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"], b.get("vw"), b.get("n")) for b in bars]
            tok = j.get("next_page_token")
            if not tok:
                break
            params["page_token"] = tok
            time.sleep(0.35)  # ~170 req/min max, below the 200/min budget
        params.pop("page_token", None)
        print(f"batch {i // 100 + 1}/{(len(syms) + 99) // 100}: rows so far {len(rows)}", flush=True)
    df = pd.DataFrame(rows, columns=["symbol", "t", "open", "high", "low", "close", "volume", "vwap", "trades"])
    df["date"] = pd.to_datetime(df["t"], utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    df = df.drop(columns="t")
    for c in ["open", "high", "low", "close", "vwap"]:
        df[c] = df[c].astype("float64")
    df["volume"] = df["volume"].astype("float64")
    df["symbol"] = df["symbol"].astype("category")
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    out = HERE / "data" / "daily_2016.parquet"
    df.to_parquet(out, compression="zstd", index=False)
    cov = df.groupby("symbol", observed=True).agg(first=("date", "min"), last=("date", "max"), days=("date", "size"),
                                                  med_dollar_vol=("close", lambda x: 0)).reset_index()
    dv = (df["close"] * df["volume"]).groupby(df["symbol"], observed=True).median()
    cov["med_dollar_vol"] = cov["symbol"].map(dv).round(-3)
    missing = sorted(set(syms) - set(cov["symbol"].astype(str)))
    cov.to_csv(HERE / "coverage_by_symbol.csv", index=False)
    print("requested", len(syms), "got", cov.shape[0], "missing", missing, "rows", len(df), "MB",
          round(out.stat().st_size / 1e6, 1))


if __name__ == "__main__":
    main(*sys.argv[1:])
