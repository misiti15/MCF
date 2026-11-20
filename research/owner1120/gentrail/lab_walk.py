"""GB-GENTRAIL lab walk (PLAN.md): rebuild 2-year signal lists for every GEN hold / holdtr spec on the generator's own
panel (first signal per symbol-day inside the window) and walk C1..C7 on the 5-minute path to 15:55.
Usage: python lab_walk.py OUT.parquet [workers]. Data paths: env MCF_DATA_ROOT (frames + headtail) and MCF_EARN.
The locked block 2024-11..2025-02 is never read (lib refuses it; asserted). Educational only - not financial advice."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
DROOT = Path(os.environ.get("MCF_DATA_ROOT", "/home/user/MCF"))
LOCKED = {"2024-11", "2024-12", "2025-01", "2025-02"}
END = "2026-10-31"
CFG = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
# up, trr, tra, gb, chk  (C5 = 0.5 * C4 + 0.5 * C2, built after)
SIMS = {"C1": (0.0, 0.0, 0.0, 0.0, 0.0), "C2": (0.0, 1.0, 1.0, 0.0, 0.0), "C3": (0.0, 0.0, 1.0, 0.5, 0.0),
        "C4": (1.0, 0.0, 0.0, 0.0, 0.0), "C6": (0.0, 0.0, 0.0, 0.0, 2.0), "C7": (0.0, 0.0, 0.0, 0.0, 3.0)}


def specs():
    d = yaml.safe_load(open(REPO / "config" / "account_gen.yaml"))
    out = {}
    for k, v in d["strategies"].items():
        g = (v or {}).get("gen") or {}
        s = g.get("spec") or {}
        if s.get("geom") in ("hold", "holdtr") and s.get("conds"):
            out[k] = s
    return out


@numba.njit(cache=True)
def _mult(t):
    if t < 935:
        return 3.8
    if t < 950:
        return 2.1
    if t < 1030:
        return 1.4
    return 1.0


@numba.njit(cache=True)
def walk(h, l, c, i0, end, e, R, side, up, trr, tra, gb, chk, atr5, ecost, cm, extra):
    """One trade on a bar path h/l/c (entry at e after bar i0, bars i0+1..end; flat at c[end]).
    Returns (R net, rule_exit flag). Stop first in a bar; stop moves take effect from the next bar."""
    stop0 = e - side * R
    stop = stop0
    tgt = e + side * up * R
    mfe = 0.0
    best = e
    x = 0.0
    cd = 0
    for k in range(i0 + 1, end + 1):
        adv = l[k] if side == 1 else h[k]
        fav = h[k] if side == 1 else l[k]
        if side * (adv - stop) <= 0:
            x = stop
            cd = 2
            break
        if up > 0 and side * (fav - tgt) >= 0:
            x = tgt
            cd = 1
            break
        mfe = max(mfe, side * (fav - e) / R)
        if side == 1:
            best = max(best, fav)
        else:
            best = min(best, fav)
        ns = stop
        if trr > 0 and mfe >= tra:
            ns = e + side * (mfe - trr) * R
        if gb > 0 and mfe >= tra:
            ns = e + side * (1.0 - gb) * mfe * R
        if chk > 0 and atr5 > 0:
            ns = best - side * chk * atr5
        stop = max(stop, ns) if side == 1 else min(stop, ns)
    rule = 0
    if cd == 0:
        x = c[end]
    if cd == 1:
        rule = 1
    if cd == 2 and stop != stop0:
        rule = 1
    xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
    if rule == 1:
        xc += extra * (0.01 + x * 1e-4)
    return side * (x - e) / R - cm * (ecost + xc) / R, rule


@numba.njit(cache=True)
def walk_many(h, l, c, tod, dend, ent, Rv, cm, side, up, trr, tra, gb, chk, atr5, extra):
    n = len(ent)
    r = np.full(n, np.nan, np.float64)
    rf = np.zeros(n, np.int8)
    for q in range(n):
        i = ent[q]
        if i < 0 or not (Rv[q] > 0):
            continue
        end = dend[i]
        if end <= i:
            continue
        e = c[i]
        ec = (0.01 + e * 1e-4) * _mult(tod[i])
        r[q], rf[q] = walk(h, l, c, i, end, e, Rv[q], side[q], up, trr, tra, gb, chk, atr5[q], ec, cm[q], extra[q])
    return r, rf


def month_job(month: str):
    assert month not in LOCKED
    from mcf.research.arena import data as AD
    from mcf.research.arena.indicators import compute
    from mcf.research.generator import data as GD
    from mcf.research.generator.screen import _cmp
    from mcf.research.generator.spec import CONTEXT, WINDOWS

    lib = AD._lib()
    lib.DATA = DROOT / "research" / "history2y" / "data"
    GD.EARN = Path(os.environ.get("MCF_EARN", GD.EARN))
    SP = specs()
    need = sorted({c[0] for s in SP.values() for c in s["conds"] if c[0] not in CONTEXT})
    df = lib.load_month(month, columns=GD.LOAD_COLS, context=True)
    df = df[df["adv20"].to_numpy(float) >= GD.MIN_ADV].reset_index(drop=True)
    df = df[pd.Series(df["date"]).astype(str) <= END].reset_index(drop=True)
    if not len(df):
        return month, None
    df["symbol"] = df["symbol"].astype(str)
    ind = compute(df, names=need, context=False)
    a0 = pd.Timestamp(month + "-01")
    ht = pd.read_parquet(DROOT / "research/bdi/cwt/test_b/data/headtail.parquet", columns=["symbol", "date", "tod", "h", "l", "c"],
                         filters=[("date", ">=", a0), ("date", "<", a0 + pd.offsets.MonthBegin(1))])
    ht["symbol"] = ht["symbol"].astype(str)
    ht["date"] = pd.to_datetime(ht["date"]).dt.date
    ht = ht[ht["tod"] > 1500].merge(df[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="inner")
    P = pd.concat([pd.DataFrame({"symbol": df["symbol"], "date": df["date"], "tod": df["tod"].astype(np.int64),
                                 "h": df["high"].astype(float), "l": df["low"].astype(float),
                                 "c": df["close"].astype(float), "_fi": np.arange(len(df))}),
                   pd.DataFrame({"symbol": ht["symbol"], "date": ht["date"], "tod": ht["tod"].astype(np.int64),
                                 "h": ht["h"].astype(float), "l": ht["l"].astype(float), "c": ht["c"].astype(float),
                                 "_fi": -1})], ignore_index=True)
    P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    seg = pd.MultiIndex.from_arrays([P["symbol"].to_numpy(), pd.Index(P["date"]).astype(str)]).factorize()[0]
    new = np.r_[True, seg[1:] != seg[:-1]]
    last = np.r_[np.flatnonzero(new)[1:] - 1, len(P) - 1]
    dend = last[np.cumsum(new) - 1].astype(np.int64)
    first = np.flatnonzero(new)[np.cumsum(new) - 1]
    has_tail = pd.Series(P["tod"].to_numpy() >= 1550).groupby(seg).transform("max").to_numpy()
    fi = P["_fi"].to_numpy()
    f2P = np.full(len(df), -1, np.int64)
    f2P[fi[fi >= 0]] = np.flatnonzero(fi >= 0)
    ph, pl, pc = P["h"].to_numpy(float), P["l"].to_numpy(float), P["c"].to_numpy(float)
    pt = P["tod"].to_numpy(np.int64)
    pcp = np.r_[np.nan, pc[:-1]]
    pcp[new] = np.nan
    tr = np.fmax(ph, np.nan_to_num(pcp, nan=-np.inf)) - np.fmin(pl, np.nan_to_num(pcp, nan=np.inf))
    tr = np.where(np.isfinite(tr), tr, ph - pl)
    atr5_all = pd.Series(tr).groupby(seg).transform(lambda s: s.rolling(6, min_periods=1).mean()).to_numpy()
    tod = df["tod"].to_numpy()
    uni = (tod >= 950) & (tod <= 1500) & ~GD._blackout(df["symbol"].to_numpy(), df["date"].to_numpy())
    A = {"tod": tod, "adv20": df["adv20"].to_numpy(np.float32)}
    for k in need:
        A[k] = ind[k].to_numpy(np.float32).astype(np.float16)
    for k in CONTEXT:
        A[k] = df[k].to_numpy(np.float32).astype(np.float16)
    sd = seg[f2P]
    c = df["close"].to_numpy(float)
    Rv_all = 0.25 * df["atr_d"].to_numpy(float)
    cm_all = np.where((np.abs(df["gap"].to_numpy(float)) >= 20) | (c < 5), 3.0, 1.0)
    rows = []
    for name, s in SP.items():
        lo, hi = WINDOWS[s["window"]]
        m = uni & (tod >= lo) & (tod <= hi) & (A["adv20"] >= float(s["min_adv"]))
        for cn, op, v in s["conds"]:
            if cn in CONTEXT:
                m &= _cmp(A[cn], op, np.float16(v))
        idx = np.flatnonzero(m)
        for cn, op, v in s["conds"]:
            if cn in CONTEXT:
                continue
            idx = idx[_cmp(A[cn][idx].astype(np.float32), op, np.float32(np.float16(v)))]
        if not len(idx):
            continue
        ss = sd[idx]
        idx = idx[np.r_[True, ss[1:] != ss[:-1]]]
        ent = f2P[idx]
        idx, ent = idx[has_tail[ent]], ent[has_tail[ent]]
        if not len(idx):
            continue
        side = np.full(len(idx), 1 if s["side"] == "long" else -1, np.int64)
        res = {"setup": name, "geom": s["geom"], "side": s["side"], "window": s["window"],
               "symbol": df["symbol"].to_numpy()[idx], "date": pd.Series(df["date"].to_numpy()[idx]).astype(str).to_numpy(),
               "tod": tod[idx], "R_ps": Rv_all[idx], "atr5_R": atr5_all[ent] / Rv_all[idx]}
        own = "C1" if s["geom"] == "hold" else "C2"
        for cfg, (up, trr, tra, gb, chk) in SIMS.items():
            extra = np.full(len(idx), 0.0 if cfg == own else 1.0)
            r, rf = walk_many(ph, pl, pc, pt, dend, ent, Rv_all[idx], cm_all[idx], side, up, trr, tra, gb,
                              chk, atr5_all[ent], extra)
            res[cfg] = r
            res[cfg + "_rule"] = rf
        res["C5"] = 0.5 * res["C4"] + 0.5 * res["C2"]
        rows.append(pd.DataFrame(res))
    return month, (pd.concat(rows, ignore_index=True) if rows else None)


def main():
    out = sys.argv[1]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    lib_months = sorted(p.name.split("=", 1)[1] for p in (DROOT / "research/history2y/data/frames").glob("month=*"))
    ms = [m for m in lib_months if m not in LOCKED and m <= END[:7]]
    assert not set(ms) & LOCKED
    parts = []
    from multiprocessing import get_context
    with get_context("spawn").Pool(workers) as pool:
        for m, x in pool.imap_unordered(month_job, ms):
            print(m, 0 if x is None else len(x), flush=True)
            if x is not None:
                parts.append(x)
    X = pd.concat(parts, ignore_index=True).sort_values(["setup", "date", "tod", "symbol"]).reset_index(drop=True)
    assert not X["date"].between("2024-11-01", "2025-02-28").any()
    X.to_parquet(out, index=False)


if __name__ == "__main__":
    main()
