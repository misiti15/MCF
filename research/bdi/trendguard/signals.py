"""Step 1: every raw signal bar (mask & window & adv, NOT only the first per symbol-day) of the 21 lab / heat setups on the
open months of the 2-year frames (research/history2y/lib.py; the locked block is never loaded). Output (git-ignored):
research/bdi/trendguard/data/signals.parquet  columns: setup, side, geom, symbol, date, tod, close, atr_d, r_frame
(r_frame = the frame's lab outcome for the setup's side/geom, used to validate the exit simulator).
    python research/bdi/trendguard/signals.py
Educational only - not financial advice.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "history2y")]
from lib import load_month, months  # noqa: E402
import rescore as RS  # noqa: E402

OUT = HERE / "data" / "signals.parquet"


def lab_setups() -> list[dict]:
    out = []
    for s in RS.setups():
        if s["kind"] not in ("lab", "heat"):
            continue
        s["mod"] = RS._load(s["path"], "m_" + re.sub(r"\W", "_", s["setup"]))
        if s["kind"] == "lab":
            s["legs"] = [(s["mod"].SIDE, getattr(s["mod"], "GEOM", "t1s1"))]
        else:
            s["legs"] = ([("long", "t1s1")] if s["sides"] in ("both", "long") and getattr(s["mod"], "LONG_AT", None) is not None else []) + \
                        ([("short", "t1s1")] if s["sides"] in ("both", "short") and getattr(s["mod"], "SHORT_AT", None) is not None else [])
        out.append(s)
    return out


def main():
    sts = lab_setups()
    rows, t0 = [], time.time()
    for mo in months():
        df = load_month(mo)
        tod, adv = df["tod"].to_numpy(), df["adv20"].fillna(0).to_numpy()
        for s in sts:
            lo, hi = s["window"]
            base = (tod >= max(950, lo)) & (tod <= min(1500, hi)) & (adv >= s["min_adv"])
            m = s["mod"]
            with np.errstate(invalid="ignore"):
                for side, geom in s["legs"]:
                    if s["kind"] == "lab":
                        mk = np.asarray(m.mask(df), bool) & base
                    else:
                        sc = np.asarray(m.score(df), float)
                        mk = base & ((sc >= m.LONG_AT) if side == "long" else (sc <= m.SHORT_AT))
                    mk &= np.isfinite(df[f"r_{side}_{geom}"].to_numpy(float)) & (df["atr_d"].to_numpy(float) > 0)
                    idx = np.flatnonzero(mk)
                    rows.append(pd.DataFrame({"setup": s["setup"], "side": side, "geom": geom,
                                              "symbol": df["symbol"].to_numpy()[idx].astype(str), "date": df["date"].to_numpy()[idx],
                                              "tod": tod[idx].astype(np.int16), "close": df["close"].to_numpy(float)[idx],
                                              "atr_d": df["atr_d"].to_numpy(float)[idx],
                                              "r_frame": df[f"r_{side}_{geom}"].to_numpy(float)[idx],
                                              "win_frame": df[f"win_{side}_{geom}"].to_numpy(float)[idx]}))
        print(f"{mo}: {len(df)} rows ({time.time() - t0:.0f}s)", flush=True)
        del df
    x = pd.concat(rows, ignore_index=True)
    x["date"] = pd.to_datetime(x["date"])
    x.to_parquet(OUT, index=False)
    print(x.groupby("setup").size().to_string(), flush=True)


if __name__ == "__main__":
    main()
