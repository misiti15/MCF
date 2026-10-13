"""dips1013 configuration -> trade set (day rows d, entry bars k), shared by score.py and report.py (PLAN.md).
Educational only - not financial advice."""
from __future__ import annotations

import numpy as np

import features as FT
from engine import NB, Data

EX_A = ("t1s1", "t05s1", "t1s05", "HTC", "SW-VWAP")
EX_B = ("t1s1", "t05s1", "t1s05", "HTC", "SL-VWAP", "SL-OPEN", "SL-HTC")
WIN = {"full": (3, 65), "am": (3, 17), "mid": (18, 41), "pm": (42, 65)}
GAPS = ("any", "notdn", "flat", "gup", "gdn")
DEPTH = [("p", 0.75), ("p", 1.0), ("p", 1.5), ("p", 2.0), ("a", 0.5), ("a", 0.75), ("a", 1.0)]
FILT_B = ("none", "spyup", "spynl", "spymid", "qqqmid", "idio", "sect", "vix", "trend", "pcl", "capd", "capr",
          "C1", "C2", "C3", "C4")
ENTRIES = ("E945", "E950", "E955", "PBH", "HL", "VR")


def have_mask(D: Data):
    return D.days["have"].to_numpy(bool) & np.isfinite(D.atr) & (D.atr > 0)


def first_true(M, lo, hi, have):
    sub = M[:, lo:hi + 1]
    k = np.argmax(sub, 1) + lo
    d = np.flatnonzero(sub.any(1) & have)
    return d, k[d]


def first_k(M, lo, hi):
    sub = M[:, lo:hi + 1]
    return np.where(sub.any(1), np.argmax(sub, 1) + lo, -1)


class PartA:
    def __init__(self, D: Data):
        self.D = D
        self.have = have_mask(D)
        self.OSL, self.T = FT.part_a(D)
        self.F = {"none": None, "spynl": FT.spy_nl(D)[D.sess], "pcl": (D.days["pcl"].to_numpy(float) >= 0.5)[:, None]}

    def trades(self, os_, L, trig, filt, win):
        M = self.OSL[(os_, L)] & self.T[trig]
        if self.F[filt] is not None:
            M = M & self.F[filt]
        lo, hi = WIN[win]
        return first_true(M, lo, hi, self.have)


class PartB:
    def __init__(self, D: Data):
        self.D = D
        self.have = have_mask(D)
        C, H, VW, LOD = D.C, D.H, D.VW, D.LOD
        with np.errstate(invalid="ignore"):
            pbh = C > FT.shift(H, 1)
            hl = (LOD >= FT.shift(LOD, 2) - 1e-12) & (C > FT.shift(C, 1))
            vr = (C > VW) & (FT.shift(C, 1) <= FT.shift(VW, 1))
        self.ENTRY = {"E945": (np.full(D.N, 2), 2), "E950": (np.full(D.N, 3), 3), "E955": (np.full(D.N, 4), 3),
                      "PBH": (first_k(pbh, 4, 8), 3), "HL": (first_k(hl, 4, 8), 3), "VR": (first_k(vr, 4, 8), 3)}
        g = D.gap
        self.GAP = {"any": np.ones(D.N, bool), "notdn": g > -1, "flat": np.abs(g) < 0.5, "gup": g >= 0.5, "gdn": g <= -1}
        self.spyfo, self.qqqmid, self.spymid = FT.mkt_fo(D, "SPY"), FT.mkt_mid(D, "QQQ"), FT.mkt_mid(D, "SPY")
        self.spynl = FT.spy_nl(D)
        self.vxxfo = FT.mkt_fo(D, "VXX")
        self.calm = D.m["VXX_calm_prior"].astype(float)
        sect = D.days["sector_etf"].fillna("").to_numpy()
        syms = [str(x) for x in D.m["syms"]]
        self.sectfo = np.full((D.N, NB), np.nan)
        for e in set(sect):
            if e and e in syms:
                idx = np.flatnonzero(sect == e)
                self.sectfo[idx] = FT.mkt_fo(D, e)[D.sess[idx]]
        self.trend = D.days["trend"].to_numpy(float) == 1
        self.pcl = D.days["pcl"].to_numpy(float) >= 0.5
        self.rv15 = D.days["rv15"].to_numpy(float)
        self.V = D.b["V"].astype(float)
        self._fcache = {}

    def filters(self, en):
        if en in self._fcache:
            return self._fcache[en]
        D, V = self.D, self.V
        k = self.ENTRY[en][0]
        kk = np.maximum(k, 0)
        rows = np.arange(D.N)
        s = D.sess
        sfo = self.spyfo[s, kk]
        stock_fo = D.C[rows, kk] / D.open0 - 1
        with np.errstate(invalid="ignore"):
            cv = np.where(np.arange(NB)[None, :] <= kk[:, None], V, -1)
            vmax, amax = cv.max(1), cv.argmax(1)
            ve = V[rows, kk]
            f = {"none": np.ones(D.N, bool), "spyup": sfo > 0, "spynl": self.spynl[s, kk], "spymid": self.spymid[s, kk],
                 "qqqmid": self.qqqmid[s, kk], "idio": sfo > stock_fo / 3, "sect": self.sectfo[rows, kk] >= sfo,
                 "vix": (self.calm[s] == 1) & (self.vxxfo[s, kk] <= 0), "trend": self.trend, "pcl": self.pcl,
                 "capd": (amax <= 2) & (ve <= 0.5 * vmax), "capr": (self.rv15 >= 2) & (ve < V[:, 0])}
        f["C1"] = f["spymid"] & f["trend"]
        f["C2"] = f["spymid"] & f["pcl"]
        f["C3"] = f["spymid"] & f["capd"]
        f["C4"] = f["spymid"] & f["sect"] & f["vix"]
        self._fcache[en] = f
        return f

    def dip(self, en, ref, unit, x):
        D = self.D
        kd = self.ENTRY[en][1]
        cd = D.C[:, kd]
        with np.errstate(invalid="ignore"):
            if unit == "p":
                mo, mp = (1 - cd / D.open0) * 100 >= x, (1 - cd / D.pc) * 100 >= x
            else:
                mo, mp = (D.open0 - cd) / D.atr >= x, (D.pc - cd) / D.atr >= x
        return mo if ref == "O" else (mp if ref == "PC" else (mo & mp))

    def base(self, en, ref, unit, x, gapc):
        ke = self.ENTRY[en][0]
        return self.dip(en, ref, unit, x) & self.GAP[gapc] & (ke >= 0) & self.have

    def trades(self, ref, unit, x, gapc, en, filt):
        d = np.flatnonzero(self.base(en, ref, unit, x, gapc) & self.filters(en)[filt])
        return d, self.ENTRY[en][0][d]
