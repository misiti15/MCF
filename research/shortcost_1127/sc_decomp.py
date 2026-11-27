"""SHORTCOST-1127: is the gain cost or selection? Candidate lots (pre-book), kept vs removed: avg gross R, LIVE-L cost,
LIVE-L net, LR8 net, per rule x split (7 real setups; RND pools separately). `python sc_decomp.py SCRATCH` -> decomp.csv.
Educational only - not financial advice."""
import os, sys
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.argv = sys.argv[:2]
import sc_hist as H  # noqa: E402
import sc_common as C  # noqa: E402
X = H.X[H.X.entry >= 5]
rows = []
for r in ["R1", "R2", "R3", "R4"]:
    sk = C.rule_skip(r, X.side.values, X.entry.values, X.risk.values, X.cex.values)
    for grp, tags in (("real", H.REAL), ("rnd", ["RND-G05", "RND-G07", "RND-G37"])):
        for per in ("FIT", "CHECK", "T2"):
            m = (X.per == per).values & X.tag.isin(tags).values
            for lab, mm in (("kept", m & ~sk), ("removed", m & sk)):
                g = X[mm]
                rows.append(dict(rule=r, grp=grp, per=per, part=lab, n=len(g), gross=g.r_gross.mean(), ll_cost=g.ll_cost.mean(),
                                 net_ll=g.r_ll.mean(), net_lr8=g.r_lr8.mean()))
D = pd.DataFrame(rows).round(4)
D.to_csv(os.path.join(HERE, "decomp.csv"), index=False)
print(D.to_string())
