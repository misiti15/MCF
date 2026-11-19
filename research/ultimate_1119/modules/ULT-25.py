# ULTIMATE CANDIDATE ULT-25 ULTRA-CHEAP (research only, not enabled in any account)
# research/ultimate_1119/round3/PLAN.md sec. 3 "ULT-25"; backtest research/ultimate_1119/round3/ULT-25/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-25 ULTRA-CHEAP - the strongest relative-edge triggers only where cost per R is lowest, LONG + SHORT.
CHECK-INFORMED (TS-1 / TS-2 short triggers and the one-bar RSI collapse, round3/PLAN.md sec. 0.5).

Rule (all point-in-time, at the decision 5-minute bar close; frame columns rsi = RSI(14), rsi5 = RSI(5), buyPressure =
19-bar, dist_lod_atr = (close - LOD) / atr_d, sma20_dist_pct, upper_wick; ret3 / ret12 / di_diff7 / atr_d_pct via
mcf.research.arena.indicators.compute as WB4 / ULT-22):
  universe   price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.03 (LR8 stop-out round trip
             ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d - NOT the trade unit); ADV20 >= $300M
             (frame adv20 in the backtest; live = YAML min_adv 300e6); atr_d% >= 2.0.
             Stocks and unlevered ETFs both sides; leveraged / inverse / volatility funds (LEV) long only.
  long       [one-bar collapse: RSI14 of the bar exactly 5 min earlier >= 50 AND RSI14 <= 35 AND buyPressure > 0]
             OR [WB4-A dip: ret3 <= -0.21 x atr_d% AND ret12 >= -0.28 x atr_d% AND di_diff7 >= -5];
             universal long filter (skip while SPY is -0.30..-0.75% from its open AND SPY 30-min change < 0);
             SPY 60-min change > -0.40% (exactly 12 bars back; while that bar would precede 09:50, i.e. bar closes
             10:30-10:45, the change since the 09:30 open = spy_fo is used - point-in-time).
  short      [TS-1 pop: 60 <= RSI5 < 90 AND dist_lod_atr >= 0.5 AND |sma20_dist_pct| >= 1.5]
             OR [TS-2 roll-over: RSI5 of the previous bar >= 80 AND RSI5 < previous AND upper_wick > 0];
             gap < +0.5%; SPY change since the 09:50 bar close <= +0.20%; RSI5 >= 25; easy to borrow (account-side
             live: shorts.require_easy_to_borrow; backtest data/universe.csv flag); never a LEV fund (SYMBOLS).
  window     bar close WINDOW (inclusive; YAML window must match).
  refire     (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain:
             >= 30 min after the first lot's exit, one lot per symbol across both sides). YAML refire true, cooldown 0.
Exit: unit Ru = M x atr_d (YAML r_atr_frac = M).  EXIT "H" -> GEOM t05s1 (+0.5 Ru / -1 Ru);  "T" -> t1s1 (+1 / -1 Ru);
      "X" -> GEOM "S": catastrophic stop 2 Ru (stop_price), no target. YAML time_stop_min 45, time_stop_min_r 99;
      flat 15:50. Shorts pay borrow (backtest 1.2 bp of entry notional, 3 bp under $20).
Two sides, one file (as ULT-15): LabStrategy has one side per setup, so the account carries TWO `type: lab` entries
pointing at this file; a setup name ending in "-S" / "-short" is the short side (YAML `symbols: module` -> non-LEV names).
Account-side: day cap 30 entries over both sides (first by time, ADV20 desc)."""
import json
from pathlib import Path

import numpy as np

from mcf.research.arena.indicators import compute

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen pick 25l (round3/ULT-25/fitsel.json, frozen 2026-11-19 before any CHECK data; fit avg R -0.0023)
M = 0.50                  # unit Ru = M x atr_d (YAML r_atr_frac)
EXIT = "X"                # H t05s1 / T t1s1 / X TX-45 (2 Ru catastrophic stop)
WINDOW = (1300, 1500)
# ----
GEOM = {"H": "t05s1", "T": "t1s1", "X": "S"}[EXIT]
COST_R_MAX, MIN_ADV, ATR_PCT_MIN, PX_MIN = 0.03, 300e6, 2.0, 10.0
RSI_PREV_MIN, RSI_MAX = 50.0, 35.0
RET3_K, RET12_K, DI_MIN = -0.21, -0.28, -5.0
SPY_R60_MIN = -0.40
UNIV_BAND = (-0.75, -0.30)
GAP_SHORT_MAX, SPY_950_MAX, RSI5_SHORT_MIN = 0.5, 0.20, 25.0
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
_U = json.loads((Path(__file__).resolve().parent / "ULT-25_symbols.json").read_text())
LEV = frozenset(_U["LEV"])
NONLEV = frozenset(_U["NONLEV"])
SYMBOLS = NONLEV if SIDE == "short" else None        # YAML `symbols: module` on the short entry only
LAYERS = [
    "universe: price >= $10, |gap| < 20%, ADV20 >= $300M, daily ATR >= 2% of price, cost <= 0.03 of a 0.25-ATR unit",
] + (["long: one-bar RSI(14) collapse 50 -> <= 35 with buy pressure, OR 15-min dip <= 0.21 ATR% with 60-min >= -0.28 "
      "ATR% and DI(7) >= -5", "skip while SPY is -0.30..-0.75% from its open and falling over 30 min",
      "SPY 60-min change > -0.40%"] if _SGN > 0 else
     ["short: RSI(5) 60-90 >= 0.5 ATR off the low and >= 1.5% from SMA20, OR RSI(5) >= 80 turning down with an "
      "upper wick", "gap < +0.5%, RSI(5) >= 25, easy to borrow, no leveraged/inverse funds",
      "SPY up no more than +0.20% since 09:50"]) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    {"H": f"exit: +0.5R / -1R (R = {M:g} x daily ATR), 45-min time exit",
     "T": f"exit: +1R / -1R (R = {M:g} x daily ATR), 45-min time exit",
     "X": f"exit: 45-min time exit, catastrophic stop {2 * M:g} x daily ATR"}[EXIT],
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
    x = np.asarray(x, dtype=float)
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


def _at(x, key, mins, target_min):
    """x at the row of the same symbol-session whose bar close is target_min (minutes); NaN when absent."""
    import pandas as pd
    s = pd.Series(np.asarray(x, float), index=pd.MultiIndex.from_arrays([key, mins]))
    s = s[~s.index.duplicated()]
    return s.reindex(pd.MultiIndex.from_arrays([key, np.asarray(target_min, float)])).to_numpy(dtype=float)


def _chg(now, then):
    with np.errstate(invalid="ignore", divide="ignore"):
        return ((1 + now / 100) / (1 + then / 100) - 1) * 100


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    import pandas as pd
    n = len(df)
    x = compute(df, names=["atr_d_pct", "di_diff7", "ret3", "ret12"], context=False)
    c = lambda k: df[k].to_numpy(dtype=float)   # noqa: E731
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    key = pd.factorize(_keys(df))[0]
    mins = _minutes(tod)
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(n, np.nan)
    fo_in = np.where(tod >= 950, fo, np.nan)
    r30 = _chg(fo, _lag(fo_in, 6, key, mins))
    # 60 min back precedes the 09:50 bar (bar closes <= 10:45): change since the 09:30 open (spy_fo there = 0)
    p60 = np.where(mins - 60 < 590, 0.0, _lag(fo_in, 12, key, mins))
    r60 = _chg(fo, p60)
    s950 = _chg(fo, _at(fo_in, key, mins, np.full(n, 590.0)))
    adv = c("adv20") if "adv20" in df.columns else np.full(n, np.inf)
    rsi, r5, bp = c("rsi"), c("rsi5"), c("buyPressure")
    rsi_p, r5_p = _lag(rsi, 1, key, mins), _lag(r5, 1, key, mins)
    atrp = x["atr_d_pct"].to_numpy(float)
    if "symbol" in df.columns:
        is_lev = df["symbol"].astype(str).isin(LEV).to_numpy()
    else:
        is_lev = np.zeros(n, bool)          # live: the short entry's YAML symbols (NONLEV) does this
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        univ = ((px >= PX_MIN) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= COST_R_MAX) & (adv >= MIN_ADV)
                & (atrp >= ATR_PCT_MIN) & np.isfinite(fo))
        coll = (rsi_p >= RSI_PREV_MIN) & (rsi <= RSI_MAX) & (bp > 0)
        ret3, ret12, di7 = (x[k].to_numpy(float) for k in ("ret3", "ret12", "di_diff7"))
        dip = (ret3 <= RET3_K * atrp) & (ret12 >= RET12_K * atrp) & (di7 >= DI_MIN)
        univ_ok = ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0)) & np.isfinite(r30)
        long_ok = univ_ok & np.isfinite(r60) & (r60 > SPY_R60_MIN)
        ts1 = (r5 >= 60) & (r5 < 90) & (c("dist_lod_atr") >= 0.5) & (np.abs(c("sma20_dist_pct")) >= 1.5)
        ts2 = (r5_p >= 80) & (r5 < r5_p) & (c("upper_wick") > 0)
        short_ok = (c("gap") < GAP_SHORT_MAX) & np.isfinite(s950) & (s950 <= SPY_950_MAX) & (r5 >= RSI5_SHORT_MIN) & ~is_lev
    return {"tod": tod, "close": px, "cost_r": cost_r, "atrp": atrp, "univ": univ, "coll": coll, "dip": dip,
            "ts1": ts1, "ts2": ts2, "long_ok": long_ok, "short_ok": short_ok, "spy_fo": fo, "spy_r30": r30,
            "spy_r60": r60, "spy_950": s950, "rsi_prev": rsi_p, "rsi5_prev": r5_p, "is_lev": is_lev}


def signal(r, sgn) -> np.ndarray:
    """Universe + side trigger + side filters (no window, no ETB, no thinning)."""
    if sgn > 0:
        return r["univ"] & (r["coll"] | r["dip"]) & r["long_ok"]
    return r["univ"] & (r["ts1"] | r["ts2"]) & r["short_ok"]


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
    m = signal(r, _SGN) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT X): catastrophic stop 2 Ru = 2 x M x atr_d beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * M * float(f["atr_d"].iloc[i])
