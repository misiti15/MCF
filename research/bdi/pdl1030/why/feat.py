"""pdl1030/why: descriptive anatomy of the Failed Prior-Day-Low Break Longs on the open 2-yr frames, TRAIN+VALID only.
HOLD (2026-04..06, 2026-09-16..10-07) and the locked block are never loaded (months skipped; 2026-09 rows > 09-15 dropped
at load). Same kernel (S6.b3_any) and simulator (top5_1028 sim) as swarm15. Educational only - not financial advice.
"""
import os, sys, time
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research/bdi/top5_1028"), str(ROOT / "research/bdi/top5_1019"), str(ROOT / "research/bdi/gates1021/scripts")]
import scan_1019 as SC  # noqa
from scan_1019 import lib, S6, CL, scan  # noqa
from scan_1028 import sim  # noqa
from mcf.research import gates  # noqa
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
OUT = Path(__file__).resolve().parent
CUT = "2026-09-15"
MONTHS = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 13)] + ["2026-01", "2026-02", "2026-03", "2026-07", "2026-08", "2026-09"]
INF = np.inf
SPEC = {"p05": dict(p=0.05, vr=INF, so=0.25), "p05lv": dict(p=0.05, vr=1.0, so=0.0),
        "p10": dict(p=0.10, vr=INF, so=0.0), "p10lv": dict(p=0.10, vr=1.0, so=0.0)}

_lm, _tr, _lc = lib.load_month, scan.tail_rows, lib.load_context
def _cut(df):
    return df[df["date"].astype(str) <= CUT].reset_index(drop=True)
lib.load_month = lambda m, *a, **k: _cut(_lm(m, *a, **k))
scan.tail_rows = lambda m: _cut(_tr(m))
lib.load_context = lambda m: _cut(_lc(m))


def month_job(month):
    t0 = time.time()
    assert month not in lib.LOCKED_MONTHS and month not in ("2026-04", "2026-05", "2026-06", "2026-10")
    f, fh, P, dend, fh2P = SC.build_paths(month)
    assert (fh["date"].astype(str) <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    ds = fh["date"].astype(str)
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    key = ds + "|" + fh["tod"].astype(str)
    def ser(sym, col):
        g = f[f["symbol"] == sym]
        return pd.Series(g[col].to_numpy(float), index=g["date"].astype(str) + "|" + g["tod"].astype(str))
    spy_fo = ser("SPY", "fromOpen").reindex(key).to_numpy(float)
    spy_vd = ser("SPY", "vwapDistPct").reindex(key).to_numpy(float)
    qqq_vd = ser("QQQ", "vwapDistPct").reindex(key).to_numpy(float)
    qqq_fo = ser("QQQ", "fromOpen").reindex(key).to_numpy(float)
    ctx = lib.load_context(month)
    br = pd.Series(ctx["breadth"].to_numpy(float), index=ctx["date"].astype(str) + "|" + ctx["tod"].astype(str)).reindex(key).to_numpy(float)
    sp = f[f["symbol"] == "SPY"]
    spy_gap = sp.groupby(sp["date"].astype(str))["gap"].first().reindex(ds).to_numpy(float)
    spy_close_fo = sp.groupby(sp["date"].astype(str))["fromOpen"].last().reindex(ds).to_numpy(float)  # descriptive only (EOD)
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy(); atr = x.atr
    risk = 0.25 * fh["atr_d"].to_numpy(float)
    base = (adv >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0)
    pdl = x.pdl
    # first PDL break (0.05 / 0.10 ATR) tod per row's segment, from 09:35
    seg = x.seg
    def first_tod(mask):
        t = np.where(mask, x.tod, 9999)
        return pd.Series(t).groupby(seg).transform("min").to_numpy()
    with np.errstate(invalid="ignore"):
        fb05 = first_tod(x.l <= pdl - 0.05 * atr); fb10 = first_tod(x.l <= pdl - 0.10 * atr)
    # ---- symbol-day frequency table (liquid names)
    first = np.flatnonzero(x.new)
    dmask = base[first]
    sd = pd.DataFrame({"date": fdat[first], "symbol": fsym[first], "gap": x.gap[first], "open_pdl": (x.open_d[first] - pdl[first]) / atr[first],
                       "pc_pdl": (x.pc[first] - pdl[first]) / atr[first], "fb05": fb05[first], "fb10": fb10[first],
                       "spy_gap": spy_gap[first], "spy_day": spy_close_fo[first]})
    sigs = {}
    with np.errstate(invalid="ignore"):
        for s, b in SPEC.items():
            m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=b["vr"]), b["p"]), bool)
            mm = m & base & (ftod >= 950) & (ftod <= 1500)
            e1 = gates.first_per_symbol_day(fsym, fdat, mm)
            sigs[s] = e1
            # any-time reclaim signals (whole session 09:35-15:55) for frequency
            hasig = pd.Series(m).groupby(seg).transform("max").to_numpy()
            sd[f"sig_{s}"] = hasig[first]
            sd[f"sigwin_{s}"] = pd.Series(mm).groupby(seg).transform("max").to_numpy()[first]
            sd[f"nsig_{s}"] = pd.Series(m).groupby(seg).transform("sum").to_numpy()[first]
    sd = sd[dmask]
    rows = []
    for s, b in SPEC.items():
        e1 = sigs[s]; ent = fh2P[e1]; Rv = risk[e1]
        res = sim(h, l, c, tod, dend, tierP, ent.astype(np.int64), Rv, 1, 0.5, 1.0, 0, 0, 0.0, 0.0, b["so"], 0.5, 1555, 0.0)
        r, mfe, mae, cd, et, xr = res
        # later break of day's low (as of entry) after entry, and before exit
        lod_e = x.lod[e1]
        later = np.zeros(len(e1), bool); later_pre = np.zeros(len(e1), bool); minpost = np.full(len(e1), np.nan)
        for q in range(len(e1)):
            i = ent[q]; d = dend[i]
            if i < d:
                mn = l[i + 1:d + 1].min(); minpost[q] = mn
                later[q] = mn < lod_e[q]
                xq = xr[q] if xr[q] >= 0 else d
                if xq > i:
                    later_pre[q] = l[i + 1:xq + 1].min() < lod_e[q]
        # bars from first break to signal; spy fo at exit
        xk = np.where(xr >= 0, xr, ent)
        xkey = pd.Series(P["date"].astype(str).to_numpy()[xk]) + "|" + pd.Series(tod[xk]).astype(str)
        spy_x = ser("SPY", "fromOpen").reindex(xkey).to_numpy(float)
        cst = (0.01 + c[ent] * 1e-4) * np.where(ftod[e1] < 1030, 1.4, 1.0) + 0.01 + c[ent] * 1e-4
        t = pd.DataFrame({"setup": s, "date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], "r": r, "mfe": mfe, "mae": mae, "code": cd,
                          "xtod": et, "price": fh["close"].to_numpy(float)[e1], "atr": atr[e1], "R": Rv, "cost_rt_R": cst * tier_fh[e1] / Rv,
                          "gap": x.gap[e1], "open_pdl": (x.open_d[e1] - pdl[e1]) / atr[e1], "depth": (pdl[e1] - lod_e) / atr[e1],
                          "reclaim": (c[ent] - pdl[e1]) / atr[e1], "fo": fh["fromOpen"].to_numpy(float)[e1],
                          "vd": fh["vwapDistPct"].to_numpy(float)[e1], "chg": (c[ent] / x.pc[e1] - 1) * 100,
                          "fb": (fb05 if b["p"] == 0.05 else fb10)[e1], "spy_fo": spy_fo[e1], "spy_vd": spy_vd[e1], "qqq_vd": qqq_vd[e1],
                          "qqq_fo": qqq_fo[e1], "breadth": br[e1], "spy_gap": spy_gap[e1], "spy_day": spy_close_fo[e1], "spy_x": spy_x,
                          "later_low": later, "later_low_pre": later_pre, "post_low_atr": (minpost - lod_e) / atr[e1],
                          "vr": fh["volumeRatio"].to_numpy(float)[e1], "rsi5": fh["rsi5"].to_numpy(float)[e1],
                          "sma20": fh["sma20_dist_pct"].to_numpy(float)[e1], "atrpct": atr[e1] / c[ent] * 100})
        rows.append(t[np.isfinite(t["r"].to_numpy())])
    T = pd.concat(rows, ignore_index=True)
    print(month, len(T), len(sd), round(time.time() - t0), flush=True)
    return T, sd


if __name__ == "__main__":
    ms = sys.argv[1:] or MONTHS
    for m in ms:
        o = OUT / f"tr_{m}.parquet"
        if o.exists():
            continue
        T, sd = month_job(m)
        T.to_parquet(o, index=False); sd.to_parquet(OUT / f"sd_{m}.parquet", index=False)
