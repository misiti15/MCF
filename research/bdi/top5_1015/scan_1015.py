"""top5_1015 step 3-4: execution-quality variants of the 5 most-traded live setups on the open two-year history.
Pre-declaration: PLAN.md (written before this was run). Educational only - not financial advice.

    python research/bdi/top5_1015/scan_1015.py parity   # simulator == gates.lab_trades on 2025-06, coil kernel == b4a
    python research/bdi/top5_1015/scan_1015.py          # -> $SCR/trades.parquet (scratch, deleted after the report)

Reuses top5_1014/scan_top5.py (CWT14 numba kernel, heat score) and refire1014/scan.py (head / tail rows).
The rule-19 locked block 2024-11-01..2025-02-28 is never loaded: lib.months() lists open months only and
lib.load_month refuses locked months; head/tail rows are read per open month; MCF_HIST_ALLOW_LOCKED is never set.
"""
from __future__ import annotations

import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numba
import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1014"), str(ROOT / "research" / "bdi" / "refire1014"),
                str(ROOT / "research" / "history2y"), str(ROOT / "research" / "heat" / "candidates"),
                str(ROOT / "research" / "bdi" / "cwt" / "live"), str(ROOT)]
import lib  # noqa: E402
import scan  # noqa: E402
import cwt_live_lib as CL  # noqa: E402
import scan_top5 as T4  # noqa: E402  (yesterday's CWT14 kernel _b3, cwt_levels, heat weights W9)
from _regime_common import regime_score  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top5_1015")
SEED = 20261015
K_CTRL = 5

ORL, ORLV, PDL = "CWT14-failbrk-orl-p05-long", "CWT14-failbrk-orl-p05-lowvol-long", "CWT14-failbrk-pdl-p05-long"
H, COIL = "heat_fade_short-FD", "CWT12-coil-k4-long"
CWT14 = {ORL: dict(level="OR", vr=np.inf), ORLV: dict(level="OR", vr=1.0), PDL: dict(level="PD", vr=np.inf)}
BASE = {s: dict(side=1, up=0.5, dn=1.0, win=(950, 1500), adv=95e6) for s in (ORL, ORLV, PDL)}
BASE[COIL] = dict(side=1, up=0.5, dn=1.0, win=(950, 1130), adv=95e6)
BASE[H] = dict(side=-1, up=1.0, dn=1.0, win=(950, 1500), adv=125e6)
COIL_P = dict(nco=4, tight=0.5, close=0.25)

# ------------------------------------------------------------------------------------------------ the grid (PLAN.md)
# exit/entry params: em entry mode (0 market at signal close, 1 limit ex R better good ek bars, 2 next bar close,
# 3 next bar close if it moved in the trade's direction), tsb/tsr time stop bars / min best R, be breakeven R,
# so/sof scale-out R / fraction, xt exit time (HHMM), kind std | mirror | rebound | sar, sig = signal variant
EX0 = dict(em=0, ex=0.0, ek=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555, kind="std", sig="P")


def grid():
    G = []
    for s in (ORL, ORLV, PDL, H, COIL):
        t1 = s == H
        G += [(s, "P", "parent", {}),
              (s, "X01", "timestop", dict(tsb=3, tsr=0.2)), (s, "X02", "timestop", dict(tsb=6, tsr=0.2)),
              (s, "X03", "timestop", dict(tsb=12, tsr=0.25)),
              (s, "X04", "breakeven", dict(be=0.5 if t1 else 0.25)), (s, "X05", "breakeven", dict(be=0.75 if t1 else 0.35)),
              (s, "X06", "scaleout", dict(so=0.5) if t1 else dict(so=0.25)),
              (s, "X07", "scaleout", dict(so=0.3) if t1 else dict(so=0.5, up=1.0)),
              (s, "X08", "stop", dict(dn=0.75)), (s, "X09", "stop", dict(dn=0.6)),
              (s, "X10", "limit", dict(em=1, ex=0.1, ek=3)), (s, "X11", "limit", dict(em=1, ex=0.2, ek=3)),
              (s, "X12", "wait1", dict(em=2)), (s, "X13", "wait1confirm", dict(em=3)),
              (s, "X14", "flow3", dict(sig="F"))]
        if t1:
            G += [(s, "X15", "timeexit", dict(xt=1500)), (s, "X16", "timeexit", dict(xt=1400))]
        if s == COIL:
            G += [(s, "T01", "nco", dict(sig="T01")), (s, "T02", "nco", dict(sig="T02")),
                  (s, "T03", "tight", dict(sig="T03")), (s, "T04", "tight", dict(sig="T04")),
                  (s, "T05", "close", dict(sig="T05")), (s, "T06", "close", dict(sig="T06"))]
        G += [(s, "O1", "opposite_early", dict(kind="mirror")), (s, "O2", "rebound_nextday", dict(kind="rebound"))]
        if t1:
            G += [(s, "O3", "reverse_after_stop", dict(kind="sar"))]
    return G


GRID = grid()
COIL_SIG = {"P": COIL_P, "T01": {**COIL_P, "nco": 3}, "T02": {**COIL_P, "nco": 5}, "T03": {**COIL_P, "tight": 0.4},
            "T04": {**COIL_P, "tight": 0.6}, "T05": {**COIL_P, "close": 0.2}, "T06": {**COIL_P, "close": 0.3}}


# ------------------------------------------------------------------------------------------------ kernels
@numba.njit(cache=True)
def _b4a(new, c, h, l, hod, atr, nco, tight, close):
    """cwt_live_lib.b4a with the coil length, tightness and closeness as knobs."""
    n = len(c)
    flag = np.zeros(n, np.bool_)
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
            if not (h[k] - l[k] < tight * mr and c[k] <= hod[i] and hod[i] - c[k] <= close * atr[i]):
                ok = False
                break
            lo = min(lo, l[k])
        if ok and lo < c[i]:
            flag[i] = True
    return flag


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
def sim(h, l, c, tod, dend, ent, Rv, side, up, dn, em, ex, ek, tsb, tsr, be, so, sof, xt):
    """5-minute path simulation mirroring mcf/backtest/engine.simulate (stop first, then target; management from the
    next bar). Returns net R (production + tod costs), filled, mfe, mae, exit code (1 target, 2 stop, 3 breakeven/
    moved stop, 4 time stop, 5 time exit, 6 flatten), entry tod, exit row."""
    n = len(ent)
    r = np.full(n, np.nan)
    mfe_o = np.full(n, np.nan)
    mae_o = np.full(n, np.nan)
    code = np.zeros(n, np.int8)
    etod = np.zeros(n, np.int32)
    xrow = np.full(n, -1, np.int64)
    for q in range(n):
        i = ent[q]
        R = Rv[q]
        if i < 0 or not (R > 0):
            continue
        end = dend[i]
        j = -1
        e = 0.0
        pre_stop = False
        if em == 0:
            j, e = i, c[i]
        elif em == 2 or em == 3:
            if i + 1 <= end:
                if em == 2 or side * (c[i + 1] - c[i]) > 0:
                    j, e = i + 1, c[i + 1]
        else:
            L = c[i] - side * ex * R
            for k in range(i + 1, min(i + ek, end) + 1):
                if (side == 1 and l[k] < L) or (side == -1 and h[k] > L):
                    j, e = k, L
                    st = L - side * dn * R
                    if (side == 1 and l[k] <= st) or (side == -1 and h[k] >= st):
                        pre_stop = True
                    break
        if j < 0:
            continue
        ec = (0.01 + e * 1e-4) * _mult(tod[j])
        stop = e - side * dn * R
        tgt = e + side * up * R
        spx = e + side * so * R
        scaled = False
        mfe, mae = 0.0, 0.0
        x, cd, xr = 0.0, 0, -1
        if pre_stop:
            x, cd, xr = stop, 2, j
            mae = -dn
        else:
            for k in range(j + 1, end + 1):
                if tod[k] > xt:
                    x, cd, xr = c[k - 1], 5, k - 1
                    break
                adv = l[k] if side == 1 else h[k]
                fav = h[k] if side == 1 else l[k]
                mae = min(mae, side * (adv - e) / R)
                if side * (adv - stop) <= 0:
                    x, xr = stop, k
                    cd = 2 if side * (stop - e) < -0.999 * dn * R else 3
                    break
                mfe = max(mfe, side * (fav - e) / R)
                if side * (fav - tgt) >= 0:
                    x, cd, xr = tgt, 1, k
                    break
                if tsb > 0 and (k - j) >= tsb and mfe < tsr:
                    x, cd, xr = c[k], 4, k
                    break
                if be > 0 and mfe >= be:
                    stop = max(stop, e) if side == 1 else min(stop, e)
                if so > 0 and not scaled and side * (fav - spx) >= 0:
                    scaled = True
                    stop = max(stop, e) if side == 1 else min(stop, e)
            if cd == 0:
                x, cd, xr = c[end], 6, end
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if (cd == 2 or cd == 3) else 0.0))
        g = side * (x - e) / R
        if scaled:
            g = sof * so + (1 - sof) * g
            xc = (1 - sof) * xc
        r[q] = g - (ec + xc) / R
        mfe_o[q], mae_o[q], code[q], etod[q], xrow[q] = mfe, mae, cd, tod[j], xr
    return r, mfe_o, mae_o, code, etod, xrow


# ------------------------------------------------------------------------------------------------ month
def build_paths(month):
    f = lib.load_month(month)
    f["symbol"] = f["symbol"].astype(str)
    f["_fi"] = np.arange(len(f))
    hd = scan.head_rows(f, month, liq=False)
    hd["_fi"] = -1
    fh = pd.concat([f, hd], ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    tl = scan.tail_rows(month)
    fh["_fhi"] = np.arange(len(fh))
    tl["_fhi"] = -1
    P = pd.concat([fh[["symbol", "date", "tod", "high", "low", "close", "_fhi"]], tl], ignore_index=True)
    P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    day = f.groupby(["symbol", "date"], sort=False).agg(atr=("atr_d", "first"), adv=("adv20", "first")).reset_index()
    P = P.merge(day, on=["symbol", "date"], how="left")   # merge keeps P's order (left join)
    key = P["symbol"].to_numpy() + "|" + P["date"].astype(str).to_numpy()
    new = np.r_[True, key[1:] != key[:-1]]
    seg = np.cumsum(new) - 1
    last = np.r_[np.flatnonzero(new)[1:] - 1, len(P) - 1]
    dend = last[seg]
    fh2P = np.full(len(fh), -1, np.int64)
    m = P["_fhi"].to_numpy() >= 0
    fh2P[P["_fhi"].to_numpy()[m]] = np.flatnonzero(m)
    f2fh = np.full(len(f), -1, np.int64)
    fi = fh["_fi"].to_numpy()
    f2fh[fi[fi >= 0]] = np.flatnonzero(fi >= 0)
    return f, fh, P, dend, fh2P[f2fh], fh2P, key, seg


def first_idx(df, mask, s):
    b = BASE[s]
    tod = df["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        m = np.asarray(mask, bool) & (tod >= b["win"][0]) & (tod <= b["win"][1]) \
            & (df["adv20"].fillna(0).to_numpy() >= b["adv"]) & (df["atr_d"].to_numpy(float) > 0)
    return gates.first_per_symbol_day(df["symbol"].to_numpy(), df["date"].to_numpy(), m)


def signals(f, fh, f2P, fh2P):
    """{setup: {sig variant: P-row index of the entry signal bar}}"""
    out = {}
    x, lev = T4.cwt_levels(fh)
    vr = np.nan_to_num(x.vr, nan=np.inf)
    fl_fh = fh["flow3"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        for s, d in CWT14.items():
            L, ok = lev[d["level"]]
            m = T4._b3(x.new, ok, L, x.h, x.l, x.c, vr, x.atr, 0.05, 3, d["vr"])
            out[s] = {"P": fh2P[first_idx(fh, m, s)], "F": fh2P[first_idx(fh, m & (fl_fh > 0), s)]}
        out[COIL] = {}
        for k, p in COIL_SIG.items():
            m = _b4a(x.new, x.c, x.h, x.l, x.hod, x.atr, p["nco"], p["tight"], p["close"])
            out[COIL][k] = fh2P[first_idx(fh, m, COIL)]
            if k == "P":
                out[COIL]["F"] = fh2P[first_idx(fh, m & (fl_fh > 0), COIL)]
        sc = regime_score(f, "short", T4.W9, 950, 1500, gate="fo-", k_cost=8.0, use_heat=False)
        m = sc <= -11.3
        out[H] = {"P": f2P[first_idx(f, m, H)], "F": f2P[first_idx(f, m & (f["flow3"].to_numpy(float) < 0), H)]}
    return out


def ctrl_pool(P, adv):
    tod = P["tod"].to_numpy()
    ok = (P["adv"].fillna(0).to_numpy() >= adv) & (P["atr"].to_numpy(float) > 0) & (tod >= 950)
    d = pd.to_datetime(P["date"]).dt.strftime("%Y%m%d").astype(np.int64).to_numpy()
    gk = d * 10000 + tod
    idx = np.flatnonzero(ok)
    o = np.argsort(gk[idx], kind="mergesort")
    return idx[o], gk[idx][o], gk


def ctrl_rows(pool, ent, rng):
    idx, sk, gk = pool
    lo = np.searchsorted(sk, gk[ent], "left")
    hi = np.searchsorted(sk, gk[ent], "right")
    cnt = hi - lo
    pick = lo[:, None] + (rng.random((len(ent), K_CTRL)) * np.maximum(cnt, 1)[:, None]).astype(np.int64)
    rows = np.where(cnt[:, None] > 0, idx[np.minimum(pick, len(idx) - 1)], -1)
    return rows


def run(Pa, ent, side, prm):
    h, l, c, tod, dend, atr = Pa
    Rv = 0.25 * atr[np.maximum(ent, 0)]
    return sim(h, l, c, tod, dend, ent.astype(np.int64), Rv, side, prm["up"], prm["dn"], prm["em"], prm["ex"],
               prm["ek"], prm["tsb"], prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["xt"])


def month_job(month, parity=False):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, f2P, fh2P, key, seg = build_paths(month)
    S = signals(f, fh, f2P, fh2P)
    Pa = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32),
          dend, P["atr"].to_numpy(float))
    sym, dat = P["symbol"].to_numpy(), P["date"].to_numpy()
    tod = Pa[3]
    # next-session 09:50 row per P row (same symbol, next date in this month)
    sd = pd.DataFrame({"symbol": sym[tod == 950], "date": dat[tod == 950], "row": np.flatnonzero(tod == 950)})
    sd["nxt"] = sd.groupby("symbol")["row"].shift(-1).fillna(-1).astype(np.int64)
    nxt_by_key = pd.Series(sd["nxt"].to_numpy(), index=sd["symbol"] + "|" + sd["date"].astype(str))
    pools = {a: ctrl_pool(P, a) for a in (95e6, 125e6)}
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    rows = []
    parent_cache = {}
    for s, vid, knob, ov in GRID:
        b = BASE[s]
        prm = {**EX0, "up": b["up"], "dn": b["dn"], **ov}
        side = b["side"]
        ent = S[s][prm["sig"]]
        if prm["kind"] == "mirror":
            ent = ent[tod[ent] < 1030]
            side, prm = -side, {**prm, "up": b["dn"], "dn": b["up"]}
        elif prm["kind"] in ("rebound", "sar"):
            pr, pc, pxr = parent_cache[s]
            stopped = pc == 2
            if prm["kind"] == "rebound":
                ent = nxt_by_key.reindex(key[S[s]["P"][stopped]]).fillna(-1).astype(np.int64).to_numpy()
                ent = ent[ent >= 0]
                side = 1
                if s == H:
                    prm = {**prm, "up": 1.0, "dn": 1.0}
            else:
                ent = pxr[stopped]
                ent = ent[ent >= 0]
                side, prm = 1, {**prm, "up": 1.0, "dn": 1.0}
        r, mfe, mae, cd, et, xr = run(Pa, ent, side, prm)
        if vid == "P":
            parent_cache[s] = (r, cd, xr)
        cr = ctrl_rows(pools[b["adv"]], ent, rng)
        cr_r = np.full(cr.shape, np.nan)
        for k in range(K_CTRL):
            cr_r[:, k] = run(Pa, cr[:, k], side, prm)[0]
        cnt = np.isfinite(cr_r).sum(1)
        ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan)
        filled = np.isfinite(r)
        t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": tod[ent], "tod": et, "r": r, "mfe": mfe,
                          "mae": mae, "code": cd, "ctrl": ctrl, "filled": filled})
        t["setup"], t["var"], t["knob"] = s, vid, knob
        rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    if parity:
        return out, f, fh, S
    out = out.astype({"setup": "category", "var": "category", "knob": "category", "symbol": "category",
                      "r": "float32", "mfe": "float32", "mae": "float32", "ctrl": "float32"})
    print(month, len(out), round(time.time() - t0), flush=True)
    return out


def check_parity(month="2025-06"):
    out, f, fh, S = month_job(month, parity=True)
    # 1. coil kernel == cwt_live_lib.b4a (first 200k rows of fh)
    sub = fh.iloc[:200_000].reset_index(drop=True)
    a = CL.b4a(sub, nco=4)
    x = CL.arrays(sub)
    b = _b4a(x.new, x.c, x.h, x.l, x.hod, x.atr, 4, 0.5, 0.25)
    assert (a == b).all(), int((a != b).sum())
    print("coil parity ok", int(a.sum()))
    # 2. simulator parent == gates.lab_trades
    for s in (ORL, ORLV, PDL, H, COIL):
        p = out[(out.setup == s) & (out["var"] == "P")]
        geom = "t1s1" if s == H else "t05s1"
        side = "short" if s == H else "long"
        if s in CWT14:
            xx, lev = T4.cwt_levels(fh)
            L, ok = lev[CWT14[s]["level"]]
            m = T4._b3(xx.new, ok, L, xx.h, xx.l, xx.c, np.nan_to_num(xx.vr, nan=np.inf), xx.atr, 0.05, 3, CWT14[s]["vr"])
            df = fh
        elif s == COIL:
            df, m = fh, CL.b4a(fh, nco=4)
        else:
            df = f
            with np.errstate(invalid="ignore"):
                m = regime_score(f, "short", T4.W9, 950, 1500, gate="fo-", k_cost=8.0, use_heat=False) <= -11.3
        lt = T4.trades(df, m, {"win": BASE[s]["win"], "adv": BASE[s]["adv"], "side": side, "geom": geom})
        j = lt.merge(p[["date", "symbol", "tod", "r"]], on=["date", "symbol", "tod"], how="outer", suffixes=("_lab", "_sim"))
        d = (j.r_lab - j.r_sim).abs()
        print(s, "lab n", len(lt), "sim n", len(p), "matched", int(d.notna().sum()), "mean|d|", round(d.mean(), 5),
              "share<0.01", round((d < 0.01).mean(), 4), "exp lab", round(lt.r.mean(), 4), "sim", round(p.r.mean(), 4))


def main():
    SCR.mkdir(parents=True, exist_ok=True)
    months = lib.months()
    assert not set(months) & set(lib.LOCKED_MONTHS)
    with Pool(int(os.environ.get("T5_PROCS", 3))) as p:
        T = pd.concat(p.map(month_job, months), ignore_index=True)
    T.to_parquet(SCR / "trades.parquet", index=False)
    print(T.groupby(["setup", "var"], observed=True).agg(n=("r", "size"), filled=("filled", "mean"), exp=("r", "mean")).to_string())


if __name__ == "__main__":
    if sys.argv[1:] == ["parity"]:
        check_parity()
    else:
        main()
