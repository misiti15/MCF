"""RW6G1-ns2-up3-vwap2sd-short-FD - FULL-DAY version of RW6G1-ns2-up3-vwap2sd-short (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py (copied; logic identical except the removed clause).
Removed: `(tod >= 950) & (tod <= 1130)` - the clause that limited WHEN the rule may fire (source module window 950-1130
ET bar close; source YAML window [950, 1130]).
Kept: every other condition; the owner's VWAP +2 SD band guard (vwap_band_block, copied verbatim, fail-safe without volume) stays.
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    RW6G1-ns2-up3-vwap2sd-short - RW6 (NS2 with fromOpen > 3%) plus the owner's VWAP band guard G1k2.
    Owner-directed to the primary account on probation 2026-10-09 (research/bdi/trendguard: nearest miss).

    Short when price crosses back ABOVE the 5-min SMA50 while overbought on a stock up > 3% from the open - but NOT while
    an excursion above the +2 SD VWAP band is unresolved: once a bar closes above VWAP + 2 SD, shorts are blocked until a
    bar closes at or below VWAP (the owner's "do not short above VWAP holding the +2 SD band; wait for a close back
    inside/below VWAP"). VWAP and its volume-weighted SD are built from today's 5-min bars (typical price), as in
    research/bdi/trendguard/features.py. Exit t1s1 (R = 0.25 x daily ATR, exit by 15:55).
    Source ran with min_adv 95000000 and window [950, 1130] (bar close ET).
    Two-year history (2024-09..2026-10, locked block excluded): n 424, +0.26R after costs, t 2.39 (required 4.76 for its
    try count), positive in up and down sessions, walk-forward share 0.63. NOT scored on the locked block. Probation.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "close crosses above the 5-min SMA50 on this bar",
    "stock up > 3% from the open",
    "RSI(14) >= 60",
    "no unresolved close above VWAP + 2 SD (owner VWAP band guard)",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def _keys(df):
    if "symbol" in df and "date" in df:     # offline frames hold many symbol-days
        return pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0]
    return np.zeros(len(df), dtype=np.int64)  # live: one symbol, today's bars


def vwap_band_block(df, k: float = 2.0) -> np.ndarray:
    """True on bars where a short is blocked: close above VWAP and a close above VWAP + k SD since the last close at
    or below VWAP (same day)."""
    if "volume" not in df:
        return np.ones(len(df), dtype=bool)  # fail safe: without volume the guard cannot be computed -> no trades
    key = _keys(df)
    h, l, c, v = (df[x].to_numpy(dtype=float) for x in ("high", "low", "close", "volume"))
    tp = (h + l + c) / 3
    g = pd.Series(key)
    cv = pd.Series(v).groupby(g).cumsum().to_numpy().copy()
    cv[cv == 0] = np.nan
    vw = pd.Series(tp * v).groupby(g).cumsum().to_numpy() / cv
    var = pd.Series(tp * tp * v).groupby(g).cumsum().to_numpy() / cv - vw * vw
    sd = np.sqrt(np.clip(var, 0, None))
    with np.errstate(invalid="ignore"):
        beyond = c - vw > 0
        seg = pd.Series((~beyond).astype(np.int64)).groupby(g).cumsum().to_numpy()
        band = c - (vw + k * sd) > 0
        flag = pd.Series(band).groupby(key.astype(np.int64) * 100_000 + seg).cummax().to_numpy()
    return beyond & flag


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    key = _keys(df)
    sma50 = col("sma50_dist_pct")
    p_sma50 = np.r_[np.nan, sma50[:-1]]
    p_sma50[np.r_[True, key[1:] != key[:-1]]] = np.nan
    rsi, fo, tod = col("rsi"), col("fromOpen"), col("tod")
    with np.errstate(invalid="ignore"):
        base = (sma50 > 0) & (p_sma50 <= 0) & (fo > 3) & (rsi >= 60)
    return base & ~vwap_band_block(df)
