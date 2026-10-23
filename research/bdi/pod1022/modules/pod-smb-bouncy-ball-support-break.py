"""pod-smb-bouncy-ball-support-break - Multi-tested flat low of day breaks (bouncy ball / tidal wave / poor low) (SHORT).
Config POOR (tail-less touches of a flat LOD, trigger-bar-high stop).

Source: Lance Breitstein 'bouncy ball' short (CTE research sheet, Market Wizards: The Next Generation); SMB 'Tidal
Wave'; auction-market 'poor low' (LuxAlgo, MarketCalls, Trader Dante). MERGED from pod-smb-bouncy-ball-support-break
and the short side of pod-of-poor-extreme-break.
URL: https://completetradersedge.com/wp-content/uploads/2026/09/CTE-Research-Sheet-Lance-Breitstein-market-wizards-next-generation.pdf

VARIANT of CWT04 backside lower-high short (failed) and R07 / R15 level breaks. Stated change: the trigger is a break
of a HORIZONTAL low of day tested >= 3 times without tails (descending-triangle structure), no prior run-up needed,
measured-move target. Short mirror of pod-wt-flat-top-poor-high-long (config POOR).

Pre-declared values inside the source ranges (no tuning): touch tolerance 0.05 x daily ATR (range 0.03-0.08), break
buffer 0.04 x daily ATR (0.03-0.05), trigger volumeRatio >= 1.3 (1.2-1.3). One config (POOR) only.

Rules (plain English), decision bar i:
  1. S = the running low of day as of bar i-1 (close - dist_lod_atr x atr_d, includes the pre-09:50 bars). S was first
     set >= 6 bars (30 min) before bar i (if it was set before 09:50 that counts). After the bar that set it, >= 2 more
     separate touch episodes (a bar with low <= S + 0.05 x daily ATR after a bar that did not touch); no close below
     S by construction (S is still the LOD). Every touch bar has lower_wick < 0.25 (poor low = no tails).
  2. vwapDistPct < 0 and fromOpen < 0 at bar i; spy_fo < 0.
  3. Trigger: close_i < S - 0.04 x daily ATR with volumeRatio_i >= 1.3.
  Entry: close_i, bar close 10:30-15:00, one per symbol-day. Stop (GEOM S): trigger-bar high + 1c. Target: S - (first
  bounce high - S), the first bounce high = the highest high between the setting bar and the second touch episode;
  when that target is not below the entry, 1R. Flat 15:55. Costs in (scorer).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1500)
CONTEXT = ["spy_fo"]
LAYERS = ["flat LOD set >= 30 min ago, >= 2 more touch episodes within 0.05 ATR, touch bars lower_wick < 0.25",
          "vwapDistPct < 0, fromOpen < 0, spy_fo < 0", "close < LOD - 0.04 ATR with volumeRatio >= 1.3",
          "stop trigger high + 1c, target LOD - first bounce height (else 1R)", "10:30-15:00 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, lod, lw, vr, vd, fo, spy, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 3, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and vd[i] < 0 and fo[i] < 0 and spy[i] < 0 and vr[i] >= 1.3):
                continue
            S = lod[i - 1]
            if not (c[i] < S - 0.04 * a):
                continue
            eps = 1e-4 * a
            f = i - 1
            while f - 1 >= i0 and lod[f - 1] <= S + eps:
                f -= 1
            # f = first frame bar whose running LOD equals S; if bar f's low is above S the LOD was set pre-09:50
            if not (l[f] <= S + eps):
                f = i0 - 1
            if i - f < 6:
                continue
            ok = True
            if f >= i0 and lw[f] >= 0.25:
                ok = False
            eps_n = 0
            sec = -1
            prev_t = True                       # the setting bar is a touch
            for k in range(f + 1, i):
                t = l[k] <= S + 0.05 * a
                if t:
                    if lw[k] >= 0.25:
                        ok = False
                        break
                    if not prev_t:
                        eps_n += 1
                        if eps_n == 1:
                            sec = k
                prev_t = t
            if not ok or eps_n < 2:
                continue
            fb = -1e18
            for k in range(max(f + 1, i0), sec):
                fb = max(fb, h[k])
            sp = h[i] + 0.01
            if not (sp > c[i]):
                continue
            tp = S - (fb - S)
            if not (tp < c[i]):
                tp = c[i] - (sp - c[i])
            m[i] = True
            stop[i] = sp
            tgt[i] = tp
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore"):
        lod = c - f("dist_lod_atr") * atr
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), lod, f("lower_wick"),
                   f("volumeRatio"), f("vwapDistPct"), f("fromOpen"), f("spy_fo"), atr, WINDOW[0], WINDOW[1])


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
