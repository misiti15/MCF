"""UPDAY bench for L3-gap-slope-fromopen-FD (Mechanic 2026-11-17): the Workbench RERUN engine (sim2.py, unchanged for
the parent / WB4) plus UP-STATE layers. Every layer is OFF by default, so PARENT and WB4 score exactly as in the RERUN.

Up state U (decided at the signal bar, only info known then; owner direction rule: post-09:50 anchors only):
  ust = ("spy950", x)  SPY up more than x % since the 09:50 close
        ("spy30",  x)  SPY up more than x % over the last 30 minutes
        ("both",   x)  SPY up more than x % since 09:50 AND rising over the last 30 minutes (> 0)
Layers that act only when U is true (the down / quiet side is untouched):
  up_skip     skip the signal
  up_w        size weight (R-weighted: the trade counts w x R; avg R is reported per unit of risk = sum(wR) / sum(w))
  up_gap      stricter gap (<= up_gap)          up_fo   stricter fromOpen (> up_fo)
  up_rs       relative strength since 09:50 (stock % since 09:50 close - SPY % since 09:50) must be < up_rs
  up_wend     entry window ends at up_wend (HHMM)      up_wstart  no U entries before up_wstart (HHMM)
  up_hold     max hold minutes                  up_tgt  target R            up_stop  stop R
  up_so       scale-out: half at +up_so R (limit), half rides the normal exit
Dynamic (acts on every trade or, with spyx_u, only on U trades):
  spyx        exit at the next 1-min open once SPY has risen more than spyx % since entry (target not yet hit)
  spyx_loss   ... only while the short is under water (last 1-min close above entry)
Educational only - not financial advice."""
import numpy as np, pandas as pd
import sim2
from sim2 import SEC, TAF, CAT, chain

UPDEF = dict(ust=None, up_skip=False, up_w=1.0, up_gap=None, up_fo=None, up_rs=None, up_wend=None, up_wstart=None, up_hold=None,
             up_tgt=None, up_stop=None, up_so=None, spyx=None, spyx_u=False, spyx_loss=False)
BASE = dict(sim2.BASE, **UPDEF)
WB4 = dict(BASE, w=(950, 1300), gap=-3.2, maxhold=75)


def spy_tables(s):
    """s: SPY 1-min OHLC (NY tz index). Returns (per-tod state table, {date: close array indexed by minute-570})."""
    s = s.assign(date=s.index.strftime("%Y-%m-%d"), mn=s.index.hour * 60 + s.index.minute)
    out, closes = [], {}
    for d, g in s.groupby("date"):
        g = g.set_index("mn")
        if 589 not in g.index:
            continue
        ref = g.close.loc[589]
        c = g.close.reindex(range(570, 960)).ffill().bfill()
        closes[d] = c.values
        prev30 = c.shift(30).fillna(c.iloc[0])          # bar t-30 (before 10:00: the 09:30 bar close)
        tods = [(m + 1) // 60 * 100 + (m + 1) % 60 for m in c.index]
        out.append(pd.DataFrame({"date": d, "tod": tods, "spy950": (c.values / ref - 1) * 100,
                                 "spy30": (c.values / prev30.values - 1) * 100}))
    return pd.concat(out, ignore_index=True), closes


def up_state(c, v):
    k = v["ust"]
    if k is None:
        return np.zeros(len(c), bool)
    kind, x = k
    if kind == "spy950":
        return (c.spy950 > x).values
    if kind == "spy30":
        return (c.spy30 > x).values
    if kind == "both":
        return ((c.spy950 > x) & (c.spy30 > 0)).values
    raise ValueError(kind)


def signals(c, v):
    U = up_state(c, v)
    m = ((c.gap <= v["gap"]) & (c.fromOpen > v["fo"]) & (c.sma20_slope_pct > v["slope"]) & (c.tod >= v["w"][0]) &
         (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"])).to_numpy(copy=True)
    if v["spy950"] is not None:
        m &= ~(c.spy950 > v["spy950"]).values
    if v["up_skip"]:
        m &= ~U
    if v["up_gap"] is not None:
        m &= ~(U & ~(c.gap <= v["up_gap"]).values)
    if v["up_fo"] is not None:
        m &= ~(U & ~(c.fromOpen > v["up_fo"]).values)
    if v["up_rs"] is not None:
        m &= ~(U & ~(c.rs950 < v["up_rs"]).values)
    if v["up_wend"] is not None:
        m &= ~(U & (c.tod > v["up_wend"]).values)
    if v["up_wstart"] is not None:
        m &= ~(U & (c.tod < v["up_wstart"]).values)
    h = c[m].assign(U=U[m]).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if not len(h):
        return h
    idx = chain(h.symbol.values, h.date.values, h.tod.values.astype(int), True, int(v["cd"]))
    return h.iloc[idx].reset_index(drop=True)


def walk(path, tod, e, R, v, up, dn, hold, spyc, spyx):
    loss = v.get("spyx_loss", False)
    mn, o, h, l, c = path
    t0 = (tod // 100) * 60 + tod % 100
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    if hold:
        flat = min(flat, t0 + hold)
    stop, tgt = e + dn * R, e - up * R
    j = np.searchsorted(mn, t0, side="left")
    s0 = spyc[t0 - 1 - 570] if (spyx is not None and spyc is not None and 570 <= t0 - 1 < 960) else None
    mfe = 0.0
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time", mfe
        if (s0 is not None and 571 <= mn[k] < 960 and (spyc[mn[k] - 1 - 570] / s0 - 1) * 100 > spyx
                and (not loss or (k > j and c[k - 1] > e))):
            return o[k], mn[k], "spyx", mfe
        if h[k] >= stop:
            return max(o[k], stop), mn[k], "stop", mfe
        if l[k] <= tgt - 0.01:
            return tgt, mn[k], "target", max(mfe, (e - tgt) / R)
        mfe = max(mfe, (e - l[k]) / R)
    k = len(mn) - 1
    return ((c[k], mn[k], "time", mfe) if k >= j else (e, t0, "time", 0.0))


def cost(e, px, kind):
    return e * (1e-4 + SEC) + TAF + 2 * CAT + (max(0.02, 4e-4 * px) if kind == "stop" else
                                                (max(0.01, 1e-4 * px) if kind in ("time", "spyx") else 0.0))


def trades(c, v, getpath, spyc):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        U = bool(r.U)
        R = v["rf"] * r.atr_d; e = r.close
        up = v["up_tgt"] if (U and v["up_tgt"] is not None) else v["up"]
        dn = v["up_stop"] if (U and v["up_stop"] is not None) else v["dn"]
        hold = v["up_hold"] if (U and v["up_hold"] is not None) else v["maxhold"]
        sx = v["spyx"] if (v["spyx"] is not None and (U or not v["spyx_u"])) else None
        sc = spyc.get(r.date)
        px, xm, kind, mfe = walk(p, int(r.tod), e, R, v, up, dn, hold, sc, sx)
        rr = ((e - px) - cost(e, px, kind)) / R
        rg = (e - px) / R
        if U and v["up_so"] is not None:      # half at +up_so R, half rides
            px2, xm2, k2, _ = walk(p, int(r.tod), e, R, v, v["up_so"], dn, hold, sc, sx)
            rr = 0.5 * rr + 0.5 * ((e - px2) - cost(e, px2, k2)) / R
            rg = 0.5 * rg + 0.5 * (e - px2) / R
            xm = max(xm, xm2)
        w = v["up_w"] if U else 1.0
        rows.append((r.symbol, r.date, int(r.tod), (int(r.tod) // 100) * 60 + int(r.tod) % 100, xm, kind, rg, rr * w, w, U,
                     mfe, r.spy950, r.spy30, r.rs950, r.gap, r.fromOpen))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "r_gross", "r", "w", "U", "mfe",
                                       "spy950", "spy30", "rs950", "gap", "fromOpen"])


def stats(t):
    """R-weighted stats: r already holds w x R; avg = sum(r) / sum(w) (= plain avg R when every w is 1)."""
    if not len(t):
        return dict(trades=0, win=np.nan, avg=np.nan, avg_wo_best=np.nan, total=0.0, worst_day=0.0, best_day=0.0,
                    best_share=np.nan, days=0)
    d = t.groupby("date").agg(s=("r", "sum"), w=("w", "sum"))
    b = d.s.idxmax()
    wo_w = t.w.sum() - d.loc[b, "w"]
    return dict(trades=len(t), win=(t.r > 0).mean(), avg=t.r.sum() / t.w.sum(),
                avg_wo_best=(t.r.sum() - d.loc[b, "s"]) / wo_w if wo_w else np.nan, total=t.r.sum(),
                worst_day=d.s.min(), best_day=d.s.max(), best_share=d.s.max() / t.r.sum() if t.r.sum() > 0 else np.nan,
                days=len(d))
