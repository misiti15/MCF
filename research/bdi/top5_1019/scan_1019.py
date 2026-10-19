"""top5_1019 step 3-4: execution variants of the 5 most-traded eligible live setups on the open two-year history.
Pre-declaration: PLAN.md (written before this was run). Educational only - not financial advice.

    python research/bdi/top5_1019/scan_1019.py parity   # parents == gates.lab_trades on 2025-06 (CWT14 x3, RW2)
    python research/bdi/top5_1019/scan_1019.py          # -> $SCR/trades.parquet (scratch, deleted after the report)

Reuses top5_1015/scan_1015.py (path builder pieces, random-control pools, tod cost multiplier), top5_1014/scan_top5.py
(CWT14 long kernel _b3), top5_1016/scan_1016.py (short-side b3, levels) and reddit1012liq/live/liq_live_lib.py (LIQ
sweep machine). The simulator is scan_1016.sim plus a per-trade risk unit and an optional fixed stop price (LIQ).
The rule-19 locked block 2024-11-01..2025-02-28 is never loaded (lib.months() lists open months only,
lib.load_month refuses locked months, MCF_HIST_ALLOW_LOCKED is never set).
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
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1016"), str(ROOT / "research" / "bdi" / "top5_1015"),
                str(ROOT / "research" / "bdi" / "top5_1014"), str(ROOT / "research" / "bdi" / "refire1014"),
                str(ROOT / "research" / "history2y"), str(ROOT / "research" / "heat" / "candidates"),
                str(ROOT / "research" / "bdi" / "cwt" / "live"), str(ROOT / "research" / "bdi" / "reddit1012liq" / "live"),
                str(ROOT)]
import lib  # noqa: E402
import cwt_live_lib as CL  # noqa: E402
import liq_live_lib as LQ  # noqa: E402
import scan  # noqa: E402  (refire1014: head/tail rows)
import scan_top5 as T4  # noqa: E402
import scan_1015 as S5  # noqa: E402
import scan_1016 as S6  # noqa: E402
from scan_1015 import _mult  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/t5tune1019_bdi")
SEED = 20261019
K_CTRL = 5
INF = np.inf

PDL10, PDL05V, PDH10 = "CWT14-failbrk-pdl-p10-long", "CWT14-failbrk-pdl-p05-lowvol-long", "CWT14-failbrk-pdh-p10-short"
LIQ, RW2 = "LIQ-orl-sweep-open15-s25-long", "RW2-exhaustion-noon-adv150-short-FD"
CWT14 = {PDL10: dict(level="PD", p=0.10, vr=INF, side=1), PDL05V: dict(level="PD", p=0.05, vr=1.0, side=1),
         PDH10: dict(level="PD", p=0.10, vr=INF, side=-1)}
BASE = {PDL10: dict(side=1, up=0.5, dn=1.0, win=(950, 1500), adv=95e6),
        PDL05V: dict(side=1, up=0.5, dn=1.0, win=(950, 1500), adv=95e6),
        PDH10: dict(side=-1, up=0.5, dn=1.0, win=(950, 1200), adv=95e6),
        LIQ: dict(side=1, up=2.5, dn=1.0, win=(950, 1500), adv=95e6),
        RW2: dict(side=-1, up=1.0, dn=1.0, win=(950, 1500), adv=150e6)}
SETUPS = (PDL10, PDL05V, PDH10, LIQ, RW2)
EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, xt=1555, kind="std", sig="P", win=None, filt=None)


def grid():
    G = []
    for s in SETUPS:
        b = BASE[s]
        t05, liq = b["up"] == 0.5, s == LIQ
        beR = 0.35 if t05 else (1.0 if liq else 0.5)
        soR = 0.25 if t05 else (1.0 if liq else 0.5)
        G += [(s, "P", "parent", {}),
              (s, "E01", "timestop30", dict(tsb=6, tsr=0.2)), (s, "E02", "timestop60", dict(tsb=12, tsr=0.25)),
              (s, "E03", "stop085", dict(dn=0.85)), (s, "E04", "stop075", dict(dn=0.75)),
              (s, "E05", "stop125_sametarget", dict(dn=1.25)),
              (s, "E06", "breakeven", dict(be=beR)), (s, "E07", "scaleout_ALPACA_CAVEAT", dict(so=soR)),
              (s, "E08", "wait1", dict(em=2))]
        if not liq:
            G += [(s, "E09", "from1000", dict(win=(1000, b["win"][1])))]
        G += [(s, "E10", "from1030", dict(win=(1030, b["win"][1]))),
              (s, "E11", "until1100", dict(win=(b["win"][0], min(1100, b["win"][1])))),
              (s, "E12", "spy_against_after1030", dict(filt="spy1030")),
              (s, "E13", "spy_against025_after1030", dict(filt="spy1030_25")),
              (s, "E14", "spy_against_allday", dict(filt="spyall")),
              (s, "E15", "flow3", dict(filt="flow3")),
              (s, "E16", "reentry_cd30", dict(kind="reentry"))]
        if s in CWT14:
            G += [(s, "T1", "p-20", dict(sig="PL")), (s, "T2", "p+20", dict(sig="PH"))]
        elif liq:
            G += [(s, "T1", "x0.12", dict(sig="XL")), (s, "T2", "x0.18", dict(sig="XH")),
                  (s, "T3", "target1.5R", dict(up=1.5)), (s, "T4", "target2.0R", dict(up=2.0))]
        else:
            G += [(s, "T1", "sma20_0.8", dict(sig="SL")), (s, "T2", "sma20_1.2", dict(sig="SH")),
                  (s, "T3", "rsi5_88", dict(sig="RL")), (s, "T4", "rsi5_92", dict(sig="RH"))]
    return G


GRID = grid()


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, ent, Rv, sabs, side, up, dn, em, tsb, tsr, be, so, sof, xt):
    """scan_1016.sim (parity-checked against mcf/backtest/engine.simulate on 5-minute bars) with a per-trade risk unit
    Rv and an optional fixed stop price sabs (LIQ: R is recomputed from the actual entry). Codes: 1 target, 2 stop,
    3 moved stop (BE), 4 time stop, 5 clock exit, 6 flatten 15:55. r is in units of the trade's risk unit R."""
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
        if em == 0:
            j, e = i, c[i]
        elif i + 1 <= end:
            j, e = i + 1, c[i + 1]
        if j < 0:
            continue
        if np.isfinite(sabs[q]):
            R = side * (e - sabs[q])
            if not (R > 0):
                continue
        ec = (0.01 + e * 1e-4) * _mult(tod[j])
        stop = e - side * dn * R
        tgt = e + side * up * R
        spx = e + side * so * R
        scaled = False
        mfe, mae = 0.0, 0.0
        x, cd, xr = 0.0, 0, -1
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


@numba.njit(cache=True)
def next_after(rows_sorted, xrow, dend, gap):
    """For each first trade: the first signal row >= exit row + gap on the same symbol-day (-1 if none)."""
    out = np.full(len(xrow), -1, np.int64)
    for q in range(len(xrow)):
        x = xrow[q]
        if x < 0:
            continue
        k = np.searchsorted(rows_sorted, x + gap)
        if k < len(rows_sorted) and rows_sorted[k] <= dend[x]:
            out[q] = rows_sorted[k]
    return out


def build_paths(month):
    """scan_1015.build_paths with the LIQ head-row columns (refire1014 scan.head_rows(liq=True))."""
    f = lib.load_month(month)
    f["symbol"] = f["symbol"].astype(str)
    f["_fi"] = np.arange(len(f))
    hd = scan.head_rows(f, month, liq=True)
    hd["_fi"] = -1
    fh = pd.concat([f, hd], ignore_index=True).sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    tl = scan.tail_rows(month)
    fh["_fhi"] = np.arange(len(fh))
    tl["_fhi"] = -1
    P = pd.concat([fh[["symbol", "date", "tod", "high", "low", "close", "_fhi"]], tl], ignore_index=True)
    P = P.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    day = f.groupby(["symbol", "date"], sort=False).agg(atr=("atr_d", "first"), adv=("adv20", "first")).reset_index()
    P = P.merge(day, on=["symbol", "date"], how="left")
    key = P["symbol"].to_numpy() + "|" + P["date"].astype(str).to_numpy()
    new = np.r_[True, key[1:] != key[:-1]]
    seg = np.cumsum(new) - 1
    last = np.r_[np.flatnonzero(new)[1:] - 1, len(P) - 1]
    dend = last[seg]
    fh2P = np.full(len(fh), -1, np.int64)
    m = P["_fhi"].to_numpy() >= 0
    fh2P[P["_fhi"].to_numpy()[m]] = np.flatnonzero(m)
    return f, fh, P, dend, fh2P


def spy_fo(f, fh):
    s = f[f["symbol"] == "SPY"][["date", "tod", "fromOpen"]].rename(columns={"fromOpen": "spy_fo"})
    return fh[["date", "tod"]].merge(s, on=["date", "tod"], how="left")["spy_fo"].to_numpy(float)


def base_ok(fh, s, win):
    b = BASE[s]
    lo, hi = win or b["win"]
    tod = fh["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        return (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (fh["adv20"].fillna(0).to_numpy() >= b["adv"]) \
            & (fh["atr_d"].to_numpy(float) > 0)


def liq_mask(fh, x):
    flag, E = LQ.sweep(fh, level="OR", side="long", x=x, trig="open", k=15)
    atr = LQ.atr_row(fh)
    stop = E - 0.05 * atr
    with np.errstate(invalid="ignore"):
        risk = fh["close"].to_numpy(float) - stop
        return flag & (risk > 0) & (risk <= 1.0 * atr), stop


def rw2_mask(fh, rsi5=90.0, sma=1.0):
    g = lambda k: fh[k].to_numpy(float)  # noqa: E731
    with np.errstate(invalid="ignore"):
        return (g("rsi5") > rsi5) & (g("sma20_dist_pct") > sma) & (g("bear_div") > 0)


def masks(fh):
    """{setup: {sig: (mask over fh, fixed stop price over fh or None)}}"""
    x = CL.arrays(fh)
    lev = S6.levels(x)
    out = {}
    with np.errstate(invalid="ignore"):
        for s, d in CWT14.items():
            L = lev[(d["level"], d["side"])]
            out[s] = {k: (S6.b3_any(x, L, d, d["p"] * m), None) for k, m in (("P", 1.0), ("PL", 0.8), ("PH", 1.2))}
        out[LIQ] = {k: liq_mask(fh, xx) for k, xx in (("P", 0.15), ("XL", 0.12), ("XH", 0.18))}
        out[RW2] = {"P": (rw2_mask(fh), None), "SL": (rw2_mask(fh, sma=0.8), None), "SH": (rw2_mask(fh, sma=1.2), None),
                    "RL": (rw2_mask(fh, rsi5=88.0), None), "RH": (rw2_mask(fh, rsi5=92.0), None)}
    return out


def filt_mask(fh, spy, s, filt):
    side = BASE[s]["side"]
    tod = fh["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        if filt is None:
            return np.ones(len(fh), bool)
        if filt == "flow3":
            return fh["flow3"].to_numpy(float) * side > 0
        ag = side * spy < 0                    # signal against SPY's move from the open (NaN -> not against)
        if filt == "spy1030":
            return ~((tod >= 1030) & ag)
        if filt == "spy1030_25":
            return ~((tod >= 1030) & (side * spy <= -0.25))
        if filt == "spyall":
            return ~ag
    raise ValueError(filt)


def month_job(month, parity=False):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, fh2P = build_paths(month)
    spy = spy_fo(f, fh)
    M = masks(fh)
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float),
                    P["tod"].to_numpy(np.int32))
    atrP = P["atr"].to_numpy(float)
    sym, dat = P["symbol"].to_numpy(), P["date"].to_numpy()
    pools = {a: S5.ctrl_pool(P, a) for a in {b["adv"] for b in BASE.values()}}
    S5.K_CTRL = K_CTRL
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    fhc = fh["close"].to_numpy(float)
    spyP = np.full(len(P), np.nan)
    spyP[fh2P] = spy
    rows, pc = [], {}

    def run(ent_fh, s, prm, sabs_fh, risk_fh):
        ent = fh2P[ent_fh]
        if risk_fh is not None:
            Rv = risk_fh[ent_fh]
        else:
            Rv = 0.25 * atrP[np.maximum(ent, 0)]
        sab = sabs_fh[ent_fh] if sabs_fh is not None else np.full(len(ent), np.nan)
        res = sim(h, l, c, tod, dend, ent.astype(np.int64), Rv, sab, BASE[s]["side"], prm["up"], prm["dn"], prm["em"],
                  prm["tsb"], prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["xt"])
        return ent, Rv, res

    for s, vid, knob, ov in GRID:
        b = BASE[s]
        prm = {**EX0, "up": b["up"], "dn": b["dn"], **ov}
        m, stp = M[s][prm["sig"]]
        sig = np.asarray(m, bool) & base_ok(fh, s, prm["win"]) & filt_mask(fh, spy, s, prm["filt"])
        risk = (fhc - stp) if stp is not None else None
        e1 = gates.first_per_symbol_day(fh["symbol"].to_numpy(), fh["date"].to_numpy(), sig)
        ent, Rv, res = run(e1, s, prm, stp, risk)
        if prm["kind"] == "reentry":
            xr = res[5]
            allrows = np.sort(fh2P[np.flatnonzero(sig)])
            nx = next_after(allrows, xr, dend, 6)
            P2fh = P["_fhi"].to_numpy()
            e2 = P2fh[nx[nx >= 0]]
            ent2, Rv2, res2 = run(e2, s, prm, stp, risk)
            ent = np.r_[ent, ent2]
            Rv = np.r_[Rv, Rv2]
            res = tuple(np.r_[a, b2] for a, b2 in zip(res, res2))
            second = np.r_[np.zeros(len(e1), bool), np.ones(len(e2), bool)]
        else:
            second = np.zeros(len(ent), bool)
        r, mfe, mae, cd, et, xr = res
        scale = prm["dn"] if vid in ("E03", "E04", "E05") else 1.0
        # random control: same date/bar, same risk in ATR units, same mechanics (relative stop)
        katr = Rv / np.where(atrP[np.maximum(ent, 0)] > 0, atrP[np.maximum(ent, 0)], np.nan)
        cr = S5.ctrl_rows(pools[b["adv"]], ent, rng)
        cr_r = np.full(cr.shape, np.nan)
        for k in range(K_CTRL):
            rk = cr[:, k]
            Rc = katr * atrP[np.maximum(rk, 0)]
            Rc = np.where(rk >= 0, Rc, np.nan)
            cr_r[:, k] = sim(h, l, c, tod, dend, rk.astype(np.int64), Rc, np.full(len(rk), np.nan), b["side"],
                             prm["up"], prm["dn"], prm["em"], prm["tsb"], prm["tsr"], prm["be"], prm["so"], prm["sof"],
                             prm["xt"])[0]
        cnt = np.isfinite(cr_r).sum(1)
        ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan)
        t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": tod[ent], "tod": et, "r": r / scale,
                          "r_unscaled": r, "mfe": mfe, "mae": mae, "code": cd, "ctrl": ctrl / scale,
                          "filled": np.isfinite(r), "second": second, "spy_fo": spyP[ent]})
        t["setup"], t["var"], t["knob"] = s, vid, knob
        rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    if parity:
        return out, fh
    out = out.astype({"setup": "category", "var": "category", "knob": "category", "symbol": "category",
                      "r": "float32", "r_unscaled": "float32", "spy_fo": "float32", "mfe": "float32", "mae": "float32", "ctrl": "float32"})
    print(month, len(out), round(time.time() - t0), flush=True)
    return out


def check_parity(month="2025-06"):
    out, fh = month_job(month, parity=True)
    sub = fh.iloc[:300_000].reset_index(drop=True)
    xs = CL.arrays(sub)
    for s, d in CWT14.items():
        sd = "short" if d["side"] == -1 else "long"
        a = CL.b3(sub, level="PD", p=d["p"], lowvol=d["vr"] == 1.0, side=sd)
        b = S6.b3_any(xs, S6.levels(xs)[("PD", d["side"])], d, d["p"])
        assert (a == b).all(), (s, int((a != b).sum()))
    print("kernel parity ok (3 CWT14)")
    import importlib.util
    spec = importlib.util.spec_from_file_location("liqmod", ROOT / "research/bdi/reddit1012liq/live/LIQ-orl-sweep-open15-s25-long.py")
    lm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lm)
    a = lm.mask(fh)
    b = liq_mask(fh, 0.15)[0]
    assert (np.asarray(a, bool) == b).all(), int((np.asarray(a, bool) != b).sum())
    print("LIQ mask == live module mask on", month)
    for s in (PDL10, PDL05V, PDH10, RW2):
        p = out[(out.setup == s) & (out["var"] == "P")]
        sd = "short" if BASE[s]["side"] == -1 else "long"
        if s in CWT14:
            d = CWT14[s]
            m, geom = CL.b3(fh, level=d["level"], p=d["p"], lowvol=d["vr"] == 1.0, side=sd), "t05s1"
        else:
            m, geom = rw2_mask(fh), "t1s1"
        lt = T4.trades(fh, m, {"win": BASE[s]["win"], "adv": BASE[s]["adv"], "side": sd, "geom": geom})
        j = lt.merge(p[["date", "symbol", "tod", "r"]], on=["date", "symbol", "tod"], how="outer", suffixes=("_lab", "_sim"))
        dd = (j.r_lab - j.r_sim).abs()
        print(s, "lab n", len(lt), "sim n", len(p), "matched", int(dd.notna().sum()), "mean|d|", round(dd.mean(), 5),
              "share<0.01", round((dd < 0.01).mean(), 4), "exp lab", round(lt.r.mean(), 4), "sim", round(p.r.mean(), 4))
    p = out[(out.setup == LIQ) & (out["var"] == "P")]
    print(LIQ, "sim n", len(p), "filled", int(p.filled.sum()), "exp", round(p.r.mean(), 4))


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
