"""Trade-for-trade parity of the candidate modules (modules/*.py) with the scored configurations, on the live-like
frame of research/bdi/cwt/live/verify.py (lab rows 09:50-15:00 + the 09:35-09:45 headtail rows, adv20 >= 95M; the
locked block is never loaded), plus `heat` and the per-bar `breadth` the scan used. First True bar per symbol-day
inside the YAML window, as LabStrategy.generate. -> verify.json. Educational only - not financial advice."""
import importlib.util
import json
import sys

import numpy as np
import pandas as pd

from common import HERE, RW, pick, frows_for, WM, trades  # noqa: F401

sys.path[:0] = [str(HERE / "modules"), str(HERE.parents[1] / "bdi" / "cwt" / "live")]
import lib  # noqa: E402
import verify as V0  # noqa: E402  (research/bdi/cwt/live/verify.py month_frame)

MODS = {  # module: (scan config, window)
    "CWT14x-orl-p20-lowvol-gap2-long": (("ORL", 0.20, 3, "v<1", "|gap|>=2"), "0950-1130", (950, 1130)),
    "CWT14x-pdl-p05-lowvol-brdlo-fo1-long": (("PDL", 0.05, 3, "v<1", "brd<.4+fo>1"), "0950-1500", (950, 1500)),
    "CWT14x-orl-p10-gapup-heatlo-long": (("ORL", 0.10, 3, "any", "gap>0+heat<=-30"), "0950-1500", (950, 1500)),
}


def load(name):
    spec = importlib.util.spec_from_file_location(f"m_{name}", HERE / "modules" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V0.COLS = V0.COLS + ["heat"]
mods = {k: load(k) for k in MODS}
got = {k: [] for k in MODS}
br = RW[["date", "tod", "breadth"]].drop_duplicates(["date", "tod"])
for m in lib.months():
    df = V0.month_frame(m)
    df = df.merge(br, on=["date", "tod"], how="left")
    for k, (_, _, w) in MODS.items():
        got[k].append(V0.first_hits(df, mods[k].mask(df), w))
    print(m, len(df), flush=True)
out = {}
for k, (cfg, wn, _) in MODS.items():
    rows = frows_for(*cfg)
    idx = pick(rows[WM[wn][rows]])
    ref = set(zip(RW["date"].to_numpy()[idx].astype(str), RW["symbol"].to_numpy()[idx].astype(str),
                  RW["tod"].to_numpy()[idx].astype(int)))
    g = pd.concat(got[k], ignore_index=True)
    mine = set(zip(g["date"].astype(str), g["symbol"].astype(str), g["tod"].astype(int)))
    out[k] = {"scored_n": len(ref), "module_n": len(mine), "matched": len(ref & mine), "only_scored": len(ref - mine),
              "only_module": len(mine - ref)}
    print(k, out[k])
json.dump(out, open(HERE / "verify.json", "w"), indent=1)
