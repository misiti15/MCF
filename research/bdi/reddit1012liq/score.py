"""Reddit liquidity study (PLAN.md): score the pre-declared grid on the open two-year history, month by month.

    python research/bdi/reddit1012liq/score.py          # -> data/daystats.npz, data/controls.json

Per configuration and session: sum of lab R (0.25 x daily ATR, costs in), trade count, wins, sum of structural R.
Also the B3 (CWT14) replicas and the random same-side baselines. The rule-19 locked block is never loaded.
Educational only - not financial advice.
"""
from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

DATA = HERE / "data"
LEVELS = ("PD", "OR", "H60", "D5", "D20")
SIDES = ("short", "long")
XS = (0.05, 0.15)
TRIGS = ("lvl", "open", "rng")
KS = (5, 15)
ATTS = (1, 2)
STOPS = ("S", "A")
TGTS = ("2R", "2.5R", "NL", "EOD")
MGMTS = ("none", "BE", "TS", "BE+TS")
WIN = (950, 1500)
S_BUF, S_MAXRISK = 0.05, 1.0
BE_R, TS_BARS, TS_R = 1.0, 3, 0.25


def sigsets():
    return list(itertools.product(LEVELS, SIDES, XS, TRIGS, KS))


def exits():
    return list(itertools.product(ATTS, STOPS, TGTS, MGMTS))


def cname(sg, ex) -> str:
    L, side, x, trig, k = sg
    a, st, tg, mg = ex
    return f"LIQ-{L}-{side}-x{x}-{trig}-k{k}-a{a}-{st}-{tg}-{mg}"


# ------------------------------------------------------------------------------------------------ kernels
@numba.njit(cache=True)
def k_liq(h, l, c, O, L, avail, atr, new, W, x, trig):
    """Short-side sweep machine on k-bars (the long side is called with negated prices). Returns candidate arrays:
    trigger bar, sweep extreme E (through the trigger bar), the level at the sweep start."""
    n = len(c)
    cj = np.empty(n, np.int64)
    cE = np.empty(n)
    cL = np.empty(n)
    m = 0
    ins = False
    s = 0
    Ls = 0.0
    Os = 0.0
    E = 0.0
    rlow = 1e18
    prevc = 0.0
    for i in range(n):
        if new[i]:
            ins = False
            prevc = O[i]                      # the day open for the first bar
        if ins and i - s >= W:
            ins = False                       # accepted break: no trigger within W bars
        if ins:
            E = max(E, h[i])
            fire = False
            if trig == 0:
                fire = c[i] < Ls
            elif trig == 1:
                fire = c[i] < Os
            else:
                fire = i >= s + 2 and c[i] < rlow and c[i] < Ls
            if fire:
                cj[m] = i
                cE[m] = E
                cL[m] = Ls
                m += 1
                ins = False
            elif i > s:
                rlow = min(rlow, l[i])
        else:
            Li = L[i]
            if avail[i] and not np.isnan(Li) and prevc < Li and h[i] >= Li + x * atr[i]:
                ins = True
                s = i
                Ls = Li
                Os = prevc
                E = h[i]
                rlow = 1e18
                if trig == 0 and c[i] < Ls:
                    cj[m] = i
                    cE[m] = E
                    cL[m] = Ls
                    m += 1
                    ins = False
        prevc = c[i]
    return cj[:m], cE[:m], cL[:m]


@numba.njit(cache=True)
def h60_level(h, new, H):
    """Established swing high: the session high through bar i-1 if it was already set by bar i-H (held >= H bars)."""
    n = len(h)
    out = np.full(n, np.nan)
    hod = np.empty(n)
    st = 0
    for i in range(n):
        if new[i]:
            st = i
            hod[i] = h[i]
        else:
            hod[i] = max(hod[i - 1], h[i])
        if i - H >= st and hod[i - 1] == hod[i - H]:
            out[i] = hod[i - 1]
    return out


@numba.njit(cache=True)
def k_b3(c, h, l, L, p, atr, new, upper):
    """research/bdi/cwt/test_b/score.py k_b3 (lowvol off, every bar usable) - the CWT14 replica."""
    n = len(c)
    flag = np.zeros(n, np.bool_)
    inexc = False
    stale = False
    st = 0
    for i in range(n):
        if new[i]:
            inexc = False
            stale = False
        if np.isnan(L[i]):
            continue
        beyond = (h[i] >= L[i] + p * atr[i]) if upper else (l[i] <= L[i] - p * atr[i])
        inside = (c[i] < L[i]) if upper else (c[i] > L[i])
        if not inexc and not stale and beyond:
            inexc = True
            st = i
        if inexc:
            if inside:
                if i - st <= 3:
                    flag[i] = True
                inexc = False
            elif i - st > 3:
                inexc = False
                stale = True
        elif stale and inside:
            stale = False
    return flag


@numba.njit(cache=True)
def sim(idx, side, e, stop0, tgt, risk, be, ts, o, h, l, c, tod, new, gap_through):
    """From the bar after entry: stop first (gap-through at the open), then the target, then management for the next
    bar (time stop: exit at the next bar open; break-even move). Else the close of the last bar <= 15:55.
    kind: 1 stop, 2 target, 3 time (15:55), 4 time stop."""
    n = len(idx)
    xp = np.empty(n)
    kind = np.empty(n, np.int8)
    xr = np.empty(n, np.int64)
    N = len(c)
    for j in range(n):
        i = idx[j]
        s = side
        stop = stop0[j]
        best = 0.0
        k = i + 1
        done = False
        while k < N and not new[k] and tod[k] <= 1555:
            if (s > 0 and l[k] <= stop) or (s < 0 and h[k] >= stop):
                px = stop
                if gap_through and ((s > 0 and o[k] < stop) or (s < 0 and o[k] > stop)):
                    px = o[k]
                xp[j] = px
                kind[j] = 1
                xr[j] = k
                done = True
                break
            tg = tgt[j]
            if not np.isnan(tg) and ((s > 0 and h[k] >= tg) or (s < 0 and l[k] <= tg)):
                xp[j] = tg
                kind[j] = 2
                xr[j] = k
                done = True
                break
            fav = h[k] if s > 0 else l[k]
            best = max(best, s * (fav - e[j]) / risk[j])
            if ts and (k - i) >= 3 and best < 0.25 and k + 1 < N and not new[k + 1] and tod[k + 1] <= 1555:
                xp[j] = o[k + 1]
                kind[j] = 4
                xr[j] = k + 1
                done = True
                break
            if be and best >= 1.0:
                stop = max(stop, e[j]) if s > 0 else min(stop, e[j])
            k += 1
        if not done:
            xp[j] = c[k - 1]
            kind[j] = 3
            xr[j] = k - 1
    return xp, kind, xr


# ------------------------------------------------------------------------------------------------ month
class Month:
    def __init__(self, month, dayidx):
        b = pd.read_parquet(DATA / "bars" / f"month={month}.parquet")
        b["date"] = pd.to_datetime(b["date"]).dt.date
        self.b = b
        sy, dt = b["symbol"].to_numpy(), b["date"].to_numpy()
        self.new = np.r_[True, (sy[1:] != sy[:-1]) | (dt[1:] != dt[:-1])]
        self.seg = np.cumsum(self.new) - 1
        g = lambda k: b[k].to_numpy(float)
        self.o, self.h, self.l, self.c, self.vwap = g("o"), g("h"), g("l"), g("c"), g("vwap")
        self.tod = b["tod"].to_numpy(np.int64)
        self.bb = b["b"].to_numpy(np.int64)
        self.atr, self.gap = g("atr_d"), g("gap")
        self.lv = {"PD": (g("pdh"), g("pdl")), "D5": (g("d5h"), g("d5l")), "D20": (g("d20h"), g("d20l"))}
        orh = pd.Series(np.where(self.tod <= 1000, self.h, np.nan)).groupby(self.seg).transform("max").to_numpy(float)
        orl = pd.Series(np.where(self.tod <= 1000, self.l, np.nan)).groupby(self.seg).transform("min").to_numpy(float)
        self.lv["OR"] = (orh, orl)
        self.dopen = pd.Series(self.o).groupby(self.seg).transform("first").to_numpy(float)
        self.day = np.array([dayidx[d] for d in dt], np.int64)
        self.kb = {5: self._kbars(5), 15: self._kbars(15)}

    def _kbars(self, k):
        """k-minute bars: (rows of the last 5-min bar, h, l, c, O proxy, new, tod_end ok)."""
        if k == 5:
            r = np.arange(len(self.c))
            return dict(r=r, h=self.h, l=self.l, c=self.c, new=self.new, tod=self.tod, ok=np.ones(len(r), bool))
        grp = self.seg * 100 + self.bb // (k // 5)
        newg = np.r_[True, grp[1:] != grp[:-1]]
        gid = np.cumsum(newg) - 1
        last = np.r_[np.flatnonzero(newg)[1:] - 1, len(grp) - 1]
        h = pd.Series(self.h).groupby(gid).max().to_numpy()
        lo = pd.Series(self.l).groupby(gid).min().to_numpy()
        c = self.c[last]
        new = self.new[np.flatnonzero(newg)]
        tod = self.tod[last]
        end = 570 + k * (self.bb[last] // (k // 5) + 1)
        ok = tod == (end // 60) * 100 + end % 60            # the group's last 5-min bar exists
        return dict(r=last, h=h, l=lo, c=c, new=new, tod=tod, ok=ok)

    def candidates(self, L, side, x, trig, k):
        kb = self.kb[k]
        r = kb["r"]
        s = 1 if side == "long" else -1
        # short semantics; long = negated prices
        hh, ll, cc = (kb["h"], kb["l"], kb["c"]) if s < 0 else (-kb["l"], -kb["h"], -kb["c"])
        O = np.r_[np.nan, cc[:-1]]
        O = np.where(kb["new"], (self.dopen[r] if s < 0 else -self.dopen[r]), O)
        atr = self.atr[r]
        if L == "H60":
            lev = h60_level(hh, kb["new"], 60 // k)
            avail = np.ones(len(r), bool)
        else:
            hi, lo = self.lv[L]
            lev = hi[r] if s < 0 else -lo[r]
            avail = (self.tod[r] >= 1005) if L == "OR" else np.ones(len(r), bool)
        j, E, Ls = k_liq(hh, ll, cc, O, lev, avail, atr, kb["new"], 60 // k, x, TRIGS.index(trig))
        ok = kb["ok"][j]
        rows = r[j]
        if s > 0:
            E, Ls = -E, -Ls
        keep = ok & (self.tod[rows] >= WIN[0]) & (self.tod[rows] <= WIN[1])
        return rows[keep], E[keep], Ls[keep]


def trade_params(M, rows, E, side, stop, tgt):
    s = 1 if side == "long" else -1
    e = M.c[rows]
    atr = M.atr[rows]
    Rl = 0.25 * atr
    if stop == "S":
        st = E - s * S_BUF * atr
        risk = s * (e - st)
        valid = (risk > 0) & (risk <= S_MAXRISK * atr)
    else:
        st = e - s * Rl
        risk = Rl.copy()
        valid = np.ones(len(rows), bool)
    if tgt == "2R":
        tg = e + s * 2.0 * risk
    elif tgt == "2.5R":
        tg = e + s * 2.5 * risk
    elif tgt == "NL":
        tg = M.vwap[rows].copy()
        valid &= s * (tg - e) >= 2.0 * risk
    else:
        tg = np.full(len(rows), np.nan)
    return e, st, tg, risk, valid


def costs(M, rows, xp, kind, s, e):
    R = 0.25 * M.atr[rows]
    tier = np.where((np.abs(M.gap[rows]) >= 20) | (e < 5), 3.0, 1.0)
    gross = s * (xp - e)
    cost = (gates.SLIP_PS + e * gates.SLIP_BPS) * gates.tod_cost_mult(M.tod[rows]) * tier
    cost = cost + np.where(kind == 2, 0.0, (gates.SLIP_PS + xp * gates.SLIP_BPS) * tier)
    cost = cost + np.where(kind == 1, gates.STOP_EXTRA * tier, 0.0)
    return (gross - cost) / R, gross


def first_per_seg(M, rows, valid):
    """Index (into rows) of the first valid candidate per symbol-day."""
    ii = np.flatnonzero(valid)
    if not len(ii):
        return ii
    sg = M.seg[rows[ii]]
    return ii[np.r_[True, sg[1:] != sg[:-1]]]


def run_exits(M, rows, E, side, ex, gap_through=True):
    """-> trades dict (row, r_lab, r_struct, kind, attempt) for one candidate set and one exit configuration."""
    a, stop, tgt, mg = ex
    s = 1 if side == "long" else -1
    e, st, tg, risk, valid = trade_params(M, rows, E, side, stop, tgt)
    be, ts = mg in ("BE", "BE+TS"), mg in ("TS", "BE+TS")
    first = first_per_seg(M, rows, valid)
    out = {"row": [], "r": [], "rs": [], "kind": [], "att": []}

    def go(ii, att):
        xp, kind, xr = sim(rows[ii], s, e[ii], st[ii], tg[ii], risk[ii], be, ts, M.o, M.h, M.l, M.c, M.tod, M.new, gap_through)
        r, gross = costs(M, rows[ii], xp, kind, s, e[ii])
        out["row"].append(rows[ii]); out["r"].append(r); out["rs"].append(r * 0.25 * M.atr[rows[ii]] / risk[ii])
        out["kind"].append(kind); out["att"].append(np.full(len(ii), att, np.int8))
        return xr, gross

    xr, gross = go(first, 1)
    if a == 2 and len(first):
        # second attempt: the next valid candidate of the same symbol-day entered after attempt 1 exited, if it lost
        seg_c = M.seg[rows]
        nxt = []
        pos = np.searchsorted(rows, xr, side="right")          # rows are sorted ascending within the month
        for q, f in enumerate(first):
            if gross[q] > 0:
                continue
            p = pos[q]
            while p < len(rows) and seg_c[p] == seg_c[f]:
                if valid[p] and rows[p] > xr[q]:
                    nxt.append(p)
                    break
                p += 1
        if nxt:
            go(np.array(nxt, np.int64), 2)
    return {k: (np.concatenate(v) if v else np.zeros(0)) for k, v in out.items()}


def main():
    t0 = time.time()
    SG, EX = sigsets(), exits()
    NC = len(SG) * len(EX)
    assert NC == 7680, NC
    dates = list(lib.regimes().index)
    dayidx = {d: i for i, d in enumerate(dates)}
    D = len(dates)
    S = np.zeros((NC, D), np.float32)
    SS = np.zeros((NC, D), np.float32)
    Nn = np.zeros((NC, D), np.int32)
    Wn = np.zeros((NC, D), np.int32)
    ctrl = {}
    rng = np.random.default_rng(20261012)
    rep = {"B3-PDH-p0.10-short": ("PD", "short", 0.10), "B3-PDL-p0.10-long": ("PD", "long", 0.10),
           "B3-PDL-p0.05-long": ("PD", "long", 0.05), "B3-ORL-p0.10-long": ("OR", "long", 0.10)}
    for month in lib.months():
        M = Month(month, dayidx)
        for si, sg in enumerate(SG):
            rows, E, _ = M.candidates(*sg)
            for ei, ex in enumerate(EX):
                cid = si * len(EX) + ei
                T = run_exits(M, rows, E, sg[1], ex)
                if not len(T["r"]):
                    continue
                d = M.day[T["row"].astype(np.int64)]
                np.add.at(S[cid], d, T["r"]); np.add.at(SS[cid], d, T["rs"])
                np.add.at(Nn[cid], d, 1); np.add.at(Wn[cid], d, (T["r"] > 0).astype(np.int32))
        # B3 replicas (CWT14): first close back inside within 3 bars, t05s1, full window; both fill rules
        for nm, (L, side, p) in rep.items():
            upper = side == "short"
            lev = M.lv[L][0] if upper else M.lv[L][1]
            lev = np.where(M.tod >= 1005, lev, np.nan) if L == "OR" else lev
            f = k_b3(M.c, M.h, M.l, lev, p, M.atr, M.new, upper)
            f &= (M.tod >= WIN[0]) & (M.tod <= WIN[1])
            ii = np.flatnonzero(f)
            ii = ii[np.r_[True, M.seg[ii][1:] != M.seg[ii][:-1]]] if len(ii) else ii
            s = -1 if upper else 1
            e = M.c[ii]
            Rl = 0.25 * M.atr[ii]
            for gt in (False, True):
                xp, kind, xr = sim(ii, s, e, e - s * Rl, e + s * 0.5 * Rl, Rl, False, False, M.o, M.h, M.l, M.c,
                                   M.tod, M.new, gt)
                r, _ = costs(M, ii, xp, kind, s, e)
                key = f"{nm}-t05s1" + ("-gapfill" if gt else "")
                cc = ctrl.setdefault(key, {"day": [], "r": []})
                cc["day"].append(M.day[ii]); cc["r"].append(r)
        # random same-side bar per symbol-day in the window (stop A)
        m = (M.tod >= WIN[0]) & (M.tod <= WIN[1])
        ii = np.flatnonzero(m)
        key = rng.random(len(ii))
        df = pd.DataFrame({"i": ii, "s": M.seg[ii], "k": key}).sort_values(["s", "k"])
        pick = np.sort(df.drop_duplicates("s")["i"].to_numpy())
        for side in SIDES:
            s = 1 if side == "long" else -1
            e = M.c[pick]
            Rl = 0.25 * M.atr[pick]
            for tg in ("2R", "EOD"):
                for mg in ("none", "BE+TS"):
                    tgt = e + s * 2 * Rl if tg == "2R" else np.full(len(pick), np.nan)
                    xp, kind, xr = sim(pick, s, e, e - s * Rl, tgt, Rl, "BE" in mg, "TS" in mg, M.o, M.h, M.l, M.c,
                                       M.tod, M.new, True)
                    r, _ = costs(M, pick, xp, kind, s, e)
                    cc = ctrl.setdefault(f"random-{side}-A-{tg}-{mg}", {"day": [], "r": []})
                    cc["day"].append(M.day[pick]); cc["r"].append(r)
        print(month, len(M.c), round(time.time() - t0), flush=True)
        del M
    np.savez_compressed(DATA / "daystats.npz", S=S, SS=SS, N=Nn, W=Wn)
    out = {}
    for k, v in ctrl.items():
        day = np.concatenate(v["day"]); r = np.concatenate(v["r"])
        tr = pd.DataFrame({"date": np.array(dates)[day], "r": r})
        out[k] = gates.summary(tr)
        np.savez_compressed(DATA / f"ctrl_{k}.npz", day=day, r=r)
    json.dump({"controls": out, "dates": [str(d) for d in dates], "n_configs": NC,
               "names": [cname(sg, ex) for sg in SG for ex in EX]}, open(DATA / "controls.json", "w"), indent=1)
    print("done", round(time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
