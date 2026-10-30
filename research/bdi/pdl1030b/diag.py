"""pdl1030b diag (disclosed post-hoc sensitivity, counted as 1 extra row, not a candidate): decompose the SPY hedge leg of
A5 (p05 S3 + cost5 + SPY beta) into gross P/L at exit-bar closes, the conservative-fill adjustment and costs, per unit beta.
TRAIN+VALID only, same harness and asserts as build.py. Educational only - not financial advice."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd
import build as B
from build import SC, CL, S6, gates, lib, sim2, mult_v, INF

OUT = B.OUT.parent / "diag"


def job(month):
    assert month not in lib.LOCKED_MONTHS and month not in B.HOLD
    f, fh, P, dend, fh2P = SC.build_paths(month)
    ds = fh["date"].astype(str)
    assert (ds <= B.CUT).all() and not ((ds >= "2024-11-01") & (ds <= "2025-02-28")).any()
    Pds = P["date"].astype(str).to_numpy(); Psym = P["symbol"].astype(str).to_numpy(); Ptod = P["tod"].to_numpy(np.int32)
    Pkey = (pd.Series(Pds) + "|" + pd.Series(Ptod).astype(str)).to_numpy()
    m = Psym == "SPY"; ser = pd.Series(P["close"].to_numpy(float)[m], index=Pkey[m])
    with np.errstate(invalid="ignore"):
        tier_fh = np.where((np.abs(fh["gap"].to_numpy(float)) >= 20) | (fh["close"].to_numpy(float) < 5), 3.0, 1.0)
    tierP = np.ones(len(P)); tierP[fh2P[fh2P >= 0]] = tier_fh[fh2P >= 0]
    h, l, c = P["high"].to_numpy(float), P["low"].to_numpy(float), P["close"].to_numpy(float)
    x = CL.arrays(fh); lev = S6.levels(x)
    fsym, fdat, ftod = fh["symbol"].to_numpy(), ds.to_numpy(), fh["tod"].to_numpy()
    risk = 0.25 * fh["atr_d"].to_numpy(float)
    base = (fh["adv20"].fillna(0).to_numpy() >= 95e6) & (fh["atr_d"].to_numpy(float) > 0) & np.isfinite(risk) & (risk > 0)
    with np.errstate(invalid="ignore"):
        mm = np.asarray(S6.b3_any(x, lev[("PD", 1)], dict(side=1, vr=INF), 0.05), bool) & base & (ftod >= 950) & (ftod <= 1500)
    e1 = gates.first_per_symbol_day(fsym, fdat, mm)
    ent = fh2P[e1].astype(np.int64); R1 = risk[e1]; e = c[ent]
    r, cd, xr, sr = sim2(h, l, c, Ptod, dend, tierP, ent, R1, 1, 0.5, 3.0, 0.25, 0.5)
    expo = e / (3.0 * R1)
    S0 = ser.reindex(Pkey[ent]).to_numpy(float)
    def cl(rows):
        return ser.reindex(Pkey[rows]).to_numpy(float)
    xk = np.where(xr >= 0, xr, ent); scaled = sr >= 0; srk = np.where(scaled, sr, ent)
    wsc = np.where(scaled, 0.5, 0.0)
    SXc, SSc = cl(xk), cl(srk)
    SXw = np.where(np.isin(cd, (1, 2, 3)), np.maximum(SXc, cl(np.maximum(xk - 1, 0))), SXc)
    SSw = np.maximum(SSc, cl(np.maximum(srk - 1, 0)))
    SS_c = np.where(scaled, SSc, SXc); SS_w = np.where(scaled, SSw, SXw)
    gross_close = -(wsc * (SS_c / S0 - 1) + (1 - wsc) * (SXc / S0 - 1)) * expo
    gross_worse = -(wsc * (SS_w / S0 - 1) + (1 - wsc) * (SXw / S0 - 1)) * expo
    cost = ((0.01 / S0 + 1e-4) * mult_v(ftod[e1]) + wsc * (0.01 / SS_w + 1e-4) + (1 - wsc) * (0.01 / SXw + 1e-4)) * expo
    cst = (0.01 + e * 1e-4) * mult_v(ftod[e1]) + 0.01 + e * 1e-4
    return pd.DataFrame({"date": fdat[e1], "symbol": fsym[e1], "r_S3": r / 3.0, "c5": cst * tier_fh[e1] / R1 <= 0.05,
                         "gross_close": gross_close, "gross_worse": gross_worse, "cost": cost})


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for mo in sys.argv[1:] or B.MONTHS:
        o = OUT / f"d_{mo}.parquet"
        if not o.exists():
            job(mo).to_parquet(o, index=False); print(mo, flush=True)
