# ULTIMATE CANDIDATE ULT-23 COLLAPSE-BASKET (research only, not enabled in any account)
# research/ultimate_1119/round3/PLAN.md sec. 3 "ULT-23"; backtest research/ultimate_1119/round3/ULT-23/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-23 COLLAPSE-BASKET - ST7's one-bar RSI(14) collapse, moved to equity-basket ETFs and mega caps, LONG. CHECK-INFORMED.

Rule (all point-in-time, at the decision 5-minute bar close; frame columns rsi = RSI(14), buyPressure = 19-bar):
  intake     price >= $10; |gap| < 20%; atr_d > 0; cost_r <= 0.08 (LR8 stop-out round trip
             ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d)
  universe   "Q" = EQB equity-basket ETFs (ULT-23_symbols.json Q), ADV20 >= $30M;
             "M" = MEGA: non-fund stocks, ADV20 >= $1B and price >= $20;  "QM" = either.
             ADV20: frame column adv20 when present (backtest); live = the YAML min_adv on ctx.avg_dollar_volume
             (Q: min_adv 30M, symbols: module; M: min_adv 1e9, symbols: module). Live QM = the Q and M entries side
             by side (one YAML min_adv per entry); the mask applies price >= $20 to non-funds when it can see a
             `symbol` column, and to every name when UNIV == "M".
  trigger    ONE-BAR collapse: RSI14 of the previous 5-min bar (same session, exactly 5 min earlier) >= 50 AND
             RSI14 now <= RMAX; fromOpen <= -min(1.0%, 0.30 x atr_d%) (atr_d% = atr_d / close x 100);
             buyPressure (19-bar) > 0
  universal  skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0 (no SPY context -> no signal)
  window     bar close 10:15-15:00 (inclusive; YAML window must match)
  refire     (THIN) max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain:
             >= 30 min after the first lot's exit). YAML: refire true, refire_cooldown 0.
Exit: EXIT "T" -> GEOM t1s1 (+1u / -1u around the decision close); EXIT "H" -> GEOM t05s1 (+0.5u / -1u);
      YAML time_stop_min 45, time_stop_min_r 99; flat 15:50.
Account-side (not in the module): day cap 30 entries (first by time, ADV20 desc)."""
import json
from pathlib import Path

import numpy as np

SIDE = "long"
# ---- fit-frozen pick 23e (round3/ULT-23/fitsel.json, frozen 2026-11-19 before any CHECK data; NO config reached 2/session)
UNIV = "M"
RMAX = 30.0
EXIT = "T"
# ----
GEOM = "t1s1" if EXIT == "T" else "t05s1"
WINDOW = (1015, 1500)
RSI_PREV_MIN = 50.0
FROM_OPEN_PCT, FROM_OPEN_ATR_K = 1.0, 0.30
COST_R_MAX = 0.08
ADV_Q, ADV_M, PX_M = 30e6, 1e9, 20.0
UNIV_BAND = (-0.75, -0.30)
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
_U = json.loads((Path(__file__).resolve().parent / "ULT-23_symbols.json").read_text())
EQB = frozenset(_U["Q"])
FUNDS = frozenset(_U["FUNDS"])
STOCKS = frozenset(_U["STOCKS"])
SYMBOLS = {"Q": EQB, "M": STOCKS, "QM": EQB | STOCKS}[UNIV]
MIN_ADV = {"Q": ADV_Q, "M": ADV_M, "QM": ADV_Q}[UNIV]
LAYERS = [
    {"Q": "equity-basket ETFs, ADV20 >= $30M", "M": "mega caps (non-fund, ADV20 >= $1B, price >= $20)",
     "QM": "equity-basket ETFs (ADV20 >= $30M) or mega caps (ADV20 >= $1B, price >= $20)"}[UNIV],
    "intake: price >= $10, |gap| < 20%, cost_r <= 0.08",
    f"RSI(14) was >= 50 on the previous 5-min bar and is <= {RMAX:g} now (one-bar collapse)",
    "down >= min(1.0%, 0.30 x daily ATR%) from the open", "19-bar buy pressure > 0",
    "skip while SPY is -0.30..-0.75% from its open and falling over 30 min",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: +1R / -1R, 45-min time exit" if EXIT == "T" else "exit: +0.5R / -1R, 45-min time exit",
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


def universe_flags(df, px):
    """(is_Q, is_M) per row. Backtest: symbol + adv20 columns. Live: no symbol / adv20 -> the YAML entry decides
    (symbols: module + min_adv); UNIV 'M' then applies price >= $20 to every row."""
    n = len(df)
    if "symbol" in df:
        sym = df["symbol"].astype(str).to_numpy()
        inq = np.array([s in EQB for s in sym])
        notfund = np.array([s not in FUNDS for s in sym])
    else:
        inq = np.full(n, UNIV in ("Q", "QM"))
        notfund = np.full(n, UNIV == "M")
    adv = df["adv20"].to_numpy(dtype=float) if "adv20" in df else np.full(n, np.inf)
    with np.errstate(invalid="ignore"):
        is_q = inq & (adv >= ADV_Q)
        is_m = notfund & (adv >= ADV_M) & (px >= PX_M)
    return is_q, is_m


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (shared with the backtest: bt.py imports this)."""
    c = lambda k: df[k].to_numpy(dtype=float)
    px, atr, tod, rsi = c("close"), c("atr_d"), c("tod"), c("rsi")
    key = _keys(df).astype(object)
    rsi_prev = _lag(rsi, 1, key, _minutes(tod))
    has_spy = "spy_fo" in df.columns
    fo = c("spy_fo") if has_spy else np.full(len(df), np.nan)
    r30 = spy_r30(df) if has_spy else np.full(len(df), np.nan)
    is_q, is_m = universe_flags(df, px)
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + px * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        atrp = atr / px * 100
        fo_thr = -np.minimum(FROM_OPEN_PCT, FROM_OPEN_ATR_K * atrp)
        intake = (px >= 10) & (np.abs(c("gap")) < 20) & (atr > 0) & (cost_r <= COST_R_MAX) & np.isfinite(fo)
        univ_ok = ~((fo >= UNIV_BAND[0]) & (fo <= UNIV_BAND[1]) & (r30 < 0))
    return {"tod": tod, "close": px, "rsi": rsi, "rsi_prev": rsi_prev, "fromOpen": c("fromOpen"), "fo_thr": fo_thr,
            "atrp": atrp, "bp": c("buyPressure"), "cost_r": cost_r, "intake": intake, "univ_ok": univ_ok,
            "is_q": is_q, "is_m": is_m, "spy_fo": fo, "spy_r30": r30}


def trigger(r, rmax) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((r["rsi_prev"] >= RSI_PREV_MIN) & (r["rsi"] <= rmax) & (r["fromOpen"] <= r["fo_thr"])
                & (r["bp"] > 0))


def in_universe(r, univ=None) -> np.ndarray:
    univ = univ or UNIV
    return {"Q": r["is_q"], "M": r["is_m"], "QM": r["is_q"] | r["is_m"]}[univ]


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
    m = (r["intake"] & r["univ_ok"] & in_universe(r) & trigger(r, RMAX) & (tod >= WINDOW[0]) & (tod <= WINDOW[1]))
    return _thin(m, df) if THIN else m
