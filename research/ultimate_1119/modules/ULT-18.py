# ULTIMATE CANDIDATE ULT-18 XS-MOMREV (research only, not enabled in any account)
# research/ultimate_1119/round2/PLAN.md sec. 3 "ULT-18"; backtest research/ultimate_1119/round2/ULT-18/RESULTS.md
# Next: only a TIER A / BEATS result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-18 XS-MOMREV - cross-sectional momentum / reversal book at fixed times, LONG and SHORT.

At the 11:00, 13:00 and 14:00 decision bars (5-minute bar close, ET) every eligible name is ranked by a key:
  K1  fromOpen in daily-ATR units = (close - open_0930) / atr_d
  K2  sector-relative = (fromOpen% - beta x sector-ETF fromOpen%) / atr_d%   (sector ETF + beta from the point-in-time
      sector map: argmax corr of prior <= 60 daily returns, OLS beta clipped [0.3, 3]; columns sec_fo / sec_beta)
MOM = long the top N, short the bottom N; REV = long the bottom N, short the top N. Exit TX45: 45-minute time exit with a
catastrophic stop 2u beyond the decision close (u = 0.25 x daily ATR, GEOM "S"); flat 15:50.
Eligibility (all point-in-time):
  intake  non-ETF (YAML `symbols: module` = SYMBOLS, the frozen lab stock list), ADV20 >= $200M (YAML min_adv),
          price >= $10, |gap| < 20%, atr_d > 0, cost_r <= 0.06 (LR8 stop round trip ((1c + 1bp) x tod mult + 1c + 1bp
          + 2c) / u)
  long    universal filter: not (SPY from open in [-0.75%, -0.30%] and SPY 30-min change < 0); needs spy_fo context
  short   gap < +0.5% and RSI(5) >= 25 (and easy-to-borrow: broker side live, universe.csv ETB in the backtest)
  An excluded name is replaced by the next eligible one (the rank is taken over eligible names only).

Cross-section: a LabStrategy mask sees ONE symbol's frame, so the rank needs the cross-section of the decision bar.
`select_book(xs, key, direction, n, blocked)` takes that cross-section (one row per name: symbol, k1/k2, ok_long,
ok_short, adv20) and returns the selected (symbol, side) list plus the per-side key cut-offs. The backtest
(round2/ULT-18/bt.py) calls exactly this function. Live, a runner hook must call `set_book(date, tod, cutoffs)` once
per decision bucket with the cut-offs computed from every polled name's frame (the runner already builds those frames);
`mask` then fires for a name whose own key is at or beyond its side's cut-off (equivalent to membership in the top /
bottom N, ties aside). No book set for that bucket -> no signal (fail safe). That hook is NOT in the runner today
(live gap, documented in RESULTS.md); with K2 the live frame also lacks sec_fo / sec_beta (same gap as ULT-11).
Two sides, one file: the account carries TWO `type: lab` entries pointing at this file; the side comes from the setup
name (ending "-S" / "-short" = short side). YAML: window [1100, 1400], min_adv 200000000, context [spy_fo], geom S,
time_stop_min 45, time_stop_min_r 99, refire true, refire_cooldown 0, symbols: module. Account side: one lot per symbol,
refire >= 30 min after the exit, max 2 per symbol-session, day cap 6N."""
import json
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
GEOM = "S"
# ---- defaults = the fit-frozen pick (round2/ULT-18/fitsel.json); bt.py passes every config explicitly
KEY = "k2"
DIRECTION = "MOM"
N = 5
# ----
TIMES = (1100, 1300, 1400)
WINDOW = (1100, 1400)
MIN_ADV = 200_000_000
COST_R_MAX = 0.06
HOLD_MIN = 45
SYMBOLS = frozenset(json.loads((Path(__file__).resolve().parent / "ULT-12_symbols.json").read_text())["S"])
LAYERS = [
    "intake: non-ETF lab stock list, ADV20 >= $200M, price >= $10, |gap| < 20%, cost_r <= 0.06",
    "side filters: long not into a falling SPY (-0.30..-0.75% from open and 30-min < 0); short gap < +0.5%, RSI5 >= 25",
    "cross-sectional rank at 11:00 / 13:00 / 14:00 by fromOpen (dATR) or sector-relative fromOpen; top / bottom N",
    "exit: 45-minute time exit, 2u catastrophic stop",
]
_BOOK = {}   # (date 'YYYY-MM-DD', tod) -> {"long": cutoff or None, "short": cutoff or None, "key", "direction"}


def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _m2(t):
    t = np.asarray(t, float)
    return np.floor(t / 100) * 60 + t % 100


def _col(df, k):
    return df[k].to_numpy(dtype=float) if k in df.columns else np.full(len(df), np.nan)


def _keys(df):
    import pandas as pd
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    elif "ts" in df:
        day = pd.DatetimeIndex(df["ts"]).strftime("%Y-%m-%d").to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        return df["symbol"].astype(str).to_numpy() + "|" + day, day
    return day, day


def cost_r(df) -> np.ndarray:
    px, atr, tod = _col(df, "close"), _col(df, "atr_d"), _col(df, "tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        return (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)


def spy_r30(df) -> np.ndarray:
    """SPY 30-min change (%) from the spy_fo context column of the same day: (1+fo_t)/(1+fo_{t-30}) - 1."""
    import pandas as pd
    key, _ = _keys(df)
    mins = _m2(_col(df, "tod"))
    fo = _col(df, "spy_fo")
    s = pd.Series(fo, index=pd.MultiIndex.from_arrays([key, mins]))
    s = s[~s.index.duplicated()]
    lag = s.reindex(pd.MultiIndex.from_arrays([key, mins - 30])).to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return ((1 + fo / 100) / (1 + lag / 100) - 1) * 100


def features(df) -> dict:
    """Point-in-time keys and eligibility at every row (only the row's own bar, the day's open, prior-day ATR / ADV,
    the SPY context and the prior-session sector map are used)."""
    c, atr, tod, gap = _col(df, "close"), _col(df, "atr_d"), _col(df, "tod"), _col(df, "gap")
    fo = _col(df, "fromOpen")
    with np.errstate(invalid="ignore", divide="ignore"):
        op = c / (1 + fo / 100)
        atrp = atr / c * 100
        k1 = (c - op) / atr
        k2 = (fo - _col(df, "sec_beta") * _col(df, "sec_fo")) / atrp
        cr = cost_r(df)
        base = (c >= 10) & (np.abs(gap) < 20) & (atr > 0) & (cr <= COST_R_MAX) & np.isin(tod, TIMES)
        if "adv20" in df.columns:          # history frames; live: YAML min_adv on the runner's ADV
            base &= np.nan_to_num(_col(df, "adv20")) >= MIN_ADV
        if "symbol" in df.columns:         # history frames; live: YAML symbols: module
            base &= df["symbol"].astype(str).isin(SYMBOLS).to_numpy()
        sfo, r30 = _col(df, "spy_fo"), spy_r30(df)
        ok_long = base & np.isfinite(sfo) & ~((sfo >= -0.75) & (sfo <= -0.30) & (r30 < 0))
        ok_short = base & (gap < 0.5) & (_col(df, "rsi5") >= 25)
    return {"tod": tod, "k1": k1, "k2": k2, "cost_r": cr, "ok_long": ok_long, "ok_short": ok_short, "spy_r30": r30}


def select_book(xs, key: str, direction: str, n: int, blocked=frozenset()):
    """xs: one decision moment's cross-section (columns symbol, k1/k2, ok_long, ok_short, adv20). Returns
    (picks [(symbol, side)], cutoffs {"long": k or None, "short": k or None}). Ranking over eligible, non-blocked names
    with a finite key; ties by ADV20 desc then symbol. MOM: long top N / short bottom N; REV: the opposite.
    A name never takes both sides (the long book is chosen first)."""
    k = xs[key].to_numpy(float)
    fin = np.isfinite(k)
    notb = ~xs["symbol"].astype(str).isin(set(blocked)).to_numpy()
    adv = np.nan_to_num(xs["adv20"].to_numpy(float)) if "adv20" in xs else np.zeros(len(xs))
    sym = xs["symbol"].astype(str).to_numpy()
    long_high = direction == "MOM"          # MOM long = highest keys; REV long = lowest keys
    picks, cut, used = [], {"long": None, "short": None}, set()
    for side, sgn in (("long", 1), ("short", -1)):
        ok = xs[f"ok_{side}"].to_numpy(bool) & fin & notb
        idx = np.flatnonzero(ok)
        hi = long_high if sgn > 0 else not long_high
        order = np.lexsort((sym[idx], -adv[idx], -k[idx] if hi else k[idx]))
        got = []
        for j in idx[order]:
            if sym[j] in used:
                continue
            got.append(j)
            if len(got) >= n:
                break
        for j in got:
            used.add(sym[j]); picks.append((sym[j], side))
        if got:
            cut[side] = float(k[got[-1]])
    return picks, cut


def set_book(date: str, tod: int, cutoffs: dict, key: str = None, direction: str = None):
    """Runner hook (not in the runner today): the per-side key cut-offs of this decision bucket (from select_book)."""
    if len(_BOOK) > 64:
        _BOOK.clear()
    _BOOK[(str(date), int(tod))] = dict(cutoffs, key=key or KEY, direction=direction or DIRECTION)


def mask(df) -> np.ndarray:
    if "spy_fo" not in df.columns:          # fail safe: no market context -> no signal
        return np.zeros(len(df), bool)
    F = features(df)
    _, day = _keys(df)
    ok = F["ok_long"] if _SGN > 0 else F["ok_short"]
    out = np.zeros(len(df), bool)
    for i in np.flatnonzero(ok):
        b = _BOOK.get((day[i], int(F["tod"][i])))
        if not b or b.get(SIDE) is None:
            continue
        k = F[b["key"]][i]
        if not np.isfinite(k):
            continue
        hi = (b["direction"] == "MOM") == (_SGN > 0)
        out[i] = k >= b[SIDE] if hi else k <= b[SIDE]
    return out


def stop_price(f, i) -> float:
    """GEOM "S": catastrophic stop 2u = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
