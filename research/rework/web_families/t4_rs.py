"""t4_rs - rule-18 rework of research/reddit_bt/t4_rel_strength (relative strength vs SPY / sector ETF).

Educational only - not financial advice. A hypothesis under test, not evidence.

Same mechanics as the original (decision on a completed 1-min bar, market entry at the next bar open, one trade per
symbol per day, at most CAP trades per day ranked by |RS| within each minute, production costs) with every rework
knob exposed as a variant parameter:
  c        RS threshold in units of (daily ATR / prev close)                      base 0.5
  mf       market filter: both (SPY > VWAP and 5-min EMA9>EMA21) | vwap | ema | none | qqq (same on QQQ)
           | sector (same on the stock's sector ETF)                              base both
  rsmode   open30 (RS since open > thr and RS30 > 0) | open (no RS30 check) | r60 | r30 (RS over the last 60/30
           bars > thr)                                                              base open30
  bench    spy | sector (RS measured against the stock's sector ETF)              base spy
  beta     b20 | b1;  trend True/False (prev close vs SMA20 of daily closes)
  rvol     cumulative volume vs 14-session average at the same minute > rvol (0 = off)   base 1.2
  w0, w1   signal-bar start minutes (09:59 = 599 ... ); fills one minute later   base 629..689 (fills 10:30-11:30)
  stop     stop distance in daily ATR                                              base 0.25
  tgt      target in R                                                             base 1.0
  cap      max trades per day                                                      base 10
  side     both | long | short
  add      none | gap (gap in the trade direction) | or30 (close beyond the 09:30-09:59 range) | pdhl (close beyond
           the prior-day high/low)
  ema      (fast, slow) EMA lengths for the 5-min market filter                    base (9, 21)
  vwapc    require the stock on the trade side of its session VWAP                base True
Sector ETF of a stock = the SPDR sector ETF in top300 (XLK XLF XLE XLV XLI XLY XLP XLU XLB XLC; XLRE is not in
top300) whose 5-minute returns, after removing SPY, correlate most with the stock's over the warm-up month
2026-06-15..2026-07-14 (before train). Residual correlation < 0.10 -> SPY. ETFs map to SPY. No future data used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mcf import features as F
from mcf.strategies.base import Signal

from research.rework.web_families import lib as L

C = L.C
NAME = "t4_rs"
SECTORS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLC"]
ETFS = set(SECTORS) | {"SPY", "QQQ", "IWM", "DIA", "XLRE", "SMH", "GLD", "SLV", "TLT", "HYG", "EEM", "EFA", "ARKK",
                       "KRE", "XBI", "GDX", "USO", "UVXY", "SQQQ", "TQQQ", "SOXL", "SOXS", "IBIT", "XOP", "VXX"}
U = [s for s in L.ROOT_U if s != "SPY"]
CACHE = "data/cache"
WARMUP_END = "2026-07-15"
G0, G1 = 570, 960

BASE = {"c": 0.5, "mf": "both", "rsmode": "open30", "bench": "spy", "beta": "b20", "trend": True, "rvol": 1.2,
        "w0": 629, "w1": 689, "stop": 0.25, "tgt": 1.0, "cap": 10, "side": "both", "add": "none", "ema": (9, 21), "vwapc": True}
STEPS = {"c": [0.25, 0.375, 0.5, 0.625, 0.75, 1.0], "rvol": [0.0, 1.0, 1.2, 1.5, 2.0],
         "w0": [599, 614, 629, 644, 659], "w1": [659, 674, 689, 719, 749, 779],
         "stop": [0.2, 0.25, 0.3, 0.35], "tgt": [0.75, 1.0, 1.5, 2.0], "cap": [5, 10, 20]}


def _mins(idx) -> np.ndarray:
    return idx.hour.to_numpy() * 60 + idx.minute.to_numpy()


def _grid(g: pd.DataFrame, arr: np.ndarray) -> np.ndarray:
    m = _mins(g.index)
    ok = (m >= G0) & (m < G1)
    out = np.full(G1 - G0, np.nan)
    out[m[ok] - G0] = arr[ok]
    return pd.Series(out).ffill().to_numpy()


_SECTOR: dict = {}


def sector_map() -> dict:
    if _SECTOR:
        return _SECTOR

    def r5(sym):
        h = C._hist(CACHE, sym)
        if h is None:
            return None
        days = h[0]
        parts = []
        for d in sorted(days):
            if str(d) >= WARMUP_END:
                break
            g = days[d]
            s = g["close"].groupby(_mins(g.index) // 5).last()
            s.index = [f"{d}_{i}" for i in s.index]
            parts.append(np.log(s).diff().iloc[1:])
        return pd.concat(parts) if parts else None

    spy = r5("SPY")
    def resid(x):
        x, y = x.align(spy, join="inner")
        b = np.cov(x, y)[0, 1] / y.var()
        return x - b * y
    sec = {e: resid(r5(e)) for e in SECTORS}
    for s in U:
        if s in ETFS:
            _SECTOR[s] = "SPY"
            continue
        x = r5(s)
        if x is None or len(x) < 500:
            _SECTOR[s] = "SPY"
            continue
        rx = resid(x)
        best, bc = "SPY", 0.10
        for e, re in sec.items():
            a, b = rx.align(re, join="inner")
            cc = float(np.corrcoef(a, b)[0, 1]) if len(a) > 200 else 0
            if cc > bc:
                best, bc = e, cc
        _SECTOR[s] = best
    return _SECTOR


def _bench(sym: str, d, ema=(9, 21)):
    """Per grid minute: vwap side, 5-min EMA side (completed buckets, warmed by 2 prior sessions), close; and open."""
    days = C._hist(CACHE, sym)[0]
    ds = sorted(days)
    i = ds.index(d)
    prior = [days[x] for x in ds[max(0, i - 2):i]]
    closes5, today_bucket = [], []
    for j, g in enumerate(prior + [days[d]]):
        b = _mins(g.index) // 5 * 5
        s = pd.Series(g["close"].to_numpy(float)).groupby(b).last()
        closes5.extend(s.to_numpy())
        if j == len(prior):
            today_bucket = list(s.index)
    cs = pd.Series(closes5)
    ef = cs.ewm(span=ema[0], adjust=False).mean().to_numpy()[-len(today_bucket):]
    es_ = cs.ewm(span=ema[1], adjust=False).mean().to_numpy()[-len(today_bucket):]
    emasig = dict(zip(today_bucket, np.sign(ef - es_)))
    g = days[d]
    m = _mins(g.index)
    vw = F.vwap(g).to_numpy()
    cl = g["close"].to_numpy(float)
    vs, es = np.zeros(G1 - G0), np.zeros(G1 - G0)
    for k, mm in enumerate(m):
        if not G0 <= mm < G1:
            continue
        lastb = mm // 5 * 5 if mm % 5 == 4 else mm // 5 * 5 - 5
        es[mm - G0] = emasig.get(lastb, 0)
        vs[mm - G0] = np.sign(cl[k] - vw[k])
    return {"vs": vs, "es": es, "close": _grid(g, cl), "open": float(g["open"].iloc[0])}


def _beta(sd: pd.DataFrame, bd: pd.DataFrame) -> float:
    a = sd["close"].iloc[-21:].pct_change().dropna()
    b = bd["close"].pct_change().reindex(a.index).dropna()
    a = a.reindex(b.index)
    if len(a) < 15 or b.var() <= 0:
        return 1.0
    return float(np.cov(a, b)[0, 1] / b.var())


_CUMV: dict = {}


def _cumv(sym: str):
    if sym not in _CUMV:
        days = C._hist(CACHE, sym)[0]
        ds = sorted(days)
        M = np.zeros((len(ds), 390))
        for i, d in enumerate(ds):
            g = days[d]
            m = _mins(g.index) - 570
            ok = (m >= 0) & (m < 390)
            np.add.at(M[i], m[ok], g["volume"].to_numpy(float)[ok])
        _CUMV[sym] = ({d: i for i, d in enumerate(ds)}, np.cumsum(M, axis=1))
    return _CUMV[sym]


LO, HI = 599, 779    # widest signal window covered by the table
GI = np.arange(LO, HI + 1) - G0


def table(d, emas=((9, 21),)):
    """Variant-independent 2-D arrays (symbols x minutes LO..HI) for one session."""
    smap = sector_map()
    bench = {}
    for e in ["SPY", "QQQ"] + SECTORS:
        for em in emas:
            bench[(e, em)] = _bench(e, d, em)
    spy_dd = C.day("SPY", d, CACHE)
    bdaily = {e: C.day(e, d, CACHE).daily for e in ["SPY"] + SECTORS}
    syms, cols = [], {k: [] for k in ("k", "close", "vwap", "rvol", "gap", "or30", "pdhl",
                                       "rs_spy_b20", "rs_spy_b1", "rs_sector_b20", "rs_sector_b1",
                                       "r30_spy_b20", "r30_spy_b1", "r30_sector_b20", "r30_sector_b1",
                                       "r60_spy_b20", "r60_spy_b1", "r60_sector_b20", "r60_sector_b1")}
    meta = {"atr": [], "thr": [], "trend": [], "sector": []}
    for s in U:
        dd = C.day(s, d, CACHE)
        if dd is None or dd.prev_close < 5 or not dd.atr > 0 or len(dd.daily) < 20:
            continue
        idx_map, CV = _cumv(s)
        i = idx_map[d]
        if i < 14:
            continue
        g = dd.bars
        m = _mins(g.index)
        kk = np.full(G1 - G0, -1)
        ok = (m >= G0) & (m < G1)
        kk[m[ok] - G0] = np.nonzero(ok)[0]
        cl = _grid(g, g["close"].to_numpy(float))
        o = float(g["open"].iloc[0])
        vw = _grid(g, F.vwap(g).to_numpy())
        avgcv = CV[i - 14:i].mean(axis=0)
        orm = (m >= 570) & (m < 600)
        orh = g["high"].to_numpy(float)[orm].max() if orm.any() else np.nan
        orl = g["low"].to_numpy(float)[orm].min() if orm.any() else np.nan
        ph, pl = float(dd.daily["high"].iloc[-1]), float(dd.daily["low"].iloc[-1])
        sec = smap.get(s, "SPY")
        c_ = cl[GI]
        cols["k"].append(kk[GI])
        cols["close"].append(c_)
        cols["vwap"].append(np.sign(c_ - vw[GI]))
        cols["rvol"].append(np.where(avgcv[GI] > 0, CV[i][GI] / np.where(avgcv[GI] > 0, avgcv[GI], 1), 0.0))
        cols["gap"].append(np.full(len(GI), np.sign(o - dd.prev_close)))
        cols["or30"].append(np.where(c_ > orh, 1, np.where(c_ < orl, -1, 0)) * (GI >= 30))
        cols["pdhl"].append(np.where(c_ > ph, 1, np.where(c_ < pl, -1, 0)))
        for bn, bsym in (("spy", "SPY"), ("sector", sec)):
            B = bench[(bsym, emas[0])]
            bd = bdaily[bsym]
            beta = _beta(dd.daily, bd)
            rb = B["close"][GI] / B["open"] - 1
            rs_ = c_ / o - 1
            for L_ in (30, 60):
                base_s = np.where(GI >= L_, cl[np.maximum(GI - L_, 0)], o)
                base_b = np.where(GI >= L_, B["close"][np.maximum(GI - L_, 0)], B["open"])
                rsl, rbl = c_ / base_s - 1, B["close"][GI] / base_b - 1
                cols[f"r{L_}_{bn}_b20"].append(rsl - beta * rbl)
                cols[f"r{L_}_{bn}_b1"].append(rsl - rbl)
            cols[f"rs_{bn}_b20"].append(rs_ - beta * rb)
            cols[f"rs_{bn}_b1"].append(rs_ - rb)
        syms.append(s)
        meta["atr"].append(dd.atr)
        meta["thr"].append(dd.atr / dd.prev_close)
        meta["trend"].append(np.sign(dd.prev_close - float(dd.daily["close"].iloc[-20:].mean())))
        meta["sector"].append(sec)
    T = {k: np.vstack(v) for k, v in cols.items()}
    T.update({k: np.asarray(v) for k, v in meta.items()})
    T["syms"] = syms
    T["bench"] = {k: {"vs": b["vs"][GI], "es": b["es"][GI]} for k, b in bench.items()}
    T["mins"] = GI + G0
    return T


def _mf(T, v):
    mf, em = v["mf"], tuple(v["ema"])
    n = len(T["syms"])
    if mf == "none":
        return None
    if mf == "sector":
        rows = []
        for sec in T["sector"]:
            b = T["bench"][(sec, em)]
            rows.append(np.where(b["vs"] == b["es"], b["vs"], 0))
        return np.vstack(rows)
    b = T["bench"][("QQQ" if mf == "qqq" else "SPY", em)]
    a = {"both": np.where(b["vs"] == b["es"], b["vs"], 0), "vwap": b["vs"], "ema": b["es"]}[mf if mf != "qqq" else "both"]
    return np.broadcast_to(a, (n, len(a)))


def picks(T, v) -> list[tuple]:
    """[(symbol, bar_index, side, close, atr)] for one session, in the order the live runner would take them."""
    mins = T["mins"]
    win = (mins >= v["w0"]) & (mins <= v["w1"])
    bn, be = v["bench"], v["beta"]
    rs = T[f"rs_{bn}_{be}"]
    prim = {"open30": rs, "open": rs, "r60": T[f"r60_{bn}_{be}"], "r30": T[f"r30_{bn}_{be}"]}[v["rsmode"]]
    thr = v["c"] * T["thr"][:, None]
    mf = _mf(T, v)
    cands = []
    sides = {"both": (1, -1), "long": (1,), "short": (-1,)}[v["side"]]
    for side in sides:
        ok = win[None, :] & (T["k"] >= 0) & (side * prim > thr)
        if v.get("vwapc", True):
            ok &= T["vwap"] == side
        if v["rsmode"] == "open30":
            ok &= side * T[f"r30_{bn}_{be}"] > 0
        if mf is not None:
            ok &= mf == side
        if v["rvol"] > 0:
            ok &= T["rvol"] > v["rvol"]
        if v["trend"]:
            ok &= (T["trend"] == side)[:, None]
        if v["add"] != "none":
            ok &= T[v["add"]] == side
        anyok = ok.any(axis=1)
        first = ok.argmax(axis=1)
        for i in np.nonzero(anyok)[0]:
            j = first[i]
            cands.append((int(mins[j]), -abs(float(prim[i, j])), T["syms"][i], int(T["k"][i, j]), side,
                          float(T["close"][i, j]), float(T["atr"][i])))
    cands.sort()
    out, seen = [], set()
    for mn, _, s, k, side, c, atr in cands:
        if len(out) >= v["cap"]:
            break
        if s not in seen:
            seen.add(s)
            out.append((s, k, side, c, atr))
    return out


def signal(p, v) -> Signal:
    s, k, side, c, atr = p
    risk = v["stop"] * atr
    return Signal(s, NAME, side, k, c - side * risk, c + side * v["tgt"] * risk)


def run(variants: dict, split: str) -> dict:
    """date-major: one table per session, all variants evaluated on it."""
    emas = tuple(sorted({tuple(v["ema"]) for v in variants.values()}, key=lambda e: e != (9, 21)))
    rows = {k: [] for k in variants}
    lo, hi, cache = C._split(split)
    for d in C.sessions(split):
        T = table(d, emas)
        for name, v in variants.items():
            for p in picks(T, v):
                dd = C.day(p[0], d, cache)
                if p[1] + 1 >= len(dd.bars):
                    continue
                sig = signal(p, v)
                tr = C.sim(sig, dd)
                if tr is not None:
                    rows[name].append(L.row(sig, tr, dd))
    return {k: C.metrics(pd.DataFrame(r)) for k, r in rows.items()}


def mask_doc():
    return __doc__
