"""SPY/QQQ 1-min bars for the live window (Alpaca GET only). Educational only - not financial advice."""
import sys
from datetime import datetime
import pandas as pd
sys.path.insert(0, sys.argv[1])
from mcf.data.bars import normalize, rth
from mcf.data.priors import _bars, _client
raw = _bars(_client(), ["SPY", "QQQ"], datetime(2026, 10, 1, 13), datetime(2026, 11, 25, 0), 1, "sip")
for s, g in raw.groupby(level=0):
    g = rth(normalize(g.droplevel(0))); g.to_parquet(f"live_{s}.parquet"); print(s, len(g), g.index.min(), g.index.max())
