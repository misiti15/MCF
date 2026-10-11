"""After-hours sample for family A (NOTES.md 1.6): Alpaca SIP 1-minute bars 15:59-17:05 ET and quotes 16:55-16:57 ET
on report day d, raw prices, for every event in the open splits (d outside 2024-10-01..2025-04-10, the locked block
plus its buffer). Data endpoints only (GET). Keys from env, never logged. Resumable (per-date parts).
    python research/bdi/earnings/ah_fetch.py
Educational only - not financial advice.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import elib as E  # noqa: E402

OUT = E.DATA / "ah"; OUT.mkdir(parents=True, exist_ok=True)
S = requests.Session()
S.headers.update({"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
BASE = "https://data.alpaca.markets/v2/stocks/"


def get(kind, params):
    out, tok = {}, None
    while True:
        p = dict(params, limit=10000, feed="sip")
        if tok:
            p["page_token"] = tok
        for a in range(8):
            try:
                r = S.get(BASE + kind, params=p, timeout=60)
            except requests.RequestException:
                time.sleep(2 ** a); continue
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(min(60, 2 ** a)); continue
            r.raise_for_status(); break
        else:
            raise RuntimeError(f"{kind} gave up")
        js = r.json()
        for s, lst in (js.get(kind) or {}).items():
            out.setdefault(s, []).extend(lst)
        tok = js.get("next_page_token")
        if not tok:
            return out
        time.sleep(0.2)


def et(day, hhmm):
    return pd.Timestamp(f"{day} {hhmm}", tz="America/New_York").tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ev = E.events()
    ev = ev[ev.elig & (ev.split != "none") & ~ev.locked_touch]
    dd = pd.Series(E.dates[ev.d.to_numpy()], index=ev.index)
    ev = ev[~((dd >= "2024-10-01") & (dd <= "2025-04-10"))]
    by = ev.groupby("d").symbol.apply(list)
    print("dates", len(by), "events", len(ev), flush=True)
    for k, (drow, syms) in enumerate(by.items()):
        day = E.dates[drow].date()
        f = OUT / f"{day}.parquet"
        if f.exists():
            continue
        syms = sorted(set(syms) | {"SPY"})
        rows = []
        for i in range(0, len(syms), 50):
            ch = ",".join(syms[i:i + 50])
            bars = get("bars", {"symbols": ch, "timeframe": "1Min", "start": et(day, "15:59"), "end": et(day, "17:05"),
                                "adjustment": "raw"})
            for s, lst in bars.items():
                for b in lst:
                    rows.append({"symbol": s, "t": b["t"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"], "kind": "bar"})
            qs = get("quotes", {"symbols": ch, "start": et(day, "16:55"), "end": et(day, "16:57")})
            for s, lst in qs.items():
                ap = np.array([q.get("ap", 0) for q in lst], float); bp = np.array([q.get("bp", 0) for q in lst], float)
                ok = (ap > 0) & (bp > 0) & (ap >= bp)
                if ok.any():
                    mid = (ap[ok] + bp[ok]) / 2
                    rows.append({"symbol": s, "t": None, "o": float(np.median((ap[ok] - bp[ok]) / mid)), "h": float(np.median(mid)),
                                 "l": float(ok.sum()), "c": np.nan, "v": np.nan, "kind": "quote"})
        df = pd.DataFrame(rows, columns=["symbol", "t", "o", "h", "l", "c", "v", "kind"])
        df["day"] = pd.Timestamp(day)
        df.to_parquet(f, index=False)
        if k % 50 == 0:
            print(k, day, len(syms), len(df), flush=True)
        time.sleep(0.2)
    print("done", flush=True)


if __name__ == "__main__":
    main()
