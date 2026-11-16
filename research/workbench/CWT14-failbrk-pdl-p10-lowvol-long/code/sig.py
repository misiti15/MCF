"""Mechanic CWT14-pdl-p10-lowvol: candidate signals (b3 PD long, p in {0.08,0.10,0.15}, lowvol on/off) from the 2-year lab
frames (open months only; locked block 2024-11..2025-02 never read) + rebuilt frames 11-05..11-10 (sibling job's
frames_extra.parquet, same setup_lab pipeline). Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, "/home/user/MCF/research/history2y"); sys.path.insert(0, "/home/user/MCF/research/bdi/cwt/live"); sys.path.insert(0, "/home/user/MCF")
from lib import load_month, months
import cwt_live_lib as L
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/"
EXTRA = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14/frames_extra.parquet"
COLS = ["symbol","date","tod","close","high","low","atr_d","gap","fromOpen","dist_pdh_atr","dist_pdl_atr","vwapDistPct",
        "volumeRatio","vol_climax","adv20","rsi5","rsi","buyPressure","flow3","dist_lod_atr","sma20_dist_pct","sma50_dist_pct","dist_hod_atr"]
VAR = [(0.10, True), (0.10, False), (0.15, True), (0.08, True)]

def build(df, m):
    df = df[df.adv20.fillna(0) >= 50e6].sort_values(["symbol","date","tod"]).reset_index(drop=True)
    x = L.arrays(df)
    masks = {v: L.b3(df, level='PD', p=v[0], lowvol=v[1], side='long') for v in VAR}
    any_ = np.zeros(len(df), bool)
    for v in VAR: any_ |= masks[v]
    idx = np.flatnonzero(any_ & (df.tod.to_numpy() >= 950) & (df.tod.to_numpy() <= 1500))
    r = df.iloc[idx].copy()
    for v in VAR: r[f"m{int(v[0]*100):02d}{'v' if v[1] else 'a'}"] = masks[v][idx]
    r["pdl"] = x.pdl[idx]; r["lod"] = x.lod[idx]; r["hod"] = x.hod[idx]; r["vwap"] = x.vwap[idx]; r["open_d"] = x.open_d[idx]; r["pc"] = x.pc[idx]
    # poke-bar volumeRatio and bars from poke: rebuild cheaply = min volumeRatio of last 4 bars (diagnostic)
    r["month"] = m; r["date"] = r.date.astype(str)
    return r

def one(m):
    return build(load_month(m, columns=COLS), m)

if __name__ == "__main__":
    ms = [m for m in months() if m not in ("2024-11","2024-12","2025-01","2025-02")]
    with Pool(4) as p:
        parts = p.map(one, ms)
    e = pd.read_parquet(EXTRA, columns=COLS); e["date"] = e.date.astype(str)
    r = build(e, "2026-11x")
    s = pd.concat(parts, ignore_index=True); s["date"] = s.date.astype(str)
    # parity 11-02..11-04 (rebuilt vs stored frames), parent mask
    a = s[(s.date >= "2026-11-02") & s.m10v & (s.adv20 >= 95e6)][["symbol","date","tod"]]
    b = r[(r.date <= "2026-11-04") & r.m10v & (r.adv20 >= 95e6)][["symbol","date","tod"]]
    print("parity 11-02..04:", a.merge(b, how="outer", indicator=True)._merge.value_counts().to_dict())
    s = pd.concat([s, r[r.date >= "2026-11-05"]], ignore_index=True)
    assert not ((s.date >= "2024-11-01") & (s.date <= "2025-02-28")).any()
    s.to_parquet(OUT + "sig.parquet"); print(len(s), s.m10v.sum(), s.date.max())
