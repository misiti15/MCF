"""rdt1030/F3 scoring: every pre-declared row (and any dated rework row), long and short, TRAIN+VALID only.
Educational only - not financial advice."""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.research import gates  # noqa
D = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F3")
NAMES = {
    "F3-A": "5-min Opening Range Break with Gap, break-even, 2 tries, QQQ context",
    "F3-B": "5-min ORB with Gap, BE, 2 tries, no index context",
    "F3-C": "5-min ORB with Gap, 2 tries, QQQ context, earlier break-even (+0.5R)",
    "F3-D": "5-min ORB with Gap, BE, QQQ context, one try only",
    "F3-E": "5-min ORB with Gap, BE, QQQ context, second try only after a loss",
    "F3-F": "5-min ORB with Gap, BE, 2 tries, QQQ context, 2R on tight stops (<= 0.20 ATR)",
    "F3-G": "5-min ORB with Gap, BE, 2 tries, QQQ context, fixed 2R target",
    "F3-H": "5-min ORB with Gap, BE, 2 tries, QQQ context, all-day window (to 15:00)",
    "F3-I": "5-min ORB with Gap, BE, 2 tries, SPY-VWAP context",
}
RULES = {
    "F3-A": "First close beyond the 09:30-09:35 range forms a 5-min FVG (>=0.05 ATR); enter at that close, stop at FVG candle 1, 2R if risk<=0.085 ATR else 1R, BE at +1R; QQQ on the trade side of its open; max 2/symbol-day (2nd after exit + close back inside + new break); 09:50-11:00",
    "F3-B": "F3-A without the QQQ gate", "F3-C": "F3-A with BE at +0.5R", "F3-D": "F3-A, max 1 trade/symbol-day",
    "F3-E": "F3-A, trade 2 only if trade 1 lost", "F3-F": "F3-A with the 2R switch at risk <= 0.20 ATR",
    "F3-G": "F3-A, always 2R (BE +1R)", "F3-H": "F3-A, signals to 15:00",
    "F3-I": "F3-A with SPY on the trade side of its VWAP instead of QQQ from open",
}
SWARM_DECLARED = 108
REWORK = json.loads((D / "rework.json").read_text()) if (D / "rework.json").exists() else {}
SWARM_REWORK = 12  # F1 6 + F2 6 rework configs declared before F3 scored
N = 2000 + SWARM_DECLARED + SWARM_REWORK + len(REWORK) * 2
BAR = 0.9 * max(1.5, math.sqrt(2 * math.log(N)))
SIDE = {"L": "long", "S": "short"}


def load():
    T = pd.concat([pd.read_parquet(p) for p in sorted(SCR.glob("tr_*.parquet")) + sorted(SCR.glob("rw_*.parquet"))], ignore_index=True)
    meta = json.loads((SCR / "meta_tr.json").read_text())  # same sessions as meta_rw
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
    s["trade2_share"] = round(float((t["tno"] == 2).mean()), 3)
    s["avg_r_trade1"] = round(float(t.loc[t["tno"] == 1, "r"].mean()), 4)
    s["avg_r_trade2"] = round(float(t.loc[t["tno"] == 2, "r"].mean()), 4) if (t["tno"] == 2).any() else np.nan
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
    # descriptive: both sides of each system together (not an extra config)
    B = []
    for cid, t in T.groupby("cfg", sort=True):
        b = stats(t, nsess, months)
        B.append({"cfg": cid, "n": b["n"], "per_sess": b["trades_per_session"], "avg_all": b["avg_all"], "t_day": b["t_day"],
                  "avg_train": b["avg_train"], "avg_valid": b["avg_valid"], "wf_pct": b["wf_pct"], "up": b["up_day_r"],
                  "down": b["down_day_r"], "ctrl": b["ctrl_avg_r"], "trade2_share": b["trade2_share"]})
    B = pd.DataFrame(B); B.to_csv(D / "both_sides_descriptive.csv", index=False)
    print("both sides (descriptive, not a config):"); print(B.to_string(index=False))
    print(R[["id", "trade2_share", "avg_r_trade1", "avg_r_trade2", "exit_be"]].to_string(index=False))
    print(R[["id", "t_train", "t_valid", "up_day_r_big", "flat_day_r", "down_day_r_big", "busiest_session_share", "median_cost_R",
             "gross_avg_r_est", "exit_target", "exit_stop", "exit_1555", "share_2R", "edge_vs_ctrl", "best_day"]].to_string(index=False))


if __name__ == "__main__":
    main()
