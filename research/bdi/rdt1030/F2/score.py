"""rdt1030 / F2 scoring of the pre-declared rows (PLAN.md) on the build.py trade cache. TRAIN+VALID only.
Educational only - not financial advice.

    python research/bdi/rdt1030/F2/score.py [extra_rows]
"""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates  # noqa
D = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F2")
T = pd.concat([pd.read_parquet(p) for p in sorted(SCR.glob("tr_*.parquet"))], ignore_index=True)
d = T["date"].astype(str)
assert (d <= "2026-09-15").all()
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
T["month"] = d.str[:7]; T["split"] = np.where(d <= "2025-12-31", "train", "valid")
NSESS = T["date"].nunique()
N_SWARM = int(os.environ.get("RDT_N_SWARM", 108 + 6))  # 108 DESIGN + 6 F2 rework rows (PLAN amendment)
N = 2000 + N_SWARM
BAR = 0.9 * max(1.5, math.sqrt(2 * math.log(N)))


def stats(df):
    df = df[np.isfinite(df["r"].to_numpy(float))]
    r = df["r"].to_numpy(float); dates = df["date"].to_numpy()
    res = {"n": len(df), "trades_per_session": round(len(df) / NSESS, 2)}
    if not len(df):
        return res
    for sp in ("train", "valid"):
        m = (df["split"] == sp).to_numpy()
        res[f"avg_{sp}"] = round(float(r[m].mean()), 4) if m.any() else np.nan
    mu = float(r.mean())
    g = pd.Series(r - mu).groupby(dates).sum()
    se = float(np.sqrt((g ** 2).sum()) / len(r))
    res["avg_r"] = round(mu, 4); res["t_day"] = round(mu / se, 2) if se > 0 else np.nan
    w, lo = r[r > 0], r[r < 0]
    res["win_rate"] = round(float((r > 0).mean()), 3)
    res["avg_win_R"] = round(float(w.mean()), 3) if len(w) else np.nan
    res["avg_loss_R"] = round(float(-lo.mean()), 3) if len(lo) else np.nan
    res["win_loss_ratio"] = round(res["avg_win_R"] / res["avg_loss_R"], 3) if len(w) and len(lo) else np.nan
    wf = gates.walk_forward(df[["date", "r"]])
    res["wf_pct"] = round(100 * wf["share_positive"], 1) if wf["share_positive"] is not None else np.nan
    res["wf_folds"] = wf["n_folds"]
    mo = pd.Series(r).groupby(df["month"].to_numpy()).mean()
    res["months_pos_pct"] = round(float((mo > 0).mean() * 100), 1)
    sd = df["spy_day"].to_numpy(float)
    for nm, m in (("up_day_r", sd > 0), ("down_day_r", sd < 0), ("flat_day_r", np.abs(sd) <= 0.25),
                  ("up_gt25_r", sd > 0.25), ("down_lt25_r", sd < -0.25)):
        res[nm] = round(float(r[m].mean()), 4) if m.any() else np.nan
    day = pd.Series(r).groupby(dates).agg(["sum", "size"])
    b = day["sum"].idxmax()
    res["avg_r_wo_best_day"] = round(float((day["sum"].sum() - day.loc[b, "sum"]) / (day["size"].sum() - day.loc[b, "size"])), 4)
    tot = day["sum"].sum()
    res["best_day_share"] = round(float(day.loc[b, "sum"] / tot), 3) if tot > 0 else np.nan
    res["best_day"] = str(b)
    res["busiest_session_share"] = round(float(day["size"].max() / len(df)), 3)
    res["med_cost_R"] = round(float(df["cost_rt_R"].median()), 3)
    cd = df["code"].to_numpy()
    for nm, k in (("x_target", 1), ("x_stop", 2), ("x_be", 3), ("x_1555", 6)):
        res[nm] = round(float((cd == k).mean()), 3)
    res["share_2R"] = round(float((df["up"] == 2).mean()), 3)
    cr = df["ctrl_r"].to_numpy(float)
    res["ctrl_avg_r"] = round(float(np.nanmean(cr)), 4)
    res["beats_ctrl"] = bool(mu > np.nanmean(cr))
    return res


def passes(s):
    return bool(s.get("n", 0) and np.isfinite(s["t_day"]) and s["t_day"] >= BAR and s["wf_pct"] >= 54 and s["avg_train"] > 0
                and s["avg_valid"] > 0 and s["trades_per_session"] >= 3 and s["up_day_r"] > 0 and s["down_day_r"] > 0 and s["beats_ctrl"])


def fails(s):
    f = []
    if not (s["t_day"] >= BAR): f.append(f"t {s['t_day']}<{BAR:.2f}")
    if not (s["wf_pct"] >= 54): f.append("WF<54")
    if not (s["avg_train"] > 0): f.append("TRAIN<=0")
    if not (s["avg_valid"] > 0): f.append("VALID<=0")
    if not (s["trades_per_session"] >= 3): f.append("<3/session")
    if not (s["up_day_r"] > 0): f.append("up-day<=0")
    if not (s["down_day_r"] > 0): f.append("down-day<=0")
    if not s["beats_ctrl"]: f.append("<=control")
    return "; ".join(f)


L = T[T.side == "L"].reset_index(drop=True); S = T[T.side == "S"].reset_index(drop=True)
for X in (L, S):
    X["opp_before"] = X["opp_before"].astype(float)


def gate(X, side, g):
    sg = 1 if side == "L" else -1
    q = X["qqq_fo"].to_numpy(float)
    G = {"G1": X.orw >= 0.30, "G2": X.orw <= 0.55, "G3": X.er >= 0.40,
         "G4": (q >= 0.20) if sg == 1 else (q <= -0.20), "G5": X.spy_er >= 0.40, "G6": X.g6 == 1,
         "G7": X.vr >= 1.0, "G8": X.opp_before == 0}
    G["G9"] = G["G3"] & G["G4"]
    # extra (rework) gates are added in REWORK below
    G.update(REWORK_GATES(X, sg))
    return np.asarray(G[g], bool)


def REWORK_GATES(X, sg):
    g6 = np.asarray(X.g6 == 1)
    return {"RW1": g6 & np.asarray(X.opp_before == 0), "RW2": g6 & np.asarray(X.orw >= 0.30),
            "RW3": g6 & np.asarray(X.cost_rt_R <= 0.05)}


GATES = {"G1": ("OR15 width >= 0.30 ATR", "Active Open"), "G2": ("OR15 width <= 0.55 ATR", "Unspent Range"),
         "G3": ("stock ER >= 0.40", "Trending Stock"), "G4": ("QQQ from open >= +0.20% / <= -0.20%", "Nasdaq With You"),
         "G5": ("SPY ER >= 0.40", "Trending Market"), "G6": ("SPY prior-day range >= 20-day median", "Active Market Yesterday"),
         "G7": ("volumeRatio >= 1.0", "High Relative Volume"), "G8": ("no prior close beyond the other OR side", "Clean One-Way Open"),
         "G9": ("G3 + G4", "Trending Stock + Nasdaq With You"),
         "RW1": ("rework: G6 + G8", "Active Market Yesterday + Clean One-Way Open"),
         "RW2": ("rework: G6 + G1", "Active Market Yesterday + Active Open"),
         "RW3": ("rework: G6 + round-trip cost <= 5% of R", "Active Market Yesterday + Low Cost")}
SIDE_NAME = {"L": "Long", "S": "Short"}
ROWS = [(f"F2-{g}-{s}", g, s) for g in GATES for s in ("L", "S")]

if __name__ == "__main__":
    out = []
    par = T[T.side == "PAR"]
    pt = par[par.split == "train"].r.mean(); pv = par[par.split == "valid"].r.mean()
    parity = dict(train=round(float(pt), 4), valid=round(float(pv), 4), ok=bool(abs(pt + 0.0677) <= 0.002 and abs(pv + 0.0675) <= 0.002))
    print("PARITY (CWT14 PDL p05 parent, unpatched sim):", parity)
    print(f"sessions {NSESS}  N {N}  t_req {BAR:.3f}")
    base = {}
    for s, X in (("L", L), ("S", S)):
        st = stats(X); st.update(id=f"F1-A-{s}", name=f"15-min Opening Range Break with Gap, {SIDE_NAME[s]} (F1-A parent, reference)",
                                rule="F1-A as written", side=s, counted=False, passes_bar=passes(st), fail_reasons=fails(st))
        out.append(st); base[s] = X
    for rid, g, s in ROWS:
        X = base[s]
        m = gate(X, s, g)
        Y = X[m]
        st = stats(Y)
        pr = X["r"].to_numpy(float); top = pr >= np.nanquantile(pr, 0.9)
        st["kept_trades_pct"] = round(100 * m.mean(), 1)
        st["kept_top_decile_pct"] = round(100 * (m & top).sum() / top.sum(), 1)
        st["gate_coverage_pct"] = round(100 * float(np.isfinite(X[{"G1": "orw", "G2": "orw", "G3": "er", "G4": "qqq_fo", "G5": "spy_er", "G6": "g6", "G7": "vr", "G8": "opp_before", "G9": "er", "RW1": "g6", "RW2": "g6", "RW3": "g6"}.get(g, "orw")].to_numpy(float)).mean()), 1)
        rid = rid if not g.startswith("RW") else f"F2-{g}-{s}"
        st.update(id=rid, name=f"15-min Opening Range Break with Gap + {GATES[g][1]}, {SIDE_NAME[s]}", rule=f"F1-A + {GATES[g][0]}",
                  side=s, counted=True, passes_bar=passes(st), fail_reasons=fails(st))
        out.append(st)
    for s_, X in (("L", L), ("S", S)):
        print(f"F1-A-{s_} approx gross (r + entry/exit cost, stop slip ignored): {float((X.r + X.cost_rt_R).mean()):.4f}; control {float(X.ctrl_r.mean()):.4f}")
    R = pd.DataFrame(out)
    R["bar_t"], R["N"] = round(BAR, 3), N
    cols = ["id", "name", "rule", "side", "counted", "passes_bar", "fail_reasons", "n", "trades_per_session", "win_rate", "avg_win_R", "avg_loss_R",
            "win_loss_ratio", "avg_r", "avg_train", "avg_valid", "t_day", "wf_pct", "wf_folds", "months_pos_pct", "up_day_r", "flat_day_r", "down_day_r",
            "up_gt25_r", "down_lt25_r", "avg_r_wo_best_day", "best_day_share", "best_day", "busiest_session_share", "med_cost_R",
            "x_target", "x_stop", "x_be", "x_1555", "share_2R", "ctrl_avg_r", "beats_ctrl", "kept_trades_pct", "kept_top_decile_pct",
            "gate_coverage_pct", "bar_t", "N"]
    R = R[[c for c in cols if c in R.columns]]
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 60); pd.set_option("display.max_colwidth", 40)
    print(R.drop(columns=["name", "rule"]).to_string(index=False))
    R.to_csv(D / "results.csv", index=False)
    json.dump(parity, open(D / "parity.json", "w"))
