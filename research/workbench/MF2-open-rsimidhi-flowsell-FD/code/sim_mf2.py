"""Mechanic MF2-FD bench (2026-11-16), reusing the RW5 / L3 workbench engine (sim.py here = research/workbench/RW5-.../code/sim.py:
5-min signal-bar close entry, 1-min exit walk stop-first, target only when traded through by >= $0.01, flat 15:55, LR8 costs,
per-setup book). MF2-FD sensors: heat <= -30, 55 <= RSI(14) <= 65, buyPressure < -0.25, window 09:50-15:00, refire on (cooldown
1 bar: LabStrategy refire_select via common.chain), ADV >= $95M (2-year only; replay names passed it live). Exit t1s05: 1R = 0.25 x
daily ATR, stop 0.5R, target 1R. Book = On Deck (account_testing.yaml): <= 150 open lots, <= 3 lots per symbol, no per-setup
latch, account cost filter max_stop_cost_r 0.15 (stop-exit round-trip cost / stop distance, applied AFTER the refire chain, as
the runner does).
R reported = P&L / the PARENT's stop distance (0.125 x daily ATR), i.e. the journal's R for the parent; copies that change the
stop or 1R are scored in the same fixed unit (col r) and in their own unit (col r_native) so no copy gains by re-scaling R.
tstop = (N min, X in units of 1R=rf x ATR): live time_stop_min / time_stop_min_r. Experimental layers (all OFF by default so PARENT scores exactly the parent): see BASE.
Educational only - not financial advice."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/home/user/MCF/research/bdi/gates1021/scripts")
from common import chain  # noqa: E402
from sim import SEC, TAF, CAT, book, stats, paired_t  # noqa: F401

U = 0.125   # parent stop distance in daily ATR = the R unit of every score
BASE = dict(heat=-30.0, rsilo=55.0, rsihi=65.0, bp=-0.25, w=(950, 1500), refire=True, cd=1, adv=95e6, up=1.0, dn=0.5, rf=0.25,
            symcap=3, cap=150, latch=-1e9, flat=1555, minpx=5.0, acct_costr=0.15,
            spy950=None, spy950min=None, spyrng=None, costr=None, vwmin=None, vwmax=None, fomin=None, fomax=None,
            gapmax=None, gapmin=None, rsi5max=None, rsi5min=None, heatmin=None, bpmin=None, atrpmax=None, slopemax=None, slopemin=None,
            maxhold=None, be_at=None, be_to=0.0, trail=None, first_only_n=None, tstop=None)


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


def stop_cost_r(c, v):
    """runner cost filter: (2 x (1c + 1 bp) + 2c) / stop distance."""
    return (2 * (0.01 + 1e-4 * c.close) + 0.02) / (v["dn"] * v["rf"] * c.atr_d)


def signals(c, v):
    m = ((c.heat <= v["heat"]) & (c.rsi >= v["rsilo"]) & (c.rsi <= v["rsihi"]) & (c.buyPressure < v["bp"]) & (c.tod >= v["w"][0]) &
         (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]))
    if "adv20" in c and v["adv"]:
        m &= c.adv20 >= v["adv"]
    for k, col, op in (("spy950", "spy950", "le"), ("spy950min", "spy950", "ge"), ("vwmin", "vwapDistPct", "ge"),
                       ("vwmax", "vwapDistPct", "le"), ("fomin", "fromOpen", "ge"), ("fomax", "fromOpen", "le"),
                       ("gapmax", "gap", "le"), ("gapmin", "gap", "ge"), ("rsi5max", "rsi5", "le"), ("rsi5min", "rsi5", "ge"),
                       ("heatmin", "heat", "ge"), ("bpmin", "buyPressure", "ge"), ("atrpmax", "atrPct", "le"), ("slopemax", "sma20_slope_pct", "le"),
                       ("slopemin", "sma20_slope_pct", "ge")):
        if v[k] is not None:
            m &= (c[col] <= v[k]) if op == "le" else (c[col] >= v[k])
    if v["spyrng"] is not None:
        m &= ~(c.spyrng >= v["spyrng"])
    if v["costr"] is not None:          # module-level cost clause (before the chain)
        m &= stop_cost_r(c, v) <= v["costr"]
    h = c[m].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if not len(h):
        return h
    idx = chain(h.symbol.values, h.date.values, h.tod.values.astype(int), bool(v["refire"]), int(v["cd"]))
    h = h.iloc[idx].reset_index(drop=True)
    if v["first_only_n"]:
        h = h[h.groupby(["symbol", "date"]).cumcount() < v["first_only_n"]].reset_index(drop=True)
    if v["acct_costr"] is not None:     # account cost filter (runner, after the chain)
        h = h[stop_cost_r(h, v) <= v["acct_costr"]].reset_index(drop=True)
    return h


def walk(path, tod, e, R, v):
    """short lot; R = 1R of the copy (rf x ATR). Stop e + dn R, target e - up R (None = no target)."""
    mn, o, h, l, c = path
    t0 = (tod // 100) * 60 + tod % 100
    flat = (v["flat"] // 100) * 60 + v["flat"] % 100
    if v["maxhold"]:
        flat = min(flat, t0 + v["maxhold"])
    stop = e + v["dn"] * R
    tgt = None if v["up"] is None else e - v["up"] * R
    trig = e - v["be_at"] * R if v["be_at"] else None
    j = np.searchsorted(mn, t0, side="left")
    mfe = 0.0; best = e
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return float(o[k]), int(mn[k]), "time", mfe
        if v["tstop"] is not None and mn[k] >= t0 + v["tstop"][0] and mfe < v["tstop"][1]:
            return float(o[k]), int(mn[k]), "time", mfe     # live time_stop_min / time_stop_min_r (best < X R after N min)
        if h[k] >= stop:
            return max(float(o[k]), stop), int(mn[k]), ("stop" if stop > e else "be"), mfe
        if tgt is not None and l[k] <= tgt - 0.01:
            return tgt, int(mn[k]), "target", max(mfe, (e - tgt) / R)
        mfe = max(mfe, (e - l[k]) / R); best = min(best, float(l[k]))
        if trig is not None and l[k] <= trig:
            stop = min(stop, e - v["be_to"] * R)
        if v["trail"] is not None and (e - best) >= v["trail"][1] * R:
            stop = min(stop, best + v["trail"][0] * R)
    k = len(mn) - 1
    return ((float(c[k]), int(mn[k]), "time", mfe) if k >= j else (e, t0, "time", 0.0))


FEAT = ["gap", "fromOpen", "heat", "buyPressure", "rsi5", "rsi", "vwapDistPct", "sma20_slope_pct", "sma20_dist_pct", "atrPct",
        "upper_wick", "dist_hod_atr", "dist_lod_atr", "volumeRatio", "pricePosition", "flow3", "close", "atr_d", "spy950", "spyrng"]


def trades(c, v, getpath):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        R = v["rf"] * r.atr_d; e = r.close; unit = U * r.atr_d; nat = v["dn"] * R
        px, xm, kind, mfe = walk(p, int(r.tod), e, R, v)
        cost = e * (1e-4 + SEC) + TAF + 2 * CAT + (max(0.02, 4e-4 * px) if kind in ("stop", "be") else
                                                    (max(0.01, 1e-4 * px) if kind == "time" else 0.0))
        f = [getattr(r, k, np.nan) for k in FEAT]
        rows.append((r.symbol, r.date, int(r.tod), (int(r.tod) // 100) * 60 + int(r.tod) % 100, xm, kind, (e - px) / unit,
                     ((e - px) - cost) / unit, ((e - px) - cost) / nat, mfe * R / unit, *f))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "r_gross", "r", "r_native", "mfe"] + FEAT)
