"""Shared data, cores, filters and scoring for the L3 + ST1-ST8 rework (PLAN.md). Educational only - not financial advice."""
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from stcore import AXES, PARENT, PGEOM, PSIDE, SRCWIN, ST, l3, points  # noqa: E402,F401

SCR = Path(os.environ.get("STSCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swarm1017/rework-st"))
S = pd.read_parquet(SCR / "superset.parquet")
S["date"] = pd.to_datetime(S["date"]).dt.date
_ap = json.load(open(SCR / "apoints.json"))
AM = np.unpackbits(np.load(SCR / "apoints.npy"), axis=1)[:, :len(_ap)].astype(bool)
ACOL = {(p, th): j for j, (p, th) in enumerate(_ap)}
assert len(AM) == len(S)
assert not ((S.date >= pd.Timestamp("2024-11-01").date()) & (S.date <= pd.Timestamp("2025-02-28").date())).any()
# superset is in month order, each month sorted by symbol/date/tod -> symbol-day rows are contiguous and in tod order
N = len(S)
dts = pd.to_datetime(S["date"])
TRAIN = (dts < "2026-01-01").to_numpy()
DOW = dts.dt.dayofweek.to_numpy()
dcode, dates = pd.factorize(S["date"])
ND = len(dates)
symday = pd.factorize(S["symbol"].astype(str) + "|" + S["date"].astype(str))[0]
tod = S["tod"].to_numpy(int)
barix = ((tod // 100) * 60 + tod % 100 - 570) // 5
col = {c: S[c].to_numpy(float) for c in S.columns if c not in ("symbol", "date", "big", "l3")}
L3OK = S["l3"].to_numpy(bool)

GEOMS = ("t1s1", "t05s1", "t1s05")
WINS = {"0950-1030": (950, 1030), "0950-1130": (950, 1130), "1135-1330": (1135, 1330), "1300-1430": (1300, 1430),
        "1335-1500": (1335, 1500), "0950-1500": (950, 1500)}
WM = {k: (tod >= a) & (tod <= b) for k, (a, b) in WINS.items()}
OPP = {"long": "short", "short": "long"}
PARENTS = list(PSIDE)


def core(p, th):
    if p in ST:
        return AM[:, ACOL[(p, repr(th))]]
    return l3(col, p, th) & L3OK


def neighbours(p, th):
    out = []
    for i, ax in enumerate(AXES[p]):
        j = ax.index(th[i])
        for k in (j - 1, j + 1):
            if 0 <= k < len(ax):
                t = list(th)
                t[i] = ax[k]
                t = tuple(t)
                if p in ("L3b", "L3c") and t[2] is None:
                    continue
                out.append(t)
    return out


def apoints(p):
    return points(p)


ap = col["atrPct"]
lo_atr, hi_atr = np.nanquantile(ap[TRAIN], [1 / 3, 2 / 3])
spy = col["spy_fo"]
rel = col["fromOpen"] - spy
rsi5 = col["rsi5"]
vx = col["vwapDistPct"]
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


def bcol(p, s, g):
    return col[f"{'b0' if p.startswith('L3') else 'b95'}_{s}_{g}"]


def score(idx, p, s, g):
    r = col[f"p_{s}_{g}"][idx].astype(float)
    ex = r - bcol(p, s, g)[idx]
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
                         "r": col[f"p_{s}_{g}"][idx].astype(float)})
