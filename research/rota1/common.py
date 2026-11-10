"""ROTA1 shared helpers. Educational only — not financial advice."""
import numpy as np
import pandas as pd


def split_of(date):
    if date <= "2025-12-31":
        return "TRAIN"
    if ("2026-01-01" <= date <= "2026-03-31") or ("2026-07-01" <= date <= "2026-09-15"):
        return "VALID"
    if "2026-10-06" <= date:
        return "FWD"
    return "GAP"   # never happens in the bt series (holdouts dropped)


def window_metrics(R, N, i, W):
    """Metrics per setup on sessions [i-W, i). R, N: numpy (days x setups). Returns dict of arrays."""
    r = R[max(0, i - W):i]
    n = N[max(0, i - W):i]
    tot_r = r.sum(0)
    tot_n = n.sum(0)
    active = n > 0
    best = np.where(active, r, -np.inf).argmax(0)
    cols = np.arange(r.shape[1])
    br = r[best, cols]
    bn = n[best, cols]
    den = tot_n - bn
    with np.errstate(invalid="ignore", divide="ignore"):
        wob = np.where(den > 0, (tot_r - br) / np.maximum(den, 1), np.nan)
        green = np.where(active.sum(0) > 0, ((r > 0) & active).sum(0) / np.maximum(active.sum(0), 1), np.nan)
        avg = np.where(tot_n > 0, tot_r / np.maximum(tot_n, 1), np.nan)
    worst = np.where(active.any(0), np.where(active, r, np.inf).min(0), np.nan)
    return {"wob": wob, "green": green, "worst": worst, "avg": avg, "n": tot_n}


def prank(x, mask):
    """Percentile rank (0..1) among mask; nan elsewhere."""
    out = np.full(len(x), np.nan)
    idx = np.where(mask & np.isfinite(x))[0]
    if len(idx) == 0:
        return out
    s = pd.Series(x[idx]).rank(pct=True, method="average").to_numpy()
    out[idx] = s
    return out


def s1(m, mask):
    return (prank(m["wob"], mask) + prank(m["green"], mask) + prank(m["worst"], mask)) / 3


def s2(m, mask):
    return 0.5 * prank(m["wob"], mask) + 0.25 * prank(m["green"], mask) + 0.25 * prank(m["worst"], mask)


def tstat(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3 or x.std(ddof=1) == 0:
        return np.nan
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
