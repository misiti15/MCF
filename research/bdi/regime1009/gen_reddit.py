"""Regime study: the 40 Reddit base rules (research/bdi/reddit: 20 strategies x long/short, no filter, t1s1, full day
09:50-15:00, first trade per symbol-day), generated with the Reddit engine exactly as its scan. Output (git-ignored):
data/reddit_trades.parquet (date, day, tod, symbol, r, setup, side). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RD = HERE.parent / "reddit"
sys.path.insert(0, str(RD))
import engine as E  # noqa: E402
import strategies as S  # noqa: E402

D = E.Data()
out = []
for name, (fn, p, grid, key) in S.STRATS.items():
    for s in (1, -1):
        side = "long" if s > 0 else "short"
        o = fn(D, s, p)
        idx, r = E.trades(D, o["ev"], side, "t1s1", None, None, 950, 1500)
        q = E.quick(D, idx, r)
        print(name, side, q["n"], round(q["exp"], 4), round(q["t"], 2), flush=True)
        out.append(pd.DataFrame({"day": D.B["day"][idx], "tod": D.tod[idx], "sym": D.B["sym"][idx], "r": r,
                                 "setup": f"RDT-{name}-{side}", "side": side}))
T = pd.concat(out, ignore_index=True)
T["date"] = np.array(D.dates)[T["day"].to_numpy()]
T["symbol"] = np.array(D.symbols)[T["sym"].to_numpy()]
T.drop(columns=["sym"]).to_parquet(HERE / "data" / "reddit_trades.parquet")
print(len(T))
