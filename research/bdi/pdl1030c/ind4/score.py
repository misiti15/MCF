"""pdl1030c/ind4 scoring of the 14 pre-declared configs (PLAN.md). TRAIN+VALID only.
Educational only - not financial advice."""
import os, sys, math
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates
D = Path(__file__).resolve().parent
C = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030c/ind4/cache")
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

def stats(o, rcol, npar):
    o = o[np.isfinite(o[rcol])].rename(columns={rcol: "r"})
    res = {}
    for sp in ("train", "valid"):
        s = gates.summary(o[o.split == sp][["date", "r"]])
        res[f"avg_{sp}"], res[f"n_{sp}"] = s["exp_r"], s["n"]
    s = gates.summary(o[["date", "r"]])
    g = o.groupby("date")["r"].sum()
    res.update(n_tv=s["n"], avg_tv=s["exp_r"], t_tv=s["t"], ex_best=s["ex_best_day"],
               best_share=round(float(g.max() / g.sum()), 3) if g.sum() > 0 else None,
               per_session=round(s["n"] / NSESS, 1), kept_pct=round(100 * s["n"] / npar, 1))
    res["up_day_r"] = round(float(o[o.spy_day > 0].r.mean()), 4)
    res["down_day_r"] = round(float(o[o.spy_day < 0].r.mean()), 4)
    res["wf_pct"] = round(float((o.groupby("month")["r"].mean() > 0).mean() * 100), 1)
    # top-5 sessions: share of total R and avg R without the top 5 (owner: is the record more than its best days?)
    top5 = g.sort_values(ascending=False).head(5)
    res["top5_share"] = round(float(top5.sum() / g.sum()), 3) if g.sum() > 0 else None
    rest = o[~o.date.isin(top5.index)]
    res["ex_top5"] = round(float(rest.r.mean()), 4)
    return res

S = {s: T[T.setup == s] for s in ("p05", "p05lv")}
PAR = {}
print(f"sessions {NSESS}  N {N}  BAR {BAR:.3f}")
for s in S:
    st = stats(S[s], "r_P", len(S[s])); PAR[s] = st
    print("PARITY", s, "P", st["avg_train"], st["avg_valid"], st["avg_tv"], st["n_tv"], st["per_session"], st["t_tv"], st["ex_best"])
    st3 = stats(S[s], "r_S3", len(S[s])); print("PARITY", s, "S3", st3["avg_train"], st3["avg_valid"], st3["avg_tv"])
par_ok = (abs(PAR["p05"]["avg_train"] + 0.0677) <= 0.0005 and abs(PAR["p05"]["avg_valid"] + 0.0675) <= 0.0005
          and abs(PAR["p05lv"]["avg_tv"] + 0.0950) <= 0.0005)
print("parity_ok", par_ok)
assert par_ok

IND = [
    ("G1", lambda t: t.gap <= -2.657, "gap <= -2.657% (L3 cut)"),
    ("G2", lambda t: t.gap > 0, "gap > 0 (opened above prior close)"),
    ("G3", lambda t: t.gap_atr <= -0.41, "gap_atr <= -0.41 (AR-AM)"),
    ("M1", lambda t: t.sd > 0, "close above SMA50 (sd > 0)"),
    ("M2", lambda t: (t.sd > 0) & (t.sd_prev_close <= 0), "SMA50 cross up on signal bar"),
    ("M3", lambda t: t.sd < 0, "close below SMA50 (sd < 0)"),
]
c5 = lambda t: (t.cost_rt_R <= 0.05).to_numpy()

def passes(st, s):
    p = PAR[s]
    return bool(st["t_tv"] is not None and st["t_tv"] >= BAR and st["wf_pct"] >= 54 and st["avg_train"] > 0 and st["avg_valid"] > 0
                and st["avg_train"] > p["avg_train"] and st["avg_valid"] > p["avg_valid"] and st["per_session"] >= 25)

rows = []
for s, lab in (("p05", "p05"), ("p05lv", "lv")):
    t = S[s]; npar = len(t); cand = []
    for i, f, rule in IND:
        st = stats(t[f(t).to_numpy()], "r_P", npar); st.update(id=f"{i}-{lab}", setup=s, base="parent exits", rule=rule,
                                                              passes=passes(st, s)); rows.append(st); cand.append((i, f, rule, st))
    ok = [c for c in cand if c[3]["per_session"] >= 25] or cand
    bi, bf, brule, _ = max(ok, key=lambda c: c[3]["avg_train"])
    st = stats(t[c5(t) & bf(t).to_numpy()], "r_S3", npar)
    st.update(id=f"S-{lab}", setup=s, base="S3 + cost5", rule=f"{brule} (picked: {bi})", passes=passes(st, s)); rows.append(st)
assert len(rows) == COUNT
for s in S:  # base references already scored elsewhere (Q08 / ind1 B-lv): printed for context, not counted
    st = stats(S[s][c5(S[s])], "r_S3", len(S[s])); print("REF (not counted)", s, "S3+cost5", st["avg_train"], st["avg_valid"], st["t_tv"], st["per_session"])
R = pd.DataFrame(rows)[["id", "setup", "base", "rule", "avg_train", "avg_valid", "avg_tv", "t_tv", "n_tv", "per_session", "kept_pct",
                        "wf_pct", "up_day_r", "down_day_r", "ex_best", "best_share", "ex_top5", "top5_share", "passes"]]
R["bar_t"], R["N"] = round(BAR, 3), N
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 30)
print(R.to_string(index=False))
R.to_csv(D / "results.csv", index=False)
