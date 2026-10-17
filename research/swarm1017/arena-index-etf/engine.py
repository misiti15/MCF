"""Matrix evaluation engine for arena-index-etf: rows laid out as [symbol-day, slot]; a configuration is an AND of
condition masks plus a window; the trade is the FIRST qualifying slot per symbol-day (same as
gates.first_per_symbol_day on sorted frames). Stats are day-clustered exactly as gates.summary.
Educational only - not financial advice."""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import GEOMS, LIVE, SIDES, TRAIN_H1_END  # noqa: E402

from mcf.research.arena import data as D  # noqa: E402

N_SLOTS = 63
OUTS = [f"{s}_{g}" for s in SIDES for g in GEOMS]


def slot_of(tod):
    tod = np.asarray(tod, int)
    mins = (tod // 100) * 60 + tod % 100
    return (mins - (9 * 60 + 50)) // 5


class Panel:
    def __init__(self, rows_dir):
        fs = sorted(glob.glob(str(Path(rows_dir) / "month=*.parquet")))
        A = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
        A["date"] = pd.to_datetime(A["date"]).dt.date
        A = A.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        self.A = A
        sd_key = pd.MultiIndex.from_arrays([A["symbol"].to_numpy(), A["date"].to_numpy()])
        sd, uniq = sd_key.factorize()
        self.nsd = len(uniq)
        self.sd_symbol = np.asarray(uniq.get_level_values(0))
        self.sd_date = np.asarray(uniq.get_level_values(1))
        self.slot = slot_of(A["tod"].to_numpy())
        assert self.slot.min() >= 0 and self.slot.max() < N_SLOTS
        self.flat = sd * N_SLOTS + self.slot
        dates = pd.Index(sorted(set(self.sd_date)))
        self.dates = dates
        self.sd_day = dates.get_indexer(self.sd_date)
        mo = pd.to_datetime(pd.Series(dates)).dt.strftime("%Y-%m").to_numpy()
        self.day_month = mo
        self.day_split = np.where(mo <= D.TRAIN_END, 0, 1)            # 0 train, 1 valid
        self.day_half = np.where(mo <= TRAIN_H1_END, 0, 1)
        reg = D.regimes()
        self.regimes_df = D._lib().regimes()
        self.day_reg = pd.Series(dates).map(reg).fillna("na").to_numpy()
        self.sd_split = self.day_split[self.sd_day]
        self.tod_slots = np.array([(950 + 0) for _ in range(1)])
        self.R, self.C, self.E = {}, {}, {}
        for o in OUTS:
            self.R[o] = self.mat(A[f"r_{o}"].to_numpy(np.float32))
            self.C[o] = self.mat(A[f"c_{o}"].to_numpy(np.float32))
            self.E[o] = self.mat(A[f"e_{o}"].to_numpy(np.float32))
            self.R[o][~(np.isfinite(self.C[o]) & np.isfinite(self.E[o]))] = np.nan
        slots = np.arange(N_SLOTS)
        tods = np.array([(9 * 60 + 50 + 5 * k) for k in slots])
        self.slot_tod = (tods // 60) * 100 + tods % 60

    def mat(self, x):
        M = np.full(self.nsd * N_SLOTS, np.nan, np.float32)
        M[self.flat] = x
        return M.reshape(self.nsd, N_SLOTS)

    def ind(self, name):
        return self.mat(self.A[name].to_numpy(np.float32))

    def win_mask(self, window):
        lo, hi = window
        t = self.slot_tod
        return (t >= lo) & ((t < hi) | ((hi >= 1500) & (t <= 1500)))


def cond_mat(P: Panel, cache: dict, cond):
    key = (cond[0], cond[1], tuple(cond[2]) if isinstance(cond[2], (list, tuple)) else cond[2])
    if key in cache:
        return cache[key]
    name, op, v = cond
    X = cache.get(("__ind", name))
    if X is None:
        X = P.ind(name)
        cache[("__ind", name)] = X
    with np.errstate(invalid="ignore"):
        if op == "<=":
            m = X <= v
        elif op == "<":
            m = X < v
        elif op == ">=":
            m = X >= v
        elif op == ">":
            m = X > v
        elif op == "==":
            m = X == v
        else:
            m = (X >= v[0]) & (X < v[1])
    cache[key] = m
    return m


def first_trades(P: Panel, M, o, rows=None):
    """M: bool [nsd, 63] already including the window. Returns sd indices, slot, r, c, e of first qualifying bar."""
    R = P.R[o]
    M = M & np.isfinite(R)
    if rows is not None:
        M = M & rows[:, None]
    has = M.any(1)
    sd = np.flatnonzero(has)
    k = M[sd].argmax(1)
    return sd, k, R[sd, k].astype(float), P.C[o][sd, k].astype(float), P.E[o][sd, k].astype(float)


def summ(day, r, ndays):
    """gates.summary equivalent: n, days, exp, se, t (day-clustered)."""
    n = len(r)
    if n == 0:
        return dict(n=0, days=0, exp=np.nan, t=np.nan)
    mu = r.mean()
    s = np.bincount(day, weights=r, minlength=ndays)
    c = np.bincount(day, minlength=ndays)
    used = c > 0
    se = np.sqrt(((s[used] - c[used] * mu) ** 2).sum()) / n if used.sum() > 1 else np.nan
    return dict(n=n, days=int(used.sum()), exp=float(mu), t=float(mu / se) if se and se > 0 else np.nan)


def stats_split(P: Panel, sd, r, c, e, split=0):
    """Train (split=0) or valid (1) screen statistics."""
    day = P.sd_day[sd]
    sel = P.day_split[day] == split
    day, r, c, e = day[sel], r[sel], c[sel], e[sel]
    nd = len(P.dates)
    s = summ(day, r, nd)
    out = {"n": s["n"], "days": s["days"], "exp": s["exp"], "t": s["t"]}
    if s["n"] == 0:
        return out
    out["exc_c"] = float((r - c).mean())
    xe = summ(day, r - e, nd)
    out["exc_e"], out["t_exc_e"] = xe["exp"], xe["t"]
    reg = P.day_reg[day]
    for k in ("up", "down"):
        m = reg == k
        out[f"n_{k}"] = int(m.sum())
        out[f"exp_{k}"] = float(r[m].mean()) if m.any() else np.nan
    if split == 0:
        h = P.day_half[day]
        out["exp_h1"] = float(r[h == 0].mean()) if (h == 0).any() else np.nan
        out["exp_h2"] = float(r[h == 1].mean()) if (h == 1).any() else np.nan
    return out


def train_gate(s):
    return (s["n"] >= 150 and s["days"] >= 60 and s["exp"] > 0 and s["exc_c"] > 0 and s["exc_e"] > 0
            and s.get("n_up", 0) >= 30 and s.get("n_down", 0) >= 30 and s["exp_up"] > 0 and s["exp_down"] > 0
            and s["exp_h1"] > 0 and s["exp_h2"] > 0)


def trade_frame(P: Panel, sd, k, r, c, e):
    return pd.DataFrame({"date": P.sd_date[sd], "symbol": P.sd_symbol[sd], "tod": P.slot_tod[k], "r": r,
                         "c": c, "e": e, "split": np.where(P.sd_split[sd] == 0, "train", "valid")})


class Sub:
    """Panel restricted to a subset of symbol-days (e.g. TRAIN only) for fast screening."""

    def __init__(self, P: Panel, sel):
        self.P, self.idx = P, np.flatnonzero(sel)
        self.nsd = len(self.idx)
        self.R = {o: P.R[o][self.idx] for o in OUTS}
        self.C = {o: P.C[o][self.idx] for o in OUTS}
        self.E = {o: P.E[o][self.idx] for o in OUTS}
        self.sd_day = P.sd_day[self.idx]
        self.dates, self.day_split, self.day_half, self.day_reg = P.dates, P.day_split, P.day_half, P.day_reg
        self.slot_tod = P.slot_tod
        self.win_mask = P.win_mask

    def ind(self, name):
        return self.P.ind(name)[self.idx]
