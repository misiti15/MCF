"""Reddit liquidity study, daily-bar version (PLAN.md section 6; information only, not eligible for Testing).

Sweep of the prior n-day high (low) by >= x * ATR14 with the close back inside; enter at the next open in the
reversal direction; exit after 1 / 3 / 5 days at the close, or S2R (stop at the sweep extreme + 0.05 ATR, 2R target,
stop first, gap-through at the open, max 10 days). Costs 1c + 1 bps per side, shorts 3%/yr borrow. One open position per
symbol per configuration. Locked rows (2024-11-01..2025-02-28) are dropped before any computation; look-backs that
span the gap are NaN and trades across it are dropped.

    python research/bdi/reddit1012liq/daily.py      # -> data/daily_results.csv
Educational only - not financial advice.
"""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

SPLITS = {"train": ("2016-01-01", "2022-12-31"), "valid1": ("2023-01-01", "2024-10-31"),
          "valid2": ("2025-03-01", "2026-12-31")}


@numba.njit(cache=True)
def run(o, h, l, c, lvl, atr, elig, side, x, mode, hold, gapflag):
    """mode 0: hold `hold` days; mode 1: S2R. Returns entry index, exit index, net return (fraction), R."""
    n = len(c)
    ei = np.empty(n, np.int64)
    xi = np.empty(n, np.int64)
    ret = np.empty(n)
    rr = np.empty(n)
    m = 0
    busy = -1
    for t in range(n - 1):
        if t <= busy or not elig[t] or np.isnan(lvl[t]) or np.isnan(atr[t]) or gapflag[t + 1]:
            continue
        if side < 0:
            sweep = h[t] >= lvl[t] + x * atr[t] and c[t] < lvl[t]
        else:
            sweep = l[t] <= lvl[t] - x * atr[t] and c[t] > lvl[t]
        if not sweep:
            continue
        e = o[t + 1]
        if mode == 0:
            k = t + hold
            if k >= n:
                continue
            bad = False
            for q in range(t + 1, k + 1):
                if gapflag[q]:
                    bad = True
            if bad:
                continue
            xp = c[k]
            risk = 0.25 * atr[t]
        else:
            stop = h[t] + 0.05 * atr[t] if side < 0 else l[t] - 0.05 * atr[t]
            risk = side * (e - stop)
            if risk <= 0:
                continue
            tg = e + side * 2.0 * risk
            k = t + 1
            xp = np.nan
            bad = False
            while k < n and k <= t + 10:
                if gapflag[k] and k > t + 1:
                    bad = True
                    break
                op = o[k] if k > t + 1 else e
                if (side > 0 and l[k] <= stop) or (side < 0 and h[k] >= stop):
                    xp = op if (side > 0 and op < stop) or (side < 0 and op > stop) else stop
                    break
                if (side > 0 and h[k] >= tg) or (side < 0 and l[k] <= tg):
                    xp = tg
                    break
                if k == t + 10 or k == n - 1:
                    xp = c[k]
                    break
                k += 1
            if bad or np.isnan(xp):
                continue
        gross = side * (xp - e) / e
        cost = (0.01 / e + 1e-4) + (0.01 / xp + 1e-4)
        ret[m] = gross - cost
        rr[m] = (side * (xp - e) - 0.01 - e * 1e-4 - 0.01 - xp * 1e-4) / risk
        ei[m] = t + 1
        xi[m] = k
        m += 1
        busy = k
    return ei[:m], xi[:m], ret[:m], rr[:m]


def ctstat(r, blk):
    mu = r.mean()
    g = pd.DataFrame({"b": blk, "r": r}).groupby("b")["r"].agg(["sum", "size"])
    se = math.sqrt(((g["sum"] - g["size"] * mu) ** 2).sum()) / len(r)
    return mu / se if se > 0 else 0.0


def main():
    d = pd.read_parquet(ROOT / "research" / "swarm1010" / "w3_daily" / "data" / "daily_2016.parquet",
                        columns=["symbol", "date", "open", "high", "low", "close", "volume"])
    d["date"] = pd.to_datetime(d["date"])
    s = d["date"].dt.strftime("%Y-%m-%d")
    d = d[(s < lib.LOCKED[0]) | (s > lib.LOCKED[1])].copy()          # locked rows dropped before anything
    d["symbol"] = d["symbol"].astype(str)
    d = d.sort_values(["symbol", "date"]).reset_index(drop=True)
    gap_lo, gap_hi = pd.Timestamp(lib.LOCKED[0]), pd.Timestamp(lib.LOCKED[1])
    cal = pd.DatetimeIndex(sorted(d["date"].unique()))
    cpos = {t: i for i, t in enumerate(cal)}
    grid = list(itertools.product((-1, 1), (10, 20), (0.0, 0.1), ("h1", "h3", "h5", "S2R")))
    res = {g: {"date": [], "ret": [], "rr": [], "blk": []} for g in grid}
    for sym, x in d.groupby("symbol", sort=False):
        if len(x) < 60:
            continue
        o, h, l, c, v = (x[k].to_numpy(float) for k in ("open", "high", "low", "close", "volume"))
        dt = x["date"].to_numpy()
        gapflag = np.r_[False, (dt[1:] > np.datetime64(gap_hi)) & (dt[:-1] < np.datetime64(gap_lo))]
        pc = np.r_[np.nan, c[:-1]]
        tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
        atr = pd.Series(tr).rolling(14, min_periods=14).mean().shift(1).to_numpy()
        dv = pd.Series(c * v).rolling(20, min_periods=20).mean().to_numpy()
        elig = (c >= 5) & (dv >= 20e6)
        gidx = np.cumsum(gapflag)                                      # segment id around the locked gap
        for side, n, xx, ex in grid:
            src = pd.Series(h if side < 0 else l)
            lv = (src.rolling(n, min_periods=n).max() if side < 0 else src.rolling(n, min_periods=n).min()).shift(1)
            gs = pd.Series(gidx)
            lv = lv.where(gs.shift(1) == gs.shift(n))                  # window must not span the locked gap
            mode, hold = (1, 10) if ex == "S2R" else (0, int(ex[1:]))
            ei, xi, ret, rr = run(o, h, l, c, lv.to_numpy(float), atr, elig, side, xx, mode, hold, gapflag)
            if not len(ei):
                continue
            # shorts: borrow 3%/yr per calendar day held
            if side < 0:
                days = (dt[xi] - dt[ei]).astype("timedelta64[D]").astype(float)
                ret = ret - 0.03 * np.maximum(days, 1) / 365
            r = res[(side, n, xx, ex)]
            r["date"].append(dt[ei]); r["ret"].append(ret); r["rr"].append(rr)
            bl = max(1, 2 * hold)
            r["blk"].append(np.array([cpos[pd.Timestamp(q)] // bl for q in dt[ei]]))
    rows = []
    for (side, n, xx, ex), r in res.items():
        if not r["date"]:
            continue
        dts = pd.to_datetime(np.concatenate(r["date"]))
        ret = np.concatenate(r["ret"]) * 1e4
        rr = np.concatenate(r["rr"])
        blk = np.concatenate(r["blk"])
        row = {"config": f"D-{'short' if side < 0 else 'long'}-n{n}-x{xx}-{ex}"}
        for sp, (a, b) in SPLITS.items():
            m = (dts >= a) & (dts <= b)
            row[f"{sp}_n"] = int(m.sum())
            row[f"{sp}_bps"] = round(float(ret[m].mean()), 2) if m.any() else None
            row[f"{sp}_t"] = round(ctstat(ret[m], blk[m]), 2) if m.sum() > 2 else None
            if ex == "S2R":
                row[f"{sp}_R"] = round(float(rr[m].mean()), 3) if m.any() else None
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "data" / "daily_results.csv", index=False)
    pd.set_option("display.width", 250)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
