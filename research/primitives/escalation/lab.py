"""Shared lab helpers for the escalation study (key: escalation). Educational only - not financial advice.

Train + valid only (research/setups2/data). The test split / anything dated >= 2026-09-16 is never read.
"""
from __future__ import annotations

import gc
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/heat/candidates"))
from mcf.research.setup_lab import load  # noqa: E402

GEOMS = ("t1s1", "t05s1", "t1s05")
GEOM_K = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
FEAT = ["close", "atr_d", "tod", "symbol", "date", "rsi", "rsi5", "momentum", "emaDiff", "macdPct", "volumeRatio",
        "volumeSurge", "pricePosition", "vwapDistPct", "buyPressure", "rsiSlope", "vwapReclaim", "gap", "fromOpen",
        "rsiHeat", "priceActionHeat", "momentumHeat", "vwapHeat", "heat", "dist_pdh_atr", "dist_pdl_atr",
        "dist_hod_atr", "dist_lod_atr", "sma20_dist_pct", "sma50_dist_pct", "sma20_slope_pct", "flow3", "flow9prev",
        "vol_climax", "bear_div", "bull_div", "upper_wick", "lower_wick"]
OUT_COLS = [f"{k}_{s}_{g}" for k in ("r", "win") for s in ("long", "short") for g in GEOMS]


class Split:
    """Column arrays (float32) for one split, sorted by symbol, date, tod."""

    def __init__(self, name: str):
        df = load(name, data_dir=str(ROOT / "research/setups2/data"), columns=FEAT + OUT_COLS)
        assert str(max(df["date"])) < "2026-09-16", "locked dates present"
        self.name = name
        self.c = {k: df[k].to_numpy() for k in FEAT if k not in ("symbol", "date")}
        close = df["close"].to_numpy(np.float64)
        atr = df["atr_d"].to_numpy(np.float64)
        # derived (all causal, all from lab-frame columns)
        self.c["vwap_atr"] = (df["vwapDistPct"].to_numpy(np.float64) * close / 100 / atr).astype(np.float32)
        self.c["fo_atr"] = (df["fromOpen"].to_numpy(np.float64) * close / 100 / atr).astype(np.float32)
        self.c["gap_atr"] = (df["gap"].to_numpy(np.float64) * close / 100 / atr).astype(np.float32)  # approx (close vs open)
        self.c["hod_fo_atr"] = self.c["fo_atr"] + df["dist_hod_atr"].to_numpy(np.float32)   # how far HOD sits above the open (ATR)
        self.c["lod_fo_atr"] = self.c["fo_atr"] - df["dist_lod_atr"].to_numpy(np.float32)   # LOD vs open (ATR, <0 below open)
        self.c["flowflip"] = (df["flow3"].to_numpy(np.float64) - df["flow9prev"].to_numpy(np.float64)).astype(np.float32)
        self.c["R"] = (0.25 * atr).astype(np.float32)
        d = pd.factorize(df["date"], sort=True)
        self.date_id, self.dates = d[0].astype(np.int32), d[1]
        sd = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        ids = np.r_[0, np.cumsum(sd[1:] != sd[:-1])].astype(np.int32)
        tod = self.c["tod"]
        assert not np.any((ids[1:] == ids[:-1]) & (tod[1:] <= tod[:-1])), "not sorted"
        self.symday = ids
        self.symbol = df["symbol"].astype(str).to_numpy()
        self.r, self.w, self.ctrl = {}, {}, {}
        key = self.date_id.astype(np.int64) * 10000 + tod.astype(np.int64)
        for s in ("long", "short"):
            for g in GEOMS:
                r = df[f"r_{s}_{g}"].to_numpy(np.float32)
                self.r[(s, g)] = r
                self.w[(s, g)] = df[f"win_{s}_{g}"].to_numpy(np.float32)
                ok = np.isfinite(r)
                cm = pd.Series(r[ok]).groupby(key[ok]).mean()
                self.ctrl[(s, g)] = cm.reindex(key).to_numpy(np.float32)
        del df, sd
        gc.collect()
        self.n = len(self.symday)
        self._base = {}

    def first_idx(self, m):
        idx = np.flatnonzero(m)
        if len(idx) == 0:
            return idx
        ids = self.symday[idx]
        return idx[np.r_[True, ids[1:] != ids[:-1]]]

    def prod_extra(self, idx, side, geom):
        """Approximate extra production cost in R: +1 bps per side, +2c on stop exits (auditor recomputes exactly;
        the 3c extended-tier surcharge is NOT modelled here)."""
        R = self.c["R"][idx].astype(np.float64)
        px = self.c["close"][idx].astype(np.float64)
        r = self.r[(side, geom)][idx]
        stop = GEOM_K[geom][1]
        stopped = r <= -stop + 1e-6 - 0.0  # loss at (or beyond after cost) the stop
        stopped = r < -stop + 0.02  # r already includes 1c costs; stop exit = -stop - cost
        return (2 * 1e-4 * px + 0.02 * stopped) / R

    def baseline(self, side, geom, t0, t1, universe=None, key=None):
        """Random-timing baseline: mean r of every bar in the window (same side), optionally inside a universe mask."""
        k = (side, geom, t0, t1, key)
        if key is not None and k in self._base:
            return self._base[k]
        tod = self.c["tod"]
        m = (tod >= t0) & (tod <= t1) & np.isfinite(self.r[(side, geom)])
        if universe is not None:
            m &= universe
        v = float(np.nanmean(self.r[(side, geom)][m])) if m.any() else float("nan")
        if key is not None:
            self._base[k] = v
        return v


def evaluate(S: Split, m, side: str, geom: str, prod: bool = True) -> dict:
    r_all = S.r[(side, geom)]
    idx = S.first_idx(np.asarray(m, bool) & np.isfinite(r_all))
    if len(idx) == 0:
        return {"n": 0}
    r = r_all[idx].astype(np.float64)
    w = S.w[(side, geom)][idx].astype(np.float64)
    di = S.date_id[idx]
    n = len(r)
    mu = r.mean()
    sums = np.bincount(di, weights=r, minlength=len(S.dates))
    cnt = np.bincount(di, minlength=len(S.dates))
    act = cnt > 0
    dm = sums[act] - cnt[act] * mu
    se = float(np.sqrt((dm ** 2).sum()) / n) if act.sum() > 1 else float("nan")
    best = int(np.argmax(np.where(act, sums, -np.inf)))
    exb = (r.sum() - sums[best]) / (n - cnt[best]) if n > cnt[best] else float("nan")
    ctrl = S.ctrl[(side, geom)][idx].astype(np.float64)
    days = np.flatnonzero(act)
    half = days[len(days) // 2]
    h1, h2 = r[di < half], r[di >= half]
    gw, gl = r[r > 0].sum(), -r[r <= 0].sum()
    out = {"n": n, "days": int(act.sum()), "win_rate": round(float(np.nanmean(w)), 4), "exp_r": round(float(mu), 4),
           "t_dc": round(mu / se, 2) if se and se > 0 else None, "pf": round(float(gw / gl), 3) if gl > 0 else None,
           "green_days": round(float((sums[act] > 0).mean()), 3), "ex_best_day": round(float(exb), 4),
           "ctrl": round(float(np.nanmean(ctrl)), 4),
           "half1": round(float(h1.mean()), 4) if len(h1) else None, "half2": round(float(h2.mean()), 4) if len(h2) else None}
    if prod:
        rp = r - S.prod_extra(idx, side, geom)
        sp = np.bincount(di, weights=rp, minlength=len(S.dates))
        mup = rp.mean()
        sep = float(np.sqrt(((sp[act] - cnt[act] * mup) ** 2).sum()) / n) if act.sum() > 1 else float("nan")
        out["exp_r_prod"] = round(float(mup), 4)
        out["t_dc_prod"] = round(mup / sep, 2) if sep and sep > 0 else None
    return out


class Sub:
    """Row subset of a Split (order preserved), so family grids run on small arrays."""

    def __init__(self, S: Split, m):
        ix = np.flatnonzero(m)
        self.parent, self.ix = S, ix
        self.name = S.name
        self.c = {k: v[ix] for k, v in S.c.items()}
        self.date_id, self.dates, self.symday = S.date_id[ix], S.dates, S.symday[ix]
        self.r = {k: v[ix] for k, v in S.r.items()}
        self.w = {k: v[ix] for k, v in S.w.items()}
        self.ctrl = {k: v[ix] for k, v in S.ctrl.items()}
        self.n = len(ix)

    first_idx = Split.first_idx
    prod_extra = Split.prod_extra


def cond(S, col, op, val):
    x = S.c[col]
    with np.errstate(invalid="ignore"):
        if op == "<":
            return x < val
        if op == ">":
            return x > val
        if op == "<=":
            return x <= val
        if op == ">=":
            return x >= val
        if op == "==":
            return x == val
        if op == "in":
            return (x >= val[0]) & (x <= val[1])
    raise ValueError(op)
