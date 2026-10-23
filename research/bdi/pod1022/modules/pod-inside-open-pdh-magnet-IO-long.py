"""pod-inside-open-pdh-magnet-IO-long - Inside-range open: ride the drift toward the prior-day high (PDH as the magnet target) (LONG, config IO).

Source: TradeThatSwing (Cory Mitchell, from edgeful data) 'Several 70%+ High Probability Intraday Stock Market
Patterns'; Trader Dante 'Auction Market Theory & Market Profile Explained' (poor highs as unfinished business).
MERGED idea.
URL: https://tradethatswing.com/high-probability-stock-market-statistics/

ORIGINAL trigger: trades the move TO the PDH with the target AT it. Related but different: obos-levels (fades at
PDH), CWT10 / ST5 (PDH breakout), bdi-reddit-pdhl-break-retest.
Rules (plain English):
  Config IO: 1. open strictly between PDL and PDH and |gap| <= 0.4%. 3. close > VWAP, fromOpen > 0, RSI(14) 50-70.
    4. QQQ above its session VWAP (qqq_vwap > 0) - the frame has no SPY-vs-VWAP context, so QQQ is the stand-in.
    Bar close 09:50-11:30.
  Config PH: 1. D-1 close in the top 10% of its range (poor-high proxy, completed day) and |open - prior close| <=
    0.3 x atr_d. 3. vwapReclaim == 1, or a lower_wick >= 0.4 bar above VWAP, with sma20_slope_pct > 0.
    4. breadth >= 0.5. Bar close 10:00-13:30.
  Both: 2. 0.30 <= dist_pdh_atr <= 1.0 and no PDH tag yet today (HOD < PDH).
  Entry: first qualifying close. Target: PDH - 0.02 x atr_d (limit). Stop (GEOM S): max(LOD, entry - 0.25 x atr_d),
  and never closer than 0.05 x atr_d to the entry (guard against a near-zero R when the close sits on the LOD).
  Flat 15:55.
Pre-declared choice inside the source range: dist_pdh_atr floor 0.30 (range 0.25-0.40). Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; daily values come
from completed days only.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (950, 1130)
CONFIG = "IO"
CONTEXT = ["qqq_vwap"]

LAYERS = ["open inside D-1 range, |gap| <= 0.4%", "0.30-1.0 ATR below PDH, no tag yet",
          "above VWAP, up on day, RSI 50-70", "QQQ above VWAP",
          "target PDH - 0.02 ATR, stop max(LOD, 0.25 ATR)"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ST = {}
_DC = {}
ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each group k."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _gcummin(x, k):
    return pd.Series(np.asarray(x, float)).groupby(k).cummin().to_numpy(float)


def _gcummax(x, k):
    return pd.Series(np.asarray(x, float)).groupby(k).cummax().to_numpy(float)


def _rowpos(k):
    """0-based bar index within the symbol-day."""
    return _gcum(np.ones(len(k)), k) - 1


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to its symbol-day. Used only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vd"] = _f(df, "vwapDistPct")
    b["vwap"] = c / (1 + b["vd"] / 100)
    b["sma20"] = c / (1 + _f(df, "sma20_dist_pct") / 100)
    return b


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _daily_feats():
    """Per (symbol, date D): daily values as of D-1's close (completed days only). Series restart after a calendar
    gap > 7 days (the locked block is absent from lib.daily())."""
    if "f" in _DC:
        return _DC["f"]
    try:
        d = _lib().daily()[["symbol", "date", "high", "low", "close"]].copy()
    except Exception:
        _DC["f"] = None
        return None
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    dt = pd.to_datetime(d["date"])
    g = ((d["symbol"] != d["symbol"].shift()) | ((dt - dt.shift()).dt.days > 7)).cumsum()
    c, h, l = d["close"], d["high"], d["low"]
    gc = c.groupby(g)
    pcl = gc.shift(1)
    tr = pd.concat([h - l, (h - pcl).abs(), (l - pcl).abs()], axis=1).max(axis=1)
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c, "d_high": h, "d_low": l,
        "d_high_p": h.groupby(g).shift(1), "d_low_p": l.groupby(g).shift(1),
        "sma200": gc.transform(lambda x: x.rolling(200, min_periods=100).mean()),
        "atr14": tr.groupby(g).transform(lambda x: x.rolling(14).mean()),
    })
    for col in [x for x in f.columns if x not in ("symbol", "date")]:
        f[col] = f[col].groupby(g).shift(1)          # the row for D carries the values as of D-1's close
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


def _map_spy_atr_pct(df, k):
    """SPY daily ATR(14) as of D-1, in % of SPY's D-1 close, per row."""
    f = _daily_feats()
    if f is None:
        return None
    s = f[f["symbol"] == "SPY"][["date", "atr14", "d_close"]]
    st = _start(k)
    u = pd.DataFrame({"date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(s, on="date", how="left")
    v = (m["atr14"] / m["d_close"] * 100).to_numpy(float)
    return v[np.cumsum(st) - 1]


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    if s is None or s[j] is None:
        return float("nan")
    return float(s[j][i])


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    need = "qqq_vwap" if CONFIG == "IO" else "breadth"
    if not len(df) or need not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    pdh, pdl, opn, pc = b["pdh"], b["pdl"], b["opn"], b["pc"]
    dpa = _f(df, "dist_pdh_atr")
    rsi = _f(df, "rsi")
    with np.errstate(invalid="ignore", divide="ignore"):
        if CONFIG == "IO":
            m = (opn > pdl) & (opn < pdh) & (np.abs(_f(df, "gap")) <= 0.4)                     # (1)
        else:
            dd = _map_daily(df, k, ["d_close", "d_high", "d_low"])
            if dd is None:
                return z
            m = (dd["d_close"] - dd["d_low"]) >= 0.9 * (dd["d_high"] - dd["d_low"])              # poor-high proxy
            m &= np.abs(opn - pc) <= 0.3 * atr
        m &= (dpa >= 0.30) & (dpa <= 1.0) & (b["hod"] < pdh)                                     # (2) room, no tag yet
        if CONFIG == "IO":
            m &= (b["vd"] > 0) & (_f(df, "fromOpen") > 0) & (rsi >= 50) & (rsi <= 70)             # (3)
            m &= _f(df, "qqq_vwap") > 0                                                          # (4) proxy for SPY > VWAP
        else:
            m &= (_f(df, "vwapReclaim") == 1) | ((_f(df, "lower_wick") >= 0.4) & (b["vd"] > 0))
            m &= _f(df, "sma20_slope_pct") > 0
            m &= _f(df, "breadth") >= 0.5
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = np.minimum(np.maximum(b["lod"], c - 0.25 * atr), c - 0.05 * atr)
        tgt = pdh - 0.02 * atr
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
