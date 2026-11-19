# ULTIMATE CANDIDATE ULT-01-gapdn-pop-fade-short (research only, not enabled in any account)
# research/ultimate_1119/PLAN.md sec. 3 "ULT-01"; backtest research/ultimate_1119/ULT-01-gapdn-pop-fade-short/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-01 gap-down pop fade short ("Cell A core") - SHORT, midday.

Thesis: gap-down names that bounce into overbought between 11:00 and 13:00 tend to roll back over (live Cell A).
Rule (all point-in-time, at the decision 5-minute bar close):
  intake U  price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.10 (LR8 stop-out round trip
            ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / R, R = 0.25 x daily ATR); ADV20 >= $20M via the YAML min_adv
  trigger   gap <= -1.5%; RSI_MIN <= RSI(5) < 90; close >= 0.5 daily ATR above the low of day (dist_lod_atr)
  gates     SPY since the 09:50 bar close <= +0.15% (context spy_fo); |close / SMA20(5-min) - 1| >= 1.5%
  window    bar close WINDOW (YAML window must match)
  refire    (THIN) first hit, a second hit >= 15 bars (75 min) after the first, max 2 per symbol-session: guarantees
            the first lot is closed (45-min max hold) plus a 30-min cooldown, decided from bars alone so live and
            backtest pick the same bars. YAML: refire true, refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 (+1R limit / -1R stop) with YAML time_stop_min 45, time_stop_min_r 99 (45-min time exit);
      EXIT "X" -> GEOM "S": stop_price = entry + 2R (catastrophic), no target, time_stop_min 45 / time_stop_min_r 99.
Account-side (not in the module): day cap 30 entries; flat 15:50 is implied (last entry 15:00 + 45 min)."""
import numpy as np

SIDE = "short"
WINDOW = (1100, 1500)     # bar-close HHMM, inclusive (fit-selected config 01f W15-R60-X)
RSI_MIN = 60.0
EXIT = "X"                # "T" t1s1 cap45 | "X" time exit 45 with a 2R catastrophic stop
GEOM = "t1s1" if EXIT == "T" else "S"
MIN_ADV = 20_000_000      # YAML min_adv (point-in-time ADV20)
GAP_MAX = -1.5
RSI_CAP = 90.0
LOD_ATR_MIN = 0.5
SPY_MAX_SINCE_0950 = 0.15
SMA20_BAND = 1.5
COST_R_MAX = 0.10
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 >= $20M (YAML min_adv)",
    "gap <= -1.5%",
    f"{RSI_MIN:g} <= RSI(5) < 90",
    "close >= 0.5 daily ATR above the low of day",
    "skip while SPY is up > +0.15% since the 09:50 bar close",
    "not within +-1.5% of the 5-min SMA20",
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
    def c(k):
        return df[k].to_numpy(dtype=float)
    if "spy_fo" not in df.columns:          # fail safe: no market context -> no signal (needs `context: [spy_fo]`)
        return np.zeros(len(df), bool)
    tod, rsi5 = c("tod"), c("rsi5")
    with np.errstate(invalid="ignore"):
        m = (intake(df) & (c("gap") <= GAP_MAX) & (rsi5 >= RSI_MIN) & (rsi5 < RSI_CAP)
             & (c("dist_lod_atr") >= LOD_ATR_MIN) & (np.abs(c("sma20_dist_pct")) >= SMA20_BAND)
             & (_spy_since_0950(df) <= SPY_MAX_SINCE_0950) & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT "X"): catastrophic stop 2R = 0.5 daily ATR above the decision close (short)."""
    return float(f["close"].iloc[i]) + 2 * 0.25 * float(f["atr_d"].iloc[i])
