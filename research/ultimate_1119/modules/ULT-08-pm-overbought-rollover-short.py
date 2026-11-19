# ULTIMATE CANDIDATE ULT-08-pm-overbought-rollover-short (research only, not enabled in any account)
# research/ultimate_1119/PLAN.md sec. 3 "ULT-08"; backtest research/ultimate_1119/ULT-08-pm-overbought-rollover-short/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-08 afternoon overbought roll-over short - SHORT, 14:00-15:00 bar close.

Thesis: 14:30-15:00 is the least-bad live block and this is the owner's "overbought name rolling over". Extension
alone predicts volatility, not direction, so: no gap-ups, the roll-over must have started (RSI5 turning down from an
overbought print, upper wick on the decision bar), no shorts into a rising 30-min tape, short time exit.
Rule (all point-in-time, at the decision 5-minute bar close):
  intake U  price >= $10; |gap| < 20%; daily ATR known; cost_r <= 0.10 (LR8 stop-out round trip
            ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / R, R = 0.25 x daily ATR); ADV20 >= $20M via the YAML min_adv
  gates     gap <= +0.5%; spy_r30 = SPY return over exactly the last 6 bars (context `spy_fo`) <= 0
  trigger   from_open_atr = (close - 09:30 open) / daily ATR >= RUN;
            RSI(5) on the previous bar (exactly 5 min earlier, same session) >= RSI_MIN and RSI(5) now < that value
            (the PLAN's "rsiSlope < 0" read as the RSI5 slope - the frame column `rsiSlope` is the 3-bar RSI(14) change);
            upper_wick (upper wick share of the decision 5-min bar) > 0
  window    bar close WINDOW. PLAN says 14:00-15:20, but the lab frames and LabStrategy both stop at the 15:00 bar
            close (setups.py clamps tod <= 1500), so the effective window is 14:00-15:00 live and in the backtest.
  refire    (THIN) first hit, a second hit >= REFIRE_BARS after the first, max 2 per symbol-session: the first lot is
            closed (time exit) plus a 30-min cooldown, decided from bars alone. YAML: refire true, refire_cooldown 0.
Exit: GEOM "S": stop_price = entry + 2R (catastrophic), no target; YAML time_stop_min 20 (TX20) or 30 (TX30),
      time_stop_min_r 99. Flat 15:50 implied (last entry 15:00 + 30 min).
Account-side (not in the module): day cap 30 entries."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "S"
WINDOW = (1400, 1500)     # bar-close HHMM, inclusive (PLAN 1400-1520; frames/live stop at 15:00)
RUN = 2.0                 # from_open_atr >= RUN  (fit-selected 08g RUN2-R85-X20; check FAIL, RESULTS.md)
RSI_MIN = 85.0            # previous-bar RSI(5) >= RSI_MIN
HOLD = 20                 # TX hold in minutes (YAML time_stop_min must match)
MIN_ADV = 20_000_000      # YAML min_adv (point-in-time ADV20)
GAP_MAX = 0.5
SPY_R30_MAX = 0.0
COST_R_MAX = 0.10
THIN = True
MAX_PER_DAY = 2
REFIRE_BARS = (HOLD + 30) // 5
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 >= $20M (YAML min_adv)",
    "gap <= +0.5% (no gap-up shorts)",
    "SPY 30-min return <= 0 (no shorts into a rising tape)",
    f"up >= {RUN:g} daily ATR from the 09:30 open",
    f"RSI(5) previous bar >= {RSI_MIN:g} and lower now (roll-over started)",
    "upper wick on the decision bar",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    f"exit: {HOLD}-min time exit, 2R catastrophic stop",
]


def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _keys(df):
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
    pk = np.r_[np.full(k, -1), key[:-k]]
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


def from_open_atr(df) -> np.ndarray:
    """(close - today's 09:30 open) / daily ATR; the open is recovered from fromOpen (= (close / open - 1) x 100)."""
    c = df["close"].to_numpy(dtype=float)
    fo = df["fromOpen"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        o = c / (1 + fo / 100)
        return (c - o) / df["atr_d"].to_numpy(dtype=float)


def rsi5_prev(df) -> np.ndarray:
    key = pd.factorize(_keys(df))[0]
    return _lag(df["rsi5"].to_numpy(dtype=float), 1, key, _minutes(df["tod"].to_numpy()))


def spy_r30(df) -> np.ndarray:
    """SPY % return over exactly the last 6 five-minute bars, from `spy_fo`; NaN without that history."""
    fo = df["spy_fo"].to_numpy(dtype=float)
    key = pd.factorize(_keys(df))[0]
    p = _lag(fo, 6, key, _minutes(df["tod"].to_numpy()))
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

    def c(k):
        return df[k].to_numpy(dtype=float)
    tod, r5 = c("tod"), c("rsi5")
    p5, r30 = rsi5_prev(df), spy_r30(df)
    with np.errstate(invalid="ignore"):
        m = (intake(df) & (c("gap") <= GAP_MAX) & np.isfinite(r30) & (r30 <= SPY_R30_MAX)
             & (from_open_atr(df) >= RUN) & (p5 >= RSI_MIN) & (r5 < p5) & (c("upper_wick") > 0)
             & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S": catastrophic stop 2R = 0.5 daily ATR above the decision close (short)."""
    return float(f["close"].iloc[i]) + 2 * 0.25 * float(f["atr_d"].iloc[i])
