# ULTIMATE CANDIDATE ULT-07-pm-volatile-dip-long (research only, not enabled in any account)
# research/ultimate_1119/PLAN.md sec. 3 "ULT-07"; backtest research/ultimate_1119/ULT-07-pm-volatile-dip-long/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-07 afternoon volatile dip buy (NM-ETF WB4 chassis, broadened) - LONG, 14:00-15:00 bar close.

Thesis: the late-day volatile dip buy (NM-ETF-late-dip-di-long WB4) broadened from its ETF list to every high-ATR name
under the cost filter, with the falling-hour SPY guard kept.
Rule (all point-in-time, at the decision 5-minute bar close):
  intake U  price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.10 (LR8 stop-out round trip
            ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / R, R = 0.25 x daily ATR); ADV20 >= $20M via the YAML min_adv
  trigger   daily ATR % of price (atr_d / close x 100; the NM-ETF chassis' atr_d_pct - the frame column `atrPct` is the
            5-minute ATR, median ~0.2%, so a 3-4% floor on it would be empty) >= A_MIN;
            from_open_atr = (close - 09:30 open) / daily ATR <= -DROP;
            19-bar buyPressure > 0;
            RSI(5) crossed UP through 30 on this bar or the previous bar (rsi5 >= 30 and the bar before < 30, the
            earlier bar exactly 5 minutes before in the same session)
  gate      SPY 60-minute return (context spy_fo now vs exactly 12 bars earlier) > -0.40%. No SPY context -> no signal.
  window    bar close WINDOW. PLAN says 14:00-15:15, but the lab frames and LabStrategy both stop at the 15:00 bar
            close (setups.py clamps tod <= 1500), so the effective window is 14:00-15:00 live and in the backtest.
  refire    (THIN) first hit, a second hit >= 15 bars (75 min) after the first, max 2 per symbol-session (first lot
            closed after <= 45 min + 30-min cooldown, decided from bars alone). In a 14:00-15:00 window this means one
            entry per symbol-session in practice. YAML: refire true, refire_cooldown 0.
Exit: EXIT "T" -> GEOM t05s1 (+0.5R limit / -1R stop) with YAML time_stop_min 45, time_stop_min_r 99;
      EXIT "X" -> GEOM "S": stop_price = entry - 2R (catastrophic), no target, time_stop_min 45 / time_stop_min_r 99.
Account-side (not in the module): day cap 30 entries; flat 15:50 implied (last entry 15:00 + 45 min = 15:45)."""
import numpy as np

SIDE = "long"
WINDOW = (1400, 1500)     # bar-close HHMM, inclusive (PLAN 1400-1515; frames/live stop at 15:00)
A_MIN = 3.0               # fit-selected config 07a (RESULTS.md: FAIL; faithful build only, NOT for deployment)
DROP = 1.0
EXIT = "T"                # "T" t05s1 cap45 | "X" time exit 45 with a 2R catastrophic stop
GEOM = "t05s1" if EXIT == "T" else "S"
MIN_ADV = 20_000_000      # YAML min_adv (point-in-time ADV20)
RSI5_LEVEL = 30.0
CROSS_BARS = 2            # cross on this bar or the one before
SPY_R60_MIN = -0.40
COST_R_MAX = 0.10
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 >= $20M (YAML min_adv)",
    f"daily ATR >= {A_MIN:g}% of price",
    f"down >= {DROP:g} daily ATR from the 09:30 open",
    "19-bar buy pressure > 0",
    "RSI(5) crossed up through 30 within the last 2 bars",
    "skip when SPY's 60-min return <= -0.40%",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: t05s1 + 45-min time exit" if EXIT == "T" else "exit: 45-min time exit, 2R catastrophic stop",
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


def _minutes(tod):
    t = np.asarray(tod, dtype=float)
    return (t // 100) * 60 + t % 100


def _lag(x, k, key, mins):
    """x k rows earlier in the same symbol-session, only when that row is exactly 5*k minutes earlier; else NaN."""
    n = len(x)
    out = np.full(n, np.nan)
    if n <= k:
        return out
    px = np.r_[np.full(k, np.nan), x[:-k]]
    pk = np.r_[np.full(k, None, dtype=object), key[:-k]]
    pm = np.r_[np.full(k, np.nan), mins[:-k]]
    ok = (pk == key) & (mins - pm == 5 * k)
    out[ok] = px[ok]
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


def atr_d_pct(df) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return df["atr_d"].to_numpy(dtype=float) / df["close"].to_numpy(dtype=float) * 100


def from_open_atr(df) -> np.ndarray:
    """(close - today's 09:30 open) / daily ATR; the open is recovered from fromOpen (= (close / open - 1) x 100)."""
    c = df["close"].to_numpy(dtype=float)
    fo = df["fromOpen"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        o = c / (1 + fo / 100)
        return (c - o) / df["atr_d"].to_numpy(dtype=float)


def crossed_up(df) -> np.ndarray:
    """RSI(5) crossed up through RSI5_LEVEL on this bar or one of the previous CROSS_BARS - 1 bars (same session)."""
    r = df["rsi5"].to_numpy(dtype=float)
    key = _keys(df).astype(object)
    mins = _minutes(df["tod"].to_numpy())
    with np.errstate(invalid="ignore"):
        cr = (r >= RSI5_LEVEL) & (_lag(r, 1, key, mins) < RSI5_LEVEL)
    out = cr.copy()
    for k in range(1, CROSS_BARS):
        out |= _lag(cr.astype(float), k, key, mins) == 1.0
    return out


def spy_r60(df) -> np.ndarray:
    """SPY % return over exactly the last 12 five-minute bars, from the `spy_fo` context column; NaN without history."""
    fo = df["spy_fo"].to_numpy(dtype=float)
    key = _keys(df).astype(object)
    mins = _minutes(df["tod"].to_numpy())
    p = _lag(fo, 12, key, mins)
    with np.errstate(invalid="ignore", divide="ignore"):
        return ((1 + fo / 100) / (1 + p / 100) - 1) * 100


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
    r60 = spy_r60(df)
    with np.errstate(invalid="ignore"):
        m = (intake(df) & (atr_d_pct(df) >= A_MIN) & (from_open_atr(df) <= -DROP)
             & (df["buyPressure"].to_numpy(dtype=float) > 0) & crossed_up(df)
             & np.isfinite(r60) & (r60 > SPY_R60_MIN) & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT "X"): catastrophic stop 2R = 0.5 daily ATR below the decision close (long)."""
    return float(f["close"].iloc[i]) - 2 * 0.25 * float(f["atr_d"].iloc[i])
