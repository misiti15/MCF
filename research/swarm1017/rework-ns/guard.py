"""RW6G1 VWAP-SD guard (k = 1.5 / 2 / 2.5) for the superset's NS2-type symbol-days, from the 1-min SIP cache resampled to
5-min bars exactly as the live module computes it (research/bdi/live1009/RW6G1-ns2-up3-vwap2sd-short.py vwap_band_block,
RTH bars from 09:30). Locked block rows dropped at load. Output: guard.parquet (symbol, date, tod, blk15, blk20, blk25).
Educational only - not financial advice.   python guard.py <scratch_dir>"""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.data.bars import resample  # noqa: E402

CACHE = ROOT / "data" / "cache_hist" / "1Min"
SCR = Path(sys.argv[1])


def block(c, vw, sd, key, k):
    beyond = c - vw > 0
    seg = pd.Series((~beyond).astype(np.int64)).groupby(key).cumsum().to_numpy()
    band = c - (vw + k * sd) > 0
    flag = pd.Series(band).groupby(key.astype(np.int64) * 100_000 + seg).cummax().to_numpy()
    return beyond & flag


def one(args):
    sym, dates = args
    p = CACHE / f"{sym}.parquet"
    if not p.exists():
        return None
    m1 = pd.read_parquet(p)
    ds_ = m1.index.strftime("%Y-%m-%d")
    keep = np.isin(ds_, list(dates)) & ~((ds_ >= "2024-11-01") & (ds_ <= "2025-02-28"))
    m1 = m1[keep]
    hm = m1.index.hour * 100 + m1.index.minute
    m1 = m1[(hm >= 930) & (hm < 1600)]
    out = []
    for day, g in m1.groupby(m1.index.date):
        d5 = resample(g, "5min")
        end = d5.index + pd.Timedelta(minutes=5)
        tod = end.hour * 100 + end.minute
        h, l, c, v = (d5[x].to_numpy(float) for x in ("high", "low", "close", "volume"))
        tp = (h + l + c) / 3
        cv = np.cumsum(v)
        cv[cv == 0] = np.nan
        vw = np.cumsum(tp * v) / cv
        sd = np.sqrt(np.clip(np.cumsum(tp * tp * v) / cv - vw * vw, 0, None))
        key = np.zeros(len(c), dtype=np.int64)
        with np.errstate(invalid="ignore"):
            r = pd.DataFrame({"symbol": sym, "date": day, "tod": tod,
                              "blk15": block(c, vw, sd, key, 1.5), "blk20": block(c, vw, sd, key, 2.0),
                              "blk25": block(c, vw, sd, key, 2.5)})
        out.append(r[(r.tod >= 950) & (r.tod <= 1500)])
    return pd.concat(out) if out else None


if __name__ == "__main__":
    S = pd.read_parquet(SCR / "superset.parquet", columns=["symbol", "date", "tod", "rsi", "fromOpen", "sma50_dist_pct",
                                                            "p_sma50_dist_pct"])
    m = (S.sma50_dist_pct > 0) & (S.p_sma50_dist_pct <= 0) & (S.rsi >= 50) & (S.fromOpen > 1)
    sd = S[m].groupby("symbol")["date"].apply(lambda x: sorted({str(v)[:10] for v in x}))
    print("symbols", len(sd), "symbol-days", int(sd.apply(len).sum()), flush=True)
    with Pool(4) as pool:
        res = [r for r in pool.imap_unordered(one, list(sd.items()), chunksize=4) if r is not None]
    g = pd.concat(res, ignore_index=True)
    g["date"] = pd.to_datetime(g["date"]).dt.date
    g.to_parquet(SCR / "guard.parquet")
    print("done", len(g))
