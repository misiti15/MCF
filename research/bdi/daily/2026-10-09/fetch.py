"""Read-only SIP 1-minute bars (Alpaca market data only, never trading endpoints) for the 2026-10-09 autopsy.
(1) traded symbols of both accounts + SPY/QQQ/IWM, 2026-08-10..2026-10-09 -> data/cache/bdi1009/<SYM>.parquet
(2) 2026-10-09 only for the lab universe (research/lab_symbols.txt) -> data/cache/bdi1009/universe_1009.parquet
    (for the market-context / breadth signal on the day). Educational only - not financial advice."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from mcf.data.alpaca_data import _client, fetch_bars  # noqa: E402

OUT = ROOT / "data" / "cache" / "bdi1009"
OUT.mkdir(parents=True, exist_ok=True)
syms = set()
for f in ("primary", "testing"):
    syms |= set(pd.read_csv(ROOT / "data" / "bdi1009" / f"{f}.csv").symbol)
syms |= {"SPY", "QQQ", "IWM"}
syms = sorted(syms)
cl = _client()
a, b = datetime(2026, 8, 10, tzinfo=timezone.utc), datetime(2026, 10, 9, 21, tzinfo=timezone.utc)
for i in range(0, len(syms), 50):
    for s, g in fetch_bars(syms[i:i + 50], a, b, feed="sip", client=cl).items():
        g.to_parquet(OUT / f"{s}.parquet")
print("traded", len(syms), len(list(OUT.glob("*.parquet"))))
uni = [s.strip() for s in (ROOT / "research" / "lab_symbols.txt").read_text().split() if s.strip()]
a1 = datetime(2026, 10, 8, 4, tzinfo=timezone.utc)
parts = []
for i in range(0, len(uni), 200):
    for s, g in fetch_bars(uni[i:i + 200], a1, b, feed="sip", client=cl).items():
        g = g.copy()
        g["symbol"] = s
        parts.append(g)
U = pd.concat(parts)
U.to_parquet(OUT / "universe_1009.parquet")
print("universe symbols", U.symbol.nunique(), len(U))
