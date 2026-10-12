"""CWT package A families A1-A4, A6-A9 (A5 is in a5.py): the pre-declared grids (TESTPLAN.md section 2 + the CWT-A
amendment) and the per-symbol signal + exit simulation. One trade per symbol-day per configuration (the first
qualifying signal inside the configuration's window). Educational only - not financial advice.
"""
from __future__ import annotations

import itertools

import numpy as np

from engine import (LAST, NM, Sym, bar_tod, exit_geom, exit_half_2r, exit_hold_days, exit_overnight, exit_struct, kidx)

TGEOMS = ("t1s1", "t05s1", "t1s05")

# ------------------------------------------------------------------------------------------------ config table
CONFIGS: list[dict] = []
KEY: dict[tuple, int] = {}


def _add(fam, **p):
    key = (fam,) + tuple(sorted(p.items()))
    KEY[key] = len(CONFIGS)
    CONFIGS.append({"cid": len(CONFIGS), "family": fam, **p})


def cid(fam, **p):
    return KEY[(fam,) + tuple(sorted(p.items()))]


WIN = {"A1": {"full": (935, 1500), "guest": (935, 1030)},
       "A2": {"full": (935, 1500), "guest": (935, 1200)},
       "A3": {"full": (935, 1500), "guest": (935, 1130)},
       "A4": {"full": (935, 1500), "guest": (945, 1030)},
       "A6": {"full": (935, 1500), "guest": (935, 1100)},
       "A7": {"full": (935, 1500), "guest": (1030, 1500)},
       "A8": {"full": (1020, 1500), "guest": (1020, 1200)},
       "A9": {"full": (935, 1500), "guest": (935, 1130)}}

for u, t, x, w in itertools.product(("r3_30", "r3_50", "streak3_r5_50"), ("T1", "T2"), ("S", "ON") + TGEOMS, ("full", "guest")):
    _add("A1", univ=u, trig=t, exit=x, win=w)
for x, w in itertools.product(("S",) + TGEOMS, ("full", "guest")):
    _add("A1", univ="day3", trig="or5l", exit=x, win=w)
for g, h, t, x, w in itertools.product((10, 20, 30), (950, 1015), ("T1", "T2"), ("S",) + TGEOMS, ("full", "guest")):
    _add("A2", gap=g, hset=h, trig=t, exit=x, win=w)
for q, c, sd, x, w in itertools.product((0.1, 0.2, 0.3), ("none", "cat"), ("long", "short"), ("S", "t1s1", "t1s05"), ("full", "guest")):
    _add("A3", q=q, cat=c, side=sd, exit=x, win=w)
for k, sd, x, w in itertools.product((3, 6), ("long", "short"), ("S", "t1s1"), ("full", "guest")):
    _add("A4", var="a_narrow", k=k, side=sd, exit=x, win=w)
for rv, sd, x, w in itertools.product((1.5, 2.5), ("long", "short"), ("S", "t1s1"), ("full", "guest")):
    _add("A4", var="b_rvol", rvol=rv, side=sd, exit=x, win=w)
for g, ref, sd, x, w in itertools.product((0.3, 0.5), ("pd", "d5"), ("short", "long"), ("S",) + TGEOMS, ("full", "guest")):
    _add("A6", g=g, ref=ref, side=sd, exit=x, win=w)
for G, E, t, x, w in itertools.product((5, 10), ("out", "earn"), ("T1", "T2"), ("S",) + TGEOMS, ("full", "guest")):
    _add("A7", gap=G, E=E, trig=t, exit=x, win=w)
for g, E, c, x, w in itertools.product((3, 5), ("out", "earn"), (0.25, 0.40), ("S", "S2") + TGEOMS, ("full", "guest")):
    _add("A8", gap=g, E=E, c=c, exit=x, win=w)
for g, E, k, x, w in itertools.product((3, 5), ("out", "earn"), (0.25, 0.40), ("S",) + TGEOMS, ("full", "guest")):
    _add("A9", gap=g, E=E, k=k, trig="vwap", exit=x, win=w)
for x, w in itertools.product(("S",) + TGEOMS, ("full", "guest")):
    _add("A9", gap=3, E="out", k=0.25, trig="prevhigh", exit=x, win=w)


def kwin(fam, w):
    lo, hi = WIN[fam][w]
    return kidx(lo), kidx(hi)


def _first(mask: np.ndarray, k0: int, k1: int) -> int:
    seg = mask[k0:k1 + 1]
    return k0 + int(np.argmax(seg)) if seg.any() else -1


def _exits(s, d, m0, side, e, stop, exits, tgt_s=np.nan):
    """r for each named exit."""
    out = {}
    for x in exits:
        if x in ("t1s1", "t05s1", "t1s05"):
            out[x] = exit_geom(s, d, m0, side, e, x)
        elif x == "S":
            out[x] = exit_struct(s, d, m0, side, e, stop, tgt_s)
        elif x == "ON":
            out[x] = exit_overnight(s, d, m0, side, e, stop)
        elif x == "S2":
            out[x] = exit_hold_days(s, d, m0, side, e, stop, 2)
    return out


def _emit(rows, fam, s, d, m0, sgn, out: dict, **p):
    for x, r in out.items():
        if np.isfinite(r):
            rows.append((cid(fam, exit=x, **p), d, m0, sgn, float(r), x))


# ------------------------------------------------------------------------------------------------ families
def a1(s: Sym, rows):
    ex = ("S", "ON") + TGEOMS
    for d in np.flatnonzero(s.ok):
        univs = []
        if s.run3[d] >= 30:
            univs.append("r3_30")
        if s.run3[d] >= 50:
            univs.append("r3_50")
        if s.upstreak[d] >= 3 and s.run5[d] >= 50:
            univs.append("streak3_r5_50")
        day3 = (s.d2_ret[d] >= 8 and s.d2_rvol[d] >= 2 and s.pdh[d] <= s.h2[d] and s.pdl[d] >= s.l2[d]
                and 0.98 * s.h2[d] <= s.open_d[d] <= s.h2[d])
        if not univs and not day3:
            continue
        c5, vw = s.c5[d], s.vw5[d]
        sig = {"T1": c5 < s.pc[d], "T2": (c5 < s.pc[d]) & (c5 < vw)}
        for w in ("full", "guest"):
            k0, k1 = kwin("A1", w)
            if univs:
                for t, m in sig.items():
                    k = _first(m, k0, k1)
                    if k < 0 or 5 * k + 5 >= NM:
                        continue
                    m0 = 5 * k + 5
                    e = s.O[d, m0]
                    out = _exits(s, d, m0, -1, e, s.hod5[d, k], ex)
                    for u in univs:
                        _emit(rows, "A1", s, d, m0, -1, out, univ=u, trig=t, win=w)
            if day3:
                k = _first(c5 < s.l5[d, 0], max(k0, 1), k1)
                if k >= 0:
                    m0 = 5 * k + 5
                    e = s.O[d, m0]
                    _emit(rows, "A1", s, d, m0, -1, _exits(s, d, m0, -1, e, s.hod5[d, k], ("S",) + TGEOMS),
                          univ="day3", trig="or5l", win=w)


def a2(s: Sym, rows, desc):
    ex = ("S",) + TGEOMS
    for d in np.flatnonzero(s.ok & (s.gap >= 10)):
        if s.gap[d] >= 20:
            desc.append((s.sym, s.dates[d], float(s.gap[d]), float(s.cl[d] < s.open_d[d]), int(bar_tod(s.hodk[d, -1]))))
        c5, vw, h5, l5 = s.c5[d], s.vw5[d], s.h5[d], s.l5[d]
        kk = np.arange(len(c5))
        after = kk > s.hodk[d]
        rv = s.rv5[d] >= 3
        prev_low = np.r_[np.nan, l5[:-1]]
        trig = {"T1": after & (c5 < vw), "T2": after & (h5 < s.hod5[d]) & (c5 < prev_low)}
        for h in (950, 1015):
            hset = s.hodk[d] <= kidx(h)
            for t, m in trig.items():
                mm = m & hset & rv
                for w in ("full", "guest"):
                    k = _first(mm, *kwin("A2", w))
                    if k < 0:
                        continue
                    m0 = 5 * k + 5
                    out = _exits(s, d, m0, -1, s.O[d, m0], s.hod5[d, k], ex)
                    for g in (10, 20, 30):
                        if s.gap[d] >= g:
                            _emit(rows, "A2", s, d, m0, -1, out, gap=g, hset=h, trig=t, win=w)


def _stop_entry(s, d, level, side, m_lo, m_hi):
    """First minute in [m_lo, m_hi] trading through `level` (buy stop above / sell stop below): (minute, fill)."""
    if m_lo > m_hi:
        return -1, np.nan
    seg = s.H[d, m_lo:m_hi + 1] > level if side > 0 else s.L[d, m_lo:m_hi + 1] < level
    if not seg.any():
        return -1, np.nan
    m = m_lo + int(np.argmax(seg))
    o = s.O[d, m]
    return m, (max(level, o) if side > 0 else min(level, o))


def _mwin(fam, w):
    lo, hi = WIN[fam][w]
    to_m = lambda t: (t // 100) * 60 + t % 100 - 570
    return to_m(lo), to_m(hi) - 1                     # trigger minutes [lo, hi)


def a3(s: Sym, rows):
    for d in np.flatnonzero(s.ok):
        atr = s.atr[d]
        cat = abs(s.d1_gap[d]) >= 4 and s.d1_rvol[d] >= 2
        for side in (1, -1):
            if side > 0:
                qv = (s.pdh[d] - s.pc[d]) / atr
                lvl = s.pdh[d]
                if not (s.open_d[d] < lvl and np.nanmax(s.H[d, :5]) <= lvl):
                    continue
            else:
                qv = (s.pc[d] - s.pdl[d]) / atr
                lvl = s.pdl[d]
                if not (s.open_d[d] > lvl and np.nanmin(s.L[d, :5]) >= lvl):
                    continue
            qs = [q for q in (0.1, 0.2, 0.3) if qv < q]
            if not qs:
                continue
            for w in ("full", "guest"):
                m0, e = _stop_entry(s, d, lvl, side, *_mwin("A3", w))
                if m0 < 0 or m0 > LAST:
                    continue
                stop = min(s.pc[d], e - 0.05 * atr) if side > 0 else max(s.pc[d], e + 0.05 * atr)
                out = {"S": exit_half_2r(s, d, m0, side, e, stop), "t1s1": exit_geom(s, d, m0, side, e, "t1s1"),
                       "t1s05": exit_geom(s, d, m0, side, e, "t1s05")}
                sd = "long" if side > 0 else "short"
                for q in qs:
                    for c in (("none", "cat") if cat else ("none",)):
                        _emit(rows, "A3", s, d, m0, side, out, q=q, cat=c, side=sd, win=w)


def a4(s: Sym, rows):
    for d in np.flatnonzero(s.ok & (np.abs(s.gap) >= 3)):
        side = 1 if s.gap[d] > 0 else -1
        sd = "long" if side > 0 else "short"
        h5, l5 = s.h5[d], s.l5[d]
        rng = h5 - l5
        for k in (3, 6):
            if not np.all(np.diff(rng[:k]) < 0):
                continue
            hi, lo = np.nanmax(h5[:k]), np.nanmin(l5[:k])
            lvl, stop = (hi, lo) if side > 0 else (lo, hi)
            for w in ("full", "guest"):
                a, b = _mwin("A4", w)
                m0, e = _stop_entry(s, d, lvl, side, max(a, 5 * k), b)
                if m0 < 0 or m0 > LAST:
                    continue
                out = {"S": exit_struct(s, d, m0, side, e, stop), "t1s1": exit_geom(s, d, m0, side, e, "t1s1")}
                _emit(rows, "A4", s, d, m0, side, out, var="a_narrow", k=k, side=sd, win=w)
        rv15 = s.rvol_m[d, 14]
        if not np.isfinite(rv15) or rv15 < 1.5:
            continue
        hi, lo = np.nanmax(h5[:3]), np.nanmin(l5[:3])
        mid = (hi + lo) / 2
        lvl = hi if side > 0 else lo
        for w in ("full", "guest"):
            a, b = _mwin("A4", w)
            m0, e = _stop_entry(s, d, lvl, side, max(a, 15), b)
            if m0 < 0 or m0 > LAST:
                continue
            tgt = e + side * 3 * abs(e - mid)
            out = {"S": exit_struct(s, d, m0, side, e, mid, tgt), "t1s1": exit_geom(s, d, m0, side, e, "t1s1")}
            for rv in (1.5, 2.5):
                if rv15 >= rv:
                    _emit(rows, "A4", s, d, m0, side, out, var="b_rvol", rvol=rv, side=sd, win=w)


def a6(s: Sym, rows):
    ex = ("S",) + TGEOMS
    kp_max = kidx(1030)
    for d in np.flatnonzero(s.ok):
        gthr = s.atr[d] / s.pc[d] * 100
        for side in (-1, 1):
            gs = [g for g in (0.3, 0.5) if (s.gap[d] >= g * gthr if side < 0 else s.gap[d] <= -g * gthr)]
            if not gs:
                continue
            for ref in ("pd", "d5"):
                if side < 0:
                    lvl = s.pdh[d] if ref == "pd" else s.hi5[d]
                    poke = s.h5[d] > lvl
                    back = s.c5[d] < lvl
                else:
                    lvl = s.pdl[d] if ref == "pd" else s.lo5[d]
                    poke = s.l5[d] < lvl
                    back = s.c5[d] > lvl
                if not np.isfinite(lvl):
                    continue
                kp = _first(poke, 0, kp_max)
                if kp < 0:
                    continue
                for w in ("full", "guest"):
                    k0, k1 = kwin("A6", w)
                    k = _first(back, max(k0, kp), k1)
                    if k < 0:
                        continue
                    m0 = 5 * k + 5
                    stop = s.hod5[d, k] if side < 0 else s.lod5[d, k]
                    out = _exits(s, d, m0, side, s.O[d, m0], stop, ex, tgt_s=s.pc[d])
                    for g in gs:
                        _emit(rows, "A6", s, d, m0, side, out, g=g, ref=ref, side=("short" if side < 0 else "long"), win=w)


def a7(s: Sym, rows, earn):
    ex = ("S",) + TGEOMS
    k1030 = kidx(1030)
    for d in np.flatnonzero(s.ok & (s.gap <= -5)):
        Es = [E for E, f in (("out", not earn["black"][d]), ("earn", earn["eday"][d])) if f]
        if not Es:
            continue
        c5, vw, h5, l5 = s.c5[d], s.vw5[d], s.h5[d], s.l5[d]
        kk = np.arange(len(c5))
        above = (h5 > vw) & (kk <= k1030)
        cond = np.logical_or.accumulate(above)
        or30h = np.nanmax(h5[:6])
        t1 = cond & (kk >= k1030) & (c5 < vw)
        reach = (h5 >= vw) | ((kk >= 6) & (h5 >= or30h))
        lowerhalf = (c5 - l5) < 0.5 * (h5 - l5)
        t2 = (cond | (h5 > vw)) & reach & lowerhalf
        fh = np.nanmax(h5[:k1030 + 1])
        for t, m in (("T1", t1), ("T2", t2)):
            for w in ("full", "guest"):
                k = _first(m, *kwin("A7", w))
                if k < 0:
                    continue
                m0 = 5 * k + 5
                stop = fh if k >= k1030 else s.hod5[d, k]
                out = _exits(s, d, m0, -1, s.O[d, m0], stop, ex)
                for G in (5, 10):
                    if s.gap[d] <= -G:
                        for E in Es:
                            _emit(rows, "A7", s, d, m0, -1, out, gap=G, E=E, trig=t, win=w)


def a8(s: Sym, rows, earn):
    ex = ("S", "S2") + TGEOMS
    k15 = kidx(1015)
    for d in np.flatnonzero(s.ok & (s.gap >= 3)):
        Es = [E for E, f in (("out", not earn["black"][d]), ("earn", earn["eday"][d])) if f]
        if not Es:
            continue
        if not (s.rv5[d, k15] >= 2 and np.nanmin(s.l5[d, :k15 + 1]) > s.pc[d] and s.c5[d, k15] > s.vw5[d, k15]):
            continue
        ch, cl = np.nanmax(s.h5[d, k15 - 5:k15 + 1]), np.nanmin(s.l5[d, k15 - 5:k15 + 1])
        width = (ch - cl) / s.atr[d]
        cs = [c for c in (0.25, 0.40) if width <= c]
        if not cs:
            continue
        for w in ("full", "guest"):
            k0, k1 = kwin("A8", w)
            k_ent = -1
            for k in range(k15 + 1, k1 + 1):
                if s.l5[d, k] < cl:
                    break
                if k >= k0 and s.c5[d, k] > ch:
                    k_ent = k
                    break
            if k_ent < 0:
                continue
            m0 = 5 * k_ent + 5
            out = _exits(s, d, m0, 1, s.O[d, m0], cl, ex)
            for g in (3, 5):
                if s.gap[d] >= g:
                    for E in Es:
                        for c in cs:
                            _emit(rows, "A8", s, d, m0, 1, out, gap=g, E=E, c=c, win=w)


def a9(s: Sym, rows, earn):
    ex = ("S",) + TGEOMS
    for d in np.flatnonzero(s.ok & (s.gap >= 3)):
        Es = [E for E, f in (("out", not earn["black"][d]), ("earn", earn["eday"][d])) if f]
        if not Es:
            continue
        c5, vw, h5 = s.c5[d], s.vw5[d], s.h5[d]
        kk = np.arange(len(c5))
        rv = s.rv5[d] >= 2
        cross = (c5 > vw) & (np.r_[np.inf, c5[:-1]] <= np.r_[np.nan, vw[:-1]])
        prevh = c5 > np.r_[np.nan, h5[:-1]]
        for kp in (0.25, 0.40):
            lvl = s.open_d[d] - kp * (s.open_d[d] - s.pc[d])
            jc = _first(s.lod5[d] <= lvl, 0, len(c5) - 1)
            if jc < 0:
                continue
            trigs = [("vwap", cross & (kk >= jc) & rv)]
            if kp == 0.25 and s.gap[d] >= 3 and "out" in Es:
                trigs.append(("prevhigh", prevh & (kk >= jc) & rv))
            for t, m in trigs:
                for w in ("full", "guest"):
                    k = _first(m, *kwin("A9", w))
                    if k < 0:
                        continue
                    m0 = 5 * k + 5
                    out = _exits(s, d, m0, 1, s.O[d, m0], s.lod5[d, k], ex)
                    if t == "vwap":
                        for g in (3, 5):
                            if s.gap[d] >= g:
                                for E in Es:
                                    _emit(rows, "A9", s, d, m0, 1, out, gap=g, E=E, k=kp, trig=t, win=w)
                    else:
                        _emit(rows, "A9", s, d, m0, 1, out, gap=3, E="out", k=0.25, trig=t, win=w)
