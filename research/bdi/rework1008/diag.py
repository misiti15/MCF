"""Diagnostics for the report (post-declared, disclosed, NOT eligible as finalists this round):
(1) the F2 neighbourhood of RW1 (already-scored rows, no new configs); (2) re-entry for RW1 / RW3 (4 new configs);
(3) RW1 by week. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from combos import Ctx  # noqa: E402
from lib import exit_bar, stats  # noqa: E402

pd.set_option("display.width", 250)
g = pd.read_parquet(HERE / "data" / "gated.parquet")
nb = g[(g.family == "F2") & (g.c2 == "rsi55-65") & (g.c3 == "gap<0") & (g.side == "short")]
print(nb.pivot_table(index=["c0", "c1"], columns=["window", "geom"], values="va_exp").round(2).to_string())
print(nb.pivot_table(index=["c0", "c1"], columns=["window", "geom"], values="tr_exp").round(2).to_string())
flip = g[(g.family == "F2") & (g.conds == "heat<=-20+bp<-0.35+rsi55-65+gap<0") & (g.window == "w0950_1100")]
print(flip[["side", "geom", "tr_n", "tr_exp", "tr_t", "va_n", "va_exp", "va_t"]].round(3).to_string())
cx = Ctx()
out = []
for lab, conds in (("RW1", ("heat<=-20", "bp<-0.35", "rsi55-65", "gap<0")), ("RW3", ("heat<=-20", "bp<-0.35", "rsi5>80", "gap<0"))):
    for s, sp in cx.sp.items():
        pm = cx.rowmask(s, conds, "w0950_1100")
        pr = np.flatnonzero(pm)
        e1 = sp.first_per_day(pr)
        xb, _ = exit_bar(sp, e1, "short", "t1s1")
        has = xb >= 0
        pos = np.searchsorted(pr, xb[has] + 1)
        ok = pos < len(pr)
        ci = pr[np.minimum(pos, len(pr) - 1)]
        ok &= sp.sid[ci] == sp.sid[e1[has]]
        re = np.sort(ci[ok])
        for k, e in (("first", e1), ("RE", re), ("BOTH", np.sort(np.r_[e1, re]))):
            m = stats(sp, e, "short", "t1s1")
            out.append({"setup": lab, "split": s, "kind": k, **{x: m[x] for x in ("n", "exp", "t", "tpd", "exbest")}} if m else {"setup": lab, "split": s, "kind": k, "n": len(e)})
        if lab == "RW1":
            r = sp.r[("short", "t1s1")][e1]
            wk = pd.to_datetime(sp.df.date.to_numpy()[e1]).isocalendar().week.to_numpy()
            print(s, pd.Series(r).groupby(wk).agg(["size", "mean"]).round(3).T.to_string())
print(pd.DataFrame(out).round(3).to_string())
pd.DataFrame(out).to_csv(HERE / "data" / "diag_reentry.csv", index=False)
