"""Rebuild research/bdi/cwt/test_b/data/headtail.parquet (+ rvol12.parquet) with prep.one() only (prep.main() also
needs the 10-year daily file research/swarm1010/w3_daily/data/daily_2016.parquet, not in this container; latch / bt_all
need only head/tail). Locked block filtered at read inside prep.one()."""
import sys, time
from multiprocessing import Pool
import pandas as pd
sys.path.insert(0, "/home/user/MCF/research/bdi/cwt/test_b")
import prep
def job(s):
    if not (prep.CACHE / f"{s}.parquet").exists(): return None
    a, b = prep.one(s)
    if a is not None:
        for c in ("h", "l", "c", "vwap"): a[c] = a[c].astype("float32")
    return a, b
if __name__ == "__main__":
    prep.OUT.mkdir(exist_ok=True)
    syms = [s.strip() for s in open(prep.ROOT / "research" / "lab_symbols.txt").read().split() if s.strip()]
    t0 = time.time(); rows, rvs = [], []
    with Pool(4) as p:
        for r in p.imap(job, syms, chunksize=8):
            if r and r[0] is not None: rows.append(r[0]); rvs.append(r[1])
    x = pd.concat(rows, ignore_index=True); x["symbol"] = x["symbol"].astype("category")
    x.to_parquet(prep.OUT / "headtail.parquet", index=False, compression="zstd")
    pd.concat(rvs, ignore_index=True).to_parquet(prep.OUT / "rvol12.parquet", index=False)
    print("headtail rows", len(x), "symbols", x.symbol.nunique(), round(time.time() - t0), "s")
