"""ULT-02-tapeflush-washout-long - "Tape-flush washout long (S4)", ultimate_1119 candidate (Workbench Mechanic 2026-11-19).

Thesis (research/ultimate_1119/PLAN.md sec. 3, ULT-02): when SPY has dropped more than |SPY_T| over the last 30 minutes,
names that are already washed out (far below their open, or far off their high of day, in daily-ATR units) snap back
with the tape. Long only.

Rule at a 5-minute decision bar close (point-in-time: only bars closed at the decision bar + prior-session daily ATR):
  - intake: close >= $10; stop-exit round-trip cost (2 x (1c + 1 bp) + 2c) <= COST_R_MAX of 1R (1R = 0.25 x daily ATR);
    |gap| < 20%; daily ATR known. ADV20 >= $20M is the YAML `min_adv` (the live 20-day dollar volume).
  - trigger: from_open_atr = (close - today's open) / daily ATR <= -D1   OR   dist_hod_atr (HOD - close) / ATR >= D2
  - gate:    spy_r30 = SPY 5-min close / SPY 5-min close 30 minutes (6 bars) earlier - 1 < SPY_T, computed from the lab
             context column `spy_fo` (SPY % from its first 5-min open, same bar): (1 + fo_t) / (1 + fo_{t-30}) - 1.
             The earlier row must be exactly 30 minutes before (tod check); otherwise NaN -> no fire (fail safe).
  - window:  bar close 10:30-15:00 ET = YAML window [1030, 1500].
Exit (YAML; the fit-selected config is recorded in research/ultimate_1119/ULT-02-tapeflush-washout-long/RESULTS.md):
  TX30 / TX45 = geom "hold" with a catastrophic stop at 2R (YAML r_atr_frac 0.5, i.e. 2 x 0.25 x ATR) and a fixed time
  exit (time_stop_min 30/45, time_stop_min_r 1e9 = unconditional); t1s1 cap45 = geom t1s1 + time_stop_min 45.
Refire: refire true with a cooldown in decision bars (the research rule is "30 minutes after the exit, max 2 per
symbol-session, day cap 30"; live approximations are listed in RESULTS.md).

Research only (ultimate_1119): NOT deployed. Only a TIER A result may go to a testing arena, and only through the normal
Workbench / ledger rules with owner approval, outside market hours. Educational only - not financial advice.
"""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "hold"          # TX exits: no target; the 2R catastrophic stop comes from YAML r_atr_frac 0.5

# Fit-selected parameters (frozen in research/ultimate_1119/ULT-02-tapeflush-washout-long/fitsel.json before any
# check-half data was loaded): config 02k = SPY_T -0.50%, depth B (D1 1.5 / D2 2.0), exit TX45. Check-half result:
# FAIL (RESULTS.md) - kept only as the faithful build of the pre-registered candidate; NOT for deployment.
SPY_T = -0.50          # SPY 30-min return threshold, %
D1 = 1.5               # from_open_atr <= -D1
D2 = 2.0               # dist_hod_atr >= D2
COST_R_MAX = 0.10
MIN_PRICE = 10.0
MAX_ABS_GAP = 20.0

LAYERS = [
    f"close >= ${MIN_PRICE:.0f}, |gap| < {MAX_ABS_GAP:.0f}%, stop-exit round-trip cost <= {COST_R_MAX} of 1R (intake U)",
    f"washout: (close - open) / daily ATR <= -{D1} OR (HOD - close) / daily ATR >= {D2}",
    f"tape flush: SPY 30-min return (6 closed 5-min bars, from spy_fo) < {SPY_T}%",
    "window: bar close 10:30-15:00 ET (YAML window [1030, 1500])",
]


def _minutes(tod):
    t = np.asarray(tod, dtype=float)
    return (t // 100) * 60 + t % 100


def spy_r30(df) -> np.ndarray:
    """SPY 30-minute return (%) at each row, from `spy_fo` of the same frame (rows of one symbol-day in time order).
    Works on the live frame (one symbol, today's bars) and on multi-symbol history frames (columns symbol and date,
    sorted by symbol, date, tod as research/history2y/lib.load_month returns them)."""
    fo = df["spy_fo"].to_numpy(dtype=float)
    mins = _minutes(df["tod"].to_numpy())
    n = len(fo)
    out = np.full(n, np.nan)
    if n <= 6:
        return out
    if "symbol" in df.columns and "date" in df.columns:
        key = pd.factorize(pd.MultiIndex.from_arrays([df["symbol"].astype(str).to_numpy(),
                                                      df["date"].astype(str).to_numpy()]))[0]
    else:
        key = np.zeros(n, dtype=np.int64)
    prev_fo = np.r_[np.full(6, np.nan), fo[:-6]]
    prev_m = np.r_[np.full(6, np.nan), mins[:-6]]
    prev_k = np.r_[np.full(6, -1), key[:-6]]
    ok = (prev_k == key) & (mins - prev_m == 30)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = ((1 + fo / 100) / (1 + prev_fo / 100) - 1) * 100
    out[ok] = r[ok]
    return out


def make_mask(spy_t=SPY_T, d1=D1, d2=D2, cost_r_max=COST_R_MAX):
    """mask(df) for one grid configuration (research backtest); the module-level `mask` uses the frozen values."""
    def _mask(df) -> np.ndarray:
        def c(k):
            return df[k].to_numpy(dtype=float)

        close, atr = c("close"), c("atr_d")
        with np.errstate(invalid="ignore", divide="ignore"):
            R = 0.25 * atr
            cost_r = (2 * (0.01 + close * 1e-4) + 0.02) / R
            day_open = close / (1 + c("fromOpen") / 100)
            from_open_atr = (close - day_open) / atr
            washout = (from_open_atr <= -d1) | (c("dist_hod_atr") >= d2)
            return ((close >= MIN_PRICE) & (atr > 0) & (np.abs(c("gap")) < MAX_ABS_GAP) & (cost_r <= cost_r_max)
                    & washout & (spy_r30(df) < spy_t))
    return _mask


def mask(df) -> np.ndarray:
    return make_mask()(df)
