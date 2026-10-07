"""Layer-1 primitive scan: one glance-readable metric at a time, threshold bands at train quantiles,
long and short, every exit geometry, five time windows, scored against the same-side same-window
random baseline. Writes metric_map.json, results.csv and METRIC_MAP.md next to this file.

Run from the repo root:  python research/primitives/primitives/scan.py
Reads ONLY research/setups2/data/{train,valid}.parquet (never the locked test split).
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
DATA = Path("research/setups2/data")
SIDES = ("long", "short")
GEOMS = {"t1s1": 1.0, "t05s1": 1.0, "t1s05": 0.5}          # geom -> stop size in R (for stop detection)
WINDOWS = {"W1": (950, 1030), "W2": (1030, 1130), "W3": (1130, 1300), "W4": (1300, 1430), "W5": (1430, 1501)}
WLABEL = {"W1": "09:50-10:30", "W2": "10:30-11:30", "W3": "11:30-13:00", "W4": "13:00-14:30", "W5": "14:30-15:00"}

# glance-readable metrics (continuous) and categorical flags. vol_climax is an exact duplicate of
# volumeRatio in the frame (checked), so it is not scanned twice.
CONT = ["fromOpen", "vwapDistPct", "gap", "volumeRatio", "volumeSurge", "rsi", "rsi5", "rsiSlope", "momentum",
        "sma20_dist_pct", "sma50_dist_pct", "sma20_slope_pct", "macdPct", "emaDiff", "buyPressure", "flow3",
        "flow9prev", "flowFlip", "dist_pdh_atr", "dist_pdl_atr", "dist_hod_atr", "dist_lod_atr", "dayRangePos",
        "dist_round_atr", "upper_wick", "lower_wick", "pricePosition", "atrPct", "heat"]
CAT = {"vwapReclaim": [-1.0, 0.0, 1.0], "bear_div": [1.0], "bull_div": [1.0]}
DERIVED = {  # deployable: computed from lab-frame columns inside mask(df)
    "flowFlip": "flow3 - flow9prev (recent signed volume vs the prior 9 bars)",
    "dayRangePos": "dist_lod_atr / (dist_hod_atr + dist_lod_atr) (0 = at low of day, 1 = at high of day)",
}
BASE_COLS = ["close", "atr_d", "tod", "symbol", "date"]
RCOLS = [f"r_{s}_{g}" for s in SIDES for g in GEOMS]


def derive(df: pd.DataFrame) -> pd.DataFrame:
    df["flowFlip"] = (df["flow3"] - df["flow9prev"]).astype("float32")
    rng = (df["dist_hod_atr"] + df["dist_lod_atr"]).replace(0, np.nan)
    df["dayRangePos"] = (df["dist_lod_atr"] / rng).astype("float32")
    return df


def load(split: str) -> pd.DataFrame:
    raw = [c for c in CONT if c not in DERIVED] + list(CAT) + ["flow3", "flow9prev", "dist_hod_atr", "dist_lod_atr"]
    cols = list(dict.fromkeys(raw + BASE_COLS + RCOLS))
    df = pd.read_parquet(DATA / f"{split}.parquet", columns=cols)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = derive(df)
    ok = np.ones(len(df), bool)
    for c in RCOLS:
        ok &= np.isfinite(df[c].to_numpy())
    df = df[ok]
    df["symbol"] = df["symbol"].astype("category")
    df = df.sort_values(["symbol", "date", "tod"], kind="stable").reset_index(drop=True)
    return df


def bands_for(train: pd.DataFrame) -> dict:
    """Threshold bands at train quantiles (all windows pooled, so thresholds are fixed and deployable)."""
    out = {}
    for m in CONT:
        x = train[m].to_numpy(dtype=float)
        x = x[np.isfinite(x)]
        q = np.quantile(x, [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95])
        q = {k: float(v) for k, v in zip(["q05", "q10", "q20", "q30", "q40", "q50", "q60", "q70", "q80", "q90", "q95"], q)}
        dec = [-np.inf, q["q10"], q["q20"], q["q30"], q["q40"], q["q50"], q["q60"], q["q70"], q["q80"], q["q90"], np.inf]
        b = []
        seen = set()
        for i in range(10):
            lo, hi = dec[i], dec[i + 1]
            if hi <= lo or (lo, hi) in seen:
                continue
            seen.add((lo, hi))
            b.append({"band": f"D{i + 1}", "lo": lo, "hi": hi})
        for nm, lo, hi in (("V1", -np.inf, q["q05"]), ("V2", q["q05"], q["q10"]),
                           ("V19", q["q90"], q["q95"]), ("V20", q["q95"], np.inf)):
            if hi > lo and (lo, hi) not in seen:
                seen.add((lo, hi))
                b.append({"band": nm, "lo": lo, "hi": hi})
        out[m] = {"quantiles": q, "bands": b}
    return out


def neighbours(metric_bands: list[str], band: str) -> list[str]:
    dec = [x for x in metric_bands if x.startswith("D")]
    if band.startswith("D"):
        i = dec.index(band)
        return [dec[j] for j in (i - 1, i + 1) if 0 <= j < len(dec)]
    nb = {"V1": ["V2", "D2"], "V2": ["V1", "D2"], "V19": ["V20", "D9"], "V20": ["V19", "D9"]}[band]
    return [x for x in nb if x in metric_bands]


class Split:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        tod = df["tod"].to_numpy()
        sym = df["symbol"].cat.codes.to_numpy()
        dcode, self.days = pd.factorize(df["date"], sort=True)
        self.dcode = dcode
        self.ndays = len(self.days)
        self.close = df["close"].to_numpy(dtype=float)
        self.R = 0.25 * df["atr_d"].to_numpy(dtype=float)
        self.r = {c: df[c].to_numpy(dtype=float) for c in RCOLS}
        self.win = {}
        for w, (a, b) in WINDOWS.items():
            sel = np.flatnonzero((tod >= a) & (tod < b))
            g = np.r_[True, (sym[sel][1:] != sym[sel][:-1]) | (dcode[sel][1:] != dcode[sel][:-1])]
            self.win[w] = (sel, g)
        # random baselines: mean r of every bar in the window (a random entry) and first-bar (lab baseline())
        self.base = {}
        for w, (sel, g) in self.win.items():
            for c in RCOLS:
                rr = self.r[c][sel]
                first = sel[g]
                self.base[(w, c)] = {"random": float(rr.mean()), "first_bar": float(self.r[c][first].mean()),
                                     "random_daily": np.bincount(dcode[sel], rr, self.ndays) /
                                     np.maximum(1, np.bincount(dcode[sel], minlength=self.ndays))}
        # tod-matched random baseline: mean r by bar time
        self.tod = tod
        self.todmean = {}
        for c in RCOLS:
            s = pd.Series(self.r[c]).groupby(tod).mean()
            self.todmean[c] = s

    def first_idx(self, w: str, m: np.ndarray) -> np.ndarray:
        sel, g = self.win[w]
        mm = m[sel]
        idx = np.flatnonzero(mm)
        if len(idx) == 0:
            return idx
        gid = np.cumsum(g) - 1
        gi = gid[idx]
        keep = np.r_[True, gi[1:] != gi[:-1]]
        return sel[idx[keep]]


def stats(sp: Split, idx: np.ndarray, side: str, geom: str, w: str) -> dict:
    c = f"r_{side}_{geom}"
    r = sp.r[c][idx]
    n = len(r)
    if n < 2:
        return {"n": int(n)}
    d = sp.dcode[idx]
    S = np.bincount(d, r, sp.ndays)
    N = np.bincount(d, minlength=sp.ndays).astype(float)
    on = N > 0
    D = int(on.sum())
    mean = float(r.mean())
    base = sp.base[(w, c)]["random"]

    def ct(rv, Sv):
        mu = rv.mean()
        resid = (Sv - mu * N)[on]
        var = D / max(1, D - 1) * float((resid ** 2).sum()) / (N.sum() ** 2)
        return float(mu / np.sqrt(var)) if var > 0 else 0.0

    t = ct(r, S)
    re = r - base
    t_edge = ct(re, np.bincount(d, re, sp.ndays))
    best = int(np.argmax(np.where(on, S, -np.inf)))
    exbest = float((S.sum() - S[best]) / (N.sum() - N[best])) if N.sum() - N[best] > 0 else None
    # production costs: + 1 bps per side and +2c on stops (extended-tier 3c not identifiable in the frame)
    R = sp.R[idx]
    stop = GEOMS[geom]
    stopped = np.abs(r - (-stop - 0.02 / R)) < 1e-4
    rp = r - 2e-4 * sp.close[idx] / R - 0.02 / R * stopped
    tm = float(sp.todmean[c].reindex(sp.tod[idx]).to_numpy().mean())
    return {"n": n, "days": D, "per_day": round(n / max(1, D), 2), "exp_r": round(mean, 4),
            "exp_r_prod": round(float(rp.mean()), 4), "win_rate": round(float((r > 0).mean()), 4),
            "t": round(t, 2), "base_random": round(base, 4), "base_first_bar": round(sp.base[(w, c)]["first_bar"], 4),
            "base_tod_matched": round(tm, 4), "edge": round(mean - base, 4), "edge_tod": round(mean - tm, 4),
            "t_edge": round(t_edge, 2), "ex_best_day": round(exbest, 4) if exbest is not None else None,
            "green_days": round(float((S[on] > 0).mean()), 3)}


def masks(sp: Split, bands: dict):
    df = sp.df
    for m in CONT:
        x = df[m].to_numpy(dtype=float)
        for b in bands[m]["bands"]:
            yield m, b["band"], (x > b["lo"]) & (x <= b["hi"]), b
    for m, vals in CAT.items():
        x = df[m].to_numpy(dtype=float)
        for v in vals:
            yield m, f"=={v:g}", x == v, {"band": f"=={v:g}", "lo": v, "hi": v}


def run():
    t0 = time.time()
    tr = load("train")
    bands = bands_for(tr)
    rows = []
    for split, df in (("train", tr), ("valid", None)):
        if df is None:
            df = load("valid")
        sp = Split(df)
        print(split, len(df), sp.ndays, "days", round(time.time() - t0), "s", flush=True)
        for m, band, mk, b in masks(sp, bands):
            for w in WINDOWS:
                idx = sp.first_idx(w, mk)
                for side in SIDES:
                    for g in GEOMS:
                        s = stats(sp, idx, side, g, w)
                        rows.append({"split": split, "metric": m, "band": band, "lo": b["lo"], "hi": b["hi"],
                                     "window": w, "side": side, "geom": g, **s})
        if split == "train":
            base = {f"{w}|{c}": {k: v for k, v in sp.base[(w, c)].items() if k != "random_daily"}
                    for w in WINDOWS for c in RCOLS}
        else:
            vbase = {f"{w}|{c}": {k: v for k, v in sp.base[(w, c)].items() if k != "random_daily"}
                     for w in WINDOWS for c in RCOLS}
        del sp, df
    res = pd.DataFrame(rows)
    key = ["metric", "band", "window", "side", "geom"]
    wide = res[res.split == "train"].drop(columns="split").merge(
        res[res.split == "valid"].drop(columns=["split", "lo", "hi"]), on=key, suffixes=("_tr", "_va"), how="outer")
    # plateau: mean exp_r of one-step neighbour bands (same metric/window/side/geom); categoricals use adjacent windows
    look = wide.set_index(key)
    wl = list(WINDOWS)
    pl_tr, pl_va = [], []
    mb = {m: [b["band"] for b in bands[m]["bands"]] for m in CONT}
    for r in wide.itertuples(index=False):
        if r.metric in CAT:
            i = wl.index(r.window)
            nk = [(r.metric, r.band, wl[j], r.side, r.geom) for j in (i - 1, i + 1) if 0 <= j < len(wl)]
        else:
            nk = [(r.metric, nb, r.window, r.side, r.geom) for nb in neighbours(mb[r.metric], r.band)]
        nk = [k for k in nk if k in look.index]
        pl_tr.append(float(np.nanmean([look.loc[k, "exp_r_tr"] for k in nk])) if nk else np.nan)
        pl_va.append(float(np.nanmean([look.loc[k, "exp_r_va"] for k in nk])) if nk else np.nan)
    wide["plateau_tr"], wide["plateau_va"] = np.round(pl_tr, 4), np.round(pl_va, 4)
    wide["survivor"] = ((wide.exp_r_tr > 0) & (wide.exp_r_va > 0) & (wide.edge_tr > 0) & (wide.edge_va > 0)
                        & (wide.n_va >= 30))
    wide["finalist"] = (wide.survivor & (wide.t_va >= 1.5) & (wide.plateau_tr > 0) & (wide.plateau_va > 0))
    wide.to_csv(OUT / "results.csv", index=False)
    json.dump({"bands": bands, "baseline_train": base, "baseline_valid": vbase,
               "configs": int(len(wide)), "seconds": round(time.time() - t0)},
              open(OUT / "scan_meta.json", "w"), indent=1, default=float)
    print("configs", len(wide), "survivors", int(wide.survivor.sum()), "finalists", int(wide.finalist.sum()),
          round(time.time() - t0), "s")


if __name__ == "__main__":
    run()
