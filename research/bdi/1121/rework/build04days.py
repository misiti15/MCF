"""Rebuild the BEG-02 T1 day table (rvol20 / rank_rvol20 point-in-time) that BEG-04 reads, with BEG-02's own build code
(research/beginner_1120/BEG-02-vwap-first-pullback/run.py t1_ctx / t1_job / the same rvol20 + rank lines), without the
candidate-bar file (disk). -> ../scratch/beg02w/days_t1.parquet. Locked block never read (bench10.hist_bars + asserts).
Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[3] / "research/beginner_1120/BEG-02-vwap-first-pullback"
sys.path.insert(0, str(SRC))
import run as R2  # noqa: E402
B = R2.B
W = HERE.parent / "scratch/beg02w"; W.mkdir(parents=True, exist_ok=True)


def job(a):
    r, _ = R2.t1_job(a)
    return r


if __name__ == "__main__":
    if not (W / "ctx1.parquet").exists():
        R2.t1_ctx().to_parquet(W / "ctx1.parquet")
    syms = sorted(p.stem for p in B.CACHE.glob("*.parquet"))
    rows = []
    with Pool(3) as p:
        for i, r in enumerate(p.imap_unordered(job, [(s, str(W)) for s in syms], chunksize=4)):
            rows.extend(r)
            if i % 200 == 0:
                print(i, len(rows), flush=True)
    D = pd.DataFrame(rows, columns=["symbol", "date", "prev_close", "atr", "adv20", "v0949", "move950", "side", "gap"])
    D = D.sort_values(["symbol", "date"]).reset_index(drop=True)
    B.no_locked(D.date.unique())
    dt = pd.to_datetime(D.date)
    seg = ((D.symbol != D.symbol.shift()) | ((dt - dt.shift()).dt.days > 10)).cumsum()
    D["avg0949"] = D.groupby(seg).v0949.transform(lambda s: s.shift(1).rolling(14, min_periods=5).mean())
    D["rvol20"] = D.v0949 / D.avg0949.where(D.avg0949 > 0)
    u0 = (D.prev_close >= 5) & (D.adv20 >= 20e6) & D.rvol20.notna()
    D["rank_rvol20"] = np.nan
    D.loc[u0, "rank_rvol20"] = D[u0].groupby("date").rvol20.rank(ascending=False, method="first")
    D.to_parquet(W / "days_t1.parquet")
    (W / "ctx1.parquet").unlink()
    print("days", len(D))
