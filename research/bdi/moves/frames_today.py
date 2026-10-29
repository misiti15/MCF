"""Move Hunt: lab frames (same features as research/history2y: heat_frame + extra_features) for one day, every bar from
09:35 (the history frames start at 09:50; rows < 09:50 are kept here for the catalogue only), plus context columns.
Usage: python frames_today.py <scratch> <day>  -> <scratch>/mh/<day>/frames.parquet. Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research.heat import heat_frame
from mcf.research.setup_lab import extra_features
from mcf.strategies.lab_context import context_from_frames

S, D = Path(sys.argv[1]), sys.argv[2]
B = pd.read_parquet(S / "mh" / D / "bars5.parquet")
day = pd.Timestamp(D).date()


def one(args):
    sym, d5 = args
    d5 = d5.drop(columns="symbol")
    if len(d5) < 300 or d5.index[-1].date() != day:
        return None
    f = heat_frame(d5); f = f.join(extra_features(d5, f)); f["symbol"] = sym
    f = f[(f.index.date == day) & (f.tod >= 935) & (f.tod <= 1500)]
    f["open"] = d5["open"].reindex(f.index); f["volume"] = d5["volume"].reindex(f.index)
    return f


if __name__ == "__main__":
    with Pool(4) as p:
        out = [x for x in p.map(one, list(B.groupby("symbol")), chunksize=20) if x is not None]
    x = pd.concat(out); x["date"] = day
    x = x.reset_index(names="ts")
    ctx = context_from_frames(x[x.tod >= 950])
    x = x.merge(ctx, on=["date", "tod"], how="left")
    x.to_parquet(S / "mh" / D / "frames.parquet")
    print(x.symbol.nunique(), "symbols", len(x), "rows; cols", len(x.columns))
