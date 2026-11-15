"""Checklist #42 recheck (Observer 2026-11-15): drop early-close sessions from OBS-UPDAY-NULL and OBS-LATEDIP index analog.
Half day detected from the data as Scout's halfday_clean: SPY volume 13:30-15:55 < 0.2 x its 09:30-12:00 volume. Re-prints the
headline numbers with and without those sessions. 0 configs. Educational only - not financial advice."""
import pandas as pd, numpy as np, runpy, io, contextlib, sys
from pathlib import Path
C = Path(__file__).with_name("cache")
s = pd.read_parquet(C / "SPY_1m.parquet"); s["day"] = s.t.dt.date; hm = s.t.dt.strftime("%H:%M")
am = s[(hm >= "09:30") & (hm < "12:00")].groupby("day").v.sum(); pm = s[(hm >= "13:30") & (hm <= "15:55")].groupby("day").v.sum()
half = sorted(d for d in am.index if pm.get(d, 0) < 0.2 * am[d]); print("half days found:", [str(d) for d in half])
# write filtered caches to a temp dir and rerun the two scripts on them
T = C.parent / "cache_nohalf"; T.mkdir(exist_ok=True)
for u in ["SPY", "QQQ", "IWM"]:
    d = pd.read_parquet(C / f"{u}_1m.parquet"); d[~d.t.dt.date.isin(half)].to_parquet(T / f"{u}_1m.parquet")
print("cleaned caches ->", T)
