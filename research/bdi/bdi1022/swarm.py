"""bdi1022 swarm (PLAN.md, pre-declared): A = time windows for the gap-down short family, B = "Nasdaq already weak"
block for long setups. 36 configs, scored with gates1021's evaluate() on gates1021's cached live-shaped signal tables
(costs in). The locked block 2024-11-01..2025-02-28 is never read (no_locked asserts in load_sig). No holdout scored.
Usage: python swarm.py            Educational only - not financial advice."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "gates1021" / "scripts"))
from load import load_sig  # noqa: E402
from part_b import evaluate  # noqa: E402

U = pd.read_csv(HERE.parent / "gates1021" / "setups_scored.csv").set_index("setup")
FAM = ["RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
       "MF2-open-rsimidhi-flowsell-FD", "MF4-h40-open-flowsell-FD"]
WIN = {"W1": (950, 1059), "W2": (1100, 1159), "W3": (1200, 1259), "W4": (1300, 1500), "W5": (1130, 1229)}
LONGS = ["NS5-sma50-flush-oversold-long-FD", "NS1-rsidip-rsi5pop-long-FD", "NM-HL-T75-pm-long",
         "NM-AR-AM-gapdown-capitulation-long", "NS5-sma50-flush-oversold-long", "ST4-emadn-long-am-t1s05-FD",
         "ST7-rsi50dn-long-pm-t1s1-FD", "ST8-volspikedn-long-pm-t1s1-FD"]
QG = {"Q50": -0.5, "Q75": -0.75}
N_LINEAGE = 718 + 196 + 340 + 36
BAR = round(math.sqrt(2 * math.log(N_LINEAGE)), 2)

sig = load_sig(FAM + LONGS)
rows = []
for part, setups, gates in (("A", FAM, WIN), ("B", LONGS, QG)):
    for st in setups:
        s = sig[sig["setup"] == st].reset_index(drop=True)
        side, geom = U.loc[st, "side"], U.loc[st, "geom"]
        ccol = f"c_{side}_{geom}"
        tod = s["tod"].to_numpy(int)
        for g, v in gates.items():
            blk = ~((tod >= v[0]) & (tod <= v[1])) if part == "A" else (s["qqq_fo"].to_numpy(float) <= v)
            e = evaluate(s, blk, ccol)
            kept_share = 1 - blk.mean()
            ok = (e["train_gated_exp"] or -1) > 0 and (e["valid_gated_exp"] or -1) > 0 \
                and (e["train_delta"] or -1) > 0 and (e["valid_delta"] or -1) > 0 \
                and e["train_delta"] > e["train_ctrl_delta"] and e["valid_delta"] > e["valid_ctrl_delta"] \
                and (e["up_delta"] or 0) >= 0 and (e["down_delta"] or 0) >= 0 and (e["all_delta_t"] or 0) >= BAR \
                and (part == "A" or kept_share >= 0.8)
            rows.append(dict(part=part, setup=st, gate=g, side=side, kept_pct=round(100 * kept_share, 1), passes=bool(ok), **e))
R = pd.DataFrame(rows)
R.to_csv(HERE / "results.csv", index=False)
(HERE / "counts.json").write_text(json.dumps({"configs": len(R), "lineage_N": N_LINEAGE, "bar_t": BAR,
                                              "passes": int(R.passes.sum()), "locked_block_read": False}, indent=1))
cols = ["setup", "gate", "kept_pct", "train_parent_exp", "train_gated_exp", "valid_parent_exp", "valid_gated_exp",
        "train_delta", "valid_delta", "train_ctrl_delta", "valid_ctrl_delta", "up_delta", "down_delta", "all_delta_t",
        "passes"]
pd.set_option("display.width", 250)
print(f"configs {len(R)}, passes {int(R.passes.sum())}, bar {BAR} (lineage N {N_LINEAGE})")
for p in ("A", "B"):
    print(f"\n== part {p}")
    print(R[R.part == p][cols].to_string(index=False))
# part A pooled over the family: avg R by window and split (descriptive)
f = sig[sig["setup"].isin(FAM)].copy()
f["w"] = np.select([f.tod.between(*v) for v in list(WIN.values())[:4]], list(WIN)[:4], "x")
print("\n== part A pooled family, avg R after costs (n) by window x split x regime")
print(f.pivot_table(index="w", columns=["split"], values="r", aggfunc=["mean", "size"]).round(3).to_string())
print(f.pivot_table(index="w", columns=["regime"], values="r", aggfunc="mean").round(3).to_string())
# qqq weak at entry for the family itself (descriptive, not a config)
f["qw"] = pd.cut(f.qqq_fo, [-99, -0.75, -0.25, 0.25, 0.75, 99])
print("\n== family avg R by QQQ from-open at entry (descriptive)")
print(f.pivot_table(index="qw", columns="split", values="r", aggfunc=["mean", "size"], observed=True).round(3).to_string())
print("\nEducational only - not financial advice.")
