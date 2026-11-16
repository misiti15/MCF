"""Mechanic RERUN L3 bench (2026-11-16): sim.py (first run, unchanged engine: 5-min signal-bar close entry, refire chain,
1-min exit walk stop-first, target only when traded through by >= $0.01, flat 15:55, LR8 costs, live book <= cap lots,
<= symcap per symbol, -2R latch) + optional experimental layers, all OFF by default so PARENT/WB3 score exactly as before:
  spy950  : skip when SPY is up more than X % since the 09:50 close (signal-bar time)   [up-day gate, measured after 09:50]
  spyrng  : skip when SPY is above (1) its 09:30-09:50 high                               [up-day gate, range position]
  rpct    : skip when 1R (0.25 x daily ATR) < X % of price                                [cost floor]
  fomax   : skip when fromOpen > X (chase / entry-drift guard)
  vwmax   : skip when price is more than X % above VWAP
  tgtc    : target limit 1 cent shallower (a touch of the 1R target fills)
  be_at/be_to : once the low reaches entry - be_at x R, stop moves to entry - be_to x R
  maxhold : time exit after N minutes (ts_r set: only if the best excursion so far is < ts_r R = runner time_stop_min_r)
Educational only - not financial advice."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/home/user/MCF/research/bdi/gates1021/scripts")
from common import chain  # noqa: E402
import sim
from sim import SEC, TAF, CAT, book, stats, paired_t  # noqa: F401

BASE = dict(sim.PARENT, spy950=None, spyrng=None, rpct=None, fomax=None, vwmax=None, tgtc=False, be_at=None, be_to=0.0,
            maxhold=None, ts_r=None)
WB3 = dict(BASE, w=(950, 1300), gap=-3.2)


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


def signals(c, v):
    m = ((c.gap <= v["gap"]) & (c.fromOpen > v["fo"]) & (c.sma20_slope_pct > v["slope"]) & (c.tod >= v["w"][0]) &
         (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]))
    if v["spy950"] is not None:
        m &= ~(c.spy950 > v["spy950"])
    if v["spyrng"] is not None:
        m &= ~(c.spyrng >= v["spyrng"])
    if v["rpct"] is not None:
        m &= (v["rf"] * c.atr_d / c.close * 100 >= v["rpct"])
    if v["fomax"] is not None:
        m &= c.fromOpen <= v["fomax"]
    if v["vwmax"] is not None:
        m &= c.vwapDistPct <= v["vwmax"]
    h = c[m].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if not len(h):
        return h
    idx = chain(h.symbol.values, h.date.values, h.tod.values.astype(int), True, int(v["cd"]))
    return h.iloc[idx].reset_index(drop=True)


def walk(path, tod, e, R, v):
    mn, o, h, l, c = path
    t0 = (tod // 100) * 60 + tod % 100
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    if v["maxhold"] and v["ts_r"] is None:
        flat = min(flat, t0 + v["maxhold"])
    tsm = t0 + v["maxhold"] if (v["maxhold"] and v["ts_r"] is not None) else None
    stop, tgt = e + v["dn"] * R, e - v["up"] * R
    lim = tgt + 0.01 if v["tgtc"] else tgt
    trig = e - v["be_at"] * R if v["be_at"] else None
    j = np.searchsorted(mn, t0, side="left")
    mfe = 0.0
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time", mfe
        if tsm is not None and mn[k] >= tsm and mfe < v["ts_r"]:
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


FEAT = ["gap", "fromOpen", "sma20_slope_pct", "vwapDistPct", "rsi5", "atrPct", "upper_wick", "dist_hod_atr", "volumeRatio",
        "sma20_dist_pct", "close", "atr_d", "spy950", "spyrng"]


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
