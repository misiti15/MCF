"""reddit1021 prep: per-symbol arrays (1-minute RTH bars, 5-minute bars, ATR5 / VWAP / EMA20 / volume averages, the
day's levels OR / PM / AH / PD, tier, eligibility) saved as <scratch>/prep/<SYM>.npz. See PLAN.md.

    python prep.py idx            # SPY, QQQ (extended hours from 1-minute bars)
    python prep.py stk            # stock universe (extended hours from 30-minute bars), 4 processes
Educational only - not financial advice."""
from __future__ import annotations

import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

from common import SCR, assert_open, load_ext, load_rth

import lib  # noqa: E402  (research/history2y)

OUT = SCR / "prep"
OUT.mkdir(parents=True, exist_ok=True)
NB = 78


def calendar() -> list:
    e = load_ext("SPY", "1Min")
    d = sorted(set(e.index.date))
    return d


CAL = None
ADV = None


def _init():
    global CAL, ADV
    CAL = calendar()
    d = lib.daily()
    ADV = d.set_index(["symbol", "date"])["adv20"]


def prep(sym: str, tf: str) -> str:
    rth = load_rth(sym)
    ext = load_ext(sym, tf)
    if rth is None or not len(rth):
        return f"{sym} no rth"
    days = sorted(set(rth.index.date))
    idx = {d: i for i, d in enumerate(days)}
    nd = len(days)
    mins = ((rth.index.hour * 60 + rth.index.minute) - 570).to_numpy()
    di = np.array([idx[d] for d in rth.index.date])
    # 1-minute arrays, concatenated by day
    order = np.lexsort((mins, di))
    m_o, m_h, m_l, m_c = (rth[c].to_numpy(float)[order] for c in ("open", "high", "low", "close"))
    m_min = mins[order].astype(np.int16)
    m_day = di[order]
    start = np.searchsorted(m_day, np.arange(nd + 1))
    # 5-minute bars [nd, 78]
    k = mins // 5
    g = pd.DataFrame({"d": di, "k": k, "o": rth["open"].to_numpy(float), "h": rth["high"].to_numpy(float),
                      "l": rth["low"].to_numpy(float), "c": rth["close"].to_numpy(float),
                      "v": rth["volume"].to_numpy(float)}).groupby(["d", "k"], sort=True)
    a = g.agg(o=("o", "first"), h=("h", "max"), l=("l", "min"), c=("c", "last"), v=("v", "sum")).reset_index()
    seq = a.copy()
    pc = seq["c"].shift(1)
    tr = pd.concat([seq.h - seq.l, (seq.h - pc).abs(), (seq.l - pc).abs()], axis=1).max(axis=1)
    seq["atr_prev"] = tr.rolling(14).mean().shift(1)
    seq["ema20"] = seq["c"].ewm(span=20, adjust=False).mean()
    seq["v20_prev"] = seq["v"].rolling(20).mean().shift(1)
    seq["v_prev"] = seq["v"].shift(1)
    seq["c_prev"] = pc
    typ = (seq.h + seq.l + seq.c) / 3
    seq["vwap"] = (typ * seq.v).groupby(seq.d).cumsum() / seq.v.groupby(seq.d).cumsum().replace(0, np.nan)
    F = {}
    for col in ("o", "h", "l", "c", "v", "atr_prev", "ema20", "v20_prev", "v_prev", "c_prev", "vwap"):
        arr = np.full((nd, NB), np.nan)
        kk = seq["k"].to_numpy()
        ok = (kk >= 0) & (kk < NB)
        arr[seq["d"].to_numpy()[ok], kk[ok]] = seq[col].to_numpy(float)[ok]
        F[col] = arr
    # levels per day: OR_H OR_L PM_H PM_L AH_H AH_L PD_H PD_L
    LV = np.full((nd, 8), np.nan)
    dl = rth.groupby(rth.index.date).agg(h=("high", "max"), l=("low", "min"), c=("close", "last"), o=("open", "first"))
    orb = rth[mins < 15]
    orl = orb.groupby(orb.index.date).agg(h=("high", "max"), l=("low", "min"))
    if ext is not None and len(ext):
        hm = ext.index.hour * 100 + ext.index.minute
        pm = ext[(hm >= 400) & (hm < 930)]
        pml = pm.groupby(pm.index.date).agg(h=("high", "max"), l=("low", "min"))
        ah = ext[(hm >= 1600) & (hm < 2000)]
        ahl = ah.groupby(ah.index.date).agg(h=("high", "max"), l=("low", "min"))
    else:
        pml = ahl = pd.DataFrame(columns=["h", "l"])
    cal_i = {d: i for i, d in enumerate(CAL)}
    prevd = np.empty(nd, dtype=object)
    gap = np.full(nd, np.nan)
    for i, d in enumerate(days):
        if d in orl.index:
            LV[i, 0], LV[i, 1] = orl.loc[d, "h"], orl.loc[d, "l"]
        if d in pml.index:
            LV[i, 2], LV[i, 3] = pml.loc[d, "h"], pml.loc[d, "l"]
        ci = cal_i.get(d)
        p = CAL[ci - 1] if ci else None
        if p is not None and (d - p).days > 5:      # prior session inside the locked block / not loaded
            p = None
        prevd[i] = p
        if p is not None:
            if p in ahl.index:
                LV[i, 4], LV[i, 5] = ahl.loc[p, "h"], ahl.loc[p, "l"]
            if p in dl.index:
                LV[i, 6], LV[i, 7] = dl.loc[p, "h"], dl.loc[p, "l"]
                gap[i] = dl.loc[d, "o"] / dl.loc[p, "c"] - 1
    price = dl["o"].to_numpy(float)
    tier = np.where((price < 5) | (np.abs(np.nan_to_num(gap)) >= 0.20), 3.0, 1.0)
    adv = np.array([ADV.get((sym, d), np.nan) for d in days], float)
    assert_open(days)
    np.savez_compressed(OUT / f"{sym}.npz", days=np.array([str(d) for d in days]), start=start, m_o=m_o, m_h=m_h,
                        m_l=m_l, m_c=m_c, m_min=m_min, LV=LV, tier=tier, adv=adv, gap=gap,
                        **{f"f_{k}": v for k, v in F.items()})
    return f"{sym} ok {nd}"


def _p(args):
    try:
        return prep(*args)
    except Exception as e:  # noqa: BLE001
        return f"{args[0]} failed {type(e).__name__}: {e}"


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "idx":
        _init()
        for s in ("SPY", "QQQ"):
            print(prep(s, "1Min"))
    else:
        syms = (SCR / "stk_syms.txt").read_text().split()
        syms = [s for s in syms if (SCR / "ext_30Min" / f"{s}.parquet").exists() and not (OUT / f"{s}.npz").exists()]
        with Pool(4, initializer=_init) as pool:
            for i, r in enumerate(pool.imap_unordered(_p, [(s, "30Min") for s in syms]), 1):
                if i % 100 == 0 or "failed" in r:
                    print(i, r, flush=True)
        print("done", len(syms))
