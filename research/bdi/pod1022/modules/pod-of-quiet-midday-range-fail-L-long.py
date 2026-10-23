"""pod-of-quiet-midday-range-fail-L-long - Quiet afternoon: failed poke out of the midday box, fade back inside (LONG, config L).

Source: Bookmap blog 'Running the stops: how it happens and how to trade the aftermath'; NexusFi 'Failed Auction';
Sunmool 'NY Lunch Model Backtesting' TradingView research script; tosindicators lunch study.
URL: https://bookmap.com/blog/running-the-stops-how-it-happens-and-how-to-trade-the-aftermath

VARIANT of CWT46 afternoon breakout of the 11:30-13:30 range (LONG the break in a strong mover, failed),
bdi-reddit-level-sweep-reclaim / bdi-reddit1012-liquidity-sweep (OR30 / HTF levels) and R15. Stated change: the
opposite regime and side - a non-mover on a quiet tape, fading a failed afternoon poke out of the midday box.
Rules (plain English, SHORT; LONG mirrors under the box low). Config L:
  1. Box = the high / low of the bars closing 12:05-13:00 ET; box width <= 0.3 x atr_d.
  2. |fromOpen| < 0.8 x atr_d / close; the day's range at the 13:00 bar <= 1.2 x atr_d; |spy_fo| < 0.4%.
  3. From 13:05 to 15:00: a poke bar's high exceeds the box high by 0.03-0.15 x atr_d with volumeRatio < 1.2,
     and that bar (or the next) closes back inside the box with the close below that bar's midpoint. No close
     above the box high before the poke bar, and the high since the box ended stays <= box high + 0.15 x atr_d.
  Entry: the close back inside. Stop (GEOM S): the poke high + 0.03 x atr_d. Target: the opposite box edge.
  One trade per symbol-day; flat 15:55.
The source gives ranges (fromOpen 0.8-1.0 ATR, stop buffer 0.03-0.05 ATR); fixed before scoring: config M uses 1.0 and
0.05, config L uses 0.8 and 0.03. No other tweak.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; prior-day
values come from completed days only.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1305, 1500)
CONTEXT = ['spy_fo']
LAYERS = ['box (1205, 1300) width <= 0.3 ATR', '|fromOpen| < 0.8 ATR, day range at 13:00 <= 1.2 ATR', '|spy_fo| < 0.4%', 'poke 0.03-0.15 ATR beyond the box, vr < 1.2', 'close back inside below/above the bar midpoint', 'stop poke + 0.03 ATR, target the opposite box edge']

import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each group k."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _gcummax(x, k):
    return pd.Series(np.asarray(x, float)).groupby(k).cummax().to_numpy(float)


def _gcummin(x, k):
    return pd.Series(np.asarray(x, float)).groupby(k).cummin().to_numpy(float)


def _runlen(cond, k):
    """Number of consecutive True bars ending at (and including) each bar, within the symbol-day."""
    cond = np.asarray(cond, bool)
    grp = np.cumsum(~cond | _start(k))           # new block whenever cond is False or a new day starts
    cnt = pd.Series(cond.astype(float)).groupby(grp).cumsum().to_numpy(float)
    return np.where(cond, cnt, 0.0)


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to its symbol-day. Used only on rows with tod > T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr          # prior completed day's high
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") * c / 100                # 5-minute ATR(14), $
    return b


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    if s is None or s[j] is None:
        return float("nan")
    return float(s[j][i])


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)

BOX = (1205, 1300)
WMAX = 0.3
FOMAX = 0.8
STOPK = 0.03
TGT = "edge"


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    vr = _f(df, "volumeRatio")
    with np.errstate(invalid="ignore", divide="ignore"):
        inb = (tod >= BOX[0]) & (tod <= BOX[1])
        hb = np.where(inb, h, np.nan)
        lb = np.where(inb, l, np.nan)
        bh = _at(_gcummax(np.where(inb, h, -np.inf), k), k, tod, BOX[1])
        bl = _at(_gcummin(np.where(inb, l, np.inf), k), k, tod, BOX[1])
        bh[~np.isfinite(bh)] = np.nan
        bl[~np.isfinite(bl)] = np.nan
        w = bh - bl
        rng13 = _at(b["hod"] - b["lod"], k, tod, 1300)
        m = (tod > BOX[1]) & (w <= WMAX * atr) & (w > 0)                                  # (1)
        m &= np.abs(_f(df, "fromOpen")) < FOMAX * atr / c * 100
        m &= rng13 <= 1.2 * atr
        m &= np.abs(_f(df, "spy_fo")) < 0.4                                               # (2)
        after = tod > BOX[1]
        mid_bar = (h + l) / 2
        if SIDE == "short":
            ext = np.where(after, h, -np.inf)
            mx = _gcummax(ext, k)                                                         # high since box end
            outc = _gcum((after & (c > bh)).astype(float), k)                              # closes above box so far
            poke = (h >= bh + 0.03 * atr) & (h <= bh + 0.15 * atr) & (vr < 1.2)
            back = (c < bh) & (c < mid_bar)
            same = poke & back & (outc == 0)
            nxt = (_lag(poke.astype(float), k) == 1) & back & (_lag(c, k) > bh) & (_lag(outc, k) == 1) \
                & (_lag(tod, k) > BOX[1])
            ph = np.where(same, h, np.fmax(_lag(h, k), h))
            m &= (same | nxt) & (mx <= bh + 0.15 * atr)
            stop = ph + STOPK * atr
            tgt = (bh + bl) / 2 if TGT == "mid" else bl
            m &= tgt < c
        else:
            ext = np.where(after, l, np.inf)
            mn = _gcummin(ext, k)
            outc = _gcum((after & (c < bl)).astype(float), k)
            poke = (l <= bl - 0.03 * atr) & (l >= bl - 0.15 * atr) & (vr < 1.2)
            back = (c > bl) & (c > mid_bar)
            same = poke & back & (outc == 0)
            nxt = (_lag(poke.astype(float), k) == 1) & back & (_lag(c, k) < bl) & (_lag(outc, k) == 1) \
                & (_lag(tod, k) > BOX[1])
            pl = np.where(same, l, np.fmin(_lag(l, k), l))
            m &= (same | nxt) & (mn >= bl - 0.15 * atr)
            stop = pl - STOPK * atr
            tgt = (bh + bl) / 2 if TGT == "mid" else bh
            m &= tgt > c
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
