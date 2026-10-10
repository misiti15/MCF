"""Dense 5-minute bars 09:35..15:55 (bar-close tod) for every lab symbol on the 426 open sessions, from
data/cache_hist/1Min with the history2y pipeline's resample. Locked-block rows (2024-11-01..2025-02-28) are dropped
right after each load, before any computation. Output (git-ignored): data/bars_{C,H,L}.f32 + bars_meta.json.
Educational only - not financial advice."""
import json
import time

import numpy as np
import pandas as pd

from common import DATA, LOCKED, ROOT, TODS, open_dates, symbols, tod_index
from mcf.data.bars import resample
from mcf.data.store import BarStore

DATA.mkdir(exist_ok=True)
syms, dates = symbols(), open_dates()
di = {d: i for i, d in enumerate(dates)}
shape = (len(syms), len(dates), len(TODS))
arr = {k: np.memmap(DATA / f"bars_{k}.f32", dtype=np.float32, mode="w+", shape=shape) for k in ("C", "H", "L")}
for a in arr.values():
    a[:] = np.nan
store = BarStore(ROOT / "data" / "cache_hist")
lo64, hi64 = np.datetime64(LOCKED[0], "us"), np.datetime64(LOCKED[1], "us")
dates64 = np.array([np.datetime64(str(x)) for x in dates], dtype="datetime64[us]")
t0 = time.time()
for j, s in enumerate(syms):
    df = store.load(s)
    if df.empty:
        continue
    day = df.index.tz_localize(None).normalize().to_numpy()
    df = df[~((day >= lo64) & (day <= hi64))]               # locked block dropped before anything else
    day = df.index.tz_localize(None).normalize().to_numpy()
    df = df[np.isin(day, dates64)]
    m = df.index.hour * 60 + df.index.minute
    df = df[(m >= 570) & (m <= 959)]
    if df.empty:
        continue
    b = resample(df, "5min")
    end = b.index + pd.Timedelta(minutes=5)
    tod = np.asarray(end.hour * 100 + end.minute)
    ok = (tod >= 935) & (tod <= 1555)
    b, tod = b[ok], tod[ok]
    dd = np.searchsorted(dates64, b.index.tz_localize(None).normalize().to_numpy())
    bi = tod_index(tod)
    arr["C"][j, dd, bi] = b["close"].to_numpy(np.float32)
    arr["H"][j, dd, bi] = b["high"].to_numpy(np.float32)
    arr["L"][j, dd, bi] = b["low"].to_numpy(np.float32)
    if j % 100 == 0:
        print(j, s, round(time.time() - t0), flush=True)
for a in arr.values():
    a.flush()
(DATA / "bars_meta.json").write_text(json.dumps({"shape": list(shape), "syms": syms, "dates": [str(x) for x in dates]}))
print("done", shape, round(time.time() - t0), flush=True)
