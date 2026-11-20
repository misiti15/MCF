"""Deploy-time duplicate check for BEG-ORB / BEG-GNG (2026-11-20). Inputs (trade lists, day tables) are session-scratchpad
files, not in git; output overlap.json is. Educational only - not financial advice.
Per symbol-day 09:30-09:49 stats for the BEG duplicate test (orb20_a / gap_continuation / gap_and_go fills)."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/beg_deploy")
sys.path.insert(0, str(ROOT / "research" / "ultimate_1119" / "top10"))
import bench10 as B

def job(sym):
    try:
        b = B.hist_bars(sym)
    except Exception as e:
        return None
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    hm = b.index.hour * 100 + b.index.minute
    df = pd.DataFrame({"date": b.index.date.astype(str), "hm": hm, "o": b.open.values, "h": b.high.values,
                       "l": b.low.values, "c": b.close.values, "v": b.volume.values})
    df["tpv"] = (df.h + df.l + df.c) / 3 * df.v
    out = []
    for d, g in df.groupby("date", sort=True):
        if g.hm.iloc[0] != 930:
            continue
        r = g[g.hm <= 949]
        if not len(r) or r.hm.iloc[-1] != 949:
            continue
        r5 = g[g.hm <= 934]
        w1 = g[(g.hm >= 950) & (g.hm <= 1129)]
        w2 = g[(g.hm >= 950) & (g.hm <= 1059)]
        w3 = g[(g.hm >= 935) & (g.hm <= 1034)]
        vw = r.tpv.sum() / r.v.sum() if r.v.sum() > 0 else np.nan
        vw5 = r5.tpv.sum() / r5.v.sum() if r5.v.sum() > 0 else np.nan
        out.append((sym, d, r.o.iloc[0], r.h.max(), r.l.min(), r.c.iloc[-1], vw, r.v.sum(),
                    w1.h.max() if len(w1) else np.nan, w1.l.min() if len(w1) else np.nan,
                    w2.h.max() if len(w2) else np.nan, w2.l.min() if len(w2) else np.nan,
                    r5.h.max(), r5.l.min(), r5.c.iloc[-1], vw5, r5.v.sum(), w3.h.max() if len(w3) else np.nan))
    return pd.DataFrame(out, columns=["symbol", "date", "o930", "hi20", "lo20", "c949", "vw949", "v20", "h_1129",
                                      "l_1129", "h_1059", "l_1059", "hi5", "lo5", "c934", "vw934", "v5", "h5_1034"])

if __name__ == "__main__":
    syms = sorted(p.stem for p in Path("/home/user/MCF/data/cache_hist/1Min").glob("*.parquet"))
    with Pool(4) as pool:
        parts = [x for x in pool.imap_unordered(job, syms, chunksize=8) if x is not None]
    D = pd.concat(parts, ignore_index=True)
    D.to_parquet(Path(__file__).parent / "r20.parquet")
    print(len(D))
