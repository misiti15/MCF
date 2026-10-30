"""rdt1030/F1 scoring: every pre-declared row (and any dated rework row), long and short, TRAIN+VALID only.
Educational only - not financial advice."""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates  # noqa
D = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F1")
NAMES = {
    "F1-A": "15-min Opening Range Break with Gap (as posted)",
    "F1-B": "15-min ORB with Gap, small gap allowed (0.02 ATR)",
    "F1-C": "15-min ORB with Gap, big gap required (0.10 ATR)",
    "F1-D": "15-min ORB with Gap, 2R on tight stops (<= 0.20 ATR)",
    "F1-E": "15-min ORB with Gap, fixed 1R target",
    "F1-F": "15-min ORB with Gap, fixed 2R target",
    "F1-G": "15-min ORB with Gap, skip if costs > 10% of risk",
    "F1-H": "15-min ORB with Gap, late gap allowed (3 bars)",
    "F1-I": "15-min ORB with Gap, all-day window (to 15:00)",
}
RULES = {
    "F1-A": "First close beyond the 09:30-09:45 range forms a 5-min FVG (>=0.05 ATR); enter at that close, stop at FVG candle 1, 2R if risk<=0.085 ATR else 1R; 09:55-11:00",
    "F1-B": "F1-A with FVG >= 0.02 ATR", "F1-C": "F1-A with FVG >= 0.10 ATR",
    "F1-D": "F1-A with the 2R switch at risk <= 0.20 ATR", "F1-E": "F1-A, always 1R", "F1-F": "F1-A, always 2R",
    "F1-G": "F1-A, skip if round-trip cost > 10% of R", "F1-H": "F1-A, FVG may complete up to 3 bars after the break",
    "F1-I": "F1-A, signals to 15:00",
}
SWARM_DECLARED = 108
REWORK = json.loads((D / "rework.json").read_text()) if (D / "rework.json").exists() else {}
N = 2000 + SWARM_DECLARED + len(REWORK) * 2
BAR = 0.9 * max(1.5, math.sqrt(2 * math.log(N)))
SIDE = {"L": "long", "S": "short"}


def load():
    T = pd.concat([pd.read_parquet(p) for p in sorted(SCR.glob("tr_*.parquet")) + sorted(SCR.glob("rw_*.parquet"))], ignore_index=True)
    meta = json.loads((SCR / "meta.json").read_text())
    d = T["date"].astype(str)
    assert (d <= "2026-09-15").all()
    assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
    T["date"] = d; T["month"] = d.str[:7]; T["split"] = np.where(d <= "2025-12-31", "train", "valid")
    return T, sum(m["sessions"] for m in meta), sorted(m["month"] for m in meta)


def tday(dates, r):
    if len(r) < 2:
        return np.nan
    mu = r.mean(); g = pd.Series(r - mu).groupby(dates).sum()
    se = math.sqrt((g ** 2).sum()) / len(r)
    return mu / se if se > 0 else np.nan


def stats(t, nsess, months):
    r = t["r"].to_numpy(float); dates = t["date"].to_numpy()
    s = {"n": len(r), "trades_per_session": round(len(r) / nsess, 2)}
    if not len(r):
        return s
    w, lo = r[r > 0], r[r <= 0]
    s["win_rate"] = round(len(w) / len(r), 3)
    s["avg_win_R"] = round(w.mean(), 3) if len(w) else np.nan
    s["avg_loss_R"] = round(-lo.mean(), 3) if len(lo) else np.nan
    s["win_loss_ratio"] = round(s["avg_win_R"] / s["avg_loss_R"], 3) if len(w) and len(lo) else np.nan
    for sp in ("train", "valid"):
        m = (t["split"] == sp).to_numpy()
        s[f"avg_{sp}"] = round(r[m].mean(), 4) if m.any() else np.nan
        s[f"t_{sp}"] = round(tday(dates[m], r[m]), 2)
    s["avg_all"] = round(r.mean(), 4); s["t_day"] = round(tday(dates, r), 2)
    wf = gates.walk_forward(t[["date", "r"]], months=months)
    s["wf_pct"] = round(100 * wf["share_positive"], 1) if wf["share_positive"] is not None else np.nan
    mo = t.groupby("month")["r"].mean()
    s["months_pos_pct"] = round(100 * (mo > 0).mean(), 1)
    sd = t["spy_day"].to_numpy(float)
    s["up_day_r"] = round(r[sd > 0].mean(), 4); s["down_day_r"] = round(r[sd < 0].mean(), 4)
    s["up_day_r_big"] = round(r[sd >= 0.25].mean(), 4); s["flat_day_r"] = round(r[np.abs(sd) < 0.25].mean(), 4)
    s["down_day_r_big"] = round(r[sd <= -0.25].mean(), 4)
    day = t.groupby("date")["r"].agg(["sum", "size"])
    b = day["sum"].idxmax()
    s["avg_r_wo_best_day"] = round((day["sum"].sum() - day.loc[b, "sum"]) / (day["size"].sum() - day.loc[b, "size"]), 4)
    tot = day["sum"].sum()
    s["best_day"] = b; s["best_day_share"] = round(day.loc[b, "sum"] / tot, 3) if tot > 0 else np.nan
    s["busiest_session_share"] = round(day["size"].max() / len(r), 3)
    s["median_cost_R"] = round(float(t["cost_R"].median()), 3)
    cd = t["code"].value_counts(normalize=True)
    s["exit_target"], s["exit_stop"], s["exit_be"], s["exit_1555"] = (round(float(cd.get(k, 0)), 3) for k in (1, 2, 3, 6))
    s["share_2R"] = round(float((t["up"] == 2).mean()), 3)
    s["ctrl_avg_r"] = round(float(np.nanmean(t["ctrl"])), 4)
    s["edge_vs_ctrl"] = round(s["avg_all"] - s["ctrl_avg_r"], 4)
    s["gross_avg_r_est"] = round(s["avg_all"] + float(t["cost_R"].mean()), 4)
    return s


def passes(s):
    return bool(np.isfinite(s.get("t_day", np.nan)) and s["t_day"] >= BAR and s["wf_pct"] >= 54 and s["avg_train"] > 0
                and s["avg_valid"] > 0 and s["trades_per_session"] >= 3 and s["up_day_r"] > 0 and s["down_day_r"] > 0
                and s["avg_all"] > s["ctrl_avg_r"])


def main():
    T, nsess, months = load()
    rows = []
    for (cid, sn), t in T.groupby(["cfg", "side"], sort=True):
        s = stats(t, nsess, months)
        nm = NAMES.get(cid) or REWORK.get(cid, {}).get("name", cid)
        s.update(id=f"{cid}-{sn}", name=f"{nm}, {'Long' if sn == 'L' else 'Short'}", side=SIDE[sn],
                 rule=RULES.get(cid) or REWORK.get(cid, {}).get("rule", ""), rework=cid in REWORK)
        s["passes_bar"] = passes(s)
        rows.append(s)
    R = pd.DataFrame(rows)
    R["N"], R["bar_t"], R["sessions"] = N, round(BAR, 3), nsess
    lead = ["id", "name", "side", "passes_bar", "n", "trades_per_session", "avg_train", "avg_valid", "avg_all", "t_day", "wf_pct",
            "months_pos_pct", "win_rate", "avg_win_R", "avg_loss_R", "win_loss_ratio", "up_day_r", "down_day_r",
            "avg_r_wo_best_day", "best_day_share", "ctrl_avg_r"]
    R = R[lead + [c for c in R.columns if c not in lead]]
    R.to_csv(D / "results.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_columns", 60)
    print(f"sessions {nsess}  N {N}  bar_t {BAR:.3f}")
    print(R[lead].to_string(index=False))
    print(R[["id", "t_train", "t_valid", "up_day_r_big", "flat_day_r", "down_day_r_big", "busiest_session_share", "median_cost_R",
             "gross_avg_r_est", "exit_target", "exit_stop", "exit_1555", "share_2R", "edge_vs_ctrl", "best_day"]].to_string(index=False))


if __name__ == "__main__":
    main()
