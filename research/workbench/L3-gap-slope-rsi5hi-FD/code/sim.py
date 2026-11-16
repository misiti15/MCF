"""Mechanic bench for L3-gap-slope-rsi5hi-FD (2026-11-16), reusing the L3-gap-slope-fromopen-FD harness (sim.py/sim2.py):
signals from the setup's three conditions (gap <= g, SMA20 slope > s, RSI(5) > r) on 5-min lab-frame bars (bar close HHMM),
refire chain (LabStrategy refire_select, cooldown 6 bars), entry at the signal-bar close, exits walked on 1-min bars (stop
first; target only when traded through by >= $0.01; flat 15:55), LR8 costs, the account's cost filter (stop-exit cost <= 0.15R),
then the On Deck (Testing 1) book: <= 150 open lots per setup, <= 3 lots per symbol, no per-setup latch.
Experimental layers (all OFF by default -> PARENT scores the setup as configured):
  spy950 : skip when SPY is up more than X % since the 09:50 close (state measured after 09:50, owner rule)
  spydn  : skip when SPY is DOWN more than X % since the 09:50 close
  rpct   : skip when 1R (0.25 x daily ATR) < X % of price;  rpmax: skip when 1R > X % of price
  vwmax  : skip when price is more than X % above VWAP;   vwmin: skip when price is less than X % above VWAP
  fomax  : skip when fromOpen > X;  fomin: skip when fromOpen < X
  gapmin : skip when gap < X (very deep gaps)
  rsimax : skip when RSI(5) > X (100 = flat-top bars)
  hodmax : skip when dist_hod_atr > X (needs to be near the day's high)
  slopemax: skip when SMA20 slope > X;  volmax: skip when volumeRatio > X;  todskip=(a, b): skip bar closes a..b
  maxhold: time exit N minutes after entry (ts_r set: only if the best excursion so far < ts_r R)
  be_at/be_to : once the low reaches entry - be_at x R the stop moves to entry - be_to x R
Educational only - not financial advice."""
import math, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/bdi/gates1021/scripts")
from common import chain  # noqa: E402

SEC, TAF, CAT = 20.60e-6, 0.000195, 0.00005
PARENT = dict(gap=-2.6573517322540283, slope=0.5964763522148127, rsi=70.0, w=(950, 1500), cd=6, up=0.5, dn=1.0, rf=0.25,
              symcap=3, cap=150, latch=None, flat=1555, minpx=5.0, cf=0.15,
              spy950=None, spydn=None, rpct=None, rpmax=None, vwmax=None, vwmin=None, fomax=None, fomin=None, gapmin=None,
              rsimax=None, hodmax=None, slopemax=None, volmax=None, todskip=None, maxhold=None, ts_r=None, be_at=None, be_to=0.0)


def spy_table(path):
    s = pd.read_parquet(path)
    s.index = pd.DatetimeIndex(s.index).tz_convert("America/New_York")
    s = s.assign(date=s.index.strftime("%Y-%m-%d"), mn=s.index.hour * 60 + s.index.minute)
    out = []
    for d, g in s.groupby("date"):
        g = g.set_index("mn")
        if 589 not in g.index:
            continue
        ref = g.close.loc[589]
        c = g.close.reindex(range(570, 960)).ffill()
        tods = [(m + 1) // 60 * 100 + (m + 1) % 60 for m in c.index]
        out.append(pd.DataFrame({"date": d, "tod": tods, "spy950": (c.values / ref - 1) * 100}))
    return pd.concat(out, ignore_index=True)


def signals(c, v):
    m = ((c.gap <= v["gap"]) & (c.sma20_slope_pct > v["slope"]) & (c.rsi5 > v["rsi"]) & (c.tod >= v["w"][0]) &
         (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]))
    rp = v["rf"] * c.atr_d / c.close * 100
    for k, cond in (("spy950", lambda x: ~(c.spy950 > x)), ("spydn", lambda x: ~(c.spy950 < -x)), ("rpct", lambda x: rp >= x),
                    ("rpmax", lambda x: rp <= x), ("vwmax", lambda x: c.vwapDistPct <= x), ("vwmin", lambda x: c.vwapDistPct >= x),
                    ("fomax", lambda x: c.fromOpen <= x), ("fomin", lambda x: c.fromOpen >= x), ("gapmin", lambda x: c.gap >= x),
                    ("rsimax", lambda x: c.rsi5 <= x), ("hodmax", lambda x: c.dist_hod_atr <= x), ("slopemax", lambda x: c.sma20_slope_pct <= x),
                    ("volmax", lambda x: c.volumeRatio <= x), ("todskip", lambda x: ~c.tod.between(x[0], x[1]))):
        if v.get(k) is not None:
            m &= cond(v[k])
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
    trig = e - v["be_at"] * R if v["be_at"] else None
    j = np.searchsorted(mn, t0, side="left")
    mfe = mae = 0.0
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time", mfe, mae
        if tsm is not None and mn[k] >= tsm and mfe < v["ts_r"]:
            return o[k], mn[k], "time", mfe, mae
        if h[k] >= stop:
            return max(o[k], stop), mn[k], ("stop" if stop > e else "be"), mfe, max(mae, (stop - e) / R)
        if l[k] <= tgt - 0.01:
            return tgt, mn[k], "target", max(mfe, v["up"]), mae
        mfe = max(mfe, (e - l[k]) / R); mae = max(mae, (h[k] - e) / R)
        if trig is not None and l[k] <= trig:
            stop = min(stop, e - v["be_to"] * R)
    k = len(mn) - 1
    return ((c[k], mn[k], "time", mfe, mae) if k >= j else (e, t0, "time", 0.0, 0.0))


FEAT = ["gap", "fromOpen", "sma20_slope_pct", "vwapDistPct", "rsi5", "atrPct", "upper_wick", "dist_hod_atr", "volumeRatio",
        "sma20_dist_pct", "close", "atr_d", "spy950"]


def trades(c, v, getpath):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        R = v["rf"] * r.atr_d; e = r.close
        if v["cf"] is not None and (2 * (0.01 + e * 1e-4) + 0.02) / R > v["cf"]:
            continue
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
            if (v["latch"] is not None and real <= v["latch"] + 1e-12) or len(open_) >= v["cap"] or \
                    sum(1 for o in open_ if o[1] == t.symbol.values[i]) >= v["symcap"]:
                continue
            keep[i] = True; open_.append((t.xm.values[i], t.symbol.values[i], t.r.values[i]))
    return t[keep].reset_index(drop=True)


def stats(t):
    if not len(t):
        return dict(trades=0, win=np.nan, avg=np.nan, avg_wo_best=np.nan, total=0.0, worst_day=0.0, best_day=0.0, best_share=np.nan, days=0)
    d = t.groupby("date").r.agg(["sum", "size"])
    b = d["sum"].idxmax(); n_wo = len(t) - d.loc[b, "size"]
    return dict(trades=len(t), win=(t.r > 0).mean(), avg=t.r.mean(),
                avg_wo_best=(t.r.sum() - d.loc[b, "sum"]) / n_wo if n_wo else np.nan, total=t.r.sum(),
                worst_day=d["sum"].min(), best_day=d["sum"].max(), best_share=d["sum"].max() / t.r.sum() if t.r.sum() > 0 else np.nan,
                days=len(d))


def paired_t(a, b, days):
    da = a.groupby("date").r.sum().reindex(days, fill_value=0.0) if len(a) else pd.Series(0.0, index=days)
    db = b.groupby("date").r.sum().reindex(days, fill_value=0.0) if len(b) else pd.Series(0.0, index=days)
    x = (db - da).values
    if len(x) < 3 or x.std(ddof=1) == 0:
        return 0.0, float(x.sum())
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))), float(x.sum())
