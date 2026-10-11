"""OF-A live feasibility numbers: message rates (trades + NBBO quotes) per symbol from the downloaded sample, and the
quoted spread in bps (the cost a 1-second flow signal must beat). -> feasibility.csv. Educational only."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import of_lib as L

HERE = Path(__file__).resolve().parent


def main():
    m = L.meta()
    rows = []
    for sym, g in m.groupby("symbol"):
        peaks, spr = [], []
        for d in L.DAYS[-5:]:
            x = L.load_day(sym, d)
            if x is None:
                continue
            msg = (x.n_tr + x.n_q).to_numpy()
            peaks.append((np.percentile(msg, 99), msg.max()))
            s = (x.spread_tw / x.mid * 1e4).to_numpy()[L.W0:L.W1]
            spr.append(np.nanmedian(s))
        rows.append(dict(symbol=sym, trades_per_day=int(g.n_trades_raw.mean()), quotes_per_day=int(g.n_quotes_raw.mean()),
                         msgs_per_sec_mean=round((g.n_trades_raw.mean() + g.n_quotes_raw.mean()) / 23400, 1),
                         msgs_per_sec_p99=round(np.mean([p[0] for p in peaks]), 0) if peaks else None,
                         msgs_per_sec_max=round(np.mean([p[1] for p in peaks]), 0) if peaks else None,
                         spread_bps_median=round(float(np.mean(spr)), 2) if spr else None,
                         disk_mb=round(sum(f.stat().st_size for f in (L.SEC / sym).glob("*.parquet")) / 1e6, 1)))
    r = pd.DataFrame(rows).sort_values("msgs_per_sec_mean", ascending=False)
    r.to_csv(HERE / "feasibility.csv", index=False)
    print(r.to_string(index=False))
    print("TOTAL msgs/s mean", r.msgs_per_sec_mean.sum(), "sum of per-symbol p99", r.msgs_per_sec_p99.sum(),
          "raw trades", int(m.n_trades_raw.sum()), "raw quotes", int(m.n_quotes_raw.sum()), "symbol-days", len(m))


if __name__ == "__main__":
    main()
