"""rdt1030 / F5 scoring of the pre-declared rows (PLAN.md) on the build.py trade cache. TRAIN+VALID only.
stats/passes/fails copied verbatim from F2/score.py. Educational only - not financial advice.

    RDT_N_SWARM=<configs in swarm> python research/bdi/rdt1030/F5/score.py
"""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates  # noqa
D = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F5")
T = pd.concat([pd.read_parquet(p) for p in sorted(SCR.glob("tr_*.parquet"))], ignore_index=True)
d = T["date"].astype(str)
assert (d <= "2026-09-15").all()
assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
T["month"] = d.str[:7]; T["split"] = np.where(d <= "2025-12-31", "train", "valid")
NSESS = T.loc[T.base == "F1A", "date"].nunique()
N_SWARM = int(os.environ.get("RDT_N_SWARM", 137))  # 108 DESIGN + 24 rework rows (F1, F2, F3, F4: 6 each) + F5 rework
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



REWORK_NAMES = {"RW1": "Very Strong Move From Open (rework)", "RW2": "Order Flow + Low Cost (rework)",
                "RW3": "Above VWAP + Buyers In Control (rework)"}
REWORK_RULES = {"RW1": "(close - open)/ATR_d >= +0.50 / <= -0.50", "RW2": "I4 + round-trip cost <= 10% of R", "RW3": "J1 + J2"}

def ind(X, s, g):
    sg = 1 if s == "L" else -1
    v = lambda k: X[k].to_numpy(float)
    with np.errstate(invalid="ignore"):
        G = {"I1": sg * v("vwapDistPct") > 0,
             "I2": (v("rsi") >= 55) if sg == 1 else (v("rsi") <= 45),
             "I3": (v("rsi5") <= 90) if sg == 1 else (v("rsi5") >= 10),
             "I4": (v("buyPressure") >= 0.20) if sg == 1 else (v("buyPressure") <= -0.20),
             "I5": (v("mfo_atr") >= 0.30) if sg == 1 else (v("mfo_atr") <= -0.30),
             "I6": sg * v("sma50_dist_pct") > 0,
             "I7": (v("heat") >= 10) if sg == 1 else (v("heat") <= -20),
             "I8": (v("breadth") >= 0.60) if sg == 1 else (v("breadth") <= 0.40),
             "J1": v("vwapDistPct") > 0, "J2": v("buyPressure") >= 0.20}
    G.update(REWORK(X, sg, G))
    return np.asarray(G[g], bool)


def REWORK(X, sg, G):
    v = lambda k: X[k].to_numpy(float)
    with np.errstate(invalid="ignore"):
        rw1 = (v("mfo_atr") >= 0.50) if sg == 1 else (v("mfo_atr") <= -0.50)
        low = v("cost_rt_R") <= 0.10
    return {"RW1": rw1, "RW2": np.asarray(G["I4"], bool) & low, "RW3": np.asarray(G["J1"], bool) & np.asarray(G["J2"], bool)}


COL = {"RW1": "mfo_atr", "RW2": "buyPressure", "RW3": "vwapDistPct", "I1": "vwapDistPct", "I2": "rsi", "I3": "rsi5", "I4": "buyPressure", "I5": "mfo_atr", "I6": "sma50_dist_pct",
       "I7": "heat", "I8": "breadth", "J1": "vwapDistPct", "J2": "buyPressure"}
DEF = {"I1": ("vwapDistPct > 0 / < 0", "VWAP Side"), "I2": ("rsi >= 55 / <= 45", "RSI Momentum"),
       "I3": ("rsi5 <= 90 / >= 10", "Not Overextended (RSI5)"), "I4": ("buyPressure >= +0.20 / <= -0.20", "Order Flow With You"),
       "I5": ("(close - open)/ATR_d >= +0.30 / <= -0.30", "Strong Move From Open"), "I6": ("sma50_dist_pct > 0 / < 0", "Above/Below SMA50"),
       "I7": ("heat >= +10 / <= -20", "MarcoFlow Heat"), "I8": ("breadth >= 0.60 / <= 0.40", "Market Breadth"),
       "J1": ("vwapDistPct > 0", "Above VWAP"), "J2": ("buyPressure >= +0.20", "Buyers In Control")}
SIDE_NAME = {"L": "Long", "S": "Short"}
ROWS = [(f"F5-{g}-{s}", "F1A", g, s) for g in ("I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8") for s in ("L", "S")] + \
       [("F5-J1-L", "F401", "J1", "L"), ("F5-J2-L", "F401", "J2", "L")]
ROWS += [("F5-RW1-L", "F1A", "RW1", "L"), ("F5-RW1-S", "F1A", "RW1", "S"), ("F5-RW2-L", "F1A", "RW2", "L"),
         ("F5-RW2-S", "F1A", "RW2", "S"), ("F5-RW3-L", "F401", "RW3", "L")]
BASENAME = {"F1A": ("F1-A", "15-min Opening Range Break with Gap"), "F401": ("F4-01", "Prior-Day-Low Sweep then 15-min Gap")}

if __name__ == "__main__":
    print(f"sessions {NSESS}  N {N}  t_req {BAR:.3f}")
    out = []
    base = {}
    for b, s in (("F1A", "L"), ("F1A", "S"), ("F401", "L")):
        X = T[(T.base == b) & (T.side == s)].reset_index(drop=True)
        base[(b, s)] = X
        st = stats(X)
        st.update(id=f"{BASENAME[b][0]}-{s}", name=f"{BASENAME[b][1]}, {SIDE_NAME[s]} (base, reference)", rule="base entry, no indicator",
                  side=s, counted=False, passes_bar=passes(st), fail_reasons=fails(st))
        out.append(st)
    for rid, b, g, s in ROWS:
        X = base[(b, s)]
        m = ind(X, s, g)
        st = stats(X[m])
        pr = X["r"].to_numpy(float); top = pr >= np.nanquantile(pr, 0.9)
        st["kept_trades_pct"] = round(100 * m.mean(), 1)
        st["kept_top_decile_pct"] = round(100 * (m & top).sum() / top.sum(), 1)
        st["ind_coverage_pct"] = round(100 * float(np.isfinite(X[COL.get(g, "vwapDistPct")].to_numpy(float)).mean()), 1)
        nm = DEF[g][1] if g in DEF else REWORK_NAMES.get(g, g)
        st.update(id=rid, name=f"{BASENAME[b][1]} + {nm}, {SIDE_NAME[s]}", rule=f"{BASENAME[b][0]} + {DEF[g][0] if g in DEF else REWORK_RULES.get(g, g)}",
                  side=s, counted=True, passes_bar=passes(st), fail_reasons=fails(st))
        out.append(st)
    R = pd.DataFrame(out)
    R["bar_t"], R["N"] = round(BAR, 3), N
    cols = ["id", "name", "rule", "side", "counted", "passes_bar", "fail_reasons", "n", "trades_per_session", "win_rate", "avg_win_R", "avg_loss_R",
            "win_loss_ratio", "avg_r", "avg_train", "avg_valid", "t_day", "wf_pct", "wf_folds", "months_pos_pct", "up_day_r", "flat_day_r", "down_day_r",
            "up_gt25_r", "down_lt25_r", "avg_r_wo_best_day", "best_day_share", "best_day", "busiest_session_share", "med_cost_R",
            "x_target", "x_stop", "x_be", "x_1555", "share_2R", "ctrl_avg_r", "beats_ctrl", "kept_trades_pct", "kept_top_decile_pct",
            "ind_coverage_pct", "bar_t", "N"]
    R = R[[c for c in cols if c in R.columns]]
    pd.set_option("display.width", 320); pd.set_option("display.max_columns", 60)
    print(R.drop(columns=["name", "rule"]).to_string(index=False))
    R.to_csv(D / os.environ.get("F5_OUT", "results.csv"), index=False)
