"""Mechanic ST7 (2026-11-16): candidate bars for ST7-rsi50dn-long-pm-t1s1-FD and every tested copy, from the lab frames
(research/history2y, open months only; the locked block 2024-11-01..2025-02-28 is never read) plus 2026-11-05..11-10
rebuilt from 1-minute bars by the CWT14 Mechanic job (same setup_lab pipeline, parity 526/526 on 11-02..11-04).
Loose superset: RSI(14) crosses below 55 from >= 45 and RSI <= 36, fromOpen < -0.7, ADV20 >= $50M, 09:50-15:00.
Educational only - not financial advice."""
import os, sys, numpy as np, pandas as pd
from multiprocessing import Pool
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
OUT = "/dev/shm/mech-st7/"
EXTRA = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14/frames_extra.parquet"
COLS = ["symbol", "date", "tod", "close", "high", "low", "rsi", "rsi5", "fromOpen", "buyPressure", "atr_d", "adv20", "gap",
        "vwapDistPct", "volumeRatio", "dist_lod_atr", "dist_hod_atr", "sma20_slope_pct", "sma50_dist_pct", "emaDiff", "flow3"]

def cut(f):
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    new = np.r_[True, (f.symbol.values[1:] != f.symbol.values[:-1]) | (f.date.values[1:] != f.date.values[:-1])]
    p = np.r_[np.nan, f.rsi.values[:-1]]; p[new] = np.nan
    f["prsi"] = p
    m = ((f.prsi >= 45) & (f.rsi < 55) & (f.rsi <= 36) & (f.fromOpen < -0.7) & (f.adv20.fillna(0) >= 50e6) &
         (f.tod >= 950) & (f.tod <= 1500) & (f.atr_d > 0))
    return f[m]

def one(m):
    f = lib.load_month(m, columns=COLS); f["date"] = f.date.astype(str)
    return cut(f)

if __name__ == "__main__":
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS]
    with Pool(4) as p:
        parts = p.map(one, ms)
    x = pd.read_parquet(EXTRA, columns=COLS); x["date"] = x.date.astype(str)
    parts.append(cut(x)[lambda d: d.date >= "2026-11-05"])
    c = pd.concat(parts, ignore_index=True)
    assert not c.date.between("2024-11-01", "2025-02-28").any()
    c.to_parquet(OUT + "cand.parquet"); print(len(c), c.date.min(), c.date.max(), c.date.nunique())
