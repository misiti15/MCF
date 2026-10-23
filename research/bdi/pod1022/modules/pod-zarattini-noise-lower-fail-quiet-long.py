"""pod-zarattini-noise-lower-fail-quiet-long - Failed break below the lower noise-area boundary on a quiet day (LONG).

Source: Zarattini, Aziz, Barbon, 'Beat the Market: An Effective Intraday Momentum Strategy for SPY' (noise area =
open +/- the 14-day average absolute move from the open at that time of day; lower band uses min(open, prior close)),
summarised by Quantified Strategies; Concretum Bands TradingView implementation.
URL: https://quantifiedstrategies.substack.com/p/systematic-intraday-trend-following

VARIANT of t7-noise-band (retired) and noise-band-simple (failed), which trade WITH the boundary break. Stated change:
the opposite logic on quiet days - a break of the lower boundary that closes back inside within 2 bars is bought,
back toward VWAP.

Rules (plain English). Symbols SPY, QQQ, IWM, DIA.
  Band: for each bar time, sigma_tod = mean over the 14 PRIOR sessions of |close at that time / that day's 09:30
  open - 1| (_r39_util.noise_sigma, full-session 5m bars). LB = min(open, prior close) x (1 - sigma_tod), each bar
  against its own time's band.
  1. Quiet gate: |gap| <= 0.30%, and the prior-day range <= the median of the 20 daily ranges ending D-1 (lib.daily).
  2. Within the last 2 bars (i-1 or i-2) a bar closed below its LB.
  3. This bar closes back above LB and above the prior bar's high.
  4. Every break bar has volumeRatio <= 1.5 (no climactic selling), and spy_fo > -0.6% on this bar.
  Entry: the reclaim bar's close, 10:00-14:30, first per symbol-day (scorer).
  Stop (GEOM S): the lowest low of the break bars - 0.05 x daily ATR. Target: session VWAP at entry; no trade when
  VWAP < entry + 0.5 x risk. Otherwise flat at 15:55.
Control (separate module ...-ctrl-nonquiet): the same reclaim on non-quiet days.
No tweak used. 1 configuration (+1 control). Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r39_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = ["spy_fo"]
QUIET = True
LAYERS = ["quiet: |gap| <= 0.3%, prior range <= 20d median", "close below noise LB in the last 2 bars",
          "close back above LB and above prior bar high", "break-bar volumeRatio <= 1.5, spy_fo > -0.6",
          "stop break low - 0.05 ATR, target VWAP (>= 0.5R), flat 15:55"]
_ST = {}


def compute(df, quiet=True):
    n = len(df)
    nan = np.full(n, np.nan)
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool), nan, nan
    b = U.base(df)
    k = U.key(df)
    sig = U.noise_sigma(df)
    d = U.map_daily(df, ["rng1", "rngmed201"])
    c, h, l, atr = b["c"], b["h"], b["l"], b["atr"]
    vr = U.f(df, "volumeRatio")
    with np.errstate(invalid="ignore", divide="ignore"):
        lb = np.fmin(b["opn"], b["pc"]) * (1.0 - sig)
        below = c < lb
        b1 = U.lag(below.astype(float), k, 1) == 1.0
        b2 = U.lag(below.astype(float), k, 2) == 1.0
        l1, l2 = U.lag(l, k, 1), U.lag(l, k, 2)
        v1, v2 = U.lag(vr, k, 1), U.lag(vr, k, 2)
        brk = b1 | b2
        vol_ok = (~b1 | (v1 <= 1.5)) & (~b2 | (v2 <= 1.5))
        blow = np.fmin(np.where(b1, l1, np.inf), np.where(b2, l2, np.inf))
        q = (np.abs(U.f(df, "gap")) <= 0.30) & (d["rng1"] <= d["rngmed201"])
        gate = q if quiet else (~q & np.isfinite(d["rngmed201"]) & np.isfinite(U.f(df, "gap")))
        m = gate & brk & (c > lb) & (c > U.lag(h, k, 1)) & vol_ok & (U.f(df, "spy_fo") > -0.6)
        stop = blow - 0.05 * atr
        risk = c - stop
        vw = b["vwap"]
        m &= np.isfinite(stop) & (risk > 0) & (vw >= c + 0.5 * risk)
        tod = b["tod"]
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, bool), np.where(m, stop, np.nan), np.where(m, vw, np.nan)


def mask(df):
    m, s, t = compute(df, QUIET)
    _ST.clear()
    _ST[id(df)] = (s, t)
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
