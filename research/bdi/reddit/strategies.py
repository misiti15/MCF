"""Reddit strategies as testable full-day rules (NOTES.md section 2). Each builder returns, for side s (+1 long /
-1 short, the short being the mirror), a dict: ev (trigger rows), sx (structural-exit condition at a bar close, or
None), tg (structural target price, or None). `p` is the strategy's one main parameter (plateau grid in PARAMS).
Only live-frame information known at the bar close is used. Educational only - not financial advice."""
from __future__ import annotations

import numpy as np

import numba

from engine import Data

NAN = np.nan


def _once(D: Data, ev):
    """Only the first time the event happens in the symbol-day (e.g. 'first break')."""
    cnt = D.grp_cumsum(ev.astype(float))
    return ev & (cnt == 1)


def orb(D: Data, s, p):
    """R01 ORB30: first close beyond the 09:30-10:00 range (+p ATR buffer) after 10:00. S: close back inside the OR."""
    c, a = D.c, D.atr
    lvl = D.F("orh") + p * a if s > 0 else D.F("orl") - p * a
    x = s * (c - lvl)
    px = D.prev(x)
    with np.errstate(invalid="ignore"):
        ev = (x > 0) & (px <= 0) & (D.tod > 1000)
        sx = s * (c - (D.F("orh") if s > 0 else D.F("orl"))) < 0
    return {"ev": _once(D, ev), "sx": sx, "tg": None}


def vwap_reclaim(D: Data, s, p):
    """R02 VWAP reclaim: close crosses to the trade side of VWAP after >= p consecutive closes on the other side
    (long: reclaim after p bars below; short: VWAP loss after p bars above). S: close back across VWAP."""
    z = D.F("z")
    other = (s * z < 0).astype(float)
    # run length of consecutive 'other side' closes ending at the previous bar
    run = _runlen(D, other)
    prun = D.prev(run)
    with np.errstate(invalid="ignore"):
        ev = (s * z > 0) & (prun >= p)
        sx = s * z < 0
    return {"ev": ev, "sx": sx, "tg": None}


def _runlen(D: Data, flag):
    """Consecutive count of flag == 1 within the symbol-day, ending at each row."""
    return _runlen_nb(np.nan_to_num(flag).astype(np.float64), D.new)


def vwap_fade(D: Data, s, p):
    """R03 VWAP rubber-band fade: after a close beyond VWAP -/+ p ATR (long below, short above), the first close back
    inside the band. S: target VWAP (close reaching VWAP)."""
    z = D.F("z")
    pz = D.prev(z)
    with np.errstate(invalid="ignore"):
        ev = (s * z > -p) & (s * pz <= -p)
        sx = s * z >= 0
    return {"ev": ev, "sx": sx, "tg": None}


def gap_go(D: Data, s, p):
    """R04 Gap-and-go (full-day proxy; no premarket data): gap >= p% (long) / <= -p% (short) and the close breaks the
    prior high (low) of the day, first time from 09:50. S: close back across VWAP."""
    hod_prev, lod_prev = D.prev(D.hod), D.prev(D.lod)
    g = D.F("gap")
    with np.errstate(invalid="ignore"):
        brk = (D.c > hod_prev) if s > 0 else (D.c < lod_prev)
        ev = brk & (s * g >= p)
        sx = s * D.F("z") < 0
    return {"ev": _once(D, ev), "sx": sx, "tg": None}


def gap_fill(D: Data, s, p):
    """R05 Gap fill: gap down <= -p% (long) / up >= p% (short); the close crosses the day's open toward the prior
    close (first time). S: structural target = prior close (gap filled)."""
    fo = D.F("fromOpen")
    pfo = D.prev(fo)
    g = D.F("gap")
    with np.errstate(invalid="ignore"):
        ev = (s * fo > 0) & (s * pfo <= 0) & (-s * g >= p)
    return {"ev": _once(D, ev), "sx": None, "tg": D.pdc}


def red_green(D: Data, s, p):
    """R06 Red-to-green (long) / green-to-red (short): opened on the other side of the prior close by >= p% and the
    close crosses the prior close, first time. S: close back across the prior close."""
    chg = D.chg
    pc = D.prev(chg)
    g = D.F("gap")
    with np.errstate(invalid="ignore"):
        ev = (s * chg > 0) & (s * pc <= 0) & (-s * g >= p)
        sx = s * chg < 0
    return {"ev": _once(D, ev), "sx": sx, "tg": None}


def hod_break(D: Data, s, p):
    """R07 HOD (LOD) break after consolidation: close above the prior high of day when that high was set >= p bars
    earlier, from 10:00. S: close back across VWAP."""
    lvl = D.prev(D.hod) if s > 0 else D.prev(D.lod)
    ext = D.hod if s > 0 else D.lod
    # bars since the extreme last changed
    chg = np.r_[True, np.abs(ext[1:] - ext[:-1]) > 1e-4 * D.atr[1:]] | D.new   # float noise tolerance
    since = _runlen(D, (~chg).astype(float))
    psince = D.prev(since)
    with np.errstate(invalid="ignore"):
        ev = (s * (D.c - lvl) > 0) & (psince >= p) & (D.tod >= 1000)
        sx = s * D.F("z") < 0
    return {"ev": ev, "sx": sx, "tg": None}


def bull_flag(D: Data, s, p):
    """R08 Bull (bear) flag: pole = rise of >= p ATR from the lowest low of bars i-12..i-4 to the highest high of bars
    i-6..i-2 (high after low); flag = bars i-2..i-1 below the pole high and retracing <= 50% of the pole; trigger =
    close above the pole high. S: close below the flag low."""
    a = D.atr
    H = D.h if s > 0 else -D.l
    L = D.l if s > 0 else -D.h
    C = D.c if s > 0 else -D.c
    ph = np.fmax.reduce([D.prev(H, k) for k in range(2, 7)])
    pl = np.fmin.reduce([D.prev(L, k) for k in range(4, 13)])
    f1, f2 = D.prev(H, 1), D.prev(H, 2)
    fl = np.fmin(D.prev(L, 1), D.prev(L, 2))
    pole = ph - pl
    with np.errstate(invalid="ignore"):
        ev = (pole >= p * a) & (np.fmax(f1, f2) <= ph) & (fl >= ph - 0.5 * pole) & (C > ph) & (D.prev(C) <= ph)
        flow = D.ffill(np.where(ev, fl, np.nan))
        sx = C < flow
    return {"ev": ev, "sx": sx, "tg": None}


def ema_pullback(D: Data, s, p):
    """R09 First pullback to the 20 MA in a trend (9/20 EMA pullback; SMA20 used as the 20-line): EMA9 > EMA21,
    SMA20 rising, bar low touches SMA20 + p ATR and the close holds above SMA20 - first touch of the day. Short mirror.
    S: close back across SMA20."""
    m20, a = D.sma20, D.atr
    with np.errstate(invalid="ignore"):
        trend = (s * D.F("emaDiff") > 0) & (s * D.F("sma20_slope_pct") > 0)
        touch = (D.l <= m20 + p * a) & (D.c > m20) if s > 0 else (D.h >= m20 - p * a) & (D.c < m20)
        ev = trend & touch
        sx = s * (D.c - m20) < 0
    return {"ev": _once(D, ev), "sx": sx, "tg": None}


def ema_cross(D: Data, s, p):
    """R10 EMA 9/21 cross: emaDiff crosses p (long up through +p, short down through -p). S: crosses back through 0."""
    e = D.F("emaDiff")
    pe = D.prev(e)
    with np.errstate(invalid="ignore"):
        ev = (s * e > p) & (s * pe <= p)
        sx = s * e < 0
    return {"ev": ev, "sx": sx, "tg": None}


def rsi_os(D: Data, s, p):
    """R11 RSI oversold (overbought) reversal: RSI(14) crosses back above p (long) / below 100-p (short) on a stock
    green (red) vs the prior close ('buy oversold in an uptrend'). S: RSI back to 50."""
    r = D.F("rsi")
    pr = D.prev(r)
    lvl = p if s > 0 else 100 - p
    with np.errstate(invalid="ignore"):
        ev = (s * (r - lvl) > 0) & (s * (pr - lvl) <= 0) & (s * D.chg > 0)
        sx = s * (r - 50) >= 0
    return {"ev": ev, "sx": sx, "tg": None}


def rsi_div(D: Data, s, p):
    """R12 RSI divergence + confirmation: the live bull_div (bear_div) flag within the last p bars (new 20-bar low with
    RSI > its 20-bar min + 5) and the close crosses above (below) the prior bar's high (low). S: none (fixed exits)."""
    f = (D.F("bull_div") if s > 0 else D.F("bear_div")).astype(float)
    recent = np.fmax.reduce([D.prev(f, k) for k in range(0, int(p) + 1)]) if p >= 1 else f
    lvl = D.prev(D.h) if s > 0 else D.prev(D.l)
    with np.errstate(invalid="ignore"):
        ev = (recent > 0) & (s * (D.c - lvl) > 0)
    return {"ev": ev, "sx": None, "tg": None}


def macd_zero(D: Data, s, p):
    """R13 MACD line crosses zero (12/26; the signal line is not in the live frame). S: crosses back."""
    m = D.F("macdPct")
    pm = D.prev(m)
    with np.errstate(invalid="ignore"):
        ev = (s * m > p) & (s * pm <= p)
        sx = s * m < 0
    return {"ev": ev, "sx": sx, "tg": None}


def fvg(D: Data, s, p):
    """R14 ICT fair-value-gap retrace: a bullish FVG forms (low[j] > high[j-2] by >= p ATR); later a bar trades back into
    the gap (low <= gap top) and closes above the gap bottom, coming from above (prev close > gap top). Most recent FVG
    of the day. Short mirror. S: close below the gap bottom."""
    a = D.atr
    if s > 0:
        top, bot = D.l, D.prev(D.h, 2)
        gapok = top - bot >= p * a
    else:
        top, bot = D.h, D.prev(D.l, 2)          # bearish: high[j] < low[j-2]
        gapok = bot - top >= p * a
    with np.errstate(invalid="ignore"):
        T = D.ffill(np.where(gapok, top, np.nan))
        Bt = D.ffill(np.where(gapok, bot, np.nan))
        T, Bt = D.prev(T), D.prev(Bt)           # gap known before this bar
        if s > 0:
            ev = (D.l <= T) & (D.c > Bt) & (D.prev(D.c) > T)
            sx = D.c < Bt
        else:
            ev = (D.h >= T) & (D.c < Bt) & (D.prev(D.c) < T)
            sx = D.c > Bt
    return {"ev": ev, "sx": sx, "tg": None}


def sweep(D: Data, s, p):
    """R15 Liquidity sweep and reclaim of the low (high) of day: the bar's low trades below the prior LOD by >= p ATR and
    the bar closes back above the prior LOD, from 10:00. S: close below the sweep bar's low."""
    a = D.atr
    with np.errstate(invalid="ignore"):
        if s > 0:
            lvl = D.prev(D.lod)
            ev = (D.l <= lvl - p * a) & (D.c > lvl)
            sl = D.ffill(np.where(ev, D.l, np.nan))
            sx = D.c < sl
        else:
            lvl = D.prev(D.hod)
            ev = (D.h >= lvl + p * a) & (D.c < lvl)
            sl = D.ffill(np.where(ev, D.h, np.nan))
            sx = D.c > sl
        ev = ev & (D.tod >= 1000)
    return {"ev": ev, "sx": sx, "tg": None}


def rel_strength(D: Data, s, p):
    """R16 Relative strength vs SPY (r/RealDayTrading, ATR-normalised): (stock move from the open in its daily ATR) minus
    (SPY move from the open in its daily ATR) crosses above +p (long) / below -p (short). S: close back across VWAP."""
    rs = D.fo_atr - D.spy_fo_atr
    prs = D.prev(rs)
    with np.errstate(invalid="ignore"):
        ev = (s * rs > p) & (s * prs <= p)
        sx = s * D.F("z") < 0
    return {"ev": ev, "sx": sx, "tg": None}


def pd_retest(D: Data, s, p):
    """R17 Prior-day high (low) break and retest: after an earlier close above PDH today, a bar's low comes back to
    within p ATR of PDH and the bar closes above PDH (first retest). S: close back below PDH."""
    a = D.atr
    lvl = D.F("pdh") if s > 0 else D.F("pdl")
    above = (s * (D.c - lvl) > 0).astype(float)
    was = D.prev(D.grp_cummax(above))
    with np.errstate(invalid="ignore"):
        touch = (D.l <= lvl + p * a) if s > 0 else (D.h >= lvl - p * a)
        ev = (was > 0) & touch & (above > 0)
        sx = above == 0
    return {"ev": _once(D, ev), "sx": sx, "tg": None}


def _was_beyond_or(D: Data, s):
    """An earlier close (before this bar) beyond the opening-range high (long) / low (short), after 10:00."""
    lvl = D.F("orh") if s > 0 else D.F("orl")
    with np.errstate(invalid="ignore"):
        b = ((s * (D.c - lvl) > 0) & (D.tod > 1000)).astype(float)
    return D.prev(D.grp_cummax(b)) > 0


def orb_fvg(D: Data, s, p):
    """R18 ORB + FVG (the 2025 r/Daytrading 'ORB + FVG/imbalance' model on 5-min bars): after the OR30 break (an
    earlier close beyond ORH/ORL), the FVG-retrace trigger of R14 with gap >= p ATR. S: close back inside the gap."""
    o = fvg(D, s, p)
    return {"ev": o["ev"] & _was_beyond_or(D, s), "sx": o["sx"], "tg": None}


def orb_fib(D: Data, s, p):
    """R19 ORB + Fib pullback (1oaa8t9): after the OR30 break, the bar's low reaches the p retracement of the day's
    range (prior LOD -> prior HOD) and the close holds above the 61.8% level; first per day. S: target = prior HOD
    (new high of day), exit on a close below the 78.6% level."""
    H, L = D.prev(D.hod), D.prev(D.lod)
    rng = H - L
    with np.errstate(invalid="ignore"):
        if s > 0:
            ev = (D.l <= H - p * rng) & (D.c >= H - 0.618 * rng) & (rng > 0)
            sx = D.c < H - 0.786 * rng
            tg = H
        else:
            ev = (D.h >= L + p * rng) & (D.c <= L + 0.618 * rng) & (rng > 0)
            sx = D.c > L + 0.786 * rng
            tg = L
    ev = _once(D, ev & _was_beyond_or(D, s))
    tgf = D.ffill(np.where(ev, tg, np.nan))
    sxf = D.ffill(np.where(ev, np.where(s > 0, H - 0.786 * rng, L + 0.786 * rng), np.nan))
    with np.errstate(invalid="ignore"):
        sx = (D.c < sxf) if s > 0 else (D.c > sxf)
    return {"ev": ev, "sx": sx, "tg": tgf}


def sma_macd(D: Data, s, p):
    """R20 SMA cross confirmed by MACD (1ia39vf, the top-scored concrete post): the close crosses the 5-min SMA20 (the
    post's 10-period SMA is not in the live frame) while the MACD line is on the trade side by > p (% of price; the
    signal-line cross is not in the live frame). S: close back across SMA20."""
    d = D.F("sma20_dist_pct")
    pd_ = D.prev(d)
    with np.errstate(invalid="ignore"):
        ev = (s * d > 0) & (s * pd_ <= 0) & (s * D.F("macdPct") > p)
        sx = s * d < 0
    return {"ev": ev, "sx": sx, "tg": None}


# name -> (builder, default p, plateau grid, reddit key in the taxonomy)
STRATS = {
    "R01-orb30": (orb, 0.0, [0.0, 0.1, 0.2], "orb"),
    "R02-vwap-reclaim": (vwap_reclaim, 6, [3, 6, 12], "vwap_reclaim"),
    "R03-vwap-fade": (vwap_fade, 1.0, [0.75, 1.0, 1.25], "vwap_fade"),
    "R04-gap-go": (gap_go, 2.0, [1.0, 2.0, 3.0], "gap_go"),
    "R05-gap-fill": (gap_fill, 2.0, [1.0, 2.0, 3.0], "gap_fade"),
    "R06-red-green": (red_green, 0.5, [0.0, 0.5, 1.0], "red_green"),
    "R07-hod-break": (hod_break, 6, [3, 6, 12], "hod_break"),
    "R08-bull-flag": (bull_flag, 0.5, [0.35, 0.5, 0.75], "bull_flag"),
    "R09-ema20-pullback": (ema_pullback, 0.0, [0.0, 0.1, 0.2], "first_pullback"),
    "R10-ema-cross": (ema_cross, 0.0, [0.0, 0.05, 0.1], "ema_cross"),
    "R11-rsi-os": (rsi_os, 30, [25, 30, 35], "rsi"),
    "R12-rsi-div": (rsi_div, 3, [1, 3, 6], "rsi_div"),
    "R13-macd-zero": (macd_zero, 0.0, [0.0, 0.05, 0.1], "macd"),
    "R14-ict-fvg": (fvg, 0.1, [0.05, 0.1, 0.2], "ict"),
    "R15-sweep": (sweep, 0.05, [0.0, 0.05, 0.1], "ict"),
    "R16-rel-strength": (rel_strength, 1.0, [0.75, 1.0, 1.5], "rel_strength"),
    "R17-pd-retest": (pd_retest, 0.1, [0.05, 0.1, 0.2], "pdh_pdl"),
    "R18-orb-fvg": (orb_fvg, 0.1, [0.05, 0.1, 0.2], "orb"),
    "R19-orb-fib": (orb_fib, 0.5, [0.382, 0.5, 0.618], "orb"),
    "R20-sma-macd": (sma_macd, 0.0, [0.0, 0.05, 0.1], "macd"),
}


# ------------------------------------------------------------------ filters (side-relative, s = +1 long / -1 short)
FTH = {"rvol": 1.5, "inplay": 2.0}                     # default thresholds
FGRID = {"rvol": [1.25, 1.5, 2.0], "inplay": [1.5, 2.0, 3.0]}   # plateau neighbours


def filt(D: Data, name: str, s: int, th=None):
    th = FTH.get(name) if th is None else th
    with np.errstate(invalid="ignore"):
        if name == "rvol":        # 'volume confirms': this bar's volume >= th x its average
            return D.F("volumeRatio") >= th
        if name == "vwap":        # 'only long above VWAP / short below'
            return s * D.F("z") > 0
        if name == "trend":       # 'trade with the trend': 5-min SMA20 slope on the trade side
            return s * D.F("sma20_slope_pct") > 0
        if name == "spy":         # 'with the market' (RDT): SPY on the trade side of its VWAP
            return s * D.spy_z > 0
        if name == "inplay":      # 'stocks in play': |move from the open| >= 2%
            return np.abs(D.F("fromOpen")) >= th
    raise KeyError(name)


FILTERS = ["rvol", "vwap", "trend", "spy", "inplay"]
FILTER_SETS = [()] + [(f,) for f in FILTERS] + [(a, b) for i, a in enumerate(FILTERS) for b in FILTERS[i + 1:]]


@numba.njit(cache=True)
def _runlen_nb(flag, new):
    out = np.empty(len(flag))
    cur = 0.0
    for i in range(len(flag)):
        if new[i]:
            cur = 0.0
        cur = cur + 1.0 if flag[i] > 0 else 0.0
        out[i] = cur
    return out
