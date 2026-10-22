"""l3_1022 Part 3 step 1: every signal of L3-gap-slope-fromopen-FD on the open two-year frames (mask + window
09:50-15:00; refire chains cd1 / cd3 / cd6 and first-only flagged), each simulated on the 5-minute path under every
exit variant of PLAN.md (P0 t1s1, X1/X2 wider stop at the same $ risk, X3/X4 time stops, X5 scale-out), with production
costs (gates.prod_r conventions, time-of-day entry multiplier, x3 extended tier), market state at entry and ONE random
same-minute partner (another symbol, same date and bar, shorted with the same exits). Educational only - not
financial advice. The locked block is never read (lib refuses it; no_locked asserts it).

    python research/bdi/l3_1022/scripts/scan.py 3      # -> scratch l3_1022/sig/<month>.parquet
"""
from __future__ import annotations

import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

import l3c
from rc import g21c, gates, lib, no_locked

SLIP, BPS, XSTOP = gates.SLIP_PS, gates.SLIP_BPS, gates.STOP_EXTRA
EXITS = {  # name: (stop multiple k of 0.25 ATR, target distance in 0.25 ATR, time-stop bars, scale-out)
    "P0": (1.0, 1.0, None, False),
    "X1": (1.5, 1.0, None, False),
    "X2": (2.0, 1.0, None, False),
    "X3": (1.0, 1.0, 12, False),
    "X4": (1.0, 1.0, 24, False),
    "X5": (1.0, 1.0, None, True),
}
SEED = 20261022
try:
    TAIL = pd.read_parquet(l3c.SCRATCH / "tail.parquet")
    TAIL["symbol"] = TAIL["symbol"].astype(str)
    TAIL["date"] = pd.to_datetime(TAIL["date"]).dt.date
except FileNotFoundError:
    TAIL = None


def sim(i, end, c, h, l, tod, atr, tier, k, tgt, tbars, scale):
    """Short entry at close of bar i; bars i+1..end-1 of the same symbol-day. Returns (net R in units of k*0.25ATR,
    gross R, exit tod, kind 1 stop / 2 target / 3 time / 0 close)."""
    e = c[i]
    R0 = 0.25 * atr[i]
    Rr = k * R0
    stop, target = e + Rr, e - tgt * R0
    hh, ll, tt, cc = h[i + 1:end], l[i + 1:end], tod[i + 1:end], c[i + 1:end]
    n = len(hh)
    if n == 0:
        return np.nan, np.nan, np.nan, -1
    ecost = (SLIP + e * BPS) * gates.tod_cost_mult(np.array([tod[i]]))[0]
    xcost = SLIP + e * BPS
    if not scale:
        hs = np.flatnonzero(hh >= stop)
        ht = np.flatnonzero(ll <= target)
        js = hs[0] if len(hs) else n
        jt = ht[0] if len(ht) else n
        jtime = (tbars - 1) if (tbars is not None and tbars - 1 < n) else n
        j = min(js, jt, jtime)
        if j == n:   # held to the last bar's close
            px, kind, cost = cc[-1], 0, ecost + xcost
            jj = n - 1
        elif js == j:   # stop first inside a bar
            px, kind, cost = stop, 1, ecost + xcost + XSTOP
            jj = j
        elif jt == j:
            px, kind, cost = target, 2, ecost
            jj = j
        else:
            px, kind, cost = cc[j], 3, ecost + xcost
            jj = j
        gross = (e - px) / Rr
        return gross - tier * cost / Rr, gross, tt[jj], kind
    # scale-out: half at 0.5R (limit), the other half to 1R with its stop at entry once the first half filled
    t1 = e - 0.5 * R0
    hs = np.flatnonzero(hh >= stop)
    h1 = np.flatnonzero(ll <= t1)
    js = hs[0] if len(hs) else n
    j1 = h1[0] if len(h1) else n
    if js <= j1:   # stopped (both halves) before / in the bar of the first target
        if js == n:
            px = cc[-1]
            gross = (e - px) / R0
            return gross - tier * (ecost + xcost) / R0, gross, tt[-1], 0
        gross = -1.0
        return gross - tier * (ecost + xcost + XSTOP) / R0, gross, tt[js], 1
    leg1 = 0.5
    # second half from bar j1 (target may fill in the same bar; breakeven stop from the next bar)
    if ll[j1] <= target:
        return 0.5 * leg1 + 0.5 * 1.0 - tier * ecost / R0, 0.5 * leg1 + 0.5, tt[j1], 2
    hh2, ll2 = hh[j1 + 1:], ll[j1 + 1:]
    m = len(hh2)
    hs2 = np.flatnonzero(hh2 >= e)
    ht2 = np.flatnonzero(ll2 <= target)
    a = hs2[0] if len(hs2) else m
    b = ht2[0] if len(ht2) else m
    if a == m and b == m:
        px = cc[-1]
        leg2, c2, et, kind = (e - px) / R0, xcost, tt[-1], 0
    elif a <= b:
        leg2, c2, et, kind = 0.0, xcost + XSTOP, tt[j1 + 1 + a], 1
    else:
        leg2, c2, et, kind = 1.0, 0.0, tt[j1 + 1 + b], 2
    gross = 0.5 * leg1 + 0.5 * leg2
    return gross - tier * (ecost + 0.5 * c2) / R0, gross, et, kind


def month_job(month):
    t0 = time.time()
    f = lib.load_month(month, context=True)
    f["symbol"] = f["symbol"].astype(str)
    no_locked(f["date"].unique())
    m = g21c.load_mod(l3c.SETUP, "research/bdi/fullday/L3-gap-slope-fromopen-FD.py")
    with np.errstate(invalid="ignore"):
        f["_mk"] = np.asarray(m.mask(f), bool)
    # the frames stop at 15:00; append the 15:05..15:55 bars (tail.py) so exits hold to 15:55 like the lab outcome
    tl = TAIL[(TAIL["date"] >= f["date"].min()) & (TAIL["date"] <= f["date"].max())]
    f = pd.concat([f, tl.assign(_mk=False)], ignore_index=True)
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    sym, dat = f["symbol"].to_numpy(), f["date"].to_numpy()
    c, h, l, tod, atr = (f[k].to_numpy(float) for k in ("close", "high", "low", "tod", "atr_d"))
    gap = f["gap"].to_numpy(float)
    tier = np.where((np.abs(gap) >= 20) | (c < 5), 3.0, 1.0)
    key = pd.Series(sym).astype(str) + "|" + pd.Series(dat).astype(str)
    brk = np.r_[True, key.to_numpy()[1:] != key.to_numpy()[:-1]]
    starts = np.flatnonzero(brk)
    ends = np.r_[starts[1:], len(f)]
    end_of = np.repeat(ends, ends - starts)
    mk = f["_mk"].to_numpy(bool)
    elig = (atr > 0) & np.isfinite(f["r_short_t1s1"].to_numpy(float)) & (end_of - np.arange(len(f)) > 1)
    ok = mk & (tod >= 950) & (tod <= 1500) & elig
    hit = np.flatnonzero(ok)
    if not len(hit):
        return month, 0, 0.0
    flags = {}
    for name, (rf, cd) in {"cd1": (True, 1), "cd3": (True, 3), "cd6": (True, 6), "first": (False, 1)}.items():
        pos = g21c.chain(sym[hit], dat[hit], tod[hit], rf, cd)
        flags[name] = set(hit[pos].tolist())
    idx = np.array(sorted(set().union(*flags.values())), int)
    # SPY / QQQ VWAP side per (date, tod)
    ix = f[f["symbol"].isin(["SPY", "QQQ"])][["symbol", "date", "tod", "vwapDistPct"]]
    vw = ix.pivot_table(index=["date", "tod"], columns="symbol", values="vwapDistPct")
    # random partner per signal: same date and bar, eligible, other symbol
    rng = np.random.default_rng(SEED + int(month.replace("-", "")))
    el = np.flatnonzero(elig & (tod >= 950) & (tod <= 1500))
    dk = pd.Series(dat[el]).astype(str).to_numpy()
    tk = tod[el].astype(int)
    bucket = pd.DataFrame({"i": el, "k": np.char.add(np.char.add(dk.astype(str), "|"), tk.astype(str))}).groupby("k")["i"].apply(np.array).to_dict()
    rows = []
    for i in idx:
        cand = bucket.get(f"{dat[i]}|{int(tod[i])}")
        cand = cand[sym[cand] != sym[i]] if cand is not None else np.array([], int)
        p = int(rng.choice(cand)) if len(cand) else -1
        row = {"symbol": sym[i], "date": dat[i], "tod": int(tod[i]), "close": c[i], "atr": atr[i], "gap": gap[i],
               "fromOpen": f["fromOpen"].to_numpy(float)[i], "spy_fo": f["spy_fo"].to_numpy(float)[i],
               "qqq_fo": f["qqq_fo"].to_numpy(float)[i], "tier": tier[i], "lab_r": f["r_short_t1s1"].to_numpy(float)[i],
               "partner": sym[p] if p >= 0 else None}
        for nm in flags:
            row[nm] = i in flags[nm]
        for nm, (k, tg, tb, sc) in EXITS.items():
            r, g, et, kd = sim(i, end_of[i], c, h, l, tod, atr, tier[i], k, tg, tb, sc)
            row[f"r_{nm}"], row[f"g_{nm}"], row[f"et_{nm}"], row[f"k_{nm}"] = r, g, et, kd
            if p >= 0:
                rr, _, _, _ = sim(p, end_of[p], c, h, l, tod, atr, tier[p], k, tg, tb, sc)
            else:
                rr = np.nan
            row[f"rc_{nm}"] = rr
        rows.append(row)
    out = pd.DataFrame(rows)
    v = vw.reindex(pd.MultiIndex.from_arrays([out["date"], out["tod"]]))
    out["spy_vwap"] = v["SPY"].to_numpy() if "SPY" in v else np.nan
    out["qqq_vwap"] = v["QQQ"].to_numpy() if "QQQ" in v else np.nan
    (l3c.SCRATCH / "sig").mkdir(exist_ok=True)
    out.to_parquet(l3c.SCRATCH / "sig" / f"{month}.parquet")
    return month, len(out), round(time.time() - t0, 1)


def main():
    months = lib.months()
    if len(sys.argv) > 2:
        months = sys.argv[2].split(",")
    w = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    with Pool(w) as p:
        for r in p.imap_unordered(month_job, months):
            print(r, flush=True)


if __name__ == "__main__":
    main()
