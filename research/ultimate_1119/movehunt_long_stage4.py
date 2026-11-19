"""Move-hunt LONG stage 4 (declared AFTER reading stages 1-3 of movehunt_long_analyze.py, so these are selected on the
fit half and carry selection noise; check half untouched). Combines the Stage-2 leaders with the WAVE1 persistent
families (time of day, gap, distance from open) and the cost lever. Each row scored on r_g1 (bracket) and r_t30
(timed 30-min) -> 2 configs per row. Deduped one live position per symbol. Same cost top-up as the analyzer.
    python research/ultimate_1119/movehunt_long_stage4.py /dev/shm/mh_long.parquet
Educational only - not financial advice.
"""
import sys
import numpy as np
import pandas as pd

sys.argv = [sys.argv[0], sys.argv[1]]
src = open(__file__.replace("_stage4.py", "_analyze.py")).read()
src = src.split("# ---------------- Stage 1")[0]          # data load, cost top-up, stats(), dedupe(), baseline
exec(src)

WO = (D.fo_atr <= -1.0) | (D.hod_atr >= 1.5)
mid = (D.tod >= 1030) & (D.tod < 1200)
cheap = D.cost_r <= 0.10
combos = {
    "S1 W & 1030-1200": WO & mid,
    "S2 W & 1030-1200 & cost_r<=.10": WO & mid & cheap,
    "S3 W & 1030-1200 & gap<=-1": WO & mid & (D.gap <= -1),
    "S4 W & spy_r30<-0.3 & cost_r<=.10 (tape flush)": WO & (D.spy_r30 < -0.3) & cheap,
    "S5 hod>=1.5 & vwap_reclaim & cost_r<=.10": (D.hod_atr >= 1.5) & (D.vwap_reclaim == 1) & cheap,
    "S6 hod>=1.5 & vwap_reclaim & 1030-1200": (D.hod_atr >= 1.5) & (D.vwap_reclaim == 1) & mid,
    "S7 W & 1030-1200 & atr_pct>=4": WO & mid & (D.atr_pct >= 4),
    "S8 W & 1030-1200 & spy_fo>0": WO & mid & (D.spy_fo > 0),
}
rows, n = [], 0
keep = {}
for k, m in combos.items():
    x = dedupe(D[m])
    keep[k] = x
    for col in ("r_g1", "r_t30"):
        n += 1
        r = stats(x, col); r["cfg"] = f"{k} | {col}"; rows.append(r)
show(rows, "Stage 4: selected combos (fit half, deduped); avgR/A/B/woBest/PASS use the named outcome")
# month table for the two best by t on r_t30
best = sorted([r for r in rows if r["cfg"].endswith("r_t30") and r.get("n", 0) > 0], key=lambda r: -r["t"])[:2]
for r in best:
    k = r["cfg"].split(" | ")[0]
    x = keep[k]
    t = x.groupby(x["date"].dt.to_period("M")).agg(n=("r_t30", "size"), t30=("r_t30", "mean"), g1=("r_g1", "mean"))
    print(f"\n### by month: {k}\n"); print(t.round(3).to_string())
print(f"\nstage-4 configurations: {n}")
