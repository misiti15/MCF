"""Open-drive track (overnight 2026-11-21): opening drive / failed opening push setups, entries 09:50-10:30.
Engine follows research/ultimate_1119/top10/bench10.py conventions: decision at 5-min bar close (tod label = bar end),
entry = close of the minute before `tod`, exits walked minute by minute from minute `tod`: stop first (gap-through at
worse of open/stop), target only when traded through by >= $0.01, flat at the 15:55 open. Costs/book applied in score.py.
Short side = the long rule on the mirrored price series (p -> -p, high<->low, gap -> -gap).
Locked block 2024-11-01..2025-02-28 never read (pyarrow filter + assert).
Educational only - not financial advice."""
from __future__ import annotations

import sys
import zlib
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

TZ = "America/New_York"
LOCK = ("2024-11-01", "2025-02-28")
W = Path(__file__).resolve().parent
CACHE = Path("/home/user/MCF/data/cache_hist/1Min")
FRESH = Path("/home/user/MCF/data/cache_fresh/1Min")
NM = 390
KS = 9                       # decision bars 09:50 .. 10:30
TODS = np.array([950 + 5 * k if k < 2 else [950, 955, 1000, 1005, 1010, 1015, 1020, 1025, 1030][k] for k in range(KS)])
TODS = np.array([950, 955, 1000, 1005, 1010, 1015, 1020, 1025, 1030])
END = 20 + 5 * np.arange(KS) - 1   # minute index (0 = 09:30) of the last minute inside decision bar k
FLAT = 385                   # 15:55
MIN_ADV = 10e6

# config id -> (family, params, geometry)   geometry: "t1s1" = 0.25 ATR stop, 1R target; "orx15" = OR extreme stop, 1.5R target
CONFIGS = {}
for side in (1, -1):
    sd = "L" if side > 0 else "S"
    for rv in (1.0, 2.0):
        CONFIGS[f"OD1-orbdrive-rv{rv:g}-{sd}"] = ("OD1", dict(d=0.3, rv=rv), "t1s1", side)
    for p in (0.3, 0.6):
        CONFIGS[f"OD2-failpush-p{p:g}-{sd}"] = ("OD2", dict(p=p), "t1s1", side)
        CONFIGS[f"OD2-failpush-p{p:g}-orx-{sd}"] = ("OD2", dict(p=p), "orx15", side)
    for d in (0.5, 0.8):
        CONFIGS[f"OD3-firstpb-d{d:g}-{sd}"] = ("OD3", dict(d=d), "t1s1", side)
    for g in (2.0, 4.0):
        CONFIGS[f"OD4-gapfail-g{g:g}-{sd}"] = ("OD4", dict(g=g), "t1s1", side)
        CONFIGS[f"OD5-gapgo-g{g:g}-{sd}"] = ("OD5", dict(g=g), "t1s1", side)
    for rv in (1.0, 2.0):
        CONFIGS[f"OD6-failorb-rv{rv:g}-{sd}"] = ("OD6", dict(rv=rv), "t1s1", side)
        CONFIGS[f"OD6-failorb-rv{rv:g}-orx-{sd}"] = ("OD6", dict(rv=rv), "orx15", side)
ROUND2 = {}
for side in (1, -1):
    sd = "L" if side > 0 else "S"
    for g in (2.0, 4.0):
        ROUND2[f"OD7-gapdrive950-g{g:g}-{sd}"] = ("OD7", dict(g=g), "t1s1", side)
    ROUND2[f"OD8-drive950-d0.5-{sd}"] = ("OD8", dict(d=0.5), "t1s1", side)
import os as _os
ROUND3 = {}
for side in (1, -1):
    sd = "L" if side > 0 else "S"
    ROUND3[f"NULL-OD1-rv2-950-{sd}"] = ("N1", dict(d=0.3, rv=2.0), "t1s1", side)
    ROUND3[f"NULL-OD2-p0.6-950-orx-{sd}"] = ("N2", dict(p=0.6), "orx15", side)
if _os.environ.get("OD_ROUND") == "3":
    CONFIGS = ROUND3
if _os.environ.get("OD_ROUND") == "2":
    CONFIGS = ROUND2
#  OD7 long = gap up >= g% and the 09:50 bar closes above the open and above VWAP -> enter at 09:50 (no trigger)
#  OD8 long = 09:50 close >= open + 0.5 ATR and above VWAP (any gap) -> enter at 09:50
# NOTE on direction naming: every rule below is written LONG; the -S config runs it on the mirrored series.
#  OD1 long  = up-drive (09:50 close >= open + 0.3 ATR) then first 5-min close above the 09:30-09:49 high (OR20H), 09:55-10:30
#  OD2 long  = failed DOWN push: OR20 low <= open - p ATR, then first close back above the open AND above VWAP with no new
#              low below OR20L since 09:50 (the push failed) -> long (the short = failed UP push, the BDI 11-20 pattern)
#  OD3 long  = first pullback after a strong drive: 09:50 close >= open + d ATR and in the top quarter of the OR; after
#              09:50 a pullback of >= 38.2% of the open->high drive that holds above VWAP, then the first 5-min close above
#              the prior 5-min bar's high
#  OD4 long  = gap down <= -g% then first close above the open and above VWAP (gap-and-fail of the gap side)
#  OD5 long  = gap up >= g%, 09:50 close above the open, then first close above OR20H (gap-and-go)
#  OD6 long  = failed ORB low break: a 5-min close below OR20L (09:55-10:25), then a later close above the OR20 midpoint


def bars_hist(sym):
    d = pads.dataset(str(CACHE / f"{sym}.parquet"), format="parquet")
    fld = pads.field("__index_level_0__")
    b = d.to_table(filter=(fld < pd.Timestamp(LOCK[0], tz=TZ)) | (fld >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    ds = b.index.date.astype(str)
    assert not ((ds >= LOCK[0]) & (ds <= LOCK[1])).any()
    return b


def bars_fresh(sym):
    b = pd.read_parquet(FRESH / f"{sym}.parquet")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    ds = b.index.date.astype(str)
    assert not ((ds >= LOCK[0]) & (ds <= LOCK[1])).any()
    return b


def grid(b):
    """days x 390 minute matrices (NaN where no bar)."""
    mi = (b.index.hour * 60 + b.index.minute - 570).to_numpy()
    ok = (mi >= 0) & (mi < NM)
    b = b[ok]
    mi = mi[ok]
    day = b.index.date.astype(str)
    days, di = np.unique(day, return_inverse=True)
    out = {}
    for k in ("open", "high", "low", "close", "volume"):
        a = np.full((len(days), NM), np.nan)
        a[di, mi] = b[k].to_numpy(float)
        out[k] = a
    return days, out


def daily_from_grid(days, g):
    """prior ATR14 (TR, regular hours), ADV20 ($, prior days), gap % vs prior regular close (T2 only)."""
    hi = np.nanmax(g["high"], 1)
    lo = np.nanmin(g["low"], 1)
    cl = pd.DataFrame(g["close"]).ffill(axis=1).iloc[:, -1].to_numpy()
    op = pd.DataFrame(g["open"]).bfill(axis=1).iloc[:, 0].to_numpy()
    dv = np.nansum(g["close"] * g["volume"], 1)
    pc = np.r_[np.nan, cl[:-1]]
    tr = np.nanmax(np.c_[hi - lo, np.abs(hi - pc), np.abs(lo - pc)], 1)
    atr = pd.Series(tr).rolling(14, min_periods=10).mean().shift(1).to_numpy()
    adv = pd.Series(dv).shift(1).rolling(20, min_periods=5).mean().to_numpy()
    gap = (op / pc - 1) * 100
    return pd.DataFrame({"date": days, "atr_d": atr, "adv20": adv, "gap": gap})


def features(O_, H_, L_, C_, V_, op, gap):
    """long-form features from (possibly mirrored) minute matrices. Returns dict of arrays (ndays,) / (ndays, KS)."""
    n = O_.shape[0]
    f = {}
    f["orh"] = np.nanmax(H_[:, :20], 1)
    f["orl"] = np.nanmin(L_[:, :20], 1)
    Hc = np.fmax.accumulate(np.nan_to_num(H_, nan=-np.inf), axis=1)
    Lc = np.fmin.accumulate(np.nan_to_num(L_, nan=np.inf), axis=1)
    Cf = pd.DataFrame(C_).ffill(axis=1).to_numpy()
    pv = np.nancumsum(C_ * V_, 1)
    vv = np.nancumsum(V_, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = pv / np.where(vv > 0, vv, np.nan)
    f["c"] = Cf[:, END]                     # 5-min bar close
    f["vw"] = vw[:, END]
    f["hod"] = Hc[:, END]
    f["lod"] = Lc[:, END]
    bh = np.full((n, KS), np.nan)
    bl = np.full((n, KS), np.nan)
    for k, e in enumerate(END):
        bh[:, k] = np.nanmax(H_[:, e - 4:e + 1], 1)
        bl[:, k] = np.nanmin(L_[:, e - 4:e + 1], 1)
    f["bh"], f["bl"] = bh, bl
    # low since 09:50 up to bar k (for pullback / no-new-low checks)
    L50 = np.fmin.accumulate(np.nan_to_num(L_[:, 20:], nan=np.inf), axis=1)
    f["lo_since50"] = np.c_[np.full(n, np.inf), L50[:, END[1:] - 20]]
    f["op"] = op
    f["gap"] = gap
    return f


def first_true(m):
    """index of first True per row, -1 if none."""
    any_ = m.any(1)
    return np.where(any_, m.argmax(1), -1)


def rule(fam, prm, f, atr, rv):
    op, c, vw = f["op"][:, None], f["c"], f["vw"]
    orh, orl = f["orh"][:, None], f["orl"][:, None]
    A = atr[:, None]
    ks = np.arange(KS)[None, :]
    if fam == "OD1":
        d0 = (f["c"][:, 0] - f["op"]) / atr
        m = (ks >= 1) & (c > orh) & (d0 >= prm["d"])[:, None] & (rv >= prm["rv"])[:, None]
    elif fam == "OD2":
        push = (f["op"] - f["orl"]) / atr
        m = (push >= prm["p"])[:, None] & (c > op) & (c > vw) & (f["lo_since50"] >= orl)
    elif fam == "OD3":
        d0 = (f["c"][:, 0] - f["op"]) / atr
        strong = (d0 >= prm["d"]) & (f["c"][:, 0] >= f["orl"] + 0.75 * (f["orh"] - f["orl"]))
        hod = f["hod"]
        pb = f["lo_since50"] <= hod - 0.382 * (hod - op)
        pb_held = f["lo_since50"] > f["vw"]          # pullback low stays above (current) VWAP
        prevh = np.c_[np.full(len(op), np.inf), f["bh"][:, :-1]]
        m = strong[:, None] & (ks >= 1) & pb & pb_held & (c > prevh) & (c > vw)
    elif fam == "OD4":
        m = (f["gap"] <= -prm["g"])[:, None] & (c > op) & (c > vw)
    elif fam == "OD5":
        m = (f["gap"] >= prm["g"])[:, None] & (f["c"][:, 0] > f["op"])[:, None] & (ks >= 1) & (c > orh)
    elif fam == "OD6":
        brk = (c < orl) & (ks >= 1) & (ks <= 7)
        seen = np.logical_or.accumulate(brk, axis=1)
        prev_seen = np.c_[np.zeros(len(op), bool), seen[:, :-1]]
        m = prev_seen & (c > (orh + orl) / 2) & (rv >= prm["rv"])[:, None]
    elif fam == "OD7":
        m = ((f["gap"] >= prm["g"]) & (f["c"][:, 0] > f["op"]) & (f["c"][:, 0] > f["vw"][:, 0]))[:, None] & (ks == 0)
    elif fam == "OD8":
        m = (((f["c"][:, 0] - f["op"]) / atr >= prm["d"]) & (f["c"][:, 0] > f["vw"][:, 0]))[:, None] & (ks == 0)
    elif fam == "N1":   # unconditioned null for OD1: its 09:50-known filters only, entry at 09:50
        d0 = (f["c"][:, 0] - f["op"]) / atr
        m = ((d0 >= prm["d"]) & (rv >= prm["rv"]))[:, None] & (ks == 0)
    elif fam == "N2":   # unconditioned null for OD2: push known at 09:50, entry at 09:50
        m = ((f["op"] - f["orl"]) / atr >= prm["p"])[:, None] & (ks == 0)
    else:
        raise ValueError(fam)
    m &= np.isfinite(c) & (A > 0)
    return first_true(m)


def walk(H, L, O, e_idx, entry, stop, tgt):
    """long-form walk on one day's minute arrays from minute e_idx+1 (= minute `tod`)."""
    a, z = e_idx + 1, FLAT
    h, lo, o = H[a:z], L[a:z], O[a:z]
    okm = np.isfinite(h)
    sh = okm & (lo <= stop)
    th = okm & (h >= tgt + 0.01) if np.isfinite(tgt) else np.zeros_like(okm)
    i_s = sh.argmax() if sh.any() else 10**6
    i_t = th.argmax() if th.any() else 10**6
    if i_s <= i_t and i_s < 10**6:
        return min(o[i_s], stop) if np.isfinite(o[i_s]) else stop, 1, a + i_s
    if i_t < 10**6:
        return tgt, 2, a + i_t
    if np.isfinite(O[FLAT]):
        return O[FLAT], 0, FLAT
    fin = np.flatnonzero(np.isfinite(h))
    if not len(fin):
        return np.nan, -1, -1
    # last close not passed; use last open-ish proxy (close unknown here) -> caller passes close array via O? use high/low mid
    return np.nan, -1, -1


def sym_job(args):
    sym, which, rng_seed = args
    try:
        b = bars_hist(sym) if which == "T1" else bars_fresh(sym)
    except Exception as ex:  # noqa: BLE001
        return sym, None
    if len(b) < 1000:
        return sym, None
    days, g = grid(b)
    if which == "T1":
        dd = DAILY.get(sym)
        if dd is None:
            return sym, None
        dd = dd.set_index("date").reindex(days)
        atr, adv, gap = dd.atr_d.to_numpy(float), dd.adv20.to_numpy(float), dd.gap.to_numpy(float)
    else:
        dd = daily_from_grid(days, g)
        atr, adv, gap = dd.atr_d.to_numpy(float), dd.adv20.to_numpy(float), dd.gap.to_numpy(float)
        keep = (days >= "2023-01-03") & (days <= "2024-09-13")
        atr = np.where(keep, atr, np.nan)
    O, H, L, C, V = (g[k] for k in ("open", "high", "low", "close", "volume"))
    op = O[:, 0]
    v20 = np.nansum(V[:, :20], 1)
    rv = v20 / pd.Series(v20).shift(1).rolling(14, min_periods=5).mean().to_numpy()
    rv = np.nan_to_num(rv, nan=0.0)
    base_ok = np.isfinite(op) & np.isfinite(atr) & (atr > 0) & (adv >= MIN_ADV) & (op >= 5) & np.all(np.isfinite(C[:, :20]).sum(1)[:, None] >= 10, 1)
    rng = np.random.default_rng(rng_seed)
    rows = []
    for side in (1, -1):
        if side > 0:
            Om, Hm, Lm, Cm = O, H, L, C
            gp = gap
        else:
            Om, Hm, Lm, Cm = -O, -L, -H, -C
            gp = -gap
        f = features(Om, Hm, Lm, Cm, V, Om[:, 0], gp)
        for cid, (fam, prm, geom, s) in CONFIGS.items():
            if s != side:
                continue
            k = rule(fam, prm, f, atr, rv)
            k = np.where(base_ok, k, -1)
            for di in np.flatnonzero(k >= 0):
                kk = int(k[di])
                e_idx = END[kk]
                entry = f["c"][di, kk]
                if geom == "t1s1":
                    R = 0.25 * atr[di]
                    stop, tgt = entry - R, entry + R
                else:  # orx15: stop 1c beyond the OR extreme on the losing side, target 1.5R
                    stop = f["lod"][di, kk] - 0.01
                    R = entry - stop
                    if not (R > 0) or R > 1.5 * atr[di]:
                        continue
                    tgt = entry + 1.5 * R
                px, kind, xi = walk(Hm[di], Lm[di], Om[di], e_idx, entry, stop, tgt)
                if kind < 0:
                    continue
                # matched random null: same symbol-day, side, geometry rule (risk), 3 random decision bars 09:50-10:30
                nr = []
                for kr in rng.integers(0, KS, 3):
                    ei = END[kr]
                    en = Cm[di, ei]
                    if not np.isfinite(en):
                        continue
                    pxr, kdr, _ = walk(Hm[di], Lm[di], Om[di], ei, en, en - R, en + (R if geom == "t1s1" else 1.5 * R))
                    if kdr < 0:
                        continue
                    nr.append((int(TODS[kr]), side * en, side * pxr, kdr))
                rows.append(dict(cfg=cid, fam=fam, symbol=sym, date=days[di], tod=int(TODS[kk]), side=side,
                                 entry=side * entry, stop=side * stop, tgt=side * tgt, risk=R, gap=gap[di], px=side * px,
                                 kind=kind, xt=int(xi), rv=rv[di], atr=atr[di], adv=adv[di],
                                 n_tod=[x[0] for x in nr], n_entry=[x[1] for x in nr], n_px=[x[2] for x in nr],
                                 n_kind=[x[3] for x in nr]))
    return sym, pd.DataFrame(rows) if rows else None


DAILY: dict = {}


def init_t1():
    d = pd.read_parquet(W / "daily_t1.parquet")
    for s, g in d.groupby("symbol"):
        DAILY[s] = g[["date", "atr_d", "adv20", "gap"]]


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "T1":
        syms = sorted(p.stem for p in CACHE.glob("*.parquet"))
        init = init_t1
    else:
        syms = sorted(p.stem for p in FRESH.glob("*.parquet"))
        init = None
    if len(sys.argv) > 2:
        syms = syms[: int(sys.argv[2])]
    out = []
    with Pool(3, initializer=init) as p:
        for i, (s, o) in enumerate(p.imap_unordered(sym_job, [(s, which, zlib.crc32(s.encode())) for s in syms], chunksize=4)):
            if o is not None:
                out.append(o)
            if i % 100 == 0:
                print(i, s, flush=True)
    T = pd.concat(out, ignore_index=True)
    T.to_parquet(W / f"trades_{which}{_os.environ.get('OD_ROUND', '')}.parquet")
    print(len(T), T.groupby("cfg").size().to_string())
