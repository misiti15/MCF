"""top20 (2026-11-09): live compass state per session, for the "R by compass state at entry" split.

Recorded live rows (mcf-data-compass, compass/<date>.csv) are used where they exist (11-06, 11-09 onward). Every other
live session is BACKFILLED with mcf.report.compass_live.compute() itself (same point-in-time logic, same 200-name
breadth universe): 1-minute bars from the 2-year cache data/cache_hist/1Min (to 2026-11-04) and, for later days without
a recorded file, read-only Alpaca market-data GETs (mcf.replay.store._fetch_bars via compass_live.fetch).
On days with a recorded file the backfill is also computed and compared (agreement printed), as a check.

Usage: python compass_backfill.py <scratch>  (scratch has spy_1m.parquet from fetch_live.py) -> <scratch>/compass.parquet
Display / research only - not a trading signal. Educational only - not financial advice."""
import io
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from mcf.report import compass_live as cl  # noqa: E402

S = Path(sys.argv[1])
NY = cl.NY
names = cl.universe()
syms = list(dict.fromkeys(["SPY", "QQQ", "IWM"] + names))
dates = sorted(pd.read_parquet(S / "trades.parquet").date.unique())
CACHE = {}


def cache_bars(day):
    out = {}
    for s in syms:
        if s not in CACHE:
            p = ROOT / "data/cache_hist/1Min" / f"{s}.parquet"
            CACHE[s] = pd.read_parquet(p).loc["2026-10-01":] if p.exists() else None
        x = CACHE[s]
        if x is not None:
            g = x.loc[day:day]
            if len(g):
                out[s] = g[["open", "high", "low", "close", "volume"]].astype(float)
    return out


recorded = {}
for p in subprocess.check_output(["git", "-C", str(ROOT), "ls-tree", "--name-only", f"origin/{cl.BRANCH}", "compass/"]).decode().split():
    if p.endswith(".csv"):
        recorded[p[8:18]] = pd.read_csv(io.BytesIO(subprocess.check_output(["git", "-C", str(ROOT), "show", f"origin/{cl.BRANCH}:{p}"])))
rows = []
for d in dates:
    end = pd.Timestamp(f"{d} 16:30", tz=NY)
    bars = cache_bars(d) if d <= "2026-11-04" else cl.fetch(d, syms, end, log=lambda *_: None)
    bf = pd.DataFrame(cl.compute(bars, d, end, names)) if "SPY" in bars else pd.DataFrame()
    if d in recorded:
        rec = recorded[d].copy()
        if len(bf):
            m = rec.merge(bf[["T", "w60", "c30", "checkpoint"]], on="T", suffixes=("", "_bf"))
            print(d, "recorded vs backfill agreement: w60", round((m.w60 == m.w60_bf).mean(), 3),
                  "checkpoint", round((m.checkpoint.fillna("") == m.checkpoint_bf.fillna("")).mean(), 3), "marks", len(m))
        rec["source"] = "recorded"
        rows.append(rec[["date", "T", "w60", "c30", "checkpoint", "gate1_state", "source"]])
    elif len(bf):
        bf["source"] = "backfill"
        rows.append(bf[["date", "T", "w60", "c30", "checkpoint", "gate1_state", "source"]])
    else:
        print(d, "no bars")
C = pd.concat(rows, ignore_index=True)
C.to_parquet(S / "compass.parquet")
print(C.groupby("source").date.nunique().to_dict(), "sessions;", len(C), "marks")
print(C[C["T"] == "10:00"].set_index("date").w60.value_counts().to_dict())
