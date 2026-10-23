"""pod-cwt4-cortes-trapzone-low-edge-hold-long - Prior-day last-45-minute 'trap zone': buy the first held test of
its low edge after an open inside it (LONG).

Source: Chat With Traders ep 309, Diego Ivan Cortes Lopez ('Trap-zone avoidance filter': the prior day's last
45 minutes is a trap zone; trade only from its edges). New reference level (nearest existing ideas use PDH or
today's midday range, not the prior day's 15:15-16:00 band).
URL: https://chatwithtraders.com/309

Rules (plain English). Universe: the top 150 symbols by adv20 on each date inside the scorer universe, plus SPY/QQQ.
  1. Trap zone TZ = high / low of the prior session's bars from 15:15 to the close (5-min bars closing 15:20-15:55;
     the history has no 15:55-16:00 bar, declared). TZ width between 0.25 and 1.0 x daily ATR(14).
  2. Today's open is inside TZ.
  3. Test: a bar between 09:50 and 12:00 trades to TZ low (bar low <= TZ low + 0.05 ATR) but not more than 0.15 ATR
     below it; skip the day once the session low is more than 0.3 ATR below TZ low. (The 09:45 bar is not in the
     frames, declared.)
  4. Only the first test episode of the day (consecutive test bars count as one). The test bar or the next bar is a 5-min bottoming tail (lower wick >= 50% of range, close in the upper half)
     and closes back at or above TZ low - this is the decision bar.
  5. No middle trades: the decision close is within 0.2 ATR of TZ low.
  Entry: decision bar's close (scorer; the source's next-bar open), bar close 09:50-12:05. Stop (GEOM S): the test
  low (lowest low of the test and decision bars) - 0.05 ATR. Target: TZ high; else flat 15:55. One per symbol-day.
No tweak made. The mirror short is not scored in this row. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt4_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1205)
TOPN = 150
LAYERS = ["prior-day 15:15-15:55 trap zone width 0.25-1.0 ATR", "open inside TZ",
          "test of TZ low (<= +0.05, >= -0.15 ATR), session low >= TZ low - 0.3 ATR",
          "bottoming tail (lower wick >= 50%, upper-half close) on test bar or next, close >= TZ low",
          "close within 0.2 ATR of TZ low", "stop test low - 0.05 ATR, target TZ high"]
_ST = {}


def _tz(df, syms):
    fb = U.full_bars(df, symbols=syms)
    if fb is None or not len(fb):
        return None
    x = fb[(fb["tod"] >= 1520) & (fb["tod"] <= 1555)]
    g = x.groupby(["symbol", "date"], sort=True).agg(tzh=("h", "max"), tzl=("l", "min"), nb=("h", "size")).reset_index()
    g = g[g["nb"] >= 6]
    days = fb[["symbol", "date"]].drop_duplicates().sort_values(["symbol", "date"]).reset_index(drop=True)
    days = days.merge(g, on=["symbol", "date"], how="left")
    dt = pd.to_datetime(days["date"])
    same = (days["symbol"] == days["symbol"].shift()) & ((dt - dt.shift()).dt.days <= 7)
    out = pd.DataFrame({"symbol": days["symbol"], "date": days["date"].astype(str),
                        "tzh": days["tzh"].shift().where(same), "tzl": days["tzl"].shift().where(same)})
    return out


def mask(df) -> np.ndarray:
    n = len(df)
    z = np.zeros(n, bool)
    if n == 0:
        return z
    sym = df["symbol"].astype(str).to_numpy()
    ds = U.dstr(df)
    adv = U.f(df, "adv20")
    st0 = U.start(U.key(df))
    u = pd.DataFrame({"symbol": sym[st0], "date": ds[st0], "adv": adv[st0]})
    u["rk"] = u.groupby("date")["adv"].rank(ascending=False, method="first")
    keep = u[(u["rk"] <= TOPN) | u["symbol"].isin(["SPY", "QQQ"])]
    ok_day = pd.MultiIndex.from_arrays([keep["symbol"], keep["date"]])
    inu = pd.MultiIndex.from_arrays([sym, ds]).isin(ok_day)
    if not inu.any():
        return z
    tz = _tz(df, sorted(set(sym[inu])))
    if tz is None:
        return z
    k = U.key(df)
    st = U.start(k)
    s = U.map_day(df, k, tz, ["tzh", "tzl"])
    tzh, tzl = s["tzh"], s["tzl"]
    b = U.base(df)
    h, l, c, lod, atr, opn = b["h"], b["l"], b["c"], b["lod"], b["atr"], b["opn"]
    lw = U.f(df, "lower_wick")
    with np.errstate(invalid="ignore", divide="ignore"):
        w = (tzh - tzl) / atr
        day = inu & (w >= 0.25) & (w <= 1.0) & (opn > tzl) & (opn < tzh)
        test = (l <= tzl + 0.05 * atr) & (l >= tzl - 0.15 * atr)
        tail = (lw >= 0.5) & ((c - l) >= 0.5 * (h - l)) & (h > l) & (c >= tzl)
        test_p = U.lag(test.astype(float), k) == 1.0
        lp = U.lag(l, k)
        m0 = tail & test                      # the test bar is itself the tail
        m1 = tail & test_p & ~m0              # the next bar is the tail
        ep = (test & ~test_p).astype(np.int64)            # a new test episode starts on this bar
        cs = np.cumsum(ep)
        base0 = np.maximum.accumulate(np.where(st, cs - ep, 0))
        first_ep = (cs - base0) == 1                        # still inside the first test episode of the day
        m = day & (m0 | m1) & first_ep & (lod >= tzl - 0.3 * atr) & ((c - tzl) <= 0.2 * atr)
        tl = np.where(m1, np.fmin(l, lp), l)
        stop = tl - 0.05 * atr
        tgt = tzh
        m &= tgt > c
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def stop_price(f, i):
    return U.stash_get(_ST, f, mask, i, 0)


def target_price(f, i, stop):
    return U.stash_get(_ST, f, mask, i, 1)
