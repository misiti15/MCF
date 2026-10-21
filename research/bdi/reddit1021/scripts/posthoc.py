"""reddit1021 post-hoc checks (NOT pre-declared; chosen after seeing stage-1; counted in N and labelled post-hoc):
skip trigger candles before 10:20 (the 09:50-10:15 bucket was the worst in both groups), alone and with the
candle-close entry. Educational only - not financial advice."""
import sys
from multiprocessing import Pool

import pandas as pd

import run as RUN
from common import HERE, SCR

CFGS = [("C-f0.5-t2.0-eod+from1020", "posthoc", dict(type_=0, klo=9)),
        ("R-f0.5-t2.0-eod+from1020", "posthoc", dict(type_=1, klo=9)),
        ("C-f0.5-t2.0-eod+market_close+from1020", "posthoc", dict(type_=0, klo=9, entry=2))]

if __name__ == "__main__":
    group = sys.argv[1]
    syms = ["SPY", "QQQ"] if group == "idx" else sorted(p.stem for p in (SCR / "prep").glob("*.npz") if p.stem not in ("SPY", "QQQ"))
    spy = None if group == "idx" else RUN.load("SPY")
    with Pool(4, initializer=RUN._init, initargs=(spy,)) as pool:
        parts = [d for d in pool.imap_unordered(RUN.sym_run, [(s, group, CFGS, 60 if group == "idx" else 20) for s in syms], chunksize=4) if d is not None]
    T = pd.concat(parts, ignore_index=True)
    T.to_parquet(SCR / f"trades_{group}_ph.parquet")
    import numpy as np
    from common import split_of
    z = RUN.load("SPY"); sp = split_of(z["days"])
    S = RUN.summarise(T, CFGS, {"train": int((sp == "train").sum()), "valid": int((sp == "valid").sum()), "all": len(sp)}, group)
    S.to_csv(HERE / f"results_{group}_ph.csv", index=False)
    print(S[["cfg", "train_n", "train_exp", "train_t", "valid_n", "valid_exp", "valid_t", "all_excess"]].to_string())
