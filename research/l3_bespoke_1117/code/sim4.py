"""L3 bespoke bench 2026-11-17 (research/l3_bespoke_1117). The Workbench engine (sim.py / sim2.py, research/workbench/
L3-gap-slope-fromopen-FD/code) with: the setup's three conditions on 5-min lab-frame bars, refire chain, entry at the
signal-bar close, exits walked on 1-min bars (stop first; target fills only when traded through by >= $0.01; flat 15:55),
LR8 costs, Primary book (<= 30 open lots, <= 3 per symbol). Extras, all OFF by default (parent = sim2 parent):
  exits : up (target R, None = no target), dn (stop R), be_at/be_to (stop -> entry - be_to*R once MFE >= be_at; be_to < 0
          = stop above entry, i.e. reduced risk), ts_min/ts_r (exit at ts_min minutes if MFE < ts_r), maxhold,
          so_at/so_up/so_be (half off at +so_at R, the other half to so_up R, stop -> entry after so_at when so_be),
          trail_after/trail (once MFE >= trail_after: stop = best low + trail*R)
  filters: fomax, vwmax, vrmax, rsi5min, rpct (1R >= rpct % of price)
  book  : latch = number (-2.0), None, or a function f(row) -> limit (time / day-state dependent);
          the latch uses the day's running LOW of realized R after costs (latched = stays latched, as the runner
          since LL-LATCH 10-23); symcap; noreentry_after_stop.
Educational only - not financial advice."""
import math
import numpy as np, pandas as pd
import sim2
from sim2 import SEC, TAF, CAT, chain

P = dict(sim2.BASE)  # parent: gap/fo/slope/window/cd/up=1/dn=1/rf=.25/symcap 3/cap 30/latch -2/flat 1555/minpx 5
P.update(be_at=None, be_to=0.0, maxhold=None, ts_min=None, ts_r=None, so_at=None, so_up=None, so_be=False,
         trail_after=None, trail=None, fomax=None, vwmax=None, vrmax=None, rsi5min=None, rpct=None,
         noreentry_after_stop=False)


def signals(c, v):
    m = ((c.gap <= v["gap"]) & (c.fromOpen > v["fo"]) & (c.sma20_slope_pct > v["slope"]) & (c.tod >= v["w"][0]) &
         (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]))
    if v["fomax"] is not None: m &= c.fromOpen <= v["fomax"]
    if v["vwmax"] is not None: m &= c.vwapDistPct <= v["vwmax"]
    if v["vrmax"] is not None: m &= c.volumeRatio <= v["vrmax"]
    if v["rsi5min"] is not None: m &= c.rsi5 >= v["rsi5min"]
    if v["rpct"] is not None: m &= (v["rf"] * c.atr_d / c.close * 100 >= v["rpct"])
    h = c[m].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if not len(h):
        return h
    idx = chain(h.symbol.values, h.date.values, h.tod.values.astype(int), True, int(v["cd"]))
    return h.iloc[idx].reset_index(drop=True)


def walk(path, t0, e, R, v, up, dn, be_at=None, be_to=0.0):
    """short lot from minute t0 (entry at the close of the bar ending t0). Returns (px, exit_min, kind, mfe)."""
    mn, o, h, l, c = path
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    if v["maxhold"]:
        flat = min(flat, t0 + v["maxhold"])
    tsm = t0 + v["ts_min"] if v["ts_min"] else None
    stop = e + dn * R
    tgt = e - up * R if up is not None else None
    j = np.searchsorted(mn, t0, side="left")
    mfe, lo = 0.0, e
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time", mfe
        if tsm is not None and mn[k] >= tsm and mfe < v["ts_r"]:
            return o[k], mn[k], "time", mfe
        if h[k] >= stop:
            return max(o[k], stop), mn[k], ("stop" if stop > e + 1e-9 else "be"), mfe
        if tgt is not None and l[k] <= tgt - 0.01:
            return tgt, mn[k], "target", max(mfe, (e - tgt) / R)
        mfe = max(mfe, (e - l[k]) / R); lo = min(lo, l[k])
        if be_at is not None and mfe >= be_at:
            stop = min(stop, e - be_to * R)
        if v["trail_after"] is not None and mfe >= v["trail_after"]:
            stop = min(stop, lo + v["trail"] * R)
    k = len(mn) - 1
    return ((c[k], mn[k], "time", mfe) if k >= j else (e, t0, "time", 0.0))


def cost(e, px, kind):
    return e * (1e-4 + SEC) + TAF + 2 * CAT + (max(0.02, 4e-4 * px) if kind in ("stop", "be") else
                                                (max(0.01, 1e-4 * px) if kind == "time" else 0.0))


def one(path, t0, e, R, v):
    """R after costs, gross R, exit minute, kind, mfe for one entry under config v (handles the scale-out)."""
    if v["so_at"] is not None:
        px1, x1, k1, m1 = walk(path, t0, e, R, v, v["so_at"], v["dn"])
        px2, x2, k2, m2 = walk(path, t0, e, R, v, v["so_up"], v["dn"], be_at=(v["so_at"] if v["so_be"] else None), be_to=0.0)
        r = 0.5 * ((e - px1) - cost(e, px1, k1)) / R + 0.5 * ((e - px2) - cost(e, px2, k2)) / R
        g = 0.5 * (e - px1) / R + 0.5 * (e - px2) / R
        return r, g, max(x1, x2), k2 if k1 == "target" else k1, max(m1, m2)
    px, xm, kind, mfe = walk(path, t0, e, R, v, v["up"], v["dn"], v["be_at"], v["be_to"])
    return ((e - px) - cost(e, px, kind)) / R, (e - px) / R, xm, kind, mfe


def trades(c, v, getpath):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        R = v["rf"] * r.atr_d; e = r.close; tod = int(r.tod); t0 = (tod // 100) * 60 + tod % 100
        rr, g, xm, kind, mfe = one(p, t0, e, R, v)
        rows.append((r.symbol, r.date, tod, t0, xm, kind, g, rr, mfe, r.atr_d, e))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "r_gross", "r", "mfe", "atr_d", "e"])


def book(t, v, latch):
    """Primary book; latch: None = off, a number = fixed limit (e.g. -2.0), a callable f(date, em) -> limit or None."""
    if not len(t):
        return t
    t = t.sort_values(["date", "em", "symbol"]).reset_index(drop=True)
    keep = np.zeros(len(t), bool)
    for d, idx in t.groupby("date").indices.items():
        open_, real, low, stopped = [], 0.0, 0.0, {}
        for i in idx:
            em = t.em.values[i]; sym = t.symbol.values[i]
            still = []
            for (xm, s, r, k) in sorted(open_):
                if xm <= em:
                    real += r; low = min(low, real)
                    if k == "stop":
                        stopped[s] = min(stopped.get(s, 9999), xm)
                else:
                    still.append((xm, s, r, k))
            open_ = still
            lim = latch(d, em) if callable(latch) else latch
            if lim is not None and low <= lim + 1e-12:
                continue
            if len(open_) >= v["cap"] or sum(1 for o in open_ if o[1] == sym) >= v["symcap"]:
                continue
            if v.get("noreentry_after_stop") and sym in stopped:
                continue
            keep[i] = True; open_.append((t.xm.values[i], sym, t.r.values[i], t.kind.values[i]))
    return t[keep].reset_index(drop=True)


def stats(t, days):
    if not len(t):
        return dict(trades=0)
    d = t.groupby("date").r.sum().reindex(days, fill_value=0.0)
    tot = t.r.sum(); b = d.idxmax()
    n_wo = len(t) - (t.date == b).sum()
    w = t.r[t.r > 0]; l = t.r[t.r <= 0]
    return dict(trades=len(t), win=(t.r > 0).mean(), avg=t.r.mean(), total=tot,
                avg_wo_best=(tot - d[b]) / n_wo if n_wo else np.nan, total_wo_best=tot - d[b],
                best_day=d.max(), best_share=d.max() / tot if tot > 0 else np.nan, worst_day=d.min(),
                green_days=int((d > 0).sum()), traded_days=int((t.groupby("date").size() > 0).sum()),
                avg_win=w.mean(), avg_loss=l.mean(), wl=(w.mean() / -l.mean()) if len(l) and len(w) else np.nan,
                pf=(w.sum() / -l.sum()) if l.sum() < 0 else np.nan, hold=(t.xm - t.em).median())


def paired_t(a, b, days):
    da = a.groupby("date").r.sum().reindex(days, fill_value=0.0)
    db = b.groupby("date").r.sum().reindex(days, fill_value=0.0)
    x = (db - da).values
    if len(x) < 3 or x.std(ddof=1) == 0:
        return 0.0, float(x.sum())
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))), float(x.sum())


def random_entries(t, v, getpath, seed, w=(950, 1500)):
    """Move every taken trade's entry to a random 5-min bar close in the window on the same symbol-day; same exits."""
    rng = np.random.default_rng(seed)
    mins = np.arange((w[0] // 100) * 60 + w[0] % 100, (w[1] // 100) * 60 + w[1] % 100 + 1, 5)
    out = []
    for r in t.itertuples():
        p = getpath(r.symbol, r.date)
        mn, o, h, l, c = p
        for _ in range(20):
            t0 = int(rng.choice(mins)); k = np.searchsorted(mn, t0 - 1)
            if k < len(mn) and mn[k] == t0 - 1:
                break
        else:
            continue
        e = c[k]; R = v["rf"] * r.atr_d
        rr, g, xm, kind, mfe = one(p, t0, e, R, v)
        out.append((r.symbol, r.date, t0, xm, kind, rr))
    return pd.DataFrame(out, columns=["symbol", "date", "em", "xm", "kind", "r"])
