"""pod-dalton-open-drive-pullback-OF-short - Open-drive day (open never revisited): continuation entry with the stop at
the opening price (SHORT, config OF).

Source: J. Dalton 'Mind Over Markets' open types (NexusFi 'Opening Types'); FTMO / LuxAlgo open types; ATAS 'Open
Drive' strategy article. Merged from pod-dalton-open-drive-pullback (config D) and pod-of-open-drive-no-retest
(config OF).
URL: https://nexusfi.com/articles/trading/Opening-Types

VARIANT of the failed 'P: first pullback holding VWAP/EMA9 after a morning low', wi-vwap-first-pullback and the SMB
opening-drive first-pullback idea. Stated change: an open-drive day-type gate (the stock never traded meaningfully
back through its opening print) with Dalton's invalidation stop at the open. Different from
pod-edgeful-green-first15-open-hold-long (that buys at the open level).
Files: pod-dalton-open-drive-pullback-{D,OF}-{long,short}; this file = CONFIG and SIDE below. Short = exact mirror
(open-drive-down day: HOD <= open + 0.04 ATR, breadth_open <= 0.5, open < PDL for OF, rsi5 >= 60, ...).

Values: open = close / (1 + fromOpen%); LOD / HOD so far from dist_lod_atr / dist_hod_atr (they include the
09:30-09:45 bars); VWAP = close / (1 + vwapDistPct%); PDH = close + dist_pdh_atr x atr_d (prior completed day).
Rules (plain English; long shown):
  1. Open drive: low of day so far >= open - 0.04 x atr_d at the entry bar, and some frame bar closing before 10:30
     (up to this bar) had fromOpen >= +0.6 x atr_d / close (in %).
  2. Config D: |gap| <= 2%.  Config OF: today's open above the prior-day high.
  3. breadth_open >= 0.5 at the entry bar.
  4. Trigger, bar close 10:00-11:30:
     D - the first pullback after the drive = the first run of bars with rsi5 <= 40; every bar of that run must close
     above open + 0.25 x (HOD - open) and above VWAP; then the first close above the prior bar's high (one try).
     OF - a pullback of >= 0.20 x atr_d from the current HOD in which every close stayed above VWAP, then the first
     close above the prior HOD (a new-HOD close) with volumeRatio >= 1.0 (one try).
  Entry: that close. Stop (GEOM S): open - 0.035 x atr_d. Config D skips when the stop is > 1.5 x 0.25 x atr_d away.
  No target: held to 15:55 (flat). Costs per config/default.yaml (scorer).
Pre-declared choices (source ranges, set once, no tuning on valid): LOD tolerance 0.04 ATR (0.03-0.05), breadth_open
0.5 (0.5-0.55), stop buffer 0.035 ATR (0.02-0.05). Deviations, declared: (a) the source's holdtr exit (1R trail) is
not available with a structural stop, so the trade holds to 15:55 with the open stop; (b) the 1.5 x 0.25 ATR stop
cap is impossible for config OF (its entry is a new HOD >= 0.6 ATR above the open), so OF keeps the open stop without
the cap.
Educational only - not financial advice."""
SIDE = "short"
CONFIG = "OF"
GEOM = "S"
WINDOW = (1000, 1130)
CONTEXT = ["breadth_open"]
LAYERS = ["LOD >= open - 0.04 ATR, fromOpen >= 0.6 ATR before 10:30", "D: |gap| <= 2% / OF: open > PDH",
          "breadth_open >= 0.5", "D: first rsi5<=40 pullback above 25% retrace and VWAP, then close > prior high / "
          "OF: >= 0.2 ATR pullback holding VWAP, then first new-HOD close with volumeRatio >= 1",
          "stop open - 0.035 ATR (D: skip > 0.375 ATR), hold to 15:55", "10:00-11:30 ET"]

LOD_TOL = 0.04
BREADTH = 0.5
STOP_BUF = 0.035

import numba
import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _gcum(x, k):
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


@numba.njit(cache=False)
def _kernel(b, e, h, l, c, hod, op, vw, rsi5, vr, atr, drove, ok, cfg_d):
    """Sign-normalised (short: negated prices, hod = -LOD, rsi5 = 100 - rsi5). One try per symbol-day."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        done = False
        armed = False
        inrun = False
        lowsince = np.inf
        held = True
        for i in range(i0, i1):
            if done:
                break
            if cfg_d:
                if not drove[i]:
                    continue
                if not armed:
                    if rsi5[i] <= 40:
                        armed = True
                        inrun = True
                        if not (c[i] > op[i] + 0.25 * (hod[i] - op[i]) and c[i] > vw[i]):
                            done = True
                    continue
                if inrun:
                    if rsi5[i] <= 40:
                        if not (c[i] > op[i] + 0.25 * (hod[i] - op[i]) and c[i] > vw[i]):
                            done = True
                            continue
                    else:
                        inrun = False
                if i > i0 and c[i] > h[i - 1]:
                    done = True
                    m[i] = ok[i]
            else:
                if i == i0:
                    lowsince = l[i]
                    held = c[i] > vw[i]
                    continue
                prevhod = hod[i - 1]
                if h[i] >= prevhod:                      # the HOD moves: test the close, then a new swing starts
                    if c[i] > prevhod and drove[i] and held and (prevhod - lowsince) >= 0.20 * atr[i] \
                            and vr[i] >= 1.0:
                        done = True
                        m[i] = ok[i]
                        continue
                    lowsince = l[i]
                    held = c[i] > vw[i]
                else:
                    lowsince = min(lowsince, l[i])
                    held = held and (c[i] > vw[i])
    return m


def mask(df) -> np.ndarray:
    _ST.clear()
    if not len(df) or "breadth_open" not in df:
        return np.zeros(len(df), dtype=bool)
    long_ = SIDE == "long"
    sg = 1.0 if long_ else -1.0
    cfg_d = CONFIG == "D"
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        op = c / (1 + _f(df, "fromOpen") / 100)
        st = _start(k)
        op = op[st][np.cumsum(st) - 1]
        vw = c / (1 + _f(df, "vwapDistPct") / 100)
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        dflag = (tod < 1030) & (sg * _f(df, "fromOpen") >= 0.6 * atr / c * 100)
        drove = _gcum(dflag, k) > 0
        bo = _f(df, "breadth_open")
        if long_:
            ok = (lod >= op - LOD_TOL * atr) & (bo >= BREADTH)
            pdh = c + _f(df, "dist_pdh_atr") * atr
            gate_of = op > pdh[st][np.cumsum(st) - 1]
            stop = op - STOP_BUF * atr
        else:
            ok = (hod <= op + LOD_TOL * atr) & (bo <= 1 - BREADTH)
            pdl = c - _f(df, "dist_pdl_atr") * atr
            gate_of = op < pdl[st][np.cumsum(st) - 1]
            stop = op + STOP_BUF * atr
        ok &= (np.abs(_f(df, "gap")) <= 2.0) if cfg_d else gate_of
        if cfg_d:
            ok &= sg * (c - stop) <= 1.5 * 0.25 * atr
        ok &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        rs = _f(df, "rsi5") if long_ else 100 - _f(df, "rsi5")
    if long_:
        H, L, C, X, O, V = h, l, c, hod, op, vw
    else:
        H, L, C, X, O, V = -l, -h, -c, -lod, -op, -vw
    b, e = _segments(k)
    m = _kernel(b, e, H, L, C, X, O, V, rs, _f(df, "volumeRatio"), atr, np.asarray(drove, np.bool_),
                np.asarray(ok, np.bool_), cfg_d)
    _ST[id(df)] = (stop,)
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")
