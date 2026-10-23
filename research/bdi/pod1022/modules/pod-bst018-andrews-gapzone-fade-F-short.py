"""pod-bst018-andrews-gapzone-fade-F-short - Andrews in-range gap fade to the prior close (stocks + ETFs; ETF half-gap long config). THIS FILE: config F, SHORT side.

Source: Better System Trader ep 018, Scott Andrews 'The Gap Guy' (gap zones, gap size vs 5-day ATR, fade vs follow,
half-gap targets); MoneyShow transcript (40%-of-ATR5 rule). MERGED from pod-bst018-andrews-gapzone-fade and
pod-andrews-gapdown-uptrend-halfgap-etf.
URL: https://bettersystemtrader.libsyn.com/018-scott-andrews-the-gap-guy-talks-all-about-gaps-why-they-work-how-to-pick-the-best-gaps-and-avoid-the-worst-gap-zones-and-setting-stops-and-targets-plus-we-discuss-a-concept-called-ensemble-systems-that-may-just-change-the-way-you-view-trading-strategi

VARIANT of index_gap_fill (index ETFs, 0.10-0.40% gaps, target prior close, exit 12:00), R05 gap fill (failed) and
CWT43 failed gap auction (failed, gaps BEYOND the range). Stated change: only Andrews' inside-zone gaps sized
0.10-0.40 x ATR5, traded AGAINST yesterday's close-to-close direction, with a confirmation trigger.

Rules (plain English):
  1. Today's open is strictly inside the prior-day range (PDL < open < PDH) and 0.10 <= |open - prior close| / ATR5
     <= 0.40 (ATR5 = mean true range of D-5..D-1 from the daily table, completed days only).
  2. rvol_day <= 1.5 at the trigger (proxy: mean volumeRatio of the day's bars from 09:50 through the trigger bar;
     the harness has no raw volume - the arena indicator 'rvol_day' definition).
  3. Gap up after a down day (D-1 close < D-2 close) -> short; gap down after an up day -> long.
  4. Trigger 09:55-10:15 bar close: the FIRST close that is both beyond the 09:30-09:50 extreme on the fill side (below the LOD as
     of the 09:50 bar for a short, above the HOD for a long; the harness has no 09:35 bar), and on the fill side of
     session VWAP.
  Entry: that close. Stop (GEOM S): the day's extreme so far (HOD for a short, LOD for a long) + 0.05 x atr_d.
  Target: config F = the prior close; config H = half the gap ((open + prior close) / 2). The target must still be
  beyond the entry. Flat 15:55 (the source's 11:30 / 12:00 time stops are not in the harness).
  CONFIG ETF (file -etf-long): SPY/QQQ/IWM/DIA, long only, rules 1-4 plus D-1 close above the daily SMA20, target
  half-gap.
Files: -F-long, -F-short, -H-long, -H-short, -etf-long. All configs are the source's own (pre-declared); no tweak.
Costs per config/default.yaml (applied by the scorer; entries before 10:30 carry the x1.4 cost).
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (955, 1015)
CFG = "F"
LAYERS = ["open inside prior-day range, gap 0.10-0.40 x ATR5", "rvol_day proxy <= 1.5", "gap against D-1 direction",
          "first close beyond the 09:50 extreme on the fill side, fill side of VWAP", "stop day extreme + 0.05 ATR",
          "target prior close (F) / half gap (H, ETF)", "09:55-10:15"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

LONG = SIDE == "long"
_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _prev(x, k, n=1):
    """x shifted n bars back inside the same symbol-day (NaN where that bar is in another symbol-day)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        same = np.zeros(len(x), bool)
        same[n:] = k[n:] == k[:-n]
        p[~same] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _first(cond, k):
    """True only on the first True row of each symbol-day (no earlier row qualified)."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to the whole symbol-day (NaN when that bar is missing).
    Callers only use it on rows with tod > T (or == T), so nothing later than the decision bar is used."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


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
    return b


def _daily_feats():
    """Per (symbol, date D): daily values known at D's open, computed on completed days up to D-1 only.
    Series restart after a calendar gap > 7 days (the locked block is absent from lib.daily(), so the SMA50 / 20-day
    values are NaN until enough post-gap days exist)."""
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
    c, h, l = d["close"], d["high"], d["low"]
    gc = c.groupby(g)
    pc = gc.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1).where(pc.notna())
    rng = (h - l).replace(0, np.nan)
    f = pd.DataFrame({
        "symbol": d["symbol"], "date": d["date"].astype(str),
        "d_close": c, "d_high": h, "d_low": l,
        "sma20": gc.transform(lambda x: x.rolling(20).mean()),
        "sma50": gc.transform(lambda x: x.rolling(50).mean()),
        "hi20": h.groupby(g).transform(lambda x: x.rolling(20).max()),
        "atr5": tr.groupby(g).transform(lambda x: x.rolling(5).mean()),
        "dchg": c - pc,
        "ibs": (c - l) / rng,
    })
    cols = [x for x in f.columns if x not in ("symbol", "date")]
    for col in cols:                       # the row for D carries the values as of D-1's close
        f[col] = f[col].groupby(g).shift(1)
    _DC["f"] = f
    return f


def _map_daily(df, k, cols):
    """Daily features for every frame row (via its symbol-day), NaN when missing."""
    f = _daily_feats()
    if f is None:
        return None
    st = _start(k)
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": df["date"].astype(str).to_numpy()[st]})
    m = u.merge(f, on=["symbol", "date"], how="left")
    return {c: m[c].to_numpy(float)[np.cumsum(st) - 1] for c in cols}


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[0][i]) if s is not None else float("nan")


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, atr = b["k"], b["tod"], b["c"], b["atr"]
    dd = _map_daily(df, k, ["atr5", "dchg", "d_close", "sma20"])
    if dd is None:
        return z
    opn, pc = b["opn"], b["pc"]
    vr = _f(df, "volumeRatio")
    fin = np.isfinite(vr)
    rvol = _gcum(np.where(fin, vr, 0.0), k) / np.where(_gcum(fin, k) > 0, _gcum(fin, k), np.nan)
    hod950, lod950 = _at(b["hod"], k, tod, 950), _at(b["lod"], k, tod, 950)
    inwin = (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    with np.errstate(invalid="ignore", divide="ignore"):
        gsz = np.abs(opn - pc) / dd["atr5"]
        m = (opn > b["pdl"]) & (opn < b["pdh"]) & (gsz >= 0.10) & (gsz <= 0.40)
        m &= rvol <= 1.5
        if LONG:
            m &= (opn < pc) & (dd["dchg"] > 0)
            m &= _first(inwin & (c > hod950) & (c > b["vwap"]), k)
            stop = b["lod"] - 0.05 * atr
            tgt = pc if CFG == "F" else (opn + pc) / 2
            if CFG == "ETF":
                m &= dd["d_close"] > dd["sma20"]
        else:
            m &= (opn > pc) & (dd["dchg"] < 0)
            m &= _first(inwin & (c < lod950) & (c < b["vwap"]), k)
            stop = b["hod"] + 0.05 * atr
            tgt = pc if CFG == "F" else (opn + pc) / 2
        m &= inwin
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def target_price(f, i, stop):
    s = _ST.get(id(f))
    if s is None:
        mask(f)
        s = _ST.get(id(f))
    return float(s[1][i]) if s is not None and s[1] is not None else float("nan")
