"""Lab frames for the LIVE period 2026-10-06..11-02 from 1-minute SIP bars (data/replay/1Min through 10-26, plus the
read-only fetch in scratch for 10-27..11-02), with the SAME pipeline as research/history2y/build_frames.py
(resample 5min -> mcf.research.setup_lab.build, adv20 from build_frames.daily_table). Warm-up from 2026-09-08.
Universe = the replay store's 1,226 names (not the full live universe). Usage: python build_live_frames.py <scratch>
-> <scratch>/live_frames.parquet. Educational only - not financial advice."""
import sys
from multiprocessing import get_context
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path[:0] = [str(ROOT), str(ROOT / "research/history2y")]
from mcf.data.bars import resample
from mcf.research.setup_lab import build
from build_frames import daily_table

S = Path(sys.argv[1])
KEEP = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "heat", "buyPressure", "rsi", "rsi5", "gap",
        "sma20_dist_pct", "sma20_slope_pct", "bear_div", "fromOpen", "vwapDistPct", "dist_hod_atr", "dist_lod_atr",
        "dist_pdh_atr", "dist_pdl_atr", "volumeRatio", "vol_climax", "emaDiff", "sma50_dist_pct", "macdPct", "flow3"] + \
       [f"{a}_{s}_{g}" for a in ("r", "win") for s in ("long", "short") for g in ("t1s1", "t05s1")]
files = sorted(p for p in (ROOT / "data/replay/1Min").glob("*.parquet") if p.stem >= "2026-09-08") + sorted((S / "bars1").glob("*.parquet"))
B = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)
B["ts"] = pd.DatetimeIndex(B["ts"]).tz_convert("America/New_York")
B = B.drop_duplicates(["symbol", "ts"]).sort_values(["symbol", "ts"])
for c in ("open", "high", "low", "close", "volume"):
    B[c] = B[c].astype("float64")
G = {s: g.drop(columns="symbol").set_index("ts") for s, g in B.groupby("symbol", sort=True)}
del B


def one(s):
    df = G[s]
    dd = daily_table(df, s)
    x = build({s: resample(df, "5min")}, log=lambda *_: None)
    if x is None or not len(x):
        return None
    x = x.reset_index(names="ts").merge(dd[["date", "adv20"]], on="date", how="left")
    x = x[x["date"].astype(str) >= "2026-10-06"]
    return x[[c for c in KEEP if c in x.columns]]


if __name__ == "__main__":
    with get_context("fork").Pool(2) as p:
        out = [x for x in p.imap(one, list(G), chunksize=10) if x is not None and len(x)]
    x = pd.concat(out, ignore_index=True)
    x.to_parquet(S / "live_frames.parquet", compression="zstd", index=False)
    print(x.symbol.nunique(), "symbols", x.date.nunique(), "dates", len(x), "rows", sorted(x.date.unique())[[0, -1]])
