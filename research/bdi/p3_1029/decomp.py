"""p3_1029: why the Type-A cost filters help - gross vs cost R of the trades they remove (parent portfolio, open
two-year history), and the same split on Primary's live 10 sessions (descriptive). Usage: python decomp.py <scratch>
Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
sys.argv = [sys.argv[0], sys.argv[1], "1"]
import evalp as E
tr = E.simulate({})
# re-attach per-trade cost columns (simulate keeps order of sig rows taken)
take = E.sig.merge(tr[["date"]].assign(k=1), how="left", left_index=True, right_index=True)
par = E.sig.copy()
out = []
cfgk = {"A1 R>=$0.10": par.R_ps >= 0.10, "A2 R>=$0.15": par.R_ps >= 0.15, "A3 cost<=0.15R": par.cost_stop_r <= 0.15}
gross = par.r_base + par.cost_stop_r * 0  # placeholder
from mcf.research.gates import GEOMK
dn = par.geom.map(lambda g: GEOMK[g][1])
par["gross"] = par.side * 0  # computed below from lab: lab_r already net of 1c/side; gross ~ lab_r/dn + 2c/R
par["gross"] = (par.lab_r + 2 * 0.01 / par.R) / dn
par["cost"] = par.gross - par.r_base
for k, m in cfgk.items():
    for lab, g in (("kept", par[m]), ("removed", par[~m])):
        out.append(f"{k:14s} {lab:8s} n {len(g):6d}  net {g.r_base.mean():+.4f}  gross {g.gross.mean():+.4f}  cost {g.cost.mean():.4f}  median R/share ${g.R_ps.median():.3f}")
out.append("\nremoved by A3, by setup: " + par[par.cost_stop_r > 0.15].groupby("setup").size().to_string())
out.append("share removed by A3, by setup: " + (par.cost_stop_r > 0.15).groupby(par.setup).mean().round(3).to_string())
# live (paper) 10 sessions
T = pd.read_csv(E.OUT / "trades10.csv")
T["R_ps"] = (T.entry - T.stop).abs()
T["cost_stop_r"] = (2 * (0.01 + T.entry * 1e-4) + 0.02) / T.R_ps
for lab, g in (("live cost<=0.15", T[T.cost_stop_r <= 0.15]), ("live cost>0.15", T[T.cost_stop_r > 0.15])):
    out.append(f"{lab:16s} n {len(g):4d} avgR {g.R.mean():+.4f} sumR {g.R.sum():+.2f} $ {g.pnl_adj.sum():+.2f} cost-in-R (pnl-pnl_adj)/risk {((g.pnl - g.pnl_adj) / g.risk).mean():.4f}")
C8 = E.sig.setup.unique()
c = T[T.strategy.isin(C8)]
for lab, g in (("live cur8 cost<=0.15", c[c.cost_stop_r <= 0.15]), ("live cur8 cost>0.15", c[c.cost_stop_r > 0.15])):
    out.append(f"{lab:20s} n {len(g):4d} avgR {g.R.mean():+.4f} sumR {g.R.sum():+.2f} $ {g.pnl_adj.sum():+.2f}")
txt = "\n".join(out) + "\n\nEducational only - not financial advice.\n"
open(E.OUT / "decomp_out.txt", "w").write(txt); print(txt)
