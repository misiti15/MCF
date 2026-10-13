"""longs1013 step 0: compact frame table (open history only, adv20 >= $95M) + head/tail bars + prior-day close location.

The rule-19 locked block is never loaded: lib.load_month refuses it, lib.months() lists open months only, the test_b
head/tail file was built with the locked block filtered at read. Output (git-ignored): data/frames.parquet,
data/day.parquet. Educational only - not financial advice.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
sys.path.insert(0, str(ROOT))
import lib  # noqa: E402

OUT = HERE / "data"
GEO = ("t1s1", "t05s1", "t1s05")
COLS = ["symbol", "date", "tod", "close", "high", "low", "fromOpen", "gap", "vwapDistPct", "dist_lod_atr", "atr_d",
        "adv20", "heat", "buyPressure", "rsi", "rsi5"] + [f"{k}_{s}_{g}" for k in ("r", "win") for s in ("long", "short") for g in GEO]


def main():
    OUT.mkdir(exist_ok=True)
    parts = []
    for m in lib.months():
        assert m not in lib.LOCKED_MONTHS
        f = lib.load_month(m, COLS)
        keep = (f.adv20 >= 95e6) & (f.atr_d > 0)
        f = f[keep | (f.symbol == "SPY")].copy()
        for c in f.columns:
            if f[c].dtype == np.float64:
                f[c] = f[c].astype("float32")
        f["symbol"] = f["symbol"].astype(str)
        parts.append(f)
        print(m, len(f), flush=True)
    f = pd.concat(parts, ignore_index=True)
    f["date"] = pd.to_datetime(f["date"])
    s = f["date"].dt.strftime("%Y-%m-%d")
    assert not ((s >= lib.LOCKED[0]) & (s <= lib.LOCKED[1])).any()
    f = f.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)
    f.to_parquet(OUT / "frames.parquet", index=False)

    # day table: head bars (09:35..09:50), 15:55 close, prior-day close location
    h = pd.read_parquet(ROOT / "research" / "bdi" / "cwt" / "test_b" / "data" / "headtail.parquet")
    h["symbol"] = h["symbol"].astype(str)
    h["date"] = pd.to_datetime(h["date"])
    piv = h[h.tod.isin([935, 940, 945, 950, 1555])].pivot_table(index=["symbol", "date"], columns="tod",
                                                                 values=["h", "l", "c", "vwap"])
    piv.columns = [f"{a}{b}" for a, b in piv.columns]
    day = piv.reset_index()
    d = lib.daily()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values(["symbol", "date"])
    g = d.groupby("symbol")
    rng = (d["high"] - d["low"]).replace(0, np.nan)
    d["cl"] = (d["close"] - d["low"]) / rng
    d["pcl"] = g["cl"].shift(1)
    d["pdate"] = g["date"].shift(1)
    d.loc[(d["date"] - d["pdate"]).dt.days > 5, "pcl"] = np.nan        # prior session across the dropped block
    day = day.merge(d[["symbol", "date", "pcl"]], on=["symbol", "date"], how="left")
    day.to_parquet(OUT / "day.parquet", index=False)
    print("frames", len(f), "days", len(day))


if __name__ == "__main__":
    main()
