"""Shared data, masks, filters and scoring for the MF rework (PLAN.md).
Educational only - not financial advice."""
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import os
SCR = Path(os.environ.get("MFSCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swarm1017/rework-mf"))
HERE = Path(__file__).resolve().parent

S = pd.read_parquet(SCR / "superset.parquet")
S["date"] = pd.to_datetime(S["date"]).dt.date
assert not ((S.date >= pd.Timestamp("2024-11-01").date()) & (S.date <= pd.Timestamp("2025-02-28").date())).any()
N = len(S)
dts = pd.to_datetime(S["date"])
TRAIN = (dts < "2026-01-01").to_numpy()
DOW = dts.dt.dayofweek.to_numpy()
dcode, dates = pd.factorize(S["date"])
ND = len(dates)
symday = pd.factorize(S["symbol"].astype(str) + "|" + S["date"].astype(str))[0]
tod = S["tod"].to_numpy(int)
barix = ((tod // 100) * 60 + tod % 100 - 570) // 5
col = {c: S[c].to_numpy(float) for c in S.columns if c not in ("symbol", "date")}
heat, bp, vw, rsi, rsi5 = col["heat"], col["buyPressure"], col["vwapDistPct"], col["rsi"], col["rsi5"]
SG = [(s, g) for s in ("short", "long") for g in ("t1s1", "t05s1", "t1s05")]
WINS = {"0950-1030": (950, 1030), "0950-1100": (950, 1100), "1100-1300": (1100, 1300), "1300-1500": (1300, 1500),
        "0950-1500": (950, 1500)}
WM = {k: (tod >= a) & (tod <= b) for k, (a, b) in WINS.items()}
PWIN = {"MF1": "0950-1030", "MF2": "0950-1100", "MF3": "0950-1100", "MF4": "0950-1100", "MF5": "0950-1500"}
PGEOM = {"MF1": "t1s05", "MF2": "t1s05", "MF3": "t1s1", "MF4": "t05s1", "MF5": "t1s1"}

ap = col["atrPct"]
lo_atr, hi_atr = np.nanquantile(ap[TRAIN], [1 / 3, 2 / 3])
rel = col["fromOpen"] - col["spy_fo"]
with np.errstate(invalid="ignore"):
    F = {"gap<0": col["gap"] < 0, "gap>0": col["gap"] > 0, "gap<-1": col["gap"] < -1, "gap>1": col["gap"] > 1,
         "fo<0": col["fromOpen"] < 0, "fo>0": col["fromOpen"] > 0, "fo<-1": col["fromOpen"] < -1, "fo>1": col["fromOpen"] > 1,
         "vwap<0": vw < 0, "vwap>0": vw > 0, "rvol>=1.5": col["volumeRatio"] >= 1.5, "rvol<1": col["volumeRatio"] < 1,
         "atr_lo": ap <= lo_atr, "atr_hi": ap >= hi_atr,
         "Mon": DOW == 0, "Tue": DOW == 1, "Wed": DOW == 2, "Thu": DOW == 3, "Fri": DOW == 4, "notMon": DOW != 0, "notFri": DOW != 4,
         "spy>0": col["spy_fo"] > 0, "spy<0": col["spy_fo"] < 0, "brd>.5": col["breadth"] > 0.5, "brd<.5": col["breadth"] < 0.5,
         "rs>0": rel > 0, "rs<0": rel < 0, "slope>0": col["sma20_slope_pct"] > 0, "slope<0": col["sma20_slope_pct"] < 0,
         "nearHOD": col["dist_hod_atr"] < 0.25, "offHOD": col["dist_hod_atr"] > 0.5,
         "sma50>0": col["sma50_dist_pct"] > 0, "sma50<0": col["sma50_dist_pct"] < 0}
assert len(F) == 33


def core(p, h, b, x):
    with np.errstate(invalid="ignore"):
        m = (heat <= h) & (bp < b)
        if p == "MF1":
            m &= vw > x
        elif p == "MF2":
            m &= (rsi >= x) & (rsi <= x + 10)
        elif p in ("MF3",):
            m &= rsi5 > x
        elif p == "MF5":
            m &= (vw > 0.05) & (rsi5 > x)
    return m


PARENT = {"MF1": (-30, -0.25, 0.05), "MF2": (-30, -0.25, 55), "MF3": (-30, -0.25, 70), "MF4": (-40, -0.25, None),
          "MF5": (-30, -0.25, 70)}
HGRID = {p: ([-30, -40, -50, -60] if p == "MF4" else [-20, -30, -40, -50]) for p in PARENT}
BGRID = [-0.15, -0.25, -0.35, -0.50]
XGRID = {"MF1": [0, 0.05, 0.25], "MF2": [50, 55, 60], "MF3": [60, 70, 80], "MF4": [None], "MF5": [60, 70, 80]}


def pick(m, s, g, refire):
    p = col[f"p_{s}_{g}"]
    m = m & np.isfinite(p)
    idx = np.flatnonzero(m)
    if not len(idx):
        return idx
    k = symday[idx]
    if not refire:
        return idx[np.r_[True, k[1:] != k[:-1]]]
    bi = barix[idx]
    newrun = np.r_[True, (k[1:] != k[:-1]) | (bi[1:] - bi[:-1] != 1)]
    rid = np.cumsum(newrun) - 1
    start = np.flatnonzero(newrun)
    off = np.arange(len(idx)) - start[rid]
    return idx[off % 2 == 0]


def dstat(r, d):
    n = len(r)
    if n < 2:
        return n, (float(r.mean()) if n else np.nan), np.nan
    mu = r.mean()
    gs = np.bincount(d, weights=r, minlength=ND)
    gn = np.bincount(d, minlength=ND)
    se = np.sqrt(((gs - gn * mu) ** 2).sum()) / n
    return n, float(mu), float(mu / se) if se > 0 else np.nan


def score(idx, s, g):
    r = col[f"p_{s}_{g}"][idx]
    ex = r - col[f"b_{s}_{g}"][idx]
    d = dcode[idx]
    tr = TRAIN[idx]
    out = {}
    for lab, sel in (("tr", tr), ("va", ~tr), ("all", slice(None))):
        n, mu, t = dstat(r[sel], d[sel])
        _, xm, xt = dstat(ex[sel], d[sel])
        out.update({f"n_{lab}": n, f"exp_{lab}": mu, f"t_{lab}": t, f"xs_{lab}": xm, f"xt_{lab}": xt})
    return out


