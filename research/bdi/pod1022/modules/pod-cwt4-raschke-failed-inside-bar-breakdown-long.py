"""pod-cwt4-raschke-failed-inside-bar-breakdown-long - 5-min failed inside-bar breakdown reversal (LONG, 2-6 bar hold).

Source: Linda Raschke (CWT guest ep 48 and later): talk on short-term 5-minute candlestick patterns, which names
'failed inside-bar breakouts' with an average hold of about 2 bars (third-party video summary).
VARIANT (opposite logic) of t5-inside-bar and pod-of-dante-insideday-fail. The change: a 5-min inside bar at a
pullback low whose breakdown fails within 2 bars; trade against the trapped breakdown sellers.
URL: https://videohighlight.com/v/kv2H152ISdM

Rules (plain English). Universe: scorer liquid stocks and ETFs. ATR5 = the frame's 5-min ATR(14) (atrPct x close;
the source's ATR20 is not in the frame, declared).
  1. Pullback: the three bars ending at the mother bar each made a lower high (h[m-2] < h[m-3], h[m-1] < h[m-2],
     h[m] < h[m-1]). Mother-bar range >= 0.8 x ATR5. The next bar is an inside bar (high < mother high, low > mother
     low) with range <= 0.6 x mother range.
  2. Within the next 2 bars after the inside bar, price trades below the inside-bar low by >= 0.02 x ATR5.
  3. Within those same 2 bars, a 5-min close back above the inside-bar high (the failure) - the decision bar (the
     first such close; the breakdown must happen on or before it).
  4. Close > VWAP - 0.5 x ATR5, and (VWAP rising over the last 30 min (6 bars) or SPY from-open >= 0).
  Window: decision bar close 10:00-15:00 ET. Entry: decision bar's close (scorer; the source's next-bar open).
  Stop (GEOM S+ts2): low of the failed breakdown - 0.02 x ATR5. Target: the nearer of mother high + 0.5 x mother
  range and entry + 1R. Time stop: the scorer has no fixed bar-count exit; 'S+ts2' with BAILOUT_BARS = 6 exits at
  the close of bar 6 unless a bar since entry made a high above the entry bar's (declared partial time stop).
  Cost check: the 1R target vs round-trip cost is reported by the scorer (costs in R).
No tweak made. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt4_util as U  # noqa: E402

SIDE = "long"
GEOM = "S+ts2"
BAILOUT_BARS = 6
WINDOW = (1000, 1500)
CONTEXT = ["spy_fo"]
LAYERS = ["3 lower highs into the mother bar, mother range >= 0.8 ATR5", "inside bar <= 0.6 mother range",
          "break below inside low by 0.02 ATR5 within 2 bars", "close above inside high within those 2 bars",
          "close > VWAP - 0.5 ATR5 and (VWAP slope 30m >= 0 or spy_fo >= 0)",
          "stop breakdown low - 0.02 ATR5, target min(mother high + 0.5 range, 1R), 6-bar bailout"]
_ST = {}


def mask(df) -> np.ndarray:
    n = len(df)
    z = np.zeros(n, bool)
    if n == 0:
        return z
    k = U.key(df)
    b = U.base(df)
    h, l, c = b["h"], b["l"], b["c"]
    a5 = b["atr5"]
    H = {j: U.lag(h, k, j) for j in range(1, 7)}
    L = {j: U.lag(l, k, j) for j in range(1, 7)}
    C = {j: U.lag(c, k, j) for j in range(1, 3)}
    H[0], L[0] = h, l
    a5p = {j: U.lag(a5, k, j) for j in (1, 2)}
    vw = b["vwap"]
    vw6 = U.lag(vw, k, 6)
    spy = U.f(df, "spy_fo")
    m = np.zeros(n, bool)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        for d in (1, 2):                      # inside bar at lag d, mother at lag d+1
            ib, mb = d, d + 1
            ih, il, mh, ml = H[ib], L[ib], H[mb], L[mb]
            mr = mh - ml
            ok = (H[mb] < H[mb + 1]) & (H[mb + 1] < H[mb + 2]) & (H[mb + 2] < H[mb + 3])
            ok &= mr >= 0.8 * a5p.get(ib, a5)
            ok &= (ih < mh) & (il > ml) & ((ih - il) <= 0.6 * mr)
            ref = a5p[ib]
            if d == 1:
                blow = l
                ok &= blow < il - 0.02 * ref
            else:
                blow = np.fmin(L[1], l)
                ok &= blow < il - 0.02 * ref
                ok &= ~(C[1] > ih)                       # first failure close
            ok &= c > ih
            s = blow - 0.02 * ref
            t = np.fmin(mh + 0.5 * mr, c + (c - s))
            new = ok & ~m
            stop = np.where(new, s, stop)
            tgt = np.where(new, t, tgt)
            m |= ok
        m &= c > vw - 0.5 * a5
        m &= ((vw - vw6) >= 0) | (spy >= 0)
        m &= np.isfinite(stop) & np.isfinite(tgt) & (tgt > c) & (stop < c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def stop_price(f, i):
    return U.stash_get(_ST, f, mask, i, 0)


def target_price(f, i, stop):
    return U.stash_get(_ST, f, mask, i, 1)
