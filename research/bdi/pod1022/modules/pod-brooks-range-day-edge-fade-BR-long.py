"""pod-brooks-range-day-edge-fade-BR-long - Trading-range day: fade the bottom of the day range (config BR, LONG).

Source: Al Brooks 'Trading Price Action Trading Ranges' and Brooks Trading Course Q&A (buy low, sell high on range
days); Bear Bull Traders 'VWAP Trading Strategies' (VWAP as target, double bottom at a level). MERGED idea.
URL: https://www.brookstradingcourse.com/?p=57348

VARIANT of obos-levels, CWT13 VWAP-stretch fade, ENVF 2-SD fade, DCN flat-VWAP layer, GEN-261020-05 and backlog
wi-overreaction-fade. Stated change: a range-day gate from the VWAP-cross count / small range, entry by POSITION in
the day range (BR) or a held retest of the extreme (RT), midpoint / VWAP target.
Rules (plain English, LONG; SHORT mirrors at the top):
  Day gate at the signal bar: day range (HOD - LOD, incl. 09:30-09:45) <= 0.8 x atr_d.
  Config BR: VWAP crossed >= 4 times since 09:50 (sign changes of close vs VWAP); |fromOpen| <= 0.4% and
    |spy_fo| <= 0.4%. Trigger: day_pos <= 0.20, lower_wick >= 0.4, close > prior close, RSI(5) <= 35, the bar does
    not make a new LOD by more than 0.05 ATR. Stop: LOD - 0.10 x atr_d. Target: the day-range midpoint.
  Config RT: VWAP flat (|VWAP_i - VWAP_(i-12)| <= 0.05 x atr_d) and SPY range <= 0.6 x SPY daily ATR(14) (SPY range =
    max - min of spy_fo since 09:50, a close-based proxy; SPY ATR from completed days). Trigger: LOD unchanged over
    the last 6 bars (set >= 6 bars earlier), low_i within 0.08 x atr_d of LOD and not below it by > 0.03 ATR,
    RSI(14) <= 40, up bar, VWAP >= 0.2 x atr_d above the close. Stop: LOD - 0.08 x atr_d. Target: VWAP.
  Both: skip if the target is < 0.6R away. Entry: close. GEOM S. Bar close 11:00-14:30. Flat 15:55.
Pre-declared single choices inside the source ranges (no tuning, no valid-period look): day range 0.8 ATR (range
0.6-1.0), RSI(5) 35 (30-35), stop 0.10 / 0.08 ATR (0.08-0.10), window start 11:00 (11:00/11:30). Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; daily values come
from completed days only.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
CONFIG = "BR"
DAY_RANGE_MAX = 0.8
RSI5_EDGE = 35
STOP_ATR = 0.1
CONTEXT = ["spy_fo"]
LAYERS = ["day range <= 0.8 ATR", "VWAP crosses >= 4, |fromOpen| and |spy_fo| <= 0.4%",
          "edge fifth of the day range, wick, reversal bar, RSI5",
          "target day midpoint >= 0.6R away", "11:00-14:30 ET"]

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
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    hod, lod, vwap, vd = b["hod"], b["lod"], b["vwap"], b["vd"]
    c1 = _lag(c, k)
    with np.errstate(invalid="ignore", divide="ignore"):
        rngd = hod - lod
        g = rngd <= DAY_RANGE_MAX * atr
        if CONFIG == "BR":
            sg = np.sign(vd)
            sp = _lag(sg, k)
            cr = (sg != 0) & np.isfinite(sp) & (sp != 0) & (sg != sp)
            g &= _gcum(cr, k) >= 4                                         # vwap_cross_n since 09:50
            g &= (np.abs(_f(df, "fromOpen")) <= 0.4) & (np.abs(_f(df, "spy_fo")) <= 0.4)
            pos = (c - lod) / rngd
            if SIDE == "long":
                m = (pos <= 0.20) & (_f(df, "lower_wick") >= 0.4) & (c > c1) & (_f(df, "rsi5") <= RSI5_EDGE)
                m &= l >= _lag(lod, k) - 0.05 * atr
                stop = lod - STOP_ATR * atr
                tgt = (hod + lod) / 2
            else:
                m = (pos >= 0.80) & (_f(df, "upper_wick") >= 0.4) & (c < c1) & (_f(df, "rsi5") >= 100 - RSI5_EDGE)
                m &= h <= _lag(hod, k) + 0.05 * atr
                stop = hod + STOP_ATR * atr
                tgt = (hod + lod) / 2
        else:  # RT
            g &= np.abs(vwap - _lag(vwap, k, 12)) <= 0.05 * atr            # flat VWAP over 12 bars
            spyr = _gcummax(_f(df, "spy_fo"), k) - _gcummin(_f(df, "spy_fo"), k)  # SPY close range since 09:50, %
            satr = _map_spy_atr_pct(df, k)
            if satr is None:
                return z
            g &= spyr <= 0.6 * satr
            rsi = _f(df, "rsi")
            if SIDE == "long":
                ext1, ext6 = _lag(lod, k), _lag(lod, k, 6)
                m = np.abs(ext6 - ext1) <= 1e-6 * c                         # LOD set >= 6 bars earlier
                m &= (l - ext1 <= 0.08 * atr) & (l >= ext1 - 0.03 * atr)
                m &= (rsi <= 40) & (c > c1) & (vwap - c >= 0.2 * atr)
                stop = lod - STOP_ATR * atr
                tgt = vwap
            else:
                ext1, ext6 = _lag(hod, k), _lag(hod, k, 6)
                m = np.abs(ext6 - ext1) <= 1e-6 * c
                m &= (ext1 - h <= 0.08 * atr) & (h <= ext1 + 0.03 * atr)
                m &= (rsi >= 60) & (c < c1) & (c - vwap >= 0.2 * atr)
                stop = hod + STOP_ATR * atr
                tgt = vwap
        m &= g
        risk = np.abs(c - stop)
        m &= np.abs(tgt - c) >= 0.6 * risk                                 # skip if the target is < 0.6R away
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
