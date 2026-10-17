"""Shared data, filters and scoring for the CWT14 rework (PLAN.md). Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y"), str(HERE)]
from build import EXITS, LEVELS, PS  # noqa: E402

SCR = Path(os.environ.get("CWSCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swarm1017/rework-cwt14"))
EV = pd.concat([pd.read_parquet(p) for p in sorted(SCR.glob("events_*.parquet"))], ignore_index=True)
RW = pd.concat([pd.read_parquet(p) for p in sorted(SCR.glob("rows_*.parquet"))], ignore_index=True)
RW["date"] = pd.to_datetime(RW["date"]).dt.date
RW["ri"] = np.arange(len(RW))
EV = EV.merge(RW[["month", "fi", "ri"]], on=["month", "fi"], how="left")
assert EV["ri"].notna().all()
assert not ((RW.date >= pd.Timestamp("2024-11-01").date()) & (RW.date <= pd.Timestamp("2025-02-28").date())).any()
# events sorted by row (symbol-day contiguous within a month, tod ascending)
EV = EV.sort_values(["ri", "L", "p"], kind="mergesort").reset_index(drop=True)
ri = EV["ri"].to_numpy()
evL, evP, evK, evV, evD, evO = (EV[k].to_numpy() for k in ("L", "p", "ks", "v0", "depth", "ord"))

N = len(RW)
dts = pd.to_datetime(RW["date"])
TRAIN = (dts < "2026-01-01").to_numpy()
DOW = dts.dt.dayofweek.to_numpy()
dcode, dates = pd.factorize(RW["date"])
ND = len(dates)
symday = pd.factorize(RW["symbol"].astype(str) + "|" + RW["date"].astype(str))[0]
tod = RW["tod"].to_numpy(int)
barix = ((tod // 100) * 60 + tod % 100 - 570) // 5
col = {c: RW[c].to_numpy(float) for c in RW.columns if c not in ("symbol", "date", "month")}

NAT = {"PDL": "long", "PDH": "short", "ORL": "long", "ORH": "short"}
OPP = {"long": "short", "short": "long"}
WINS = {"0950-1030": (950, 1030), "0950-1130": (950, 1130), "1030-1300": (1030, 1300), "1130-1500": (1130, 1500),
        "1300-1500": (1300, 1500), "0950-1500": (950, 1500)}
WM = {k: (tod >= a) & (tod <= b) for k, (a, b) in WINS.items()}
KS = (1, 2, 3, 5)
VOLS = ("any", "v<1", "v<.7", "v>=1", "v>=1.5")

PARENTS = {  # name: (level, p, vol, side, window)
    "pdl-p10-long": ("PDL", 0.10, "any", "long", "0950-1500"),
    "pdl-p05-long": ("PDL", 0.05, "any", "long", "0950-1500"),
    "pdl-p10-lowvol-long": ("PDL", 0.10, "v<1", "long", "0950-1500"),
    "pdl-p05-lowvol-long": ("PDL", 0.05, "v<1", "long", "0950-1500"),
    "pdh-p10-short": ("PDH", 0.10, "any", "short", "0950-1200"),
    "pdh-p10-lowvol-short": ("PDH", 0.10, "v<1", "short", "0950-1500"),
    "pdh-p05-lowvol-short": ("PDH", 0.05, "v<1", "short", "0950-1500"),
    "orl-p10-long": ("ORL", 0.10, "any", "long", "0950-1200"),
    "orl-p05-long": ("ORL", 0.05, "any", "long", "0950-1500"),
    "orl-p10-lowvol-long": ("ORL", 0.10, "v<1", "long", "0950-1500"),
    "orl-p05-lowvol-long": ("ORL", 0.05, "v<1", "long", "0950-1500"),
}
WM["0950-1200"] = (tod >= 950) & (tod <= 1200)


def volmask(v, vol):
    with np.errstate(invalid="ignore"):
        return {"any": np.ones(len(v), bool), "v<1": v < 1, "v<.7": v < 0.7, "v>=1": v >= 1, "v>=1.5": v >= 1.5}[vol]


def core_ev(L, p, k, vol):
    """event mask for core (level name, p value, k, vol)."""
    li, pi = LEVELS.index(L), PS.index(p)
    return (evL == li) & (evP == pi) & (evK <= k) & volmask(evV, vol)


def core_rows(L, p, k, vol, extra_ev=None):
    m = core_ev(L, p, k, vol)
    if extra_ev is not None:
        m &= extra_ev
    return np.unique(ri[m])          # sorted row indices


# ------------------------------------------------------------------------------------------------ filters (rows)
ap = col["atrPct"]
lo_atr, hi_atr = np.nanquantile(ap[TRAIN], [1 / 3, 2 / 3])
spy = col["spy_fo"]
rel = col["fromOpen"] - spy
c_ = col["close"]
with np.errstate(invalid="ignore"):
    FR = {"gap<-1": col["gap"] < -1, "gap<0": col["gap"] < 0, "gap>0": col["gap"] > 0, "gap>1": col["gap"] > 1,
          "|gap|<1": np.abs(col["gap"]) < 1, "|gap|>=2": np.abs(col["gap"]) >= 2,
          "vwap>0": col["vwapDistPct"] > 0, "vwap<0": col["vwapDistPct"] < 0,
          "rvol>=1.5": col["volumeRatio"] >= 1.5, "rvol<1": col["volumeRatio"] < 1,
          "atr_lo": ap <= lo_atr, "atr_mid": (ap > lo_atr) & (ap < hi_atr), "atr_hi": ap >= hi_atr,
          "Mon": DOW == 0, "Tue": DOW == 1, "Wed": DOW == 2, "Thu": DOW == 3, "Fri": DOW == 4, "notMon": DOW != 0,
          "notFri": DOW != 4,
          "spy>0": spy > 0, "spy<0": spy < 0, "spy>.5": spy > 0.5, "spy<-.5": spy < -0.5, "|spy|<.25": np.abs(spy) < 0.25,
          "brd>.5": col["breadth"] > 0.5, "brd<.5": col["breadth"] < 0.5, "brd>.6": col["breadth"] > 0.6,
          "brd<.4": col["breadth"] < 0.4, "rs>0": rel > 0, "rs<0": rel < 0,
          "fo>0": col["fromOpen"] > 0, "fo<0": col["fromOpen"] < 0, "fo>1": col["fromOpen"] > 1, "fo<-1": col["fromOpen"] < -1,
          "rsi<40": col["rsi"] < 40, "rsi>60": col["rsi"] > 60, "rsi5>=70": col["rsi5"] >= 70, "rsi5<=30": col["rsi5"] <= 30,
          "heat>=30": col["heat"] >= 30, "heat<=-30": col["heat"] <= -30,
          "slope>0": col["sma20_slope_pct"] > 0, "slope<0": col["sma20_slope_pct"] < 0,
          "ema>0": col["emaDiff"] > 0, "ema<0": col["emaDiff"] < 0,
          "adv>=250M": col["adv20"] >= 250e6, "px>=20": c_ >= 20}
# event-level filters (depend on the core)
EVF = ("depth>=.3", "depth<.15", "ord1", "otherlvl_below", "otherlvl_above")
LIVE_CODE = {"spy>0", "spy<0", "spy>.5", "spy<-.5", "|spy|<.25", "brd>.5", "brd<.5", "brd>.6", "brd<.4", "rs>0", "rs<0"}
FILTERS = list(FR) + list(EVF)
assert len(FILTERS) == 52, len(FILTERS)


def evfilter(name, L):
    """event mask for an event-level filter; 'other level' = the OR level for PD cores, the PD level for OR cores
    (same side: low levels for PDL/ORL, high levels for PDH/ORH); NaN level (before 10:05) counts as False."""
    if name == "depth>=.3":
        return evD >= 0.3
    if name == "depth<.15":
        return evD < 0.15
    if name == "ord1":
        return evO == 1
    other = {"PDL": "orl", "ORL": "pdl", "PDH": "orh", "ORH": "pdh"}[L]
    lv = col[other][ri]
    cc = c_[ri]
    with np.errstate(invalid="ignore"):
        return cc < lv if name == "otherlvl_below" else cc > lv


# ------------------------------------------------------------------------------------------------ picking / scoring
def pick(rows, refire=False):
    """rows: sorted row indices of qualifying bars. First per symbol-day, or the refire chain (cooldown 1 = live
    refire_select over decision bars)."""
    if not len(rows):
        return rows
    k = symday[rows]
    if not refire:
        return rows[np.r_[True, k[1:] != k[:-1]]]
    return rows[_chain(k, barix[rows])]


@numba.njit(cache=True)
def _chain(k, bi):
    keep = np.zeros(len(k), np.bool_)
    lastk, lastb = -1, -99
    for j in range(len(k)):
        if k[j] == lastk and bi[j] - lastb <= 1:
            continue
        keep[j] = True
        lastk, lastb = k[j], bi[j]
    return keep


def dstat(r, d):
    n = len(r)
    if n < 2:
        return n, (float(r.mean()) if n else np.nan), np.nan
    mu = r.mean()
    gs = np.bincount(d, weights=r, minlength=ND)
    gn = np.bincount(d, minlength=ND)
    se = np.sqrt(((gs - gn * mu) ** 2).sum()) / n
    return n, float(mu), float(mu / se) if se > 0 else np.nan


def score(idx, s, x):
    r = col[f"o_{s}_{x}"][idx].astype(float)
    ok = np.isfinite(r)
    idx, r = idx[ok], r[ok]
    ex = r - col[f"b_{s}_{x}"][idx]
    d = dcode[idx]
    tr = TRAIN[idx]
    out = {}
    for lab, sel in (("tr", tr), ("va", ~tr), ("all", slice(None))):
        n, mu, t = dstat(r[sel], d[sel])
        _, xm, xt = dstat(ex[sel], d[sel])
        out.update({f"n_{lab}": n, f"exp_{lab}": mu, f"t_{lab}": t, f"xs_{lab}": xm, f"xt_{lab}": xt})
    return out


def trades(idx, s, x):
    r = col[f"o_{s}_{x}"][idx].astype(float)
    ok = np.isfinite(r)
    return pd.DataFrame({"date": RW["date"].to_numpy()[idx[ok]], "symbol": RW["symbol"].to_numpy()[idx[ok]],
                         "tod": tod[idx[ok]], "r": r[ok], "ri": idx[ok]})


def frows_for(L, p, k, vol, filters=""):
    """qualifying rows of core (L, p, k, vol) with '+'-joined filters (row filters on the bar, event filters on the
    core's event at that bar)."""
    fl = [f for f in filters.split("+") if f] if filters else []
    evm = None
    for f in fl:
        if f not in FR:
            m = evfilter(f, L)
            evm = m if evm is None else (evm & m)
    rows = core_rows(L, p, k, vol, evm)
    for f in fl:
        if f in FR:
            rows = rows[FR[f][rows]]
    return rows
