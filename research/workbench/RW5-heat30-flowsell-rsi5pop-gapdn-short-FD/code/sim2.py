"""Mechanic RW5 bench (2026-11-16), reusing the L3 workbench engine (research/workbench/L3-gap-slope-fromopen-FD/code/sim.py:
5-min signal-bar close entry, 1-min exit walk stop-first, target only when traded through by >= $0.01, flat 15:55, LR8 costs,
live book <= 30 lots / <= 3 per symbol / -2R latch). RW5 sensors: heat <= -30, buyPressure < -0.15, RSI(5) > 80, gap < 0,
window 09:50-15:00, refire off (first qualifying bar per symbol-day), ADV >= $95M (2-year only; replay names passed it live).
Experimental layers, all OFF by default so PARENT scores exactly the parent:
  spy950  : skip when SPY is up more than X % since the 09:50 close (signal-bar time)   [after-09:50 market-state gate]
  spyrng  : skip when SPY is above (1) its 09:30-09:50 high
  costr   : skip when the stop-exit round-trip cost (2 x (1c + 1 bp) + 2c) / 1R > X       [cost-to-R floor]
  rpct    : skip when 1R (0.25 x daily ATR) < X % of price
  vwmin/vwmax : require vwapDistPct >= / <= X (price vs VWAP at the signal bar)
  fomin/fomax : require fromOpen >= / <= X
  rsimax, heatmin, bpmax, gapmax : extra sensor bounds
  maxhold : time exit after N minutes;  be_at/be_to : breakeven / lock move;  dn/up : stop / target multiples
Educational only - not financial advice."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/home/user/MCF/research/bdi/gates1021/scripts")
from common import chain  # noqa: E402
from sim import SEC, TAF, CAT, book, stats, paired_t  # noqa: F401

BASE = dict(heat=-30.0, bp=-0.15, rsi5=80.0, gap=0.0, w=(950, 1500), refire=False, cd=1, adv=95e6, up=1.0, dn=1.0, rf=0.25,
            symcap=3, cap=30, latch=-2.0, flat=1555, minpx=5.0,
            spy950=None, spyrng=None, costr=None, rpct=None, vwmin=None, vwmax=None, fomin=None, fomax=None, rsimax=None,
            gapmax=None, gapmin=None, slopemax=None, maxhold=None, be_at=None, be_to=0.0, tgtc=False)


def spy_table(path):
    s = pd.read_parquet(path)
    s.index = pd.DatetimeIndex(s.index).tz_convert("America/New_York")
    s = s.assign(date=s.index.strftime("%Y-%m-%d"), mn=s.index.hour * 60 + s.index.minute)
    out = []
    for d, g in s.groupby("date"):
        g = g.set_index("mn")
        if 589 not in g.index:
            continue
        ref = g.close.loc[589]; hi = g.high.loc[570:589].max(); lo = g.low.loc[570:589].min()
        c = g.close.reindex(range(570, 960)).ffill()
        tods = [(m + 1) // 60 * 100 + (m + 1) % 60 for m in c.index]
        out.append(pd.DataFrame({"date": d, "tod": tods, "spy950": (c.values / ref - 1) * 100,
                                 "spyrng": np.where(c.values > hi, 1, np.where(c.values < lo, -1, 0))}))
    return pd.concat(out, ignore_index=True)


def costr(c, rf):
    R = rf * c.atr_d
    return (2 * (0.01 + 1e-4 * c.close) + 0.02) / R


def signals(c, v):
    m = ((c.heat <= v["heat"]) & (c.buyPressure < v["bp"]) & (c.rsi5 > v["rsi5"]) & (c.gap < v["gap"]) & (c.tod >= v["w"][0]) &
         (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]))
    if "adv20" in c and v["adv"]:
        m &= c.adv20 >= v["adv"]
    for k, col, op in (("spy950", "spy950", "le"), ("vwmin", "vwapDistPct", "ge"), ("vwmax", "vwapDistPct", "le"),
                       ("fomin", "fromOpen", "ge"), ("fomax", "fromOpen", "le"), ("rsimax", "rsi5", "le"),
                       ("gapmax", "gap", "le"), ("gapmin", "gap", "ge"), ("slopemax", "sma20_slope_pct", "le")):
        if v[k] is not None:
            m &= (c[col] <= v[k]) if op == "le" else (c[col] >= v[k])
    if v["spyrng"] is not None:
        m &= ~(c.spyrng >= v["spyrng"])
    if v["costr"] is not None:
        m &= costr(c, v["rf"]) <= v["costr"]
    if v["rpct"] is not None:
        m &= (v["rf"] * c.atr_d / c.close * 100 >= v["rpct"])
    h = c[m].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if not len(h):
        return h
    idx = chain(h.symbol.values, h.date.values, h.tod.values.astype(int), bool(v["refire"]), int(v["cd"]))
    return h.iloc[idx].reset_index(drop=True)


def walk(path, tod, e, R, v):
    mn, o, h, l, c = path
    t0 = (tod // 100) * 60 + tod % 100
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    if v["maxhold"]:
        flat = min(flat, t0 + v["maxhold"])
    stop, tgt = e + v["dn"] * R, e - v["up"] * R
    lim = tgt + 0.01 if v["tgtc"] else tgt
    trig = e - v["be_at"] * R if v["be_at"] else None
    j = np.searchsorted(mn, t0, side="left")
    mfe = 0.0
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time", mfe
        if h[k] >= stop:
            return max(o[k], stop), mn[k], ("stop" if stop > e else "be"), mfe
        if l[k] <= lim - 0.01:
            return lim, mn[k], "target", max(mfe, (e - lim) / R)
        mfe = max(mfe, (e - l[k]) / R)
        if trig is not None and l[k] <= trig:
            stop = min(stop, e - v["be_to"] * R)
    k = len(mn) - 1
    return ((c[k], mn[k], "time", mfe) if k >= j else (e, t0, "time", 0.0))


FEAT = ["gap", "fromOpen", "heat", "buyPressure", "rsi5", "rsi", "vwapDistPct", "sma20_slope_pct", "sma20_dist_pct", "atrPct",
        "upper_wick", "dist_hod_atr", "dist_lod_atr", "volumeRatio", "pricePosition", "flow3", "close", "atr_d", "spy950", "spyrng"]


def trades(c, v, getpath):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        R = v["rf"] * r.atr_d; e = r.close
        px, xm, kind, mfe = walk(p, int(r.tod), e, R, v)
        cost = e * (1e-4 + SEC) + TAF + 2 * CAT + (max(0.02, 4e-4 * px) if kind in ("stop", "be") else
                                                    (max(0.01, 1e-4 * px) if kind == "time" else 0.0))
        f = [getattr(r, k, np.nan) for k in FEAT]
        rows.append((r.symbol, r.date, int(r.tod), (int(r.tod) // 100) * 60 + int(r.tod) % 100, xm, kind, (e - px) / R,
                     ((e - px) - cost) / R, mfe, *f))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "r_gross", "r", "mfe"] + FEAT)
