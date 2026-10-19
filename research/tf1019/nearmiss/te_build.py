"""Time-equivalent (TE) indicator columns for tf1019/nearmiss (see PLAN.md).

For m-minute decision bars, recompute the bar-count columns the 12 near-miss masks read with every lookback scaled to
its 5-minute clock span: windows -> max(2, floor(n*5/m+0.5)), shifts -> max(1, floor(n*5/m+0.5)). Same source and
resampling as the frames (data/cache_hist 1-minute SIP -> mcf.data.bars.resample) and the same formulas as
heat.heat_frame / setup_lab.extra_features. `tod` = true bar-close HHMM, rows 09:50-15:00. Locked dates
(2024-11-01..2025-02-28) are dropped right after load, before anything is computed.
    python research/tf1019/nearmiss/te_build.py --out <scratch> [--minutes 1,3,10,15] [--check]
Output: <out>/te_<m>min/<YYYY-MM>.parquet. --check builds m=5 for 3 symbols and compares with frames_tf/5min.
Educational only - not financial advice."""
from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import resample  # noqa: E402
from mcf.data.store import BarStore  # noqa: E402
from mcf.research.heat import _rsi_simple  # noqa: E402

LOCKED = ("2024-11-01", "2025-02-28")
FIRST = "2024-10-01"
COLS = ["rsi", "rsi5", "sma50_dist_pct", "sma20_dist_pct", "sma20_slope_pct", "buyPressure", "volumeRatio",
        "bear_div", "rsiHeat", "momentumHeat", "priceActionHeat"]


def W(n: int, m: int) -> int:
    """Rolling window / indicator length on m-minute bars spanning the clock time of n 5-minute bars."""
    return max(2, int(np.floor(n * 5 / m + 0.5)))


def SH(n: int, m: int) -> int:
    """Shift (k bars ago) on m-minute bars spanning the clock time of n 5-minute bars."""
    return max(1, int(np.floor(n * 5 / m + 0.5)))


def te_frame(d: pd.DataFrame, m: int, scale: bool = True) -> pd.DataFrame:
    w = (lambda n: W(n, m)) if scale else (lambda n: n)
    s = (lambda n: SH(n, m)) if scale else (lambda n: n)
    c, h, l, v, o = d["close"], d["high"], d["low"], d["volume"], d["open"]
    f = pd.DataFrame(index=d.index)
    f["rsi"] = _rsi_simple(c, w(14))
    f["rsi5"] = _rsi_simple(c, w(5))
    m5 = (c / c.shift(s(4)) - 1) * 100
    m10 = (c / c.shift(s(9)) - 1) * 100
    mom = m5 * 0.6 + m10 * 0.4
    avgv = v.rolling(w(20)).mean()
    f["volumeRatio"] = v / avgv.replace(0, np.nan)
    hi20, lo20 = h.rolling(w(20)).max(), l.rolling(w(20)).min()
    pp = ((c - lo20) / (hi20 - lo20).replace(0, np.nan)).fillna(0.5)
    sgn = np.sign(c - o)
    n19 = w(19)
    f["buyPressure"] = ((sgn * v).rolling(n19).sum() / v.rolling(n19).sum().replace(0, np.nan)).clip(-1, 1)
    sma20, sma50 = c.rolling(w(20)).mean(), c.rolling(w(50)).mean()
    f["sma20_dist_pct"] = (c / sma20 - 1) * 100
    f["sma50_dist_pct"] = (c / sma50 - 1) * 100
    f["sma20_slope_pct"] = (sma20 / sma20.shift(s(5)) - 1) * 100
    f["bear_div"] = ((h >= hi20) & (f["rsi"] < f["rsi"].rolling(w(20)).max() - 5)).astype(int)
    r = f.rsi.fillna(50)
    f["rsiHeat"] = np.select([r >= 80, r >= 70, r <= 20, r <= 30, r < 45, r > 55],
                             [-25, -((r - 70) / 10) * 20, 25, ((30 - r) / 10) * 20, (45 - r) / 15 * 10, (55 - r) / 15 * 10], 0)
    f["momentumHeat"] = (mom.fillna(0) * 8).clip(-20, 20)
    f["priceActionHeat"] = np.select([pp <= 0.2, pp >= 0.8], [15, -15], (0.5 - pp) * 20)
    end = d.index + pd.Timedelta(minutes=m)
    f["tod"] = (end.hour * 100 + end.minute).astype("int16")
    f["date"] = d.index.date
    f = f[(f.tod >= 950) & (f.tod <= 1500)]
    f = f[pd.Series(f["date"]).astype(str).to_numpy() >= FIRST]
    return f


def one(args):
    sym, minutes, scale = args
    df = BarStore(ROOT / "data" / "cache_hist").load(sym)
    if df.empty:
        return {}
    s = pd.Series(df.index.date, index=df.index).astype(str)
    df = df[~((s >= LOCKED[0]) & (s <= LOCKED[1])).to_numpy()]          # locked block never enters a computation
    out = {}
    for m in minutes:
        f = te_frame(resample(df, f"{m}min"), m, scale).reset_index(drop=True)
        f["symbol"] = sym
        for k in COLS:
            f[k] = f[k].astype("float32")
        out[m] = f[["symbol", "date", "tod"] + COLS]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--minutes", default="1,3,10,15")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    from mcf.research import timeframes as tf
    if a.check:
        syms = ["SPY", "AAPL", tf.universe("core")[-1]]
        rep = {}
        for m in (5, 1, 15):
            res = [one((s, [m], m == 5)) for s in syms]       # m=5 scaled==unscaled; m=1/15 unscaled == as-is frames
            te = pd.concat([r[m] for r in res if r], ignore_index=True)
            fr = pd.concat([tf.load_tf(m, mo, ["symbol", "date", "tod"] + COLS, syms) for mo in ("2025-06", "2026-09")])
            j = fr.merge(te, on=["symbol", "date", "tod"], suffixes=("", "_te"))
            rr = {"rows_frame": len(fr), "rows_joined": len(j)}
            for k in COLS:
                dlt = (j[k].astype(float) - j[k + "_te"].astype(float)).abs()
                rr[k] = round(float(np.nanmax(dlt)), 6)
            rep[m] = rr
        print(rep)
        return
    minutes = [int(x) for x in a.minutes.split(",")]
    syms = tf.universe("core")
    acc = {m: [] for m in minutes}
    with Pool(a.workers) as p:
        for r in p.imap_unordered(one, [(s, minutes, True) for s in syms]):
            for m, f in r.items():
                acc[m].append(f)
    for m in minutes:
        x = pd.concat(acc[m], ignore_index=True)
        acc[m] = None
        d = out / f"te_{m}min"
        d.mkdir(exist_ok=True)
        mo = pd.Series(x["date"]).astype(str).str[:7]
        for k, g in x.groupby(mo):
            g.to_parquet(d / f"{k}.parquet", index=False)
        print(m, len(x), flush=True)
        del x


if __name__ == "__main__":
    main()
