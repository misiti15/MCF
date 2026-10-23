"""top5_1023: score the scan (PLAN.md bars) -> results.csv, summary.json, hist_parent_detail.txt.
BACKTEST, open two-year history, TRAIN + VALID only (HOLD rows dropped, scored only for a Testing candidate; the locked
block is not in the data). Educational only - not financial advice.

    python research/bdi/top5_1023/report_1022.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
from scan_1023 import SCR, SETUPS, grid_of  # noqa: E402

N = sum(len(grid_of(s)) - 1 for s in SETUPS)
assert N == 80, N  # PLAN.md section 3
BAR_STUDY = round(max(1.5, math.sqrt(2 * math.log(N))), 2)
BARS = {s: round(max(1.5, math.sqrt(2 * math.log(len(grid_of(s)) - 1))), 2) for s in SETUPS}


def split(d):
    d = pd.to_datetime(d)
    tr = d <= "2025-12-31"
    va = ((d >= "2026-01-01") & (d <= "2026-03-31")) | ((d >= "2026-07-01") & (d <= "2026-09-15"))
    return np.where(tr, "train", np.where(va, "valid", "hold"))


def tday(x):
    """day-clustered t of mean R per trade."""
    g = x.groupby("date")["r"].agg(["sum", "size"])
    n = g["size"].sum()
    if n < 2:
        return np.nan
    m = g["sum"].sum() / n
    se = np.sqrt(((g["sum"] - m * g["size"]) ** 2).sum()) / n
    return round(float(m / se), 2) if se > 0 else np.nan


def dday(v, p):
    a = p.groupby("date")["r"].agg(["sum", "size"])
    b = v.groupby("date")["r"].sum().reindex(a.index.union(v["date"].unique()), fill_value=0.0)
    a = a.reindex(b.index, fill_value=0)
    D = b - a["sum"]
    n = a["size"].sum()
    dl = D.sum() / n
    se = np.sqrt(((D - dl * a["size"]) ** 2).sum()) / n
    return float(dl), (round(float(dl / se), 2) if se > 0 else np.nan)


def main():
    T = pd.read_parquet(SCR / "trades.parquet")
    T = T[T["r"].notna()].copy()
    T["date"] = pd.to_datetime(T["date"]).dt.date
    T["sp"] = split(T["date"])
    T = T[T.sp != "hold"]
    sys.path.insert(0, str(OUT.parent / "gates1021" / "scripts"))
    from load import day_table  # SPY open-to-close per session (%), as top5_1022's cached column
    T = T.join(day_table()["spy_o2c"], on="date")
    assert T["spy_o2c"].notna().all()
    rows = []
    for s in SETUPS:
        P = T[(T.setup == s) & (T["var"] == "P")]
        BAR_SETUP = BARS[s]
        for vid, knob, _ in grid_of(s):
            V = T[(T.setup == s) & (T["var"] == vid)]
            w, l = V[V.r > 0], V[V.r <= 0]
            aw, al = w.r.mean(), l.r.mean()
            day = V.groupby("date")["r"].sum()
            row = dict(setup=s, var=vid, knob=knob, is_parent=vid == "P", n_tv=len(V), win_tv=round((V.r > 0).mean(), 4),
                       avg_win=round(aw, 4), avg_loss=round(al, 4), be_win=round(-al / (aw - al), 4),
                       exp_tv=round(V.r.mean(), 4), t_tv=tday(V),
                       exp_train=round(V[V.sp == "train"].r.mean(), 4), exp_valid=round(V[V.sp == "valid"].r.mean(), 4),
                       t_valid=tday(V[V.sp == "valid"]),
                       up=round(V[V.spy_o2c > 0].r.mean(), 4), down=round(V[V.spy_o2c <= 0].r.mean(), 4),
                       ex_best_day=round((V.r.sum() - day.max()) / max(len(V) - 1, 1), 4),
                       excess_vs_random=round((V.r - V.ctrl).mean(), 4),
                       med_mfe=round(V.mfe.median(), 3), med_mae=round(V.mae.median(), 3))
            if vid != "P":
                dt, _ = dday(V[V.sp == "train"], P[P.sp == "train"])
                dv, _ = dday(V[V.sp == "valid"], P[P.sp == "valid"])
                d, t = dday(V, P)
                row.update(d_train=round(dt, 4), d_valid=round(dv, 4), d_tv=round(d, 4), t_improve=t)
                row["beats_parent"] = bool(dt > 0 and dv > 0 and t >= BAR_SETUP)
                row["testing_bar"] = bool(row["beats_parent"] and row["exp_train"] > 0 and row["exp_valid"] > 0
                                          and (row["t_valid"] or 0) >= BAR_STUDY and row["up"] > 0 and row["down"] > 0
                                          and row["ex_best_day"] > 0 and row["excess_vs_random"] > 0)
            row.update(bar_setup=BAR_SETUP, bar_study=BAR_STUDY, N_study=N)
            rows.append(row)
    R = pd.DataFrame(rows)
    R = R.sort_values(["setup", "is_parent", "testing_bar", "beats_parent", "t_improve"],
                      ascending=[True, False, True, True, True], na_position="first")
    R.to_csv(OUT / "results.csv", index=False)
    summ = dict(N_study=N, bar_study=BAR_STUDY, bar_setup=BARS, beats_parent=int(R.beats_parent.fillna(False).sum()),
                testing_bar=int(R.testing_bar.fillna(False).sum()), exp_pos=int((R[~R.is_parent].exp_tv > 0).sum()),
                exp_pos_train_and_valid=int(((R.exp_train > 0) & (R.exp_valid > 0) & ~R.is_parent).sum()),
                locked_block_loaded=False, hold_scored=False)
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1))
    pd.set_option("display.width", 250)
    cols = ["setup", "var", "knob", "n_tv", "win_tv", "be_win", "exp_tv", "exp_train", "exp_valid", "t_valid", "up", "down",
            "excess_vs_random", "d_train", "d_valid", "t_improve", "beats_parent", "testing_bar"]
    print(R[cols].to_string(index=False))
    print(summ)
    # parent diagnostics (history)
    txt = ["Educational only - not financial advice. BACKTEST parents (open history, TRAIN+VALID, costs in)."]
    for s in SETUPS:
        P = T[(T.setup == s) & (T["var"] == "P")].copy()
        l = P[P.r <= 0]
        P["tb"] = pd.cut(P.tod, [0, 1000, 1030, 1130, 1300, 1400, 1600],
                         labels=["09:50-10:00", "10:00-10:30", "10:30-11:30", "11:30-13:00", "13:00-14:00", "14:00-16:00"])
        txt.append(f"=== {s}  n {len(P)}  exp {P.r.mean():+.4f}  win {(P.r > 0).mean():.3f}")
        txt.append(f"losers {len(l)}: never reached +0.2R {int((l.mfe < 0.2).sum())}, reached +0.5R {int((l.mfe >= 0.5).sum())}; "
                   f"med MFE {P.mfe.median():.2f} med MAE {P.mae.median():.2f}")
        txt.append("by entry time:\n" + P.groupby("tb", observed=True)["r"].agg(["size", "mean", lambda x: (x > 0).mean()]).round(3).to_string())
        txt.append("by split / SPY session:\n" + P.groupby(["sp", P.spy_o2c > 0])["r"].agg(["size", "mean"]).round(3).to_string())
        txt.append("by exit code (1 tgt, 2 stop, 6 flat):\n" + P.groupby("code")["r"].agg(["size", "mean"]).round(3).to_string())
        txt.append("")
    (OUT / "hist_parent_detail.txt").write_text("\n".join(txt))
    print("\n".join(txt))


if __name__ == "__main__":
    main()
