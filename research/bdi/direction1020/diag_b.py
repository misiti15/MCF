"""Part B diagnostics (descriptive, not policies, not counted): (1) Primary-book R per side by the 10:00 / 10:30 Q25 call
for entries at or after the checkpoint; (2) hindsight ceiling: the M1 / M2 tilt applied with the TRUE session direction
(universe-median regime up / down, flat = neutral) and with the true QQQ checkpoint->close sign. Not tradable; it bounds
what any early-direction signal could add. Writes diag_b_out.txt. Usage: python diag_b.py <scratch>.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.argv += [] if len(sys.argv) > 1 else ["."]
import tilt as T  # noqa: E402  (reuses its loaded, locked-asserted entries and context)

OUT = Path(__file__).resolve().parent
F = pd.read_parquet(Path(sys.argv[1]) / "features.parquet")
q = F[F.sym == "QQQ"].pivot_table(index="date", columns="C", values="ROD")
lines = []
P = lambda *x: lines.append(" ".join(str(y) for y in x))
for bk, B in (("primary", T.E[T.E.primary].reset_index(drop=True)), ("pooled", T.E)):
    P(f"\n== book {bk} ==")
    for C in (1000, 1030):
        d = T.direction(B, "static", "Q25", [C], 1)
        m = B.tod.to_numpy() >= C
        X = B[m].assign(d=d[m])
        P(f"Q25 @{C}: mean R of entries at/after {C} by side x call (n)")
        P(X.groupby(["split", "side", "d"]).r.agg(["mean", "count"]).round(4).unstack("d").to_string())
    reg = B.regime.map({"up": 1, "down": -1, "flat": 0}).fillna(0).to_numpy()
    for C in (1000, 1030):
        true_q = np.sign(B.date.map(q[C]).fillna(0).to_numpy())
        for lab, dd in (("regime (hindsight)", reg), (f"QQQ {C}->close sign (hindsight)", true_q)):
            dd = np.where(B.tod.to_numpy() >= C, dd, 0)
            for siz in ("M1", "M2"):
                for sp in ("train", "valid"):
                    mm = (B.split == sp).to_numpy()
                    o = T.score(B[mm], dd[mm], siz)
                    P(f"ceiling {lab:32s} from {C} {siz} {sp}: delta {o['delta']:+.4f} t {o['t']:.2f} excess {o['excess']:+.4f} (t {o['excess_t']:.2f})")
open(OUT / "diag_b_out.txt", "w").write("\n".join(lines) + "\n\nEducational only - not financial advice.\n")
print("\n".join(lines))
