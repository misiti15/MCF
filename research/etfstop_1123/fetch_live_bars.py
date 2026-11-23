"""Fetch SIP 1-minute RTH bars (read-only market-data GET via mcf.data.priors) for every live NM-ETF-family day,
for the family's traded symbols + SPY, so the live replay uses real minute bars instead of interpolated marks.
Usage: python fetch_live_bars.py CHECKOUT live.parquet OUTDIR.  Educational only - not financial advice."""
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
CK, LIVE, OUT = sys.argv[1], sys.argv[2], Path(sys.argv[3])
sys.path.insert(0, CK)
from mcf.data.bars import normalize, rth
from mcf.data.priors import _bars, _client
FAM = ["NM-ETF-late-dip-di-long", "NM-ETF-late-dip-di-long-WB1", "NM-ETF-late-dip-di-long-WB4", "ULT-22-wb4-wide-etf-long"]
t = pd.read_parquet(LIVE)
t = t[t.strategy.isin(FAM)]
dc, parts = _client(), []
for D, g in t.groupby("date"):
    syms = sorted(set(g.symbol) | {"SPY"})
    day = pd.Timestamp(D).date()
    a = datetime.combine(day, datetime.min.time()) + timedelta(hours=13)
    raw = _bars(dc, syms, a, a + timedelta(hours=8), 1, "sip")
    for s, x in raw.groupby(level=0):
        x = rth(normalize(x.droplevel(0)))
        x = x[x.index.date == day][["open", "high", "low", "close", "volume"]].copy()
        x["symbol"], x["date"] = s, D
        parts.append(x)
    print(D, len(syms))
B = pd.concat(parts)
B.index.name = "ts"
B.reset_index().to_parquet(OUT / "livebars.parquet", index=False)
print(B.shape)
