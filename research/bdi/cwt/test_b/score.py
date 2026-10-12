"""CWT package B (research/bdi/cwt/TESTPLAN.md section 3 + the 2026-10-12 package B amendment): 7 families, 368
configurations, scored on the open two-year history (research/history2y/lib.py; the rule-19 locked block is never
loaded). One process, month by month.

Per configuration: one trade per symbol-day (first qualifying decision bar in the window), entry at the signal bar's
close, exits on the 5-min rows to the 15:55 bar (structural S with the family's stop, or the lab geometries),
production costs with the time-of-day entry multiplier and x3 extended-tier slippage, R = 0.25 x daily ATR.
Also: SPY-hedged (beta60) market-neutral version of every trade, and random same-side same-window baselines.

    python research/bdi/cwt/test_b/score.py            # -> data/trades.npz, data/baseline.json
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

DATA = HERE / "data"
MIN_ADV = 95e6
GEOMS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
INDEX = ("SPY", "QQQ", "IWM", "DIA")
FCOLS = ["symbol", "date", "tod", "close", "high", "low", "vwapDistPct", "gap", "fromOpen", "atr_d", "dist_pdh_atr",
         "dist_pdl_atr", "dist_hod_atr", "dist_lod_atr", "volumeRatio", "vol_climax", "rsi", "adv20"]
FCOLS += [f"r_{s}_{g}" for s in ("long", "short") for g in GEOMS]
WIN = {"full": (950, 1500)}
GUEST = {"B1": (1030, 1500), "B2": (1100, 1500), "B3": (950, 1200), "B4": (950, 1130), "B5": (950, 1130),
         "B6": (1335, 1500), "B7": (1015, 1500)}


# ------------------------------------------------------------------------------------------------ grid (pre-declared)
def grid() -> list[dict]:
    g = []
    ex4 = ["S", "t1s1", "t05s1", "t1s05"]
    win2 = ["full", "guest"]
    for a in (1.5, 2.5):
        for trig in ("T1", "T2"):
            for ex in ex4:
                for w in win2:
                    g.append(dict(fam="B1", side="short", a=a, trig=trig, exit=ex, win=w))
    for z in (0.5, 0.75):
        for U in ("all", "index"):
            for side in ("short", "long"):
                for ex in ex4:
                    for w in win2:
                        g.append(dict(fam="B2", side=side, z=z, U=U, exit=ex, win=w))
    for L in ("PD", "OR"):
        for p in (0.05, 0.10):
            for V in ("any", "lowvol"):
                for side in ("short", "long"):
                    for ex in ("S", "t1s1", "t05s1"):
                        for w in win2:
                            g.append(dict(fam="B3", side=side, L=L, p=p, V=V, exit=ex, win=w))
    for n in (4, 6):
        for ex in ex4:
            for w in win2:
                g.append(dict(fam="B4", side="long", part="a", k=n, exit=ex, win=w))
    for s in (1, 2):
        for ex in ex4:
            for w in win2:
                g.append(dict(fam="B4", side="long", part="b", k=s, exit=ex, win=w))
    for m in (0.5, 0.75):
        for v in (3, 5):
            for D in ("none", "ret5"):
                for ex in ex4:
                    for w in win2:
                        g.append(dict(fam="B5", side="long", m=m, v=v, D=D, exit=ex, win=w))
    for u in (4, 8):
        for wd in (0.3, 0.5):
            for vc in ("none", "abovevwap"):
                for ex in ex4:
                    g.append(dict(fam="B6", side="long", u=u, wd=wd, vc=vc, exit=ex, win="guest"))
    for th in (30, 25):
        for ex in ex4:
            for w in win2:
                g.append(dict(fam="B7", side="long", part="a", th=th, f=None, exit=ex, win=w))
    for th in (2.0, 3.0):
        for f in ("half", "zero"):
            for ex in ex4:
                for w in win2:
                    g.append(dict(fam="B7", side="long", part="b", th=th, f=f, exit=ex, win=w))
    for i, c in enumerate(g):
        c["id"] = i
    return g


PARAMS = {"B1": ("a", "trig"), "B2": ("z", "U", "side"), "B3": ("L", "p", "V", "side"), "B4": ("part", "k"),
          "B5": ("m", "v", "D"), "B6": ("u", "wd", "vc"), "B7": ("part", "th", "f")}


def cname(c: dict) -> str:
    return c["fam"] + "-" + "-".join(f"{k}{c[k]}" for k in PARAMS[c["fam"]] if c.get(k) is not None) + f"-{c['exit']}-{c['win']}"


# ------------------------------------------------------------------------------------------------ numba kernels
@numba.njit(cache=True)
def seg_cum(x, new, ismax):
    out = np.empty_like(x)
    cur = x[0]
    for i in range(len(x)):
        if new[i]:
            cur = x[i]
        elif ismax:
            cur = max(cur, x[i])
        else:
            cur = min(cur, x[i])
        out[i] = cur
    return out


@numba.njit(cache=True)
def seg_prev(x, new, k):
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        ok = True
        for j in range(k):
            if i - j < 0 or new[i - j]:
                ok = False
                break
        if ok:
            out[i] = x[i - k]
    return out


@numba.njit(cache=True)
def sim(idx, side, c, h, l, tod, new, stop, tgt, dyn, use_dyn):
    """From the bar after entry: stop first (stop price), then the limit target (fixed tgt, or dyn[k-1] when use_dyn),
    else the close of the last row of the symbol-day with tod <= 1555. Returns exit price, kind (1 stop, 2 target,
    3 time) and exit row."""
    n = len(idx)
    xp = np.empty(n)
    kind = np.empty(n, np.int8)
    xr = np.empty(n, np.int64)
    N = len(c)
    for j in range(n):
        i = idx[j]
        s = side[j]
        k = i + 1
        done = False
        while k < N and not new[k] and tod[k] <= 1555:
            if (s > 0 and l[k] <= stop[j]) or (s < 0 and h[k] >= stop[j]):
                xp[j] = stop[j]
                kind[j] = 1
                xr[j] = k
                done = True
                break
            tg = dyn[k - 1] if use_dyn else tgt[j]
            if not np.isnan(tg) and ((s > 0 and h[k] >= tg) or (s < 0 and l[k] <= tg)):
                xp[j] = tg
                kind[j] = 2
                xr[j] = k
                done = True
                break
            k += 1
        if not done:
            xp[j] = c[k - 1]
            kind[j] = 3
            xr[j] = k - 1
    return xp, kind, xr


@numba.njit(cache=True)
def k_b1(c, h, l, vwap, open_d, atr, new, a, trig):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    stp = np.full(n, np.nan)
    hod = -1e18
    bd = False
    bdrow = -1
    bdhi = -1e18
    Lmin = 1e18
    Bmax = -1e18
    for i in range(n):
        if new[i]:
            hod = -1e18
            bd = False
            bdhi = -1e18
            Lmin = 1e18
            Bmax = -1e18
        # trigger uses the state through bar i-1 (bounce) and the close of bar i
        if h[i] > hod:
            hod = h[i]
            bd = False
            Lmin = 1e18
            Bmax = -1e18
            continue
        if bd:
            bdhi = max(bdhi, h[i])
            if i > bdrow:
                ok = False
                if trig == 1:
                    ok = h[i] >= vwap[i] - 0.05 * atr[i] and c[i] < vwap[i]
                elif Lmin < 1e17 and Bmax > -1e17 and hod > Lmin:
                    rt = (Bmax - Lmin) / (hod - Lmin)
                    ok = rt >= 0.38 and rt <= 0.62 and c[i] < l[i - 1]
                if ok and bdhi > c[i]:
                    flag[i] = True
                    stp[i] = bdhi
        # update the post-high low and the bounce high (through bar i)
        if l[i] < Lmin:
            Lmin = l[i]
            Bmax = -1e18
        else:
            Bmax = max(Bmax, h[i])
        if not bd and atr[i] > 0 and hod > open_d[i]:
            run = (hod - open_d[i]) / atr[i]
            drop = (hod - c[i]) / (hod - open_d[i])
            if run >= a and drop >= 0.4 and c[i] < vwap[i]:
                bd = True
                bdrow = i
                bdhi = h[i]
    return flag, stp


@numba.njit(cache=True)
def k_b3(c, h, l, vr, L, p, atr, new, upper, lo_ok):
    """Fade a poke beyond level L (upper: short at L from above; else long at L from below). Excursion = first bar
    whose high (low) trades >= p x atr beyond L after a close inside; trigger = a close back inside within 3 bars of
    the excursion start. Returns flag, stop (poke extreme), poke-bar volumeRatio."""
    n = len(c)
    flag = np.zeros(n, np.bool_)
    stp = np.full(n, np.nan)
    pvr = np.full(n, np.nan)
    inexc = False
    stale = False
    st = 0
    ext = 0.0
    v0 = np.nan
    for i in range(n):
        if new[i]:
            inexc = False
            stale = False
        if not lo_ok[i] or np.isnan(L[i]):
            continue
        beyond = (h[i] >= L[i] + p * atr[i]) if upper else (l[i] <= L[i] - p * atr[i])
        inside = (c[i] < L[i]) if upper else (c[i] > L[i])
        if not inexc and not stale and beyond:
            inexc = True
            st = i
            ext = h[i] if upper else l[i]
            v0 = vr[i]
        if inexc:
            ext = max(ext, h[i]) if upper else min(ext, l[i])
            if inside:
                if i - st <= 3:
                    flag[i] = True
                    stp[i] = ext
                    pvr[i] = v0
                inexc = False
            elif i - st > 3:
                inexc = False
                stale = True
        elif stale and inside:
            stale = False
    return flag, stp, pvr


@numba.njit(cache=True)
def k_b4a(c, h, l, hod, atr, new, nco):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    stp = np.full(n, np.nan)
    s0 = 0
    for i in range(n):
        if new[i]:
            s0 = i
        if i - s0 + 1 < nco + 6:
            continue
        thr = hod[i] - 0.1 * atr[i]
        touches = 0
        for k in range(s0, i + 1):
            if h[k] >= thr:
                touches += 1
        if touches < 3:
            continue
        a = i - nco + 1
        m0 = max(s0, a - 20)
        mr = 0.0
        for k in range(m0, a):
            mr += h[k] - l[k]
        mr /= (a - m0)
        ok = True
        lo = 1e18
        for k in range(a, i + 1):
            if not (h[k] - l[k] < 0.5 * mr and c[k] <= hod[i] and hod[i] - c[k] <= 0.25 * atr[i]):
                ok = False
                break
            lo = min(lo, l[k])
        if ok and lo < c[i]:
            flag[i] = True
            stp[i] = lo
    return flag, stp


@numba.njit(cache=True)
def k_b4b(c, h, l, vwap, open_d, atr, new, s):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    stp = np.full(n, np.nan)
    hod = -1e18
    L = 1e18
    above = True
    nb = 0
    for i in range(n):
        if new[i]:
            hod = -1e18
            L = 1e18
            above = True
            nb = 0
        if nb > 0 and hod > open_d[i] and atr[i] > 0 and (hod - open_d[i]) >= s * atr[i] and above and c[i] > hod:
            d = (hod - L) / (hod - open_d[i])
            if d >= 0.3 and d <= 0.5 and L < c[i]:
                flag[i] = True
                stp[i] = L
        if h[i] > hod:
            hod = h[i]
            L = 1e18
            above = True
            nb = 0
        else:
            L = min(L, l[i])
            above = above and l[i] > vwap[i]
            nb += 1
    return flag, stp


@numba.njit(cache=True)
def k_b5(c, h, l, lod_prev, c6, vcmax3, atr, new, m, v):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    fl = False
    lod = 1e18
    for i in range(n):
        if new[i]:
            fl = False
            lod = 1e18
        if fl and i > 0 and not new[i] and c[i] > h[i - 1]:
            flag[i] = True
        lod = min(lod, l[i])
        if not fl and atr[i] > 0 and not np.isnan(c6[i]) and (c6[i] - c[i]) >= m * atr[i] and c[i] < lod_prev[i] \
                and vcmax3[i] >= v:
            fl = True
    return flag


@numba.njit(cache=True)
def k_b6(c, h, l, vwap, tod, new, wd, atr, need_above):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    stp = np.full(n, np.nan)
    mh = -1e18
    ml = 1e18
    ab = True
    for i in range(n):
        if new[i]:
            mh = -1e18
            ml = 1e18
            ab = True
        t = tod[i]
        if t >= 1135 and t <= 1330:
            mh = max(mh, h[i])
            ml = min(ml, l[i])
            ab = ab and l[i] > vwap[i]
        elif t >= 1335 and t <= 1500 and mh > -1e17:
            if (mh - ml) <= wd * atr[i] and (ab or not need_above) and c[i] > mh and ml < c[i]:
                flag[i] = True
                stp[i] = ml
    return flag, stp


@numba.njit(cache=True)
def k_b7a(c, h, l, rsi, isdec, new, th):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    seen = False
    for i in range(n):
        if new[i]:
            seen = False
        if seen and i > 0 and not new[i] and c[i] > h[i - 1]:
            flag[i] = True
        if not seen and isdec[i] and rsi[i] < th:
            seen = True
    return flag


@numba.njit(cache=True)
def k_b7b(c, h, l, rs, tod, new, th, zero):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    stp = np.full(n, np.nan)
    M = -1e18
    fallen = False
    dl = 1e18
    for i in range(n):
        if new[i]:
            M = -1e18
            fallen = False
            dl = 1e18
        if np.isnan(rs[i]):
            continue
        if fallen and i > 0 and not new[i] and not np.isnan(rs[i - 1]) and rs[i] > rs[i - 1] and c[i] > h[i - 1]:
            flag[i] = True
            stp[i] = min(dl, l[i])
        if tod[i] <= 1015 and rs[i] > M:
            M = rs[i]
            fallen = False
            dl = 1e18
        else:
            dl = min(dl, l[i])
            if not fallen and M >= th:
                lim = 0.0 if zero else 0.5 * M
                if rs[i] < lim:
                    fallen = True
    return flag, stp


# ------------------------------------------------------------------------------------------------ month frame
class Month:
    def __init__(self, month: str, ht: pd.DataFrame, feat: pd.DataFrame, rv: pd.DataFrame, dayidx: dict):
        f = lib.load_month(month, FCOLS)
        f = f[(f["adv20"].to_numpy(float) >= MIN_ADV) & (f["atr_d"].to_numpy(float) > 0)].reset_index(drop=True)
        f["symbol"] = f["symbol"].astype(str)
        f["isdec"] = True
        keys = f[["symbol", "date"]].drop_duplicates()
        h = ht[ht["month"] == month].merge(keys, on=["symbol", "date"], how="inner")
        self.check = self._check(f, h)
        h = h[~h["tod"].isin([950, 1000, 1200, 1500])]
        h = h.rename(columns={"h": "high", "l": "low", "c": "close", "vwap": "vwap_ht"}).drop(columns="month")
        h["isdec"] = False
        x = pd.concat([f, h], ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
        self.x = x
        sy, dt = x["symbol"].to_numpy(), x["date"].to_numpy()
        self.new = np.r_[True, (sy[1:] != sy[:-1]) | (dt[1:] != dt[:-1])]
        segid = np.cumsum(self.new) - 1
        # per-day constants from the frame rows, spread to the head/tail rows
        isdec = x["isdec"].to_numpy(bool)
        self.isdec = isdec
        c = x["close"].to_numpy(float)
        self.c, self.h, self.l = c, x["high"].to_numpy(float), x["low"].to_numpy(float)
        self.tod = x["tod"].to_numpy(np.int64)
        atr = x["atr_d"].to_numpy(float)
        open_row = c / (1 + x["fromOpen"].to_numpy(float) / 100)
        pdh_row = c + x["dist_pdh_atr"].to_numpy(float) * atr
        pdl_row = c - x["dist_pdl_atr"].to_numpy(float) * atr

        def per_seg(v):
            s = pd.Series(v).groupby(segid).transform("first")       # first non-NaN per segment
            return s.to_numpy(float)
        self.atr = per_seg(atr)
        self.gap = per_seg(x["gap"].to_numpy(float))
        self.open_d = per_seg(open_row)
        self.pdh, self.pdl = per_seg(pdh_row), per_seg(pdl_row)
        self.pc = self.open_d / (1 + self.gap / 100)
        vw = c / (1 + x["vwapDistPct"].to_numpy(float) / 100)
        self.vwap = np.where(isdec, vw, x["vwap_ht"].to_numpy(float))
        self.fo = (c / self.open_d - 1) * 100
        self.hod = seg_cum(self.h, self.new, True)
        self.lod = seg_cum(self.l, self.new, False)
        self.sym = x["symbol"].to_numpy()
        self.date = x["date"].to_numpy()
        self.day = np.array([dayidx[d] for d in self.date], np.int64)
        fk = pd.MultiIndex.from_arrays([x["symbol"], x["date"]])
        fe = feat.reindex(fk)
        self.ret5 = fe["ret5"].to_numpy(float)
        self.ret20 = fe["ret20"].to_numpy(float)
        self.near252 = fe["near252"].to_numpy(float)
        self.beta = fe["beta60"].to_numpy(float)
        self.rvol12 = rv.reindex(fk).to_numpy(float)
        self.vr = x["volumeRatio"].to_numpy(float)
        self.vc = x["vol_climax"].to_numpy(float)
        self.rsi = x["rsi"].to_numpy(float)
        # SPY close and from-open at the same (day, tod)
        m = self.sym == "SPY"
        k = self.day * 10000 + self.tod
        self.spy_c = pd.Series(c[m], index=k[m]).reindex(k).to_numpy()
        self.spy_fo = pd.Series(self.fo[m], index=k[m]).reindex(k).to_numpy()
        self.key = k
        self.labr = {f"{s}_{g}": x[f"r_{s}_{g}"].to_numpy(float) for s in ("long", "short") for g in GEOMS}
        del self.x, x, fe, fk

    @staticmethod
    def _check(f, h):
        """Head/tail rows vs the frames at the shared 09:50 / 10:00 / 12:00 / 15:00 bars."""
        m = h[h["tod"].isin([950, 1000, 1200, 1500])].merge(f[["symbol", "date", "tod", "close", "high", "vwapDistPct"]],
                                                             on=["symbol", "date", "tod"], how="inner")
        if not len(m):
            return {}
        vw = m["close"] / (1 + m["vwapDistPct"] / 100)
        return {"n": int(len(m)), "close_match": float((abs(m["c"] - m["close"]) <= 1e-3 * m["close"]).mean()),
                "high_match": float((abs(m["h"] - m["high"]) <= 1e-3 * m["high"]).mean()),
                "vwap_match_10bp": float((abs(m["vwap"] - vw) <= 1e-3 * vw).mean())}

    def prev(self, v, k=1):
        return seg_prev(np.asarray(v, float), self.new, k)


# ------------------------------------------------------------------------------------------------ signals
def signals(M: Month, c: dict):
    """-> (flag, stop, tgt, dyn) for the structural version of configuration c. stop/tgt are row arrays (the
    stop / fixed limit if entered at that row); dyn=True means the S target is the prior bar's VWAP."""
    fam, n = c["fam"], len(M.c)
    nan = np.full(n, np.nan)
    if fam == "B1":
        flag, stp = k_b1(M.c, M.h, M.l, M.vwap, M.open_d, M.atr, M.new, c["a"], 1 if c["trig"] == "T1" else 2)
        return flag, stp, nan, False
    if fam == "B2":
        rng = (M.hod - M.lod) / M.atr
        uni = np.isin(M.sym, INDEX) if c["U"] == "index" else np.ones(n, bool)
        if c["side"] == "short":
            ext = ((M.hod - M.c) / M.atr <= 0.05) & ((M.c - M.vwap) >= c["z"] * M.atr) & (rng >= 0.4)
            flag = (M.prev(ext.astype(float)) == 1) & (M.h < M.prev(M.h))
            stp = M.hod + 0.1 * M.atr
        else:
            ext = ((M.c - M.lod) / M.atr <= 0.05) & ((M.vwap - M.c) >= c["z"] * M.atr) & (rng >= 0.4)
            flag = (M.prev(ext.astype(float)) == 1) & (M.l > M.prev(M.l))
            stp = M.lod - 0.1 * M.atr
        return flag & uni, stp, nan, True
    if fam == "B3":
        upper = c["side"] == "short"
        if c["L"] == "PD":
            L = M.pdh if upper else M.pdl
            lo_ok = np.ones(n, bool)
            tg = (M.pdh + M.pdl) / 2
        else:
            at10 = np.where(M.tod == 1000, M.hod if upper else M.lod, np.nan)
            L = pd.Series(at10).groupby(np.cumsum(M.new)).ffill().to_numpy(float)
            other = pd.Series(np.where(M.tod == 1000, M.lod if upper else M.hod, np.nan)).groupby(np.cumsum(M.new)).ffill().to_numpy(float)
            lo_ok = M.tod >= 1005
            tg = other
        flag, stp, pvr = k_b3(M.c, M.h, M.l, M.vr, L, c["p"], M.atr, M.new, upper, lo_ok)
        if c["V"] == "lowvol":
            flag = flag & (pvr < 1)
        tg = np.where((upper & (tg < M.c)) | (~upper & (tg > M.c)), tg, np.nan)
        return flag, stp, tg, False
    if fam == "B4":
        if c["part"] == "a":
            flag, stp = k_b4a(M.c, M.h, M.l, M.hod, M.atr, M.new, int(c["k"]))
            return flag, stp, M.hod + 0.25 * M.atr, False
        flag, stp = k_b4b(M.c, M.h, M.l, M.vwap, M.open_d, M.atr, M.new, float(c["k"]))
        return flag, stp, nan, False
    if fam == "B5":
        c6 = M.prev(M.c, 6)
        lodp = M.prev(M.lod, 1)
        vc = np.nan_to_num(M.vc, nan=0.0)
        vc3 = np.fmax(np.fmax(vc, np.nan_to_num(M.prev(vc, 1))), np.nan_to_num(M.prev(vc, 2)))
        flag = k_b5(M.c, M.h, M.l, np.nan_to_num(lodp, nan=-1e18), c6, vc3, M.atr, M.new, c["m"], c["v"])
        if c["D"] == "ret5":
            flag = flag & (M.ret5 <= -15)
        return flag, M.lod.copy(), nan, True
    if fam == "B6":
        fo12 = pd.Series(np.where(M.tod == 1200, M.fo, np.nan)).groupby(np.cumsum(M.new)).transform("max").to_numpy(float)
        flag, stp = k_b6(M.c, M.h, M.l, M.vwap, M.tod, M.new, c["wd"], M.atr, c["vc"] == "abovevwap")
        flag = flag & (fo12 >= c["u"]) & (M.rvol12 >= 2)
        return flag, stp, nan, False
    if fam == "B7":
        if c["part"] == "a":
            day_ok = (M.near252 == 1) & (M.ret20 >= 15)
            flag = k_b7a(M.c, M.h, M.l, np.nan_to_num(M.rsi, nan=100.0), M.isdec, M.new, float(c["th"])) & day_ok
            return flag, M.lod.copy(), M.hod.copy(), False
        beta = np.nan_to_num(M.beta, nan=1.0)
        rs = M.fo - beta * M.spy_fo
        flag, stp = k_b7b(M.c, M.h, M.l, rs, M.tod, M.new, c["th"], c["f"] == "zero")
        return flag, stp, nan, False
    raise ValueError(fam)


def first_in_window(M: Month, flag, lo, hi):
    m = flag & M.isdec & (M.tod >= lo) & (M.tod <= hi) & (M.atr > 0)
    idx = np.flatnonzero(m)
    if not len(idx):
        return idx
    seg = np.cumsum(M.new)[idx]
    keep = np.r_[True, seg[1:] != seg[:-1]]
    return idx[keep]


def costs(M: Month, idx, xp, kind, side):
    e = M.c[idx]
    R = 0.25 * M.atr[idx]
    tier = np.where((np.abs(M.gap[idx]) >= 20) | (e < 5), 3.0, 1.0)
    gross = side * (xp - e) / R
    cost = (gates.SLIP_PS + e * gates.SLIP_BPS) * gates.tod_cost_mult(M.tod[idx]) * tier
    cost = cost + np.where(kind == 2, 0.0, (gates.SLIP_PS + xp * gates.SLIP_BPS) * tier)
    cost = cost + np.where(kind == 1, gates.STOP_EXTRA * tier, 0.0)
    return gross, gross - cost / R


def hedge(M: Month, idx, xr, side, r):
    e = M.c[idx]
    R = 0.25 * M.atr[idx]
    b = np.nan_to_num(M.beta[idx], nan=1.0)
    s0 = M.spy_c[idx]
    s1 = M.spy_c[xr]
    spy_ret = s1 / s0 - 1
    hc = 2 * (gates.SLIP_PS * np.abs(b) * e / s0 + gates.SLIP_BPS * np.abs(b) * e)
    return r - side * b * spy_ret * e / R - hc / R


def run_month(M: Month, G: list[dict], out: dict, base: dict, rng):
    cache = {}
    for c in G:
        sk = tuple((k, c.get(k)) for k in PARAMS[c["fam"]]) + (("fam", c["fam"]),)
        if sk not in cache:
            cache.clear()
            cache[sk] = signals(M, c)
        flag, stp, tg, dyn = cache[sk]
        lo, hi = WIN["full"] if c["win"] == "full" else GUEST[c["fam"]]
        if c["fam"] == "B6":
            lo, hi = GUEST["B6"]
        idx = first_in_window(M, flag, lo, hi)
        s = 1 if c["side"] == "long" else -1
        e = M.c[idx]
        R0 = 0.25 * M.atr[idx]
        if c["exit"] == "S":
            st = stp[idx]
            ok = np.isfinite(st) & ((s * (e - st)) > 0)
            idx, e, R0, st = idx[ok], e[ok], R0[ok], st[ok]
            tgt = tg[idx]
            tgt = np.where(s * (tgt - e) > 0, tgt, np.nan)
            use_dyn = dyn
        else:
            up, dn = GEOMS[c["exit"]]
            st = e - s * dn * R0
            tgt = e + s * up * R0
            use_dyn = False
        sides = np.full(len(idx), s, np.int64)
        xp, kind, xr = sim(idx, sides, M.c, M.h, M.l, M.tod, M.new, st, tgt, M.vwap, use_dyn)
        gross, r = costs(M, idx, xp, kind, s)
        rh = hedge(M, idx, xr, s, r)
        o = out.setdefault(c["id"], {k: [] for k in ("day", "sym", "tod", "xtod", "r", "rh", "kind", "gross")})
        o["day"].append(M.day[idx]); o["sym"].append(M.sym[idx]); o["tod"].append(M.tod[idx])
        o["xtod"].append(M.tod[xr]); o["r"].append(r); o["rh"].append(rh); o["kind"].append(kind); o["gross"].append(gross)
    # lab-geometry parity check: re-simulated gross vs the frames' r_* (+ the lab's 2c) on a random sample of rows
    samp = rng.choice(np.flatnonzero(M.isdec & (M.atr > 0)), size=min(20000, int(M.isdec.sum())), replace=False)
    for side, s in (("long", 1), ("short", -1)):
        for g, (up, dn) in GEOMS.items():
            e = M.c[samp]
            R0 = 0.25 * M.atr[samp]
            xp, kind, xr = sim(samp, np.full(len(samp), s, np.int64), M.c, M.h, M.l, M.tod, M.new, e - s * dn * R0,
                               e + s * up * R0, M.vwap, False)
            mine = s * (xp - e) / R0 - 2 * 0.01 / R0
            lab = M.labr[f"{side}_{g}"][samp]
            ok = np.isfinite(lab)
            base.setdefault("parity", []).append(float((np.abs(mine[ok] - lab[ok]) < 1e-3).mean()))
    # random same-side same-window baselines: one random decision bar per symbol-day in the window
    wins = {"full": WIN["full"], **{f"g{k}": v for k, v in GUEST.items()}}
    seg = np.cumsum(M.new)
    for wn, (lo, hi) in wins.items():
        m = M.isdec & (M.tod >= lo) & (M.tod <= hi) & (M.atr > 0)
        ii = np.flatnonzero(m)
        if not len(ii):
            continue
        key = rng.random(len(ii))
        df = pd.DataFrame({"i": ii, "s": seg[ii], "k": key}).sort_values(["s", "k"])
        pick = df.drop_duplicates("s")["i"].to_numpy().copy()
        pick.sort()
        for side, s in (("long", 1), ("short", -1)):
            for g, (up, dn) in list(GEOMS.items()) + [("hold", (np.inf, 1.0))]:
                e = M.c[pick]
                R0 = 0.25 * M.atr[pick]
                tgt = e + s * up * R0 if np.isfinite(up) else np.full(len(pick), np.nan)
                xp, kind, xr = sim(pick, np.full(len(pick), s, np.int64), M.c, M.h, M.l, M.tod, M.new,
                                   e - s * dn * R0, tgt, M.vwap, False)
                _, r = costs(M, pick, xp, kind, s)
                b = base.setdefault(f"{wn}|{side}|{g}", [0.0, 0])
                b[0] += float(r.sum()); b[1] += int(len(r))


def main():
    t0 = time.time()
    G = grid()
    assert len(G) == 368, len(G)
    feat = pd.read_parquet(DATA / "daily_feat.parquet")
    feat["date"] = pd.to_datetime(feat["date"]).dt.date
    feat = feat.set_index(["symbol", "date"])
    rv = pd.read_parquet(DATA / "rvol12.parquet")
    rv["date"] = pd.to_datetime(rv["date"]).dt.date
    rv = rv.set_index(["symbol", "date"])["rvol12"]
    dates = list(lib.regimes().index)
    dayidx = {d: i for i, d in enumerate(dates)}
    out, base, checks = {}, {}, {}
    rng = np.random.default_rng(20261012)
    import os
    months = os.environ.get("CWTB_MONTHS", "").split(",") if os.environ.get("CWTB_MONTHS") else lib.months()
    for month in months:
        a = pd.Timestamp(month + "-01")
        ht = pd.read_parquet(DATA / "headtail.parquet", filters=[("date", ">=", a), ("date", "<", a + pd.offsets.MonthBegin(1))])
        ht["symbol"] = ht["symbol"].astype(str)
        ht["date"] = pd.to_datetime(ht["date"]).dt.date
        ht["month"] = month
        M = Month(month, ht, feat, rv, dayidx)
        del ht
        checks[month] = M.check
        run_month(M, G, out, base, rng)
        print(month, len(M.c), M.check, round(time.time() - t0), flush=True)
        del M
    arrs = {}
    for cid, o in out.items():
        for k, v in o.items():
            arrs[f"{cid}|{k}"] = np.concatenate(v) if v else np.zeros(0)
    np.savez_compressed(DATA / "trades.npz", **arrs)
    par = base.pop("parity")
    json.dump({"baseline": {k: {"exp": v[0] / max(1, v[1]), "n": v[1]} for k, v in base.items()},
               "parity_mean": float(np.mean(par)), "parity_min": float(np.min(par)), "checks": checks,
               "dates": [str(d) for d in dates]}, open(DATA / "baseline.json", "w"), indent=1)
    print("done", round(time.time() - t0), "parity", np.mean(par), np.min(par), flush=True)


if __name__ == "__main__":
    main()
