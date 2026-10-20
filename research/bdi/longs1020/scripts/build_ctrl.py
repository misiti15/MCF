"""Deterministic random sample of universe rows (adv20 >= $95M, bar close 09:50-14:00, crc32 % 20 == 0) for the
same-minute random-long control of the 1-minute exits (holdtr, time60). Educational only - not financial advice."""
import zlib

import numpy as np
import pandas as pd

from common import SCR, lib


def main():
    out = []
    for month in lib.months(locked=False):
        if month in lib.LOCKED_MONTHS:
            continue
        df = lib.load_month(month, columns=["symbol", "date", "tod", "close", "atr_d", "gap", "adv20"])
        df = df[(df["adv20"] >= 95e6) & (df["tod"] >= 950) & (df["tod"] <= 1400) & (df["atr_d"] > 0)]
        k = df["symbol"].astype(str) + "|" + df["date"].astype(str) + "|" + df["tod"].astype(str)
        keep = np.fromiter((zlib.crc32(s.encode()) % 20 == 0 for s in k), bool, len(k))
        x = df[keep].copy()
        x["tier"] = np.where((np.abs(x["gap"]) >= 20) | (x["close"] < 5), 3.0, 1.0)
        out.append(x.drop(columns=["adv20", "gap"]))
        print(month, keep.sum(), flush=True)
    pd.concat(out, ignore_index=True).to_parquet(SCR / "ctrl_rows.parquet", index=False)


if __name__ == "__main__":
    main()
