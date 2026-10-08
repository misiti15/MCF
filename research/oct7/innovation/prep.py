"""Build the BD scan frame: lab frame (research/setups2/data) restricted to 2026-07-15..2026-09-15
(train 07-15..08-25, valid 08-26..09-15) plus the causal BD features from _bd_features.py.
Locked data is never read (setup_lab.load refuses the test split; dates >= 09-16 are not in train/valid).
Output: research/oct7/innovation/data/{train,valid}.parquet (gitignored). Educational only - not financial advice."""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
sys.path.insert(0, "research/oct7/innovation")
from mcf.research.setup_lab import load  # noqa: E402
import _bd_features as F  # noqa: E402

COLS = ["symbol", "date", "tod", "close", "high", "low", "rsi", "rsi5", "momentum", "volumeRatio", "vwapDistPct",
        "buyPressure", "atrPct", "fromOpen", "gap", "atr_d", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr",
        "dist_pdl_atr", "sma20_dist_pct", "sma20_slope_pct", "flow3", "bear_div", "bull_div", "upper_wick",
        "lower_wick", "pricePosition", "rsiSlope",
        "volumeHeat", "rsiHeat", "momentumHeat", "priceActionHeat", "trendHeat", "macdHeat", "vwapHeat"]
OUT = [f"{k}_{s}_{g}" for k in ("r", "win") for s in ("long", "short") for g in ("t1s1", "t05s1", "t1s05")]
out_dir = Path("research/oct7/innovation/data")
out_dir.mkdir(parents=True, exist_ok=True)

for split in ("train", "valid"):
    t0 = time.time()
    df = load(split, columns=COLS + OUT)
    df = df[df["date"] >= pd.Timestamp("2026-07-15").date()] if split == "train" else df
    assert df["date"].max() <= pd.Timestamp("2026-09-15").date()
    df = df.sort_values(["symbol", "date", "tod"], kind="stable").reset_index(drop=True)
    for n in (2, 3, 4):
        df[f"rsi{n}"] = F.rsi(df, n).astype("float32")
    L = F.levels(df)
    for k in ("up_run", "dn_run", "move_atr"):
        df[k] = L[k].astype("float32")
    df["pc_atr"] = ((L["close"] - L["pc_px"]) / L["atr"]).astype("float32")      # >0 above prior close
    for t in (950, 1000, 1010, 1030):
        df[f"up_run_{t}"] = F.at_time(df, L["up_run"], t).astype("float32")
        df[f"dn_run_{t}"] = F.at_time(df, L["dn_run"], t).astype("float32")
        df[f"hod_{t}"] = F.at_time(df, L["hod_px"], t).astype("float32")
        df[f"lod_{t}"] = F.at_time(df, L["lod_px"], t).astype("float32")
    df["hod_px"] = L["hod_px"].astype("float32")
    df["lod_px"] = L["lod_px"].astype("float32")
    v = df["vwapDistPct"].to_numpy(dtype=float)
    df["vwap_max"] = F.running(df, v, "max").astype("float32")
    df["vwap_min"] = F.running(df, v, "min").astype("float32")
    df["symbol"] = df["symbol"].astype("category")
    df.to_parquet(out_dir / f"{split}.parquet")
    print(split, len(df), df["date"].nunique(), "sessions", round(time.time() - t0), "s", flush=True)
