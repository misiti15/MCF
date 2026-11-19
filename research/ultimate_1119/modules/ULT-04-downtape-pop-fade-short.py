# ULTIMATE CANDIDATE ULT-04-downtape-pop-fade-short (research only, not enabled in any account)
# research/ultimate_1119/PLAN.md sec. 3 "ULT-04"; backtest research/ultimate_1119/ULT-04-downtape-pop-fade-short/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-04 down-tape pop fade short - SHORT, regime specialist (in-day down tape).

Thesis: short fades earn on down sessions and lose on up sessions; the point-in-time version of a down session (SPY
already below its 09:30 open and not rising over the last 30 min) plus a weak name (below its 5-min SMA20) and an
overbought RSI(5) pop. No gap-up shorts, no oversold shorts.
Rule (all point-in-time, at the decision 5-minute bar close):
  intake U  price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.10 (LR8 stop-out round trip
            ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / R, R = 0.25 x daily ATR); ADV20 >= $20M via the YAML min_adv
  tape      spy_s930 = SPY % from its 09:30 open (runner context column `spy_fo`) <= SPY_T
            AND spy_r30 = SPY return over the last 30 min ((1 + fo_t) / (1 + fo_t-6bars) - 1) <= 0
            (the earlier row must be exactly 30 min before on the same symbol-day, else NaN -> no fire)
  name      gap <= +0.5%; sma20_dist_pct (close vs 5-min SMA20) <= -1.5%
  trigger   RSI_MIN <= RSI(5) < 90
  window    bar close 10:30-14:30 (YAML window must match)
  refire    (THIN) first hit, a second hit >= REFIRE_BARS after the first, max 2 per symbol-session: guarantees the first
            lot is closed (max hold) plus a 30-min cooldown, decided from bars alone. YAML: refire true, refire_cooldown 0.
Exit: EXIT "T"   -> GEOM t1s1 (+1R limit / -1R stop), YAML time_stop_min 45, time_stop_min_r 99;
      EXIT "X30" -> GEOM "S": stop_price = entry + 2R (catastrophic), no target, YAML time_stop_min 30, time_stop_min_r 99;
      EXIT "X45" -> same with time_stop_min 45.
Account-side (not in the module): day cap 30 entries; flat by 15:50 is implied (last entry 14:30 + 45 min)."""
import numpy as np
import pandas as pd

SIDE = "short"
WINDOW = (1030, 1430)     # bar-close HHMM, inclusive
SPY_T = -0.50             # spy_s930 (%) must be <= this (fit-selected config 04j S50-R80-T; check FAIL, RESULTS.md)
RSI_MIN = 80.0
EXIT = "T"                # "T" t1s1 cap45 | "X30" / "X45" time exit with a 2R catastrophic stop
GEOM = "t1s1" if EXIT == "T" else "S"
MIN_ADV = 20_000_000      # YAML min_adv (point-in-time ADV20)
GAP_MAX = 0.5
RSI_CAP = 90.0
SMA20_MAX = -1.5
SPY_R30_MAX = 0.0
COST_R_MAX = 0.10
THIN = True
MAX_PER_DAY = 2
REFIRE_BARS = 12 if EXIT == "X30" else 15   # (max hold + 30 min) / 5
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 >= $20M (YAML min_adv)",
    f"tape: SPY <= {SPY_T:+.2f}% from its 09:30 open AND SPY 30-min return <= 0",
    "gap <= +0.5% (no gap-up shorts)",
    "close >= 1.5% below the 5-min SMA20",
    f"{RSI_MIN:g} <= RSI(5) < 90",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: t1s1 + 45-min time exit" if EXIT == "T" else f"exit: {EXIT[1:]}-min time exit, 2R catastrophic stop",
]


def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _minutes(tod):
    t = np.asarray(tod, dtype=float)
    return (t // 100) * 60 + t % 100


def _keys(df):
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        day = df["symbol"].astype(str).to_numpy() + "|" + day
    return day


def spy_r30(df) -> np.ndarray:
    """SPY 30-min return (%) from `spy_fo` of the same frame (rows of one symbol-day in time order); NaN unless the row
    6 back is the same symbol-day and exactly 30 minutes earlier."""
    fo = df["spy_fo"].to_numpy(dtype=float)
    mins = _minutes(df["tod"].to_numpy())
    n = len(fo)
    out = np.full(n, np.nan)
    if n <= 6:
        return out
    key = pd.factorize(_keys(df))[0]
    prev_fo = np.r_[np.full(6, np.nan), fo[:-6]]
    prev_m = np.r_[np.full(6, np.nan), mins[:-6]]
    prev_k = np.r_[np.full(6, -1), key[:-6]]
    ok = (prev_k == key) & (mins - prev_m == 30)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = ((1 + fo / 100) / (1 + prev_fo / 100) - 1) * 100
    out[ok] = r[ok]
    return out


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
    tod, rsi5, fo = c("tod"), c("rsi5"), c("spy_fo")
    with np.errstate(invalid="ignore"):
        m = (intake(df) & (fo <= SPY_T) & (spy_r30(df) <= SPY_R30_MAX) & (c("gap") <= GAP_MAX)
             & (c("sma20_dist_pct") <= SMA20_MAX) & (rsi5 >= RSI_MIN) & (rsi5 < RSI_CAP)
             & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT X30/X45): catastrophic stop 2R = 0.5 daily ATR above the decision close (short)."""
    return float(f["close"].iloc[i]) + 2 * 0.25 * float(f["atr_d"].iloc[i])
