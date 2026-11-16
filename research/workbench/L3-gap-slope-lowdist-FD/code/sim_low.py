"""Mechanic bench for L3-gap-slope-lowdist-FD (2026-11-16). Reuses the L3-fromopen bench engine (sim.py/sim2.py: 5-min
signal-bar close entry, 1-min exit walk stop-first, target only when traded through by >= $0.01, flat 15:55, LR8 costs,
book) with the lowdist sensors and the Testing-account parts:
  sensors : gap <= gap, sma20_slope_pct > slope, lo < dist_lod_atr <= hi, price >= minpx, window
  refire  : off (first qualifying bar per symbol-day) unless refire=True (LabStrategy chain, cooldown cd)
  P17 cost filter (Testing): skip if (2 x (0.01 + 1bp px) + 0.02) / R > costf   (runner max_stop_cost_r 0.15)
  book    : <= cap open lots (150), <= symcap per symbol (3), per-setup latch off (Testing), as live today
Optional experimental layers, all OFF by default: spy950, spyrng, rpct, fomax, fomin, vwmax, vwmin, rsi5min, adv, tgtc,
be_at/be_to, maxhold/ts_r (runner time_stop_min/_r).  Educational only - not financial advice."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/home/user/MCF/research/bdi/gates1021/scripts")
from common import chain  # noqa: E402
import sim2
from sim import SEC, TAF, CAT, book, stats, paired_t  # noqa: F401

PARENT = dict(gap=-2.6573517322540283, slope=0.37244729995727527, lo=0.7816761255264282, hi=0.9764953255653381,
              w=(950, 1500), refire=False, cd=1, up=1.0, dn=1.0, rf=0.25, symcap=3, cap=150, latch=-1e9, flat=1555,
              minpx=5.0, costf=0.15, spy950=None, spyrng=None, rpct=None, fomax=None, fomin=None, vwmax=None, vwmin=None,
              rsi5min=None, adv=None, tgtc=False, be_at=None, be_to=0.0, maxhold=None, ts_r=None, fo=None, gapmin=None, slopemax=None)


def signals(c, v):
    m = ((c.gap <= v["gap"]) & (c.sma20_slope_pct > v["slope"]) & (c.dist_lod_atr > v["lo"]) & (c.dist_lod_atr <= v["hi"]) &
         (c.tod >= v["w"][0]) & (c.tod <= v["w"][1]) & (c.atr_d > 0) & (c.close >= v["minpx"]))
    if v["costf"] is not None:
        px = c.close; R = v["rf"] * c.atr_d
        m &= (2 * (0.01 + px * 1e-4) + 0.02) / R <= v["costf"]
    for k, col, op in (("spy950", "spy950", "gt"), ("fomax", "fromOpen", "le"), ("fomin", "fromOpen", "ge"),
                       ("vwmax", "vwapDistPct", "le"), ("vwmin", "vwapDistPct", "ge"), ("rsi5min", "rsi5", "ge"),
                       ("adv", "adv20", "ge")):
        if v[k] is not None:
            m &= ~(c[col] > v[k]) if op == "gt" else ((c[col] <= v[k]) if op == "le" else (c[col] >= v[k]))
    if v["gapmin"] is not None:
        m &= c.gap >= v["gapmin"]
    if v["slopemax"] is not None:
        m &= c.sma20_slope_pct <= v["slopemax"]
    if v["spyrng"] is not None:
        m &= ~(c.spyrng >= v["spyrng"])
    if v["rpct"] is not None:
        m &= (v["rf"] * c.atr_d / c.close * 100 >= v["rpct"])
    h = c[m].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    if not len(h):
        return h
    idx = chain(h.symbol.values, h.date.values, h.tod.values.astype(int), bool(v["refire"]), int(v["cd"]))
    return h.iloc[idx].reset_index(drop=True)


FEAT = ["gap", "fromOpen", "sma20_slope_pct", "dist_lod_atr", "vwapDistPct", "rsi5", "atrPct", "upper_wick", "volumeRatio",
        "close", "atr_d", "adv20", "spy950", "spyrng"]


def trades(c, v, getpath):
    s = signals(c, v)
    rows = []
    for r in s.itertuples():
        p = getpath(r.symbol, r.date)
        if p is None:
            continue
        R = v["rf"] * r.atr_d; e = r.close
        px, xm, kind, mfe = sim2.walk(p, int(r.tod), e, R, v)
        cost = e * (1e-4 + SEC) + TAF + 2 * CAT + (max(0.02, 4e-4 * px) if kind in ("stop", "be") else
                                                    (max(0.01, 1e-4 * px) if kind == "time" else 0.0))
        f = [getattr(r, k, np.nan) for k in FEAT]
        rows.append((r.symbol, r.date, int(r.tod), (int(r.tod) // 100) * 60 + int(r.tod) % 100, xm, kind, (e - px) / R,
                     ((e - px) - cost) / R, mfe, *f))
    return pd.DataFrame(rows, columns=["symbol", "date", "tod", "em", "xm", "kind", "r_gross", "r", "mfe"] + FEAT)
