# ULTIMATE CANDIDATE ULT-26 WITH-GAP TREND (research only, not enabled in any account)
# research/ultimate_1119/round3/PLAN.md sec. 3 "ULT-26"; backtest research/ultimate_1119/round3/ULT-26/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-26 WITH-GAP TREND - with-the-gap continuation only on a trend tape, LONG + SHORT. Not check-informed.

Thesis: ULT-05 (with-gap pullback) traded 13-21/session at ~0R and lost on flat tapes; the targeted remedy is a
point-in-time "trend day so far" layer: the name trades only in the direction of BOTH its own gap and the tape
(market intraday momentum, Gao, Han, Li & Zhou 2018).
Rule (all point-in-time, at the decision 5-minute bar close; frame columns gap, vwapDistPct, buyPressure, rsi5,
dist_hod_atr / dist_lod_atr (session HOD / LOD so far, in daily ATR), context spy_fo = SPY % from its 09:30 open):
  intake   price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.08 (LR8 stop-out round trip
           ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); ADV20 >= $50M (frame adv20 in the backtest;
           live = YAML min_adv 50e6).
  name rp  range position = dist_lod / (dist_lod + dist_hod) = (close - LOD) / (HOD - LOD); NaN when HOD == LOD.
  SPY rp   SPY's position in its range since 09:30, from the 5-minute closes of the context: hi = max(0, max spy_fo of
           this session's bars with close >= 09:50 up to now), lo = min(0, ...); rp = (spy_fo - lo) / (hi - lo).
           (0 = the 09:30 open; 5-min closes, not intrabar extremes - the same table live and in the backtest, because
           the history context starts at 09:50 and the live rows 09:35-09:45 are ignored.)
  long     gap >= +G; 0 < vwapDistPct <= 0.5 x atr_d% (atr_d / close x 100); buyPressure > 0; name rp >= 0.6;
           spy_fo >= +T and SPY rp >= 0.7.
  short    gap <= -G; -0.5 x atr_d% <= vwapDistPct < 0; buyPressure < 0; name rp <= 0.4; spy_fo <= -T and
           SPY rp <= 0.3; RSI(5) >= 25; easy to borrow (account-side live: shorts.require_easy_to_borrow; backtest
           data/universe.csv flag); never a leveraged / inverse / volatility fund (LEV; live: YAML `symbols: module`
           on the short entry = SYMBOLS = NONLEV; backtest: is_lev flag).
  window   bar close 10:30-14:30 (YAML window must match).
  refire   (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain: >= 30 min
           after the first lot's exit, one lot per symbol). YAML refire true, refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 (+1u / -1u, u = 0.25 x atr_d) with YAML time_stop_min 45, time_stop_min_r 99;
      EXIT "X" -> GEOM "S": catastrophic stop 2u beyond the decision close (stop_price), no target, time_stop_min 45.
      Flat 15:50 (last entry 14:30 + 45 min). Shorts pay borrow (backtest 1.2 bp of entry notional, 3 bp under $20).
Two sides, one file (as ULT-05 / ULT-25): LabStrategy has one side per setup, so the account carries TWO `type: lab`
entries pointing at this file; a setup name ending in "-S" / "-short" is the short side. A name cannot be gap-up and
gap-down on one day, so the two never collide. Account-side: day cap 30 entries over both sides (first by time)."""
import json
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen pick 26g (round3/ULT-26/fitsel.json, frozen 2026-11-19T08:13Z before any CHECK data); CHECK FAIL
G = 3.0                   # |gap| floor, %
T = 0.50                  # SPY from-open floor, %
EXIT = "T"                # "T" t1s1 cap45 | "X" TX-45 with a 2u catastrophic stop
# ----
GEOM = "t1s1" if EXIT == "T" else "S"
WINDOW = (1030, 1430)
MIN_ADV, COST_R_MAX, PX_MIN = 50e6, 0.08, 10.0
VWAP_ATR_FRAC = 0.5
RP_LONG, RP_SHORT = 0.6, 0.4
SPY_RP_LONG, SPY_RP_SHORT = 0.7, 0.3
RSI5_SHORT_MIN = 25.0
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
_U = json.loads((Path(__file__).resolve().parent / "ULT-26_symbols.json").read_text())
LEV = frozenset(_U["LEV"])
NONLEV = frozenset(_U["NONLEV"])
SYMBOLS = NONLEV if SIDE == "short" else None        # YAML `symbols: module` on the short entry only
LAYERS = [
    "intake: price >= $10, |gap| < 20%, ADV20 >= $50M, cost <= 0.08 of a 0.25-ATR unit",
    f"gap {'>=' if _SGN > 0 else '<='} {_SGN * G:+g}%",
    f"close on the gap side of VWAP, within {VWAP_ATR_FRAC:g} x daily ATR% of it",
    f"buyPressure {'>' if _SGN > 0 else '<'} 0",
    (f"name in the top 40% of its intraday range" if _SGN > 0 else "name in the bottom 40% of its intraday range"),
    (f"SPY >= +{T:g}% from its open and in the top 30% of its range since 09:30" if _SGN > 0 else
     f"SPY <= -{T:g}% from its open and in the bottom 30% of its range since 09:30"),
] + ([] if _SGN > 0 else [f"RSI(5) >= {RSI5_SHORT_MIN:g}, easy to borrow, no leveraged/inverse funds"]) + [
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: +1R / -1R (R = 0.25 x daily ATR), 45-min time exit" if EXIT == "T" else
    "exit: 45-min time exit, catastrophic stop 0.5 x daily ATR",
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


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    import pandas as pd
    n = len(df)
    c = lambda k: df[k].to_numpy(dtype=float)   # noqa: E731
    px, atr, tod = c("close"), c("atr_d"), c("tod")
    key = _keys(df)
    fo = c("spy_fo") if "spy_fo" in df.columns else np.full(n, np.nan)
    fo_in = pd.Series(np.where(tod >= 950, fo, np.nan))
    g = fo_in.groupby(key)
    hi = np.fmax(g.cummax().to_numpy(float), 0.0)      # cummax skips NaN (rows before 09:50); fmax(NaN, 0) = 0
    lo = np.fmin(g.cummin().to_numpy(float), 0.0)
    adv = c("adv20") if "adv20" in df.columns else np.full(n, np.inf)
    dl, dh = c("dist_lod_atr"), c("dist_hod_atr")
    with np.errstate(invalid="ignore", divide="ignore"):
        spy_rp = np.where((tod >= 950) & (hi > lo), (fo - lo) / (hi - lo), np.nan)
        rp = np.where(dl + dh > 0, dl / (dl + dh), np.nan)
        atrp = atr / px * 100
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        intake = ((px >= PX_MIN) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= COST_R_MAX) & (adv >= MIN_ADV))
    if "symbol" in df.columns:
        is_lev = df["symbol"].astype(str).isin(LEV).to_numpy()
    else:
        is_lev = np.zeros(n, bool)          # live: the short entry's YAML symbols / eligible list does this
    return {"tod": tod, "close": px, "gap": c("gap"), "vd": c("vwapDistPct"), "bp": c("buyPressure"),
            "rsi5": c("rsi5"), "atrp": atrp, "cost_r": cost_r, "intake": intake, "rp": rp, "spy_fo": fo,
            "spy_rp": spy_rp, "is_lev": is_lev}


def signal(r, sgn, g=None, t=None) -> np.ndarray:
    """Intake + side rule for gap floor g and tape floor t (no window, no ETB, no thinning)."""
    g = G if g is None else g
    t = T if t is None else t
    with np.errstate(invalid="ignore"):
        if sgn > 0:
            return (r["intake"] & (r["gap"] >= g) & (r["vd"] > 0) & (r["vd"] <= VWAP_ATR_FRAC * r["atrp"])
                    & (r["bp"] > 0) & (r["rp"] >= RP_LONG) & (r["spy_fo"] >= t) & (r["spy_rp"] >= SPY_RP_LONG))
        return (r["intake"] & (r["gap"] <= -g) & (r["vd"] < 0) & (r["vd"] >= -VWAP_ATR_FRAC * r["atrp"])
                & (r["bp"] < 0) & (r["rp"] <= RP_SHORT) & (r["spy_fo"] <= -t) & (r["spy_rp"] <= SPY_RP_SHORT)
                & (r["rsi5"] >= RSI5_SHORT_MIN) & ~r["is_lev"])


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
    """GEOM "S" (EXIT X): catastrophic stop 2u = 0.5 x atr_d beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
