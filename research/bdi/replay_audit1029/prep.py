"""REPS replay audit 2026-10-29: private replay store (the shared data/replay is never written).

Links the shared 1-minute packs / priors into $MCF_REPLAY_STORE, copies daily.parquet, then read-only Alpaca
market-data fetch of the sessions the store lacks (1-minute SIP bars, lab universe) and daily bars up to the last
session, and builds the live-prep priors. Educational only - not financial advice."""
import os
import shutil
import sys
from datetime import timedelta
from pathlib import Path

SRC = Path("/home/user/MCF/data/replay")
DST = Path(os.environ["MCF_REPLAY_STORE"])
for sub in ("1Min", "priors"):
    (DST / sub).mkdir(parents=True, exist_ok=True)
    for f in (SRC / sub).glob("*"):
        t = DST / sub / f.name
        if not t.exists():
            t.symlink_to(f)
for f in ("daily.parquet", "spreads.json"):
    if (SRC / f).exists() and not (DST / f).exists():
        shutil.copy(SRC / f, DST / f)

from mcf.replay import store  # noqa: E402  (reads MCF_REPLAY_STORE)

start, end = sys.argv[1], sys.argv[2]
days = store.sessions(start, end)
have = set(store.available_days())
store.fetch_1min([d for d in days if d not in have])
store.fetch_daily(store._d(end) - timedelta(days=12), end)     # appends / overrides the copied daily file
import pandas as pd  # noqa: E402
daily = pd.read_parquet(DST / "daily.parquet")
cache = {}
for d in days:
    if d in set(store.available_days()):
        p = store.build_priors_for(d, store.symbols(), cache=cache, daily=daily)
        print("priors", d, len(p), flush=True)
print("Educational only - not financial advice.")
