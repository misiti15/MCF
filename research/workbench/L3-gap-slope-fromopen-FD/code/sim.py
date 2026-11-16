"""Mechanic L3 bench: one simulator for both tests (live-session replay and 2-year lab). Signals from the setup's three
conditions on 5-min lab-frame bars (bar close HHMM), refire chain (LabStrategy), entry at the signal-bar close, exits walked
on 1-minute bars (stop first; target only when traded through by >= $0.01, as UGP 10-26 showed a touch does not fill;
flat 15:55), LR8 production costs, then the live book: <= cap open lots per setup, <= symcap per symbol, -2R net latch.
Educational only - not financial advice."""
import sys, math
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/bdi/gates1021/scripts")
from common import chain  # noqa: E402

PARENT = dict(gap=-2.6573517322540283, fo=3.460294628143309, slope=0.37244729995727527, w=(950, 1500), cd=1,
              up=1.0, dn=1.0, rf=0.25, symcap=3, cap=30, latch=-2.0, flat=1555, minpx=5.0)
SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005


def signals(c, v):
    m = ((c.gap <= v["gap"]) & (c.fromOpen > v["fo"]) & (c.sma20_slope_pct > v["slope"]) & (c.tod >= v["w"][0]) &
         (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]))
    h = c[m].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if not len(h):
        return h
    idx = chain(h.symbol.values, h.date.values, h.tod.values.astype(int), True, int(v["cd"]))
    return h.iloc[idx].reset_index(drop=True)


def walk(path, tod, e, R, v):
    """short lot. path = (minute-of-day array, o, h, l, c) of the session. Returns (exit_px, exit_min, kind)."""
    mn, o, h, l, c = path
    t0 = (tod // 100) * 60 + tod % 100
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    stop, tgt = e + v["dn"] * R, e - v["up"] * R
    j = np.searchsorted(mn, t0, side="left")
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time"
        if h[k] >= stop:
            return max(o[k], stop), mn[k], "stop"
        if l[k] <= tgt - 0.01:
            return tgt, mn[k], "target"
    k = len(mn) - 1
    return (c[k], mn[k], "time") if k >= j else (e, t0, "time")


def trades(c, v, getpath):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        R = v["rf"] * r.atr_d; e = r.close
        px, xm, kind = walk(p, int(r.tod), e, R, v)
        cost = e * (1e-4 + SEC) + TAF + 2 * CAT + (max(0.02, 4e-4 * px) if kind == "stop" else (max(0.01, 1e-4 * px) if kind == "time" else 0.0))
        rows.append((r.symbol, r.date, int(r.tod), (int(r.tod) // 100) * 60 + int(r.tod) % 100, xm, kind, (e - px) / R, ((e - px) - cost) / R))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "r_gross", "r"])


def book(t, v):
    """apply the live per-setup book day by day; returns the taken trades."""
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


def stats(t, days=None):
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
    """day-paired t of (b - a) day R over the given days (0 for no trades)."""
    da = a.groupby("date").r.sum().reindex(days, fill_value=0.0)
    db = b.groupby("date").r.sum().reindex(days, fill_value=0.0)
    x = (db - da).values
    if len(x) < 3 or x.std(ddof=1) == 0:
        return 0.0, float(x.sum())
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))), float(x.sum())
