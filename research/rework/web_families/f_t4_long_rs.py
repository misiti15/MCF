"""f_t4_long_rs - finalist module from the rule-18 rework of t4_rel_strength (key web_families).

Educational only - not financial advice. A hypothesis that passed train/valid gates, not evidence; the lead scores
it once on the locked holdouts.

Standalone (depends only on research/reddit_bt/common.py, whose split lock applies) so the backlog runner and the
lead can score it with  common.run(signals, VARIANTS[name], split, universe=top300).  The same logic as
research/rework/web_families/t4_rs.py restricted to the knobs the finalists use:

Decision on a completed 1-minute bar whose start minute is in [w0, w1] (629..689 -> fills 10:30-11:30); market entry
at the next 1-min open. LONG ONLY.
  RS     stock return since the 09:30 open minus beta20 x SPY return since the open > c x (daily ATR / prev close),
         and the same over the last 30 bars > 0
  stock  close > session VWAP; cumulative volume > rvol x the 14-session average at the same minute;
         prev close > SMA20 of daily closes
  market mf = "none" (no market filter) | "ema" (SPY 5-min EMA9 > EMA21 on completed bars, warmed with 2 prior
         sessions) | "vwap" (SPY close > SPY session VWAP)
  ranking one trade per symbol per day; at most `cap` per day; within a minute ranked by RS
  exit   stop `stop` x daily ATR below the signal close, target `tgt` R, else flat 15:55
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from mcf import features as F
from mcf.strategies.base import Signal

from research.reddit_bt import common as C

NAME = "f_t4_long_rs"
UNIVERSE = "top300"
_U = [s for s in (Path(__file__).resolve().parents[2] / "reddit_bt" / "top300.txt").read_text().split() if s and s != "SPY"]
BASE = {"c": 0.5, "mf": "none", "rvol": 1.2, "w0": 629, "w1": 689, "stop": 0.25, "tgt": 1.0, "cap": 10}
VARIANTS = {
    "long_nomf": dict(BASE),
    "long_emamf": dict(BASE, mf="ema"),
}
STEPS = {"c": [0.375, 0.5, 0.625], "rvol": [1.0, 1.2, 1.5], "w0": [614, 629, 644], "w1": [674, 689, 719],
         "stop": [0.2, 0.25, 0.3], "tgt": [0.75, 1.0, 1.5], "cap": [5, 10, 20]}
for _f in list(VARIANTS):
    for _k, _st in STEPS.items():
        for _x in _st:
            if _x != BASE[_k]:
                VARIANTS[f"{_f}__{_k}{_x}"] = dict(VARIANTS[_f], **{_k: _x})
NEIGHBORS = {f: [k for k in VARIANTS if k.startswith(f + "__")] for f in ("long_nomf", "long_emamf")}
FINALISTS = ["long_nomf", "long_emamf"]
BASELINE = {"stop_atr": 0.25, "target_atr": 0.25}


def _cache(d) -> str:
    return "data/cache_q2" if str(d) <= "2026-06-30" else "data/cache"


def _mins(idx) -> np.ndarray:
    return idx.hour.to_numpy() * 60 + idx.minute.to_numpy()


def _grid(g, arr):
    m = _mins(g.index)
    ok = (m >= 570) & (m < 960)
    out = np.full(390, np.nan)
    out[m[ok] - 570] = arr[ok]
    return pd.Series(out).ffill().to_numpy()


def _spy(cache, d):
    days = C._hist(cache, "SPY")[0]
    ds = sorted(days)
    i = ds.index(d)
    prior = [days[x] for x in ds[max(0, i - 2):i]]
    closes5, tb = [], []
    for j, g in enumerate(prior + [days[d]]):
        s = pd.Series(g["close"].to_numpy(float)).groupby(_mins(g.index) // 5 * 5).last()
        closes5.extend(s.to_numpy())
        if j == len(prior):
            tb = list(s.index)
    cs = pd.Series(closes5)
    e9 = cs.ewm(span=9, adjust=False).mean().to_numpy()[-len(tb):]
    e21 = cs.ewm(span=21, adjust=False).mean().to_numpy()[-len(tb):]
    emasig = dict(zip(tb, np.sign(e9 - e21)))
    g = days[d]
    m = _mins(g.index)
    vw = F.vwap(g).to_numpy()
    cl = g["close"].to_numpy(float)
    vs, es = np.zeros(390), np.zeros(390)
    for k, mm in enumerate(m):
        if 570 <= mm < 960:
            lastb = mm // 5 * 5 if mm % 5 == 4 else mm // 5 * 5 - 5
            es[mm - 570] = emasig.get(lastb, 0)
            vs[mm - 570] = np.sign(cl[k] - vw[k])
    return vs, es, _grid(g, cl), float(g["open"].iloc[0])


_T: dict = {}
_CV: dict = {}


def _table(d):
    if d in _T:
        return _T[d]
    _T.clear()
    cache = _cache(d)
    vs, es, spyc, spyo = _spy(cache, d)
    spy_daily = C.day("SPY", d, cache).daily
    GI = np.arange(599, 780) - 570
    rows = {}
    for s in _U:
        dd = C.day(s, d, cache)
        if dd is None or dd.prev_close < 5 or not dd.atr > 0 or len(dd.daily) < 20:
            continue
        key = (cache, s)
        if key not in _CV:
            days = C._hist(cache, s)[0]
            ds = sorted(days)
            M = np.zeros((len(ds), 390))
            for i, x in enumerate(ds):
                g = days[x]
                m = _mins(g.index) - 570
                ok = (m >= 0) & (m < 390)
                np.add.at(M[i], m[ok], g["volume"].to_numpy(float)[ok])
            _CV[key] = ({x: i for i, x in enumerate(ds)}, np.cumsum(M, axis=1))
        im, CV = _CV[key]
        i = im[d]
        if i < 14:
            continue
        g = dd.bars
        m = _mins(g.index)
        kk = np.full(390, -1)
        ok = (m >= 570) & (m < 960)
        kk[m[ok] - 570] = np.nonzero(ok)[0]
        cl = _grid(g, g["close"].to_numpy(float))
        o = float(g["open"].iloc[0])
        vw = _grid(g, F.vwap(g).to_numpy())
        a = dd.daily["close"].iloc[-21:].pct_change().dropna()
        b = spy_daily["close"].pct_change().reindex(a.index).dropna()
        a = a.reindex(b.index)
        beta = 1.0 if len(a) < 15 or b.var() <= 0 else float(np.cov(a, b)[0, 1] / b.var())
        avg = CV[i - 14:i].mean(axis=0)
        c_ = cl[GI]
        b30s = np.where(GI >= 30, cl[np.maximum(GI - 30, 0)], o)
        b30m = np.where(GI >= 30, spyc[np.maximum(GI - 30, 0)], spyo)
        rows[s] = {"k": kk[GI], "close": c_, "atr": dd.atr, "thr": dd.atr / dd.prev_close,
                   "trend": np.sign(dd.prev_close - float(dd.daily["close"].iloc[-20:].mean())),
                   "rs": (c_ / o - 1) - beta * (spyc[GI] / spyo - 1),
                   "rs30": (c_ / b30s - 1) - beta * (spyc[GI] / b30m - 1),
                   "vwap": np.sign(c_ - vw[GI]),
                   "rvol": np.where(avg[GI] > 0, CV[i][GI] / np.where(avg[GI] > 0, avg[GI], 1), 0.0)}
    _T[d] = (rows, GI + 570, vs[GI], es[GI])
    return _T[d]


_P: dict = {}


def picks(d, v) -> dict:
    key = (d, tuple(sorted(v.items())))
    if key in _P:
        return _P[key]
    if len(_P) > 500:
        _P.clear()
    rows, mins, vs, es = _table(d)
    mf = {"none": np.ones(len(mins)), "ema": es, "vwap": vs}[v["mf"]]
    win = (mins >= v["w0"]) & (mins <= v["w1"]) & (mf == 1)
    cands = []
    for s, r in rows.items():
        if r["trend"] != 1:
            continue
        ok = win & (r["k"] >= 0) & (r["rs"] > v["c"] * r["thr"]) & (r["rs30"] > 0) & (r["vwap"] == 1) & (r["rvol"] > v["rvol"])
        j = np.nonzero(ok)[0]
        if len(j):
            j = int(j[0])
            cands.append((int(mins[j]), -abs(float(r["rs"][j])), s, int(r["k"][j]), float(r["close"][j]), r["atr"]))
    cands.sort()
    out = {}
    for mn, _, s, k, c, atr in cands:
        if len(out) >= v["cap"]:
            break
        out.setdefault(s, (k, c, atr))
    _P[key] = out
    return out


def signals(day, v) -> list[Signal]:
    p = picks(day.date, v).get(day.symbol)
    if p is None:
        return []
    k, c, atr = p
    if k + 1 >= len(day.bars):
        return []
    risk = v["stop"] * atr
    return [Signal(day.symbol, NAME, 1, k, c - risk, c + v["tgt"] * risk)]
