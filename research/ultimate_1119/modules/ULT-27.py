# ULTIMATE CANDIDATE ULT-27 PERIODICITY (research only, not enabled in any account)
# research/ultimate_1119/round3/PLAN.md sec. 3 "ULT-27"; backtest research/ultimate_1119/round3/ULT-27/RESULTS.md
# Next: only a TIER A result goes to a testing arena, with the owner's yes. Educational only - not financial advice.
"""ULT-27 PERIODICITY - same-clock-interval return persistence across days, LONG + SHORT. Not check-informed.

Thesis (Heston, Korajczyk & Sadka 2010, J. Finance): a stock's return in a given half hour tends to repeat at the same
clock half hour on later days (order splitting, scheduled flows). Cross-sectional, both sides, any tape.

Rule (point-in-time):
  slots     decision bars closing 10:00, 11:00, 12:00, 13:00, 14:00, 15:00 ET; interval t..t+30 min.
  x         for every prior session d and slot t: x = (C[t+29] / C[t-1] - 1) x 100 / ATR%_d, with C[m] = close of the
            1-minute bar starting at minute m (the last bar within the 5 minutes up to m), ATR%_d = mean true range of
            the 14 sessions before d (min 5) / close of the session before d x 100 (known at d's open).
  P         mean of x over the previous L open sessions (prior sessions only); needs >= ceil(0.7 L) valid days.
  pre-open  eligibility (all known before 09:30): not a leveraged / inverse / volatility fund (LEV list); ADV20 >=
            $200M (prior sessions); previous close >= $10; cost_r(previous close, atr_d, slot) <= 0.05 (LR8 stop-out
            round trip ((1c + 1bp) x tod mult + 1c + 1bp + 2c) / u, u = 0.25 x atr_d); short list also easy to borrow.
  lists     per slot in clock order: long = the N highest P, short = the N lowest P among pre-open-eligible names; a
            name already listed at 2 earlier slots today is skipped and replaced by the next (max 2 per symbol-session).
            Built pre-open by build_profile() into ULT-27_profile.json (the live job runs it before 09:30 from the
            1-minute cache; the backtest calls the same functions for every session).
  in-day    at the decision bar the listed name must still pass: close >= $10, cost_r (bar close) <= 0.05, |gap| < 20%,
            atr_d > 0; longs: universal long filter (no long while SPY is -0.30..-0.75% from its open AND SPY's 30-min
            change < 0); shorts: gap < +0.5% and RSI(5) >= 25. A name that fails is dropped, NOT replaced (other names'
            in-day state is not visible to a per-symbol live module).
Exit: TX-30 = GEOM "S": catastrophic stop 2u = 0.5 x atr_d beyond the decision close (stop_price), no target, YAML
      time_stop_min 30; flat 15:50 (last entry 15:00 + 30 min). R per 2u. Shorts pay borrow (backtest 1.2 bp of entry
      notional, 3 bp under $20).
Two sides, one file: LabStrategy has one side per setup, so the account carries TWO `type: lab` entries pointing here
(`context: [spy_fo]`, refire true, refire_cooldown 0, window 1000-1500, min_adv 200e6); a setup name ending "-S" /
"-short" is the short side. Day cap 36 (6 slots x 2N). Live frames carry no symbol column: the symbol is recovered from
the runner's frame cache (_infer_symbol, as ULT-21); unknown symbol, no profile for today or no SPY context -> nothing."""
import json
import math
from pathlib import Path

import numpy as np

_NAME = __name__.lower()
SIDE = "short" if _NAME.endswith(("-s", "_s", "-short", "_short")) else "long"
_SGN = 1 if SIDE == "long" else -1
# ---- fit-frozen pick (round3/ULT-27/fitsel.json); placeholders until the fit is frozen
L = 10                    # look-back sessions
N = 2                     # names per side per slot
# ----
GEOM, EXIT, HOLD_MIN = "S", "X", 30
SLOTS = (1000, 1100, 1200, 1300, 1400, 1500)
WINDOW = (1000, 1500)
MIN_ADV, COST_R_MAX, PX_MIN = 200e6, 0.05, 10.0
MAX_LIST_PER_SYM = 2
VALID_FRAC = 0.7
ATR_N, ATR_MIN = 14, 5
RSI5_SHORT_MIN, GAP_SHORT_MAX = 25.0, 0.5
HERE = Path(__file__).resolve().parent
_U = json.loads((HERE / "ULT-26_symbols.json").read_text())     # LEV / NONLEV lists (fund names only, round 3)
LEV = frozenset(_U["LEV"])
PROFILE_PATH = HERE / "ULT-27_profile.json"
LAYERS = [
    "universe: non-leveraged names, ADV20 >= $200M, price >= $10, cost <= 0.05 of a 0.25-ATR unit",
    f"periodicity score P = mean of the same clock half-hour's ATR-scaled return over the prior {L} sessions",
    f"{'long the top' if _SGN > 0 else 'short the bottom'} {N} names by P at 10:00, 11:00, ..., 15:00 (pre-open lists)",
    ("no long while SPY is -0.30..-0.75% from its open and falling over 30 min" if _SGN > 0 else
     "no short if gap >= +0.5% or RSI(5) < 25; easy to borrow"),
    "exit: 30-min time exit, catastrophic stop 0.5 x daily ATR",
]


def _tod_mult(tod):
    tod = np.asarray(tod, dtype=float)
    return np.where(tod < 935, 3.8, np.where(tod < 950, 2.1, np.where(tod < 1030, 1.4, 1.0)))


def cost_r(px, atr, tod):
    px, atr = np.asarray(px, dtype=float), np.asarray(atr, dtype=float)
    one = 0.01 + px * 1e-4
    with np.errstate(invalid="ignore", divide="ignore"):
        return (one * _tod_mult(tod) + one + 0.02) / (0.25 * atr)


def _m(hhmm):
    return (hhmm // 100) * 60 + hhmm % 100


# ------------------------------------------------------------------ profile (pre-open; shared with the backtest)
def interval_returns(b1m):
    """1-minute bars (tz-aware America/New_York index, open/high/low/close) -> DataFrame index date (str), columns
    SLOTS: raw return C[t+29] / C[t-1] - 1 (NaN when either close is missing within its 5-minute tolerance)."""
    import pandas as pd
    if not len(b1m):
        return pd.DataFrame(columns=list(SLOTS), dtype=float)
    idx = b1m.index
    mins = (idx.hour * 60 + idx.minute).to_numpy()
    day = np.asarray(idx.strftime("%Y-%m-%d"))
    cl = b1m["close"].to_numpy(float)
    out = {}
    st = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    en = np.r_[st[1:], len(day)]
    for a, e in zip(st, en):
        mm, cc = mins[a:e], cl[a:e]
        row = []
        for s in SLOTS:
            v = []
            for tgt in (_m(s) - 1, _m(s) + 29):
                j = np.searchsorted(mm, tgt, side="right") - 1
                v.append(cc[j] if j >= 0 and mm[j] >= tgt - 4 else np.nan)
            row.append(v[1] / v[0] - 1 if np.isfinite(v).all() and v[0] > 0 else np.nan)
        out[day[a]] = row
    return pd.DataFrame.from_dict(out, orient="index", columns=list(SLOTS))


def atr_pct(daily):
    """Daily bars of one symbol (columns date, high, low, close; one contiguous segment, ascending) -> Series
    date -> ATR% known at that date's open: mean true range of the ATR_N previous sessions (min ATR_MIN) / previous
    close x 100."""
    import pandas as pd
    d = daily.sort_values("date")
    pc = d["close"].shift(1)
    tr = np.maximum(d["high"], pc) - np.minimum(d["low"], pc)
    tr = tr.where(pc.notna())
    atr = tr.rolling(ATR_N, min_periods=ATR_MIN).mean().shift(1)
    return pd.Series((atr / pc * 100).to_numpy(), index=d["date"].astype(str).to_numpy())


def scores(xn, L_=None):
    """xn: DataFrame rows = consecutive open sessions in order (sessions with no data, e.g. the locked block, present
    as NaN rows), columns SLOTS, ATR-scaled returns of one symbol. Returns P per row = mean of the previous L rows,
    NaN when fewer than ceil(0.7 L) are valid. Row r uses rows r-L..r-1 only."""
    L_ = L if L_ is None else L_
    return xn.rolling(L_, min_periods=math.ceil(VALID_FRAC * L_)).mean().shift(1)


def preopen_ok(adv20, prev_close, atr_d, tod):
    return ((np.asarray(adv20, float) >= MIN_ADV) & (np.asarray(prev_close, float) >= PX_MIN)
            & (np.asarray(atr_d, float) > 0) & (cost_r(prev_close, atr_d, tod) <= COST_R_MAX))


def rank_lists(P, elig_long, elig_short, N_=None):
    """P: DataFrame index symbol, columns SLOTS (today's scores); elig_long / elig_short: DataFrames of bool with the
    same shape (pre-open eligibility per slot). Returns {slot: {"L": [...], "S": [...]}}; a name listed at
    MAX_LIST_PER_SYM earlier slots (either side) is skipped and replaced by the next."""
    N_ = N if N_ is None else N_
    cnt, out = {}, {}
    for s in SLOTS:
        p = P[s]
        lists = {}
        for side, el in (("L", elig_long), ("S", elig_short)):
            q = p[el[s].reindex(p.index).fillna(False).astype(bool) & p.notna()]
            order = sorted(q.index, key=lambda k: ((-q[k] if side == "L" else q[k]), k))
            pick = []
            for k in order:
                if len(pick) >= N_:
                    break
                if cnt.get(k, 0) >= MAX_LIST_PER_SYM or (side == "S" and k in lists.get("L", [])):
                    continue
                pick.append(k)
            lists[side] = pick
        for k in lists["L"] + lists["S"]:
            cnt[k] = cnt.get(k, 0) + 1
        out[s] = lists
    return out


def build_profile(date, xn_by_symbol, meta, etb, L_=None, N_=None, write=False):
    """Pre-open job. xn_by_symbol: {symbol: DataFrame of ATR-scaled returns, rows = the sessions before `date` in
    order (+ any row for `date` itself, ignored), columns SLOTS}; meta: DataFrame index symbol with adv20, prev_close,
    atr_d (all known before the open); etb: set of easy-to-borrow symbols. Returns {date: {slot: {"L":..,"S":..}}}."""
    import pandas as pd
    L_ = L if L_ is None else L_
    rows = {}
    for sym, xn in xn_by_symbol.items():
        if sym in LEV:
            continue
        x = xn[xn.index.astype(str) < str(date)]
        x = pd.concat([x, pd.DataFrame([[np.nan] * len(SLOTS)], index=[str(date)], columns=list(SLOTS))])
        rows[sym] = scores(x, L_).iloc[-1]
    P = pd.DataFrame(rows).T.reindex(columns=list(SLOTS))
    m = meta.reindex(P.index)
    el = pd.DataFrame({s: preopen_ok(m.adv20, m.prev_close, m.atr_d, s) for s in SLOTS}, index=P.index)
    es = el & np.asarray(P.index.isin(list(etb)))[:, None]
    prof = {str(date): {str(s): v for s, v in rank_lists(P, el, es, N_).items()}}
    if write:
        PROFILE_PATH.write_text(json.dumps(prof))
    return prof


_PROF = [None, None]


def load_profile():
    if not PROFILE_PATH.exists():
        return {}
    mt = PROFILE_PATH.stat().st_mtime
    if _PROF[0] != mt:
        _PROF[:] = [mt, json.loads(PROFILE_PATH.read_text())]
    return _PROF[1]


# ------------------------------------------------------------------ in-day features and filters
def _keys(df):
    import pandas as pd
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    return day


def features(df) -> dict:
    """Point-in-time inputs at each decision bar close (rows of ONE symbol-day or many, sorted by symbol, date, tod)."""
    import pandas as pd
    n = len(df)
    c = lambda k: df[k].to_numpy(dtype=float)   # noqa: E731
    px, atr, tod = c("close"), c("atr_d"), c("tod").astype(int)
    fo = c("spy_fo") if "spy_fo" in df.columns else np.full(n, np.nan)
    day = _keys(df)
    # SPY 30-min change: spy_fo now vs spy_fo at tod - 30 min of the same session (0 at the 09:30 open)
    lk = pd.Series(fo, index=pd.MultiIndex.from_arrays([day, tod]))
    lk = lk[~lk.index.duplicated()]
    back = tod - 30 - np.where(tod % 100 < 30, 40, 0)
    prev = lk.reindex(pd.MultiIndex.from_arrays([day, back])).to_numpy(float)
    prev = np.where(back == 930, 0.0, prev)
    with np.errstate(invalid="ignore"):
        spy_r30 = ((1 + fo / 100) / (1 + prev / 100) - 1) * 100
    return {"tod": tod, "close": px, "atr_d": atr, "gap": c("gap"), "rsi5": c("rsi5"), "cost_r": cost_r(px, atr, tod),
            "spy_fo": fo, "spy_r30": spy_r30, "day": day}


def day_ok(r, sgn) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        base = ((r["close"] >= PX_MIN) & (r["cost_r"] <= COST_R_MAX) & (np.abs(r["gap"]) < 20) & (r["atr_d"] > 0)
                & np.isfinite(r["spy_fo"]))          # fail safe: no SPY context at the bar -> no signal (both sides)
        if sgn > 0:
            bad = (r["spy_fo"] <= -0.30) & (r["spy_fo"] >= -0.75) & (r["spy_r30"] < 0)
            return base & ~bad
        return base & (r["gap"] < GAP_SHORT_MAX) & (r["rsi5"] >= RSI5_SHORT_MIN)


def listed(r, syms, prof, sgn) -> np.ndarray:
    side = "L" if sgn > 0 else "S"
    out = np.zeros(len(r["tod"]), bool)
    for i, (d, t, s) in enumerate(zip(r["day"], r["tod"], syms)):
        lst = prof.get(str(d), {}).get(str(int(t)))
        out[i] = bool(lst) and s in lst.get(side, ())
    return out


def mask(df, sym=None, prof=None) -> np.ndarray:
    if "spy_fo" not in df.columns:          # fail safe: no market context -> no signal (needs `context: [spy_fo]`)
        return np.zeros(len(df), bool)
    if "symbol" in df.columns:
        syms = df["symbol"].astype(str).to_numpy()
    else:
        sym = sym or _infer_symbol(df)
        if sym is None:
            return np.zeros(len(df), bool)
        syms = np.full(len(df), sym, dtype=object)
    prof = load_profile() if prof is None else prof
    if not prof:
        return np.zeros(len(df), bool)
    r = features(df)
    return listed(r, syms, prof, _SGN) & day_ok(r, _SGN) & np.isin(r["tod"], SLOTS)


def _infer_symbol(df):
    """Live LabStrategy frames carry no symbol column; the runner caches one feature frame per (symbol, date, n bars,
    last bar) in mcf.strategies.setups._LAB_FRAMES, so the symbol is the key whose frame has the same index and
    closes (as ULT-21). None when no unique match."""
    try:
        from mcf.strategies.setups import _LAB_FRAMES
    except Exception:
        return None
    hits = set()
    c = df["close"].to_numpy(float)
    for key, f in list(_LAB_FRAMES.items()):
        if len(f) == len(df) and f.index.equals(df.index) and np.array_equal(f["close"].to_numpy(float), c,
                                                                              equal_nan=True):
            hits.add(key[0])
    return hits.pop() if len(hits) == 1 else None


def stop_price(f, i) -> float:
    """GEOM "S": catastrophic stop 2u = 0.5 x atr_d beyond the decision close."""
    return float(f["close"].iloc[i]) - _SGN * 2 * 0.25 * float(f["atr_d"].iloc[i])
