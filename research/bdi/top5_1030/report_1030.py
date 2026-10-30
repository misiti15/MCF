"""top5_1030: score the scan (PLAN.md bars) -> results.csv, summary.json, hist_parent_detail.txt.
BACKTEST, open two-year history, TRAIN + VALID only (HOLD rows dropped, scored only for a Testing candidate; the locked
block is not in the data). Educational only - not financial advice.

    python research/bdi/top5_1030/report_1028.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
from scan_1030 import SCR, SETUPS, grid_of  # noqa: E402



N = sum(len(grid_of(s)) - 1 for s in SETUPS)
assert N == 75, N  # PLAN.md section 3
BAR_STUDY = round(max(1.5, math.sqrt(2 * math.log(N))), 2)
BARS = {s: round(max(1.5, math.sqrt(2 * math.log(len(grid_of(s)) - 1))), 2) for s in SETUPS}
# PLAN.md section 3: lineage N (backlog configs_tried + earlier grids + tonight's 75) -> rule 22 BAR90
LINEAGE_N = {"L3-gap-slope-rsi5hi-FD": 274339, "NS3-failed-vwap-reclaim-short-FD": 163093,
             "NS3V1-am-widestop-short": 163093, "MF5-flowsell-vwapup-rsi5hi-FD": 935045,
             "NS1-rsidip-rsi5pop-long-FD": 935045}
BAR90 = {s: round(max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(n)))), 3) for s, n in LINEAGE_N.items()}


def wf_pos(V):
    m = pd.to_datetime(V["date"]).dt.strftime("%Y-%m")
    g = V.groupby(m)["r"].mean()
    return round(float((g > 0).mean()), 3) if len(g) else np.nan


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
    # parity gates (PLAN.md section 2)
    for s in SETUPS:
        pv = "P0" if s == "NS3V1-am-widestop-short" else "P"
        P = T[(T.setup == s) & (T["var"] == pv)]
        d = (P.r - P.cache_r).abs()
        print("PARITY", s, "n", len(P), "mean|d|", round(float(d.mean()), 5), "share<0.01", round(float((d < 0.01).mean()), 4))
        assert d.mean() < 0.002, s
    assert T["spy_o2c"].notna().all()
    rows = []
    for s in SETUPS:
        P = T[(T.setup == s) & (T["var"] == "P")]
        BAR_SETUP = BARS[s]
        for vid, knob, _ in grid_of(s):
            V = T[(T.setup == s) & (T["var"] == vid)]
            if not len(V):
                rows.append(dict(setup=s, var=vid, knob=knob, is_parent=False, n_tv=0, beats_parent=False,
                                 testing_bar=False, bar_setup=BAR_SETUP, bar_study=BAR_STUDY, N_study=N,
                                 bar90=BAR90[s], lineage_N=LINEAGE_N[s]))
                continue
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
                       med_mfe=round(V.mfe.median(), 3), med_mae=round(V.mae.median(), 3), wf_pos=wf_pos(V),
                       best_day_share=round(day.max() / V.r.sum(), 3) if V.r.sum() > 0 else np.nan,
                       per_session=round(len(V) / T.date.nunique(), 2))
            if vid != "P":
                dt, _ = dday(V[V.sp == "train"], P[P.sp == "train"])
                dv, _ = dday(V[V.sp == "valid"], P[P.sp == "valid"])
                d, t = dday(V, P)
                row.update(d_train=round(dt, 4), d_valid=round(dv, 4), d_tv=round(d, 4), t_improve=t)
                row["beats_parent"] = bool(dt > 0 and dv > 0 and t >= BAR_SETUP)
                row["testing_bar"] = bool(row["beats_parent"] and row["exp_train"] > 0 and row["exp_valid"] > 0
                                          and (row["t_tv"] or 0) >= BAR90[s] and row["wf_pos"] >= 0.54
                                          and row["up"] > 0 and row["down"] > 0
                                          and row["ex_best_day"] > 0 and row["excess_vs_random"] > 0)
            row.update(bar_setup=BAR_SETUP, bar_study=BAR_STUDY, N_study=N, bar90=BAR90[s], lineage_N=LINEAGE_N[s])
            rows.append(row)
    R = pd.DataFrame(rows)
    R = R.sort_values(["setup", "is_parent", "testing_bar", "beats_parent", "t_improve"],
                      ascending=[True, False, True, True, True], na_position="first")
    R.to_csv(OUT / "results.csv", index=False)
    summ = dict(N_study=N, bar_study=BAR_STUDY, bar_setup=BARS, bar90=BAR90, lineage_N=LINEAGE_N, beats_parent=int(R.beats_parent.fillna(False).sum()),
                testing_bar=int(R.testing_bar.fillna(False).sum()), exp_pos=int((R[~R.is_parent].exp_tv > 0).sum()),
                exp_pos_train_and_valid=int(((R.exp_train > 0) & (R.exp_valid > 0) & ~R.is_parent).sum()),
                locked_block_loaded=False, hold_scored=False)
    (OUT / "summary.json").write_text(json.dumps(summ, indent=1))
    pd.set_option("display.width", 250)
    cols = ["setup", "var", "knob", "n_tv", "win_tv", "be_win", "exp_tv", "t_tv", "exp_train", "exp_valid", "t_valid", "wf_pos", "up", "down", "ex_best_day",
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
        P = P if len(P) else P
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
