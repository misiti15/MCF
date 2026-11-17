"""FREQ: read-only SIP GET of 1-minute RTH bars for the symbols the old 1,226-symbol cache lacks (24 of the parent's own ETFs
+ the wider sets), 2024-09-16..2024-10-31 and 2025-03-01..2026-10-16. The locked block 2024-11-01..2025-02-28 is NEVER
fetched. Written as a scratch BarStore (same format as data/cache_hist). Educational only - not financial advice."""
import json, glob, os, sys, pandas as pd
from mcf.replay.store import _fetch_bars
from mcf.data.bars import TZ
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/etffreq/"
sets = json.load(open(S + "sets.json"))
have = {os.path.basename(p)[:-8] for p in glob.glob("/home/user/MCF/data/cache_hist/1Min/*.parquet")}
want = sorted({s for k, v in sets.items() if k != "VIX" for s in v} - have)
os.makedirs(S + "cache/1Min", exist_ok=True)
todo = [s for s in want if not os.path.exists(S + f"cache/1Min/{s}.parquet")]
print(len(want), "missing from cache;", len(todo), "to fetch", flush=True)
RANGES = [("2024-09-16T13:00:00Z", "2024-11-01T04:00:00Z"), ("2025-03-01T05:00:00Z", "2026-10-17T00:00:00Z")]
for i in range(0, len(todo), 10):
    grp = todo[i:i + 10]
    parts = [_fetch_bars(grp, a, b, "1Min", batch=10) for a, b in RANGES]
    df = pd.concat(parts)
    df = df.set_index(pd.DatetimeIndex(df.ts).tz_convert(TZ)).drop(columns="ts")
    t = df.index
    df = df[((t.hour > 9) | ((t.hour == 9) & (t.minute >= 30))) & (t.hour < 16)]
    ds_ = df.index.strftime("%Y-%m-%d")
    assert not ((ds_ >= "2024-11-01") & (ds_ <= "2025-02-28")).any()
    for s in grp:
        g = df[df.symbol == s][["open", "high", "low", "close", "volume"]].astype(float).sort_index()
        g = g[~g.index.duplicated()]
        g.to_parquet(S + f"cache/1Min/{s}.parquet")
    print(i + len(grp), "done", flush=True)
