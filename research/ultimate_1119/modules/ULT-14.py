# ULTIMATE CANDIDATE ULT-14 SNAP (research only, not enabled in any account)
# research/ultimate_1119/round2/PLAN.md sec. 3 "ULT-14"; backtest research/ultimate_1119/round2/ULT-14/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-14 SNAP - a sharp 15-min counter-move against a still-intact trend, LONG and SHORT, ATR-scaled.

Rule (all point-in-time, at the decision 5-minute bar close; indicators via mcf.research.arena.indicators.compute):
  intake U2  price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.08 (LR8 stop-out round trip
             ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $50M via the YAML min_adv
  long       ret3_atr <= -D (15-min change of 5-min closes in daily ATRs) AND di_diff7 >= 0 (+DI(7) - -DI(7), in-day)
             AND buyPressure (19-bar) > 0 AND atr_d_pct >= 3.0 AND SPY 60-min change > -0.40%
  short      ret3_atr >= +D AND di_diff7 <= 0 AND buyPressure < 0 AND gap < +0.5% AND 25 <= RSI5 < 90 AND
             SPY since the 09:50 bar close <= +0.20%; easy-to-borrow (account-side live: shorts.require_easy_to_borrow;
             backtest: data/universe.csv flag)
  Build rules fixed before any fit scoring: (a) the long side has its own tape rule (SPY 60-min), so the chassis'
  universal SPY long filter is NOT added (PLAN sec. 2 "except where a candidate states a tape rule of its own");
  the universal short filters (gap >= +0.5%, RSI5 < 25) are kept. (b) SPY 60-min change / since-09:50 change come from
  the spy_fo context column at the same session's bar 60 min earlier / the 09:50 bar; when that row is missing the
  side does not fire (fail safe; both windows start >= 11:00, so it never binds in the lab frames).
  window     bar close WINDOW (inclusive; YAML window must match). No SPY context -> no signal (fail safe).
  refire     (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain:
             >= 30 min after the first lot's exit, one lot per symbol across both sides). YAML: refire true,
             refire_cooldown 0.
Two sides, one file (as ULT-05): LabStrategy has one side per setup, so the account carries TWO `type: lab` entries
pointing at this file; a setup name ending in "-S" / "-short" is the short side, anything else the long side.
Exit: GEOM t05s1 (+0.5u / -1u) or t1s1 (+1u / -1u) around the decision close, YAML time_stop_min 45,
time_stop_min_r 99; flat 15:50 implied (last entry 15:00 + 45 min). Account-side: day cap 30 entries over both sides."""
import numpy as np

from mcf.research.arena.indicators import compute

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen pick 14a (round2/ULT-14/fitsel.json); set after the FIT grid, before any CHECK data
WINDOW = (1400, 1500)
D = 0.20
GEOM = "t05s1"
# ----
MIN_ADV = 50_000_000
COST_R_MAX = 0.08
ATR_PCT_MIN = 3.0
SPY60_MIN = -0.40          # long: SPY 60-min change > -0.40%
SPY950_MAX = 0.20          # short: SPY since 09:50 <= +0.20%
GAP_SHORT_MAX = 0.5        # short: gap < +0.5% (universal short filter; spec "gap <= +0.5%")
RSI5_SHORT = (25.0, 90.0)  # short: 25 <= RSI5 < 90 (25 = universal short filter)
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
LAYERS = [
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.08, ADV20 >= $50M (YAML min_adv)",
    (f"15-min drop >= {D:g} daily ATR" if _SGN > 0 else f"15-min pop >= {D:g} daily ATR"),
    ("+DI(7) >= -DI(7) (trend still up)" if _SGN > 0 else "+DI(7) <= -DI(7) (trend still down)"),
    ("19-bar buy pressure > 0" if _SGN > 0 else "19-bar buy pressure < 0"),
] + (["daily ATR >= 3.0% of price", "SPY 60-min change > -0.40%"] if _SGN > 0 else
     ["gap < +0.5%", "25 <= RSI(5) < 90", "SPY since the 09:50 bar close <= +0.20%", "easy to borrow"]) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    f"exit: {'+0.5R' if GEOM == 't05s1' else '+1R'} / -1R, 45-min time exit",
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


def _spy_lag(df, lag_min=None) -> np.ndarray:
    """SPY % change from spy_fo: over the last lag_min minutes (same session, bar closes >= 09:50), or since the 09:50
    bar close when lag_min is None. NaN without the reference row."""
    import pandas as pd
    fo = df["spy_fo"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    key = _keys(df)
    if lag_min is None:
        ref = pd.Series(np.where(tod == 950, fo, np.nan)).groupby(key).transform("first").to_numpy(dtype=float)
    else:
        m = _minutes(tod)
        s = pd.Series(np.where(tod >= 950, fo, np.nan), index=pd.MultiIndex.from_arrays([key, m]))
        s = s[~s.index.duplicated()]
        ref = s.reindex(pd.MultiIndex.from_arrays([key, m - lag_min])).to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return ((1 + fo / 100) / (1 + ref / 100) - 1) * 100


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    x = compute(df, names=["ret3_atr", "di_diff7", "atr_d_pct"], context=False)
    c = lambda k: df[k].to_numpy(dtype=float)
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    has_spy = "spy_fo" in df.columns
    n = len(df)
    fo = c("spy_fo") if has_spy else np.full(n, np.nan)
    s60 = _spy_lag(df, 60) if has_spy else np.full(n, np.nan)
    s950 = _spy_lag(df, None) if has_spy else np.full(n, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        intake = (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= COST_R_MAX) & np.isfinite(fo)
    return {"tod": tod, "close": px, "r3a": x["ret3_atr"].to_numpy(float), "di7": x["di_diff7"].to_numpy(float),
            "atrp": x["atr_d_pct"].to_numpy(float), "bp": c("buyPressure"), "gap": c("gap"), "rsi5": c("rsi5"),
            "cost_r": cost_r, "intake": intake, "spy_fo": fo, "spy60": s60, "spy950": s950}


def trigger(r, sgn, d) -> np.ndarray:
    """Un-thinned, un-windowed trigger for one side (sgn +1 long / -1 short) at threshold d (shared with bt.py)."""
    with np.errstate(invalid="ignore"):
        if sgn > 0:
            return (r["intake"] & (r["r3a"] <= -d) & (r["di7"] >= 0) & (r["bp"] > 0) & (r["atrp"] >= ATR_PCT_MIN)
                    & (r["spy60"] > SPY60_MIN))
        return (r["intake"] & (r["r3a"] >= d) & (r["di7"] <= 0) & (r["bp"] < 0) & (r["gap"] < GAP_SHORT_MAX)
                & (r["rsi5"] >= RSI5_SHORT[0]) & (r["rsi5"] < RSI5_SHORT[1]) & (r["spy950"] <= SPY950_MAX))


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
    m = trigger(r, _SGN, D) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return _thin(m, df) if THIN else m
