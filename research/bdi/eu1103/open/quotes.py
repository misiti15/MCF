"""eu1103/open (1): SIP NBBO spreads by minute of the session from Alpaca historical quotes (data the live runner has).
Sample: the 60 symbols with the most live trades 10-20..11-02 (all accounts), 8 recent sessions, a 5-second window at
each mark. Spread in bps of the mid and as a fraction of the live stop distance (median live risk per symbol).
Ratio = spread at the mark / the same symbol-day's median spread at 11:00-14:00 marks (the cost multiplier check).
    python quotes.py <journal dir>        (needs ALPACA_API_KEY / ALPACA_SECRET_KEY in the environment; never printed)
Educational only - not financial advice."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockQuotesRequest

J = Path(sys.argv[1])
t = pd.read_parquet(J / "live_trades.parquet")
t = t[(t.date >= "2026-10-20")]
risk = t.groupby("symbol").risk.median()
syms = t.symbol.value_counts().head(60).index.tolist()
days = ["2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02"]
MARKS = ["09:35", "09:40", "09:45", "09:50", "09:55", "10:00", "10:15", "10:30", "11:00", "12:00", "14:00"]
c = StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
rows = []
for d in days:
    for mk in MARKS:
        a = pd.Timestamp(f"{d} {mk}:20", tz="America/New_York")
        req = StockQuotesRequest(symbol_or_symbols=syms, start=a.to_pydatetime(),
                                 end=(a + pd.Timedelta(seconds=5)).to_pydatetime(), feed=DataFeed.SIP)
        try:
            q = c.get_stock_quotes(req).df
        except Exception as e:
            print("err", d, mk, type(e).__name__, flush=True)
            continue
        if q.empty:
            continue
        q = q.reset_index()
        q = q[(q.bid_price > 0) & (q.ask_price > q.bid_price)]
        mid = (q.bid_price + q.ask_price) / 2
        q["bps"] = (q.ask_price - q.bid_price) / mid * 1e4
        q["usd"] = q.ask_price - q.bid_price
        g = q.groupby("symbol").agg(bps=("bps", "median"), usd=("usd", "median"), n=("bps", "size")).reset_index()
        g["day"], g["mark"] = d, mk
        rows.append(g)
    print(d, "done", flush=True)
x = pd.concat(rows, ignore_index=True)
x["spread_R"] = x.usd / x.symbol.map(risk)
mid = x[x.mark.isin(["11:00", "12:00", "14:00"])].groupby(["symbol", "day"]).bps.median().rename("bps_mid")
x = x.join(mid, on=["symbol", "day"])
x["ratio"] = x.bps / x.bps_mid
print("Educational only - not financial advice.")
print(f"symbols {x.symbol.nunique()}, sessions {x.day.nunique()}, symbol-day-marks {len(x)}")
out = x.groupby("mark").agg(n=("bps", "size"), med_bps=("bps", "median"), p75_bps=("bps", lambda s: s.quantile(.75)),
                            med_spread_R=("spread_R", "median"), p75_spread_R=("spread_R", lambda s: s.quantile(.75)),
                            med_ratio_vs_midday=("ratio", "median"), mean_ratio=("ratio", "mean"),
                            share_gt_25pct_stop=("spread_R", lambda s: (s > 0.25).mean()))
print(out.round(3).to_string())
x.to_csv(J / "quotes_sample.csv", index=False)
