"""Shared data, parent cores, filter library and scoring for the RW-family rework (PLAN.md).
Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
SCR = Path(os.environ.get("RWSCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swarm1017/rework-rw"))
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
fam = col["fam"].astype(int)
heat, bp, rsi, rsi5, gap, fo = col["heat"], col["buyPressure"], col["rsi"], col["rsi5"], col["gap"], col["fromOpen"]
vw, pvw, s50, ps50, s20, bdiv, adv = (col["vwapDistPct"], col["p_vwapDistPct"], col["sma50_dist_pct"],
                                      col["p_sma50_dist_pct"], col["sma20_dist_pct"], col["bear_div"], col["adv20"])
SG = [(s, g) for s in ("short", "long") for g in ("t1s1", "t05s1", "t1s05")]
WINS = {"0950-1030": (950, 1030), "0950-1100": (950, 1100), "1100-1300": (1100, 1300), "1300-1500": (1300, 1500),
        "0950-1500": (950, 1500), "1110-1500": (1110, 1500)}
WM = {k: (tod >= a) & (tod <= b) for k, (a, b) in WINS.items()}
W5 = ["0950-1030", "0950-1100", "1100-1300", "1300-1500", "0950-1500"]
LINEAGE = {"RW1": "MF", "RW7": "MF", "RW3": "MF", "RW5": "MF", "RW2": "EXH", "EXH": "EXH", "RW4": "NS", "RW6": "NS",
           "G-MF2": "MF", "G-MF3": "MF", "G-EXH": "EXH", "G-RW4": "NS", "G-RW6": "NS"}
CWIN = {p: (["0950-1500", "1300-1500"] if p in ("RW2", "EXH") else ["0950-1500", "0950-1100"]) for p in LINEAGE}

ap = col["atrPct"]
lo_atr, hi_atr = np.nanquantile(ap[TRAIN], [1 / 3, 2 / 3])
rel = fo - col["spy_fo"]
with np.errstate(invalid="ignore"):
    F = {"gap<0": gap < 0, "gap>0": gap > 0, "gap<-1": gap < -1, "gap>1": gap > 1, "gap<-2": gap < -2, "gap>-1": gap > -1,
         "fo<0": fo < 0, "fo>0": fo > 0, "fo<-1": fo < -1, "fo>1": fo > 1,
         "vwap<0": vw < 0, "vwap>0": vw > 0, "rvol>=1.5": col["volumeRatio"] >= 1.5, "rvol<1": col["volumeRatio"] < 1,
         "atr_lo": ap <= lo_atr, "atr_hi": ap >= hi_atr,
         "Mon": DOW == 0, "Tue": DOW == 1, "Wed": DOW == 2, "Thu": DOW == 3, "Fri": DOW == 4, "notMon": DOW != 0, "notFri": DOW != 4,
         "spy>0": col["spy_fo"] > 0, "spy<0": col["spy_fo"] < 0, "spy<-.5": col["spy_fo"] < -0.5, "spy>.5": col["spy_fo"] > 0.5,
         "qqq>0": col["qqq_fo"] > 0, "qqq<0": col["qqq_fo"] < 0,
         "brd>.5": col["breadth"] > 0.5, "brd<.5": col["breadth"] < 0.5, "brd<.35": col["breadth"] < 0.35, "brd>.65": col["breadth"] > 0.65,
         "spygap>0": col["spy_gap"] > 0, "spygap<0": col["spy_gap"] < 0,
         "rs>0": rel > 0, "rs<0": rel < 0, "slope>0": col["sma20_slope_pct"] > 0, "slope<0": col["sma20_slope_pct"] < 0,
         "nearHOD": col["dist_hod_atr"] < 0.25, "offHOD": col["dist_hod_atr"] > 0.5,
         "nearLOD": col["dist_lod_atr"] < 0.25, "offLOD": col["dist_lod_atr"] > 0.5,
         "sma50>0": s50 > 0, "sma50<0": s50 < 0}
assert len(F) == 45
LIVE_CODE = {"spy>0", "spy<0", "spy<-.5", "spy>.5", "qqq>0", "qqq<0", "brd>.5", "brd<.5", "brd<.35", "brd>.65",
             "spygap>0", "spygap<0", "rs>0", "rs<0"}


def _ok(x):
    return np.isfinite(x)


def g_mf2(h, b, band, gp, a=95e6):
    with np.errstate(invalid="ignore"):
        m = (heat <= h) & (bp < b) & (adv >= a)
        if band is not None:
            m &= (rsi >= band) & (rsi <= band + 10)
        if gp is not None:
            m &= gap < gp
    return m


def g_mf3(h, b, r5, gp, a=95e6):
    with np.errstate(invalid="ignore"):
        m = (heat <= h) & (bp < b) & (adv >= a)
        if r5 is not None:
            m &= rsi5 > r5
        if gp is not None:
            m &= gap < gp
    return m


def g_exh(r5, sm, div, a):
    with np.errstate(invalid="ignore"):
        m = (rsi5 > r5) & (s20 > sm) & (adv >= a)
        if div:
            m &= bdiv > 0
    return m


def g_rw4(f, s5, a):
    with np.errstate(invalid="ignore"):
        m = (vw > 0) & (pvw <= 0) & (fo < f) & (adv >= a)
        if s5 == ">0":
            m &= s50 > 0
        elif s5 == "<0":
            m &= s50 < 0
    return m


def g_rw6(f, r, a):
    with np.errstate(invalid="ignore"):
        m = (s50 > 0) & (ps50 <= 0) & (fo > f) & (adv >= a)
        if r is not None:
            m &= rsi >= r
    return m


PARENT = {"RW1": lambda: g_mf2(-20, -0.35, 55, 0), "RW7": lambda: g_mf2(-20, -0.15, 55, 0),
          "RW3": lambda: g_mf3(-20, -0.35, 80, 0), "RW5": lambda: g_mf3(-30, -0.15, 80, 0),
          "RW2": lambda: g_exh(90, 1.0, True, 150e6), "EXH": lambda: g_exh(90, 1.0, True, 95e6),
          "RW4": lambda: g_rw4(-2, ">0", 150e6), "RW6": lambda: g_rw6(3, 60, 95e6)}
LIVE_REFIRE = {"RW1": None, "RW7": None, "RW3": None, "RW5": 6, "RW2": None, "EXH": None, "RW4": 1, "RW6": 1}
GRIDS = {
    "G-MF2": (g_mf2, [[-10, -20, -30, -40], [-0.15, -0.25, -0.35, -0.50], [50, 55, 60, None], [0, -1, None]]),
    "G-MF3": (g_mf3, [[-10, -20, -30, -40], [-0.15, -0.25, -0.35, -0.50], [70, 80, 90, None], [0, -1, None]]),
    "G-EXH": (g_exh, [[80, 85, 90, 95], [0.5, 1.0, 1.5, 2.0], [True, False], [95e6, 150e6, 300e6]]),
    "G-RW4": (g_rw4, [[-1, -2, -3], [">0", "any", "<0"], [95e6, 150e6]]),
    "G-RW6": (g_rw6, [[2, 3, 4], [50, 60, 70, None], [95e6, 150e6]]),
}


def pick(rows, s, g, refire=None):
    """rows: ascending indices into S (already masked). First qualifying bar per symbol-day, or the refire chain
    (LabStrategy.refire_select semantics; cooldown int)."""
    rows = rows[np.isfinite(col[f"p_{s}_{g}"][rows])]
    if not len(rows):
        return rows
    k = symday[rows]
    if refire is None:
        return rows[np.r_[True, k[1:] != k[:-1]]]
    if refire == 1:
        bi = barix[rows]
        newrun = np.r_[True, (k[1:] != k[:-1]) | (bi[1:] - bi[:-1] != 1)]
        rid = np.cumsum(newrun) - 1
        start = np.flatnonzero(newrun)
        off = np.arange(len(rows)) - start[rid]
        return rows[off % 2 == 0]
    out, lk, lb = [], -1, -10**9
    for r_, kk, bb in zip(rows, k, barix[rows]):
        if kk != lk:
            lk, lb = kk, -10**9
        if bb - lb > refire:
            out.append(r_)
            lb = bb
    return np.asarray(out, dtype=np.int64)


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
    return pd.DataFrame({"date": S["date"].to_numpy()[idx], "symbol": S["symbol"].to_numpy()[idx],
                         "tod": tod[idx], "r": col[f"p_{s}_{g}"][idx]})
