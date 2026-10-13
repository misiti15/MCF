"""longs1013 selection (PLAN.md section 3) from results.csv: finalists, plateau, Testing-1 bar, summary.json.
Split out of score.py (which wrote results.csv and then stopped on a column-type bug in the plateau lookup; no
configuration was re-scored). Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research import gates  # noqa: E402

N_STUDY = 580
N_Q1, N_Q2 = 96 + 9132, 484 + 30970
XS = (0.5, 0.75, 1.0)
res = pd.read_csv(HERE / "results.csv")
res["W"] = res["W"].astype("Int64")
res["d"] = res["d"].astype("Int64")
# ------------------------------------------------------------------------------------------------ plateau + selection
def plateau_q2(r):
    nb = []
    i = XS.index(r.x)
    for x2 in [XS[j] for j in (i - 1, i + 1) if 0 <= j < 3]:
        nb.append(f"Q2-{r.ref}-x{x2}-W{int(r.W)}-{r.trig}-{r.filt}-{r.exit}")
    nb.append(f"Q2-{r.ref}-x{r.x}-W{30 - int(r.W)}-{r.trig}-{r.filt}-{r.exit}")
    v = res.set_index("cfg").loc[nb, "open_exp"]
    return float(v.min())


def plateau_q1(r):
    ds = [d for d in (0, 1, 3) if d != r.d]
    v = res.set_index("cfg").loc[[f"Q1-{r.set}-long-d{int(d)}-{r.exit}" for d in ds], "open_exp"]
    return float(v.min())


fin = []
for q in ("Q1", "Q2"):
    x = res[(res.q == q) & (res.side == "long") & (res.train_n >= 150) & (res.train_exp > 0)].copy()
    x = x.sort_values("train_t", ascending=False)
    pick = list(x.head(5).cfg)
    if q == "Q2":
        for tg in ("RB", "VR", "HL"):
            y = x[x.trig == tg]
            if len(y) and y.iloc[0].cfg not in pick:
                pick.append(y.iloc[0].cfg)
    fin += pick
F2 = res[res.cfg.isin(fin)].copy()
F2["plateau"] = [plateau_q1(r) if r.q == "Q1" else plateau_q2(r) for r in F2.itertuples()]
rand = res[res.trig == "RANDOM"].set_index("exit")["open_exp"]
shortref = res[(res.q == "Q1") & (res.side == "short")].set_index(["set", "exit"])["open_exp"]


def bar(r):
    base = (r.open_n >= 150 and (r.open_exp or -1) > 0 and (r.open_t or 0) >= 1.5 and (r.train_exp or -1) > 0
            and (r.valid_exp or -1) > 0 and (r.ex_best or -1) > 0 and r.busiest <= 0.10 and r.excess > 0 and r.plateau > 0)
    if r.q == "Q2":
        return base and r.open_exp > rand[r.exit] + 0.05
    return base and r.open_exp > shortref[(r.set, r.exit)]


F2["testing_bar"] = [bar(r) for r in F2.itertuples()]
F2.to_csv(HERE / "finalists.csv", index=False)
summ = {"n_configs": int(len(res)), "n_study_declared": N_STUDY, "t_bar_study": gates.t_required(N_STUDY),
        "t_bar_q1": gates.t_required(N_Q1), "t_bar_q2": gates.t_required(N_Q2),
        "keep": int((res.verdict == "keep").sum()), "finalists": F2.cfg.tolist(),
        "testing_pass": F2[F2.testing_bar].cfg.tolist()}
json.dump(summ, open(HERE / "summary.json", "w"), indent=1)
print(json.dumps(summ, indent=1))
