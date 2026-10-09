"""Per-session betas, sector map and pair partners from PRIOR sessions only (NOTES 1.2): daily open-to-close returns,
window = previous 60 open sessions (min 30). Output (git-ignored): data/betas.npz, arrays [day, sym].
Educational only - not financial advice."""
import numpy as np
import pandas as pd

from common import DATA, ETFS, SECTOR, lib, open_dates, symbols

W, MINN = 60, 30
syms, dates = symbols(), open_dates()
si = {s: i for i, s in enumerate(syms)}
d = lib.daily()
d = d[d["symbol"].isin(si) & (d["open"] > 0)]
R = pd.DataFrame(np.nan, index=dates, columns=syms)
o2c = (d["close"] / d["open"] - 1) * 100
R = (pd.Series(o2c.to_numpy(), index=pd.MultiIndex.from_arrays([d["date"], d["symbol"]])).unstack()
     .reindex(index=dates, columns=syms)).to_numpy(np.float64)
ND, NS = R.shape
spy = si["SPY"]
sec_idx = np.array([si[e] for e in SECTOR])
etf_mask = np.array([s in ETFS for s in syms])
out = {k: np.full((ND, NS), np.nan, np.float32) for k in ("beta_spy", "beta_sec", "corr_sec", "beta_pair", "corr_pair")}
out["sec"] = np.full((ND, NS), -2, np.int16)        # index into SECTOR; -1 = SPY fallback; -2 undefined
out["partner"] = np.full((ND, NS), -1, np.int32)


def stats(Y, V, x):
    """Pairwise-complete beta and corr of each column of Y on vector x (NaN-masked)."""
    xv = np.isfinite(x)
    v = V & xv[:, None]
    n = v.sum(0)
    xx = np.where(v, x[:, None], 0.0)
    yy = np.where(v, Y, 0.0)
    sx, sy = xx.sum(0), yy.sum(0)
    cxy = (xx * yy).sum(0) - sx * sy / np.maximum(n, 1)
    cxx = (xx ** 2).sum(0) - sx ** 2 / np.maximum(n, 1)
    cyy = (yy ** 2).sum(0) - sy ** 2 / np.maximum(n, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        b = cxy / cxx
        c = cxy / np.sqrt(cxx * cyy)
    b[n < MINN] = np.nan
    c[n < MINN] = np.nan
    return b, c


for t in range(ND):
    if t < MINN:
        continue
    Y = R[max(0, t - W):t]
    V = np.isfinite(Y)
    b, _ = stats(Y, V, Y[:, spy])
    out["beta_spy"][t] = np.clip(b, 0, 3)
    C = np.full((len(SECTOR), NS), np.nan)
    B = np.full((len(SECTOR), NS), np.nan)
    for k, e in enumerate(sec_idx):
        B[k], C[k] = stats(Y, V, Y[:, e])
        C[k, e] = np.nan                                 # self excluded
    has = np.isfinite(C).any(0)
    best = np.where(has, np.nanargmax(np.where(np.isfinite(C), C, -9), 0), -1)
    bc = np.where(has, C[np.maximum(best, 0), np.arange(NS)], np.nan)
    fb = has & (bc < 0.30)
    sec = np.where(has, np.where(fb, -1, best), -2)
    out["sec"][t] = sec
    out["corr_sec"][t] = bc
    out["beta_sec"][t] = np.where(sec >= 0, np.clip(B[np.maximum(best, 0), np.arange(NS)], 0, 3),
                                  np.where(sec == -1, out["beta_spy"][t], np.nan))
    # pairs: correlation matrix over pairwise-complete rows
    Vf = V.astype(float)
    Y0 = np.where(V, Y, 0.0)
    n = Vf.T @ Vf
    sx = Y0.T @ Vf            # [i, j] = sum of y_i over rows where both valid
    sxx = (Y0 ** 2).T @ Vf
    sxy = Y0.T @ Y0
    with np.errstate(invalid="ignore", divide="ignore"):
        cov = sxy - sx * sx.T / n
        vi = sxx - sx ** 2 / n
        corr = cov / np.sqrt(vi * vi.T)
        beta = cov / vi.T     # slope of i on j
    corr[n < MINN] = np.nan
    np.fill_diagonal(corr, np.nan)
    corr[:, etf_mask] = np.nan
    same = (sec[:, None] == sec[None, :]) & (sec[:, None] >= 0)
    corr[~same] = np.nan
    corr[etf_mask, :] = np.nan
    okr = np.isfinite(corr).any(1)
    p = np.where(okr, np.nanargmax(np.where(np.isfinite(corr), corr, -9), 1), -1)
    pc = np.where(okr, corr[np.arange(NS), np.maximum(p, 0)], np.nan)
    good = okr & (pc >= 0.60)
    out["partner"][t] = np.where(good, p, -1)
    out["corr_pair"][t] = np.where(good, pc, np.nan)
    out["beta_pair"][t] = np.where(good, np.clip(beta[np.arange(NS), np.maximum(p, 0)], 0.2, 3), np.nan)
    if t % 50 == 0:
        print(t, dates[t], int(np.isfinite(out["beta_spy"][t]).sum()), int((sec >= 0).sum()), int(good.sum()), flush=True)
np.savez(DATA / "betas.npz", **out)
print("done")
