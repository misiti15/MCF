"""Article indicators (BDI 2026-10-08) on 5-minute bars - causal, one row per 5-minute bar close.

article_features(hist, prev_hlc, daily_closes) takes the same history LabStrategy builds live
(the last 40 prior-session 5-minute bars + today's bars so far) and returns new columns for every row:

  macdh_F_S_G            MACD(F,S) minus its G-signal, % of price (12-26-9, 8-17-9, 5-35-5)
  bbz_{c,lo,hi}_N        (close|low|high - SMA N) / stdev N   (Bollinger z; band touch = z <= -k / >= k), N = 15/20/30
  bbw_20, bbw_pctl       Bollinger(20,2) width % of mid, and its percentile among the last 60 bars (squeeze)
  stk_N, std_N           slow Stochastic(N,3,3) %K and %D, N = 9/14/21
  adx_N, dmi_N           ADX(N) and +DI minus -DI (Wilder), N = 10/14/20
  obv_slope, ad_slope    10-bar change of OBV / Chaikin A-D line, divided by 10-bar volume (-1..1)
  obv_bull, obv_bear     price at a 20-bar low (high) while OBV is not at its 20-bar low (high)
  ema_5_13, ema_9_21, ema_13_34   EMA difference, % of the slower EMA
  sma_20_50              5-min SMA20 minus SMA50, % of SMA50
  rsi14, vwapd           RSI(14) as in heat.py, and % distance to the session VWAP (recomputed for prev values)
  aroon_N                Aroon(N) up minus down, N = 14/25/50
  ichi_tk, ichi_top, ichi_bot   Tenkan-Kijun (% of price) and the cloud (9/26/52, spans shifted 26)
  piv_p, piv_r1, piv_s1  classic pivots from the prior session's high/low/close
  hod, lod, upleg        today's high/low so far and 1 if the HOD came after the LOD (up-leg), else 0
  d_sma20, d_sma50, d_rsi14   daily SMA20/50 and Wilder RSI14 of prior sessions' closes (as of the prior close)
Every column also has a *_prev twin (value at the previous 5-minute bar) where the setups need crosses.
Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

PREV = ["macdh_12_26_9", "macdh_8_17_9", "macdh_5_35_5", "bbw_pctl", "stk_9", "std_9", "stk_14", "std_14", "stk_21",
        "std_21", "dmi_10", "dmi_14", "dmi_20", "ema_5_13", "ema_9_21", "ema_13_34", "sma_20_50", "rsi14", "vwapd",
        "close", "aroon_14", "aroon_25", "aroon_50", "ichi_tk", "ichi_top", "ichi_bot"]


def _rsi_simple(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    g = d.clip(lower=0).rolling(n).sum() / n
    l = (-d.clip(upper=0)).rolling(n).sum() / n
    rsi = 100 - 100 / (1 + g / l.replace(0, np.nan))
    return rsi.where(l != 0, 100.0)


def daily_rsi_wilder(closes: np.ndarray, n: int = 14) -> float:
    if len(closes) < n + 1:
        return np.nan
    d = np.diff(closes)
    g, l = np.clip(d, 0, None), np.clip(-d, 0, None)
    ag, al = g[:n].mean(), l[:n].mean()
    for i in range(n, len(d)):
        ag, al = (ag * (n - 1) + g[i]) / n, (al * (n - 1) + l[i]) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def _aroon(h: np.ndarray, l: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(h), np.nan)
    if len(h) < n + 1:
        return out
    wh, wl = sliding_window_view(h, n + 1), sliding_window_view(l, n + 1)
    since_hi = n - (n - np.argmax(wh[:, ::-1], 1))          # bars since the highest high (latest occurrence)
    since_lo = n - (n - np.argmin(wl[:, ::-1], 1))
    out[n:] = 100 * (n - since_hi) / n - 100 * (n - since_lo) / n
    return out


def _pctl(x: np.ndarray, n: int = 60, minp: int = 30) -> np.ndarray:
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        w = x[max(0, i - n + 1): i + 1]
        w = w[np.isfinite(w)]
        if len(w) >= minp and np.isfinite(x[i]):
            out[i] = (w <= x[i]).mean()
    return out


def article_features(hist: pd.DataFrame, prev_hlc: tuple | None = None, daily_closes: np.ndarray | None = None) -> pd.DataFrame:
    c, h, l, v = hist["close"], hist["high"], hist["low"], hist["volume"]
    x = pd.DataFrame(index=hist.index)
    ema = lambda s, n: s.ewm(span=n, adjust=False).mean()
    for f_, s_, g_ in ((12, 26, 9), (8, 17, 9), (5, 35, 5)):
        line = ema(c, f_) - ema(c, s_)
        hst = (line - ema(line, g_)) / c * 100
        hst[: s_ + g_ - 1] = np.nan                          # not warmed up
        x[f"macdh_{f_}_{s_}_{g_}"] = hst
    for n in (15, 20, 30):
        mid, sd = c.rolling(n).mean(), c.rolling(n).std(ddof=0).replace(0, np.nan)
        x[f"bbz_lo_{n}"], x[f"bbz_hi_{n}"] = (l - mid) / sd, (h - mid) / sd
        if n == 20:
            x["bbz_c_20"] = (c - mid) / sd
            x["bbw_20"] = 4 * sd / mid * 100
    x["bbw_pctl"] = _pctl(x["bbw_20"].to_numpy())
    for n in (9, 14, 21):
        ll, hh = l.rolling(n).min(), h.rolling(n).max()
        k = (100 * (c - ll) / (hh - ll).replace(0, np.nan)).rolling(3).mean()
        x[f"stk_{n}"], x[f"std_{n}"] = k, k.rolling(3).mean()
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    up, dn = h.diff(), -l.diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=c.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=c.index)
    for n in (10, 14, 20):
        w = lambda s: s.ewm(alpha=1 / n, adjust=False).mean()
        atr = w(tr).replace(0, np.nan)
        pdi, mdi = 100 * w(pdm) / atr, 100 * w(mdm) / atr
        dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
        adx = w(dx.fillna(0))
        adx[: 2 * n] = np.nan
        x[f"adx_{n}"], x[f"dmi_{n}"] = adx, (pdi - mdi).where(adx.notna())
    vs10 = v.rolling(10).sum().replace(0, np.nan)
    obv = (np.sign(c.diff()).fillna(0) * v).cumsum()
    x["obv_slope"] = (obv - obv.shift(10)) / vs10
    mfm = (((c - l) - (h - c)) / (h - l).replace(0, np.nan)).fillna(0)
    ad = (mfm * v).cumsum()
    x["ad_slope"] = (ad - ad.shift(10)) / vs10
    x["obv_bull"] = ((l <= l.rolling(20).min()) & (obv > obv.rolling(20).min())).astype(np.int8)
    x["obv_bear"] = ((h >= h.rolling(20).max()) & (obv < obv.rolling(20).max())).astype(np.int8)
    for a, b in ((5, 13), (9, 21), (13, 34)):
        eb = ema(c, b)
        x[f"ema_{a}_{b}"] = (ema(c, a) - eb) / eb * 100
    s20, s50 = c.rolling(20).mean(), c.rolling(50).mean()
    x["sma_20_50"] = (s20 - s50) / s50 * 100
    x["rsi14"] = _rsi_simple(c, 14)
    day = pd.Series(hist.index.date, index=hist.index)
    typ = (h + l + c) / 3
    vw = (typ * v).groupby(day).cumsum() / v.groupby(day).cumsum().replace(0, np.nan)
    x["vwapd"] = (c - vw) / vw * 100
    x["close"] = c
    hv, lv = h.to_numpy(float), l.to_numpy(float)
    for n in (14, 25, 50):
        x[f"aroon_{n}"] = _aroon(hv, lv, n)
    mid = lambda n: (h.rolling(n).max() + l.rolling(n).min()) / 2
    ten, kij = mid(9), mid(26)
    sa, sb = ((ten + kij) / 2).shift(26), mid(52).shift(26)
    x["ichi_tk"] = (ten - kij) / c * 100
    x["ichi_top"], x["ichi_bot"] = np.maximum(sa, sb), np.minimum(sa, sb)
    if prev_hlc is not None:
        ph, pl, pcl = prev_hlc
        p = (ph + pl + pcl) / 3
        x["piv_p"], x["piv_r1"], x["piv_s1"] = p, 2 * p - pl, 2 * p - ph
    # today's swing (for Fibonacci retracements)
    last = hist.index.date[-1]
    today = hist.index.date == last
    hod, lod, upleg = np.full(len(x), np.nan), np.full(len(x), np.nan), np.zeros(len(x), np.int8)
    ti = np.flatnonzero(today)
    if len(ti):
        th, tl = hv[ti], lv[ti]
        hod[ti], lod[ti] = np.maximum.accumulate(th), np.minimum.accumulate(tl)
        ih = np.zeros(len(ti), int)
        il = np.zeros(len(ti), int)
        for j in range(1, len(ti)):
            ih[j] = j if th[j] >= hod[ti[j - 1]] else ih[j - 1]
            il[j] = j if tl[j] <= lod[ti[j - 1]] else il[j - 1]
        upleg[ti] = (ih > il).astype(np.int8)
    x["hod"], x["lod"], x["upleg"] = hod, lod, upleg
    dc = np.asarray(daily_closes if daily_closes is not None else [], float)
    x["d_sma20"] = dc[-20:].mean() if len(dc) >= 20 else np.nan
    x["d_sma50"] = dc[-50:].mean() if len(dc) >= 50 else np.nan
    x["d_rsi14"] = daily_rsi_wilder(dc[-60:]) if len(dc) >= 15 else np.nan
    for k in PREV:
        x[k + "_prev"] = x[k].shift(1)
    return x
