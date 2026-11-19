# ULTIMATE CANDIDATE ULT-16 COST-GEO (research only, not enabled in any account)
# research/ultimate_1119/round2/PLAN.md sec. 3 "ULT-16"; backtest research/ultimate_1119/round2/ULT-16/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-16 COST-GEO - wider R unit, liquid names, on the ULT-01 (short) + ULT-03 (long) triggers.

Rule (all point-in-time, at the decision 5-minute bar close):
  intake     price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.10 with cost_r = LR8 stop-out round trip
             ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d (the chassis definition, the same for every
             m, so every grid config sees one universe); ADV20 >= $150M via the YAML min_adv (stocks and ETFs, incl.
             leveraged ETFs); optional vol floor atr_d % >= VOL_FLOOR.
  short      (ULT-01 trigger) gap <= -1.5%; 60 <= RSI5 < 90; dist_lod_atr >= 0.5; SPY since the 09:50 bar close
             <= +0.15%; |sma20_dist_pct| >= 1.5; window 11:00-15:00; easy-to-borrow (account-side live:
             shorts.require_easy_to_borrow; backtest: data/universe.csv flag).
  long       (ULT-03 trigger) RSI14 crossed below 50 on this bar or one of the 2 before (same session) AND RSI14 <= 30;
             fromOpen <= -1.0%; buyPressure (19-bar) > 0; NOT (spy_fo in [-0.75, -0.30] AND SPY 30-min change < 0);
             window 10:15-15:00.
  No SPY context -> no signal (fail safe).
Exit: unit Ru = M x atr_d; bracket +1 Ru limit / -1 Ru stop around the decision close (GEOM "S": stop_price and
      target_price), YAML time_stop_min 45, time_stop_min_r 99; flat 15:50 implied (last entry 15:00 + 45 min).
      R is per Ru.
Entry: ENTRY "MKT" = market at the next minute (the live LabStrategy default). ENTRY "LMT" (limit 0.1u better than the
      decision close, valid 10 min) is NOT expressible by the live LabStrategy / Signal (entry_type market|stop only);
      a LMT pick would need runner support first (see RESULTS.md).
refire (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain: >= 30 min
      after the first lot's exit, one lot per symbol across both sides). YAML: refire true, refire_cooldown 0.
Two sides, one file (as ULT-05/ULT-14): a setup name ending in "-S" / "-short" is the short side, else the long side.
Account-side: day cap 30 entries over both sides."""
import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen pick 16h m1-LMT-vol2.5 (round2/ULT-16/fitsel.json); set after the FIT grid, before any CHECK data.
# FAIL on fit (avg R -0.036); faithful build for the record only, NOT for deployment. ENTRY "LMT" cannot be expressed by
# the live LabStrategy (market entries only): run as is, this module would trade the MKT variant (16f).
M = 1.0                 # Ru = M x atr_d
ENTRY = "LMT"
VOL_FLOOR = 2.5         # atr_d % floor (0 = none)
# ----
GEOM = "S"
MIN_ADV = 150_000_000
COST_R_MAX = 0.10
WIN_SHORT = (1100, 1500)
WIN_LONG = (1015, 1500)
WINDOW = WIN_LONG if _SGN > 0 else WIN_SHORT
# short trigger (ULT-01)
GAP_MAX = -1.5
RSI5_RANGE = (60.0, 90.0)
LOD_ATR_MIN = 0.5
SPY_MAX_SINCE_0950 = 0.15
SMA20_BAND = 1.5
# long trigger (ULT-03)
CROSS_LEVEL, CROSS_BARS, RSI_MAX = 50.0, 3, 30.0
FROM_OPEN_MAX = -1.0
SPY_BAND = (-0.75, -0.30)
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.10 (u = 0.25 dATR), ADV20 >= $150M (YAML min_adv)",
] + (["RSI(14) crossed below 50 within the last 3 bars and <= 30", "down >= 1.0% from the open",
      "19-bar buy pressure > 0", "skip when SPY is -0.75..-0.30% from its open AND SPY's 30-min return < 0"]
     if _SGN > 0 else
     ["gap <= -1.5%", "60 <= RSI(5) < 90", "close >= 0.5 daily ATR above the low of day",
      "skip while SPY is up > +0.15% since the 09:50 bar close", "not within +-1.5% of the 5-min SMA20",
      "easy to borrow"]) + ([f"daily ATR >= {VOL_FLOOR:g}% of price"] if VOL_FLOOR > 0 else []) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    f"exit: +/-{M:g} daily ATR bracket, 45-min time exit",
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


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    import pandas as pd
    c = lambda k: df[k].to_numpy(dtype=float)
    n = len(df)
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    key = _keys(df).astype(object)
    mins = _minutes(tod)
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(n, np.nan)
    at950 = pd.Series(np.where(tod == 950, fo, np.nan)).groupby(key).transform("first").to_numpy(dtype=float)
    p30 = _lag(fo, 6, key, mins)
    rsi = c("rsi")
    with np.errstate(invalid="ignore", divide="ignore"):
        s950 = ((1 + fo / 100) / (1 + at950 / 100) - 1) * 100
        r30 = ((1 + fo / 100) / (1 + p30 / 100) - 1) * 100
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        atrp = atr / px * 100
        intake = (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= COST_R_MAX) & np.isfinite(fo)
        cr = (rsi < CROSS_LEVEL) & (_lag(rsi, 1, key, mins) >= CROSS_LEVEL)
    crossed = cr.copy()
    for k in range(1, CROSS_BARS):
        crossed |= _lag(cr.astype(float), k, key, mins) == 1.0
    return {"tod": tod, "close": px, "gap": c("gap"), "rsi": rsi, "rsi5": c("rsi5"), "lod": c("dist_lod_atr"),
            "sma20": c("sma20_dist_pct"), "fromOpen": c("fromOpen"), "bp": c("buyPressure"), "spy_fo": fo,
            "spy950": s950, "spy_r30": r30, "cost_r": cost_r, "atrp": atrp, "intake": intake, "crossed": crossed}


def trigger(r, sgn) -> np.ndarray:
    """Un-thinned trigger for one side (sgn +1 long / -1 short) inside that side's window (shared with bt.py).
    The vol floor is applied separately (vol_ok)."""
    tod = r["tod"]
    with np.errstate(invalid="ignore"):
        if sgn > 0:
            spy_ok = (np.isfinite(r["spy_fo"]) & np.isfinite(r["spy_r30"])
                      & ~((r["spy_fo"] >= SPY_BAND[0]) & (r["spy_fo"] <= SPY_BAND[1]) & (r["spy_r30"] < 0)))
            return (r["intake"] & r["crossed"] & (r["rsi"] <= RSI_MAX) & (r["fromOpen"] <= FROM_OPEN_MAX)
                    & (r["bp"] > 0) & spy_ok & (tod >= WIN_LONG[0]) & (tod <= WIN_LONG[1]))
        return (r["intake"] & (r["gap"] <= GAP_MAX) & (r["rsi5"] >= RSI5_RANGE[0]) & (r["rsi5"] < RSI5_RANGE[1])
                & (r["lod"] >= LOD_ATR_MIN) & (np.abs(r["sma20"]) >= SMA20_BAND)
                & (r["spy950"] <= SPY_MAX_SINCE_0950) & (tod >= WIN_SHORT[0]) & (tod <= WIN_SHORT[1]))


def vol_ok(r, floor) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return np.ones(len(r["tod"]), bool) if floor <= 0 else (r["atrp"] >= floor)


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
    m = trigger(r, _SGN) & vol_ok(r, VOL_FLOOR)
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S": stop 1 Ru = M x daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * M * float(f["atr_d"].iloc[i])


def target_price(f, i, stop) -> float:
    """Limit target 1 Ru = M x daily ATR beyond the decision close (symmetric bracket)."""
    return float(f["close"].iloc[i]) + _SGN * M * float(f["atr_d"].iloc[i])
