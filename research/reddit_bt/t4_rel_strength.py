"""t4_rel_strength - relative strength / weakness vs SPY, mechanised r/RealDayTrading method (low-medium credibility).

Hypothesis from a web sweep (Reddit bodies unreadable from this server) - a hypothesis, not evidence.
Educational only - not financial advice.

Decision on a completed 1-minute bar k (bar labelled by start time, decision at its close, market entry at the next
1-min bar open). Signal bars start in 09:59..10:29 ("early", fills 10:00-10:30) or 10:29..11:29 ("late", fills
10:30-11:30) - all fills are >= 09:50.
  market filter : long only if SPY close > SPY session VWAP and SPY 5-min EMA9 > EMA21 (completed 5-min bars only,
                  warmed with the 2 prior sessions' 5-min bars); short only if both below.
  RS            : stock return since the 09:30 open minus beta x SPY return since open. beta = beta20 (OLS on up to 20
                  prior daily close-to-close returns, min 15) or 1.0.  RS30 = same over the last 30 one-minute bars.
  long          : RS > c x (daily ATR / prev close), RS30 > 0, close > session VWAP,
                  cumulative volume since open > 1.2 x the 14-session average cumulative volume at the same minute,
                  daily trend: prev close > SMA20 of daily closes. SMA50 is NOT used: data/cache starts 2026-06-15,
                  so only ~20 sessions of history exist at the train start (SMA50 impossible on train) - SMA20 is the
                  substitute, applied identically on every split.  Shorts mirror.
  ranking       : one trade per symbol per day; at most 10 trades per day across the universe. Minutes are processed
                  in time order; on each minute the newly qualifying symbols are ranked by |RS| and taken until the
                  day's cap is used (live-implementable: the runner scans the universe at each bar close).
  stop          : 0.25 x daily ATR from the signal close.
  exits         : "1R" target +1R; "hold" no target, stop to breakeven at +1R, flat 15:55;
                  "holdts" = hold + time stop after 60 min if MFE < 0.3R.
Grid (pre-declared, 30): c {0.25,0.5,1.0} x window {early,late} x exit {1R,hold,holdts} with beta20 + trend (18);
plus c=0.5 without the daily trend filter (6) and c=0.5 with beta 1.0 (6).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mcf import features as F
from mcf.strategies.base import Signal

from . import common as C

NAME = "t4_rel_strength"
UNIVERSE = "top300"
WINDOWS = {"early": (599, 629), "late": (629, 689)}  # signal-bar start minute-of-day, inclusive
CAP = 10
_U = [s.strip() for s in (Path(__file__).parent / "top300.txt").read_text().split() if s.strip()]

VARIANTS: dict = {}
for _c in (0.25, 0.5, 1.0):
    for _w in ("early", "late"):
        for _e in ("1R", "hold", "holdts"):
            VARIANTS[f"c{_c}_{_w}_{_e}"] = {"c": _c, "win": _w, "exit": _e, "trend": True, "beta": "b20"}
for _w in ("early", "late"):
    for _e in ("1R", "hold", "holdts"):
        VARIANTS[f"c0.5_{_w}_{_e}_nt"] = {"c": 0.5, "win": _w, "exit": _e, "trend": False, "beta": "b20"}
        VARIANTS[f"c0.5_{_w}_{_e}_b1"] = {"c": 0.5, "win": _w, "exit": _e, "trend": True, "beta": "b1"}

# Result: all 30 variants have exp_r < 0 on train after costs (best c0.5_late_1R_b1 -0.027R); valid was positive for
# most (regime-dependent, 14 days) but a finalist needs train > 0 too -> no finalists.
FINALISTS: list[str] = []
BASELINE = {"stop_atr": 0.25, "target_atr": 0.25}

_TABLE: dict = {}   # date -> per-symbol feature arrays (variant independent)
_PICKS: dict = {}   # (date, entry key) -> {symbol: (bar_index, side, close, atr)}
_CUMV: dict = {}    # symbol -> (dates, cum-volume matrix on the 390-minute grid)


def _mins(idx) -> np.ndarray:
    return idx.hour.to_numpy() * 60 + idx.minute.to_numpy()


def _cumv(sym: str, cache: str):
    if sym not in _CUMV:
        days = C._hist(cache, sym)[0]
        ds = sorted(days)
        M = np.zeros((len(ds), 390))
        for i, d in enumerate(ds):
            g = days[d]
            m = _mins(g.index) - 570
            ok = (m >= 0) & (m < 390)
            np.add.at(M[i], m[ok], g["volume"].to_numpy(float)[ok])
        _CUMV[sym] = ({d: i for i, d in enumerate(ds)}, np.cumsum(M, axis=1))
    return _CUMV[sym]


def _spy_filter(cache: str, d):
    """Per bar-start minute 570..959: +1 if SPY above VWAP and EMA9>EMA21 on completed 5-min bars, -1 if both below."""
    days = C._hist(cache, "SPY")[0]
    ds = sorted(days)
    i = ds.index(d)
    prior = [days[x] for x in ds[max(0, i - 2):i]]
    closes5, today_bucket = [], []
    for j, g in enumerate(prior + [days[d]]):
        m = _mins(g.index)
        b = m // 5 * 5
        s = pd.Series(g["close"].to_numpy(float)).groupby(b).last()
        closes5.extend(s.to_numpy())
        if j == len(prior):
            today_bucket = list(s.index)
    cs = pd.Series(closes5)
    e9 = cs.ewm(span=9, adjust=False).mean().to_numpy()[-len(today_bucket):]
    e21 = cs.ewm(span=21, adjust=False).mean().to_numpy()[-len(today_bucket):]
    emasig = dict(zip(today_bucket, np.sign(e9 - e21)))
    g = days[d]
    m = _mins(g.index)
    vw = F.vwap(g).to_numpy()
    cl = g["close"].to_numpy(float)
    out = np.zeros(390)
    spy_close = np.full(390, np.nan)
    for k, mm in enumerate(m):
        if not 570 <= mm < 960:
            continue
        lastb = mm // 5 * 5 if mm % 5 == 4 else mm // 5 * 5 - 5  # last completed 5-min bucket at this bar's close
        es = emasig.get(lastb, 0)
        vs = np.sign(cl[k] - vw[k])
        out[mm - 570] = es if es == vs else 0
        spy_close[mm - 570] = cl[k]
    spy_close = pd.Series(spy_close).ffill().to_numpy()
    return out, spy_close, float(g["open"].iloc[0])


def _beta(stock_daily: pd.DataFrame, spy_daily: pd.DataFrame) -> float:
    a = stock_daily["close"].iloc[-21:].pct_change().dropna()
    b = spy_daily["close"].pct_change().reindex(a.index).dropna()
    a = a.reindex(b.index)
    if len(a) < 15 or b.var() <= 0:
        return 1.0
    return float(np.cov(a, b)[0, 1] / b.var())


def _table(d, cache: str):
    if d in _TABLE:
        return _TABLE[d]
    if len(_TABLE) > 3:
        _TABLE.clear()
    spy = C.day("SPY", d, cache)
    mf, spyc, spyo = _spy_filter(cache, d)
    spy_ret = spyc / spyo - 1
    rows = {}
    for s in _U:
        if s in ("SPY",):
            continue
        dd = C.day(s, d, cache)
        if dd is None or dd.prev_close < 5 or not dd.atr > 0 or len(dd.daily) < 20:
            continue
        g = dd.bars
        m = _mins(g.index)
        sel = np.nonzero((m >= 599) & (m <= 689))[0]
        if not len(sel):
            continue
        cl_grid = pd.Series(np.nan, index=range(570, 960))
        cl_grid.loc[m[(m >= 570) & (m < 960)]] = g["close"].to_numpy(float)[(m >= 570) & (m < 960)]
        cl_grid = cl_grid.ffill().to_numpy()
        o = float(g["open"].iloc[0])
        idx_map, CV = _cumv(s, cache)
        i = idx_map[d]
        if i < 14:
            continue
        avgcv = CV[i - 14:i].mean(axis=0)
        cv_today = CV[i]
        vw = F.vwap(g).to_numpy()
        beta = _beta(dd.daily, spy.daily)
        closes = dd.daily["close"]
        sma20 = float(closes.iloc[-20:].mean())
        trend = np.sign(dd.prev_close - sma20)
        mm = m[sel]
        gi = mm - 570
        r_s = cl_grid[gi] / o - 1
        b30 = np.where(gi >= 30, cl_grid[np.maximum(gi - 30, 0)], o)      # 09:59 bar: last 30 min = since open
        m30 = np.where(gi >= 30, spyc[np.maximum(gi - 30, 0)], spyo)
        r_s30 = cl_grid[gi] / b30 - 1
        r_m30 = spyc[gi] / m30 - 1
        rows[s] = {"k": sel, "min": mm, "close": g["close"].to_numpy(float)[sel], "atr": dd.atr,
                   "thr": dd.atr / dd.prev_close, "trend": trend,
                   "rs_b20": r_s - beta * spy_ret[gi], "rs_b1": r_s - spy_ret[gi],
                   "rs30_b20": r_s30 - beta * r_m30, "rs30_b1": r_s30 - r_m30,
                   "vwap": np.sign(g["close"].to_numpy(float)[sel] - vw[sel]),
                   "rvol": np.where(avgcv[gi] > 0, cv_today[gi] / np.where(avgcv[gi] > 0, avgcv[gi], 1), 0.0),
                   "mf": mf[gi]}
    _TABLE[d] = rows
    return rows


def _picks(d, v, cache: str):
    key = (d, v["c"], v["win"], v["trend"], v["beta"])
    if key in _PICKS:
        return _PICKS[key]
    if len(_PICKS) > 200:
        _PICKS.clear()
    lo, hi = WINDOWS[v["win"]]
    cands = []  # (minute, -|rs|, sym, k, side, close, atr)
    for s, r in _table(d, cache).items():
        rs, rs30 = r["rs_" + v["beta"]], r["rs30_" + v["beta"]]
        for side in (1, -1):
            ok = ((r["min"] >= lo) & (r["min"] <= hi) & (r["mf"] == side) & (side * rs > v["c"] * r["thr"])
                  & (side * rs30 > 0) & (r["vwap"] == side) & (r["rvol"] > 1.2))
            if v["trend"]:
                ok &= r["trend"] == side
            j = np.nonzero(ok)[0]
            if len(j):
                j = int(j[0])
                cands.append((int(r["min"][j]), -abs(float(rs[j])), s, int(r["k"][j]), side, float(r["close"][j]), r["atr"]))
    cands.sort()
    out = {}
    for mn, _, s, k, side, c, atr in cands:
        if len(out) >= CAP:
            break
        if s not in out:
            out[s] = (k, side, c, atr)
    _PICKS[key] = out
    return out


def signals(day, v) -> list[Signal]:
    cache = _cache(day.date)
    p = _picks(day.date, v, cache).get(day.symbol)
    if p is None:
        return []
    k, side, c, atr = p
    if k + 1 >= len(day.bars):
        return []
    risk = 0.25 * atr
    sig = Signal(day.symbol, NAME, side, k, c - side * risk, c + side * risk if v["exit"] == "1R" else None)
    if v["exit"] in ("hold", "holdts"):
        sig.be_at_r = 1.0
    if v["exit"] == "holdts":
        sig.time_stop_min, sig.time_stop_min_r = 60, 0.3
    return [sig]


def _cache(d) -> str:
    """q2 dates live in data/cache_q2 (only the q2 split has dates <= 2026-06-30); everything else in data/cache."""
    return "data/cache_q2" if str(d) <= "2026-06-30" else "data/cache"
