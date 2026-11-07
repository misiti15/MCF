"""Block A keep flags (PLAN.md): flush-gate neighbours (A1-A3), QDAY flush gate (A4-A5), realised -2R + open -3R latch
(A6), A4 + A6 (A7). Inputs: BURST2 tables (<b2>/trades2_<mode>.parquet, keep2_<mode>.parquet; locked block absent).
Usage: python sim_a.py <burst2 scratch> <out scratch>     Educational only - not financial advice."""
import os, sys
from pathlib import Path
import numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
B2, S = Path(sys.argv[1]), Path(sys.argv[2]); S.mkdir(exist_ok=True)
for mode in ("2y", "live"):
    T = pd.read_parquet(B2 / f"trades2_{mode}.parquet"); K = pd.read_parquet(B2 / f"keep2_{mode}.parquet")
    assert not T.date.between("2024-11-01", "2025-02-28").any()
    base = K["base"].to_numpy()
    m_, side_, q_, fo_ = T.m.to_numpy(), T.side.to_numpy(int), T.qqq_r30.to_numpy(float), T.spy_fo.to_numpy(float)
    COND = {"A1_D_flush_2_30": (2, -0.003, False), "A2_D_flush_2_50": (2, -0.005, False), "A3_D_flush_3_40": (3, -0.004, False),
            "A4_D_flushQ_2_40": (2, -0.004, True), "A5_D_flushQ_2_30": (2, -0.003, True)}
    cols = {c: np.ones(len(T), bool) for c in COND}
    for (su, d), ix in T[base].groupby(["setup", "date"], sort=False).indices.items():
        ix = np.flatnonzero(base)[np.asarray(ix)]; ix = ix[np.lexsort((ix, m_[ix]))]
        if len(ix) <= 2: continue
        for c, (B, y, q) in COND.items():
            keep = np.ones(len(ix), bool)
            for k in range(B, len(ix)):
                j = ix[k]
                if side_[j] != -1 or not (q_[j] <= y) or (q and not (fo_[j] >= -0.0025)): continue
                prev = keep[:k] & (m_[ix[:k]] > m_[j] - 15) & (side_[ix[:k]] == -1)
                if prev.sum() >= B: keep[k] = False
            cols[c][ix] = keep
    out = pd.DataFrame(cols)
    out["base"] = base; out["latch_realised_-2"] = K["latch_realised_-2"].to_numpy()
    out["A6_latch_or_-3"] = K["latch_realised_-2"].to_numpy() & K["A_openlatch_-3"].to_numpy()
    out["A7_flushQ_latch_or"] = out["A6_latch_or_-3"] & out["A4_D_flushQ_2_40"]
    # flush / QDAY flags are applied on top of the live latch for A4 / A7 comparisons in score_a.py
    out.to_parquet(S / f"keepA_{mode}.parquet")
    print(mode, len(T), {c: round(1 - out[c][base].mean(), 4) for c in out.columns if c not in ("base",)})
