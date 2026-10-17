"""Shared data, cores, filters and scoring for the NS rework (PLAN.md). Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
SCR = Path(os.environ.get("NSSCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swarm1017/rework-ns"))
HERE = Path(__file__).resolve().parent

S = pd.read_parquet(SCR / "superset.parquet")
S["date"] = pd.to_datetime(S["date"]).dt.date
G = pd.read_parquet(SCR / "guard.parquet")
G["date"] = pd.to_datetime(G["date"]).dt.date
S = S.merge(G, on=["symbol", "date", "tod"], how="left")
S = S.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
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
rsi, prsi, rsi5, fo = col["rsi"], col["p_rsi"], col["rsi5"], col["fromOpen"]
sx, psx, vx, pvx = col["sma50_dist_pct"], col["p_sma50_dist_pct"], col["vwapDistPct"], col["p_vwapDistPct"]
with np.errstate(invalid="ignore"):
    SMAUP = (sx > 0) & (psx <= 0)
    SMADN = (sx < 0) & (psx >= 0)
    VWUP = (vx > 0) & (pvx <= 0)
BLK = {k: np.nan_to_num(col[c], nan=1.0) > 0.5 for k, c in (("k1.5", "blk15"), ("k2", "blk20"), ("k2.5", "blk25"))}

GEOMS = ("t1s1", "t05s1", "t1s05")
WINS = {"0950-1030": (950, 1030), "0950-1130": (950, 1130), "1130-1300": (1130, 1300), "1130-1500": (1130, 1500),
        "1300-1500": (1300, 1500), "0950-1500": (950, 1500)}
WM = {k: (tod >= a) & (tod <= b) for k, (a, b) in WINS.items()}
PSIDE = {"NS1": "long", "NS2": "short", "NS3": "short", "NS4": "short", "NS5": "long", "RW6G1": "short"}
PGEOM = {"NS1": "t05s1", "NS2": "t1s1", "NS3": "t1s1", "NS4": "t1s05", "NS5": "t1s1", "RW6G1": "t1s1"}
PWIN = {"NS1": "0950-1130", "NS2": "0950-1130", "NS3": "0950-1130", "NS4": "1130-1500", "NS5": "0950-1130",
        "RW6G1": "0950-1130"}
OPP = {"long": "short", "short": "long"}

# threshold grids (Stage A); parent point is PARENT[p]
GRID = {"NS1": [(a, b, c) for a in (35, 40, 45) for b in (70, 80, 90) for c in (1, 2, 3)],
        "NS2": [(a, b) for a in (50, 55, 60, 65, 70) for b in (1, 2, 3, 4)],
        "NS3": [(a, b) for a in (True, False) for b in (-1, -2, -3, -4)],
        "NS4": [(a, b) for a in (30, 35, 40) for b in (1, 2, 3)],
        "NS5": [(a, b) for a in (25, 30, 35) for b in (-1, -2, -3)],
        "RW6G1": [(a, b, c) for a in (2, 3, 4) for b in (55, 60, 65) for c in ("none", "k1.5", "k2", "k2.5")]}
PARENT = {"NS1": (40, 80, 2), "NS2": (60, 2), "NS3": (True, -2), "NS4": (30, 2), "NS5": (30, -2), "RW6G1": (3, 60, "k2")}
AXES = {"NS1": [(35, 40, 45), (70, 80, 90), (1, 2, 3)], "NS2": [(50, 55, 60, 65, 70), (1, 2, 3, 4)],
        "NS3": [(True, False), (-1, -2, -3, -4)], "NS4": [(30, 35, 40), (1, 2, 3)], "NS5": [(25, 30, 35), (-1, -2, -3)],
        "RW6G1": [(2, 3, 4), (55, 60, 65), ("none", "k1.5", "k2", "k2.5")]}


def core(p, th):
    with np.errstate(invalid="ignore"):
        if p == "NS1":
            a, b, c = th
            return (rsi <= a) & (prsi > a) & (rsi5 >= b) & (fo > c)
        if p == "NS2":
            a, b = th
            return SMAUP & (rsi >= a) & (fo > b)
        if p == "NS3":
            a, b = th
            m = VWUP & (fo < b)
            return m & (sx > 0) if a else m
        if p == "NS4":
            a, b = th
            return VWUP & (rsi <= a) & (fo > b)
        if p == "NS5":
            a, b = th
            return SMADN & (rsi <= a) & (fo < b)
        if p == "RW6G1":
            a, b, g = th
            m = SMAUP & (rsi >= b) & (fo > a)
            return m if g == "none" else m & ~BLK[g]
    raise KeyError(p)


def neighbours(p, th):
    out = []
    for i, ax in enumerate(AXES[p]):
        j = ax.index(th[i])
        for k in (j - 1, j + 1):
            if 0 <= k < len(ax):
                t = list(th)
                t[i] = ax[k]
                out.append(tuple(t))
    return out


ap = col["atrPct"]
lo_atr, hi_atr = np.nanquantile(ap[TRAIN], [1 / 3, 2 / 3])
spy = col["spy_fo"]
rel = fo - spy
with np.errstate(invalid="ignore"):
    F = {"gap<0": col["gap"] < 0, "gap>0": col["gap"] > 0, "gap<-1": col["gap"] < -1, "gap>1": col["gap"] > 1,
         "|gap|<1": np.abs(col["gap"]) < 1,
         "vwap<0": vx < 0, "vwap>0": vx > 0, "rvol>=1.5": col["volumeRatio"] >= 1.5, "rvol<1": col["volumeRatio"] < 1,
         "atr_lo": ap <= lo_atr, "atr_mid": (ap > lo_atr) & (ap < hi_atr), "atr_hi": ap >= hi_atr,
         "Mon": DOW == 0, "Tue": DOW == 1, "Wed": DOW == 2, "Thu": DOW == 3, "Fri": DOW == 4, "notMon": DOW != 0,
         "notFri": DOW != 4,
         "spy>0": spy > 0, "spy<0": spy < 0, "spy>.5": spy > 0.5, "spy<-.5": spy < -0.5, "|spy|<.25": np.abs(spy) < 0.25,
         "brd>.5": col["breadth"] > 0.5, "brd<.5": col["breadth"] < 0.5, "rs>0": rel > 0, "rs<0": rel < 0,
         "slope>0": col["sma20_slope_pct"] > 0, "slope<0": col["sma20_slope_pct"] < 0,
         "nearHOD": col["dist_hod_atr"] < 0.25, "offHOD": col["dist_hod_atr"] > 0.5,
         "nearLOD": col["dist_lod_atr"] < 0.25, "offLOD": col["dist_lod_atr"] > 0.5,
         "heat<=-30": col["heat"] <= -30, "heat>=30": col["heat"] >= 30, "bp<0": col["buyPressure"] < 0,
         "bp>0": col["buyPressure"] > 0, "rsi5>=70": rsi5 >= 70, "rsi5<=30": rsi5 <= 30}
assert len(F) == 40
LIVE_CODE = {"spy>0", "spy<0", "spy>.5", "spy<-.5", "|spy|<.25", "brd>.5", "brd<.5", "rs>0", "rs<0"}


def pick(m, s, g, refire=False):
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


def trades(idx, s, g):
    return pd.DataFrame({"date": S["date"].to_numpy()[idx], "symbol": S["symbol"].to_numpy()[idx], "tod": tod[idx],
                         "r": col[f"p_{s}_{g}"][idx]})
