"""ULT-06-late-morning-turn-long - "Late morning-turn long", ultimate_1119 candidate (Workbench Mechanic 2026-11-19).

Thesis (research/ultimate_1119/PLAN.md sec. 3, ULT-06): a new low of day printed after 09:50 and then reclaimed around
11:00 is the "morning turn"; applied per name, with the SPY tape turning as well. Long only.

Rule at a 5-minute decision bar close (point-in-time: only 5-minute bars closed at the decision bar + prior-session
daily ATR; the low of day comes from the frame's dist_lod_atr = (close - today's running low) / daily ATR):
  - intake U: close >= $10; stop-exit round-trip cost (2 x (1c + 1 bp) + 2c) <= COST_R_MAX of 1R (1R = 0.25 x daily
    ATR); |gap| < 20%; daily ATR known. ADV20 >= $20M is the YAML `min_adv`.
  - new low: one of the last 6 decision bars (this bar and the 5 before it, same symbol-day) has a 5-minute low strictly
    below the running low of day as of the bar before it, and that bar closes at 09:55 or later (its low is printed
    after 09:50). The running low is close - dist_lod_atr x atr_d (it includes 09:30-09:50).
  - reclaim: dist_lod_atr (close above the low of day, in daily ATR) >= RCL.
  - fromOpen < 0 (still below today's open) and rsiSlope > 0 (RSI14 up over the last 3 bars).
  - SPY turn gate: SPY close >= 0.10% above SPY's lowest 5-minute close since 09:50 (the 09:50 bar close included,
    the current bar included), from the context column `spy_fo`: (1 + fo_t) / (1 + min fo_{09:50..t}) - 1 >= 0.10%.
    On multi-symbol history frames the SPY running minimum is built from the (date, tod) table of every symbol, so a
    symbol's missing 5-minute rows cannot drop a SPY low; on the live frame (one symbol-day) it uses that day's rows.
  - window: bar close inside W (YAML window; W1 [1050, 1130] or W2 [1030, 1200]).
Exit (YAML): TX30 / TX45 = geom "hold" with a catastrophic stop at 2R (YAML r_atr_frac 0.5 = 2 x 0.25 x ATR) and an
unconditional time exit (time_stop_min 30/45, time_stop_min_r 1e9).
Refire: refire true + refire_cooldown (the research rule "30 min after exit, max 2 per symbol-session, day cap 30" is
approximated live; see research/ultimate_1119/ULT-06-late-morning-turn-long/RESULTS.md).

Research only (ultimate_1119): NOT deployed. Only a TIER A result may go to a testing arena, and only through the normal
Workbench / ledger rules with owner approval, outside market hours. Educational only - not financial advice.
"""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "hold"          # TX exits: no target; the 2R catastrophic stop comes from YAML r_atr_frac 0.5

# Frozen values = the fit-selected config 06a (fitsel.json, frozen before any check data was loaded): W1 = YAML window
# [1050, 1130], RCL 0.3, exit TX30. Check-half result: FAIL (RESULTS.md) - kept only as the faithful build; NOT for deployment.
RCL = 0.3              # dist_lod_atr >= RCL
SPY_TURN = 0.10        # SPY close vs its lowest 5-min close since 09:50, %
LOOKBACK = 6           # new low within the last 6 decision bars (current included)
COST_R_MAX = 0.10
MIN_PRICE = 10.0
MAX_ABS_GAP = 20.0

LAYERS = [
    f"close >= ${MIN_PRICE:.0f}, |gap| < {MAX_ABS_GAP:.0f}%, stop-exit round-trip cost <= {COST_R_MAX} of 1R (intake U)",
    f"new low of day printed after 09:50 within the last {LOOKBACK} 5-min bars",
    f"reclaim: (close - LOD) / daily ATR >= {RCL}; below today's open; RSI14 slope > 0",
    f"SPY turn: SPY close >= {SPY_TURN}% above its lowest 5-min close since 09:50",
]


def _keys(df) -> np.ndarray:
    n = len(df)
    if "symbol" in df.columns and "date" in df.columns:
        return pd.factorize(pd.MultiIndex.from_arrays([df["symbol"].astype(str).to_numpy(),
                                                      df["date"].astype(str).to_numpy()]))[0]
    return np.zeros(n, dtype=np.int64)


def new_low_recent(df, lookback=LOOKBACK) -> np.ndarray:
    """True where one of the last `lookback` rows of the same symbol-day (current included) printed a new low of day
    (5-min low < running LOD of the row before) and that row's bar closes at 09:55 or later."""
    c = df["close"].to_numpy(dtype=float)
    lod = c - df["dist_lod_atr"].to_numpy(dtype=float) * df["atr_d"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy()
    key = _keys(df)
    n = len(c)
    prev_lod = np.r_[np.nan, lod[:-1]]
    same = np.r_[False, key[1:] == key[:-1]]
    with np.errstate(invalid="ignore"):
        nl = same & (low < prev_lod - 1e-7 * np.abs(prev_lod)) & (tod >= 955)
    out = nl.copy()
    for k in range(1, lookback):
        sh = np.r_[np.zeros(k, bool), nl[:-k]] if n > k else np.zeros(n, bool)
        kk = np.r_[np.full(k, -1), key[:-k]] if n > k else np.full(n, -1)
        out |= sh & (kk == key)
    return out


def spy_turn(df) -> np.ndarray:
    """SPY close vs its lowest 5-min close since 09:50 (inclusive, current bar inclusive), in %. NaN before 09:50."""
    fo = df["spy_fo"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy()
    if "date" in df.columns:
        d = df["date"].astype(str).to_numpy()
    else:
        d = np.zeros(len(df), dtype=object)
    t = pd.DataFrame({"d": d, "tod": tod, "fo": fo})
    t = t[(t.tod >= 950) & np.isfinite(t.fo)]
    tab = t.groupby(["d", "tod"], sort=True)["fo"].first().reset_index()
    tab["mn"] = tab.groupby("d")["fo"].cummin()
    m = pd.DataFrame({"d": d, "tod": tod}).merge(tab[["d", "tod", "mn"]], on=["d", "tod"], how="left")["mn"].to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        return ((1 + fo / 100) / (1 + m / 100) - 1) * 100


def make_mask(rcl=RCL, spy_t=SPY_TURN, cost_r_max=COST_R_MAX):
    """mask(df) for one grid configuration (the window is the YAML / backtest window)."""
    def _mask(df) -> np.ndarray:
        def c(k):
            return df[k].to_numpy(dtype=float)

        close, atr = c("close"), c("atr_d")
        with np.errstate(invalid="ignore", divide="ignore"):
            cost_r = (2 * (0.01 + close * 1e-4) + 0.02) / (0.25 * atr)
            return ((close >= MIN_PRICE) & (atr > 0) & (np.abs(c("gap")) < MAX_ABS_GAP) & (cost_r <= cost_r_max)
                    & new_low_recent(df) & (c("dist_lod_atr") >= rcl) & (c("fromOpen") < 0) & (c("rsiSlope") > 0)
                    & (spy_turn(df) >= spy_t))
    return _mask


def mask(df) -> np.ndarray:
    return make_mask()(df)
