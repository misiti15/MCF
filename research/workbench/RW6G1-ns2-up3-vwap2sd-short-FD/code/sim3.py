"""Mechanic RW6G1 bench (2026-11-16), reusing the L3/RW5 workbench engine (research/workbench/L3-gap-slope-fromopen-FD/code/sim.py:
5-min signal-bar close entry, 1-min exit walk stop-first, target only when traded through by >= $0.01, flat 15:55, LR8 costs,
per-setup book). RW6G1 sensors: close crosses above the 5-min SMA50 on this bar (previous bar of the same session <= 0),
fromOpen > 3, RSI(14) >= 60, VWAP +2 SD band guard (the module's own vwap_band_block, code/band.py), window 09:50-15:00,
refire on with cooldown 1 (LabStrategy chain), ADV >= $95M (2-year only), Graveyard book (<= 75 lots, <= 3 per symbol, -2R latch).
Experimental layers, all OFF by default so PARENT scores exactly the parent:
  spy950 : skip when SPY is up more than X % since the 09:50 close     spyrng : skip when SPY above its 09:30-09:50 high
  spydn  : require SPY <= X % since 09:50 (same as spy950, kept for naming)
  costr  : skip when stop-exit cost / 1R > X      rpct : skip when 1R < X % of price
  fomax  : fromOpen <= X     vwmin/vwmax : vwapDistPct bounds     z5min/z5max : (close - VWAP) / VWAP SD bounds at the signal bar (zmaxmax unused: first-bar SD = 0)
  k      : band multiple (None = band guard off)     rsimax, slopemax, pdh : extra bounds
  hodmax : (HOD - close) / daily ATR <= X     volmin : volumeRatio >= X
  maxhold, be_at/be_to, dn/up, flat : exits
Educational only - not financial advice."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/home/user/MCF/research/bdi/gates1021/scripts")
from common import chain  # noqa: E402
from sim import SEC, TAF, CAT, book, stats, paired_t  # noqa: F401

BASE = dict(fo=3.0, rsi=60.0, k=2.0, w=(950, 1500), refire=True, cd=1, adv=95e6, up=1.0, dn=1.0, rf=0.25,
            symcap=3, cap=75, latch=-2.0, flat=1555, minpx=5.0,
            spy950=None, spyrng=None, costr=None, rpct=None, vwmin=None, vwmax=None, fomax=None, rsimax=None, zmaxmax=None,
            slopemax=None, slopemin=None, z5min=None, z5max=None, hodmax=None, volmin=None, pdhmin=None, maxhold=None, be_at=None, be_to=0.0, gapmax=None, gapmin=None)
TESTBOOK = dict(cap=50, symcap=3, latch=-1e9, costr=0.15)   # Testing A/D/E book: no per-setup latch, CF stop-cost filter


def costr(c, rf):
    R = rf * c.atr_d
    return (2 * (0.01 + 1e-4 * c.close) + 0.02) / R


def signals(c, v):
    m = ((c.sma50_dist_pct > 0) & (c.p_sma50 <= 0) & (c.fromOpen > v["fo"]) & (c.rsi >= v["rsi"]) & (c.tod >= v["w"][0]) &
         (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]))
    if v["k"] is not None:
        m &= ~c[f"blk{int(v['k'] * 10)}"].fillna(True).astype(bool)
    if "adv20" in c and v["adv"]:
        m &= c.adv20 >= v["adv"]
    for k, col, op in (("spy950", "spy950", "le"), ("vwmin", "vwapDistPct", "ge"), ("vwmax", "vwapDistPct", "le"),
                       ("fomax", "fromOpen", "le"), ("rsimax", "rsi", "le"), ("zmaxmax", "zmax", "le"),
                       ("slopemax", "sma20_slope_pct", "le"), ("slopemin", "sma20_slope_pct", "ge"),
                       ("pdhmin", "dist_pdh_atr", "ge"), ("z5min", "z5", "ge"), ("hodmax", "dist_hod_atr", "le"), ("volmin", "volumeRatio", "ge"), ("z5max", "z5", "le"), ("gapmax", "gap", "le"), ("gapmin", "gap", "ge")):
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
    trig = e - v["be_at"] * R if v["be_at"] else None
    j = np.searchsorted(mn, t0, side="left")
    mfe = mae = 0.0
    for k in range(j, len(mn)):
        if mn[k] >= flat:
            return o[k], mn[k], "time", mfe, mae
        if h[k] >= stop:
            return max(o[k], stop), mn[k], ("stop" if stop > e else "be"), mfe, max(mae, (stop - e) / R)
        if l[k] <= tgt - 0.01:
            return tgt, mn[k], "target", max(mfe, (e - tgt) / R), mae
        mfe = max(mfe, (e - l[k]) / R); mae = max(mae, (h[k] - e) / R)
        if trig is not None and l[k] <= trig:
            stop = min(stop, e - v["be_to"] * R)
    k = len(mn) - 1
    return ((c[k], mn[k], "time", mfe, mae) if k >= j else (e, t0, "time", 0.0, 0.0))


FEAT = ["gap", "fromOpen", "rsi", "rsi5", "heat", "buyPressure", "vwapDistPct", "sma20_slope_pct", "sma20_dist_pct", "atrPct",
        "upper_wick", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr", "volumeRatio", "pricePosition", "flow3", "close", "atr_d",
        "spy950", "spyrng", "zmax", "z5"]


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
