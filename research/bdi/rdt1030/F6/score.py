"""rdt1030/F6 scoring: every pre-declared row, TRAIN+VALID only. Statistics are ../F1/score.py stats() unchanged.
Educational only - not financial advice."""
import os, sys, math, json
for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[k] = "1"
import importlib.util
from pathlib import Path
import numpy as np, pandas as pd
D = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("rdt_f1_score", D.parent / "F1/score.py")
F1S = importlib.util.module_from_spec(spec); spec.loader.exec_module(F1S)
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rdt1030/F6")
# swarm count at score time: 108 declared + dated rework rows (F1 6, F2 6, F3 6, F4 6); override with RDT_N_SWARM
N_SWARM = int(os.environ.get("RDT_N_SWARM", 108 + 24))
N = 2000 + N_SWARM
BAR = 0.9 * max(1.5, math.sqrt(2 * math.log(N)))
F1S.BAR = BAR
NAMES = {
    "F6-01": "Nasdaq 15-min Opening Range Break with Gap, Long via TQQQ",
    "F6-02": "Nasdaq 15-min Opening Range Break with Gap, Short via SQQQ",
    "F6-03": "S&P 15-min Opening Range Break with Gap, Long via SPXL",
    "F6-04": "S&P 15-min Opening Range Break with Gap, Short via SPXS",
    "F6-05": "Nasdaq 15-min Opening Range Break with 1-min Gap, Long via TQQQ",
    "F6-06": "Nasdaq 15-min Opening Range Break with 1-min Gap, Short via SQQQ",
    "F6-07": "Nasdaq 5-min Opening Range Break with Gap, break-even, 2 tries, Long via TQQQ",
    "F6-08": "Nasdaq 5-min Opening Range Break with Gap, break-even, 2 tries, Short via SQQQ",
    "F6-09": "Nasdaq Prior-Day-Low Sweep then 15-min Gap, Long via TQQQ",
    "F6-10": "Nasdaq Prior-Day-High Sweep then 15-min Gap, Short via SQQQ",
    "F6-11": "Nasdaq Opening-Range-Low Sweep then 15-min Gap, Long via TQQQ",
    "F6-12": "Nasdaq Opening-Range-High Sweep then 15-min Gap, Short via SQQQ",
    "F6-13": "S&P Prior-Day-Low Sweep then 15-min Gap, Long via SPXL",
    "F6-14": "S&P Prior-Day-High Sweep then 15-min Gap, Short via SPXS",
    "F6-15": "Index ETFs (QQQ/SPY/TQQQ/SQQQ) 15-min Opening Range Break with Gap, Long",
    "F6-16": "Index ETFs (QQQ/SPY/TQQQ/SQQQ) 15-min Opening Range Break with Gap, Short",
    "F6-17": "Nasdaq 15-min Opening Range Break with Gap traded as QQQ, Long",
    "F6-18": "Nasdaq 15-min Opening Range Break with Gap traded as QQQ, Short",
}
RULES = {
    "F6-01": "F1-A on QQQ (first close beyond 09:30-09:45 range completes a 5-min FVG >= 0.05 ATR; stop FVG candle 1; 2R if risk <= 0.085 ATR else 1R; 09:55-11:00) traded in TQQQ, levels x3 by %",
    "F6-03": "F1-A on SPY traded in SPXL / SPXS, levels x3 by %",
    "F6-05": "F1-A with a 1-min FVG on QQQ (OR15 from 5-min rows; day skipped if the 09:50 5-min close is already beyond) traded in TQQQ / SQQQ",
    "F6-07": "F3-A on QQQ (09:30-09:35 range, FVG break entry, BE at +1R, QQQ-from-open context, max 2 trades/day) traded in TQQQ / SQQQ",
    "F6-09": "F4-01 / F4-09 on QQQ (PDL/PDH sweep >= 0.05 ATR, 15-min displacement >= 0.20 ATR, first 15-min FVG; stop beyond sweep; DOL target) traded in TQQQ / SQQQ",
    "F6-11": "F4-05 / F4-12 on QQQ (OR15 low/high sweep version) traded in TQQQ / SQQQ",
    "F6-13": "F4-01 / F4-09 on SPY traded in SPXL / SPXS",
    "F6-15": "F1-A on each of QQQ, SPY, TQQQ, SQQQ, traded as itself (shorts are real shorts)",
    "F6-17": "F1-A on QQQ traded as QQQ (unlevered reference)",
}
for a, b in (("F6-02", "F6-01"), ("F6-04", "F6-03"), ("F6-06", "F6-05"), ("F6-08", "F6-07"), ("F6-10", "F6-09"),
             ("F6-12", "F6-11"), ("F6-14", "F6-13"), ("F6-16", "F6-15"), ("F6-18", "F6-17")):
    RULES[a] = RULES[b]


def main():
    T = pd.concat([pd.read_parquet(p) for p in sorted(SCR.glob("tr_*.parquet"))], ignore_index=True)
    meta = json.loads((SCR / "meta.json").read_text())
    d = T["date"].astype(str)
    assert (d <= "2026-09-15").all()
    assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any() and not d.str[:7].isin(["2026-04", "2026-05", "2026-06", "2026-10"]).any()
    T["date"] = d; T["month"] = d.str[:7]; T["split"] = np.where(d <= "2025-12-31", "train", "valid")
    nsess = sum(m["sessions"] for m in meta); months = sorted(m["month"] for m in meta)
    rows = []
    for cid in sorted(NAMES):
        t = T[T["cfg"] == cid]
        s = F1S.stats(t, nsess, months) if len(t) >= 2 else {"n": len(t), "trades_per_session": round(len(t) / nsess, 3)}
        s.update(id=cid, name=NAMES[cid], side="long" if cid in {f"F6-{k:02d}" for k in range(1, 19, 2)} else "short",
                 rule=RULES[cid])
        s["passes_bar"] = bool(len(t) >= 2 and F1S.passes(s))
        s["passes_all_but_rate"] = bool(len(t) >= 2 and np.isfinite(s.get("t_day", np.nan)) and s["t_day"] >= BAR
                                        and s["wf_pct"] >= 54 and s["avg_train"] > 0 and s["avg_valid"] > 0
                                        and s["up_day_r"] > 0 and s["down_day_r"] > 0 and s["avg_all"] > s["ctrl_avg_r"])
        s["n_train"] = int((t["split"] == "train").sum()); s["n_valid"] = int((t["split"] == "valid").sum())
        s["trade2_n"] = int((t["tno"] == 2).sum())
        rows.append(s)
    R = pd.DataFrame(rows)
    R["N"], R["bar_t"], R["sessions"] = N, round(BAR, 3), nsess
    lead = ["id", "name", "side", "passes_bar", "passes_all_but_rate", "n", "n_train", "n_valid", "trades_per_session",
            "avg_train", "avg_valid", "avg_all", "t_day", "wf_pct", "months_pos_pct", "win_rate", "avg_win_R", "avg_loss_R",
            "win_loss_ratio", "up_day_r", "down_day_r", "avg_r_wo_best_day", "best_day_share", "ctrl_avg_r"]
    R = R[[c for c in lead if c in R.columns] + [c for c in R.columns if c not in lead]]
    R.to_csv(D / "results.csv", index=False)
    pd.set_option("display.width", 280); pd.set_option("display.max_columns", 60)
    print(f"sessions {nsess}  N {N}  bar_t {BAR:.3f}")
    print(R[[c for c in lead if c in R.columns and c not in ("name", "side")]].to_string(index=False))
    ex = ["id", "t_train", "t_valid", "flat_day_r", "up_day_r_big", "down_day_r_big", "median_cost_R", "gross_avg_r_est",
          "exit_target", "exit_stop", "exit_be", "exit_1555", "share_2R", "edge_vs_ctrl", "best_day", "busiest_session_share", "trade2_n"]
    print(R[[c for c in ex if c in R.columns]].to_string(index=False))


if __name__ == "__main__":
    main()
