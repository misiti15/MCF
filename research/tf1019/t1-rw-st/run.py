"""Run the pre-declared t1-rw-st grid (PLAN.md) for one timeframe. Educational only - not financial advice."""
import json, sys, time
from pathlib import Path
import pandas as pd
from mcf.research import timeframes as tf

ROOT = Path(__file__).resolve().parents[3]
FD = ROOT / "research/bdi/fullday"
OUT = Path(sys.argv[2])
NAMES = ["RW1-gapdn-bounce-flowsell-short", "RW2-exhaustion-noon-adv150-short", "RW3-gapdn-rsi5pop-flowsell-short",
         "RW4-ns3-adv150-short", "RW5-heat30-flowsell-rsi5pop-gapdn-short", "RW6-ns2-up3-short",
         "RW7-gapdn-bounce-early-short", "ST1-ordn-long-pm-t05s1", "ST2-slope20up-long-am-t05s1",
         "ST3-rsi5up-short-pm-t1s1", "ST4-emadn-long-am-t1s05", "ST5-pdbrkup-short-mid-t05s1",
         "ST6-volspikeup-short-mid-t1s1", "ST7-rsi50dn-long-pm-t1s1", "ST8-volspikedn-long-pm-t1s1",
         "L3-gap-slope-fromopen", "L3-gap-slope-lowdist", "L3-gap-slope-rsi5hi", "exhaustion_short"]
spec = {s["name"]: s for s in json.load(open(FD / "specs.json"))}
m = int(sys.argv[1])
for nm in NAMES:
    t0 = time.time()
    tr = tf.run_module_tf(str(FD / f"{nm}-FD.py"), m, window=(950, 1500), split="open", symbols="core",
                          min_adv=float(spec[nm]["min_adv"]))
    tr.to_parquet(OUT / f"{nm}__{m}.parquet")
    print(nm, m, len(tr), round(time.time() - t0, 1), flush=True)
