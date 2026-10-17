"""Arena single-indicator screen (TRAIN only): every indicator x bin x window x side x geometry vs random entries.

Cell = (indicator, bin, window, side, geometry). Trades: the FIRST bar per symbol-day inside the window whose
indicator value falls in the bin (gates.first_per_symbol_day convention), production-cost R (arena.data.outcomes).
Random baseline: each trade's same-date, same-minute universe mean (c_*); excess = r - control.
Bins per (indicator, window): train deciles d1..d10 ([lo, hi)), tails le_q05, le_q20, ge_q80, ge_q95; indicators with
<= 12 distinct values get one bin per value (eq_<v>). Statistics are day-clustered (gates.summary convention).

    python -m mcf.research.arena.screen --cache <dir> --out research/swarm1017/arena [--sample 2] [--workers 2]
Writes <out>/single_screen.parquet (every cell) and <out>/top300.csv. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import data as D
from .indicators import INDICATORS

WINDOWS = {"0950-1100": (950, 1100), "1100-1400": (1100, 1400), "1400-1530": (1400, 1530)}
TAILS = (("le_q05", "<=", 0.05), ("le_q20", "<=", 0.20), ("ge_q80", ">=", 0.80), ("ge_q95", ">=", 0.95))
MIN_N_TOP = 200


def bins_for(v: np.ndarray, kind: str):
    """List of (label, op, lo, hi, mask) for finite values v (op: between [lo, hi) | <= | >= | ==)."""
    f = np.isfinite(v)
    vals = np.unique(v[f])
    out = []
    if kind != "cont" or len(vals) <= 12:
        for x in vals:
            out.append((f"eq_{x:g}", "==", float(x), float(x), f & (v == x)))
        return out
    q = np.quantile(v[f], np.arange(1, 10) / 10)
    edges = np.unique(q)
    b = np.searchsorted(edges, v, side="right")
    lo_e = np.r_[-np.inf, edges]
    hi_e = np.r_[edges, np.inf]
    for k in range(len(edges) + 1):
        out.append((f"d{k + 1:02d}", "between", float(lo_e[k]), float(hi_e[k]), f & (b == k)))
    for lab, op, p in TAILS:
        thr = float(np.quantile(v[f], p))
        out.append((lab, op, thr, thr, f & ((v <= thr) if op == "<=" else (v >= thr))))
    return out


def first_rows(sd: np.ndarray, m: np.ndarray) -> np.ndarray:
    """Index of the first True row per symbol-day (rows are ordered by sd, then tod)."""
    idx = np.flatnonzero(m)
    if not len(idx):
        return idx
    _, f = np.unique(sd[idx], return_index=True)
    return idx[f]


def cell_stats(cell: np.ndarray, day: np.ndarray, reg: np.ndarray, half: np.ndarray, R: np.ndarray, X: np.ndarray):
    """Per-cell stats for all outcome columns. cell/day/reg/half: (n,) ints; R, X: (n, k) production R and excess.
    Returns dict of (ncell, k) arrays: n, days, exp, se, t, exc, t_exc, win, exp_up, n_up, exp_dn, n_dn, h1, h2."""
    k = R.shape[1]
    ncell = int(cell.max()) + 1
    res = {}
    n = np.bincount(cell, minlength=ncell).astype(float)
    res["n"] = np.repeat(n[:, None], k, 1)
    cd = pd.MultiIndex.from_arrays([cell, day]).factorize()[0]
    cd_cell = np.zeros(cd.max() + 1, int)
    cd_cell[cd] = cell
    res["days"] = np.repeat(np.bincount(cd_cell, minlength=ncell)[:, None].astype(float), k, 1)
    for nm, Y in (("", R), ("x", X)):
        s = np.stack([np.bincount(cell, Y[:, j], ncell) for j in range(k)], 1)
        mu = s / np.where(n[:, None] > 0, n[:, None], np.nan)
        ds = np.stack([np.bincount(cd, Y[:, j]) for j in range(k)], 1)
        dn = np.bincount(cd).astype(float)
        resid = (ds - dn[:, None] * mu[cd_cell]) ** 2
        se = np.sqrt(np.stack([np.bincount(cd_cell, resid[:, j], ncell) for j in range(k)], 1)) / np.where(n[:, None] > 0, n[:, None], np.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            t = np.where(se > 0, mu / se, np.nan)
        if nm == "":
            res["exp"], res["se"], res["t"] = mu, se, t
        else:
            res["exc"], res["t_exc"] = mu, t
    res["win"] = np.stack([np.bincount(cell, (R[:, j] > 0).astype(float), ncell) for j in range(k)], 1) / np.where(n[:, None] > 0, n[:, None], np.nan)
    for lab, sel in (("up", reg == 2), ("dn", reg == 0), ("h1", half == 0), ("h2", half == 1)):
        nn = np.bincount(cell[sel], minlength=ncell).astype(float)
        ss = np.stack([np.bincount(cell[sel], R[sel, j], ncell) for j in range(k)], 1)
        with np.errstate(invalid="ignore", divide="ignore"):
            res[f"exp_{lab}"] = ss / np.where(nn[:, None] > 0, nn[:, None], np.nan)
        res[f"n_{lab}"] = np.repeat(nn[:, None], k, 1)
    return res


def run(cache_dir: Path, out_dir: Path, sample=(2, 0), workers: int = 2, names=None, log=print) -> pd.DataFrame:
    names = [n for n in (names or list(INDICATORS))]
    base = D.load(names=[], split="train", sample=sample, cache_dir=cache_dir, workers=workers, log=log)
    ms = D.months("train")
    log(f"screen: base {len(base)} rows, {base['date'].nunique()} sessions, months {ms}")
    sd = pd.MultiIndex.from_arrays([base["symbol"].to_numpy(), pd.Index(base["date"]).astype(str)]).factorize()[0]
    # rows are ordered by month, symbol, date, tod (lib.load_month), so each symbol-day is contiguous and in time order
    dates = pd.Index(base["date"])
    day = dates.factorize()[0]
    reg = pd.Series(base["regime"]).map({"down": 0, "flat": 1, "up": 2}).fillna(-1).to_numpy(int)
    ud = np.array(sorted(set(base["date"])))
    mid = ud[len(ud) // 2]
    half = (base["date"].to_numpy() >= mid).astype(int)
    R = base[[f"r_{o}" for o in D.OUTS]].to_numpy(np.float32)
    C = base[[f"c_{o}" for o in D.OUTS]].to_numpy(np.float32)
    okR = np.isfinite(R).all(1) & np.isfinite(C).all(1)
    tod = base["tod"].to_numpy()
    files = [Path(cache_dir) / f"month={m}.parquet" for m in ms]
    rows = []
    t0 = time.time()
    for ii, name in enumerate(names):
        v = np.concatenate([pd.read_parquet(f, columns=[name])[name].to_numpy(np.float32) for f in files]).astype(float)
        sd_o, day_o, reg_o, half_o, R_o, C_o, ok_o, tod_o = sd, day, reg, half, R, C, okR, tod
        meta = INDICATORS[name]
        for wn, (lo, hi) in WINDOWS.items():
            w = ok_o & (tod_o >= lo) & (tod_o < hi)
            vw = np.where(w, v, np.nan)
            cells, idxs, defs = [], [], []
            for ci, (lab, op, a, b, m) in enumerate(bins_for(vw, meta.kind)):
                idx = first_rows(sd_o, m)
                if not len(idx):
                    continue
                defs.append((lab, op, a, b))
                cells.append(np.full(len(idx), len(defs) - 1))
                idxs.append(idx)
            if not idxs:
                continue
            cell, idx = np.concatenate(cells), np.concatenate(idxs)
            Rr, Cc = R_o[idx].astype(float), C_o[idx].astype(float)
            st = cell_stats(cell, day_o[idx], reg_o[idx], half_o[idx], Rr, Rr - Cc)
            for c, (lab, op, a, b) in enumerate(defs):
                for j, o in enumerate(D.OUTS):
                    side, geom = o.split("_")
                    rows.append((name, meta.family, meta.live, wn, lab, op, a, b, side, geom,
                                 *(st[k][c, j] for k in ("n", "days", "exp", "se", "t", "exc", "t_exc", "win", "exp_up",
                                                         "n_up", "exp_dn", "n_dn", "exp_h1", "exp_h2"))))
        log(f"screen: {ii + 1}/{len(names)} {name} ({time.time() - t0:.0f}s, {len(rows)} cells)")
    cols = ["indicator", "family", "live", "window", "bin", "op", "lo", "hi", "side", "geom", "n", "days", "exp_r", "se",
            "t", "excess", "t_excess", "win_rate", "exp_up", "n_up", "exp_down", "n_down", "exp_h1", "exp_h2"]
    res = pd.DataFrame(rows, columns=cols)
    for c in ("n", "days", "n_up", "n_down"):
        res[c] = res[c].astype(int)
    out_dir.mkdir(parents=True, exist_ok=True)
    res.to_parquet(out_dir / "single_screen.parquet", index=False)
    top = top_cells(res, 300)
    top.to_csv(out_dir / "top300.csv", index=False, float_format="%.4f")
    return res


def add_direction(res: pd.DataFrame) -> pd.DataFrame:
    """Long and short cells of the same (indicator, window, bin, geom) take the SAME first rows, so their excesses
    split into a side-neutral part (composition: e.g. names whose costs are small in R) and a directional part:
    comp = (excess_long + excess_short) / 2, dir_excess = (excess_side - excess_other_side) / 2."""
    k = ["indicator", "window", "bin", "geom"]
    other = res[k + ["side", "excess"]].copy()
    other["side"] = other["side"].map({"long": "short", "short": "long"})
    m = res.merge(other.rename(columns={"excess": "excess_other"}), on=k + ["side"], how="left")
    m["comp"] = (m["excess"] + m["excess_other"]) / 2
    m["dir_excess"] = (m["excess"] - m["excess_other"]) / 2
    return m


def top_cells(res: pd.DataFrame, k: int = 300, min_n: int = MIN_N_TOP, min_days: int = 60) -> pd.DataFrame:
    """The k cells closest to tradable: n >= min_n, days >= min_days, ranked by the day-clustered t of the
    production-cost expectancy (NOT by excess over random, which is dominated by side-neutral composition)."""
    q = add_direction(res)
    q = q[(q["n"] >= min_n) & (q["days"] >= min_days)]
    return q.sort_values("t", ascending=False).head(k)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", default="research/swarm1017/arena")
    ap.add_argument("--sample", type=int, default=2, help="keep 1 of every N symbol-days (crc32 hash); 1 = all")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--names", default=None)
    a = ap.parse_args()
    res = run(Path(a.cache), Path(a.out), sample=None if a.sample <= 1 else (a.sample, 0), workers=a.workers,
              names=a.names.split(",") if a.names else None)
    print(f"cells: {len(res)}")
