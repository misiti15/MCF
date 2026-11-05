"""HC1 step 1: re-run Hunch's pooled logreg walk over the 200-ticker replay (M1) and keep, per 3-min bar, the
cross-ticker aggregates of its next-bar P(up) and of the pressure feature. Same model / update order as
mcf.hunch.replay._walk (pooled LogReg with ticker intercept; update on the previous step, then guess).
Usage: python hunch_probs.py <scratch>. Writes <scratch>/hunch_agg.parquet. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/MCF")
from mcf.hunch import data as D, learners as Lr, replay as R  # noqa: E402

S = Path(sys.argv[1])
U = [ln.split()[0] for ln in Path("/home/user/MCF/research/hunch/universe200.txt").read_text().splitlines()
     if ln.strip() and ln[0] != "#"]
pf = S / "panel200.parquet"
panel = pd.read_parquet(pf) if pf.exists() else D.build_panel(U)
if not pf.exists():
    panel.to_parquet(pf)
g = R.make_grid(panel, "M1")
del panel
feats = g.extra["features"]; X = g.X; T, Sn, F = X.shape
tod_col = feats.index("tod"); pc = feats.index("pressure")
pooled = Lr.LogReg(F, tod_col, n_groups=Sn)
rows = []
for k in range(T):
    if k > 0:
        m = g.mask[k - 1]; idx = np.flatnonzero(m)
        if len(idx):
            pooled.update(X[k - 1][m].astype(float), g.y[k - 1][m], idx)
    m = g.mask[k]
    if not m.any():
        continue
    idx = np.flatnonzero(m)
    p = pooled.proba(X[k][m].astype(float), idx)
    pr = X[k][m][:, pc]
    rows.append((k, len(idx), float((p > 0.5).mean()), float(p.mean()), float(np.nanmean(pr))))
A = pd.DataFrame(rows, columns=["k", "n", "share_up", "mean_p", "press"])
st = g.steps.reset_index(drop=True)
A = A.join(st[["date", "b", "sess", "period", "scored"]], on="k")
A["date"] = pd.to_datetime(A.date).dt.strftime("%Y-%m-%d")
A.to_parquet(S / "hunch_agg.parquet")
print(A.groupby("period").agg(n=("k", "size"), su=("share_up", "mean"), mp=("mean_p", "mean")))
