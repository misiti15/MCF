"""Mechanic ST7 bench (2026-11-16): one simulator for both tests (live-session replay 2026-10-12..11-10 and the 2-year
backtest 2024-10-01..2026-10-09, locked block 2024-11-01..2025-02-28 never read).
Engine (identical for the parent and every copy): signal = the module's conditions on 5-minute lab-frame bars (bar close
HHMM), first qualifying bar per symbol-day (refire false), ADV20 >= $95M, price >= $5. Fill = open of the 1-minute bar that
starts at the signal-bar close (live fills ~2 s after the close); stop / target from the signal-bar close (LabStrategy);
exits walked on 1-minute bars: stop first, target only when traded through by >= $0.01, flat 15:55. R = net P/L /
|fill - stop| (the live R). LR8 costs as the CWT14 bench (entry (1c + 1 bp) x time-of-day mult + 1 bp cushion; target at
the limit; stop (1c + 1 bp) + max(2c, 4 bp); time exit (1c + 1 bp) + max(1c, 1 bp); SEC, TAF, CAT). Then Primary's book:
<= 30 open lots per setup, -2R net per-setup latch (realised R after costs).
Optional layers (all OFF for the parent):
  w        entry window (bar close)          lvl/rsimax/fo/bp  P8-P11 thresholds
  rf       1R = rf x daily ATR               up/dn  target / stop in R (from the signal close)
  be_at/be_to  stop to fill + be_to R once the high reaches fill + be_at R
  maxhold  time exit after N min (ts_r: only if the best excursion is still < ts_r R)
  gapmax   skip when the open gap > X %      g1045: skip the 10:45 bar when gap > X % (the RSI gap artefact)
  spymin   skip when SPY since 09:50 < X %   spymax: skip when SPY since 09:50 > X %
  spyhi    skip when SPY is above its 09:30-09:50 high      spylo: skip when SPY is below its 09:30-09:50 low
  costr    skip when the stop round-trip cost > X of 1R      atrmin: skip when daily ATR < X % of price
  lodmax   skip when the close is more than X ATR above the session low (P10 depth)   vrmin: volumeRatio >= X
  cap      open lots per setup (book)       latch  per-setup daily latch (R)
Educational only - not financial advice."""
import math, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.gates import tod_cost_mult

PARENT = dict(w=(950, 1500), lvl=50.0, rsimax=30.0, fo=-1.0, bp=0.0, adv=95e6, minpx=5.0, rf=0.25, up=1.0, dn=1.0,
              be_at=None, be_to=0.0, maxhold=None, ts_r=None, flat=1555, gapmax=None, g1045=None, spymin=None, spymax=None,
              spyhi=None, spylo=None, costr=None, atrmin=None, lodmax=None, vrmin=None, cap=30, latch=-2.0, book=True)
SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005


def cost_entry(px, tod):
    return (0.01 + px * 1e-4) * tod_cost_mult([tod])[0] + px * 1e-4 + CAT


def cost_exit(px, why):
    base = 0.01 + px * 1e-4
    c = 0.0 if why == "target" else (base + max(0.02, 4e-4 * px) if why in ("stop", "be") else base + max(0.01, 1e-4 * px))
    return c + SEC * px + TAF + CAT


def signals(c, v):
    with np.errstate(invalid="ignore"):
        m = ((c.prsi >= v["lvl"]) & (c.rsi < v["lvl"]) & (c.rsi <= v["rsimax"]) & (c.fromOpen < v["fo"]) &
             (c.buyPressure > v["bp"]) & (c.adv20 >= v["adv"]) & (c.close >= v["minpx"]) & (c.tod >= v["w"][0]) &
             (c.tod <= v["w"][1]))
        if v["gapmax"] is not None: m &= c.gap <= v["gapmax"]
        if v["g1045"] is not None: m &= ~((c.tod == 1045) & (c.gap > v["g1045"]))
        if v["spymin"] is not None: m &= c.spy_d950 >= v["spymin"]
        if v["spymax"] is not None: m &= c.spy_d950 <= v["spymax"]
        if v["spyhi"] is not None: m &= ~(c.spy_rng >= 1)
        if v["spylo"] is not None: m &= ~(c.spy_rng <= -1)
        if v["costr"] is not None:
            R = v["rf"] * c.atr_d
            m &= (2 * (0.01 + c.close * 1e-4) + np.maximum(0.02, 4e-4 * c.close)) / (v["dn"] * R) <= v["costr"]
        if v["atrmin"] is not None: m &= c.atr_d / c.close * 100 >= v["atrmin"]
        if v["lodmax"] is not None: m &= c.dist_lod_atr <= v["lodmax"]
        if v["vrmin"] is not None: m &= c.volumeRatio >= v["vrmin"]
    h = c[m].sort_values(["symbol", "date", "tod"], kind="mergesort")
    return h.drop_duplicates(["symbol", "date"]).reset_index(drop=True)


def walk(path, tod, px, R, v):
    mn, o, h, l, c = path
    t0 = (tod // 100) * 60 + tod % 100
    i0 = np.searchsorted(mn, t0)
    if i0 >= len(mn) or mn[i0] > t0 + 4:
        return None
    fill = o[i0]
    stop, tgt = px - v["dn"] * R, px + v["up"] * R
    if fill <= stop:
        return fill, stop, fill, mn[i0], "stop", 0.0, 0.0
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    if v["maxhold"] and v["ts_r"] is None:
        flat = min(flat, t0 + v["maxhold"])
    tsm = t0 + v["maxhold"] if (v["maxhold"] and v["ts_r"] is not None) else None
    risk = fill - stop
    trig = fill + v["be_at"] * risk if v["be_at"] else None
    cur = stop; mfe = 0.0; mae = 0.0
    for k in range(i0, len(mn)):
        if mn[k] >= flat:
            return fill, stop, o[k], mn[k], "time", mfe, mae
        if tsm is not None and mn[k] >= tsm and mfe < v["ts_r"]:
            return fill, stop, o[k], mn[k], "time", mfe, mae
        if l[k] <= cur:
            ex = min(cur, o[k]) if k > i0 else cur
            return fill, stop, ex, mn[k], ("stop" if cur < fill else "be"), mfe, min(mae, (ex - fill) / risk)
        if h[k] >= tgt + 0.01:
            return fill, stop, tgt, mn[k], "target", max(mfe, (tgt - fill) / risk), mae
        mfe = max(mfe, (h[k] - fill) / risk); mae = min(mae, (l[k] - fill) / risk)
        if trig is not None and h[k] >= trig:
            cur = max(cur, fill + v["be_to"] * risk)
    k = len(mn) - 1
    return fill, stop, c[k], mn[k], "time", mfe, mae


FEAT = ["gap", "fromOpen", "rsi", "prsi", "buyPressure", "vwapDistPct", "atr_d", "close", "dist_lod_atr", "volumeRatio",
        "spy_d950", "spy_rng", "sma20_slope_pct", "rsi5"]


def trades(c, v, getpath):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        R = v["rf"] * r.atr_d
        w = walk(p, int(r.tod), r.close, R, v)
        if w is None:
            continue
        fill, stop, ex, xm, kind, mfe, mae = w
        risk = fill - stop
        net = ex - fill - cost_exit(ex, kind) - cost_entry(fill, int(r.tod))
        f = [getattr(r, k, np.nan) for k in FEAT]
        rows.append((r.symbol, r.date, int(r.tod), (int(r.tod) // 100) * 60 + int(r.tod) % 100, int(xm), kind, fill, stop,
                     ex, (ex - fill) / risk, net / risk, mfe, mae, (fill - r.close) / R, *f))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "fill", "stop", "exit", "r_gross", "r",
                                       "mfe", "mae", "drift"] + FEAT)


def book(t, v):
    if not len(t) or not v["book"]:
        return t
    t = t.sort_values(["date", "em", "symbol"]).reset_index(drop=True)
    keep = np.zeros(len(t), bool)
    for _, idx in t.groupby("date").indices.items():
        open_, real = [], 0.0
        for i in idx:
            em = t.em.values[i]
            still = []
            for (xm, r) in open_:
                if xm <= em: real += r
                else: still.append((xm, r))
            open_ = still
            if real <= v["latch"] + 1e-12 or len(open_) >= v["cap"]:
                continue
            keep[i] = True; open_.append((t.xm.values[i], t.r.values[i]))
    return t[keep].reset_index(drop=True)


def stats(t):
    if not len(t):
        return dict(trades=0, win=np.nan, avg=np.nan, avg_wo_best=np.nan, total=0.0, worst_day=0.0, best_day=0.0,
                    best_share=np.nan, days=0)
    d = t.groupby("date").r.agg(["sum", "size"])
    b = d["sum"].idxmax(); n_wo = len(t) - d.loc[b, "size"]
    return dict(trades=len(t), win=(t.r > 0).mean(), avg=t.r.mean(),
                avg_wo_best=(t.r.sum() - d.loc[b, "sum"]) / n_wo if n_wo else np.nan, total=t.r.sum(),
                worst_day=d["sum"].min(), best_day=d["sum"].max(),
                best_share=d["sum"].max() / t.r.sum() if t.r.sum() > 0 else np.nan, days=len(d))


def paired_t(a, b, days):
    da = a.groupby("date").r.sum().reindex(days, fill_value=0.0)
    db = b.groupby("date").r.sum().reindex(days, fill_value=0.0)
    x = (db - da).values
    if len(x) < 3 or x.std(ddof=1) == 0:
        return 0.0, float(x.sum())
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))), float(x.sum())
