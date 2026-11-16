"""Mechanic CWT14-orl-p10: candidate signals from the 2-year lab frames (open months only; locked block never read).
Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, "/home/user/MCF/research/history2y"); sys.path.insert(0, "/home/user/MCF/research/bdi/cwt/live"); sys.path.insert(0, "/home/user/MCF")
from lib import load_month, months
import cwt_live_lib as L
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14/"
COLS = ["symbol","date","tod","close","high","low","atr_d","gap","fromOpen","dist_pdh_atr","dist_pdl_atr","vwapDistPct",
        "volumeRatio","vol_climax","adv20","rsi5","rsi","buyPressure","flow3","dist_lod_atr","sma20_dist_pct","sma50_dist_pct","dist_hod_atr"]
PS = [0.10, 0.15, 0.08]

def one(m):
    df = load_month(m, columns=COLS)
    df = df[df.adv20.fillna(0) >= 50e6].reset_index(drop=True)
    x = L.arrays(df)
    # OR low (as b3) for diagnostics
    at10 = np.where(x.tod == 1000, x.lod, np.nan)
    orl = pd.Series(at10).groupby(x.seg).ffill().to_numpy(float)
    out = []
    masks = {p: L.b3(df, level='OR', p=p, lowvol=False, side='long') for p in PS}
    any_ = np.zeros(len(df), bool)
    for p in PS: any_ |= masks[p]
    idx = np.flatnonzero(any_ & (df.tod.to_numpy() >= 950) & (df.tod.to_numpy() <= 1500))
    r = df.iloc[idx].copy()
    for p in PS: r[f"m{int(p*100):02d}"] = masks[p][idx]
    r["orl"] = orl[idx]; r["lod"] = x.lod[idx]; r["vwap"] = x.vwap[idx]; r["open_d"] = x.open_d[idx]; r["pc"] = x.pc[idx]
    r["month"] = m
    return r

if __name__ == "__main__":
    ms = [m for m in months() if m not in ("2024-11","2024-12","2025-01","2025-02")]
    with Pool(4) as p:
        parts = p.map(one, ms)
    s = pd.concat(parts, ignore_index=True)
    s.to_parquet(OUT + "sig_frames.parquet"); print(len(s), s.groupby("month").size().to_dict())
