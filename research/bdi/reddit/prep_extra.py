"""Reddit study step 0: compact extra columns aligned row-for-row with research/bdi/stack1009/data/base.npz
(same loader, same filter: open months only via research/history2y/lib.py - the rule-19 locked block is refused -,
09:50-15:00, adv20 >= 95M). Stores bar high/low as distances in daily ATR (float16), the candle wicks, and the
live-frame RSI divergence flags. Output (git-ignored): data/extra.npz. Educational only - not financial advice."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

COLS = ["close", "high", "low", "upper_wick", "lower_wick", "bull_div", "bear_div", "tod", "atr_d", "adv20"]


def main():
    out = {k: [] for k in ("hi_atr", "lo_atr", "upper_wick", "lower_wick", "bull_div", "bear_div", "close")}
    for m in lib.months():
        df = lib.load_month(m, COLS + ["symbol", "date"])
        df = df[(df.tod >= 950) & (df.tod <= 1500)]
        df = df[df["adv20"].to_numpy(float) >= 95e6].reset_index(drop=True)
        c, a = df["close"].to_numpy(float), df["atr_d"].to_numpy(float)
        out["hi_atr"].append(((df["high"].to_numpy(float) - c) / a).astype("float16"))
        out["lo_atr"].append(((c - df["low"].to_numpy(float)) / a).astype("float16"))
        out["upper_wick"].append(df["upper_wick"].to_numpy(float).astype("float16"))
        out["lower_wick"].append(df["lower_wick"].to_numpy(float).astype("float16"))
        out["bull_div"].append(np.nan_to_num(df["bull_div"].to_numpy(float)).astype("int8"))
        out["bear_div"].append(np.nan_to_num(df["bear_div"].to_numpy(float)).astype("int8"))
        out["close"].append(c.astype("float32"))
        print(m, len(df), flush=True)
    arr = {k: np.concatenate(v) for k, v in out.items()}
    base_c = np.load(ROOT / "research" / "bdi" / "stack1009" / "data" / "base.npz")["close"]
    assert len(base_c) == len(arr["close"]) and np.allclose(base_c, arr["close"], equal_nan=True), "row misalignment"
    arr.pop("close")
    np.savez_compressed(HERE / "data" / "extra.npz", **arr)
    print("rows", len(base_c), "aligned with stack1009 base.npz")


if __name__ == "__main__":
    main()
