"""Point-in-time intraday BREADTH series built from the universe's own 1-minute bars (BREADTH-1125, reusable).

Usage:  python research/breadth_1125/build_breadth.py OUT_DIR
Writes OUT_DIR/breadth.parquet (date, T, n, pct_vwap, pct_open, ad30, upvol, nhnl, src) and OUT_DIR/spy.parquet
(date, T, spy_px, spy_close, y_close_up, TT1, src).

Universe = symbols present in BOTH data/cache_fresh/1Min (2023-01..2024-09, "T2") and data/cache_hist/1Min
(2024-09-16..2026-11-04, "T1"), so every split uses the same names. T = decision minute (HHMM) on the 5-minute grid
09:50..15:00; only bars labelled < T are used (the bar labelled T-1 closes at T). Among names with >= 1 bar before T:
  pct_vwap  share with last close > cumulative session VWAP
  pct_open  share with last close > the day's first 1-min open
  ad30      (n up - n down) / n on the 30-min return (last close vs last close labelled < T-30)
  upvol     sum volume of bars closing above the previous close / volume of bars closing above or below it (pooled)
  nhnl      sum over minutes 09:45..T-1 of (#names printing a new session high - #new session low) / n
SPY: spy_px = last close labelled < T, spy_close = 15:59 bar close (half days -> NaN), TT1 = Team G tape-turn gate.
The locked block 2024-11-01..2025-02-28 is never read (pyarrow filter + assert). Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

TZ = "America/New_York"
HIST = Path("/home/user/MCF/data/cache_hist/1Min")
FRESH = Path("/home/user/MCF/data/cache_fresh/1Min")
LOCK = ("2024-11-01", "2025-02-28")
T2_LO, T2_HI, T1_HI = "2023-01-03", "2024-09-13", "2026-11-04"
NMIN = 330                                    # minutes 09:30..14:59 (labels)
GRID = np.arange(20, NMIN + 1, 5)             # decision minute offsets: 09:50 (20) .. 15:00 (330)
TGRID = ((570 + GRID) // 60) * 100 + (570 + GRID) % 60


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load(sym, src):
    if src == "T1":
        f = pads.field("__index_level_0__")
        flt = (f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))
        b = pads.dataset(str(HIST / f"{sym}.parquet"), format="parquet").to_table(filter=flt).to_pandas()
    else:
        b = pd.read_parquet(FRESH / f"{sym}.parquet")
    if "__index_level_0__" in b.columns:
        b = b.set_index("__index_level_0__")
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ)
    b = b.sort_index()
    d = b.index.date.astype(str)
    keep = (d <= T1_HI) if src == "T1" else ((d >= T2_LO) & (d <= T2_HI))
    b = b[keep]
    no_locked(np.unique(b.index.date.astype(str)))
    return b


def grid2d(b, cols, nmin=NMIN):
    """-> dates, dict col -> (D x nmin) array (NaN where no bar), minute offsets from 09:30."""
    m = b.index.hour * 60 + b.index.minute - 570
    ok = (m >= 0) & (m < nmin)
    b, m = b[ok], np.asarray(m[ok])
    d = b.index.date.astype(str)
    dates, di = np.unique(d, return_inverse=True)
    out = {}
    for c in cols:
        a = np.full((len(dates), nmin), np.nan)
        a[di, m] = b[c].to_numpy(float)
        out[c] = a
    return dates, out


def ffill(a):
    idx = np.where(np.isfinite(a), np.arange(a.shape[1]), 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    r = a[np.arange(a.shape[0])[:, None], idx]
    r[~np.isfinite(a[:, :1]) & (idx == 0)] = np.nan
    return r


def sym_job(args):
    sym, src = args
    b = load(sym, src)
    if not len(b):
        return None
    dates, g = grid2d(b, ["open", "high", "low", "close", "volume"])
    O, H, L, C, V = g["open"], g["high"], g["low"], g["close"], g["volume"]
    has = np.isfinite(C)
    v0 = np.where(has, V, 0.0)
    pv = np.where(has, C * V, 0.0)
    vw = np.cumsum(pv, 1) / np.where(np.cumsum(v0, 1) > 0, np.cumsum(v0, 1), np.nan)
    first_open = O[np.arange(len(dates)), np.argmax(has, 1)]
    first_open[~has.any(1)] = np.nan
    Cf = ffill(C)
    vwf = ffill(np.where(has, vw, np.nan))
    seen = np.cumsum(has, 1) > 0
    prev = np.concatenate([np.full((len(dates), 1), np.nan), Cf[:, :-1]], 1)
    upv = np.cumsum(np.where(has & (C > prev), V, 0.0), 1)
    dnv = np.cumsum(np.where(has & (C < prev), V, 0.0), 1)
    hh = np.fmax.accumulate(np.where(has, H, -np.inf), 1)
    ll = np.fmin.accumulate(np.where(has, L, np.inf), 1)
    hprev = np.concatenate([np.full((len(dates), 1), -np.inf), hh[:, :-1]], 1)
    lprev = np.concatenate([np.full((len(dates), 1), np.inf), ll[:, :-1]], 1)
    after = np.arange(NMIN)[None, :] >= 15                      # events counted from 09:45
    nh = np.cumsum(has & after & (H > hprev) & np.isfinite(hprev), 1)
    nl = np.cumsum(has & after & (L < lprev) & np.isfinite(lprev), 1)
    k = GRID - 1                                                # bar labelled T-1
    k30 = GRID - 31
    valid = seen[:, k]
    r30 = Cf[:, k] / np.where(k30 >= 0, Cf[:, np.maximum(k30, 0)], np.nan) - 1
    res = np.stack([valid, valid & (Cf[:, k] > vwf[:, k]), valid & (Cf[:, k] > first_open[:, None]),
                    valid & (r30 > 0), valid & (r30 < 0), upv[:, k], dnv[:, k], nh[:, k], nl[:, k]], -1).astype(float)
    return src, dates, res


def spy_table(src):
    b = load("SPY", src)
    dates, g = grid2d(b, ["close", "volume"], nmin=390)
    C, V = g["close"], g["volume"]
    has = np.isfinite(C)
    Cf = ffill(C)
    vw = np.cumsum(np.where(has, C * V, 0), 1) / np.maximum(np.cumsum(np.where(has, V, 0), 1), 1)
    vwf = ffill(np.where(has, vw, np.nan))
    dist = (Cf / vwf - 1) * 100
    below = (dist <= -0.05) & (np.arange(390)[None, :] >= 5)
    cumbelow = np.cumsum(below, 1) > 0
    close = np.where(has[:, 389], C[:, 389], np.nan)            # 15:59 bar; half days -> NaN
    k, k30 = GRID - 1, GRID - 31
    tt1 = (dist[:, k] > 0) & cumbelow[:, k] & (Cf[:, k] / Cf[:, np.maximum(k30, 0)] - 1 > 0) & (k30 >= 0)[None, :]
    D, G = len(dates), len(GRID)
    return pd.DataFrame({"date": np.repeat(dates, G), "T": np.tile(TGRID, D), "spy_px": Cf[:, k].ravel(),
                         "spy_close": np.repeat(close, G), "TT1": tt1.ravel(), "src": src})


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    syms = sorted(set(p.stem for p in FRESH.glob("*.parquet")) & set(p.stem for p in HIST.glob("*.parquet")))
    acc = {}
    with Pool(3) as p:
        for r in p.imap_unordered(sym_job, [(s, src) for s in syms for src in ("T1", "T2")], chunksize=4):
            if r is None:
                continue
            src, dates, res = r
            for d, x in zip(dates, res):
                key = (src, d)
                acc[key] = acc[key] + x if key in acc else x.copy()
    rows = []
    for (src, d), x in acc.items():
        n = np.maximum(x[:, 0], 1)
        rows.append(pd.DataFrame({"date": d, "T": TGRID, "n": x[:, 0], "pct_vwap": x[:, 1] / n, "pct_open": x[:, 2] / n,
                                  "ad30": (x[:, 3] - x[:, 4]) / n,
                                  "upvol": x[:, 5] / np.maximum(x[:, 5] + x[:, 6], 1),
                                  "nhnl": (x[:, 7] - x[:, 8]) / n, "src": src}))
    br = pd.concat(rows, ignore_index=True).sort_values(["date", "T"]).reset_index(drop=True)
    br.loc[br["T"] < 1000, "ad30"] = np.nan                     # 30-min window needs >= 10:00
    no_locked(br.date.unique())
    br.to_parquet(out / "breadth.parquet")
    spy = pd.concat([spy_table("T1"), spy_table("T2")], ignore_index=True)
    spy["y_close_up"] = (spy.spy_close > spy.spy_px).where(spy.spy_close.notna())
    no_locked(spy.date.unique())
    spy.to_parquet(out / "spy.parquet")
    print(len(syms), "symbols;", br.date.nunique(), "dates;", br.groupby("src").date.nunique().to_dict())


if __name__ == "__main__":
    main(sys.argv[1])
