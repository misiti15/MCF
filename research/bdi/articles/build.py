"""Build the article-indicator columns for the setup-lab frame (train+valid dates only), live-parity history.
Reads data/cache/1Min with a parquet filter timestamp < 2026-09-16 (later rows are never loaded).
Output: research/bdi/articles/data/feat.parquet keyed by symbol, date, tod (not in git). Educational only."""
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from features import article_features  # noqa: E402

CACHE = Path("data/cache/1Min")
CUT = pd.Timestamp("2026-09-16", tz="America/New_York")
FIRST = pd.Timestamp("2026-06-30").date()
OUT = Path("research/bdi/articles/data")


def one(path):
    try:
        m = pd.read_parquet(path, filters=[("timestamp", "<", CUT)])
    except Exception:
        return None
    m = m[m.index < CUT]
    m = m.between_time("09:30", "15:59")
    if len(m) < 2000:
        return None
    d5 = m.resample("5min", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna(subset=["open"])
    daily = m.groupby(m.index.date).agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
    days = list(daily.index)
    dd = np.array(d5.index.date)
    out = []
    for i, d in enumerate(days):
        if d < FIRST or i == 0:
            continue
        a = np.searchsorted(dd, d)
        b = np.searchsorted(dd, d, side="right")
        hist = d5.iloc[max(0, a - 40): b]
        pr = daily.iloc[i - 1]
        f = article_features(hist, (pr.high, pr.low, pr.close), daily.close.iloc[:i].to_numpy())
        f = f.iloc[-(b - a):]
        end = f.index + pd.Timedelta(minutes=5)
        f["tod"] = end.hour * 100 + end.minute
        f = f[(f.tod >= 950) & (f.tod <= 1500)]
        f["date"] = d
        out.append(f)
    if not out:
        return None
    x = pd.concat(out).reset_index(drop=True)
    x["symbol"] = path.stem
    num = [k for k in x.columns if k not in ("symbol", "date", "tod")]
    return x.astype({k: "float32" for k in num})


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(CACHE.glob("*.parquet"))
    parts = []
    with Pool(4) as p:
        for n, r in enumerate(p.imap_unordered(one, files, chunksize=4)):
            if r is not None:
                parts.append(r)
            if n % 100 == 0:
                print(n, len(files), flush=True)
    x = pd.concat(parts, ignore_index=True)
    x["tod"] = x["tod"].astype("int16")
    x.to_parquet(OUT / "feat.parquet", index=False)
    print("rows", len(x), "symbols", x.symbol.nunique(), "dates", x.date.min(), x.date.max())
