"""MH1105-P1 (research/bdi/1105/MH_PLAN.md, pre-registered): ONE 2-year test of the 09:50 gap-up-vs-falling-tape short.
Usage: python mh_p1.py     Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path("/home/user/MCF"); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib
from mcf.research.gates import t_required
BAR = 0.9 * t_required(6); HERE = Path(__file__).resolve().parent; LK0, LK1 = "2024-11-01", "2025-02-28"
F = []
for m in lib.months():
    f = lib.load_month(m, columns=["symbol", "date", "tod", "gap", "fromOpen", "adv20", "r_short_t1s1"]); F.append(f[f.tod == 950])
F = pd.concat(F, ignore_index=True); F["date"] = F.date.astype(str); assert not F.date.between(LK0, LK1).any()
ctx = pd.concat([lib.load_context(m) for m in lib.months()], ignore_index=True); ctx["date"] = ctx.date.astype(str)
F = F.merge(ctx[ctx.tod == 950][["date", "spy_fo"]], on="date", how="left")
F = F[(F.adv20 >= 95e6) & F.r_short_t1s1.notna()].copy()
dly = lib.daily(); dly = dly[dly.symbol == "SPY"].copy(); dly["date"] = dly.date.astype(str)
oc = (dly.set_index("date").close / dly.set_index("date").open - 1) * 100
F["dtype"] = F.date.map(pd.Series(np.where(oc > 0.25, "up", np.where(oc < -0.25, "down", "quiet")), index=oc.index))
F["r"] = F.r_short_t1s1; F["ex"] = F.r - F.groupby("date").r.transform("mean")
A = F[(F.gap >= 0.8) & (F.fromOpen <= 0) & (F.spy_fo <= -0.5)].copy()
def ctt(x, c):
    g = x.groupby("date")[c].agg(["sum", "size"]); mu = g["sum"].sum() / g["size"].sum(); G = len(g)
    v = ((g["sum"] - mu * g["size"]) ** 2).sum() / g["size"].sum() ** 2 * G / max(G - 1, 1); return mu, mu / np.sqrt(v), G
mu, t, G = ctt(A, "r"); emu, et, _ = ctt(A, "ex")
tr, va = A[A.date < "2025-09-01"].r.mean(), A[A.date >= "2025-09-01"].r.mean()
bt = A.groupby("dtype").r.agg(["size", "mean"])
mo = A.groupby(A.date.str[:7]).r.sum(); wf = (mo > 0).mean()
d = A.groupby("date").r.sum(); wob = (d.sum() - d.max()) / (len(A) - (A.date == d.idxmax()).sum()); share = d.max() / d.sum() if d.sum() > 0 else np.nan
ok = bool(len(A) >= 200 and G >= 20 and t >= BAR and tr > 0 and va > 0 and bt.loc["up", "mean"] > 0 and bt.loc["down", "mean"] > 0 and et > 0 and wf >= 0.54)
P = [f"MH1105-P1: liquid 09:50 short rows {len(F)} on {F.date.nunique()} days (all-row avg {F.r.mean():+.3f}R); class n {len(A)} on {G} days",
     f"  avg R {mu:+.3f} (day-t {t:+.2f}, Testing bar {BAR:.2f}); excess over same-day 09:50 shorts {emu:+.3f} (t {et:+.2f})",
     f"  TRAIN {tr:+.3f} (n {(A.date < '2025-09-01').sum()}) | VALID {va:+.3f} (n {(A.date >= '2025-09-01').sum()}); WF positive months {wf:.0%} ({len(mo)})",
     "  by SPY day type: " + "; ".join(f"{k} n {int(r['size'])} {r['mean']:+.3f}" for k, r in bt.iterrows()),
     f"  avg R w/o best day {wob:+.3f} (best day {d.idxmax()} share {share:.0%})",
     f"  PASS {ok}", "", "Educational only - not financial advice."]
print("\n".join(P)); (HERE / "mh_p1_out.txt").write_text("\n".join(P) + "\n")
