"""rework-cwt scan: grids A / B / C of PLAN.md on the event tables from build.py. Educational only - not financial advice.

    python scan.py <scratch_dir>        -> scan_all.csv.gz (every configuration, empty ones included), counts.json
Train = 2024-10 + 2025-03..2025-12, valid = 2026-01-01..2026-10-07. The locked block is never in the event tables.
Rows within the live earnings blackout (4 trading days either side of a report) are dropped (config/default.yaml).
"""
import itertools
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y")]
import lib  # noqa: E402

SCR = Path(sys.argv[1]) if __name__ == "__main__" else None
EX7 = ["t1s1", "t05s1", "t1s05", "t05s05", "so1", "so05", "tr1"]
EXB = ["t1s1", "t05s1", "t1s05", "so1", "so05", "tr1"]
WG = [(950, 1030), (1030, 1130), (1130, 1300), (1300, 1500), (950, 1500)]
WA7 = [(1030, 1130), (1130, 1300), (1300, 1500), (1030, 1500)]
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())


# ------------------------------------------------------------------------------------------------ data
def load(scr):
    parts = sorted(Path(scr).glob("ev_*.parquet"))
    S = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    S["date"] = pd.to_datetime(S["date"]).dt.date
    assert not ((S.date >= LOCK[0]) & (S.date <= LOCK[1])).any()
    S = S[~S["black"].astype(bool)].sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    atr = np.concatenate([np.load(p) for p in sorted(Path(scr).glob("atr_*.npy")) if p.stem[4:] < "2026-01"])
    cuts = tuple(np.nanquantile(atr, [1 / 3, 2 / 3]))
    return S, cuts


def families():
    """name -> list of variants: (vid, params dict, parent flag, parent side, parent window, parent exit, mask fn)."""
    F = {}
    v = []
    for bi, (a, dt, tg) in enumerate([(a, dt, tg) for a in (1.0, 1.5, 2.0, 2.5, 3.0) for dt in (0.3, 0.4, 0.5) for tg in (1, 2)]):
        par = dt == 0.4 and a in (1.5, 2.5)
        w = (1030, 1500) if tg == 2 else (950, 1500)
        ex = "t1s05" if (tg == 1 and a == 1.5) else "t1s1"
        v.append((f"a{a}-d{dt}-T{tg}", {"a": a, "d": dt, "T": tg}, par, "short", w, ex,
                  lambda S, bi=bi: ((S["b1bits"].to_numpy() >> bi) & 1 == 1) & S["p95"].to_numpy(bool)))
    F["B1"] = v
    v = []
    for sd in ("above", "below"):
        for z in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
            ps = "short" if sd == "above" else "long"
            par = z in (0.5, 0.75)
            w = (950, 1500) if (sd == "below" and z >= 0.75) else (1100, 1500)
            ex = "t05s1" if (sd == "below" and z <= 0.5) else "t1s1"
            col = "b2zs" if sd == "above" else "b2zl"
            v.append((f"{sd}-z{z}", {"sd": sd, "z": z}, par, ps, w, ex,
                      lambda S, col=col, z=z: (S[col].to_numpy(float) >= z - 1e-9) & S["p95"].to_numpy(bool)))
    F["B2"] = v
    v = []
    for k in (2, 3, 4, 6, 8):
        for tc in (2, 3, 4):
            par = tc == 3 and k in (4, 6)
            v.append((f"k{k}-tc{tc}", {"k": k, "tc": tc}, par, "long", (950, 1130), "t1s05" if k == 6 else "t05s1",
                      lambda S, k=k, tc=tc: (S[f"b4a{k}"].to_numpy() >= tc) & S["p95"].to_numpy(bool)))
    F["B4a"] = v
    v = []
    for s in (0.5, 1.0, 1.5, 2.0):
        for lo, hi in ((0.3, 0.5), (0.2, 0.6), (0.2, 0.4), (0.4, 0.6)):
            par = s == 1.0 and (lo, hi) == (0.3, 0.5)
            v.append((f"s{s}-pb{lo}-{hi}", {"s": s, "pb": f"{lo}-{hi}"}, par, "long", (950, 1500), "t05s1",
                      lambda S, s=s, lo=lo, hi=hi: (S["b4bpush"].to_numpy(float) >= s - 1e-9) & (S["b4bd"].to_numpy(float) >= lo - 1e-9)
                      & (S["b4bd"].to_numpy(float) <= hi + 1e-9) & S["p95"].to_numpy(bool)))
    F["B4b"] = v
    v = []
    for bi, (m, vv) in enumerate([(m, vv) for m in (0.5, 0.75, 1.0, 1.25) for vv in (2, 3, 5, 8)]):
        par = m in (0.5, 0.75) and vv in (3, 5)
        v.append((f"m{m}-v{vv}", {"m": m, "v": vv}, par, "long", (950, 1500), "t05s1",
                  lambda S, bi=bi: ((S["b5bits"].to_numpy() >> bi) & 1 == 1) & S["p95"].to_numpy(bool)))
    F["B5"] = v
    v = []
    for g in (3, 5, 7, 10, 15):
        for tg in (1, 2):
            par = g in (5, 10)
            ex = "t1s05" if (g == 5 and tg == 1) else "S"
            v.append((f"g{g}-T{tg}", {"g": g, "T": tg}, par, "short", (1030, 1500), ex,
                      lambda S, g=g, tg=tg: S["a7t1" if tg == 1 else "a7t2"].to_numpy(bool) & (S["gap"].to_numpy(float) <= -g)))
    F["A7"] = v
    return F


def filters(S, cuts):
    col = lambda c: S[c].to_numpy(float)  # noqa: E731
    dow = pd.to_datetime(S["date"]).dt.dayofweek.to_numpy()
    spy, brd, sg, rv, vw, gap, ap, fo = (col("spy_fo"), col("breadth"), col("spy_gap"), col("volumeRatio"),
                                         col("vwapDistPct"), col("gap"), col("atrPct"), col("fromOpen"))
    with np.errstate(invalid="ignore"):
        F = {"spy>0": spy > 0, "spy<0": spy < 0, "spy>.3": spy > 0.3, "spy<-.3": spy < -0.3,
             "brd>.5": brd > 0.5, "brd<.5": brd < 0.5, "brd>.6": brd > 0.6, "brd<.4": brd < 0.4,
             "spygap>0": sg > 0, "spygap<0": sg < 0,
             "rvol>=1.5": rv >= 1.5, "rvol>=2": rv >= 2, "rvol<1": rv < 1, "vwap>0": vw > 0, "vwap<0": vw < 0,
             "gap>0": gap > 0, "gap<0": gap < 0, "|gap|<1": np.abs(gap) < 1, "gap>2": gap > 2, "gap<-2": gap < -2,
             "atr_lo": ap <= cuts[0], "atr_mid": (ap > cuts[0]) & (ap < cuts[1]), "atr_hi": ap >= cuts[1],
             "Mon": dow == 0, "Tue": dow == 1, "Wed": dow == 2, "Thu": dow == 3, "Fri": dow == 4,
             "fo>0": fo > 0, "fo<0": fo < 0, "fo>1": fo > 1, "fo<-1": fo < -1,
             "slope>0": col("sma20_slope_pct") > 0, "slope<0": col("sma20_slope_pct") < 0,
             "rsi<30": col("rsi") < 30, "rsi>70": col("rsi") > 70,
             "sma50>0": col("sma50_dist_pct") > 0, "sma50<0": col("sma50_dist_pct") < 0,
             "spy~fo": spy * fo > 0, "spy!fo": spy * fo < 0}
    assert len(F) == 40
    return F


CODE_NEEDED = {"spy>0", "spy<0", "spy>.3", "spy<-.3", "brd>.5", "brd<.5", "brd>.6", "brd<.4", "spygap>0", "spygap<0",
               "spy~fo", "spy!fo"}


# ------------------------------------------------------------------------------------------------ picking
@numba.njit(cache=True)
def _pick(idx, symday, barix, valid, refire):
    out = np.empty(len(idx), np.int64)
    n = 0
    lastk = -1
    lastb = -1000
    done = False
    for j in range(len(idx)):
        i = idx[j]
        k = symday[i]
        if k != lastk:
            lastk = k
            lastb = -1000
            done = False
        if done:
            continue
        if refire:
            if barix[i] - lastb <= 1:
                continue
            if not valid[i]:
                continue
            out[n] = i
            n += 1
            lastb = barix[i]
        else:
            done = True          # live: only the first hit of the day; an untradeable first hit means no trade
            if valid[i]:
                out[n] = i
                n += 1
    return out[:n]


class Ctx:
    def __init__(self, S, base):
        self.S = S
        self.symday = pd.factorize(S["symbol"].astype(str) + "|" + S["date"].astype(str))[0].astype(np.int64)
        tod = S["tod"].to_numpy(np.int64)
        self.tod = tod
        self.barix = (((tod // 100) * 60 + tod % 100 - 570) // 5).astype(np.int64)
        self.dcode, self.dates = pd.factorize(S["date"])
        self.nd = len(self.dates)
        dts = pd.to_datetime(pd.Series(self.dates))
        self.dtrain = (dts < "2026-01-01").to_numpy()
        reg = lib.regimes()["regime"]
        rg = pd.Series(self.dates).map(reg).to_numpy()
        self.dup, self.ddn = rg == "up", rg == "down"
        self.train = self.dtrain[self.dcode]
        self.mcode, self.months = pd.factorize(pd.PeriodIndex(pd.to_datetime(S["date"]), freq="M"))
        self.wfm = np.array([str(m) >= "2025-06" for m in self.months])
        self.R = {}
        for side in ("long", "short"):
            for e in EX7 + (["S"] if side == "short" else []):
                c = f"o_{side}_{e}"
                if c in S:
                    r = S[c].to_numpy(np.float64)
                    b = S[f"{base}_{side}_{e}"].to_numpy(np.float64) if f"{base}_{side}_{e}" in S else np.zeros(len(S))
                    self.R[(side, e)] = (r, r - b)

    def pick(self, m, w, refire=False, valid=None):
        m = m & (self.tod >= w[0]) & (self.tod <= w[1])
        idx = np.flatnonzero(m)
        if valid is None:
            valid = np.ones(len(self.tod), np.bool_)
        return _pick(idx, self.symday, self.barix, valid, refire)

    def dstat(self, r, d):
        n = len(r)
        if n < 2:
            return n, (float(r.mean()) if n else np.nan), np.nan
        mu = r.mean()
        gs = np.bincount(d, weights=r, minlength=self.nd)
        gn = np.bincount(d, minlength=self.nd)
        se = np.sqrt(((gs - gn * mu) ** 2).sum()) / n
        return n, float(mu), (float(mu / se) if se > 0 else np.nan)

    def score(self, idx, side, e):
        r, x = self.R[(side, e)]
        r, x = r[idx], x[idx]
        ok = np.isfinite(r)
        idx, r, x = idx[ok], r[ok], x[ok]
        d = self.dcode[idx]
        tr = self.train[idx]
        o = {}
        for lab, sel in (("tr", tr), ("va", ~tr), ("all", None)):
            rr, dd, xx = (r, d, x) if sel is None else (r[sel], d[sel], x[sel])
            n, mu, t = self.dstat(rr, dd)
            o[f"n_{lab}"], o[f"exp_{lab}"], o[f"t_{lab}"] = n, mu, t
            o[f"xs_{lab}"] = float(xx.mean()) if len(xx) else np.nan
        _, _, o["xt_all"] = self.dstat(x, d)
        for lab, dm in (("up", self.dup), ("dn", self.ddn)):
            s = dm[d]
            o[f"n_{lab}"] = int(s.sum())
            o[f"exp_{lab}"] = float(r[s].mean()) if s.any() else np.nan
        mc = self.mcode[idx]
        cnt = np.bincount(mc, minlength=len(self.months))
        sm = np.bincount(mc, weights=r, minlength=len(self.months))
        okm = self.wfm & (cnt >= 10)
        o["wf"] = float((sm[okm] > 0).mean()) if okm.any() else np.nan
        o["days"] = int(len(np.unique(d)))
        return o


def run_family(args):
    scr, fam = args
    S, cuts = load(scr)
    V = families()[fam]
    m_any = np.zeros(len(S), bool)
    masks = {}
    for vid, prm, par, ps, pw, pe, fn in V:
        masks[vid] = fn(S)
        m_any |= masks[vid]
    S = S[m_any].reset_index(drop=True)
    for k in masks:
        masks[k] = masks[k][m_any]
    base = "ball" if fam == "A7" else "b95"
    C = Ctx(S, base)
    F = filters(S, cuts)
    validS = np.isfinite(C.R[("short", "S")][0]) if fam == "A7" else None
    rows = []
    W = WA7 if fam == "A7" else WG

    def add(stage, vid, side, e, w, pick, f1, f2, idx):
        o = C.score(idx, side, e) if len(idx) else {"n_all": 0}
        o.update({"fam": fam, "stage": stage, "vid": vid, "side": side, "exit": e, "win": f"{w[0]}-{w[1]}",
                  "pick": pick, "f1": f1, "f2": f2})
        rows.append(o)

    def exits_for(side, lst):
        return lst + (["S"] if fam == "A7" and side == "short" else [])

    for vid, prm, par, ps, pw, pe, fn in V:
        opp = "long" if ps == "short" else "short"
        m = masks[vid]
        # stage A
        for w in list(dict.fromkeys(W + [pw])):
            for pick in ("first", "refire"):
                ib = C.pick(m, w, pick == "refire")
                iS = C.pick(m, w, pick == "refire", validS) if validS is not None else None
                for side in (ps, opp):
                    for e in exits_for(side, EX7):
                        add("A", vid, side, e, w, pick, "", "", iS if e == "S" else ib)
        # stage B
        wb = list(dict.fromkeys([pw, (W[-1][0], 1500)]))
        for fk, fm in F.items():
            mm = m & fm
            for w in wb:
                ib = C.pick(mm, w)
                iS = C.pick(mm, w, False, validS) if validS is not None else None
                for side in (ps, opp):
                    for e in exits_for(side, EXB):
                        add("B", vid, side, e, w, "first", fk, "", iS if e == "S" else ib)
        # stage C (parents only)
        if par:
            ex = list(dict.fromkeys([pe, "t1s1", "t05s1"]))
            for f1, f2 in itertools.combinations(F, 2):
                mm = m & F[f1] & F[f2]
                ib = C.pick(mm, pw)
                iS = C.pick(mm, pw, False, validS) if validS is not None else None
                for e in ex:
                    add("C", vid, ps, e, pw, "first", f1, f2, iS if e == "S" else ib)
    out = pd.DataFrame(rows)
    out.to_parquet(Path(scr) / f"scan_{fam}.parquet", index=False)
    print(fam, len(S), len(out), flush=True)
    return fam, len(out)


if __name__ == "__main__":
    fams = sys.argv[2:] or ["B1", "B2", "B4a", "B4b", "B5", "A7"]
    with Pool(3) as p:
        res = p.map(run_family, [(str(SCR), f) for f in fams], chunksize=1)
    print(res)
