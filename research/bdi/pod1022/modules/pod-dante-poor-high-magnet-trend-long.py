"""pod-dante-poor-high-magnet-trend-long - The prior day's POOR high as a magnet: buy a held VWAP pullback with the
target at the poor high (LONG). Structural stop, structural target.

Source: Trader Dante 'Auction Market Theory & Market Profile Explained' (poor highs get repaired) + TradeThatSwing /
edgeful PDH-touch statistics ('Several 70%+ High Probability Intraday Stock Market Patterns'). Not re-fetched this round.
URL: https://tradethatswing.com/high-probability-stock-market-statistics/

VARIANT of pod-inside-open-pdh-magnet (IO / PH configs; scored with --ref for the duplicate check). Stated changes:
D-1's high must be POOR (multi-bucket flat top, not just a high close), there is no inside-open requirement, and the
entry is a VWAP pullback hold, not a drift entry.

Rules (plain English, LONG):
  1. D-1 poor high: >= 2 of D-1's 30-min buckets (09:30-10:00, 10:00-10:30, ... built from D-1's visible 5-min bars)
     have a high within 0.05 x atr_d of the PDH (D-1's daily high), and D-1 closed in the top 35% of its daily range
     (completed day; daily table).
  2. Today's open is below the PDH by 0.3-1.5 x atr_d.
  3. Bar close 10:00-13:30: close above session VWAP and above today's open; the bar's low comes within
     0.1 x ATR5m of VWAP (|low - VWAP| <= 0.1 x ATR5m) and the bar closes above VWAP (the pullback holds).
  4. The target is >= 1.0R above the entry.
  Entry: the close of the hold bar. Stop (GEOM S): min(bar low, VWAP - 0.25 x ATR5m). Target: PDH - 0.02 x atr_d
  (limit). Flat 15:55 (the source's time stop).
Harness approximation (declared): the frames hold 09:50-15:00 bars, so D-1's first bucket is 09:45-10:00 only and the
15:00-16:00 buckets are not visible (a poor high printed in the last hour is missed). The previous open month's
last day is read for the first day of a month (never the locked block).
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1330)
LAYERS = [">= 2 D-1 30-min highs within 0.05 ATR of PDH, D-1 close in top 35%", "open 0.3-1.5 ATR below PDH",
          "close > VWAP and > open, low within 0.1 ATR5m of VWAP", "target PDH - 0.02 ATR >= 1R",
          "stop min(low, VWAP - 0.25 ATR5m)"]

import sys
from pathlib import Path

import numba
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


def _segs(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


def _lib():
    try:
        import lib
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "history2y"))
        import lib
    return lib


def _base(df):
    """Point-in-time levels per row (all from the bar itself or earlier / completed prior days)."""
    c, atr = _f(df, "close"), _f(df, "atr_d")
    b = dict(c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr, tod=df["tod"].to_numpy(np.int64))
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr          # running low of day (includes 09:30-09:45)
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") / 100 * c               # 5m ATR(14), $
    return b


def _prev_month(m):
    y, mo = int(m[:4]), int(m[5:7])
    y, mo = (y - 1, 12) if mo == 1 else (y, mo - 1)
    return f"{y:04d}-{mo:02d}"


def _open_month(m):
    """True only for an OPEN month (never the rule-19 locked block)."""
    L = _lib()
    return m not in L.LOCKED_MONTHS and m in set(L.months())


def mask(df) -> np.ndarray:
    n = len(df)
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])


def _daily_prev():
    """Per (symbol, date D): D-1's daily high / low / close and D-1's date (completed days only)."""
    if "dp" in _DC:
        return _DC["dp"]
    d = _lib().daily()[["symbol", "date", "high", "low", "close"]].copy()
    d["symbol"] = d["symbol"].astype(str)
    d["date"] = d["date"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    g = d.groupby("symbol")
    out = pd.DataFrame({"symbol": d["symbol"], "date": d["date"], "pdate": g["date"].shift(1),
                        "ph": g["high"].shift(1), "pl": g["low"].shift(1), "pcl": g["close"].shift(1)})
    gap = (pd.to_datetime(out["date"]) - pd.to_datetime(out["pdate"])).dt.days
    out = out[out["pdate"].notna() & (gap <= 5)]
    _DC["dp"] = out
    return out


def _bucket_highs(months):
    """(symbol, pdate) -> the 13 30-min bucket highs of that day from the raw 5-min frames (open months only)."""
    L = _lib()
    parts = []
    for mo in sorted(months):
        if not _open_month(mo):
            continue
        p = L.load_month(mo, columns=["symbol", "date", "tod", "high"])
        parts.append(p)
        pm = _prev_month(mo)
        if pm not in months and _open_month(pm):
            q = L.load_month(pm, columns=["symbol", "date", "tod", "high"])
            parts.append(q[q["date"] == q["date"].max()])
    if not parts:
        return None
    t = pd.concat(parts, ignore_index=True)
    tod = t["tod"].to_numpy(np.int64)
    start = (tod // 100) * 60 + tod % 100 - 5 - 570          # bar start, minutes after 09:30
    t["bk"] = np.clip(start // 30, 0, 12)
    w = t.groupby([t["symbol"].astype(str), t["date"].astype(str), "bk"])["high"].max().unstack("bk")
    w = w.reindex(columns=range(13))
    w.index.names = ["symbol", "pdate"]
    return w.reset_index()


def _compute(df):
    n = len(df)
    z = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n:
        return z
    ds = df["date"].astype(str).to_numpy()
    k = _key(df)
    st = np.r_[True, k[1:] != k[:-1]]
    rep = np.cumsum(st) - 1
    u = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy()[st], "date": ds[st]})
    u = u.merge(_daily_prev(), on=["symbol", "date"], how="left")
    bh = _bucket_highs(set(x[:7] for x in np.unique(ds)))
    if bh is None:
        return z
    u = u.merge(bh, on=["symbol", "pdate"], how="left")
    b = _base(df)
    atr = b["atr"]
    a0 = atr[st]
    ph = u["ph"].to_numpy(float)
    H = u[list(range(13))].to_numpy(float)
    with np.errstate(invalid="ignore"):
        touch = (H >= (ph - 0.05 * a0)[:, None]).sum(axis=1)
        rng = u["ph"].to_numpy(float) - u["pl"].to_numpy(float)
        cl = (u["pcl"].to_numpy(float) - u["pl"].to_numpy(float)) / rng
        day_ok = (touch >= 2) & (cl >= 0.65) & (rng > 0)                                  # (1)
        pdh = ph[rep]
        c, l, vwap, a5, opn, tod = b["c"], b["l"], b["vwap"], b["atr5"], b["opn"], b["tod"]
        m = day_ok[rep]
        m &= ((pdh - opn) >= 0.3 * atr) & ((pdh - opn) <= 1.5 * atr)                     # (2)
        m &= (tod >= 1000) & (tod <= 1330)
        m &= (c > vwap) & (c > opn) & (np.abs(l - vwap) <= 0.1 * a5)                     # (3)
        stop = np.minimum(l, vwap - 0.25 * a5)
        tgt = pdh - 0.02 * atr
        R = c - stop
        m &= (R > 0) & (tgt - c >= R)                                                    # (4)
        m &= np.isfinite(stop) & np.isfinite(tgt)
    return np.asarray(m, bool), stop, tgt
