"""pdl1030b build: p05/p10 CWT14 entries (09:50-15:00) and the early-window (09:35-09:45) reclaim / continuation entries,
simulated with the top5_1028 sim logic (copied to also return the scale-out row), plus the per-unit-beta SPY/QQQ hedge
leg P/L and costs in R of the stock's risk, and a daily close table for the prior-20-day beta.
TRAIN+VALID only; HOLD months and the locked block are never loaded (asserts). Educational only - not financial advice.

    python research/bdi/pdl1030b/build.py [months...]     # -> $SCR/cache/tr_<m>.parquet, dc_<m>.parquet
"""
import os, sys, time
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numba
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research/bdi/top5_1028"), str(ROOT / "research/bdi/top5_1019"), str(ROOT / "research/bdi/gates1021/scripts")]
import scan_1019 as SC  # noqa
from scan_1019 import lib, S6, CL, scan, _mult  # noqa
from mcf.research import gates  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030b/cache")
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
HOLD = ("2026-04", "2026-05", "2026-06", "2026-10")
INF = np.inf
_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df):
    return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))


@numba.njit(cache=True)
def sim2(h, l, c, tod, dend, tierP, ent, Rv, side, up, dn, so, sof):
    """top5_1028 sim with em=0, no time stop / be / clock / limit (the parent p05/p10 settings); also returns the
    scale-out row (-1 when not scaled)."""
    n = len(ent)
    r = np.full(n, np.nan)
    code = np.zeros(n, np.int8)
    xrow = np.full(n, -1, np.int64)
    srow = np.full(n, -1, np.int64)
    for q in range(n):
        i = ent[q]
        R = Rv[q]
        if i < 0 or not (R > 0):
            continue
        end = dend[i]
        j, e = i, c[i]
        ec = (0.01 + e * 1e-4) * _mult(tod[j])
        stop = e - side * dn * R
        tgt = e + side * up * R
        spx = e + side * so * R
        scaled = False
        x, cd, xr, sr = 0.0, 0, -1, -1
        for k in range(j + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                x, xr = stop, k
                cd = 2 if side * (stop - e) < -0.999 * dn * R else 3
                break
            if side * (fav - tgt) >= 0:
                x, cd, xr = tgt, 1, k
                break
            if so > 0 and not scaled and side * (fav - spx) >= 0:
                scaled = True
                sr = k
                stop = max(stop, e) if side == 1 else min(stop, e)
        if cd == 0:
            x, cd, xr = c[end], 6, end
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if (cd == 2 or cd == 3) else 0.0))
        g = side * (x - e) / R
        if scaled:
            g = sof * so + (1 - sof) * g
            xc = (1 - sof) * xc
        r[q] = g - tierP[i] * (ec + xc) / R
        code[q], xrow[q], srow[q] = cd, xr, sr
    return r, code, xrow, srow


def mult_v(t):
    t = np.asarray(t)
    return np.where(t < 935, 3.8, np.where(t < 950, 2.1, np.where(t < 1030, 1.4, 1.0)))


# entry sets: name -> (kind, p, window, extra); exits: name -> list of (exit id, side, up, dn, so)
SETS = {
    "p05": ("rec", 0.05, (950, 1500), None), "p10": ("rec", 0.10, (950, 1500), None),
    "e_rec05": ("rec", 0.05, (935, 945), None), "e_rec10": ("rec", 0.10, (935, 945), None),
    "e_con05": ("con", 0.05, (935, 945), "above"), "e_con10": ("con", 0.10, (935, 945), "above"),
    "e_con05any": ("con", 0.05, (935, 945), None),
}
EXITS = {
    "p05": [("P", 1, 0.5, 1.0, 0.25), ("S3", 1, 0.5, 3.0, 0.25)],
    "p10": [("S3", 1, 0.5, 3.0, 0.0)],
    "e_rec05": [("P", 1, 0.5, 1.0, 0.25), ("S3", 1, 0.5, 3.0, 0.25), ("T1", 1, 1.0, 1.0, 0.0)],
    "e_rec10": [("P10", 1, 0.5, 1.0, 0.0)],
    "e_con05": [("P", -1, 0.5, 1.0, 0.25), ("S3", -1, 0.5, 3.0, 0.25), ("T1", -1, 1.0, 1.0, 0.0)],
    "e_con10": [("P", -1, 0.5, 1.0, 0.25)],
    "e_con05any": [("P", -1, 0.5, 1.0, 0.25)],
}


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in HOLD
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    Pds = P["date"].astype(str).to_numpy()
    assert (ds <= CUT).all() and (Pds <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    assert not pd.Series(Pds).str[:7].isin(HOLD).any()
    key = ds + "|" + fh["tod"].astype(str)
    Psym = P["symbol"].astype(str).to_numpy()
    Ptod = P["tod"].to_numpy(np.int32)
    Pkey = pd.Series(Pds) + "|" + pd.Series(Ptod).astype(str)
    etf = {}
    for s in ("SPY", "QQQ"):
        m = Psym == s
        etf[s] = pd.Series(P["close"].to_numpy(float)[m], index=Pkey[m].to_numpy())
    fsp = fh[fh["symbol"].astype(str) == "SPY"]
    spy_vd = pd.Series(fsp["vwapDistPct"].to_numpy(float), index=(fsp["date"].astype(str) + "|" + fsp["tod"].astype(str)).to_numpy()).reindex(key).to_numpy(float)
    sp = f[f["symbol"] == "SPY"]
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last().reindex(ds).to_numpy(float)  # EOD: descriptive split only
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), Ptod)
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy()
    risk = 0.25 * fh["atr_d"].to_numpy(float)
    base = (adv >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0)
    rows = []
    with np.errstate(invalid="ignore"):
        for sname, (kind, p, (lo, hi), extra) in SETS.items():
            if kind == "rec":
                m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=INF), p), bool)
            else:
                m = x.c <= x.pdl - p * x.atr
                if extra == "above":
                    m &= x.open_d > x.pdl
            mm = m & base & (ftod >= lo) & (ftod <= hi)
            e1 = gates.first_per_symbol_day(fsym, fdat, mm)
            ent = fh2P[e1].astype(np.int64); R1 = risk[e1]
            assert (ent >= 0).all()
            e = c[ent]
            cst = (0.01 + e * 1e-4) * mult_v(ftod[e1]) + 0.01 + e * 1e-4
            cols = {"set": sname, "date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], "price": e, "R1": R1,
                    "cost_rt_R": cst * tier_fh[e1] / R1, "spy_vd": spy_vd[e1], "spy_day": spy_day[e1]}
            ekey = Pkey.to_numpy()[ent]
            for xid, side, up, dn, so in EXITS[sname]:
                r, cd, xr, sr = sim2(h, l, c, tod, dend, tierP, ent, R1, side, up, dn, so, 0.5)
                cols[f"r_{xid}"] = r / dn
                # hedge leg per unit beta, opposite side, in R of the stock's risk (dn * R1 per share)
                expo = e / (dn * R1)  # stock notional / $ risk
                hs = -side
                xk = np.where(xr >= 0, xr, ent)
                intra = np.isin(cd, (1, 2, 3))
                for en, ser in etf.items():
                    S0 = ser.reindex(ekey).to_numpy(float)
                    def px(rows_, intrabar):
                        a = ser.reindex(Pkey.to_numpy()[rows_]).to_numpy(float)
                        b = ser.reindex(Pkey.to_numpy()[np.maximum(rows_ - 1, 0)]).to_numpy(float)
                        worse = np.maximum(a, b) if hs == -1 else np.minimum(a, b)  # short hedge: higher is worse
                        return np.where(intrabar, worse, a)
                    SX = px(xk, intra)
                    scaled = sr >= 0
                    SS = np.where(scaled, px(np.where(scaled, sr, ent), np.ones(len(ent), bool)), SX)
                    wsc = np.where(scaled, 0.5, 0.0)
                    pnl = hs * (wsc * (SS / S0 - 1) + (1 - wsc) * (SX / S0 - 1)) * expo
                    hc = ((0.01 / S0 + 1e-4) * mult_v(ftod[e1]) + wsc * (0.01 / SS + 1e-4) + (1 - wsc) * (0.01 / SX + 1e-4)) * expo
                    cols[f"h{en}_{xid}"] = pnl - hc   # per unit beta, costs in
            rows.append(pd.DataFrame(cols))
    T = pd.concat(rows, ignore_index=True)
    # daily close table (15:55 close) for liquid names + ETFs
    last = np.r_[np.flatnonzero((Psym[1:] != Psym[:-1]) | (Pds[1:] != Pds[:-1])), len(P) - 1]
    liq = set(fsym[base]) | {"SPY", "QQQ"}
    dc = pd.DataFrame({"symbol": Psym[last], "date": Pds[last], "close": c[last], "tod": tod[last]})
    dc = dc[dc["symbol"].isin(liq)]
    print(month, len(T), T.groupby("set").size().to_dict(), round(time.time() - t0), flush=True)
    return T, dc


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for mo in sys.argv[1:] or MONTHS:
        o = OUT / f"tr_{mo}.parquet"
        if not o.exists():
            T, dc = month_job(mo)
            T.to_parquet(o, index=False); dc.to_parquet(OUT / f"dc_{mo}.parquet", index=False)
