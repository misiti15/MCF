"""top5_1016 step 3-4: execution variants of the next 5 most-traded live setups on the open two-year history.
Pre-declaration: PLAN.md (written before this was run). Educational only - not financial advice.

    python research/bdi/top5_1016/scan_1016.py parity   # simulator == gates.lab_trades on 2025-06; short kernel == b3
    python research/bdi/top5_1016/scan_1016.py          # -> $SCR/trades.parquet (scratch, deleted after the report)

Reuses top5_1015/scan_1015.py (path builder, coil kernel, random-control pools) and top5_1014/scan_top5.py (CWT14
long kernel _b3, levels). The simulator here is scan_1015.sim plus: no target (up = inf), trailing stop
(engine order: time stop, breakeven, trail, scale-out), a clock exit, and re-entry after a stop.
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
sys.path[:0] = [str(ROOT / "research" / "bdi" / "top5_1015"), str(ROOT / "research" / "bdi" / "top5_1014"),
                str(ROOT / "research" / "bdi" / "refire1014"), str(ROOT / "research" / "history2y"),
                str(ROOT / "research" / "heat" / "candidates"), str(ROOT / "research" / "bdi" / "cwt" / "live"), str(ROOT)]
import lib  # noqa: E402
import cwt_live_lib as CL  # noqa: E402
import scan_top5 as T4  # noqa: E402
import scan_1015 as S5  # noqa: E402
from scan_1015 import _mult  # noqa: E402
from mcf.research import gates  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top5_1016")
SEED = 20261016
K_CTRL = 5
INF = np.inf

PDH, ORL10, ORL10V = "CWT14-failbrk-pdh-p05-lowvol-short", "CWT14-failbrk-orl-p10-long", "CWT14-failbrk-orl-p10-lowvol-long"
COIL, RW7 = "CWT12-coil-k4-long", "RW7-gapdn-bounce-early-short-FD"
CWT14 = {PDH: dict(level="PD", p=0.05, vr=1.0, side=-1), ORL10: dict(level="OR", p=0.10, vr=INF, side=1),
         ORL10V: dict(level="OR", p=0.10, vr=1.0, side=1)}
BASE = {PDH: dict(side=-1, up=0.5, dn=1.0, win=(950, 1500), adv=95e6),
        ORL10: dict(side=1, up=0.5, dn=1.0, win=(950, 1200), adv=95e6),
        ORL10V: dict(side=1, up=0.5, dn=1.0, win=(950, 1500), adv=95e6),
        COIL: dict(side=1, up=0.5, dn=1.0, win=(950, 1130), adv=95e6),
        RW7: dict(side=-1, up=1.0, dn=1.0, win=(950, 1500), adv=95e6)}
SETUPS = (PDH, ORL10, ORL10V, COIL, RW7)

# em entry mode (0 signal close, 2 next bar close), tsb/tsr time stop bars / min best R, be breakeven R, so/sof
# scale-out R / fraction, trr/tra trail distance / trail-after R (0 = off), xt clock exit HHMM, sig signal variant,
# kind std | reentry
EX0 = dict(em=0, tsb=0, tsr=0.0, be=0.0, so=0.0, sof=0.5, trr=0.0, tra=0.0, xt=1555, kind="std", sig="P")


def grid():
    G = []
    for s in SETUPS:
        t1 = BASE[s]["up"] == 1.0
        G += [(s, "P", "parent", {}),
              (s, "E01", "timestop30", dict(tsb=6, tsr=0.2)), (s, "E02", "timestop60", dict(tsb=12, tsr=0.25)),
              (s, "E03", "timestop90", dict(tsb=18, tsr=0.3)),
              (s, "E04", "breakeven", dict(be=0.5 if t1 else 0.35)),
              (s, "E05", "scaleout025", dict(so=0.25)), (s, "E06", "scaleout", dict(so=0.5 if t1 else 0.35)),
              (s, "E07", "stop085", dict(dn=0.85)), (s, "E08", "stop075", dict(dn=0.75)),
              (s, "E09", "wait1", dict(em=2)), (s, "E10", "flow3", dict(sig="F"))]
        if s != RW7:
            G += [(s, "E11", "from1030", dict(sig="W"))]
        if s in CWT14:
            G += [(s, "E12", "p-20", dict(sig="PL")), (s, "E13", "p+20", dict(sig="PH"))]
        if s in (PDH, RW7):
            u = BASE[s]["up"]
            G += [(s, "H01", "hold1555", dict(up=INF)),
                  (s, "H02", "trail05", dict(up=INF, trr=0.5, tra=0.5)),
                  (s, "H03", "trail10", dict(up=INF, trr=1.0, tra=1.0)),
                  (s, "H04", "trail075", dict(up=INF, trr=0.75, tra=0.5)),
                  (s, "H05", "target2x", dict(up=2 * u)),
                  (s, "H06", "half_runner_be", dict(up=INF, so=u)),
                  (s, "H07", "half_runner_trail05", dict(up=INF, so=u, trr=0.5, tra=u))]
            if s == RW7:
                G += [(s, "H08", "flat1430", dict(xt=1430))]
        G += [(s, "O1", "reentry_after_stop", dict(kind="reentry"))]
    return G


GRID = grid()


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, ent, Rv, side, up, dn, em, tsb, tsr, be, so, sof, trr, tra, xt):
    """scan_1015.sim (parity-checked against mcf/backtest/engine.simulate on 5-minute bars) plus no target (up inf),
    a trailing stop and a clock exit xt. Codes: 1 target, 2 stop, 3 moved stop (BE / trail), 4 time stop,
    5 clock exit, 6 flatten 15:55."""
    n = len(ent)
    r = np.full(n, np.nan)
    mfe_o = np.full(n, np.nan)
    mae_o = np.full(n, np.nan)
    code = np.zeros(n, np.int8)
    etod = np.zeros(n, np.int32)
    xrow = np.full(n, -1, np.int64)
    epx = np.full(n, np.nan)
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
            if trr > 0 and mfe >= tra:
                tr = e + side * (mfe - trr) * R
                stop = max(stop, tr) if side == 1 else min(stop, tr)
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
        mfe_o[q], mae_o[q], code[q], etod[q], xrow[q], epx[q] = mfe, mae, cd, tod[j], xr, e
    return r, mfe_o, mae_o, code, etod, xrow, epx


@numba.njit(cache=True)
def reentry_rows(c, tod, dend, xrow, epx, code, side, hi, kmax):
    """First bar within kmax bars after a parent stop bar whose close is back beyond the parent's entry price."""
    out = np.full(len(xrow), -1, np.int64)
    for q in range(len(xrow)):
        if code[q] != 2 or xrow[q] < 0:
            continue
        x = xrow[q]
        for k in range(x + 1, min(x + kmax, dend[x]) + 1):
            if tod[k] > hi:
                break
            if side * (c[k] - epx[q]) > 0:
                out[q] = k
                break
    return out


def b3_any(x, lev, d, p):
    L, ok = lev
    vr = np.nan_to_num(x.vr, nan=np.inf)
    if d["side"] == 1:
        return T4._b3(x.new, ok, L, x.h, x.l, x.c, vr, x.atr, p, 3, d["vr"])
    # short: negate prices into the long kernel (beyond: h >= L + p ATR; inside: c < L)
    return T4._b3(x.new, ok, -L, -x.l, -x.h, -x.c, vr, x.atr, p, 3, d["vr"])


def first_idx(df, mask, s, win=None):
    b = BASE[s]
    lo, hi = win or b["win"]
    tod = df["tod"].to_numpy()
    with np.errstate(invalid="ignore"):
        m = np.asarray(mask, bool) & (tod >= max(950, lo)) & (tod <= min(1500, hi)) \
            & (df["adv20"].fillna(0).to_numpy() >= b["adv"]) & (df["atr_d"].to_numpy(float) > 0)
    return gates.first_per_symbol_day(df["symbol"].to_numpy(), df["date"].to_numpy(), m)


def levels(x):
    at10 = np.where(x.tod == 1000, x.lod, np.nan)
    Lor = pd.Series(at10).groupby(x.seg).ffill().to_numpy(float)
    return {("OR", 1): (Lor, x.tod >= 1005), ("PD", 1): (x.pdl, np.ones(x.n, bool)), ("PD", -1): (x.pdh, np.ones(x.n, bool))}


def rw7_mask(f):
    g = lambda k: f[k].to_numpy(float)  # noqa: E731
    with np.errstate(invalid="ignore"):
        return (g("heat") <= -20) & (g("buyPressure") < -0.15) & (g("rsi") >= 55) & (g("rsi") <= 65) & (g("gap") < 0)


def signals(f, fh, f2P, fh2P):
    out = {}
    x = CL.arrays(fh)
    lev = levels(x)
    fl = fh["flow3"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        for s, d in CWT14.items():
            L = lev[(d["level"], d["side"])]
            m = b3_any(x, L, d, d["p"])
            agree = fl * d["side"] > 0
            out[s] = {"P": fh2P[first_idx(fh, m, s)], "F": fh2P[first_idx(fh, m & agree, s)],
                      "W": fh2P[first_idx(fh, m, s, (1030, BASE[s]["win"][1]))],
                      "PL": fh2P[first_idx(fh, b3_any(x, L, d, d["p"] * 0.8), s)],
                      "PH": fh2P[first_idx(fh, b3_any(x, L, d, d["p"] * 1.2), s)]}
        m = S5._b4a(x.new, x.c, x.h, x.l, x.hod, x.atr, 4, 0.5, 0.25)
        out[COIL] = {"P": fh2P[first_idx(fh, m, COIL)], "F": fh2P[first_idx(fh, m & (fl > 0), COIL)],
                     "W": fh2P[first_idx(fh, m, COIL, (1030, 1130))]}
        m = rw7_mask(f)
        out[RW7] = {"P": f2P[first_idx(f, m, RW7)], "F": f2P[first_idx(f, m & (f["flow3"].to_numpy(float) < 0), RW7)]}
    return out


def run(Pa, ent, side, prm):
    h, l, c, tod, dend, atr = Pa
    Rv = 0.25 * atr[np.maximum(ent, 0)]
    return sim(h, l, c, tod, dend, ent.astype(np.int64), Rv, side, prm["up"], prm["dn"], prm["em"], prm["tsb"],
               prm["tsr"], prm["be"], prm["so"], prm["sof"], prm["trr"], prm["tra"], prm["xt"])


def month_job(month, parity=False):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS
    f, fh, P, dend, f2P, fh2P, key, seg = S5.build_paths(month)
    S = signals(f, fh, f2P, fh2P)
    Pa = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32),
          dend, P["atr"].to_numpy(float))
    sym, dat, tod = P["symbol"].to_numpy(), P["date"].to_numpy(), Pa[3]
    pool = S5.ctrl_pool(P, 95e6)
    S5.K_CTRL = K_CTRL
    rng = np.random.default_rng([SEED, int(month.replace("-", ""))])
    rows, pc = [], {}
    for s, vid, knob, ov in GRID:
        b = BASE[s]
        prm = {**EX0, "up": b["up"], "dn": b["dn"], **ov}
        side = b["side"]
        ent = S[s][prm["sig"]]
        if prm["kind"] == "reentry":
            _, _, _, cd0, _, xr0, ep0 = pc[s]
            ent = reentry_rows(Pa[2], tod, dend, xr0, ep0, cd0, side, b["win"][1], 12)
            ent = ent[ent >= 0]
        res = run(Pa, ent, side, prm)
        r, mfe, mae, cd, et, xr, ep = res
        if vid == "P":
            pc[s] = res
        cr = S5.ctrl_rows(pool, ent, rng)
        cr_r = np.full(cr.shape, np.nan)
        for k in range(K_CTRL):
            cr_r[:, k] = run(Pa, cr[:, k], side, prm)[0]
        cnt = np.isfinite(cr_r).sum(1)
        ctrl = np.where(cnt > 0, np.nansum(cr_r, 1) / np.maximum(cnt, 1), np.nan)
        t = pd.DataFrame({"date": dat[ent], "symbol": sym[ent], "sig_tod": tod[ent], "tod": et, "r": r, "mfe": mfe,
                          "mae": mae, "code": cd, "ctrl": ctrl, "filled": np.isfinite(r)})
        t["setup"], t["var"], t["knob"] = s, vid, knob
        rows.append(t)
    out = pd.concat(rows, ignore_index=True)
    if parity:
        return out, f, fh
    out = out.astype({"setup": "category", "var": "category", "knob": "category", "symbol": "category",
                      "r": "float32", "mfe": "float32", "mae": "float32", "ctrl": "float32"})
    print(month, len(out), round(time.time() - t0), flush=True)
    return out


def check_parity(month="2025-06"):
    out, f, fh = month_job(month, parity=True)
    sub = fh.iloc[:300_000].reset_index(drop=True)
    xs = CL.arrays(sub)
    a = CL.b3(sub, level="PD", p=0.05, lowvol=True, side="short")
    b = b3_any(xs, levels(xs)[("PD", -1)], CWT14[PDH], 0.05)
    assert (a == b).all(), int((a != b).sum())
    a = CL.b3(sub, level="OR", p=0.10, lowvol=True, side="long")
    b = b3_any(xs, levels(xs)[("OR", 1)], CWT14[ORL10V], 0.10)
    assert (a == b).all(), int((a != b).sum())
    print("kernel parity ok (pdh short, orl p10 lowvol)")
    for s in SETUPS:
        p = out[(out.setup == s) & (out["var"] == "P")]
        geom = "t1s1" if s == RW7 else "t05s1"
        sd = "short" if BASE[s]["side"] == -1 else "long"
        if s in CWT14:
            d = CWT14[s]
            df, m = fh, CL.b3(fh, level=d["level"], p=d["p"], lowvol=d["vr"] == 1.0, side=sd)
        elif s == COIL:
            df, m = fh, CL.b4a(fh, nco=4)
        else:
            df, m = f, rw7_mask(f)
        lt = T4.trades(df, m, {"win": BASE[s]["win"], "adv": BASE[s]["adv"], "side": sd, "geom": geom})
        j = lt.merge(p[["date", "symbol", "tod", "r"]], on=["date", "symbol", "tod"], how="outer", suffixes=("_lab", "_sim"))
        dd = (j.r_lab - j.r_sim).abs()
        print(s, "lab n", len(lt), "sim n", len(p), "matched", int(dd.notna().sum()), "mean|d|", round(dd.mean(), 5),
              "share<0.01", round((dd < 0.01).mean(), 4), "exp lab", round(lt.r.mean(), 4), "sim", round(p.r.mean(), 4))


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
