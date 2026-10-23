"""pod-bbt-bottom-reversal-level-hammer-long - Bottom reversal: a run of lower closes ending in a hammer at a daily
level, on quiet/choppy days (LONG).

Source: Bear Bull Traders / Andrew Aziz, 'Top Reversal and Bottom Reversal' strategy (How to Day Trade for a Living,
reversal chapter; BBT YouTube reversal lessons). Rules from the public material as previously known (not re-fetched
this round).
URL: https://bearbulltraders.com/wp-content/uploads/2023/06/Reversal-Andrew-June-22-2023.pdf

VARIANT of pod-bbt-extreme-rev-mtf-long (also related to CWT05 panic flush V). Stated changes: no EMA9/EMA20 cross,
no VWAP-minus-1-ATR stretch and no volume climax; the trigger is a count of consecutive down bars ending in a hammer
AT a daily level, and the setup runs only on quiet days.

Rules (plain English), bars up to the decision bar i only:
  1. At least 5 consecutive 5-minute bars with close < the previous close, ending at bar i-1 (closes i-6 > i-5 > ...
     > i-1).
  2. Bar i-1 is a hammer: lower_wick >= 0.5 and its low is the running low of day.
  3. Bar i-1's low is within 0.10 x atr_d of the prior-day low, or within 0.05 x atr_d of a round number (step $5 >=
     $100, $1 >= $20, else $0.5; measured from that low).
  4. rsi5 at i-1 <= 15.
  5. Bar i closes above high_{i-1}.
  6. Quiet-day gate at bar i: 0.35 <= breadth <= 0.65 and |spy_fo| <= 0.4.
  Entry: close_i, bar close 10:15-14:30, one trade per symbol-day. Stop (GEOM S): LOD - 0.03 x atr_d. Target: the
  lower of the session VWAP and the 20-bar average at entry; no trade if target - entry < 1.5 x risk. Flat 15:55.
  Proxy (stated): EMA20 is taken as the 5-minute SMA20 (sma20_dist_pct, computed over full sessions across days);
  the frame's own bars start at 09:50 and end at 15:00, so an EMA rebuilt from them would be distorted.
  Costs per config/default.yaml (scorer). No tweak used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1430)
CONTEXT = ["breadth", "spy_fo"]
LAYERS = [">= 5 consecutive lower closes ending at i-1", "i-1 hammer (lower_wick >= 0.5) at the running LOD",
          "i-1 low within 0.10 ATR of PDL or 0.05 ATR of a round number", "rsi5(i-1) <= 15", "close_i > high_{i-1}",
          "0.35 <= breadth <= 0.65, |spy_fo| <= 0.4", "stop LOD - 0.03 ATR, target min(VWAP, SMA20) >= 1.5R",
          "10:15-14:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, lw, lod, pdl, rsi5, atr, br, spy, vw, sma, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 6, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and br[i] >= 0.35 and br[i] <= 0.65 and abs(spy[i]) <= 0.4):
                continue
            j = i - 1
            if not (c[i] > h[j] and rsi5[j] <= 15 and lw[j] >= 0.5 and l[j] <= lod[j] + 1e-9 * c[j]):
                continue
            ok = True
            for k in range(i - 5, i):
                if not (c[k] < c[k - 1]):
                    ok = False
                    break
            if not ok:
                continue
            px = l[j]
            step = 5.0 if px >= 100 else (1.0 if px >= 20 else 0.5)
            rd = abs(px - np.round(px / step) * step) / a
            if not (abs(px - pdl[j]) <= 0.10 * a or rd <= 0.05):
                continue
            sp = lod[i] - 0.03 * a
            tp = min(vw[i], sma[i])
            R = c[i] - sp
            if not (R > 0 and tp - c[i] >= 1.5 * R):
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = tp
            break
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "breadth" not in df or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        lod = c - f("dist_lod_atr") * atr
        pdl = c - f("dist_pdl_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
        sma = c / (1 + f("sma20_dist_pct") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), f("lower_wick"), lod, pdl, f("rsi5"),
                   atr, f("breadth"), f("spy_fo"), vw, sma, WINDOW[0], WINDOW[1])


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
