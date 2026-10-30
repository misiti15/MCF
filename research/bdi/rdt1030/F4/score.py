"""rdt1030/F4 scoring: every pre-declared row (and any dated rework row), long and short, TRAIN+VALID only.
Educational only - not financial advice."""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates  # noqa
D = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F4")
NAMES = {
    "F4-01": "Prior-Day-Low Sweep then 15-min Gap (to liquidity)",
    "F4-02": "Prior-Day-Low Sweep then 15-min Gap (2R)",
    "F4-03": "Prior-Day-Low Sweep, buy the 15-min Gap retest (to liquidity)",
    "F4-04": "Prior-Day-Low Sweep, buy the 15-min Gap retest (2R)",
    "F4-05": "Opening-Range-Low Sweep then 15-min Gap (to liquidity)",
    "F4-06": "Opening-Range-Low Sweep then 15-min Gap (2R)",
    "F4-07": "Opening-Range-Low Sweep, buy the 15-min Gap retest (to liquidity)",
    "F4-08": "Opening-Range-Low Sweep, buy the 15-min Gap retest (2R)",
    "F4-09": "Prior-Day-High Sweep then 15-min Gap (to liquidity)",
    "F4-10": "Prior-Day-High Sweep then 15-min Gap (2R)",
    "F4-11": "Prior-Day-High Sweep, sell the 15-min Gap retest (to liquidity)",
    "F4-12": "Opening-Range-High Sweep then 15-min Gap (to liquidity)",
    "F4-13": "Opening-Range-High Sweep then 15-min Gap (2R)",
    "F4-14": "Prior-Day-Low Sweep + strong 15-min push (0.30 ATR) then Gap (to liquidity)",
    "F4-15": "Prior-Day-Low Sweep then big 15-min Gap (0.10 ATR) (to liquidity)",
    "F4-16": "Prior-Day-Low shallow sweep (any trade-through) then 15-min Gap (to liquidity)",
    "F4-17": "Prior-Day-Low Sweep then 15-min Gap (to liquidity), break-even at +1R",
}
_B = "sweep >=0.05 ATR through {lv}, 15-min displacement candle >= {d} ATR, first 15-min FVG (>= {g} ATR) after the sweep closing back through {lv} within 2h; "
_E = {"f": "enter at the FVG bar close (10:15-14:00)", "r": "limit at the FVG edge within 30 min"}
_T = {"D": ", stop beyond sweep extreme -0.02 ATR, target nearest liquidity >=1R (cap 4R) else 2R",
      "2": ", stop beyond sweep extreme -0.02 ATR, fixed 2R"}
RULES = {
    "F4-01": _B.format(lv="PDL", d=0.20, g=0.05) + _E["f"] + _T["D"], "F4-02": _B.format(lv="PDL", d=0.20, g=0.05) + _E["f"] + _T["2"],
    "F4-03": _B.format(lv="PDL", d=0.20, g=0.05) + _E["r"] + _T["D"], "F4-04": _B.format(lv="PDL", d=0.20, g=0.05) + _E["r"] + _T["2"],
    "F4-05": _B.format(lv="ORL", d=0.20, g=0.05) + _E["f"] + _T["D"], "F4-06": _B.format(lv="ORL", d=0.20, g=0.05) + _E["f"] + _T["2"],
    "F4-07": _B.format(lv="ORL", d=0.20, g=0.05) + _E["r"] + _T["D"], "F4-08": _B.format(lv="ORL", d=0.20, g=0.05) + _E["r"] + _T["2"],
    "F4-09": _B.format(lv="PDH", d=0.20, g=0.05) + _E["f"] + _T["D"], "F4-10": _B.format(lv="PDH", d=0.20, g=0.05) + _E["f"] + _T["2"],
    "F4-11": _B.format(lv="PDH", d=0.20, g=0.05) + _E["r"] + _T["D"],
    "F4-12": _B.format(lv="ORH", d=0.20, g=0.05) + _E["f"] + _T["D"], "F4-13": _B.format(lv="ORH", d=0.20, g=0.05) + _E["f"] + _T["2"],
    "F4-14": _B.format(lv="PDL", d=0.30, g=0.05) + _E["f"] + _T["D"], "F4-15": _B.format(lv="PDL", d=0.20, g=0.10) + _E["f"] + _T["D"],
    "F4-16": "F4-01 with the sweep = any trade-through of PDL", "F4-17": "F4-01 with break-even at +1R",
}
SWARM_DECLARED = 108
REWORK = json.loads((D / "rework.json").read_text()) if (D / "rework.json").exists() else {}
F1_REWORK = 6
N = 2000 + SWARM_DECLARED + F1_REWORK + len(REWORK)  # each F4 rework row is one config (one side)
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
    s["median_up"] = round(float(t["up"].median()), 2)
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
             "gross_avg_r_est", "median_up", "exit_target", "exit_stop", "exit_1555", "share_2R", "edge_vs_ctrl", "best_day"]].to_string(index=False))


if __name__ == "__main__":
    main()
