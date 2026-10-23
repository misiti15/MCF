"""pod-cpr-wide-range-day-pivot-fade-short - Wide central-pivot-range day: fade S1/R1 back to the CPR (SHORT).

Source: Frank Ochoa 'Secrets of a Pivot Boss' (CPR width); LuxAlgo 'Central Pivot Range'; ProRealCode 'CPR width'.
URL: https://www.luxalgo.com/library/concept/central-pivot-range.md

VARIANT of the articles indicator grid floor pivots (s1bounce / r1reject, failed) and obos-levels. Sibling of
pod-camarilla-l3-quiet-fade (different levels and gate). Stated change: a pre-open CPR-width regime gate and a
structural fade from S1/R1 to the CPR. Files: -long (fade at S1) and -short (mirror at R1).

Levels from the prior COMPLETED day's H/L/C (daily table, research/history2y lib.daily()):
  P = (H+L+C)/3, BC = (H+L)/2, TC = 2P - BC, S1 = 2P - H, R1 = 2P - L. CPR bottom/top = min/max(BC, TC).
  CPR width = |TC - BC| / P.
Rules (plain English; long shown, short = mirror):
  1. Wide CPR: today's width (from D-1) ranks in the top 30% of the trailing 20 sessions' widths (D-20..D-1 HLC,
     percentile rank > 0.70; completed days only).
  2. Today's open is inside [S1, R1] and |gap| <= 0.5%.
  3. This bar's low <= S1 and it closes back above S1; rsi5 <= 25 on this or the prior bar.
     (short: high >= R1, close back below R1, rsi5 >= 75 on this or the prior bar)
  4. Day range so far (HOD - LOD, incl. 09:30-09:45 via dist_hod/lod_atr) <= 1.2 x atr_d.
  Entry: that close, bar close 10:00-14:30. Stop (GEOM S): S1 - 0.15 x atr_d (short: R1 + 0.15 x atr_d).
  Target: the CPR bottom (long; 'BC' in the conventional ordering) or VWAP, whichever is nearer AND beyond the entry
  (short: CPR top or VWAP); no trade when neither is beyond the entry. Flat 15:55.
Pre-declared reading: rsi5 >= 75 for the short mirror (100 - 25). No tweak used. No tuning on valid.
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = []
LAYERS = ["CPR width (D-1) top 30% of trailing 20 sessions", "open inside [S1, R1], |gap| <= 0.5%",
          "low <= S1 and close > S1, rsi5 <= 25 this or prior bar (short mirror at R1)", "day range <= 1.2 ATR",
          "stop S1 - 0.15 ATR, target nearer of CPR bottom / VWAP", "10:00-14:30 ET"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day (NaN across a day boundary)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _gacc(x, k, fn):
    """Inclusive running max / min (fn = np.fmax / np.fmin) within each symbol-day, ignoring NaN."""
    s = pd.Series(np.asarray(x, float))
    g = s.groupby(k)
    return (g.cummax() if fn is np.fmax else g.cummin()).to_numpy(float)


def _first(cond, k):
    """True only on the first True row of each symbol-day."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _at(x, k, tod, T):
    """Value of x on the bar closing at T, broadcast to its symbol-day. Use only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _sym_ctx(df, sym, x):
    """Column x of symbol `sym` at the same (date, tod) as each row (NaN when that symbol's bar is missing)."""
    s = df["symbol"].astype(str).to_numpy()
    sel = s == sym
    if not sel.any():
        return np.full(len(df), np.nan)
    d = df["date"].astype(str).to_numpy()
    t = df["tod"].to_numpy(np.int64)
    ser = pd.Series(np.asarray(x, float)[sel], index=pd.MultiIndex.from_arrays([d[sel], t[sel]]))
    ser = ser[~ser.index.duplicated()]
    return ser.reindex(pd.MultiIndex.from_arrays([d, t])).to_numpy(float)


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


def _daily_feats():
    """Per (symbol, date D): CPR levels from D-1 HLC and the CPR-width percentile rank over D-20..D-1 (completed
    days only). Series restart after a calendar gap > 7 days (the locked block is absent from lib.daily())."""
    if "f" in _DC:
        return _DC["f"]
    try:
        try:
            import lib
        except ImportError:
            sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
            import lib
        d = lib.daily()[["symbol", "date", "high", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    H, L, C = d["high"], d["low"], d["close"]
    P = (H + L + C) / 3
    BC = (H + L) / 2
    TC = 2 * P - BC
    w = (TC - BC).abs() / P
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "P": P, "cpr_lo": np.minimum(BC, TC), "cpr_hi": np.maximum(BC, TC),
        "S1": 2 * P - H, "R1": 2 * P - L,
        "wrank": w.groupby(g).transform(lambda x: x.rolling(20).rank(pct=True)),
    })
    for col in [x for x in f.columns if x not in ("symbol", "date")]:
        f[col] = f[col].groupby(g).shift(1)          # the row for D carries values as of D-1's close
    _DC["f"] = f
    return f


def _map_daily(df, k, cols):
    f = _daily_feats()
    if f is None:
        return None
    st = _start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(f, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    k = _key(df)
    dd = _map_daily(df, k, ["cpr_lo", "cpr_hi", "S1", "R1", "wrank"])
    if dd is None:
        return z
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    r5 = _f(df, "rsi5")
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = c / (1 + _f(df, "fromOpen") / 100)
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        S1, R1 = dd["S1"], dd["R1"]
        m = (dd["wrank"] > 0.70)
        m &= (opn >= S1) & (opn <= R1) & (np.abs(_f(df, "gap")) <= 0.5)
        m &= (hod - lod) <= 1.2 * atr
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        pr5 = _lag(r5, k)
        if SIDE == "long":
            m &= (l <= S1) & (c > S1) & ((r5 <= 25) | (pr5 <= 25))
            stop = S1 - 0.15 * atr
            a = np.where(dd["cpr_lo"] > c, dd["cpr_lo"], np.nan)
            b = np.where(vwap > c, vwap, np.nan)
            tgt = np.fmin(a, b)
        else:
            m &= (h >= R1) & (c < R1) & ((r5 >= 75) | (pr5 >= 75))
            stop = R1 + 0.15 * atr
            a = np.where(dd["cpr_hi"] < c, dd["cpr_hi"], np.nan)
            b = np.where(vwap < c, vwap, np.nan)
            tgt = np.fmax(a, b)
        m &= np.isfinite(tgt)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
