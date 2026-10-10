"""Exit re-simulation on the dense 5-min bars and the hedge leg (NOTES 1.3). Educational only - not financial advice."""
from __future__ import annotations

import numba
import numpy as np
import pandas as pd

from common import LOCKED, lib
from mcf.research import gates

GEOMK = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
HCOST_PS, HCOST_BPS = 0.01, 1e-4


@numba.njit(cache=True)
def sim_exit(C, H, L, s, d, b, side, upk, dnk, R):
    """Lab exit (mcf.research.setup_lab._outcomes_asym): from the bar after entry to the 15:55 bar, stop first when both
    touch in one bar; else timed exit at the last bar's close. Returns entry px, exit bar, lab R (1c/side), win."""
    n = len(s)
    ex = np.full(n, -1, np.int64)
    lab = np.full(n, np.nan)
    win = np.full(n, np.nan)
    ent = np.full(n, np.nan)
    nb = C.shape[2]
    for j in range(n):
        e = C[s[j], d[j], b[j]]
        ent[j] = e
        r = R[j]
        if not (r > 0) or np.isnan(e):
            continue
        tg = e + side[j] * upk[j] * r
        st = e - side[j] * dnk[j] * r
        last = -1
        res = np.nan
        w = 0.0
        for k in range(b[j] + 1, nb):
            c = C[s[j], d[j], k]
            if np.isnan(c):
                continue
            hh, ll = H[s[j], d[j], k], L[s[j], d[j], k]
            last = k
            if side[j] > 0:
                hs, ht = ll <= st, hh >= tg
            else:
                hs, ht = hh >= st, ll <= tg
            if hs:
                res = -dnk[j]
                break
            if ht:
                res = upk[j]
                w = 1.0
                break
        if last < 0:
            res = 0.0
            last = b[j]
        elif np.isnan(res):
            res = side[j] * (C[s[j], d[j], last] - e) / r
        ex[j] = last
        lab[j] = res - 2 * 0.01 / r
        win[j] = w
    return ent, ex, lab, win


@numba.njit(cache=True)
def etf_px(C, h, d, k):
    """ETF close at bar k of day d (last valid bar at or before k); NaN if none."""
    out = np.full(len(h), np.nan)
    for j in range(len(h)):
        if h[j] < 0 or k[j] < 0:
            continue
        for q in range(k[j], -1, -1):
            v = C[h[j], d[j], q]
            if not np.isnan(v):
                out[j] = v
                break
    return out


def hedge_r(C, side, e, R, beta, h, d, b, ex):
    """Hedge-leg P/L minus both sides' hedge costs, in stock-R units."""
    he, hx = etf_px(C, h, d, b), etf_px(C, h, d, ex)
    pnl = -side * beta * e * (hx / he - 1) / R
    cost = 2 * beta * e * (HCOST_PS / he + HCOST_BPS) / R
    return pnl - cost


def score(tr: pd.DataFrame, reg: pd.DataFrame) -> dict:
    """tr: date, r. Summary + regime split + walk-forward + busiest-session share."""
    sm = gates.summary(tr)
    if not sm.get("n"):
        return {"n": 0}
    rg = gates.regime_split(tr, reg)
    wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
    busy = float(tr.groupby("date").size().max() / len(tr))
    out = {k: sm.get(k) for k in ("n", "days", "win_rate", "exp_r", "t", "ex_best_day")}
    out["busiest"] = round(busy, 4)
    for k in ("up", "flat", "down"):
        out[f"{k}_n"], out[f"{k}_exp"], out[f"{k}_t"] = rg[k].get("n", 0), rg[k].get("exp_r"), rg[k].get("t")
    out["regime_pass"] = bool(rg["pass"])
    out["wf_share"] = wf["share_positive"]
    out["wf_folds"] = wf["n_folds"]
    return out


def bar_check(o: dict, treq: float, plateau=None) -> tuple[bool, list[str]]:
    f = []
    if o.get("n", 0) < 150:
        f.append("n<150")
    if (o.get("exp_r") or -1) <= 0:
        f.append("exp<=0")
    if not o.get("regime_pass"):
        f.append("up/down")
    if (o.get("t") or 0) < treq:
        f.append(f"t<{treq}")
    if o.get("wf_share") is None or o["wf_share"] < 0.6:
        f.append("wf<0.6")
    if (o.get("ex_best_day") or -1) <= 0:
        f.append("exbest<=0")
    if (o.get("busiest") or 1) > 0.10:
        f.append("busiest>10%")
    if plateau is not None and not (plateau > 0):
        f.append("plateau<=0")
    return (not f), f
