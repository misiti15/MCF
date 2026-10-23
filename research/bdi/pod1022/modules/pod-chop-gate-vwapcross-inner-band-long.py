"""pod-chop-gate-vwapcross-inner-band-long - Choppy-day gate (many VWAP crosses by noon), then buy the afternoon
VWAP -1.5 sigma band reclaim (LONG).

Source: DayTradingToolkit, 'The Trader's Playbook: How to Day Trade the Midday Chop (11 AM-2 PM)' and its 'chop'
glossary entry (tight directionless oscillation; fade failed range moves).
URL: https://daytradingtoolkit.com/strategies/traders-playbook-midday-chop

VARIANT of Reddit R03 VWAP rubber-band fade and config vwap_reversion (2.5 sigma, all days). Stated changes: a chop
day-type gate defined by the VWAP cross count, a tighter 1.5 sigma inner band, an afternoon-only window and a
long-only side.

VWAP and sigma are our own session values (cumulative typical price x 5-min volume from 09:35; sigma = the
volume-weighted standard deviation of typical price; _r212_util).
Rules (plain English, LONG). Universe: SPY, QQQ, IWM, plus the 30 core large caps (_cwt3_bars.LARGE30) when NOT in
play (cumulative relative volume 09:30..bar < 1.2x its 20-session same-time mean).
  1. From 09:35 to the 12:00 bar close, the 5-min close has switched sides of VWAP >= 4 times.
  2. The session range (high - low of day) at the 12:00 bar is <= 0.7 x daily ATR14.
  3. Bar close 12:05-15:00: the bar's low is below VWAP - 1.5 sigma, it closes back above VWAP - 1.5 sigma, and
     RSI(14) (5-min) was < 35 on the prior bar.
  4. The close is above the prior day's low.
  Entry: that close. Stop (GEOM S): the bar low - 0.25 sigma. Target: VWAP (at the signal bar). Flat at 15:55.
Harness deviations (stated): the source's 15:50 time exit is 15:55 here (the scorer's flat time), and the scorer takes
one trade per symbol-day, not the source's maximum of two. Tight targets: the scorer reports R after costs; compare
with the cost share noted in the result. No tweak made. Costs per config/default.yaml.
Educational only - not financial advice."""
import numpy as np

import _r212_util as U

SIDE = "long"
GEOM = "S"
WINDOW = (1205, 1500)
SYMBOLS = U.INDEX3 + U.CORE
LAYERS = [">= 4 VWAP side switches 09:35-12:00", "range at 12:00 <= 0.7 ATR",
          "12:05-15:00 low < VWAP-1.5 sigma, close back above, prior-bar RSI14 < 35", "close > PDL",
          "ETF or core stock with rvc < 1.2", "stop low - 0.25 sigma, target VWAP"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    tod, c, lo = b["tod"], b["c"], b["l"]
    vw, sg = U.vwap_sigma_rows(df)
    l15 = vw - 1.5 * sg
    sw = U.side_switches_by(df, 1200)
    rng12 = U.at_tod(b["hod"] - b["lod"], k, tod, 1200)
    rv = U.rvc(df)
    sym = df["symbol"].astype(str).to_numpy()
    with np.errstate(invalid="ignore"):
        m = (tod >= 1205) & (sw >= 4)                                              # (1)
        m &= rng12 <= 0.7 * b["atr"]                                               # (2)
        m &= (tod <= 1500) & (lo < l15) & (c > l15) & (U.lag(U.f(df, "rsi"), k, 1) < 35)   # (3)
        m &= c > b["pdl"]                                                          # (4)
        m &= np.isin(sym, U.INDEX3) | (rv < 1.2)
        sp = lo - 0.25 * sg
        m &= (sp < c) & (vw > c)
    return np.asarray(m, bool), sp, vw


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
