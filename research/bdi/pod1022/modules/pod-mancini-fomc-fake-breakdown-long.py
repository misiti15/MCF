"""pod-mancini-fomc-fake-breakdown-long - FOMC-day 'fake breakdown': fade the 14:00 flush once price reclaims the
pre-announcement level (SPY / QQQ, LONG).

Source: Adam Mancini's S&P 500 Trade Companion, 'Standard FOMC fake breakdown and...' (Substack); DayTradingToolkit,
'How to Day Trade an FOMC / Fed Announcement' (the 2 PM reaction is often reversed by 2:30).
URL: https://tradecompanion.substack.com/p/standard-fomc-fake-breakdown-and

NEW (event window; the only earlier FOMC item, CWT26, is the FOMC-eve drift). Sibling of
pod-fomc-2pm-flush-reversal-long (that one triggers on a 2-bar high break above the flush midpoint with the 13:55
close as target; this one needs the RECLAIM of the 14:00 open and a break of the 13:00-14:00 range low).
Rules (plain English, LONG). SYMBOLS: SPY, QQQ. FOMC calendar hardcoded (_r25_util.FOMC, 13 open-history days; the
locked-block meetings are omitted).
  1. Today is an FOMC decision day.
  2. The flush: a bar closing 14:05-14:45 (bars starting 14:00-14:40) trades below both the 14:00 bar open and the
     13:00-14:00 range low (bars closing 13:05-14:00). Flush low = the lowest low of those bars up to the decision
     bar.
  3. Reclaim: the first 5-min bar closing 14:10-15:15 at or after the flush whose close is above the 14:00 open.
  4. The flush low is >= 0.2% below the 14:00 open.
  Entry: the reclaim bar's close. Stop (GEOM S): post-announcement low (lowest low since 14:00) - 0.05%. Target:
  14:00 open + 1.5 x (14:00 open - flush low), or the session high if that is nearer (and above the entry). Flat
  15:55.
14:00 open = the raw 5-min open of the 14:00-14:05 bar (frames_tf/5min); the 13:55 close when it is missing.
Harness limit (declared): the scorer's last entry bar is 15:00, so the reclaim window is 14:10-15:00 (not 15:15).
Small sample (13 events x 2 ETFs): report N; shadow only. The symmetric short mirror is the -short file.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1410, 1500)
SYMBOLS = ["SPY", "QQQ"]
LAYERS = ["FOMC day", "14:00-14:45 trades below the 14:00 open and the 13:00-14:00 low",
          "first close back above the 14:00 open, 14:10-15:00", "flush low >= 0.2% below the 14:00 open",
          "stop post-14:00 low - 0.05%, target open + 1.5 x flush depth or HOD if nearer"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r25_util as U  # noqa: E402

_ST = {}
SGN = 1          # +1 long (flush then reclaim); -1 short mirror (pop then loss)


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def target_price(f, i, stop):
    return _stash(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n:
        return z
    fomc = np.isin(df["date"].astype(str).to_numpy(), U.FOMC)                         # (1)
    if not fomc.any():
        return z
    b = U.base(df)
    k = U.key(df)
    tod = b["tod"]
    s = float(SGN)
    # work in "long space": x -> s * x so the short mirror reuses the same code (highs <-> lows)
    c = s * b["c"]
    lo = s * (b["l"] if SGN > 0 else b["h"])
    hod = s * (b["hod"] if SGN > 0 else b["lod"])
    o1400 = U.CB.at_tod(b["c"], k, tod, 1355)
    t5 = U.CB.tf5(df, symbols=sorted(set(df["symbol"].astype(str))))
    if t5 is not None:
        t5 = t5[t5["tod"] == 1405][["symbol", "date", "open"]]
        kk = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "date": df["date"].to_numpy()})
        op = kk.merge(t5, on=["symbol", "date"], how="left")["open"].to_numpy(float)
        o1400 = np.where(np.isfinite(op), op, o1400)
    o = s * o1400
    st = U.start(k)
    seg = np.cumsum(st) - 1
    rl = np.where((tod >= 1305) & (tod <= 1400), lo, np.inf)
    rlow = pd.Series(rl).groupby(seg).cummin().to_numpy(float)
    rlow = U.CB.at_tod(rlow, k, tod, 1400)                                            # 13:00-14:00 range extreme
    fl = np.where((tod >= 1405) & (tod <= 1445), lo, np.inf)
    flow = pd.Series(fl).groupby(seg).cummin().to_numpy(dtype=float, copy=True)
    flow[~np.isfinite(flow)] = np.nan
    pa = np.where(tod >= 1405, lo, np.inf)
    plow = pd.Series(pa).groupby(seg).cummin().to_numpy(dtype=float, copy=True)
    plow[~np.isfinite(plow)] = np.nan
    with np.errstate(invalid="ignore"):
        flushed = fomc & (flow < o) & (flow < rlow)                                    # (2)
        flushed &= flow <= o - 0.002 * np.abs(o)                                       # (4)
        rec = flushed & (c > o) & (tod >= 1410) & (tod <= 1500)                         # (3)
        nrec = pd.Series(rec.astype(float)).groupby(seg).cumsum().to_numpy(float)
        m = rec & (nrec == 1)
        stp = plow - 0.0005 * np.abs(plow)
        t1 = o + 1.5 * (o - flow)
        tg = np.where((hod > c) & (hod < t1), hod, t1)
        m &= (stp < c) & (tg > c)
        stop[:] = s * stp
        tgt[:] = s * tg
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
