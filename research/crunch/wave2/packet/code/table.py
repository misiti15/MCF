"""Every live setup -> TABLE.md (one line each). Educational only - not financial advice."""
import pandas as pd, numpy as np
R = pd.read_csv("scores.csv")
order = ["Primary", "On Deck", "Testing A", "Testing B", "Testing C", "Testing D", "Testing E", "Testing F", "Setup Generator", "Graveyard"]
R["o"] = R.account.map({a: i for i, a in enumerate(order)})
f = lambda v, d=3: "" if pd.isna(v) else f"{v:+.{d}f}"
def share(x):
    if pd.isna(x.best_share): return "n/a"
    return f"{x.best_share:.0%}" + (" `1 day`" if x.best_share >= 0.5 else "")
def verdict(x):
    v = []
    if x.acct == "primary": v.append("demote −10R" if x.demote10 else "keep (≥ −10R)")
    if isinstance(x.bar2, str) and x.bar2: v.append("BAR2 " + x.bar2 + ("" if x.bar2 == "READY" else f" ({x.bar2_fails})"))
    if isinstance(x.footrace_exit, str) and x.footrace_exit: v.append("FOOTRACE " + x.footrace_exit)
    if x.acct == "graveyard": v.append("GY grad" if x.gy_grad else "")
    if x.tag == "GY-BENCH guest": v.append("guest")
    return "; ".join(a for a in v if a)
L = ["Educational only — not financial advice", "",
     "# Every live setup — Friday review packet table (live run 1, 10-06..11-19, LR8 basis)", "",
     "Primary rows: record in Primary since admission. Other rows: live record outside Primary, identical signals counted once. "
     "Account R = LR8 $ ÷ 0.25% of the account's equity (UNIT1; testing lots are half size since 11-17, TSZ1). "
     "t = day-clustered t (mean of per-day mean R / SE); try-count bar " + f"{R.t_bar.iloc[0]:.2f}" + " (N = setups with trades). "
     "Shrunk = n/(n+150)·avg + 150/(n+150)·(−0.10). 0-trade setups are listed at the end.", "",
     "| Setup | Account | n | Act. days | Trade R | Avg R | Avg R w/o best day | Best-day share | t (bar) | Shrunk | Account R | $ (LR8) | 11-19 R | Verdict |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
X = R[R.n.fillna(0) > 0].sort_values(["o", "totR"], ascending=[True, False])
for _, x in X.iterrows():
    L.append(f"| {x.setup} | {x.account} | {int(x.n)} | {int(x.active_days)} | {x.totR:+.1f} | {f(x.avgR)} | {f(x.wo_best)} | {share(x)} | "
             f"{x.t_day:+.2f} | {f(x.shrunk)} | {x.acctR:+.2f} | {x.usd:+,.0f} | {f(x.d1119, 2)} | {verdict(x)} |")
Z = R[R.n.fillna(0) == 0]
L += ["", f"**0 live trades ({len(Z)}):** " + "; ".join(f"{a}: " + ", ".join(g.setup) for a, g in Z.groupby("account")), "",
      "Educational only — not financial advice"]
open("TABLE.md", "w").write("\n".join(L) + "\n")
print(len(X), len(Z))
