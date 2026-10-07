"""Earnings blackout (owner rule 2026-10-07): no trades within N trading days of a company's earnings, either side.

Source: the public Nasdaq earnings calendar (api.nasdaq.com, no key), one request per calendar date. If it cannot be
reached, the Alpaca news feed is the fallback: headlines that mention earnings/results in the past N trading days
(the forward side is then unknown, which the status reports). Results are cached per session in
state/earnings/<date>.json so every job of the day uses the same list. Educational only — not financial advice.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

NASDAQ = "https://api.nasdaq.com/api/calendar/earnings?date={d}"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36",
           "Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"}
NEWS_RX = re.compile(r"\b(earnings|quarterly results|Q[1-4] (?:20\d\d )?results|reports? (?:first|second|third|fourth)[- ]quarter)\b", re.I)


def window(day: date, n: int) -> list[date]:
    """Weekdays within n trading days before and after `day` (holidays count as days; slightly conservative)."""
    d = pd.Timestamp(day)
    return [x.date() for x in pd.bdate_range(d - pd.offsets.BDay(n), d + pd.offsets.BDay(n))]


def _nasdaq(dates: list[date], get) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for d in dates:
        r = get(NASDAQ.format(d=d.isoformat()))
        rows = ((r or {}).get("data") or {}).get("rows") or []
        for row in rows:
            sym = (row.get("symbol") or "").strip().upper()
            if sym:
                out.setdefault(sym, []).append(d.isoformat())
    return out


def _http_get(url: str):
    import requests

    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _alpaca_news(symbols: list[str], start: date, end: date) -> dict[str, list[str]]:
    from alpaca.data.historical.news import NewsClient
    from alpaca.data.requests import NewsRequest

    cli = NewsClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
    out: dict[str, list[str]] = {}
    for i in range(0, len(symbols), 50):
        req = NewsRequest(symbols=",".join(symbols[i:i + 50]), start=pd.Timestamp(start).to_pydatetime(),
                          end=pd.Timestamp(end + timedelta(days=1)).to_pydatetime(), limit=50)
        for n in cli.get_news(req).data.get("news", []):
            if NEWS_RX.search(n.headline or ""):
                for s in n.symbols or []:
                    if s in symbols:
                        out.setdefault(s, []).append(str(n.created_at)[:10])
    return out


def blackout(day: date, symbols: list[str], n: int, state_dir: str | Path | None = None, get=None, log=print) -> dict:
    """{"symbols": {SYM: [dates]}, "source": ..., "complete": bool} for symbols with earnings within ±n trading days."""
    cache = Path(state_dir) / "earnings" / f"{day}.json" if state_dir else None
    if cache and cache.exists():
        return json.loads(cache.read_text())
    dates = window(day, n)
    res = {"day": str(day), "days": n, "source": "nasdaq", "complete": True, "symbols": {}}
    try:
        cal = _nasdaq(dates, get or _http_get)
        if not cal:
            raise RuntimeError("empty calendar")
        res["symbols"] = {s: v for s, v in cal.items() if s in set(symbols)}
    except Exception as e:
        log(f"earnings: Nasdaq calendar unavailable ({e}); falling back to Alpaca news (past side only)")
        res.update(source="alpaca-news", complete=False)
        try:
            res["symbols"] = _alpaca_news(sorted(symbols), dates[0], day)
        except Exception as e2:
            log(f"earnings: news fallback failed too ({e2}); no blackout applied")
            res.update(source="none", symbols={})
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(res, indent=1))
    log(f"earnings blackout ±{n} trading days ({res['source']}): {len(res['symbols'])} symbols excluded")
    return res
