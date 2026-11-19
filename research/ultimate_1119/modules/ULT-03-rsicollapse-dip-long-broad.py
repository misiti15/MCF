# ULTIMATE CANDIDATE ULT-03-rsicollapse-dip-long-broad (research only, not enabled in any account)
# research/ultimate_1119/PLAN.md sec. 3 "ULT-03"; backtest research/ultimate_1119/ULT-03-rsicollapse-dip-long-broad/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-03 RSI-collapse dip buy, broadened (ST7 chassis) - LONG, 10:15-15:00.

Thesis: ST7-FD (RSI14 crosses below 50, RSI14 <= 30, down > 1% from the open, 19-bar buy pressure > 0) with the cost
filter instead of ADV >= $95M as intake, and a falling-hour SPY guard.
Rule (all point-in-time, at the decision 5-minute bar close):
  intake U  price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.10 (LR8 stop-out round trip
            ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / R, R = 0.25 x daily ATR); ADV20 floor via the YAML min_adv
  trigger   RSI(14) crossed below 50 on this bar or one of the 2 previous bars (cross = rsi < 50 and the bar before
            >= 50, same session); RSI(14) <= RSI_MAX now; fromOpen <= -1.0%; 19-bar buyPressure > 0
  gate      skip when SPY from its 09:30 open (context spy_fo) is in [-0.75%, -0.30%] AND SPY's 30-min return
            (spy_fo now vs 6 bars earlier, exactly 30 min) < 0. No SPY context -> no signal (fail safe).
  window    bar close WINDOW (YAML window must match)
  refire    (THIN) first hit, a second hit >= 15 bars (75 min) after the first, max 2 per symbol-session: the first lot
            is closed (45-min max hold) plus a 30-min cooldown, decided from bars alone. YAML: refire true,
            refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 with YAML time_stop_min 45, time_stop_min_r 99 (45-min time exit);
      EXIT "X" -> GEOM "S": stop_price = entry - 2R (catastrophic), no target, time_stop_min 45 / time_stop_min_r 99.
Account-side (not in the module): day cap 30 entries; flat 15:50 implied (last entry 15:00 + 45 min)."""
import numpy as np

SIDE = "long"
WINDOW = (1015, 1500)     # bar-close HHMM, inclusive
RSI_MAX = 30.0            # fit-selected config 03b (RESULTS.md: FAIL; faithful build only, NOT for deployment)
EXIT = "X"                # 03b; "T" t1s1 cap45 | "X" time exit 45 with a 2R catastrophic stop
GEOM = "t1s1" if EXIT == "T" else "S"
MIN_ADV = 20_000_000      # YAML min_adv (point-in-time ADV20)
CROSS_LEVEL = 50.0
CROSS_BARS = 3            # cross on this bar or the 2 before
FROM_OPEN_MAX = -1.0
SPY_BAND = (-0.75, -0.30)
COST_R_MAX = 0.10
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 floor (YAML min_adv)",
    "RSI(14) crossed below 50 within the last 3 bars",
    f"RSI(14) <= {RSI_MAX:g}",
    "down >= 1.0% from the open",
    "19-bar buy pressure > 0",
    "skip when SPY is -0.75..-0.30% from its open AND SPY's 30-min return < 0",
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


def crossed(df) -> np.ndarray:
    """RSI(14) crossed below 50 on this bar or one of the previous CROSS_BARS - 1 bars (same session)."""
    rsi = df["rsi"].to_numpy(dtype=float)
    key = _keys(df).astype(object)
    mins = _minutes(df["tod"].to_numpy())
    with np.errstate(invalid="ignore"):
        cr = (rsi < CROSS_LEVEL) & (_lag(rsi, 1, key, mins) >= CROSS_LEVEL)
    out = cr.copy()
    for k in range(1, CROSS_BARS):
        lk = _lag(cr.astype(float), k, key, mins)
        out |= lk == 1.0
    return out


def spy_gate(df) -> np.ndarray:
    """True = allowed. Blocks when SPY from the open is in SPY_BAND and the SPY 30-min return < 0; NaN -> blocked."""
    fo = df["spy_fo"].to_numpy(dtype=float)
    key = _keys(df).astype(object)
    mins = _minutes(df["tod"].to_numpy())
    p30 = _lag(fo, 6, key, mins)
    with np.errstate(invalid="ignore", divide="ignore"):
        r30 = ((1 + fo / 100) / (1 + p30 / 100) - 1) * 100
        block = (fo >= SPY_BAND[0]) & (fo <= SPY_BAND[1]) & (r30 < 0)
    return np.isfinite(fo) & np.isfinite(r30) & ~block


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
    tod, rsi = c("tod"), c("rsi")
    with np.errstate(invalid="ignore"):
        m = (intake(df) & crossed(df) & (rsi <= RSI_MAX) & (c("fromOpen") <= FROM_OPEN_MAX)
             & (c("buyPressure") > 0) & spy_gate(df) & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT "X"): catastrophic stop 2R = 0.5 daily ATR below the decision close (long)."""
    return float(f["close"].iloc[i]) - 2 * 0.25 * float(f["atr_d"].iloc[i])
