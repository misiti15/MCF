# ULTIMATE CANDIDATE ULT-24 CONFL-2 (research only, not enabled in any account)
# research/ultimate_1119/round3/PLAN.md sec. 3 "ULT-24"; backtest research/ultimate_1119/round3/ULT-24/RESULTS.md
# Next: only a TIER A / BEATS result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-24 CONFL-2 - confluence of gated triggers on gated cheap bases (equity-basket ETFs, mega caps), LONG + SHORT.
CHECK-INFORMED (TS-1 / TS-2 / TL-B, round3/PLAN.md sec. 0.5).

Bases (decision 5-min bar close 10:30-15:00, point-in-time; intake price >= $10, |gap| < 20%, atr_d > 0):
  BQ-L  long : EQB equity-basket ETF (ULT-24_symbols.json Q), ADV20 >= $30M, atr_d% >= 2.0, cost_r <= 0.08,
               own ret12 >= -0.28 x atr_d% (falling-hour guard), universal long filter.
  BM-L  long : MEGA (non-fund, ADV20 >= $1B, price >= $20), cost_r <= 0.05, SPY 60-min change > -0.40%, universal
               long filter.
  BM-S  short: MEGA, easy to borrow (account-side live / universe.csv in the backtest), cost_r <= 0.05, gap < +0.5%,
               SPY change since the 09:50 close <= +0.20% AND SPY 30-min change <= +0.10%, RSI5 >= 25.
  cost_r = LR8 stop-out round trip ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d.
  universal long filter: skip while SPY is -0.30..-0.75% from its open AND SPY's 30-min change < 0.
  SPY 60-min change: from spy_fo at exactly t-60 min (same session); when that bar is not in the frame, the reference is
  the open (t-60 <= 09:30) or else the 09:50 bar (backtest frames start at 09:50; 10:35-10:45 then use 45-55 min).
Triggers (decision bar; ret3 / ret12 / di_diff7 / atr_d_pct via mcf.research.arena.indicators.compute, as WB4):
  long  TL-A WB4-A dip: ret3 <= -0.21 x atr_d% AND ret12 >= -0.28 x atr_d% AND di_diff7 >= -5
        TL-B one-bar RSI14 collapse: RSI14[previous bar] >= 50 AND RSI14 <= 35
        TL-C RSI2 <= 5 (Wilder RSI(2) of the session's 5-min closes from the 09:50 bar)
        TL-D capitulation bar: lower_wick share >= 0.5 AND volumeRatio (bar volume / 20-bar mean) >= 2 AND
             (close - low) / (high - low) >= 0.5
  short TS-1 pop: 60 <= RSI5 < 90 AND dist_lod_atr >= 0.5 AND |sma20_dist_pct| >= 1.5
        TS-2 roll-over: RSI5[previous bar] >= 80 AND RSI5 < RSI5[previous] AND upper_wick > 0
        TS-3 from_open_dATR >= +1.0
        TS-4 RSI2 >= 95
Gates (FIT only, round3/ULT-24/base_gate.json, trigger_gate.json): a base trades only if its random-entry avg R was
  >= 0 in both fit sub-halves under the frozen exit (BASE_OPEN); only triggers whose signal-minus-random was >= 0 in both
  sub-halves count (SURVIVE).
Signal: base AND >= CONF surviving triggers of the base each true on the decision bar or one of the previous W bars
  (same session, exact 5-min spacing).
Refire (THIN): max 2 per symbol-session, the 2nd >= REFIRE_BARS decision bars after the 1st (backtest chain: >= 30 min
  after the first lot's exit, one lot per symbol across sides). YAML: refire true, refire_cooldown 0.
Three setups, one file: the setup name picks the base - ending "-S"/"-short" -> BM-S (short), "-M" -> BM-L (long),
  anything else -> BQ-L (long). YAML per entry: symbols: module, min_adv = SYMBOLS' floor (BQ-L 30e6, BM-* 1e9),
  context: [spy_fo], window [1030, 1500].
Exit: EXIT "H" -> GEOM t05s1 (+0.5u / -1u around the decision close), EXIT "X" -> GEOM "S" (2u catastrophic stop, no
  target); YAML time_stop_min 45, time_stop_min_r 99; flat 15:50. Account side: day cap 30 entries (first by time)."""
import json
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
if _NAME.endswith(("-s", "_s", "-short", "_short")):
    BASE = "BM-S"
elif _NAME.endswith(("-m", "_m")):
    BASE = "BM-L"
else:
    BASE = "BQ-L"
SIDE = "short" if BASE == "BM-S" else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen (round3/ULT-24/fitsel.json, base_gate.json, trigger_gate.json); set before any CHECK data.
# The FIT base gate CLOSED all three bases under both exits (random avg R < 0 in both sub-halves), so the trigger gate
# was skipped, no config may trade (pre-registered rule) and this module never fires as frozen. W / CONF / EXIT hold the
# DIAGNOSTIC base-gate-ignored pick 24b (W3-C2-TX45; diagnostic trigger survivors BM-L TL-A/TL-C/TL-D, BM-S
# TS-1/TS-2/TS-4, BQ-L none) for the record; it lost on CHECK (-0.023R). RESULTS.md: FAIL.
W = 3
CONF = 2
EXIT = "X"
BASE_OPEN = {"BQ-L": {"H": False, "X": False}, "BM-L": {"H": False, "X": False}, "BM-S": {"H": False, "X": False}}
SURVIVE = {"BQ-L": (), "BM-L": (), "BM-S": ()}
# ----
GEOM = "t05s1" if EXIT == "H" else "S"
WINDOW = (1030, 1500)
LONG_TRIG = ("TL-A", "TL-B", "TL-C", "TL-D")
SHORT_TRIG = ("TS-1", "TS-2", "TS-3", "TS-4")
ADV_Q, ADV_M, PX_M = 30e6, 1e9, 20.0
COST_MAX = {"BQ-L": 0.08, "BM-L": 0.05, "BM-S": 0.05}
UNIV_BAND = (-0.75, -0.30)
THIN = True
REFIRE_BARS, MAX_PER_DAY = 15, 2
_U = json.loads((Path(__file__).resolve().parent / "ULT-24_symbols.json").read_text())
EQB = frozenset(_U["Q"])
FUNDS = frozenset(_U["FUNDS"])
STOCKS = frozenset(_U["STOCKS"])
SYMBOLS = EQB if BASE == "BQ-L" else STOCKS
MIN_ADV = ADV_Q if BASE == "BQ-L" else ADV_M
SYMBOL_HINT = None
LAYERS = [
    {"BQ-L": "equity-basket ETFs (ADV20 >= $30M, daily ATR >= 2%, cost_r <= 0.08, not down > 0.28 ATR% in 60 min)",
     "BM-L": "mega caps (ADV20 >= $1B, price >= $20, cost_r <= 0.05), SPY 60-min change > -0.40%",
     "BM-S": "mega caps, easy to borrow, cost_r <= 0.05, gap < +0.5%, SPY <= +0.20% since 09:50 and <= +0.10% in 30 min, "
             "RSI5 >= 25"}[BASE],
    f"at least {CONF} of the gated triggers {', '.join(SURVIVE[BASE]) or '(none)'} within {W} bars",
    f"window: bar close {WINDOW[0]}-{WINDOW[1]} ET",
    "exit: +0.5R / -1R, 45-min time exit" if EXIT == "H" else "exit: 45-min time exit, 2u catastrophic stop",
]


def _tod_mult(tod):
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def _m2(t):
    t = np.asarray(t, float)
    return np.floor(t / 100) * 60 + t % 100


def _keys(df):
    import pandas as pd
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        day = df["symbol"].astype(str).to_numpy() + "|" + day
    return day


def _col(df, k):
    return df[k].to_numpy(dtype=float) if k in df.columns else np.full(len(df), np.nan)


def _lag(v, key, mins, lag):
    """v at (same key, mins - lag), exact time match; NaN otherwise."""
    import pandas as pd
    v = np.asarray(v, float)
    kc = pd.factorize(key)[0].astype(np.int64)
    code = kc * 100000 + np.asarray(mins, np.int64)
    if len(code) and np.all(np.diff(code) > 0):          # rows grouped by key, time ascending (frames are)
        want = code - np.asarray(lag, np.int64)
        j = np.clip(np.searchsorted(code, want), 0, len(code) - 1)
        hit = code[j] == want
        return np.where(hit, v[j], np.nan)
    s = pd.Series(np.asarray(v, float), index=pd.MultiIndex.from_arrays([key, mins]))
    s = s[~s.index.duplicated()]
    return s.reindex(pd.MultiIndex.from_arrays([key, mins - lag])).to_numpy(dtype=float)


def _rsi2(close, key, ok):
    """Wilder RSI(2) (alpha 0.5) of the session's closes on rows ok (tod >= 09:50), per key, rows in time order."""
    out = np.full(len(close), np.nan)
    cur, prev, au, ad = None, np.nan, np.nan, np.nan
    for i in range(len(close)):
        if not ok[i]:
            continue
        if key[i] != cur:
            cur, prev, au, ad = key[i], close[i], np.nan, np.nan
            continue
        d = close[i] - prev
        prev = close[i]
        if not np.isfinite(d):
            continue
        up, dn = max(d, 0.0), max(-d, 0.0)
        if np.isnan(au):
            au, ad = up, dn
        else:
            au, ad = 0.5 * au + 0.5 * up, 0.5 * ad + 0.5 * dn
        if ad > 0:
            out[i] = 100 - 100 / (1 + au / ad)
        elif au > 0:
            out[i] = 100.0
    return out


def _symbols(df):
    if "symbol" in df.columns:
        return df["symbol"].astype(str).to_numpy()
    return np.full(len(df), SYMBOL_HINT if SYMBOL_HINT else "", dtype=object)


def features(df) -> dict:
    """Point-in-time base parts and the eight triggers (on the bar) for every row (shared with bt.py).
    Only the row's own and earlier bars of the same symbol-session, its context columns and prior-day values."""
    from mcf.research.arena.indicators import compute
    n = len(df)
    key = _keys(df).astype(object)
    tod = _col(df, "tod")
    mins = _m2(tod)
    c, h, lo, atr, gap = _col(df, "close"), _col(df, "high"), _col(df, "low"), _col(df, "atr_d"), _col(df, "gap")
    ind = compute(df, names=["atr_d_pct", "di_diff7", "ret3", "ret12"], context=False)
    ret3, ret12 = ind["ret3"].to_numpy(float), ind["ret12"].to_numpy(float)
    di7, atrp = ind["di_diff7"].to_numpy(float), ind["atr_d_pct"].to_numpy(float)
    rsi, r5 = _col(df, "rsi"), _col(df, "rsi5")
    fo_s = _col(df, "spy_fo")
    sym = _symbols(df)
    adv = _col(df, "adv20")
    with np.errstate(invalid="ignore", divide="ignore"):
        one = 0.01 + c * 1e-4
        cost_r = (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)
        foa = (c - c / (1 + _col(df, "fromOpen") / 100)) / atr
        rsi2 = _rsi2(c, key, tod >= 950)
        rsi_p, r5_p = _lag(rsi, key, mins, 5), _lag(r5, key, mins, 5)
        # SPY context
        r30 = ((1 + fo_s / 100) / (1 + _lag(fo_s, key, mins, 30) / 100) - 1) * 100
        l60 = _lag(fo_s, key, mins, 60)
        s950 = _lag(fo_s, key, mins, mins - _m2(950))          # spy_fo at the session's 09:50 bar
        ref60 = np.where(np.isfinite(l60), l60, np.where(mins - 60 <= _m2(930), 0.0,
                                                         np.where(mins - 60 < _m2(950), s950, np.nan)))
        spy60 = ((1 + fo_s / 100) / (1 + ref60 / 100) - 1) * 100
        since950 = ((1 + fo_s / 100) / (1 + s950 / 100) - 1) * 100
        trig = {
            "TL-A": (ret3 <= -0.21 * atrp) & (ret12 >= -0.28 * atrp) & (di7 >= -5),
            "TL-B": (rsi_p >= 50) & (rsi <= 35),
            "TL-C": rsi2 <= 5,
            "TL-D": (_col(df, "lower_wick") >= 0.5) & (_col(df, "volumeRatio") >= 2.0) & ((h - lo) > 0)
                    & ((c - lo) >= 0.5 * (h - lo)),
            "TS-1": (r5 >= 60) & (r5 < 90) & (_col(df, "dist_lod_atr") >= 0.5) & (np.abs(_col(df, "sma20_dist_pct")) >= 1.5),
            "TS-2": (r5_p >= 80) & (r5 < r5_p) & (_col(df, "upper_wick") > 0),
            "TS-3": foa >= 1.0,
            "TS-4": rsi2 >= 95,
        }
        intake = (c >= 10) & (np.abs(gap) < 20) & (atr > 0) & np.isfinite(fo_s) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        univ_long = ~((fo_s >= UNIV_BAND[0]) & (fo_s <= UNIV_BAND[1]) & (r30 < 0)) & np.isfinite(r30)
        has_sym = "symbol" in df.columns or SYMBOL_HINT is not None
        in_q = np.array([s in EQB for s in sym]) if has_sym else np.full(n, BASE == "BQ-L")
        in_s = np.array([s in STOCKS for s in sym]) if has_sym else np.full(n, BASE != "BQ-L")
        advq = np.nan_to_num(adv, nan=0.0) >= ADV_Q if np.isfinite(adv).any() else np.ones(n, bool)
        advm = np.nan_to_num(adv, nan=0.0) >= ADV_M if np.isfinite(adv).any() else np.ones(n, bool)
        mega = in_s & advm & (c >= PX_M)
        bases = {
            "BQ-L": intake & in_q & advq & (atrp >= 2.0) & (cost_r <= COST_MAX["BQ-L"]) & (ret12 >= -0.28 * atrp)
                    & univ_long,
            "BM-L": intake & mega & (cost_r <= COST_MAX["BM-L"]) & (spy60 > -0.40) & univ_long,
            "BM-S": intake & mega & (cost_r <= COST_MAX["BM-S"]) & (gap < 0.5) & (since950 <= 0.20) & (r30 <= 0.10)
                    & (r5 >= 25),
        }
    trig = {k: np.nan_to_num(v.astype(float)) > 0 for k, v in trig.items()}
    bases = {k: np.nan_to_num(v.astype(float)) > 0 for k, v in bases.items()}
    return {"n": n, "key": key, "mins": mins, "tod": tod, "trig": trig, "bases": bases, "cost_r": cost_r,
            "spy60": spy60, "since950": since950, "spy_r30": r30, "rsi2": rsi2}


def within(r, name, w) -> np.ndarray:
    """Trigger `name` true on the bar or one of the previous w bars (same session, exact 5-min spacing)."""
    b = r["trig"][name]
    out = b.copy()
    for k in range(1, w + 1):
        out |= _lag(b.astype(float), r["key"], r["mins"], 5 * k) == 1.0
    return out


def count(r, base, w, survive=None) -> np.ndarray:
    names = SURVIVE[base] if survive is None else survive
    tot = np.zeros(r["n"], int)
    for k in names:
        tot += within(r, k, w).astype(int)
    return tot


def _thin(m, df):
    hit = np.flatnonzero(m)
    out = np.zeros(len(m), bool)
    if not len(hit):
        return out
    key = _keys(df)
    last, n, cur = -10**9, 0, None
    for i in hit:
        if key[i] != cur:
            cur, last, n = key[i], -10**9, 0
        if n < MAX_PER_DAY and i - last >= REFIRE_BARS:
            out[i] = True; last = i; n += 1
    return out


def mask(df) -> np.ndarray:
    if "spy_fo" not in df.columns or not BASE_OPEN[BASE][EXIT] or len(SURVIVE[BASE]) < CONF:
        return np.zeros(len(df), bool)       # fail safe / base or triggers closed by the FIT gates
    r = features(df)
    m = r["bases"][BASE] & (count(r, BASE, W) >= CONF)
    return _thin(m, df) if THIN else m


def stop_price(f, i) -> float:
    """GEOM "S" (EXIT "X"): catastrophic stop 2u = 0.5 daily ATR beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
