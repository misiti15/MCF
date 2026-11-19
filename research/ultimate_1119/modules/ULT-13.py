# ULTIMATE CANDIDATE ULT-13 ST7-SHARP (research only, not enabled in any account)
# research/ultimate_1119/round2/PLAN.md sec. 3 "ULT-13"; backtest research/ultimate_1119/round2/ULT-13/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-13 ST7-SHARP - ST7's one-bar RSI(14) collapse + a point-in-time down-tape guard, LONG, 09:50-15:00.

Rule (all point-in-time, at the decision 5-minute bar close; frame columns rsi = RSI(14), buyPressure = 19-bar):
  intake U2  price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.10 (LR8 stop-out round trip
             ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $50M via the YAML min_adv
  trigger    ONE-BAR collapse: RSI14 of the previous 5-min bar (same session, exactly 5 min earlier) >= 50 AND
             RSI14 now <= RMAX; fromOpen <= -1.0%; buyPressure (19-bar) > 0
  universal  skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0 (round-2 chassis)
  guard G1   skip when spy_fo <= -0.30% AND spy_r30 <= 0 (SPY down from the open and still falling). Build rule fixed
             before any fit scoring: if spy_r30 is unknown (no SPY row 30 min earlier, i.e. before the 10:20 bar in the
             lab frames) G1 decides on spy_fo alone (skip when spy_fo <= -0.30%). G0 = no guard.
  window     bar close WINDOW (inclusive; YAML window must match). No SPY context -> no signal (fail safe).
  refire     (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain:
             >= 30 min after the first lot's exit). YAML: refire true, refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 (+1u / -1u around the decision close), YAML time_stop_min 45, time_stop_min_r 99;
      EXIT "X" -> GEOM "S": stop_price = decision close - 2u (catastrophic), no target, time_stop_min 45.
Account-side (not in the module): day cap 30 entries (first by time, ADV20 desc); flat 15:50 implied."""
import numpy as np

SIDE = "long"
# ---- fit-frozen pick (round2/ULT-13/fitsel.json); set after the FIT grid, before any CHECK data
RMAX = 35.0
GUARD = "G0"
EXIT = "X"
# ----
GEOM = "t1s1" if EXIT == "T" else "S"
WINDOW = (950, 1500)
MIN_ADV = 50_000_000
RSI_PREV_MIN = 50.0
FROM_OPEN_MAX = -1.0
COST_R_MAX = 0.10
UNIV_BAND = (-0.75, -0.30)
GUARD_FO = -0.30
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10, ADV20 >= $50M (YAML min_adv)",
    f"RSI(14) was >= 50 on the previous 5-min bar and is <= {RMAX:g} now (one-bar collapse)",
    "down >= 1.0% from the open", "19-bar buy pressure > 0",
    "skip while SPY is -0.30..-0.75% from its open and falling over 30 min",
    ("skip while SPY is <= -0.30% from its open and not rising over 30 min" if GUARD == "G1" else "no extra tape guard"),
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: +1R / -1R, 45-min time exit" if EXIT == "T" else "exit: 45-min time exit, 2R catastrophic stop",
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
    tod = np.asarray(tod, float)
    return (tod // 100) * 60 + tod % 100


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


def spy_r30(df) -> np.ndarray:
    """SPY % change over the last 30 minutes from spy_fo (same session, bar closes >= 09:50); NaN without the t-30 row."""
    import pandas as pd
    fo = df["spy_fo"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    key = _keys(df)
    m = _minutes(tod)
    s = pd.Series(np.where(tod >= 950, fo, np.nan), index=pd.MultiIndex.from_arrays([key, m]))
    s = s[~s.index.duplicated()]
    lag = s.reindex(pd.MultiIndex.from_arrays([key, m - 30])).to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return ((1 + fo / 100) / (1 + lag / 100) - 1) * 100


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    c = lambda k: df[k].to_numpy(dtype=float)
    px, atr, tod, rsi = c("close"), c("atr_d"), c("tod"), c("rsi")
    key = _keys(df).astype(object)
    rsi_prev = _lag(rsi, 1, key, _minutes(tod))
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(len(df), np.nan)
    r30 = spy_r30(df) if has_spy else np.full(len(df), np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        intake = (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= COST_R_MAX) & np.isfinite(fo)
        univ_ok = ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0))
        g1_ok = ~((fo <= GUARD_FO) & ((r30 <= 0) | ~np.isfinite(r30)))
    return {"tod": tod, "close": px, "rsi": rsi, "rsi_prev": rsi_prev, "fromOpen": c("fromOpen"),
            "bp": c("buyPressure"), "cost_r": cost_r, "intake": intake, "univ_ok": univ_ok, "g1_ok": g1_ok,
            "spy_fo": fo, "spy_r30": r30}


def trigger(r, rmax) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((r["rsi_prev"] >= RSI_PREV_MIN) & (r["rsi"] <= rmax) & (r["fromOpen"] <= FROM_OPEN_MAX)
                & (r["bp"] > 0))


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
    r = features(df)
    tod = r["tod"]
    m = r["intake"] & r["univ_ok"] & trigger(r, RMAX) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    if GUARD == "G1":
        m &= r["g1_ok"]
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT "X"): catastrophic stop 2u = 0.5 daily ATR below the decision close (long)."""
    return float(f["close"].iloc[i]) - 2 * 0.25 * float(f["atr_d"].iloc[i])
