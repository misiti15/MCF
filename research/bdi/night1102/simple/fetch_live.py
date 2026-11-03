"""Read-only Alpaca market-data GET: 1-minute SIP RTH bars for the replay universe on sessions missing from
data/replay (10-27..11-02) into scratch. Usage: python fetch_live.py <scratch>. Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.replay import store
S = Path(sys.argv[1]) / "bars1"; S.mkdir(parents=True, exist_ok=True)
syms = store.symbols()
for d in ["2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02"]:
    p = S / f"{d}.parquet"
    if p.exists():
        continue
    df = store._fetch_bars(syms, f"{d}T13:00:00Z", f"{d}T21:00:00Z", "1Min").set_index("ts")
    df.index = df.index.tz_convert("America/New_York")
    df = df[(df.index.time >= pd.Timestamp("09:30").time()) & (df.index.time < pd.Timestamp("16:00").time())]
    df.reset_index().to_parquet(p, compression="zstd", index=False)
    print(d, df.symbol.nunique(), len(df), flush=True)
