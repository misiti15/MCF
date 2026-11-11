"""Exchange session close for a day, and the flatten time that follows from it (LR1, owner 2026-11-11).

On half-day sessions (NYSE 13:00 ET close: e.g. Fri 2026-11-27, Thu 2026-12-24) a fixed 15:55 flatten never comes: the
market closes at 13:00, the bracket legs (DAY orders) expire, and positions would sit unprotected over the weekend /
holiday. Every intraday component therefore reads the calendar close:

  flatten time = min(config session.flatten_by, calendar close - session.flatten_lead_min (5 min))

Sources, in order: the Alpaca trading calendar (GET /v2/calendar, read-only; through a broker object's client or plain
HTTPS with the account keys), then the known early closes below (fallback when the calendar is unreachable), then the
regular 16:00 close. Educational only - not financial advice."""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import date, datetime, time, timedelta

import pandas as pd

NY = "America/New_York"
REGULAR_CLOSE = time(16, 0)
# NYSE published early closes (13:00 ET). Fallback only: the Alpaca calendar is read first.
# Source: NYSE holidays & trading hours (nyse.com/markets/hours-calendars), read 2026-11-11.
EARLY_CLOSES = {"2026-11-27": time(13, 0), "2026-12-24": time(13, 0)}
DEFAULT_LEAD_MIN = 5

_cache: dict[str, time] = {}


def _t(x) -> time:
    if isinstance(x, time):
        return x
    if isinstance(x, datetime):
        return x.time()
    s = str(x).strip()
    if "T" in s or " " in s:                          # an ISO timestamp: take its ET wall time
        ts = pd.Timestamp(s)
        ts = ts.tz_localize(NY) if ts.tzinfo is None else ts.tz_convert(NY)
        return ts.time().replace(second=0, microsecond=0)
    hh, mm = s.split(":")[:2]
    return time(int(hh), int(mm))


def _from_broker(broker, day: str) -> time | None:
    client = getattr(broker, "client", None)
    if client is None:
        return None
    try:
        from alpaca.trading.requests import GetCalendarRequest

        cal = client.get_calendar(GetCalendarRequest(start=date.fromisoformat(day), end=date.fromisoformat(day)))
    except Exception:
        try:
            cal = client.get_calendar()
        except Exception:
            return None
    for c in cal or []:
        d = getattr(c, "date", None) if not isinstance(c, dict) else c.get("date")
        if str(d)[:10] == day:
            close = getattr(c, "close", None) if not isinstance(c, dict) else c.get("close")
            return _t(close) if close is not None else None
    return None


def _from_http(day: str) -> time | None:
    key, sec = os.environ.get("ALPACA_TRADE_API_KEY") or os.environ.get("ALPACA_API_KEY"), \
        os.environ.get("ALPACA_TRADE_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY")
    if not key or not sec:
        return None
    req = urllib.request.Request(f"https://paper-api.alpaca.markets/v2/calendar?start={day}&end={day}",
                                 headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            cal = json.loads(r.read())
    except Exception as e:  # noqa: BLE001 - a calendar hiccup falls back to the known early closes
        print(f"calendar unreachable ({type(e).__name__}); using the known early closes")
        return None
    for c in cal or []:
        if c.get("date") == day and c.get("close"):
            return _t(c["close"])
    return None


def session_close(day, broker=None, use_http: bool = True) -> time:
    """The exchange close (ET wall time) of `day`: Alpaca calendar, else EARLY_CLOSES, else 16:00. Cached per day."""
    d = str(pd.Timestamp(str(day)).date())
    if d in _cache:
        return _cache[d]
    c = _from_broker(broker, d) if broker is not None else None
    if c is None and use_http and broker is None:
        c = _from_http(d)
    if c is None:
        c = EARLY_CLOSES.get(d, REGULAR_CLOSE)
    else:
        _cache[d] = c                                 # only a calendar answer is cached (a fallback is retried)
    return c


def is_early_close(close: time) -> bool:
    return close < REGULAR_CLOSE


def flatten_time(configured, close: time, lead_min: float = DEFAULT_LEAD_MIN) -> time:
    """min(configured flatten, close - lead_min)."""
    cfg_t = _t(configured)
    c = (datetime.combine(date(2000, 1, 3), close) - timedelta(minutes=float(lead_min))).time()
    return min(cfg_t, c)


def plus(t0: time, minutes: float) -> time:
    return (datetime.combine(date(2000, 1, 3), t0) + timedelta(minutes=float(minutes))).time()
