"""Market breadth per minute for 2026-10-09 and the 20 prior sessions (lab universe, SIP, regular session).
Prior sessions from the local bar cache data/cache/1Min (ends 10-07) + data/universe_1008.parquet; 10-09 from
data/universe_1009.parquet. Per minute (bar label t, known at t+1): share of symbols with close above session VWAP,
above the session open, making a new 30-minute high (high >= max of prior 30 highs) / new 30-minute low.
-> data/breadth.parquet. Educational only - not financial advice."""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "data"


def per_symbol(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_index()
    day = g.index.date
    tp = (g.high + g.low + g.close) / 3
    cv = g.volume.groupby(day).cumsum().replace(0, np.nan)
    vwap = (tp * g.volume).groupby(day).cumsum() / cv
    op = g.open.groupby(day).transform("first")
    ph = g.high.groupby(day).transform(lambda s: s.shift(1).rolling(30, min_periods=10).max())
    pl = g.low.groupby(day).transform(lambda s: s.shift(1).rolling(30, min_periods=10).min())
    return pd.DataFrame({"above_vwap": (g.close > vwap).astype(float), "above_open": (g.close > op).astype(float),
                         "new30h": (g.high > ph).astype(float).where(ph.notna()),
                         "new30l": (g.low < pl).astype(float).where(pl.notna())}, index=g.index)


def main():
    uni = [s.strip() for s in (ROOT / "research" / "lab_symbols.txt").read_text().split() if s.strip()]
    cache = ROOT / "data" / "cache" / "1Min"
    spy = pd.read_parquet(cache / "SPY.parquet")
    days = sorted(set(spy.index.date))
    keep = set(days[-19:])  # 19 cached sessions to 10-07, + 10-08 + 10-09
    acc = None
    extra = pd.concat([pd.read_parquet(OUT / "universe_1008.parquet"), pd.read_parquet(OUT / "universe_1009.parquet")])
    extra = extra.set_index("timestamp")
    for n, s in enumerate(uni):
        parts = []
        p = cache / f"{s}.parquet"
        if p.exists():
            d = pd.read_parquet(p, columns=["open", "high", "low", "close", "volume"])
            parts.append(d[np.isin(d.index.date, list(keep))])
        e = extra[extra.symbol == s][["open", "high", "low", "close", "volume"]]
        parts.append(e.between_time("09:30", "15:59"))
        g = pd.concat(parts)
        if len(g) < 100:
            continue
        f = per_symbol(g[~g.index.duplicated()])
        f["n"] = 1.0
        acc = f.fillna(0).assign(nh=f.new30h.notna().astype(float)) if acc is None else acc.add(
            f.fillna(0).assign(nh=f.new30h.notna().astype(float)), fill_value=0)
        if n % 200 == 0:
            print(n, flush=True)
    b = pd.DataFrame({"br_above_vwap": acc.above_vwap / acc.n, "br_above_open": acc.above_open / acc.n,
                      "br_new30h": acc.new30h / acc.nh, "br_new30l": acc.new30l / acc.nh, "br_n": acc.n})
    b.to_parquet(OUT / "breadth.parquet")
    print(b.describe().T)


if __name__ == "__main__":
    main()
