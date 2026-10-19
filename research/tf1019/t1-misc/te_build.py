"""Time-equivalent (TE) indicator columns for tf1019/t1-misc (copy of research/tf1019/primary/te_build.py; adds the
heat components rsiHeat/momentumHeat/priceActionHeat/vwapHeat that the heat_fade formulas read; see PLAN.md).

For decision bars of m minutes, recompute the bar-count columns the 12 Primary masks read - rsi, rsi5, buyPressure,
sma50_dist_pct, heat (all inner lookbacks) - with every lookback n scaled to max(2, round(n * 5 / m)), i.e. the same
clock-time span as on 5-minute bars. Same source and resampling as the frames (data/cache_hist 1-minute SIP ->
mcf.data.bars.resample), `tod` = true bar-close HHMM, rows 09:50-15:00. Locked dates (2024-11-01..2025-02-28) are
dropped right after load, before anything is computed. Output: <out>/te_<m>min.parquet (scratch only).
    python research/tf1019/primary/te_build.py --out <scratch> [--minutes 1,3,10,15] [--check]
--check builds m=5 with scale 1 for 3 symbols and compares with frames_tf/5min (parity).
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
from mcf.research.heat import COMPONENTS, _rsi_simple  # noqa: E402

LOCKED = ("2024-11-01", "2025-02-28")
FIRST = "2024-10-01"
COLS = ["rsi", "rsi5", "buyPressure", "sma50_dist_pct", "heat", "rsiHeat", "momentumHeat", "priceActionHeat", "vwapHeat"]


def L(n: int, m: int) -> int:
    return max(2, int(round(n * 5 / m)))


def te_frame(d: pd.DataFrame, m: int) -> pd.DataFrame:
    """heat_frame + sma50 with lookbacks scaled to the 5-minute clock span (m=5 -> identical lookbacks)."""
    c, h, l, v, o = d["close"], d["high"], d["low"], d["volume"], d["open"]
    day = pd.Series(d.index.date, index=d.index)
    f = pd.DataFrame(index=d.index)
    f["rsi"] = _rsi_simple(c, L(14, m))
    f["rsi5"] = _rsi_simple(c, L(5, m))
    m5 = (c / c.shift(L(4, m)) - 1) * 100
    m10 = (c / c.shift(L(9, m)) - 1) * 100
    mom = m5 * 0.6 + m10 * 0.4
    ema = lambda n: c.ewm(span=L(n, m), adjust=False).mean()  # noqa: E731
    e9, e21 = ema(9), ema(21)
    emaDiff = (e9 - e21) / e21 * 100
    macdPct = (ema(12) - ema(26)) / c * 100
    avgv = v.rolling(L(20, m)).mean()
    vr = (v / avgv.replace(0, np.nan)).fillna(1)
    vs = (v.rolling(L(5, m)).mean() / v.shift(L(5, m)).rolling(L(15, m)).mean().replace(0, np.nan)).fillna(1)
    hi20, lo20 = h.rolling(L(20, m)).max(), l.rolling(L(20, m)).min()
    pp = ((c - lo20) / (hi20 - lo20).replace(0, np.nan)).fillna(0.5)
    typ = (h + l + c) / 3
    vw = (typ * v).groupby(day).cumsum() / v.groupby(day).cumsum().replace(0, np.nan)
    vdp = (c - vw) / vw * 100
    sgn = np.sign(c - o)
    n19 = L(19, m)
    f["buyPressure"] = ((sgn * v).rolling(n19).sum() / v.rolling(n19).sum().replace(0, np.nan)).clip(-1, 1)
    f["sma50_dist_pct"] = (c / c.rolling(L(50, m)).mean() - 1) * 100
    comp = pd.DataFrame(index=d.index)
    comp["volumeHeat"] = np.select([vs > 2, vr > 1.5, vr < 0.5], [20, np.minimum(20, (vr - 1) * 20), -10], (vr - 1) * 15)
    r = f.rsi.fillna(50)
    comp["rsiHeat"] = np.select([r >= 80, r >= 70, r <= 20, r <= 30, r < 45, r > 55],
                                [-25, -((r - 70) / 10) * 20, 25, ((30 - r) / 10) * 20, (45 - r) / 15 * 10, (55 - r) / 15 * 10], 0)
    comp["momentumHeat"] = (mom.fillna(0) * 8).clip(-20, 20)
    comp["priceActionHeat"] = np.select([pp <= 0.2, pp >= 0.8], [15, -15], (0.5 - pp) * 20)
    comp["trendHeat"] = (emaDiff.fillna(0) * 5).clip(-15, 15)
    comp["macdHeat"] = (macdPct.fillna(0) * 20).clip(-10, 10)
    comp["vwapHeat"] = (vdp.fillna(0) * 12).clip(-12, 12)
    vh, mh, rh, ph = comp.volumeHeat, comp.momentumHeat, comp.rsiHeat, comp.priceActionHeat
    bonus = (np.where((vh > 5) & (mh > 5), 5, 0) + np.where((rh > 10) & (ph > 5), 5, 0)
             + np.where((vh < -5) & (mh < -5), -5, 0) + np.where((rh < -10) & (ph < -5), -5, 0))
    f["heat"] = (comp[COMPONENTS].sum(axis=1) + bonus).clip(-100, 100)
    for k in ("rsiHeat", "momentumHeat", "priceActionHeat", "vwapHeat"):
        f[k] = comp[k]
    end = d.index + pd.Timedelta(minutes=m)
    f["tod"] = (end.hour * 100 + end.minute).astype("int16")
    f["date"] = d.index.date
    f = f[(f.tod >= 950) & (f.tod <= 1500)]
    s = pd.Series(f["date"]).astype(str).to_numpy()
    f = f[s >= FIRST]
    return f


def one(args):
    sym, minutes = args
    df = BarStore(ROOT / "data" / "cache_hist").load(sym)
    if df.empty:
        return {}
    s = pd.Series(df.index.date, index=df.index).astype(str)
    df = df[~((s >= LOCKED[0]) & (s <= LOCKED[1])).to_numpy()]          # locked block never enters a computation
    out = {}
    for m in minutes:
        f = te_frame(resample(df, f"{m}min"), m).reset_index(drop=True)
        f["symbol"] = sym
        for k in COLS:
            f[k] = f[k].astype("float32")
        out[m] = f[["symbol", "date", "tod"] + COLS]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--minutes", default="1,3,10,15")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    from mcf.research import timeframes as tf
    if a.check:
        syms = ["SPY", "AAPL", tf.universe("core")[-1]]
        res = [one((s, [5])) for s in syms]
        te = pd.concat([r[5] for r in res if r], ignore_index=True)
        fr = pd.concat([tf.load_tf(5, mo, ["symbol", "date", "tod"] + COLS, syms) for mo in ("2025-06", "2026-09")])
        j = fr.merge(te, on=["symbol", "date", "tod"], suffixes=("", "_te"))
        rep = {"rows_frame": len(fr), "rows_joined": len(j)}
        for k in COLS:
            dlt = (j[k] - j[k + "_te"]).abs()
            rep[k] = {"max_abs_diff": float(np.nanmax(dlt)), "nan_mismatch": int((j[k].isna() != j[k + "_te"].isna()).sum())}
        print(rep)
        return
    minutes = [int(x) for x in a.minutes.split(",")]
    syms = tf.universe("core")
    acc = {m: [] for m in minutes}
    with Pool(a.workers) as p:
        for r in p.imap_unordered(one, [(s, minutes) for s in syms]):
            for m, f in r.items():
                acc[m].append(f)
    for m in minutes:
        x = pd.concat(acc[m], ignore_index=True)
        acc[m] = None
        d = out / f"te_{m}min"
        d.mkdir(exist_ok=True)
        mo = pd.Series(x["date"]).astype(str).str[:7]
        for k, g in x.groupby(mo):
            g.to_parquet(d / f"{k}.parquet", index=False, compression="zstd")
        print(m, len(x), flush=True)
        del x


if __name__ == "__main__":
    main()
