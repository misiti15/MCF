"""Move Hunt precursor scan on one day's decision rows (rows.parquet from moves.py): base rate of a big move
(>= K daily ATR within 90 min, in the given direction) and the lift of single-feature quintiles. Descriptive, one day,
hindsight labels: it only nominates candidates for the 2-year test. Usage: python precursors.py <scratch> <day> [K]
Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S, D = Path(sys.argv[1]), sys.argv[2]; K = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
R = pd.read_parquet(S / "mh" / D / "rows.parquet")
R = R[~R.blackout & (R.tod >= 950)].copy()
R["fo_atr"] = R.fromOpen / 100 * R.close / R.atr_d
R["vwap_atr"] = R.vwapDistPct / 100 * R.close / R.atr_d
R["gap_atr"] = R.gap / 100 * R.close / R.atr_d
R["range_atr"] = R.dist_hod_atr + R.dist_lod_atr          # day range so far / ATR
R["vol_exp"] = R.atrPct / R.atr_pct_d                       # 5-min ATR(14) as a share of the daily ATR ("in play")
R["absfo_atr"] = R.fo_atr.abs()
feats = ["vol_exp", "absfo_atr", "rvol", "fo_atr", "vwap_atr", "gap_atr", "range_atr", "atr_pct_d", "volumeRatio", "volumeSurge", "rsi", "rsi5",
         "buyPressure", "heat", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr", "dist_pdl_atr", "momentum", "atrPct", "tod"]
print(f"rows {len(R)} (non-blackout, 09:50-15:00), symbols {R.symbol.nunique()}, K = {K} ATR")
for side, col in (("long", "up_atr"), ("short", "dn_atr")):
    y = R[col] >= K; base = y.mean()
    print(f"\n### {side}: base rate {base:.2%} ({y.sum()} rows, {R.loc[y, 'symbol'].nunique()} symbols)")
    out = []
    for f in feats:
        q = pd.qcut(R[f].rank(method="first"), 5, labels=False)
        t = y.groupby(q).mean()
        out.append((f, *(t / base).round(2).tolist(), round(R[f].groupby(q).median().iloc[-1], 2), round(R[f].groupby(q).median().iloc[0], 2)))
    o = pd.DataFrame(out, columns=["feature", "q1", "q2", "q3", "q4", "q5", "q5_median", "q1_median"])
    o["spread"] = (o[["q1", "q5"]].max(axis=1) / o[["q1", "q5"]].min(axis=1).replace(0, np.nan)).round(1)
    print(o.sort_values("spread", ascending=False).to_string(index=False))
