"""Reddit study engine: the open 2-year lab rows (research/bdi/stack1009/data/base.npz + data/extra.npz), the
Reddit-strategy triggers (long + short mirrors), the simple filter menu, the fixed exits (t1s1 / t05s1 / t1s05 from
the frames, production costs via gates.prod_r) and a structural exit S simulated on the 5-min rows, plus the gates.

Locked block: base.npz was built by research/history2y/lib.py with MCF_HIST_ALLOW_LOCKED unset, so the rule-19 block
(2024-11-01..2025-02-28) is not in it. Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

GEOMS = ("t1s1", "t05s1", "t1s05")
SDIR = ROOT / "research" / "bdi" / "stack1009" / "data"
KEYS = ["close", "rsi", "rsi5", "emaDiff", "macdPct", "volumeRatio", "vwapDistPct", "buyPressure", "gap", "fromOpen",
        "tod", "atr_d", "dist_pdh_atr", "dist_pdl_atr", "dist_hod_atr", "dist_lod_atr", "sma20_dist_pct",
        "sma50_dist_pct", "sma20_slope_pct", "flow3", "sd", "z", "orh", "orl", "pdh", "pdl", "day", "sym"]
KEYS += [f"p_{s}_{g}" for s in ("long", "short") for g in GEOMS]


class Data:
    def __init__(self):
        z = np.load(SDIR / "base.npz")
        self.B = {k: z[k] for k in KEYS}
        e = np.load(HERE / "data" / "extra.npz")
        self.B.update({k: e[k] for k in e.files})
        self.dates = pd.read_csv(SDIR / "dates.csv").iloc[:, 0].tolist()
        self.symbols = pd.read_csv(SDIR / "symbols.csv").iloc[:, 0].astype(str).tolist()
        reg = lib.regimes().reindex(pd.to_datetime(self.dates).date)["regime"].to_numpy()
        self.regc = np.select([reg == "up", reg == "down"], [1, -1], 0)
        self.reg = lib.regimes()
        self.nd = len(self.dates)
        sd = self.B["sd"]
        self.new = np.r_[True, sd[1:] != sd[:-1]]
        self._cache = {}
        B = self.B
        c, a = B["close"].astype(float), B["atr_d"].astype(float)
        self.c, self.atr, self.tod = c, a, B["tod"]
        self.h = c + B["hi_atr"].astype(float) * a
        self.l = c - B["lo_atr"].astype(float) * a
        self.hod = c + B["dist_hod_atr"].astype(float) * a
        self.lod = c - B["dist_lod_atr"].astype(float) * a
        self.open_d = c / (1 + B["fromOpen"].astype(float) / 100)
        self.pdc = self.open_d / (1 + B["gap"].astype(float) / 100)
        self.chg = (c / self.pdc - 1) * 100                 # % change vs prior close
        self.vwap = c / (1 + B["vwapDistPct"].astype(float) / 100)
        self.sma20 = c / (1 + B["sma20_dist_pct"].astype(float) / 100)
        # SPY at the same (day, tod): z and fromOpen in ATR units
        spy = self.symbols.index("SPY")
        m = B["sym"] == spy
        k = B["day"].astype(np.int64) * 10000 + B["tod"].astype(np.int64)
        sz = pd.Series(B["z"][m].astype(float), index=k[m])
        sfo = pd.Series((B["fromOpen"][m].astype(float) / 100) * c[m] / (1 + B["fromOpen"][m].astype(float) / 100) / a[m], index=k[m])
        self.spy_z = sz.reindex(k).to_numpy()
        self.spy_fo_atr = sfo.reindex(k).to_numpy()
        self.fo_atr = (c - self.open_d) / a

    def F(self, k):
        return self.B[k].astype(float)

    def prev(self, x, k=1):
        if k == 0:
            return np.asarray(x, float).copy()
        p = np.empty(len(x), float)
        p[:k] = np.nan
        p[k:] = x[:-k]
        sd = self.B["sd"]
        bad = np.r_[np.ones(k, bool), sd[k:] != sd[:-k]]
        p[bad] = np.nan
        return p

    def grp_cummax(self, x):
        return _seg_cum(np.nan_to_num(x, nan=-np.inf), self.new, True)

    def grp_cummin(self, x):
        return _seg_cum(np.nan_to_num(x, nan=np.inf), self.new, False)

    def grp_cumsum(self, x):
        return _seg_cumsum(x.astype(float), self.new)

    def ffill(self, x):
        return _seg_ffill(x.astype(float), self.new)


@numba.njit(cache=True)
def _seg_cum(x, new, ismax):
    out = np.empty_like(x)
    cur = x[0]
    for i in range(len(x)):
        if new[i]:
            cur = x[i]
        elif ismax:
            cur = max(cur, x[i])
        else:
            cur = min(cur, x[i])
        out[i] = cur
    return out


@numba.njit(cache=True)
def _seg_cumsum(x, new):
    out = np.empty_like(x)
    cur = 0.0
    for i in range(len(x)):
        if new[i]:
            cur = 0.0
        if not np.isnan(x[i]):
            cur += x[i]
        out[i] = cur
    return out


@numba.njit(cache=True)
def _seg_ffill(x, new):
    out = np.empty_like(x)
    cur = np.nan
    for i in range(len(x)):
        if new[i]:
            cur = np.nan
        if not np.isnan(x[i]):
            cur = x[i]
        out[i] = cur
    return out


@numba.njit(cache=True)
def _first_per_sd(idx, sd):
    keep = np.zeros(len(idx), np.bool_)
    last = -1
    for j in range(len(idx)):
        s = sd[idx[j]]
        if s != last:
            keep[j] = True
            last = s
    return keep


@numba.njit(cache=True)
def _sexit(idx, side, c, h, l, atr, sd, tod, cond, tgt, slip_ps, slip_bps, stop_extra):
    """Structural exit on the 5-min rows: from the bar after entry, stop-first (-1R on the bar's low/high), then the
    structural target `tgt` (a limit, no exit slippage), then the structural condition `cond` at the bar close;
    else flat at the last row of the symbol-day (15:00 bar close in these frames). Production costs."""
    out = np.empty(len(idx))
    for j in range(len(idx)):
        i = idx[j]
        e = c[i]
        R = 0.25 * atr[i]
        st = e - side * R
        tg = tgt[i]
        k = i + 1
        x = np.nan
        kind = 0
        while k < len(c) and sd[k] == sd[i]:
            if (side > 0 and l[k] <= st) or (side < 0 and h[k] >= st):
                x = st
                kind = 1
                break
            if not np.isnan(tg) and ((side > 0 and h[k] >= tg) or (side < 0 and l[k] <= tg)):
                x = tg
                kind = 2
                break
            if cond[k]:
                x = c[k]
                kind = 3
                break
            k += 1
        if np.isnan(x):
            x = c[k - 1]
            kind = 3
        gross = side * (x - e) / R
        cost = slip_ps + e * slip_bps
        if kind != 2:
            cost += slip_ps + x * slip_bps
        if kind == 1:
            cost += stop_extra
        out[j] = gross - cost / R
    return out


def tstat(r, day, nd):
    n = len(r)
    if n < 2:
        return 0.0
    mu = r.mean()
    S = np.bincount(day, weights=r, minlength=nd)
    C = np.bincount(day, minlength=nd)
    se = np.sqrt(((S - C * mu) ** 2).sum()) / n
    return float(mu / se) if se > 0 else 0.0


def trades(D: Data, ev, side: str, geom: str, sexit=None, tgt=None, lo=950, hi=1500):
    """First qualifying row per symbol-day in [lo, hi] -> (row idx, production R)."""
    m = ev & (D.tod >= lo) & (D.tod <= hi)
    idx = np.flatnonzero(m)
    if not len(idx):
        return idx, np.zeros(0)
    idx = idx[_first_per_sd(idx, D.B["sd"])]
    s = 1 if side == "long" else -1
    if geom == "S":
        cond = np.zeros(len(D.c), np.bool_) if sexit is None else np.nan_to_num(sexit).astype(np.bool_)
        tg = np.full(len(D.c), np.nan) if tgt is None else tgt.astype(float)
        r = _sexit(idx, s, D.c, D.h, D.l, D.atr, D.B["sd"], D.tod, cond, tg, gates.SLIP_PS, gates.SLIP_BPS, gates.STOP_EXTRA)
    else:
        r = D.B[f"p_{side}_{geom}"][idx].astype(float)
    ok = np.isfinite(r) & (D.atr[idx] > 0)
    return idx[ok], r[ok]


def quick(D: Data, idx, r):
    day = D.B["day"][idx]
    n = len(r)
    out = {"n": n, "per_day": round(n / D.nd, 3)}
    if n < 2:
        return out | {"exp": np.nan, "t": 0.0}
    out["exp"] = float(r.mean())
    out["win"] = float((r > 0).mean())
    out["t"] = tstat(r, day, D.nd)
    rc = D.regc[day]
    for nm, v in (("up", 1), ("flat", 0), ("down", -1)):
        mm = rc == v
        out[f"n_{nm}"] = int(mm.sum())
        out[f"exp_{nm}"] = float(r[mm].mean()) if mm.any() else np.nan
        out[f"t_{nm}"] = tstat(r[mm], day[mm], D.nd) if mm.sum() > 1 else 0.0
    C = np.bincount(day, minlength=D.nd)
    S = np.bincount(day, weights=r, minlength=D.nd)
    out["maxday"] = float(C.max() / n)
    b = int(np.argmax(S))
    out["ex_best_day"] = float((S.sum() - S[b]) / max(1, n - C[b]))
    return out


def full(D: Data, idx, r, n_tries: int):
    """Gate metrics via mcf.research.gates (regime split, walk-forward, verdict)."""
    tr = pd.DataFrame({"date": pd.to_datetime(np.array(D.dates)[D.B["day"][idx]]).date, "r": r})
    sm = gates.summary(tr)
    rg = gates.regime_split(tr, D.reg)
    wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
    v, fails = gates.verdict(sm, rg, wf, n_tries)
    return {"summary": sm, "regime": {k: rg[k] for k in ("up", "flat", "down")}, "regime_pass": rg["pass"],
            "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"], "verdict": v, "fails": fails,
            "t_required": gates.t_required(n_tries)}
