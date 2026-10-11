"""Score stage D (amendment A2) -> data/scores_D.parquet. Percent lines in bps of entry price, t1s1 in R.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

from common import COND_IDS_X, DATA, NCX
from score import setup, stats

T_BAR = 4.68
LN = ["pct_t05_s035", "pct_t05_s025", "t1s1", "pct_t05_s035_hedged", "pct_t05_s025_hedged", "t1s1_hedged"]
S = setup()
z = np.load(DATA / "aggD.npz")
combos = z["combos"]
names = [" & ".join(COND_IDS_X[i] for i in c if i < NCX) for c in combos]
ncond = np.array([(c < NCX).sum() for c in combos])
rows = []
for side in ("long", "short"):
    a = z[side].astype(np.float64)
    b = z[f"base_{side}"]
    fires = a[:, 0].sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        diag = {"fires": fires, "fires_train": a[:, 0][:, S["train"]].sum(1)}
        for i, x in ((1, "x25"), (2, "x35")):
            diag[f"p_turn_{x}"] = a[:, i].sum(1) / fires
            diag[f"lift_{x}"] = diag[f"p_turn_{x}"] / (b[i].sum() / b[0].sum())
            diag[f"cover_{x}"] = a[:, i].sum(1) / b[i].sum()
        fb = a[:, 3].sum(1)
        diag["lift_close_raw"] = (a[:, 4].sum(1) / fb) / (b[4].sum() / b[3].sum())
        diag["lift_close_res"] = (a[:, 5].sum(1) / fb) / (b[5].sum() / b[3].sum())
    for li, ln in enumerate(LN):
        hed = li >= 3
        n_d = a[:, 10] if hed else a[:, 6]
        s_d = a[:, 11 + li - 3] if hed else a[:, 7 + li]
        st = stats(n_d, s_d, S)
        rows.append(pd.DataFrame({"side": side, "cond": names, "ncond": ncond, "line": ln, **st, **diag}))
out = pd.concat(rows, ignore_index=True)
out["pass"] = ((out.n >= 150) & (out.up_n >= 30) & (out.down_n >= 30) & (out.up_exp > 0) & (out.down_exp > 0)
               & (out.t >= T_BAR) & (out.wf_share >= 0.6) & (out.ex_best > 0) & (out.busiest <= 0.10)
               & (out.train_exp > 0) & (out.valid_exp > 0))
out.to_parquet(DATA / "scores_D.parquet", index=False)
base = []
for side in ("long", "short"):
    b = z[f"base_{side}"]
    for li, ln in enumerate(LN):
        hed = li >= 3
        n_d, s_d = (b[10] if hed else b[6])[None], (b[11 + li - 3] if hed else b[7 + li])[None]
        st = {k: float(v[0]) for k, v in stats(n_d, s_d, S).items()}
        base.append({"side": side, "line": ln, **st, "Y25": b[1].sum() / b[0].sum(), "Y35": b[2].sum() / b[0].sum()})
pd.DataFrame(base).to_csv(DATA / "baseD.csv", index=False)
print(len(out), "lines;", int(out["pass"].sum()), "pass")
