"""Candidate signals for CWT09 vwaploss (A7 trig 1) and every variant, from the live module code (cwt_live_lib.a7):
every 5-minute bar 10:30-15:00 where the A7 condition holds and the close is below VWAP, on symbol-days with
gap <= -7% (superset; variants pick the first bar that passes their own filters). Two sources:
  2y     research/history2y lab frames, open months only (the locked block 2024-11..2025-02 is never loaded)
  replay frames rebuilt from SIP 1-minute bars for 2026-10-12..11-13 (fetch_replay.py), as live
Educational only - not financial advice."""
import os, sys, numpy as np, pandas as pd
from multiprocessing import Pool
from common import OUT, LOCK, GAP_LOOSE, CODE_ROOT
sys.path[:0] = [CODE_ROOT, "/home/user/MCF/research/history2y", CODE_ROOT + "/research/bdi/cwt/live"]
import cwt_live_lib as L
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "gap", "fromOpen", "dist_pdh_atr", "dist_pdl_atr",
        "vwapDistPct", "volumeRatio", "vol_climax", "adv20", "rsi5", "rsi"]

def feats(df):
    df = df[df.gap <= -GAP_LOOSE].sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
    if not len(df): return None
    x = L.arrays(df)
    tod, c, h, l, vw = x.tod, x.c, x.h, x.l, x.vwap
    m = L.a7(df, gap=GAP_LOOSE, trig=1)
    seg = pd.Series(x.seg)
    fh = pd.Series(np.where(tod <= 1030, h, np.nan)).groupby(x.seg).transform("max").to_numpy(float)
    fl = pd.Series(np.where(tod <= 1030, l, np.nan)).groupby(x.seg).transform("min").to_numpy(float)
    with np.errstate(invalid="ignore"):
        cab = pd.Series(np.where(tod <= 1030, (c > vw).astype(float), np.nan)).groupby(x.seg).transform("max").to_numpy(float)
        exc = pd.Series(np.where(tod <= 1030, (h - vw) / x.atr, np.nan)).groupby(x.seg).transform("max").to_numpy(float)
        nab = pd.Series(np.where(tod <= 1030, (c > vw).astype(float), np.nan)).groupby(x.seg).transform("sum").to_numpy(float)
    pvd = L.prev(x, df.vwapDistPct.to_numpy(float), 1)
    idx = np.flatnonzero(m & (tod >= 1030) & (tod <= 1500))
    r = df.iloc[idx][["symbol", "date", "tod", "close", "high", "low", "atr_d", "gap", "fromOpen", "vwapDistPct", "adv20", "rsi5", "rsi", "volumeRatio"]].copy()
    r["vwap"] = vw[idx]; r["fh"] = fh[idx]; r["fl"] = fl[idx]; r["hod"] = x.hod[idx]; r["lod"] = x.lod[idx]
    r["open_d"] = x.open_d[idx]; r["pc"] = x.pc[idx]; r["cab"] = cab[idx]; r["exc"] = exc[idx]; r["nab"] = nab[idx]
    r["pvd"] = pvd[idx]
    r["date"] = r.date.astype(str)
    return r

def month(m):
    import lib
    return feats(lib.load_month(m, columns=COLS))

if __name__ == "__main__":
    import lib
    ms = [m for m in lib.months() if m not in lib.LOCKED_MONTHS and m <= "2026-10"]
    with Pool(4) as p:
        parts = [x for x in p.map(month, ms) if x is not None]
    s = pd.concat(parts, ignore_index=True)
    s = s[s.date <= "2026-10-09"]
    assert not s.date.between(*LOCK).any()
    s.to_parquet(OUT + "sig_2y.parquet"); print("2y", len(s), s.groupby(["symbol", "date"]).ngroups, s.date.min(), s.date.max())
    f = pd.read_parquet(OUT + "replay_frames.parquet").reset_index(drop=True)
    f["tod"] = f.tod.astype(int)
    r = feats(f[COLS])
    r.to_parquet(OUT + "sig_replay.parquet"); print("replay", len(r), r.groupby(["symbol", "date"]).ngroups)
