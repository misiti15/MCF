"""pod-vwap-1sd-band-ride-pullback-long - Trend-day band ride: a pullback to the VWAP +1 sigma band (not to VWAP)
holds (LONG).

Source: LuxAlgo, 'VWAP Bands' concept (price that opens above the +1 band and refuses to close inside it is riding the
band: join pullbacks to the first trend-side band, do not fade strength).
URL: https://www.luxalgo.com/library/concept/vwap-bands/

VARIANT of pod-bbt-orb-vwap-pullback-atr-room-long and pod-dalton-open-drive-pullback. Stated change: the support is
the +1 sigma VWAP band, the day-type gate is band riding, the entry window is midday / afternoon and the target is the
+2 sigma band.

VWAP and sigma are our own session values: cumulative typical price x 5-min volume from 09:35, sigma = the
volume-weighted standard deviation of typical price (_r212_util; the VWAP matches the frame's to < 0.0001%).
Rules (plain English, LONG). Universe: SPY, QQQ, IWM, DIA, plus the 30 core large caps (_cwt3_bars.LARGE30) when in
play (pre-declared: cumulative relative volume 09:30..bar >= 1.5x its 20-session same-time mean).
  1. Every 5-min close from 10:00 up to the signal bar is above VWAP, and at least 6 closes after 10:00 (signal bar
     included) are above VWAP + 1 sigma.
  2. VWAP is higher than 12 bars (one hour) earlier.
  3. Bar close 11:00-14:45: the bar's low touches or pierces VWAP + 1 sigma by at most 0.25 sigma, and the bar
     closes back above VWAP + 1 sigma.
  4. That bar's volume <= its 20-bar average (volumeRatio <= 1; a quiet pullback).
  Entry: that close. Stop (GEOM S): the lower of VWAP + 0.5 sigma and the bar low - 0.05 x daily ATR. Target: the
  VWAP + 2 sigma band at the fill (the signal bar's close, which is the fill price). Flat at 15:55.
No tweak made. Costs per config/default.yaml. Educational only - not financial advice."""
import numpy as np
import pandas as pd

import _r212_util as U

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1445)
SYMBOLS = U.ETF4 + U.CORE
LAYERS = ["all closes since 10:00 > VWAP, >= 6 closes > +1 sigma", "VWAP rising over 12 bars",
          "11:00-14:45 low tags +1 sigma (<= 0.25 sigma through), close back above", "volumeRatio <= 1",
          "ETF or in-play core stock (rvc >= 1.5)", "stop min(VWAP+0.5 sigma, low-0.05 ATR), target +2 sigma"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    tod, c, lo = b["tod"], b["c"], b["l"]
    vw, sg = U.vwap_sigma_rows(df)
    u1, u2 = vw + sg, vw + 2 * sg
    rv = U.rvc(df)
    sym = df["symbol"].astype(str).to_numpy()
    st = U.start(k)
    grp = np.cumsum(st) - 1
    with np.errstate(invalid="ignore"):
        after = tod >= 1000
        below = (after & ~(c > vw)).astype(int)                          # NaN VWAP counts as a failure
        nbelow = pd.Series(below).groupby(grp).cumsum().to_numpy()
        above1 = ((tod > 1000) & (c > u1)).astype(int)
        nabove1 = pd.Series(above1).groupby(grp).cumsum().to_numpy()
        m = (nbelow == 0) & (nabove1 >= 6)                                                 # (1)
        m &= vw > U.lag(vw, k, 12)                                                         # (2)
        m &= (tod >= 1100) & (tod <= 1445) & (lo <= u1) & (lo >= u1 - 0.25 * sg) & (c > u1)  # (3)
        m &= U.f(df, "volumeRatio") <= 1.0                                                 # (4)
        m &= np.isin(sym, U.ETF4) | (rv >= 1.5)
        sp = np.minimum(vw + 0.5 * sg, lo - 0.05 * b["atr"])
        m &= (sp < c) & (u2 > c)
    return np.asarray(m, bool), sp, u2


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
