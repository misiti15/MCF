"""Move Hunt input: SIP 5-minute RTH bars 2026-09-22..<day> for every universe symbol with ADV >= $60M (Alpaca market-data
GET only). Usage: python fetch5.py <scratch> <day>  -> <scratch>/mh/<day>/bars5.parquet. Educational only - not financial advice."""
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.bars import normalize, rth
from mcf.data.priors import _bars, _client

S, D = Path(sys.argv[1]), sys.argv[2]
uni = pd.read_csv(S / "cov" / "p" / "universe.csv")
syms = sorted(set(uni.loc[uni.adv >= 60e6, "symbol"].astype(str)) | {"SPY", "QQQ", "IWM"})
out = S / "mh" / D; out.mkdir(parents=True, exist_ok=True)
dc = _client()
a = datetime(2026, 9, 22, 13); b = datetime.combine(pd.Timestamp(D).date(), datetime.min.time()) + timedelta(hours=21)
raw = _bars(dc, syms, a, b, 5, "sip")
fr = []
for s, g in raw.groupby(level=0):
    g = rth(normalize(g.droplevel(0)))
    if len(g):
        fr.append(g.assign(symbol=s))
x = pd.concat(fr); x.to_parquet(out / "bars5.parquet")
print(len(syms), "requested,", x.symbol.nunique(), "with bars,", len(x), "rows", x.index.min(), x.index.max())
