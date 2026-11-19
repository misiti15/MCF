# ULTIMATE CANDIDATE ULT-09-failed-vwap-reclaim-short (research only, not enabled in any account)
# research/ultimate_1119/PLAN.md sec. 3 "ULT-09"; backtest research/ultimate_1119/ULT-09-failed-vwap-reclaim-short/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-09 failed VWAP reclaim short on a weak tape - SHORT, 10:30-15:00.

Thesis (archive archetype 6): weak names (below the 5-min SMA20 and below the open) that poke back above VWAP and fail
are shorted only while SPY is not rising since 09:50.
Rule (all point-in-time, at the decision 5-minute bar close):
  intake U  price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.10 (LR8 stop-out round trip
            ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / R, R = 0.25 x daily ATR); ADV20 >= $20M via the YAML min_adv
  name      gap <= +0.5%; fromOpen < 0; sma20_dist_pct (close vs 5-min SMA20) <= -1.5%
  trigger   vwapDistPct > 0 (close above VWAP) on at least one of the previous 3 bars of the same symbol-day (each lag
            must be exactly 5/10/15 min earlier, else it does not count) AND vwapDistPct < 0 now; RSI(5) >= 40
  tape      SPY % since the 09:50 bar close (from the runner's `spy_fo` context column) <= SPY_T
  window    bar close WINDOW (YAML window must match; the engine caps decision bars at 15:00, so the PLAN's 15:20 end
            is effectively 15:00)
  refire    (THIN) first hit, a second hit >= 15 bars (75 min) after the first, max 2 per symbol-session: the first lot
            is closed (45-min max hold) plus a 30-min cooldown, decided from bars alone. YAML: refire true,
            refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 (+1R limit / -1R stop), YAML time_stop_min 45, time_stop_min_r 99;
      EXIT "X" -> GEOM "S": stop_price = entry + 2R (catastrophic), no target, YAML time_stop_min 45, time_stop_min_r 99.
Account-side (not in the module): day cap 30 entries; flat by 15:50 is implied (last entry 15:00 + 45 min)."""
import numpy as np
import pandas as pd

SIDE = "short"
WINDOW = (1030, 1500)     # bar-close HHMM, inclusive (fit-selected 09c W1520, capped at 15:00 by the engine)
SPY_T = -0.20             # SPY % since the 09:50 bar close must be <= this (fit-selected 09c; check FAIL, RESULTS.md)
EXIT = "T"                # "T" t1s1 cap45 | "X" time exit 45 with a 2R catastrophic stop
GEOM = "t1s1" if EXIT == "T" else "S"
MIN_ADV = 20_000_000      # YAML min_adv (point-in-time ADV20)
GAP_MAX = 0.5
SMA20_MAX = -1.5
RSI_MIN = 40.0
LOOKBACK = 3
COST_R_MAX = 0.10
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 >= $20M (YAML min_adv)",
    "gap <= +0.5% (no gap-up shorts); below the open",
    "close >= 1.5% below the 5-min SMA20",
    "closed above VWAP on one of the previous 3 bars, now closes below VWAP; RSI(5) >= 40",
    f"tape: SPY <= {SPY_T:+.2f}% since the 09:50 bar close",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: t1s1 + 45-min time exit" if EXIT == "T" else "exit: 45-min time exit, 2R catastrophic stop",
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


def _spy_since_0950(df) -> np.ndarray:
    """SPY % change since the 09:50 bar close from `spy_fo`; NaN without a 09:50 row of the same symbol-day."""
    fo = df["spy_fo"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    at950 = pd.Series(np.where(tod == 950, fo, np.nan)).groupby(_keys(df)).transform("first").to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return ((1 + fo / 100) / (1 + at950 / 100) - 1) * 100


def was_above_vwap(df, lookback=LOOKBACK) -> np.ndarray:
    """True where the same symbol-day closed above VWAP (vwapDistPct > 0) on one of the previous `lookback` 5-min bars,
    each exactly 5 x k minutes earlier (rows in time order per symbol-day, as the frames are built)."""
    vd = df["vwapDistPct"].to_numpy(dtype=float)
    mins = _minutes(df["tod"].to_numpy())
    key = pd.factorize(_keys(df))[0]
    n = len(vd)
    out = np.zeros(n, bool)
    for k in range(1, lookback + 1):
        if n <= k:
            break
        pv = np.r_[np.full(k, np.nan), vd[:-k]]
        pm = np.r_[np.full(k, np.nan), mins[:-k]]
        pk = np.r_[np.full(k, -1), key[:-k]]
        with np.errstate(invalid="ignore"):
            out |= (pk == key) & (mins - pm == 5 * k) & (pv > 0)
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
    tod = c("tod")
    with np.errstate(invalid="ignore"):
        m = (intake(df) & (c("gap") <= GAP_MAX) & (c("fromOpen") < 0) & (c("sma20_dist_pct") <= SMA20_MAX)
             & (c("vwapDistPct") < 0) & was_above_vwap(df) & (c("rsi5") >= RSI_MIN)
             & (_spy_since_0950(df) <= SPY_T) & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT "X"): catastrophic stop 2R = 0.5 daily ATR above the decision close (short)."""
    return float(f["close"].iloc[i]) + 2 * 0.25 * float(f["atr_d"].iloc[i])
