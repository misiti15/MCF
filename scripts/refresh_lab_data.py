"""Bring the research bar cache (data/cache, 1-minute SIP, research/lab_symbols.txt) up to the last full session.

Downloads only the missing days per symbol (BarStore.save merges). Used by the weekly backlog job so every
backlog idea is re-tested on all data collected so far. Educational only — not financial advice.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mcf.data.priors import _bars, _client          # noqa: E402
from mcf.data.bars import normalize, rth             # noqa: E402
from mcf.data.store import BarStore                  # noqa: E402

START = datetime(2026, 6, 15)
store = BarStore("data/cache")
syms = Path("research/lab_symbols.txt").read_text().split()
end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)   # through yesterday
groups: dict[datetime, list[str]] = {}
for s in syms:
    p = store.path(s)
    if p.exists():
        import pandas as pd
        last = pd.read_parquet(p, columns=["close"]).index.max()
        start = datetime(last.year, last.month, last.day) + timedelta(days=1)
    else:
        start = START
    if start < end:
        groups.setdefault(start, []).append(s)
dc = _client()
for start, ss in sorted(groups.items()):
    for i in range(0, len(ss), 50):
        df = _bars(dc, ss[i:i + 50], start, end, 1, "sip", batch=25, workers=8)
        if len(df):
            for s, g in df.groupby(level=0):
                store.save(s, rth(normalize(g.droplevel(0))))
    print(f"{start:%F}: {len(ss)} symbols refreshed", flush=True)
print("cache up to date", flush=True)
