"""LL-LATCH: should the per-setup -2R daily stop latch for the day? Live mcf/execution/risk.py blocks a setup only while
its realized R(j) is <= -2R, so a later winner closing re-arms it. Reuses research/bdi/ll1020/replay.py's candidate set
(live run-1 trades + the signals the live limit blocked, priced by the journal what-if run less production costs; days
10-12..10-22; accounts with the limit: Testing 1, Testing 2, GEN, Graveyard) and its rules, and adds ONE configuration:
latch2 = once realized R(j) has touched -2R, no new entry that day. Compared with fixed2 (live) and fixed1.5 (LL-1.5).
Configurations tried tonight: 1 (latch2); protection lineage N 92 -> 93, bar sqrt(2 ln 93) = 3.01.
Writes latch_out.txt.  Usage: python latch.py <scratch>   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
SRC = Path("/home/user/MCF/research/bdi/ll1020/replay.py").read_text()
head = SRC[:SRC.index("RULES = {")].replace("C.drop(columns=[\"nt\", \"et\"]).to_csv(OUT / \"candidates.csv\", index=False)", "")
ns = {"__file__": str(Path(__file__).resolve()), "__name__": "latch"}
exec(compile(head, "replay_head", "exec"), ns)
C, make, realized, avg_tpd, LIM = ns["C"], ns["make"], ns["realized"], ns["avg_tpd"], ns["LIM"]

def latch(X):
    def f(t, tk, ctx):
        d = sorted((e, r) for (_, e, r) in tk if e < t); cum = 0.0
        for _, r in d:
            cum += r
            if cum <= -X:
                return False
        return True
    return f

RULES = {"none": make("none"), "fixed2": make("fixed", 2), "fixed1.5": make("fixed", 1.5), "latch2": latch(2)}
recs = []
for (a, d, st), g in C.groupby(["acct", "date", "strategy"], sort=False):
    if a not in LIM:
        continue
    ctx = {"tpd": avg_tpd(a, st, d)}
    for name, f in RULES.items():
        tk, net, blk = [], 0.0, 0
        for r in g.itertuples():
            if f(r.nt, tk, ctx):
                tk.append((r.nt, r.et, r.r_multiple)); net += r.netR
            else:
                blk += 1
        recs.append((name, a, d, st, len(tk), blk, net))
SD = pd.DataFrame(recs, columns=["rule", "acct", "date", "strategy", "taken", "blocked", "netR"])
PD = SD.groupby(["rule", "date"]).netR.sum().unstack()
D = PD.loc["latch2"] - PD.loc["fixed2"]
pd.set_option("display.width", 250)
o = ["net R after costs per day (t1+t2+gen+gy):", PD.round(2).to_string(), "",
     "latch2 - fixed2 per day:", D.round(2).to_string(),
     f"total {D.sum():+.2f}R over {len(D)} days; days better {(D > 0).sum()} / worse {(D < 0).sum()}; "
     f"day-clustered t {D.mean() / (D.std(ddof=1) / np.sqrt(len(D))):+.2f} (bar 3.01)",
     "", "by account (all days):", SD.groupby(["rule", "acct"]).netR.sum().unstack().round(2).to_string(),
     "", "entries taken by rule:", SD.groupby("rule").taken.sum().to_string()]
x = SD.pivot_table(index=["acct", "date", "strategy"], columns="rule", values="netR")
x["d"] = x.latch2 - x.fixed2
o += ["", "setup-days latch2 changes (vs fixed2):", x[x.d.abs() > 0.01].sort_values("d").round(2).to_string()]
txt = "\n".join(o)
(Path(__file__).resolve().parent / "latch_out.txt").write_text(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
