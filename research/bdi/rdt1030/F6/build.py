"""rdt1030/F6 index-native build: F1-A / F3-A / F4 signals on QQQ / SPY, traded on 3x ETFs (or as themselves) with the
stop and target mapped by percentage; 1-min FVG variant on frames_tf/1min. Patched stop-first sim (F4 copy), K=5 random
control, per-month trade parquet in scratch. TRAIN+VALID only; HOLD months and the locked block are never loaded.
Educational only - not financial advice.

    python build.py check      # 1-min signal copy with (step 5, 0955) == F1 signals on 2025-06
    python build.py sanity     # 2025-06 signal features only (counts, R/ATR, cost/R, time); no outcome column
    python build.py [months]   # score months into scratch
"""
import os, sys, time, json, zlib, glob
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
import importlib.util
from pathlib import Path
import numba
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "research/bdi/top5_1028"), str(ROOT / "research/bdi/top5_1019"),
                str(ROOT / "research/bdi/gates1021/scripts")]
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
_argv = sys.argv[:]
sys.dont_write_bytecode = True  # do not write __pycache__ into the sibling folders
sys.argv = sys.argv[:1]  # sibling modules read sys.argv at import


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


F1 = _load("rdt_f1_build", HERE.parent / "F1/build.py")   # signals (F1-A), _cut patches
F3 = _load("rdt_f3_build", HERE.parent / "F3/build.py")   # trade1 / trade2 (F3-A)
F4 = _load("rdt_f4_build", HERE.parent / "F4/build.py")   # sim (epx-capable patched copy), seg_arrays, run_signal
sys.argv = _argv
from numba.core.caching import NullCache  # noqa
for _d in (F1.signals, F3.trade1, F3.trade2, F4.sim, F4._tgt, F4.signals):
    _d._cache = NullCache()  # no on-disk cache for dynamically loaded siblings (never write into ../F1, F3, F4)
import scan_1019 as SC  # noqa  (lib.load_month etc. already wrapped by the siblings' _cut)
from scan_1019 import lib, scan  # noqa
sim = F4.sim
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F6")
SCR.mkdir(parents=True, exist_ok=True)
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
HOLD = ("2026-04", "2026-05", "2026-06", "2026-10")
SEED, K_CTRL, G = 20261030, 5, 0.05
LEV = {"QQQ": ("TQQQ", "SQQQ"), "SPY": ("SPXL", "SPXS")}
ONE_MIN = Path("/home/user/MCF/research/history2y/data/frames_tf/1min")
COLS1 = ["symbol", "date", "tod", "high", "low", "close", "adv20", "atr_d", "gap"]  # never the outcome columns


@numba.njit(cache=True)
def signals_step(ss, se, h, l, c, mins, tod, atr, orh, orl, side, g, kmax, tod_hi, step, tod_lo):
    """Copy of ../F1/build.py signals with the bar step (minutes) and the earliest signal row as parameters.
    (step=5, tod_lo=955) reproduces F1 exactly (build.py check)."""
    out = np.full(len(ss), -1, np.int64)
    for s in range(len(ss)):
        a, z = ss[s], se[s]
        lvl = orh[s] if side == 1 else orl[s]
        if not np.isfinite(lvl):
            continue
        b = -1
        for i in range(a, z + 1):
            if tod[i] >= 950 and side * (c[i] - lvl) > 0:
                b = i
                break
        if b < 0:
            continue
        for i in range(b, min(b + kmax, z) + 1):
            if side * (c[i] - lvl) <= 0:
                break
            if tod[i] > tod_hi:
                break
            if tod[i] < tod_lo or i - 2 < a:
                continue
            if mins[i] - mins[i - 1] != step or mins[i - 1] - mins[i - 2] != step:
                continue
            gap = (l[i] - h[i - 2]) if side == 1 else (l[i - 2] - h[i])
            if gap >= g * atr[i] and gap >= 0.02:
                out[s] = i
                break
    return out


def segs(sym, dat):
    key = sym.astype(object) + "|" + dat.astype(object)
    new = np.r_[True, key[1:] != key[:-1]]
    ss = np.flatnonzero(new); se = np.r_[ss[1:] - 1, len(sym) - 1]
    return key, ss, se, np.cumsum(new) - 1


def or_levels(tod, h, l, seg, nseg, atr, rows):
    """OR high/low per segment from the given head-row tods (all of 0935/0940/0945 present, width >= 0.05 ATR)."""
    hd = np.isin(tod, [935, 940, 945])
    nh = pd.Series(hd.astype(int)).groupby(seg).sum().reindex(range(nseg), fill_value=0).to_numpy()
    sel = np.isin(tod, rows)
    g3 = pd.DataFrame({"seg": seg[sel], "h": h[sel], "l": l[sel]}).groupby("seg").agg(H=("h", "max"), L=("l", "min"))
    orh = np.full(nseg, np.nan); orl = np.full(nseg, np.nan)
    orh[g3.index] = g3["H"].to_numpy(); orl[g3.index] = g3["L"].to_numpy()
    satr = pd.Series(atr).groupby(seg).max().reindex(range(nseg)).to_numpy()
    with np.errstate(invalid="ignore"):
        bad = (nh != 3) | ~((orh - orl) >= 0.05 * satr)
    orh[bad] = np.nan; orl[bad] = np.nan
    return orh, orl


def load_1min(month, syms=None):
    assert month not in lib.LOCKED_MONTHS and month not in HOLD
    parts = sorted(glob.glob(str(ONE_MIN / f"month={month}" / "*.parquet")))
    d = pd.concat([pd.read_parquet(p, columns=COLS1) for p in parts], ignore_index=True)
    d["symbol"] = d["symbol"].astype(str); d["date"] = d["date"].astype(str)
    d = d[d["date"] <= CUT]
    assert not ((d["date"] >= "2024-11-01") & (d["date"] <= "2025-02-28")).any()
    if syms is not None:
        d = d[d["symbol"].isin(syms)]
    return d.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


class Month:
    """Everything one month needs: 5-min frames + paths, ETF row lookup, control pool."""

    def __init__(self, month):
        assert month not in lib.LOCKED_MONTHS and month not in HOLD
        self.month = month
        f, fh, P, dend, fh2P = SC.build_paths(month)
        ds = fh["date"].astype(str)
        assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
        assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
        sp = f[f["symbol"] == "SPY"]
        self.spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last()  # EOD: descriptive split only
        ctx = lib.load_context(month)
        self.qfo = pd.Series(ctx["qqq_fo"].to_numpy(float), index=ctx["date"].astype(str) + "|" + ctx["tod"].astype(str))
        del f, ctx
        self.fh, self.P, self.dend, self.fh2P, self.ds = fh, P, dend, fh2P, ds
        self.fsym, self.fdat = fh["symbol"].to_numpy(), ds.to_numpy()
        self.tod = fh["tod"].to_numpy(np.int64)
        self.h, self.l, self.c = (fh[k].to_numpy(float) for k in ("high", "low", "close"))
        self.atr = fh["atr_d"].to_numpy(float)
        adv = fh["adv20"].fillna(0).to_numpy(float)
        with np.errstate(invalid="ignore"):
            self.tier = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (self.c < 5), 3.0, 1.0)
        key, ss, se, seg = segs(self.fsym, self.fdat)
        self.key = key
        orh, orl = or_levels(self.tod, self.h, self.l, seg, len(ss), self.atr, [935, 940, 945])
        with np.errstate(invalid="ignore"):
            univ = (adv >= 95e6) & (self.atr > 0) & np.isfinite(orh[seg])
        self.tierP = np.ones(len(P)); self.tierP[fh2P] = self.tier
        self.hP, self.lP, self.cP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float))
        self.todP = P["tod"].to_numpy(np.int32)
        self.P2fh = P["_fhi"].to_numpy(np.int64)
        pool_idx = np.flatnonzero(univ & (self.tod >= 950))
        pkey = (pd.Series(self.fdat[pool_idx]).astype(str) + "|" + pd.Series(self.tod[pool_idx]).astype(str)).to_numpy()
        self.pk = {k: np.asarray(v) for k, v in pd.Series(pool_idx).groupby(pkey)}
        self.rng = np.random.default_rng(SEED + zlib.crc32(month.encode()))
        self.sessions = int(len(np.unique(self.fdat)))
        names = ["QQQ", "SPY", "TQQQ", "SQQQ", "SPXL", "SPXS"]
        m = np.isin(self.fsym, names)
        self.row = pd.Series(np.flatnonzero(m), index=pd.MultiIndex.from_arrays(
            [self.fsym[m], self.fdat[m], self.tod[m]]))

    def sub(self, syms):
        """Global fh indices of the given signal symbols, with segment arrays on that subset."""
        idx = np.flatnonzero(np.isin(self.fsym, syms))
        key, ss, se, seg = segs(self.fsym[idx], self.fdat[idx])
        tod = self.tod[idx]
        return dict(idx=idx, ss=ss, se=se, seg=seg, tod=tod, mins=(tod // 100) * 60 + tod % 100,
                    h=np.ascontiguousarray(self.h[idx]), l=np.ascontiguousarray(self.l[idx]),
                    c=np.ascontiguousarray(self.c[idx]), atr=np.ascontiguousarray(self.atr[idx]))

    def map_trade(self, gi, R, side, mode):
        """Signal rows gi (global) with signal risk R and signal side -> traded rows, traded R, traded side.
        mode 'lev': 3x ETF at the same row's close (short -> long inverse ETF), 'self': the signal symbol itself."""
        if mode == "self":
            return gi, R, np.full(len(gi), side), np.ones(len(gi), bool)
        tj = np.full(len(gi), -1, np.int64)
        for q, i in enumerate(gi):
            etf = LEV[self.fsym[i]][0 if side == 1 else 1]
            tj[q] = self.row.get((etf, self.fdat[i], self.tod[i]), -1)
        ok = tj >= 0
        Rt = np.where(ok, 3.0 * self.c[np.maximum(tj, 0)] * R / self.c[gi], np.nan)
        return tj, Rt, np.ones(len(gi), np.int64), ok

    def simulate(self, j, Rt, sd, up, be):
        """sim on the traded rows j (global fh), per-trade side sd; returns r, mfe, code, exit tod, control."""
        n = len(j)
        r = np.full(n, np.nan); mfe = np.full(n, np.nan); code = np.zeros(n, np.int8); xt = np.full(n, -1, np.int64)
        ctrl = np.full(n, np.nan)
        for side in (1, -1):
            m = np.flatnonzero(sd == side)
            if not len(m):
                continue
            r_, mfe_, code_, xr_ = sim(self.hP, self.lP, self.cP, self.todP, self.dend, self.tierP, self.fh2P[j[m]],
                                       np.full(len(m), np.nan), Rt[m], side, up[m], be, False, True)
            r[m], mfe[m], code[m] = r_, mfe_, code_
            xt[m] = np.where(xr_ >= 0, self.todP[np.maximum(xr_, 0)], -1)
            ce, cR, cu, cq = [], [], [], []
            for q in m:
                cand = self.pk.get(self.fdat[j[q]] + "|" + str(self.tod[j[q]]))
                if cand is None:
                    continue
                cand = cand[cand != j[q]]
                if not len(cand):
                    continue
                pick = self.rng.choice(cand, size=min(K_CTRL, len(cand)), replace=False)
                ra = Rt[q] / self.atr[j[q]]
                ce.extend(self.fh2P[pick]); cR.extend(ra * self.atr[pick]); cu.extend([up[q]] * len(pick)); cq.extend([q] * len(pick))
            if ce:
                rc = sim(self.hP, self.lP, self.cP, self.todP, self.dend, self.tierP, np.asarray(ce, np.int64),
                         np.full(len(ce), np.nan), np.asarray(cR, float), side, np.asarray(cu, float), be, False, True)[0]
                cm = pd.Series(rc).groupby(np.asarray(cq)).mean()
                ctrl[cm.index.to_numpy()] = cm.to_numpy()
        return r, mfe, code, xt, ctrl

    def frame(self, cid, sig_side, gi, j, Rsig, Rt, sd, up, res, tno=1):
        r, mfe, code, xt, ctrl = res
        c = self.c[j]
        cst = ((0.01 + c * 1e-4) * np.where(self.tod[j] < 1030, 1.4, 1.0) + 0.01 + c * 1e-4) * self.tier[j] / Rt
        return pd.DataFrame({"cfg": cid, "side": np.where(sig_side == 1, "L", "S"), "tno": np.int8(tno),
                             "date": self.fdat[gi], "sig_symbol": self.fsym[gi], "symbol": self.fsym[j],
                             "tod": self.tod[gi].astype(np.int16), "r": r, "code": code, "mfe": mfe, "up": up,
                             "R_atr": Rsig / self.atr[gi], "R_atr_traded": Rt / self.atr[j], "cost_R": cst, "ctrl": ctrl,
                             "spy_day": self.spy_day.reindex(self.fdat[gi]).to_numpy(float)})


# ---------------------------------------------------------------- plans (signals only, no outcomes)
def plan_f1(M, syms):
    """F1-A on the signal symbols: (global row, side, R, up) per side."""
    S = M.sub(syms)
    orh, orl = or_levels(S["tod"], S["h"], S["l"], S["seg"], len(S["ss"]), S["atr"], [935, 940, 945])
    out = {}
    for side in (1, -1):
        i = F1.signals(S["ss"], S["se"], S["h"], S["l"], S["c"], S["mins"], S["tod"], S["atr"], orh, orl, side, G, 1, 1100)
        i = i[i >= 0]
        stop = S["l"][i - 2] if side == 1 else S["h"][i - 2]
        R = side * (S["c"][i] - stop)
        ra = R / S["atr"][i]
        keep = (S["atr"][i] > 0) & (ra >= 0.03) & (ra <= 1.0)
        i, R, ra = i[keep], R[keep], ra[keep]
        out[side] = (S["idx"][i], R, np.where(ra <= 0.085, 2.0, 1.0))
    return out


def plan_f4(M, sym, sk):
    """F4 signal key sk (F4.SIG) on one symbol: global row, side, R, up (DOL)."""
    S = M.sub([sym])
    fh = M.fh.iloc[S["idx"]].reset_index(drop=True)
    X = F4.seg_arrays(fh, M.ds.iloc[S["idx"]].reset_index(drop=True))
    i, px, R, up, sw, side = F4.run_signal(X, sk, 0, False)
    assert np.isnan(px).all()
    keep = X["atr"][i] > 0
    return S["idx"][i[keep]], side, R[keep], up[keep]


def f3_arrays(M):
    """F3-A arrays on QQQ (OR5, FVG flags, stops, gates), as ../F3/build.py month_job."""
    S = M.sub(["QQQ"])
    tod, c, h, l, atr, seg = S["tod"], S["c"], S["h"], S["l"], S["atr"], S["seg"]
    mins = S["mins"]
    orh, orl = or_levels(tod, h, l, seg, len(S["ss"]), atr, [935])
    n = len(c)
    cons = np.zeros(n, bool)
    cons[2:] = (seg[2:] == seg[:-2]) & (mins[2:] - mins[1:-1] == 5) & (mins[1:-1] - mins[:-2] == 5)
    gL = np.full(n, -np.inf); gS = np.full(n, -np.inf)
    gL[2:] = l[2:] - h[:-2]; gS[2:] = l[:-2] - h[2:]
    stopL = np.full(n, np.nan); stopS = np.full(n, np.nan)
    stopL[2:] = l[:-2]; stopS[2:] = h[:-2]
    gi = S["idx"]
    qv = M.qfo.reindex(pd.Series(M.fdat[gi]).astype(str) + "|" + pd.Series(tod).astype(str)).to_numpy(float)
    with np.errstate(invalid="ignore"):
        fvgL = cons & (gL >= G * atr) & (gL >= 0.02)
        fvgS = cons & (gS >= G * atr) & (gS >= 0.02)
        RL, RS = c - stopL, stopS - c
        u = (atr > 0) & np.isfinite(orh[seg])
        win = (tod >= 950) & (tod <= 1100)
        okL = u & (RL / atr >= 0.03) & (RL / atr <= 1.0) & win & (qv > 0)
        okS = u & (RS / atr >= 0.03) & (RS / atr <= 1.0) & win & (qv < 0)
    return S, orh, orl, fvgL, fvgS, okL, okS, stopL, stopS


def run_f3(M, cid="F3-A"):
    S, orh, orl, fvgL, fvgS, okL, okS, stopL, stopS = f3_arrays(M)
    c, atr = S["c"], S["atr"]
    i1, s1, b1 = F3.trade1(S["ss"], S["se"], S["tod"], c, orh, orl, fvgL, fvgS, okL, okS)
    rows = []

    def go(i, sd, tno):
        R = sd * (c[i] - np.where(sd == 1, stopL[i], stopS[i]))
        up = np.where(R / atr[i] <= 0.085, 2.0, 1.0)
        gi = S["idx"][i]
        out = []
        xt = np.full(len(i), -1, np.int64)
        for side in (1, -1):
            m = np.flatnonzero(sd == side)
            if not len(m):
                continue
            j, Rt, tsd, ok = M.map_trade(gi[m], R[m], side, "lev")
            mm = m[ok]
            res = M.simulate(j[ok], Rt[ok], tsd[ok], up[mm], 1.0)
            xt[mm] = res[3]
            out.append(M.frame(cid, np.full(len(mm), side), gi[mm], j[ok], R[mm], Rt[ok], tsd[ok], up[mm], res, tno))
        return out, xt

    has = i1 >= 0
    o, xt1 = go(i1[has], s1[has], 1)
    rows += o
    # trade 1's exit (on the ETF) -> the QQQ row of the same day at or after that time
    x1 = np.full(len(S["ss"]), -1, np.int64)
    for q, s in enumerate(np.flatnonzero(has)):
        a, z = S["ss"][s], S["se"][s]
        t = xt1[q]
        if t < 0:
            continue
        k = a + np.searchsorted(S["tod"][a:z + 1], t)
        x1[s] = min(k, z) if t <= S["tod"][z] else z
    i2, s2 = F3.trade2(S["ss"], S["se"], c, orh, orl, fvgL, fvgS, okL, okS, b1, x1, has.copy())
    h2 = i2 >= 0
    o, _ = go(i2[h2], s2[h2], 2)
    rows += o
    return rows


# ---------------------------------------------------------------- 1-min (F6-05/06)
class OneMin:
    def __init__(self, M):
        d = load_1min(M.month)
        self.d = d
        tl = scan.tail_rows(M.month)
        tl["symbol"] = tl["symbol"].astype(str); tl["date"] = tl["date"].astype(str)
        tl = tl[(tl["date"] <= CUT) & tl["symbol"].isin(d["symbol"].unique())]
        d["_i"] = np.arange(len(d)); tl["_i"] = -1
        P = pd.concat([d[["symbol", "date", "tod", "high", "low", "close", "_i"]], tl[["symbol", "date", "tod", "high", "low", "close", "_i"]]],
                      ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        key, ss, se, seg = segs(P["symbol"].to_numpy(), P["date"].to_numpy())
        self.dend = se[seg]
        self.d2P = np.full(len(d), -1, np.int64)
        m = P["_i"].to_numpy() >= 0
        self.d2P[P["_i"].to_numpy()[m]] = np.flatnonzero(m)
        self.hP, self.lP, self.cP = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float))
        self.todP = P["tod"].to_numpy(np.int32)
        self.sym, self.dat = d["symbol"].to_numpy(), d["date"].to_numpy()
        self.tod = d["tod"].to_numpy(np.int64)
        self.h, self.l, self.c = (d[k].to_numpy(float) for k in ("high", "low", "close"))
        self.atr = d["atr_d"].to_numpy(float)
        with np.errstate(invalid="ignore"):
            self.tier = np.where((np.abs(d["gap"].to_numpy(float)) >= 20) | (self.c < 5), 3.0, 1.0)
        self.tierP = np.ones(len(P)); self.tierP[self.d2P] = self.tier
        adv = d["adv20"].fillna(0).to_numpy(float)
        pool = np.flatnonzero((adv >= 95e6) & (self.atr > 0))
        pkey = (pd.Series(self.dat[pool]) + "|" + pd.Series(self.tod[pool]).astype(str)).to_numpy()
        self.pk = {k: np.asarray(v) for k, v in pd.Series(pool).groupby(pkey)}
        self.row = pd.Series(np.arange(len(d)), index=pd.MultiIndex.from_arrays([self.sym, self.dat, self.tod]))
        self.M = M

    def plan(self, sym="QQQ"):
        M = self.M
        idx = np.flatnonzero(self.sym == sym)
        key, ss, se, seg = segs(self.sym[idx], self.dat[idx])
        tod = self.tod[idx]; mins = (tod // 100) * 60 + tod % 100
        h, l, c, atr = (np.ascontiguousarray(a[idx]) for a in (self.h, self.l, self.c, self.atr))
        # OR15 and the 0950 5-min close from the 5-min frames of the same symbol-day
        S5 = M.sub([sym])
        orh5, orl5 = or_levels(S5["tod"], S5["h"], S5["l"], S5["seg"], len(S5["ss"]), S5["atr"], [935, 940, 945])
        dates5 = M.fdat[S5["idx"][S5["ss"]]]
        r950 = np.flatnonzero(S5["tod"] == 950)
        c950 = pd.Series(S5["c"][r950], index=M.fdat[S5["idx"][r950]])
        o = pd.DataFrame({"orh": orh5, "orl": orl5}, index=dates5)
        dd = self.dat[idx][ss]
        orh = o["orh"].reindex(dd).to_numpy(float); orl = o["orl"].reindex(dd).to_numpy(float)
        cc = c950.reindex(dd).to_numpy(float)
        out = {}
        for side in (1, -1):
            lh, ll = orh.copy(), orl.copy()
            with np.errstate(invalid="ignore"):
                skip = ~np.isfinite(cc) | (side * (cc - (orh if side == 1 else orl)) > 0)
            (lh if side == 1 else ll)[skip] = np.nan
            i = signals_step(ss, se, h, l, c, mins, tod, atr, lh, ll, side, G, 1, 1100, 1, 952)
            i = i[i >= 0]
            stop = l[i - 2] if side == 1 else h[i - 2]
            R = side * (c[i] - stop)
            ra = R / atr[i]
            keep = (atr[i] > 0) & (ra >= 0.03) & (ra <= 1.0)
            i, R, ra = i[keep], R[keep], ra[keep]
            out[side] = (idx[i], R, np.where(ra <= 0.085, 2.0, 1.0))
        return out

    def run(self, cid, side, gi, R, up):
        M = self.M
        etf = "TQQQ" if side == 1 else "SQQQ"
        j = np.array([self.row.get((etf, self.dat[i], self.tod[i]), -1) for i in gi], np.int64)
        ok = j >= 0
        gi, R, up, j = gi[ok], R[ok], up[ok], j[ok]
        Rt = 3.0 * self.c[j] * R / self.c[gi]
        r, mfe, code, xr = sim(self.hP, self.lP, self.cP, self.todP, self.dend, self.tierP, self.d2P[j],
                               np.full(len(j), np.nan), Rt, 1, up, 0.0, False, True)
        ctrl = np.full(len(j), np.nan)
        ce, cR, cu, cq = [], [], [], []
        for q in range(len(j)):
            cand = self.pk.get(self.dat[j[q]] + "|" + str(self.tod[j[q]]))
            if cand is None:
                continue
            cand = cand[cand != j[q]]
            if not len(cand):
                continue
            pick = M.rng.choice(cand, size=min(K_CTRL, len(cand)), replace=False)
            ce.extend(self.d2P[pick]); cR.extend(Rt[q] / self.atr[j[q]] * self.atr[pick]); cu.extend([up[q]] * len(pick)); cq.extend([q] * len(pick))
        if ce:
            rc = sim(self.hP, self.lP, self.cP, self.todP, self.dend, self.tierP, np.asarray(ce, np.int64),
                     np.full(len(ce), np.nan), np.asarray(cR, float), 1, np.asarray(cu, float), 0.0, False, True)[0]
            cm = pd.Series(rc).groupby(np.asarray(cq)).mean()
            ctrl[cm.index.to_numpy()] = cm.to_numpy()
        c = self.c[j]
        cst = ((0.01 + c * 1e-4) * np.where(self.tod[j] < 1030, 1.4, 1.0) + 0.01 + c * 1e-4) * self.tier[j] / Rt
        return pd.DataFrame({"cfg": cid, "side": "L" if side == 1 else "S", "tno": np.int8(1), "date": self.dat[gi],
                             "sig_symbol": self.sym[gi], "symbol": self.sym[j], "tod": self.tod[gi].astype(np.int16),
                             "r": r, "code": code, "mfe": mfe, "up": up, "R_atr": R / self.atr[gi],
                             "R_atr_traded": Rt / self.atr[j], "cost_R": cst, "ctrl": ctrl,
                             "spy_day": M.spy_day.reindex(self.dat[gi]).to_numpy(float)})


# ---------------------------------------------------------------- month job
F1ROWS = {  # cid: (signal symbols, mode, sides -> config ids)
    "QQQlev": (["QQQ"], "lev", {1: "F6-01", -1: "F6-02"}),
    "SPYlev": (["SPY"], "lev", {1: "F6-03", -1: "F6-04"}),
    "IDXself": (["QQQ", "SPY", "TQQQ", "SQQQ"], "self", {1: "F6-15", -1: "F6-16"}),
    "QQQself": (["QQQ"], "self", {1: "F6-17", -1: "F6-18"}),
}
F4ROWS = {"F6-09": ("QQQ", "PDL"), "F6-10": ("QQQ", "PDH"), "F6-11": ("QQQ", "ORL"), "F6-12": ("QQQ", "ORH"),
          "F6-13": ("SPY", "PDL"), "F6-14": ("SPY", "PDH")}


def month_job(month):
    t0 = time.time()
    M = Month(month)
    rows = []
    for key, (syms, mode, ids) in F1ROWS.items():
        pl = plan_f1(M, syms)
        for side, (gi, R, up) in pl.items():
            j, Rt, sd, ok = M.map_trade(gi, R, side, mode)
            gi, R, up, j, Rt, sd = gi[ok], R[ok], up[ok], j[ok], Rt[ok], sd[ok]
            res = M.simulate(j, Rt, sd, up, 0.0)
            rows.append(M.frame(ids[side], np.full(len(gi), side), gi, j, R, Rt, sd, up, res))
    for cid, (sym, sk) in F4ROWS.items():
        gi, side, R, up = plan_f4(M, sym, sk)
        j, Rt, sd, ok = M.map_trade(gi, R, side, "lev")
        gi, R, up, j, Rt, sd = gi[ok], R[ok], up[ok], j[ok], Rt[ok], sd[ok]
        res = M.simulate(j, Rt, sd, up, 0.0)
        rows.append(M.frame(cid, np.full(len(gi), side), gi, j, R, Rt, sd, up, res))
    for fr in run_f3(M):
        fr["cfg"] = np.where(fr["side"] == "L", "F6-07", "F6-08")
        rows.append(fr)
    O = OneMin(M)
    for side, (gi, R, up) in O.plan("QQQ").items():
        rows.append(O.run("F6-05" if side == 1 else "F6-06", side, gi, R, up))
    T = pd.concat([r for r in rows if len(r)], ignore_index=True)
    meta = {"month": month, "sessions": M.sessions, "secs": round(time.time() - t0)}
    print(json.dumps(meta), len(T), flush=True)
    return T, meta


def sanity(month="2025-06"):
    """Signal features only: trade-1 counts, R/ATR, traded R/ATR, cost/R, signal time. No sim, no outcome column."""
    M = Month(month)
    out = []

    def add(cid, gi, R, Rt, j, up):
        c = M.c[j]
        cst = ((0.01 + c * 1e-4) * np.where(M.tod[j] < 1030, 1.4, 1.0) + 0.01 + c * 1e-4) * M.tier[j] / Rt
        out.append(dict(cfg=cid, n=len(gi), per_sess=round(len(gi) / M.sessions, 2),
                        med_R_atr=round(float(np.median(R / M.atr[gi])), 3) if len(gi) else np.nan,
                        med_R_atr_traded=round(float(np.median(Rt / M.atr[j])), 3) if len(gi) else np.nan,
                        med_cost_R=round(float(np.median(cst)), 4) if len(gi) else np.nan,
                        share_2R=round(float((up == 2).mean()), 2) if len(gi) else np.nan,
                        med_tod=float(np.median(M.tod[gi])) if len(gi) else np.nan))
    for key, (syms, mode, ids) in F1ROWS.items():
        for side, (gi, R, up) in plan_f1(M, syms).items():
            j, Rt, sd, ok = M.map_trade(gi, R, side, mode)
            add(ids[side], gi[ok], R[ok], Rt[ok], j[ok], up[ok])
    for cid, (sym, sk) in F4ROWS.items():
        gi, side, R, up = plan_f4(M, sym, sk)
        j, Rt, sd, ok = M.map_trade(gi, R, side, "lev")
        add(cid, gi[ok], R[ok], Rt[ok], j[ok], up[ok])
    S, orh, orl, fvgL, fvgS, okL, okS, stopL, stopS = f3_arrays(M)
    i1, s1, b1 = F3.trade1(S["ss"], S["se"], S["tod"], S["c"], orh, orl, fvgL, fvgS, okL, okS)
    for side, cid in ((1, "F6-07 (trade 1)"), (-1, "F6-08 (trade 1)")):
        i = i1[(i1 >= 0) & (s1 == side)]
        R = side * (S["c"][i] - (stopL[i] if side == 1 else stopS[i]))
        up = np.where(R / S["atr"][i] <= 0.085, 2.0, 1.0)
        j, Rt, sd, ok = M.map_trade(S["idx"][i], R, side, "lev")
        add(cid, S["idx"][i][ok], R[ok], Rt[ok], j[ok], up[ok])
    O = OneMin(M)
    for side, (gi, R, up) in O.plan("QQQ").items():
        out.append(dict(cfg="F6-05" if side == 1 else "F6-06", n=len(gi), per_sess=round(len(gi) / M.sessions, 2),
                        med_R_atr=round(float(np.median(R / O.atr[gi])), 3) if len(gi) else np.nan,
                        share_2R=round(float((up == 2).mean()), 2) if len(gi) else np.nan,
                        med_tod=float(np.median(O.tod[gi])) if len(gi) else np.nan))
    print(f"{month}: sessions {M.sessions}")
    print(pd.DataFrame(out).sort_values("cfg").to_string(index=False))


def check(month="2025-06"):
    """signals_step(step=5, tod_lo=955) == F1.signals on every symbol-day of a month (both sides)."""
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str).to_numpy()
    sym = fh["symbol"].to_numpy(); tod = fh["tod"].to_numpy(np.int64); mins = (tod // 100) * 60 + tod % 100
    h, l, c, atr = (fh[k].to_numpy(float) for k in ("high", "low", "close", "atr_d"))
    key, ss, se, seg = segs(sym, ds)
    orh, orl = or_levels(tod, h, l, seg, len(ss), atr, [935, 940, 945])
    bad = 0
    for side in (1, -1):
        a = F1.signals(ss, se, h, l, c, mins, tod, atr, orh, orl, side, G, 1, 1100)
        b = signals_step(ss, se, h, l, c, mins, tod, atr, orh, orl, side, G, 1, 1100, 5, 955)
        bad += int((a != b).sum())
        print("side", side, "signals", int((a >= 0).sum()), "mismatch", int((a != b).sum()))
    return bad


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["check"]:
        assert check() == 0
        sys.exit()
    if args == ["sanity"]:
        sanity()
        sys.exit()
    mp = SCR / "meta.json"
    metas = json.loads(mp.read_text()) if mp.exists() else []
    done = {m["month"] for m in metas}
    for m in args or MONTHS:
        if m in done:
            continue
        T, meta = month_job(m)
        T.to_parquet(SCR / f"tr_{m}.parquet", index=False)
        metas.append(meta)
        mp.write_text(json.dumps(metas))
