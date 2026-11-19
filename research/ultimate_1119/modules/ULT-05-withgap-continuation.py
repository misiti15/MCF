# ULTIMATE CANDIDATE ULT-05-withgap-continuation (research only, not enabled in any account)
# research/ultimate_1119/PLAN.md sec. 3 "ULT-05"; backtest research/ultimate_1119/ULT-05-withgap-continuation/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-05 with-the-gap continuation (two-sided) - LONG and SHORT, 10:15-13:00/14:00.

Thesis: trading WITH a 2%+ gap beats fading it in both halves; enter on a pullback that holds the gap side of VWAP,
with the tape not against the trade.
Rule (all point-in-time, at the decision 5-minute bar close):
  intake U  price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.10 (LR8 stop-out round trip
            ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / R, R = 0.25 x daily ATR); ADV20 >= $20M via the YAML min_adv
  long      gap >= G; 0 < vwapDistPct <= 0.5 x atrPct (5-min ATR(14) % of price, frame column); buyPressure > 0;
            SPY since the 09:50 bar close >= -0.15% (context spy_fo)
  short     gap <= -G; -0.5 x atrPct <= vwapDistPct < 0; buyPressure < 0; SPY since 09:50 <= +0.15%; RSI(5) >= 25
  window    bar close WINDOW (YAML window must match)
  refire    (THIN) first hit, a second hit >= 15 bars (75 min) after the first, max 2 per symbol-session (first lot closed
            by its 45-min max hold + 30-min cooldown, decided from bars alone). YAML: refire true, refire_cooldown 0.
Two sides, one file: LabStrategy has one side per setup, so the account carries TWO `type: lab` entries pointing at this
file; the side comes from the setup name (a name ending in "-S" / "-short" is the short side, anything else the long
side), e.g. `ULT-05-L` and `ULT-05-S`. A name cannot be gap-up and gap-down on the same day, so the two never collide.
Exit: EXIT "T" -> GEOM t1s1 (+1R limit / -1R stop) with YAML time_stop_min 45, time_stop_min_r 99 (45-min time exit);
      EXIT "X" -> GEOM "S": stop_price = 2R catastrophic stop beyond the entry, no target, time_stop_min 45.
Account-side (not in the module): day cap 30 entries over both sides; flat 15:50 implied (last entry 14:00 + 45 min)."""
import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
G = 3.0                   # |gap| floor, % (fit-selected config 05h G3-W14-X)
WINDOW = (1015, 1400)     # bar-close HHMM, inclusive
EXIT = "X"                # "T" t1s1 cap45 | "X" time exit 45 with a 2R catastrophic stop
GEOM = "t1s1" if EXIT == "T" else "S"
MIN_ADV = 20_000_000      # YAML min_adv (point-in-time ADV20)
VWAP_ATR_FRAC = 0.5
SPY_TOL = 0.15            # long: SPY since 09:50 >= -0.15%; short: <= +0.15%
RSI5_SHORT_MIN = 25.0
COST_R_MAX = 0.10
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
_SGN = 1 if SIDE == "long" else -1
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 >= $20M (YAML min_adv)",
    f"gap {'>=' if _SGN > 0 else '<='} {_SGN * G:+g}%",
    f"close on the gap side of VWAP, within {VWAP_ATR_FRAC:g} x 5-min ATR% of it",
    f"buyPressure {'>' if _SGN > 0 else '<'} 0",
    (f"SPY since the 09:50 bar close >= -{SPY_TOL:g}%" if _SGN > 0 else f"SPY since the 09:50 bar close <= +{SPY_TOL:g}%"),
] + ([] if _SGN > 0 else [f"RSI(5) >= {RSI5_SHORT_MIN:g}"]) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: t1s1 + 45-min time exit" if EXIT == "T" else "exit: 45-min time exit, 2R catastrophic stop",
]


def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _keys(df):
    import pandas as pd
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        day = df["symbol"].astype(str).to_numpy() + "|" + day
    return day


def _spy_since_0950(df) -> np.ndarray:
    """SPY % change since the 09:50 bar close from the runner's `spy_fo` context column; NaN without a 09:50 row."""
    import pandas as pd
    fo = df["spy_fo"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    at950 = pd.Series(np.where(tod == 950, fo, np.nan)).groupby(_keys(df)).transform("first").to_numpy(dtype=float)
    return ((1 + fo / 100) / (1 + at950 / 100) - 1) * 100


def intake(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    R = 0.25 * atr
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / R
        return (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= COST_R_MAX)


def side_mask(df, sgn: int, g: float) -> np.ndarray:
    """The un-thinned, un-windowed trigger for one side (sgn +1 long / -1 short) and gap floor g (shared with bt.py)."""
    def c(k):
        return df[k].to_numpy(dtype=float)
    vd, ap, bp, spy = c("vwapDistPct"), c("atrPct"), c("buyPressure"), _spy_since_0950(df)
    with np.errstate(invalid="ignore"):
        m = (intake(df) & (sgn * c("gap") >= g) & (sgn * vd > 0) & (sgn * vd <= VWAP_ATR_FRAC * ap)
             & (sgn * bp > 0) & (sgn * spy >= -SPY_TOL))
        if sgn < 0:
            m &= c("rsi5") >= RSI5_SHORT_MIN
    return m


def _thin(m, df):
    hit = np.flatnonzero(m)
    if not len(hit):
        return m
    key = _keys(df)
    out = np.zeros(len(m), bool)
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= REFIRE_BARS:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    if "spy_fo" not in df.columns:          # fail safe: no market context -> no signal (needs `context: [spy_fo]`)
        return np.zeros(len(df), bool)
    tod = df["tod"].to_numpy(dtype=float)
    m = side_mask(df, _SGN, G) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT "X"): catastrophic stop 2R = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
