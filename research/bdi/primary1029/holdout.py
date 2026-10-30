"""primary1029 ONE locked-block look (2024-11-01..2025-02-28) for the single finalist that beat the parent (D0, ST-P on)
on train AND valid: R2b (after >= 2 short-family stops today, family lots at half size), with its uniform control.
Sets MCF_HIST_ALLOW_LOCKED in its own process only. Lineage look 1 -> bar t >= 1.0.
Usage: python holdout.py <scratch>   Educational only - not financial advice."""
import os, sys, math
os.environ["MCF_HIST_ALLOW_LOCKED"] = "1"
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
S = Path(sys.argv[1])
import importlib
os.environ.pop("MCF_HIST_ALLOW_LOCKED")          # sim asserts unset at import; the locked frames are read via allow_locked
import sim
sig = sim.load(S / "p3" / "p3hold", allow_locked=True)
STP = lambda c: c["setup_real"] <= -2
tr = sim.simulate(sig, block=STP)
SESS = sorted(set(sig.date))
w = np.where((tr.fam == "S") & (tr.fam_stops >= 2), 0.5, 1.0)
mw = w.mean()
def day(wt): return tr.assign(wr=wt * tr.r).groupby("date").wr.sum().reindex(SESS, fill_value=0.0)
pday, cday, uday = day(np.ones(len(tr))), day(w), day(np.full(len(tr), mw))
def m(d, wt):
    q = np.sort(d.to_numpy()); k = max(1, round(0.05 * len(q))); c = d.cumsum()
    return dict(totR=round(d.sum(), 1), R_per_risk=round((wt * tr.r).sum() / wt.sum(), 4), worst=round(q[0], 1), cvar5=round(q[:k].mean(), 2),
                red=int((d < 0).sum()), maxdd=round(float((c.cummax() - c).max()), 1))
rows = {"PARENT D0 (locked)": m(pday, np.ones(len(tr))), "R2b fam2half (locked)": m(cday, w), "U(R2b) (locked)": m(uday, np.full(len(tr), mw))}
print(pd.DataFrame(rows).T.to_string())
dd = cday - uday; t = dd.mean() / (dd.std(ddof=1) / math.sqrt(len(dd)))
worst = pday.sort_values().index[:max(1, round(0.05 * len(pday)))]
x = (cday - uday)[worst]
print(f"sessions {len(SESS)}, trades {len(tr)}, mean weight {mw:.3f}")
print(f"vs uniform control: mean {dd.mean():+.3f} R/day, t {t:.2f}; on the parent's worst-5% days {x.mean():+.2f} R/day")
print("holdout look 1 (bar t >= 1.0 vs U, and R per risk >= parent):", "PASS" if t >= 1.0 and rows["R2b fam2half (locked)"]["R_per_risk"] >= rows["PARENT D0 (locked)"]["R_per_risk"] else "FAIL")
print("Educational only - not financial advice.")
