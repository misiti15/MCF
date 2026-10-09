"""Stack study step 1: load the open 2-year frames (locked block refused by lib), keep adv20 >= 95M and 09:50-15:00,
derive the live-parity building blocks (NOTES.md 1.2) and production-cost R per side/exit. Output (git-ignored):
data/base.npz. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402
from mcf.research.gates import prod_r  # noqa: E402

COLS = ["close", "rsi", "rsi5", "emaDiff", "macdPct", "volumeRatio", "vwapDistPct", "buyPressure", "gap", "fromOpen",
        "tod", "atr_d", "dist_pdh_atr", "dist_pdl_atr", "dist_hod_atr", "dist_lod_atr", "sma20_dist_pct",
        "sma50_dist_pct", "sma20_slope_pct", "flow3", "symbol", "date", "adv20"]
OUTC = [f"{k}_{s}_{g}" for s in ("long", "short") for g in ("t1s1", "t05s1", "t1s05") for k in ("r", "win")]
MIN_ADV = 95e6


def main():
    parts = []
    for m in lib.months():
        df = lib.load_month(m, COLS + OUTC)
        df = df[(df.tod >= 950) & (df.tod <= 1500)]
        keep = df["adv20"].to_numpy(float) >= MIN_ADV
        df = df[keep].reset_index(drop=True)
        out = {}
        for g in ("t1s1", "t05s1", "t1s05"):
            for s in ("long", "short"):
                out[f"p_{s}_{g}"] = prod_r(df[f"r_{s}_{g}"], df[f"win_{s}_{g}"], df["close"], df["atr_d"], g).astype("float32")
        df = df.drop(columns=OUTC)
        for k, v in out.items():
            df[k] = v
        parts.append(df)
        print(m, len(df), flush=True)
    df = pd.concat(parts, ignore_index=True)
    key = df["symbol"].astype(str) + "|" + df["date"].astype(str)
    sd = np.r_[0, np.cumsum(key.to_numpy()[1:] != key.to_numpy()[:-1])].astype("int64")
    c = df["close"].to_numpy(float)
    atr = df["atr_d"].to_numpy(float)
    vw = c / (1 + df["vwapDistPct"].to_numpy(float) / 100)
    z = (c - vw) / atr
    hod = c + df["dist_hod_atr"].to_numpy(float) * atr
    lod = c - df["dist_lod_atr"].to_numpy(float) * atr
    tod = df["tod"].to_numpy()
    orh = pd.Series(np.where(tod == 1000, hod, np.nan)).groupby(sd).ffill().to_numpy()
    orl = pd.Series(np.where(tod == 1000, lod, np.nan)).groupby(sd).ffill().to_numpy()
    pdh = c + df["dist_pdh_atr"].to_numpy(float) * atr
    pdl = c - df["dist_pdl_atr"].to_numpy(float) * atr
    dates = sorted(set(df["date"]))
    di = pd.Series(range(len(dates)), index=dates)
    arrays = {k: df[k].to_numpy() for k in df.columns if k not in ("symbol", "date")}
    arrays.update(sd=sd, z=z.astype("float32"), orh=orh.astype("float32"), orl=orl.astype("float32"),
                  pdh=pdh.astype("float32"), pdl=pdl.astype("float32"), day=df["date"].map(di).to_numpy().astype("int32"),
                  sym=df["symbol"].astype("category").cat.codes.to_numpy().astype("int32"))
    np.savez(HERE / "data" / "base.npz", **arrays)
    pd.Series([str(d) for d in dates]).to_csv(HERE / "data" / "dates.csv", index=False)
    pd.Series(df["symbol"].astype("category").cat.categories).to_csv(HERE / "data" / "symbols.csv", index=False)
    print("rows", len(df), "sessions", len(dates), "symbol-days", sd[-1] + 1)


if __name__ == "__main__":
    main()
