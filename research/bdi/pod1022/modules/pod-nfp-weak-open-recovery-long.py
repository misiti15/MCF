"""pod-nfp-weak-open-recovery-long - Jobs-Friday weak open, then recovery: NFP first-hour selloff, VWAP reclaim (LONG).

Source: Eric Parnell, Seeking Alpha 'Trading Jobs Friday' (stocks tend to open weak on jobs day, then recover);
OneOption 'Market Reversal Friday'.
URL: https://seekingalpha.com/article/3986677-trading-jobs-friday

VARIANT of pod-bespoke-hotcpi-gapdown-first-hour-bounce-long. Stated change: the event is the Employment Situation
(NFP) release day and the trigger is a first-hour selloff (not necessarily a gap) followed by a SPY VWAP reclaim.
Opposite day-type side to pod-gao-newsday-first30-hold-long (which buys release-day strength).

Rules (plain English, LONG), SYMBOLS SPY, QQQ, IWM. Conditions 1-4 are measured on SPY:
  1. Today is an NFP release day (BLS calendar, published in advance; list _r212_util.NFP).
  2. Weak first hour: SPY's 09:30-10:30 low is >= 0.40% below today's open, or >= 0.40% below the prior close.
  3. Daily trend: SPY's close yesterday > its daily SMA50 (both as of D-1, completed days).
  4. After 10:30 and until 13:00 ET: SPY's 5m close crosses above session VWAP (previous bar at or below VWAP, first
     above-bar closing at 10:35 or later) and the next bar also closes above VWAP ("holds for 2 bars"); SPY has made no
     new session low on any bar closing after 10:45 (the running low is unchanged since the 10:45 bar).
  Entry: the close of that second bar, on SPY / QQQ / IWM (each must still be below its own first-hour high).
  Stop (GEOM S): the symbol's own first-hour low - 0.05%, capped so the risk is at most 1.2 x the 5m ATR(14)
  (atrPct x close; read literally as "ATR5m-based"). Target: the symbol's own first-hour high; else flat 15:55.
Point-in-time: first-hour high / low are the running HOD / LOD on the 10:30 bar (they include 09:30-09:45); VWAP and
5m ATR are frame columns; SMA50 / prior close come from completed daily bars. No lookahead.
Low frequency (~12 NFP days a year, fewer pass the gates; x3 symbols): N is reported as is; no pooling with other
08:30 releases in this module. Score (r3_12): 3 trades on one day (2026-06-05). No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
import numpy as np

import _r212_util as U

SIDE = "long"
GEOM = "S"
WINDOW = (1040, 1305)
SYMBOLS = ["SPY", "QQQ", "IWM"]
LAYERS = ["NFP release day", "SPY 09:30-10:30 low >= 0.40% below open or prior close", "SPY D-1 close > SMA50",
          "SPY 5m VWAP reclaim held 2 bars, 10:35-13:00, no new low after 10:45",
          "stop own first-hour low - 0.05% (risk <= 1.2 ATR5m), target own first-hour high, flat 15:55"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    tod, c = b["tod"], b["c"]
    ds = U.dstr(df)
    sym = df["symbol"].astype(str).to_numpy()
    nfp = np.isin(ds, U.NFP)
    H = U.at_tod(b["hod"], k, tod, 1030)
    L = U.at_tod(b["lod"], k, tod, 1030)
    L45 = U.at_tod(b["lod"], k, tod, 1045)
    dd = U.map_daily(df, k, ["d_close_1", "sma50_1"])
    above = c > b["vwap"]
    trig = {}
    idx = np.flatnonzero((sym == "SPY") & nfp)
    for d in np.unique(ds[idx]):
        r = idx[ds[idx] == d]
        r = r[np.argsort(tod[r], kind="mergesort")]
        j0 = r[0]
        with np.errstate(invalid="ignore"):
            weak = (L[r[-1]] <= b["opn"][j0] * 0.996) or (L[r[-1]] <= b["pc"][j0] * 0.996)
            up = dd["d_close_1"][j0] > dd["sma50_1"][j0]
        if not (weak and up):
            continue
        for q in range(2, len(r)):
            i, i1, i2 = r[q], r[q - 1], r[q - 2]
            if tod[i] > 1300:
                break
            if tod[i1] < 1035 or tod[i2] < 1030:
                continue
            if tod[i] >= 1050 and b["lod"][i] < L45[i] - 1e-9 * c[i]:
                break                                                   # new session low after 10:45: stop looking
            if above[i] and above[i1] and not above[i2]:
                trig[d] = int(tod[i])
                break
    tt = np.array([trig.get(d, -1) for d in ds]) if n else np.zeros(0, int)
    with np.errstate(invalid="ignore"):
        m = nfp & (tod == tt) & (c < H)
        sp = np.maximum(L * (1 - 0.0005), c - 1.2 * b["atr5"])
        m &= sp < c
        tg = H
    return np.asarray(m, bool), sp, tg


def mask(df) -> np.ndarray:
    try:
        m, sp, tg = _compute(df)
    except (KeyError, FileNotFoundError):
        m, sp, tg = np.zeros(len(df), bool), np.full(len(df), np.nan), np.full(len(df), np.nan)
    _ST.clear()
    _ST[id(df)] = (sp, tg)
    return m


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
