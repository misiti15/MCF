"""shorts_autopsy: Alpaca GET only. Daily bars (SIP, split-adjusted) for every symbol in the non-Graveyard live trades
2026-09-25..11-27, and SPY/QQQ/IWM 1-min bars on the live sessions. Only bar numbers are stored (scratch, deleted after).
Educational only - not financial advice."""
import sys
from datetime import datetime
import pandas as pd
from mcf.data.priors import _bars, _client
OUT = sys.argv[1]
t = pd.read_parquet(f"{OUT}/live.parquet")
t = t[(t.account != "graveyard") & (t.date >= "2026-10-23")]
syms = sorted(set(t.symbol) | {"SPY", "QQQ", "IWM"})
dc = _client()
d = _bars(dc, syms, datetime.fromisoformat("2026-09-20T00:00:00+00:00"), datetime.fromisoformat("2026-11-28T00:00:00+00:00"), None, "sip")
d = d.reset_index(); d.to_parquet(f"{OUT}/daily.parquet"); print("daily", len(d), d.symbol.nunique())
out = []
for day in sorted(t.date.unique()):
    m = _bars(dc, ["SPY", "QQQ", "IWM"], datetime.fromisoformat(day + "T13:00:00+00:00"), datetime.fromisoformat(day + "T21:05:00+00:00"), 1, "sip")
    out.append(m.reset_index())
pd.concat(out).to_parquet(f"{OUT}/idx1m.parquet"); print("idx 1m", sum(len(x) for x in out))
