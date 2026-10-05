"""Is the FREE data good enough? Compare IEX vs SIP (consolidated) on recent history.

For a sample of universe symbols over N recent sessions, using 1-minute bars from both feeds:
  * price agreement: median |IEX close - SIP close| per bar, in bps
  * opening relative volume (first 5 min vs that symbol's prior 10-day average at the same time),
    computed separately inside each feed -> Spearman rank correlation and top-20 overlap per day.
If rank correlation is high and top-20 overlap is large, the free IEX scan picks the same
'stocks in play' as the paid SIP feed, and the $99 plan can wait.

Usage: python scripts/validate_iex_proxy.py [--symbols 300] [--days 15]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.config import load_dotenv  # noqa: E402
from mcf.data.alpaca_data import fetch_bars  # noqa: E402
from mcf.data.universe import load_universe  # noqa: E402


def opening_rvol(bars: dict[str, pd.DataFrame], minutes=5, lookback=10) -> pd.DataFrame:
    out = {}
    for sym, df in bars.items():
        t = df.index
        first = df[(t.hour == 9) & (t.minute >= 30) & (t.minute < 30 + minutes)]
        v = first.groupby(first.index.date)["volume"].sum()
        out[sym] = v / v.rolling(lookback, min_periods=5).mean().shift(1)
    return pd.DataFrame(out)  # rows = dates, cols = symbols


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", type=int, default=300)
    ap.add_argument("--days", type=int, default=15)
    a = ap.parse_args()
    load_dotenv()
    uni = load_universe()
    syms = uni.sample(min(a.symbols, len(uni)), random_state=1)["symbol"].tolist()
    end = datetime.now(timezone.utc) - timedelta(minutes=20)
    start = end - timedelta(days=(a.days + 12) * 1.5)
    res = {}
    for feed in ("iex", "sip"):
        bars = {}
        for i in range(0, len(syms), 50):
            bars.update(fetch_bars(syms[i:i + 50], start, end, feed=feed))
        res[feed] = bars
    common = sorted(set(res["iex"]) & set(res["sip"]))
    px = []
    for s in common:
        j = res["iex"][s][["close"]].join(res["sip"][s][["close"]], lsuffix="_iex", rsuffix="_sip", how="inner")
        px.append(((j.close_iex / j.close_sip - 1).abs() * 1e4).median())
    ri, rs = opening_rvol({s: res["iex"][s] for s in common}), opening_rvol({s: res["sip"][s] for s in common})
    days = ri.dropna(how="all").index.intersection(rs.dropna(how="all").index)[-a.days:]
    corr, overlap = [], []
    for d in days:
        x = pd.concat([ri.loc[d], rs.loc[d]], axis=1, keys=["iex", "sip"]).dropna()
        if len(x) < 30:
            continue
        corr.append(x.rank().corr().iloc[0, 1])
        overlap.append(len(set(x.iex.nlargest(20).index) & set(x.sip.nlargest(20).index)) / 20)
    cover = np.mean([len(res["iex"][s]) / max(len(res["sip"][s]), 1) for s in common])
    print(f"symbols compared: {len(common)}; sessions: {len(corr)}")
    print(f"IEX bars present vs SIP minutes: {cover:.0%}  (missing IEX minutes = no IEX trade that minute)")
    print(f"price: median |IEX-SIP| close difference {np.median(px):.1f} bps")
    print(f"opening rel. volume: Spearman rank corr IEX vs SIP mean {np.mean(corr):.2f} (min {np.min(corr):.2f})")
    print(f"top-20 'in play' overlap IEX vs SIP: mean {np.mean(overlap):.0%}")


if __name__ == "__main__":
    main()
