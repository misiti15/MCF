"""Shared loading, filter library and scoring for the rework-misc scan (PLAN.md). Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
SCR = Path(os.environ.get("MISCSCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swarm1017/rework-misc/sup"))
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
GEOMS = ("t1s1", "t05s1", "t1s05")
# atrPct tercile cuts: train rows of the IM universe sample (adv >= 95M, fixed bars), computed once (see cuts.json)
ATR_CUTS = None


def load(fam: str, pop: int) -> pd.DataFrame:
    parts = sorted((SCR / fam).glob("*.parquet"))
    S = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    ctx = pd.concat([pd.read_parquet(p) for p in sorted((SCR / "ctx").glob("*.parquet"))], ignore_index=True)
    keep = ["date", "tod", "breadth", "spy_fo", "spy_r30"] + [f"b{pop}_{s}_{g}" for s in ("short", "long") for g in GEOMS]
    S = S.merge(ctx[keep], on=["date", "tod"], how="left")
    S = S.rename(columns={f"b{pop}_{s}_{g}": f"b_{s}_{g}" for s in ("short", "long") for g in GEOMS})
    S["date"] = pd.to_datetime(S["date"]).dt.date
    assert not ((S.date >= LOCK[0]) & (S.date <= LOCK[1])).any()
    return S.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


class Fam:
    def __init__(self, S: pd.DataFrame, atr_cuts):
        self.S = S
        dts = pd.to_datetime(S["date"])
        self.train = (dts < "2026-01-01").to_numpy()
        self.dow = dts.dt.dayofweek.to_numpy()
        self.dcode, self.dates = pd.factorize(S["date"])
        self.nd = len(self.dates)
        self.symday = pd.factorize(S["symbol"].astype(str) + "|" + S["date"].astype(str))[0]
        self.tod = S["tod"].to_numpy(int)
        self.barix = ((self.tod // 100) * 60 + self.tod % 100 - 570) // 5
        self.col = {c: S[c].to_numpy(float) for c in S.columns if c not in ("symbol", "date") and S[c].dtype.kind in "fi"}
        self.F = filters(self.col, self.dow, atr_cuts)

    def win(self, a, b):
        return (self.tod >= a) & (self.tod <= b)

    def pick(self, m, side, g, refire=False):
        """First qualifying row per symbol-day (or refire chain, cooldown 1) for one side."""
        m = m & np.isfinite(self.col[f"p_{side}_{g}"])
        idx = np.flatnonzero(m)
        if not len(idx):
            return idx
        k = self.symday[idx]
        if not refire:
            return idx[np.r_[True, k[1:] != k[:-1]]]
        bi = self.barix[idx]
        newrun = np.r_[True, (k[1:] != k[:-1]) | (bi[1:] - bi[:-1] != 1)]
        rid = np.cumsum(newrun) - 1
        start = np.flatnonzero(newrun)
        off = np.arange(len(idx)) - start[rid]
        return idx[off % 2 == 0]

    def trades(self, parts):
        """parts: list of (idx, side, geom) -> (r, excess, dcode, train) concatenated."""
        r, ex, d, tr, ix = [], [], [], [], []
        for idx, side, g in parts:
            rr = self.col[f"p_{side}_{g}"][idx]
            r.append(rr)
            ex.append(rr - self.col[f"b_{side}_{g}"][idx])
            d.append(self.dcode[idx])
            tr.append(self.train[idx])
            ix.append(idx)
        return tuple(np.concatenate(v) if v else np.array([]) for v in (r, ex, d, tr, ix))

    def dstat(self, r, d):
        n = len(r)
        if n < 2:
            return n, (float(r.mean()) if n else np.nan), np.nan
        mu = r.mean()
        gs = np.bincount(d, weights=r, minlength=self.nd)
        gn = np.bincount(d, minlength=self.nd)
        se = np.sqrt(((gs - gn * mu) ** 2).sum()) / n
        return n, float(mu), float(mu / se) if se > 0 else np.nan

    def score(self, parts):
        r, ex, d, tr, _ = self.trades(parts)
        out = {}
        tr = tr.astype(bool)
        for lab, sel in (("tr", tr), ("va", ~tr), ("all", np.ones(len(r), bool))):
            n, mu, t = self.dstat(r[sel], d[sel])
            _, xm, xt = self.dstat(ex[sel], d[sel])
            out.update({f"n_{lab}": n, f"exp_{lab}": mu, f"t_{lab}": t, f"xs_{lab}": xm, f"xt_{lab}": xt})
        return out


def filters(col, dow, atr_cuts):
    ap = col["atrPct"]
    lo, hi = atr_cuts
    vw, fo, gap, spy, brd = col["vwapDistPct"], col["fromOpen"], col["gap"], col["spy_fo"], col["breadth"]
    with np.errstate(invalid="ignore"):
        F = {"gap<0": gap < 0, "gap>0": gap > 0, "gap<-1": gap < -1, "gap>1": gap > 1,
             "fo<0": fo < 0, "fo>0": fo > 0, "fo<-1": fo < -1, "fo>1": fo > 1,
             "vwap<0": vw < 0, "vwap>0": vw > 0, "rvol>=1.5": col["volumeRatio"] >= 1.5, "rvol<1": col["volumeRatio"] < 1,
             "atr_lo": ap <= lo, "atr_hi": ap >= hi,
             "Mon": dow == 0, "Tue": dow == 1, "Wed": dow == 2, "Thu": dow == 3, "Fri": dow == 4, "notMon": dow != 0, "notFri": dow != 4,
             "spy>0": spy > 0, "spy<0": spy < 0, "spy>0.5": spy > 0.5, "spy<-0.5": spy < -0.5,
             "brd>.5": brd > 0.5, "brd<.5": brd < 0.5,
             "slope>0": col["sma20_slope_pct"] > 0, "slope<0": col["sma20_slope_pct"] < 0,
             "nearHOD": col["dist_hod_atr"] < 0.25, "offHOD": col["dist_hod_atr"] > 0.5,
             "nearLOD": col["dist_lod_atr"] < 0.25, "offLOD": col["dist_lod_atr"] > 0.5,
             "sma50>0": col["sma50_dist_pct"] > 0, "sma50<0": col["sma50_dist_pct"] < 0,
             "rsi<30": col["rsi"] < 30, "rsi>70": col["rsi"] > 70}
    assert len(F) == 37
    return F


CODE_NEEDED = {"spy>0", "spy<0", "spy>0.5", "spy<-0.5", "brd>.5", "brd<.5"}
