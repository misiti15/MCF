"""Point-in-time SPY / QQQ context per (date, 5-min bar tod) from 1-min SIP bars (data/cache_hist/1Min). Decision time
= the frame tod, which is the 5-min bar CLOSE time (verified: matches lib.load_context qqq_fo to 1e-8). Locked-block rows (2024-11-01..2025-02-28) are dropped on load and never used.
Columns per index X in {q, s}: X_r30, X_r60 (% move over the last 30 / 60 min, 09:30 open if earlier), X_fo (% from the
09:30 open), X_dhi / X_dlo (% distance of the close below the session high / above the session low so far).
Writes <scratch>/idx.parquet. Usage: python index_ctx.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
S = Path(sys.argv[1])
LOCK = ("2024-11-01", "2025-02-28")
TZ = "America/New_York"


def one(sym, k):
    b = pd.read_parquet(ROOT / "data/cache_hist/1Min" / f"{sym}.parquet", columns=["open", "high", "low", "close"])
    ix = pd.to_datetime(b.index)
    ix = ix.tz_convert(TZ) if ix.tz is not None else ix.tz_localize(TZ)
    b.index = ix
    d = ix.strftime("%Y-%m-%d")
    b = b[~((d >= LOCK[0]) & (d <= LOCK[1]))]
    b = b[(b.index.hour * 60 + b.index.minute >= 570) & (b.index.hour * 60 + b.index.minute < 960)]
    out = []
    for day, g in b.groupby(b.index.strftime("%Y-%m-%d")):
        mins = g.index.hour * 60 + g.index.minute
        # minute m's bar closes at m+1; series of close by "close minute" (1-min bar starting m-1 closes at m)
        close = pd.Series(g.close.to_numpy(), index=mins + 1)
        grid = np.arange(571, 961)
        c = close.reindex(grid).ffill()
        o = float(g.open.iloc[0]) if mins[0] == 570 else np.nan
        hi = pd.Series(g.high.to_numpy(), index=mins + 1).reindex(grid).cummax().ffill()
        lo = pd.Series(g.low.to_numpy(), index=mins + 1).reindex(grid).cummin().ffill()
        tods = np.arange(950, 1505, 5)
        tods = tods[(tods % 100) < 60]
        dm = (tods // 100) * 60 + tods % 100              # decision minute: frame tod is the bar CLOSE time (checked vs load_context)
        cv = c.reindex(dm).to_numpy()
        def ref(L):
            rm = dm - L
            return np.where(rm <= 570, o, c.reindex(np.maximum(rm, 571)).to_numpy())
        out.append(pd.DataFrame({"date": day, "tod": tods,
                                 f"{k}_r30": (cv / ref(30) - 1) * 100, f"{k}_r60": (cv / ref(60) - 1) * 100,
                                 f"{k}_fo": (cv / o - 1) * 100,
                                 f"{k}_dhi": (hi.reindex(dm).to_numpy() / cv - 1) * 100,
                                 f"{k}_dlo": (cv / lo.reindex(dm).to_numpy() - 1) * 100}))
    return pd.concat(out, ignore_index=True)


if __name__ == "__main__":
    X = one("QQQ", "q").merge(one("SPY", "s"), on=["date", "tod"], how="outer")
    assert not ((X.date >= LOCK[0]) & (X.date <= LOCK[1])).any()
    X.to_parquet(S / "idx.parquet", index=False)
    print(X.shape, X.date.min(), X.date.max()); print(X.describe().round(3).to_string())
