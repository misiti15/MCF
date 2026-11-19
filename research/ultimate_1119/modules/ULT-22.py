# ULTIMATE CANDIDATE ULT-22 WB4-WIDE (research only, not enabled in any account)
# research/ultimate_1119/round3/PLAN.md sec. 3 "ULT-22"; backtest research/ultimate_1119/round3/ULT-22/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-22 WB4-WIDE - WB4's own trigger, more hours and an ATR-scaled twin, basket ETFs only, LONG. CHECK-INFORMED.

Triggers (indicators via mcf.research.arena.indicators.compute on the frame passed in, as WB4 / ULT-12):
  "P" (WB4 exact): ret3 <= -0.75% AND ret12 >= -1.0% AND di_diff7 >= -5 AND atr_d_pct >= 3.5967583179473883
  "A" (ATR-scaled): ret3 <= -0.21 x atr_d_pct AND ret12 >= -0.28 x atr_d_pct AND di_diff7 >= -5 AND atr_d_pct >= 2.4
Intake: price >= $10; |gap| < 20%; atr_d > 0; cost_r <= COST_R_MAX[TRIG] (P 0.10, A 0.08; LR8 stop-out round trip
  ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $95M via the YAML min_adv.
Universal long filter: skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0 (YAML
  `context: [spy_fo]`; no SPY context -> no signal, fail safe).
Universe UNIV (YAML `symbols: module` = SYMBOLS, ULT-22_symbols.json): "W" exact WB4 ETF list (124), "Q" EQB =
  WB4 + other equity-basket ETFs of >= 10 stocks (167; no single-stock / commodity / crypto / vol / bond funds).
Window: bar close WINDOW (inclusive). Refire (THIN): max 2 per symbol-session, 2nd >= REFIRE_BARS bars after the 1st
  (backtest chain is stricter: >= 30 min after the first lot's EXIT). YAML: refire true, refire_cooldown 0.
Exit: GEOM t05s1 (+0.5 u limit / -1 u stop around the decision close), YAML time_stop_min 45, time_stop_min_r 99."""
import json
from pathlib import Path

import numpy as np

from mcf.research.arena.indicators import compute

SIDE = "long"
GEOM = "t05s1"
# ---- fit-frozen pick 22b (round3/ULT-22/fitsel.json, frozen 2026-11-19 before any CHECK data)
UNIV = "W"
TRIG = "P"
WINDOW = (1230, 1500)
# ----
RET3_PCT, RET12_PCT = -0.75, -1.0
RET3_K, RET12_K = -0.21, -0.28
DI_MIN = -5.0
ATR_PCT_MIN = {"P": 3.5967583179473883, "A": 2.4}
COST_R_MAX = {"P": 0.10, "A": 0.08}
MIN_ADV = 95e6
REFIRE_BARS, MAX_PER_DAY = 6, 2
THIN = True
_U = json.loads((Path(__file__).resolve().parent / "ULT-22_symbols.json").read_text())
UNIVERSES = {"W": frozenset(_U["W"]), "Q": frozenset(_U["Q"])}
SYMBOLS = UNIVERSES[UNIV]
LAYERS = [
    f"universe {UNIV} ({'WB4 ETF list' if UNIV == 'W' else 'equity-basket ETFs'}; YAML symbols: module; min_adv $95M)",
    f"intake: price >= $10, |gap| < 20%, cost_r <= {COST_R_MAX[TRIG]}",
    ("15-min return <= -0.75% and 60-min return >= -1.0%" if TRIG == "P"
     else "15-min return <= -0.21 x daily ATR% and 60-min return >= -0.28 x daily ATR%"),
    "+DI(7) - -DI(7) >= -5", f"daily ATR >= {ATR_PCT_MIN[TRIG]:.1f}% of price",
    "skip while SPY is -0.30..-0.75% from its open and falling over 30 min",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET", "exit: +0.5R / -1R, 45-min time exit",
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
    x = compute(df, names=["atr_d_pct", "di_diff7", "ret3", "ret12"], context=False)
    c = lambda k: df[k].to_numpy(dtype=float)
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        fo = c("spy_fo") if "spy_fo" in df.columns else np.full(len(df), np.nan)
        r30 = spy_r30(df) if "spy_fo" in df.columns else np.full(len(df), np.nan)
        intake = (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= max(COST_R_MAX.values())) & np.isfinite(fo)
        univ_ok = ~((fo <= -0.30) & (fo >= -0.75) & (r30 < 0))
    return {"tod": tod, "close": px, "ret3": x["ret3"].to_numpy(float), "ret12": x["ret12"].to_numpy(float),
            "di7": x["di_diff7"].to_numpy(float), "atrp": x["atr_d_pct"].to_numpy(float), "cost_r": cost_r,
            "intake": intake, "univ_ok": univ_ok, "spy_fo": fo, "spy_r30": r30}


def trigger(r, trig) -> np.ndarray:
    """Trigger P or A including its own cost_r cap (the intake applies the looser 0.10)."""
    a = r["atrp"]
    with np.errstate(invalid="ignore"):
        if trig == "P":
            d = (r["ret3"] <= RET3_PCT) & (r["ret12"] >= RET12_PCT)
        else:
            d = (r["ret3"] <= RET3_K * a) & (r["ret12"] >= RET12_K * a)
        return d & (r["di7"] >= DI_MIN) & (a >= ATR_PCT_MIN[trig]) & (r["cost_r"] <= COST_R_MAX[trig])


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
    m = r["intake"] & r["univ_ok"] & trigger(r, TRIG) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    if "symbol" in getattr(df, "columns", ()):
        m &= df["symbol"].astype(str).isin(SYMBOLS).to_numpy()
    return _thin(m, df) if THIN else m
