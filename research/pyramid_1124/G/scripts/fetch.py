"""SIP 1-min bars for live signal symbol-days of GEN-261027-01 / L3-fromopen (Alpaca GET only). Educational only."""
import sys
from datetime import datetime, timedelta
import pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX)
from mcf.data.bars import normalize, rth
from mcf.data.priors import _bars, _client
S = pd.read_parquet("live_sig.parquet")
S = S[S.symbol.notna()]
dc = _client(); out = []
for d, g in S.groupby("day"):
    syms = sorted(g.symbol.unique())
    a = datetime.fromisoformat(d) + timedelta(hours=13); b = a + timedelta(hours=10)
    raw = _bars(dc, syms, a, b, 1, "sip")
    if raw.empty: print(d, "empty"); continue
    for s, x in raw.groupby(level=0):
        x = rth(normalize(x.droplevel(0)))
        x = x[["open", "high", "low", "close", "volume"]].astype("float32")
        x["symbol"] = s
        out.append(x)
    print(d, len(syms), flush=True)
T = pd.concat(out); T.index.name = "ts"
T.to_parquet("live_bars.parquet"); print(T.shape)
