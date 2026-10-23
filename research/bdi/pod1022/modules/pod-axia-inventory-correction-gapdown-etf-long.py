"""pod-axia-inventory-correction-gapdown-etf-long - Overnight inventory correction: a small gap down inside the prior
range stops making lows early; buy the first VWAP close, target the prior close (index / sector ETFs, LONG).

Source: Axia Futures / J. Dalton 'overnight inventory' teaching (a lopsided overnight inventory is corrected early in
the session); edgeful-style gap-fill statistics. Not re-fetched this round.
URL: https://ftmo.com/en/futures/blog/market-profile-types-of-opens-and-the-anatomy-of-a-trading-day-2/

VARIANT of 'Reddit R05-gap-fill' (both sides, 16 filter sets, failed). Stated changes: long only, ETFs only (SPY QQQ
IWM DIA + the sector SPDRs), the gap must open INSIDE the prior-day range (inventory, not a new auction), and the
trigger is the end of new lows after 09:45, not the open. Kin: pod-bst018-andrews-gapzone-fade-etf-long,
pod-chan-buy-on-gap-etf-idio (scored with --ref for the duplicate check).

Rules (plain English, LONG):
  1. Gap = open / prior close - 1 between -1.0% and -0.25%, and the open is >= the PDL.
  2. No new session low after 09:45: the 09:45-09:50 bar's low is above the low of day (so the low was made
     09:30-09:45) and the running low of day has not moved since; the session low is >= the PDL.
  3. Entry 09:50-11:00: the FIRST 5-min close above session VWAP (only that bar; if a rule fails there, no trade).
  4. The prior close is >= 1R above the entry (R = entry - stop).
  Stop (GEOM S): session low - 0.05 x ATR5m. Target: the prior close (limit). Exit at 15:55 (the source's 12:30 time
  stop is not available in the harness; the source names 15:55 as its alternative).
No tweak made. Costs per config/default.yaml (applied by the scorer; entries before 10:30 carry the x1.4 cost).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1100)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
LAYERS = ["gap -1.0..-0.25%, open >= PDL", "low made 09:30-09:45, no new low since, LOD >= PDL",
          "first close above VWAP 09:50-11:00", "prior close >= 1R away", "stop LOD - 0.05 ATR5m, target prior close"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _segs(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _base(df):
    """Point-in-time levels per row (all from the bar itself or earlier / completed prior days)."""
    c, atr = _f(df, "close"), _f(df, "atr_d")
    b = dict(c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr, tod=df["tod"].to_numpy(np.int64))
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") / 100 * c               # 5m ATR(14), $
    return b


def _prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
    return f"{y:04d}-{mo:02d}"


def _open_month(m):
    """True only for an OPEN month (never the rule-19 locked block)."""
    L = _lib()
    return m not in L.LOCKED_MONTHS and m in set(L.months())


def mask(df) -> np.ndarray:
    n = len(df)
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


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


@numba.njit(cache=False)
def _kernel(bs, be, tod, c, l, lod, vwap, atr5, opn, pc, pdl, gap):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(bs)):
        i0, i1 = bs[s], be[s]
        if tod[i0] != 950:
            continue
        if not (gap[i0] >= -1.0 and gap[i0] <= -0.25 and opn[i0] >= pdl[i0]):           # (1)
            continue
        L0 = lod[i0]
        eps = 1e-6 * c[i0]
        if not (l[i0] > L0 + eps and L0 >= pdl[i0]):                                     # (2) low set 09:30-09:45
            continue
        for i in range(i0, i1):
            if tod[i] > 1100:
                break
            if abs(lod[i] - L0) > eps:
                break                                                                    # new low after 09:45
            if c[i] > vwap[i]:                                                           # (3) first VWAP close
                sp = L0 - 0.05 * atr5[i]
                R = c[i] - sp
                if R > 0 and pc[i] - c[i] >= R:                                          # (4)
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = pc[i]
                break
    return m, stop, tgt


def _compute(df):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    b = _base(df)
    bs, be = _segs(_key(df))
    return _kernel(bs, be, b["tod"], b["c"], b["l"], b["lod"], b["vwap"], b["atr5"], b["opn"], b["pc"], b["pdl"],
                   _f(df, "gap"))
