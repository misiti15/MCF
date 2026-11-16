"""Mechanic GEN-261027-01: read-only SIP GET of 1-minute bars for the lab universe (research/lab_symbols.txt, 1226 names,
the 2-year frames' universe) for the live sessions after the frames end (2026-11-05..11-13). Educational only - not financial advice."""
import sys
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-gen27101")
import pandas as pd
from mcf.replay.store import _fetch_bars, symbols
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-gen27101/"
syms = symbols()
parts = []
for i in range(0, len(syms), 200):
    df = _fetch_bars(syms[i:i + 200], "2026-11-05T14:00:00Z", "2026-11-13T21:05:00Z", "1Min")
    parts.append(df); print(i, len(df), flush=True)
m = pd.concat(parts, ignore_index=True)
m.to_parquet(OUT + "fetch_1m.parquet"); print("done", len(m), m.symbol.nunique())
