"""Scoring helpers for the BD innovation scans. Educational only - not financial advice.

score(df, mask, side, geom, window) -> dict with, for the FIRST qualifying bar per symbol-day (the
production entry rule of LabStrategy):
  n, days, exp_r (lab cost: flat 1c/side), exp_r_prod (adds 1 bps/side and +2c on stop-outs, as in the
  metric map), win, t_day (day-clustered t of exp_r_prod: mean of daily mean R / its SE over days),
  ex_best (exp_r_prod without the best day), base_win (mean R of EVERY bar in the same side+window,
  lab cost), edge_win = exp_r - base_win, edge_st (same-time control: trade R minus the mean R of all
  symbols' bars at the same date+bar time and side), t_st (day-clustered t of edge_st).
"""
import numpy as np
import pandas as pd

GEOMS = {"t1s1": (1.0, 1.0), "t05s1": (0.5, 1.0), "t1s05": (1.0, 0.5)}
_CACHE = {}


def load(split):
    if split not in _CACHE:
        df = pd.read_parquet(f"research/oct7/innovation/data/{split}.parquet")
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df.attrs["split"] = split
        _CACHE[split] = df
    return _CACHE[split]


_ST = {}
_BW = {}


def _same_time(df, side, geom):
    k = (df.attrs.get("split"), side, geom)
    if k not in _ST:
        col = f"r_{side}_{geom}"
        g = df.groupby([df["date"], df["tod"]], observed=True)[col].transform("mean")
        _ST[k] = g.to_numpy(dtype=float)
    return _ST[k]


def _first_idx(df, m):
    idx = np.flatnonzero(m)
    if not len(idx):
        return idx
    sym = df["symbol"].cat.codes.to_numpy()[idx].astype(np.int64)
    d = pd.to_datetime(df["date"].to_numpy()[idx]).values.astype("datetime64[D]").astype(np.int64)
    key = sym * 100000 + d
    _, first = np.unique(key, return_index=True)
    return idx[np.sort(first)]


def _tday(r, dates):
    s = pd.Series(r).groupby(dates).mean()
    if len(s) < 3 or s.std(ddof=1) == 0:
        return float("nan"), s
    return float(s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))), s


def score(df, mask, side, geom="t1s1", window=(950, 1500)):
    col = f"r_{side}_{geom}"
    r_all = df[col].to_numpy(dtype=float)
    tod = df["tod"].to_numpy()
    inwin = (tod >= window[0]) & (tod <= window[1]) & np.isfinite(r_all)
    m = np.asarray(mask, bool) & inwin
    idx = _first_idx(df, m)
    bk = (df.attrs.get("split"), side, geom, tuple(window))
    if bk not in _BW:
        _BW[bk] = float(np.nanmean(r_all[inwin]))
    base = _BW[bk]
    if len(idx) == 0:
        return {"n": 0, "base_win": round(base, 4)}
    up, dn = GEOMS[geom]
    r = r_all[idx]
    R = 0.25 * df["atr_d"].to_numpy(dtype=float)[idx]
    px = df["close"].to_numpy(dtype=float)[idx]
    lost = r < -dn + 1e-9
    rp = r - 2 * 1e-4 * px / R - 0.02 / R * lost
    w = df[f"win_{side}_{geom}"].to_numpy(dtype=float)[idx]
    dates = df["date"].to_numpy()[idx]
    t, daily = _tday(rp, dates)
    st = _same_time(df, side, geom)[idx]
    tst, _ = _tday(r - st, dates)
    tot = pd.Series(rp).groupby(dates).sum()
    best = tot.idxmax()
    ex = rp[dates != best]
    return {"n": int(len(r)), "days": int(len(daily)), "exp_r": round(float(r.mean()), 4),
            "exp_r_prod": round(float(rp.mean()), 4), "se": round(float(rp.std(ddof=1) / np.sqrt(len(rp))) if len(rp) > 1 else np.nan, 4),
            "win": round(float(np.nanmean(w)), 3), "t_day": round(t, 2),
            "ex_best": round(float(ex.mean()), 4) if len(ex) else np.nan,
            "best_share": round(float(tot.max() / tot.sum()), 2) if tot.sum() > 0 else np.nan,
            "green_days": round(float((daily > 0).mean()), 2),
            "base_win": round(base, 4), "edge_win": round(float(r.mean() - base), 4),
            "edge_st": round(float((r - st).mean()), 4), "t_st": round(tst, 2)}


def gate(tr, va, min_n_tr=40, min_n_va=30):
    """Pre-declared finalist gate (written before any scan ran)."""
    if tr.get("n", 0) < min_n_tr or va.get("n", 0) < min_n_va:
        return False
    return (tr["exp_r_prod"] > 0 and tr["edge_win"] > 0 and tr["edge_st"] > 0 and tr["t_day"] >= 1.0
            and va["exp_r_prod"] > 0 and va["edge_win"] > 0 and va["edge_st"] > 0 and va["t_day"] >= 1.0
            and va["ex_best"] > 0)


def flat(prefix, d):
    return {f"{prefix}_{k}": v for k, v in d.items()}
