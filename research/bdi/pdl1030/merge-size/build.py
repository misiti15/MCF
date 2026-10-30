"""pdl1030/merge-size step 1: per month, build the four parent entries (parity) and the merged union entries, simulate
them with the unchanged top5_1028 `sim` (1R and 3R-at-same-$ risk units), and store per-trade r plus entry-time
features and the SPY move during each trade. TRAIN+VALID months only; HOLD months and the locked block are never loaded
(2026-09 rows after 09-15 are dropped at load; same loader patch as pdl1030/why/feat.py).
Educational only - not financial advice.
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
OUT = Path(__file__).resolve().parent / "cache"
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
    ds = fh["date"].astype(str)
    assert (ds <= CUT).all() and (P["date"].astype(str) <= CUT).all()
    assert not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    key = ds + "|" + fh["tod"].astype(str)
    sp = f[f["symbol"] == "SPY"]
    spk = sp["date"].astype(str) + "|" + sp["tod"].astype(str)
    spy_vd = pd.Series(sp["vwapDistPct"].to_numpy(float), index=spk).reindex(key).to_numpy(float)
    spy_s = pd.Series(sp["close"].to_numpy(float), index=spk)
    g = pd.DataFrame({"d": P["date"].astype(str).to_numpy(), "t": P["tod"].to_numpy(np.int32)}).drop_duplicates().sort_values(["d", "t"])
    g["k"] = g["d"] + "|" + g["t"].astype(str)
    g["v"] = spy_s.reindex(g["k"]).to_numpy(float)
    g["v"] = g.groupby("d")["v"].ffill()  # last SPY close at or before that bar (no look-ahead)
    spy_c = pd.Series(g["v"].to_numpy(float), index=g["k"].to_numpy())
    spy_gap = sp.groupby(sp["date"].astype(str))["gap"].first().reindex(ds).to_numpy(float)
    spy_day = sp.groupby(sp["date"].astype(str))["fromOpen"].last().reindex(ds).to_numpy(float)  # descriptive only (EOD)
    ctx = lib.load_context(month)
    br = pd.Series(ctx["breadth"].to_numpy(float), index=ctx["date"].astype(str) + "|" + ctx["tod"].astype(str)).reindex(key).to_numpy(float)
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c, tod = (P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float), P["tod"].to_numpy(np.int32))
    Pkey = P["date"].astype(str).to_numpy()
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    adv = fh["adv20"].fillna(0).to_numpy(); atr = x.atr
    atr_d = fh["atr_d"].to_numpy(float)
    risk = 0.25 * atr_d
    base = (adv >= 95e6) & (atr_d > 0) & np.isfinite(risk) & (risk > 0) & (ftod >= 950) & (ftod <= 1500)
    masks, par = {}, []
    with np.errstate(invalid="ignore"):
        for s, b in SPEC.items():
            m = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=b["vr"]), b["p"]), bool) & base
            masks[s] = m
            e1 = gates.first_per_symbol_day(fsym, fdat, m)
            ent = fh2P[e1]
            r = sim(h, l, c, tod, dend, tierP, ent.astype(np.int64), risk[e1], 1, 0.5, 1.0, 0, 0, 0.0, 0.0, b["so"], 0.5, 1555, 0.0)[0]
            par.append(pd.DataFrame({"setup": s, "date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], "r": r}))
    PAR = pd.concat(par, ignore_index=True)
    U = masks["p05"] | masks["p05lv"] | masks["p10"] | masks["p10lv"]
    e1 = gates.first_per_symbol_day(fsym, fdat, U)
    e1 = e1[fh2P[e1] >= 0]
    ent = fh2P[e1].astype(np.int64)
    nmem = sum(masks[s][e1].astype(int) for s in SPEC)
    cst = ((0.01 + c[ent] * 1e-4) * np.where(ftod[e1] < 1030, 1.4, 1.0) + 0.01 + c[ent] * 1e-4) * tier_fh[e1]
    R1 = risk[e1]
    T = pd.DataFrame({"date": fdat[e1], "symbol": fsym[e1], "tod": ftod[e1], "e": c[ent], "A": atr_d[e1], "tier": tier_fh[e1],
                      "nmem": nmem, "is_p05": masks["p05"][e1], "cost_R1": cst / R1, "cost_R3": cst / (3 * R1),
                      "depth": (x.pdl[e1] - x.lod[e1]) / atr[e1], "spy_vd": spy_vd[e1], "breadth": br[e1],
                      "spy_gap": spy_gap[e1], "spy_day": spy_day[e1]})
    for tag, Rv, up, so in (("1", R1, 0.5, 0.25), ("3", 3 * R1, 0.5 / 3, 0.25 / 3)):
        r, mfe, mae, cd, et, xr = sim(h, l, c, tod, dend, tierP, ent, Rv, 1, up, 1.0, 0, 0, 0.0, 0.0, so, 0.5, 1555, 0.0)
        xk = np.where(xr >= 0, xr, dend[ent])
        s0 = spy_c.reindex(pd.Series(Pkey[ent]) + "|" + pd.Series(tod[ent]).astype(str)).to_numpy(float)
        s1 = spy_c.reindex(pd.Series(Pkey[xk]) + "|" + pd.Series(tod[xk]).astype(str)).to_numpy(float)
        T["r" + tag], T["code" + tag] = r, cd
        T["spy_mv" + tag] = (s1 / s0 - 1) * 100  # SPY % move entry bar close -> exit bar close (hedge leg)
        T["spy_px"] = s0
    T.to_parquet(OUT / f"u_{month}.parquet", index=False)
    PAR.to_parquet(OUT / f"par_{month}.parquet", index=False)
    print(month, len(T), len(PAR), round(time.time() - t0), flush=True)


if __name__ == "__main__":
    for m in sys.argv[1:] or MONTHS:
        if not (OUT / f"u_{m}.parquet").exists():
            month_job(m)
