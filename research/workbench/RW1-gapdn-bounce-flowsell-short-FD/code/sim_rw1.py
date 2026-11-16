"""Mechanic RW1-FD bench (2026-11-16), copied from research/workbench/RW3-gapdn-rsi5pop-flowsell-short-FD/code/sim_rw3.py. Same engine as the L3 Workbench bench (research/workbench/L3-gap-slope-fromopen-FD/code/
sim.py + sim2.py): signals on 5-min lab-frame bars (bar close HHMM), entry at the signal-bar close, exits walked on 1-min bars
(stop first; target only when traded through by >= $0.01; flat 15:55), LR8 production costs, live book (<= cap open lots per
setup, <= symcap per symbol, -2R net latch). RW1-FD specifics: conditions heat <= -20, buyPressure < -0.35, 55 <= RSI(14) <= 65,
gap < 0; refire false (first qualifying bar per symbol-day); account universe daily ATR >= 1% of price; price >= $5.
Optional experimental layers, all OFF in BASE (so the PARENT scores as the live rule):
  gapmax  : gap <= X % (deeper gap only)            rpct   : 1R (0.25 x daily ATR) >= X % of price
  spy950  : skip when SPY is up more than X % since the 09:50 close    spydn : skip when SPY is down more than X % since 09:50
  vwmax   : price <= X % above VWAP                 vwmin  : price >= X % above VWAP (pop must reach VWAP-ish)
  fomax   : fromOpen <= X                           fomin  : fromOpen >= X
  be_at/be_to : once the low reaches entry - be_at x R, stop moves to entry - be_to x R
  cf      : Testing-account cost filter (live.max_stop_cost_r), computed at the signal-bar close
  minadv  : 20-day $ volume >= X (replay: adv20 of the last 2-year daily row <= the session, 11-04 for later sessions)
  maxhold : time exit N minutes after entry (ts_r set: only if best excursion so far < ts_r R, runner time_stop_min_r)
Educational only - not financial advice."""
import sys, math
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/bdi/gates1021/scripts")
from common import chain  # noqa: E402

SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
BASE = dict(heat=-20.0, bp=-0.35, rsilo=55.0, rsihi=65.0, rsi5min=None, rsi5max=None, rsidelta=None, slopemax=None, gap=0.0, w=(950, 1500), refire=False, cd=1, up=1.0, dn=1.0, rf=0.25, symcap=3,
            cap=150, latch=-99.0, flat=1555, minpx=5.0, minatr=1.0, gapmax=None, rpct=None, spy950=None, spydn=None,
            vwmax=None, vwmin=None, fomax=None, fomin=None, be_at=None, be_to=0.0, maxhold=None, ts_r=None, minadv=None, cf=0.15)


def spy_table(path):
    s = pd.read_parquet(path)
    s.index = pd.DatetimeIndex(pd.to_datetime(s.index, utc=True)).tz_convert("America/New_York")
    s = s.assign(date=s.index.strftime("%Y-%m-%d"), mn=s.index.hour * 60 + s.index.minute)
    out = []
    for d, g in s.groupby("date"):
        g = g[~g.mn.duplicated()].set_index("mn")
        if 589 not in g.index:
            continue
        ref = g.close.loc[589]
        c = g.close.reindex(range(570, 960)).ffill()
        tods = [(m + 1) // 60 * 100 + (m + 1) % 60 for m in c.index]
        out.append(pd.DataFrame({"date": d, "tod": tods, "spy950": (c.values / ref - 1) * 100}))
    return pd.concat(out, ignore_index=True)


def signals(c, v):
    m = ((c.heat <= v["heat"]) & (c.buyPressure < v["bp"]) & (c.rsi >= v["rsilo"]) & (c.rsi <= v["rsihi"]) & (c.gap < v["gap"]) &
         (c.tod >= v["w"][0]) & (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]) &
         (c.atr_d / c.close * 100 >= v["minatr"]))
    if v["cf"] is not None:   # Testing-account cost filter CF (runner max_stop_cost_r): (2 x (1c + 1 bp) + 2c) / 1R <= cf
        m &= (2 * (0.01 + c.close * 1e-4) + 0.02) / (v["rf"] * c.atr_d) <= v["cf"]
    if v["minadv"] is not None:
        m &= c.adv20 >= v["minadv"]
    if v["gapmax"] is not None:
        m &= c.gap <= v["gapmax"]
    if v["rpct"] is not None:
        m &= (v["rf"] * c.atr_d / c.close * 100 >= v["rpct"])
    if v["spy950"] is not None:
        m &= ~(c.spy950 > v["spy950"])
    if v["spydn"] is not None:
        m &= ~(c.spy950 < -v["spydn"])
    if v["vwmax"] is not None:
        m &= c.vwapDistPct <= v["vwmax"]
    if v["vwmin"] is not None:
        m &= c.vwapDistPct >= v["vwmin"]
    if v["fomax"] is not None:
        m &= c.fromOpen <= v["fomax"]
    if v["fomin"] is not None:
        m &= c.fromOpen >= v["fomin"]
    if v["rsi5min"] is not None:
        m &= c.rsi5 >= v["rsi5min"]
    if v["rsi5max"] is not None:
        m &= c.rsi5 <= v["rsi5max"]
    if v["slopemax"] is not None:
        m &= c.sma20_slope_pct <= v["slopemax"]
    h = c[m].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if not len(h):
        return h
    if not v["refire"]:
        return h.drop_duplicates(["symbol", "date"]).reset_index(drop=True)
    idx = chain(h.symbol.values, h.date.values, h.tod.values.astype(int), True, int(v["cd"]))
    return h.iloc[idx].reset_index(drop=True)


def walk(path, tod, e, R, v):
    """short lot. path = (minute-of-day array, o, h, l, c). Returns (exit_px, exit_min, kind, mfe, mae)."""
    mn, o, h, l, c = path
    t0 = (tod // 100) * 60 + tod % 100
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    if v["maxhold"] and v["ts_r"] is None:
        flat = min(flat, t0 + v["maxhold"])
    tsm = t0 + v["maxhold"] if (v["maxhold"] and v["ts_r"] is not None) else None
    stop, tgt = e + v["dn"] * R, e - v["up"] * R
    trig = e - v["be_at"] * R if v["be_at"] else None
    j = np.searchsorted(mn, t0, side="left")
    mfe = mae = 0.0
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time", mfe, mae
        if tsm is not None and mn[k] >= tsm and mfe < v["ts_r"]:
            return o[k], mn[k], "time", mfe, mae
        if h[k] >= stop:
            return max(o[k], stop), mn[k], ("stop" if stop > e else "be"), mfe, min(mae, (e - h[k]) / R)
        if l[k] <= tgt - 0.01:
            return tgt, mn[k], "target", max(mfe, (e - tgt) / R), mae
        mfe = max(mfe, (e - l[k]) / R); mae = min(mae, (e - h[k]) / R)
        if trig is not None and l[k] <= trig:
            stop = min(stop, e - v["be_to"] * R)
    k = len(mn) - 1
    return ((c[k], mn[k], "time", mfe, mae) if k >= j else (e, t0, "time", 0.0, 0.0))


FEAT = ["gap", "heat", "buyPressure", "rsi5", "rsi", "fromOpen", "vwapDistPct", "atrPct", "upper_wick", "dist_hod_atr",
        "dist_lod_atr", "dist_pdl_atr", "volumeRatio", "sma20_dist_pct", "sma20_slope_pct", "flow3", "pricePosition", "close",
        "atr_d", "spy950"]


def trades(c, v, getpath):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        R = v["rf"] * r.atr_d; e = r.close
        px, xm, kind, mfe, mae = walk(p, int(r.tod), e, R, v)
        cost = e * (1e-4 + SEC) + TAF + 2 * CAT + (max(0.02, 4e-4 * px) if kind in ("stop", "be") else
                                                    (max(0.01, 1e-4 * px) if kind == "time" else 0.0))
        f = [getattr(r, k, np.nan) for k in FEAT]
        rows.append((r.symbol, r.date, int(r.tod), (int(r.tod) // 100) * 60 + int(r.tod) % 100, xm, kind, (e - px) / R,
                     ((e - px) - cost) / R, mfe, mae, *f))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "r_gross", "r", "mfe", "mae"] + FEAT)


def book(t, v):
    if not len(t):
        return t
    t = t.sort_values(["date", "em", "symbol"]).reset_index(drop=True)
    keep = np.zeros(len(t), bool)
    for _, idx in t.groupby("date").indices.items():
        open_, real = [], 0.0
        for i in idx:
            em = t.em.values[i]
            still = []
            for (xm, s, r) in open_:
                if xm <= em:
                    real += r
                else:
                    still.append((xm, s, r))
            open_ = still
            if real <= v["latch"] + 1e-12 or len(open_) >= v["cap"] or sum(1 for o in open_ if o[1] == t.symbol.values[i]) >= v["symcap"]:
                continue
            keep[i] = True; open_.append((t.xm.values[i], t.symbol.values[i], t.r.values[i]))
    return t[keep].reset_index(drop=True)


def stats(t):
    if not len(t):
        return dict(trades=0, win=np.nan, avg=np.nan, avg_wo_best=np.nan, total=0.0, worst_day=0.0, best_day=0.0, best_share=np.nan, days=0)
    d = t.groupby("date").r.agg(["sum", "size"])
    b = d["sum"].idxmax()
    n_wo = len(t) - d.loc[b, "size"]
    return dict(trades=len(t), win=(t.r > 0).mean(), avg=t.r.mean(),
                avg_wo_best=(t.r.sum() - d.loc[b, "sum"]) / n_wo if n_wo else np.nan, total=t.r.sum(),
                worst_day=d["sum"].min(), best_day=d["sum"].max(), best_share=d["sum"].max() / t.r.sum() if t.r.sum() > 0 else np.nan,
                days=len(d))


def paired_t(a, b, days):
    da = a.groupby("date").r.sum().reindex(days, fill_value=0.0)
    db = b.groupby("date").r.sum().reindex(days, fill_value=0.0)
    x = (db - da).values
    if len(x) < 3 or x.std(ddof=1) == 0:
        return 0.0, float(x.sum())
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))), float(x.sum())
