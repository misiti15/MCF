"""pdl1030c/ind2 scoring of the 14 pre-declared configs (PLAN.md). TRAIN+VALID only.
Educational only - not financial advice."""
import os, sys, math
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates
D = Path(__file__).resolve().parent
C = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030c/ind2/cache")
T = pd.concat([pd.read_parquet(p) for p in sorted(C.glob("tr_*.parquet"))], ignore_index=True)
T = T[T["date"].astype(str) <= "2026-09-15"]
d = T["date"].astype(str)
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
T["month"] = d.str[:7]
T["split"] = np.where(d <= "2025-12-31", "train", "valid")
NSESS = T["date"].nunique()
COUNT = 14
N = 121635 + 5 * COUNT
BAR = max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(N))))
PAR = {"p05": dict(train=-0.0677, valid=-0.0675), "p05lv": dict(train=None, valid=None)}


def stats(o, rcol, npar):
    o = o[np.isfinite(o[rcol])].rename(columns={rcol: "r"})
    res = {}
    for sp in ("train", "valid"):
        s = gates.summary(o[o.split == sp][["date", "r"]])
        res[f"avg_{sp}"], res[f"n_{sp}"] = s["exp_r"], s["n"]
    s = gates.summary(o[["date", "r"]])
    g = o.groupby("date")["r"].sum().sort_values(ascending=False)
    tot = g.sum()
    res.update(n_tv=s["n"], avg_tv=s["exp_r"], t_tv=s["t"], ex_best=s["ex_best_day"],
               best_share=round(float(g.iloc[0] / tot), 3) if tot > 0 else None,
               top5_share=round(float(g.iloc[:5].sum() / tot), 3) if tot > 0 else None,
               ex_top5=round(float((tot - g.iloc[:5].sum()) / (len(o) - o[o.date.isin(g.index[:5])].shape[0])), 4),
               per_session=round(s["n"] / NSESS, 1), kept_pct=round(100 * s["n"] / npar, 1))
    res["up_day_r"] = round(float(o[o.spy_day > 0].r.mean()), 4)
    res["down_day_r"] = round(float(o[o.spy_day < 0].r.mean()), 4)
    res["wf_pct"] = round(float((o.groupby("month")["r"].mean() > 0).mean() * 100), 1)
    return res


def passes(st, s):
    p = PAR[s]
    return bool(st["t_tv"] is not None and st["t_tv"] >= BAR and st["wf_pct"] >= 54 and st["avg_train"] > 0 and st["avg_valid"] > 0
                and st["avg_train"] > p["train"] and st["avg_valid"] > p["valid"] and st["per_session"] >= 25)


print(f"sessions {NSESS}  N {N}  BAR {BAR:.3f}")
SET = {s: T[T.setup == s] for s in ("p05", "p05lv")}
NPAR = {s: int(np.isfinite(SET[s].r_P).sum()) for s in SET}
c5 = lambda t: t.cost_rt_R <= 0.05
for s in SET:  # parity (not counted)
    st = stats(SET[s], "r_P", NPAR[s]); print("PARITY", s, st["avg_train"], st["avg_valid"], st["avg_tv"], st["n_tv"], st["per_session"],
                                              "t", st["t_tv"], "wf", st["wf_pct"], "exbest", st["ex_best"])
    PAR[s] = dict(train=st["avg_train"], valid=st["avg_valid"])
    st = stats(SET[s], "r_S3", NPAR[s]); print("PARITY S3", s, st["avg_train"], st["avg_valid"])
st = stats(SET["p05"][c5(SET["p05"]).to_numpy()], "r_S3", NPAR["p05"]); print("PARITY Q08", st["avg_train"], st["avg_valid"], st["per_session"], st["t_tv"])
IND = [("rsi<=30", lambda t: t.rsi <= 30), ("rsi<=40", lambda t: t.rsi <= 40), ("rsi>50", lambda t: t.rsi > 50),
       ("buyPressure>0", lambda t: t.bp > 0), ("flow3>0", lambda t: t.flow3 > 0), ("buyPressure<-0.25", lambda t: t.bp < -0.25)]
rows = []
for s, pre in (("p05", "A"), ("p05lv", "B")):
    t = SET[s]
    sub = []
    for i, (nm, f) in enumerate(IND, 1):
        st = stats(t[f(t).to_numpy()], "r_P", NPAR[s]); st.update(id=f"{pre}{i}", setup=s, indicator=nm.split("<")[0].split(">")[0],
                                                                   rule=f"{s} parent exits | {nm}", passes=passes(st, s))
        sub.append((st, f, nm)); rows.append(st)
    ok = [x for x in sub if x[0]["per_session"] >= 25] or sub
    best = max(ok, key=lambda x: x[0]["avg_train"])
    f = best[1]
    st = stats(t[(c5(t) & f(t)).to_numpy()], "r_S3", NPAR[s])
    st.update(id=f"{pre}7", setup=s, indicator=best[2].split("<")[0].split(">")[0], rule=f"{s} S3 + cost5 | {best[2]} (best of {pre}1-{pre}6 by TRAIN)",
              passes=passes(st, s))
    rows.append(st)
assert len(rows) == COUNT
R = pd.DataFrame(rows)[["id", "setup", "rule", "avg_train", "avg_valid", "avg_tv", "t_tv", "n_tv", "per_session", "kept_pct", "wf_pct",
                        "up_day_r", "down_day_r", "ex_best", "best_share", "top5_share", "ex_top5", "passes"]]
R["bar_t"], R["N"] = round(BAR, 3), N
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 30)
print(R.to_string(index=False))
R.to_csv(D / "results.csv", index=False)
