"""st7_1022 Part 2: the pre-declared variant grid (PLAN.md; 42 rows) + reference rows P0 / P1 + rows added after the
diagnosis (H, counted and flagged). Writes variants.csv. Educational only - not financial advice."""
import numpy as np
import pandas as pd
from core import load, first_per_symday, p0_cond, exit_r, stats, EXITS
from sc import HERE

cand, part, pc, pp = load()
base = p0_cond(cand)
R = {e: exit_r(cand, pc, e) for e in EXITS}                     # every candidate row, every exit
PR = {e: exit_r(part, pp, e) for e in EXITS}
CT = {e: pd.Series(PR[e]).groupby(part["cid"].to_numpy()).mean() for e in EXITS}
cid = cand["cid"]
CTRL = {e: cid.map(CT[e]).to_numpy(float) for e in EXITS}
spyv = (cand["spy_vwap"] > 0).to_numpy()


def ex_cond(cond_hold, e_up, e_else="t1s1"):
    return (np.where(cond_hold, R[e_up], R[e_else]), np.where(cond_hold, CTRL[e_up], CTRL[e_else]))


def ent(m):
    return first_per_symday(cand, m)


def cap_per(idx, by, k):
    x = cand.loc[idx].sort_values(["date", "tod", "rsi", "symbol"])
    keys = [x["date"], x["tod"]] if by == "bar" else [x["date"]]
    return np.sort(x[x.groupby(keys).cumcount() < k].index.to_numpy())


tod = cand["tod"].to_numpy()
with np.errstate(invalid="ignore"):
    ENTRY = {
        "P0": ent(base),
        "P1_window_1335_1500(ref)": ent(base & (tod >= 1335)),
        "A1_spy_above_vwap": ent(base & spyv),
        "A2_spy_up_from_open": ent(base & (cand["spy_fo"] > 0).to_numpy()),
        "A3_breadth_rising": ent(base & (cand["d2"] > 0).to_numpy()),
        "A4_qqq_above_vwap": ent(base & (cand["qqq_vwap"] > 0).to_numpy()),
        "A5a_rs_ge_-2": ent(base & ((cand["fromOpen"] - cand["spy_fo"]) >= -2).to_numpy()),
        "A5b_rs_ge_-3": ent(base & ((cand["fromOpen"] - cand["spy_fo"]) >= -3).to_numpy()),
        "A6a_no_1045_bar": ent(base & (tod != 1045)),
        "A6b_only_1045_bar": ent(base & (tod == 1045)),
        "A7a_gap_gt_0": ent(base & (cand["gap"] > 0).to_numpy()),
        "A7b_gap_le_0": ent(base & (cand["gap"] <= 0).to_numpy()),
        "B1_0950_1200": ent(base & (tod <= 1200)),
        "B2_1200_1500": ent(base & (tod >= 1200)),
        "B3_0950_1100": ent(base & (tod <= 1100)),
        "C1a_rsi_le_27": ent(p0_cond(cand, rsi_max=27)),
        "C1b_rsi_le_33": ent(p0_cond(cand, rsi_max=33)),
        "C1c_rsi_le_24": ent(p0_cond(cand, rsi_max=24)),
        "C1d_rsi_le_36": ent(p0_cond(cand, rsi_max=36)),
        "C2a_fo_lt_-0.8": ent(p0_cond(cand, fo_max=-0.8)),
        "C2b_fo_lt_-0.9": ent(p0_cond(cand, fo_max=-0.9)),
        "C2c_fo_lt_-1.1": ent(p0_cond(cand, fo_max=-1.1)),
        "C2d_fo_lt_-1.2": ent(p0_cond(cand, fo_max=-1.2)),
        "C3a_cross_45": ent(p0_cond(cand, lvl=45)),
        "C3b_cross_55": ent(p0_cond(cand, lvl=55)),
    }
    i0 = ENTRY["P0"]
    ENTRY["E1_max1_per_bar"] = cap_per(i0, "bar", 1)
    ENTRY["E2_max2_per_bar"] = cap_per(i0, "bar", 2)
    ENTRY["E3_max5_per_day"] = cap_per(i0, "day", 5)
    # added after the diagnosis (counted, flagged): the opposite tape filters, and buyPressure strength
    POST = {
        "H1_qqq_below_vwap(post-diag)": ent(base & (cand["qqq_vwap"] <= 0).to_numpy()),
        "H2_spy_below_vwap(post-diag)": ent(base & (cand["spy_vwap"] <= 0).to_numpy()),
        "H3_bp_gt_0.25(post-diag)": ent(base & (cand["buyPressure"] > 0.25).to_numpy()),
        "H4_qqq_below_vwap_or_1335(post-diag)": ent(base & ((cand["qqq_vwap"] <= 0).to_numpy() | (tod >= 1335))),
    }

EXIT_ROWS = {"D1_t15s1": "D1_t15s1", "D2_t2s1": "D2_t2s1", "D3_hold": "D3_hold", "D4_trail1": "D4_trail1",
             "D5_t2_be1": "D5_t2_be1", "D6_half1_rest_hold_be": "D6_half1_rest_hold_be", "D7_t05s1": "t05s1",
             "D8_t1s05": "t1s05"}


def exit_vec(name):
    if name == "t1s1":
        return R["t1s1"], CTRL["t1s1"]
    if name == "F1_spyabove_hold":
        return ex_cond(spyv, "D3_hold")
    if name == "F2_spyabove_t2":
        return ex_cond(spyv, "D2_t2s1")
    e = EXIT_ROWS[name]
    return R[e], CTRL[e]


rows = []
p0df = cand.loc[i0]


def score(name, idx, exitname, group, counted=True):
    r, c = exit_vec(exitname)
    df = cand.loc[idx]
    s = stats(df, r[idx], c[idx])
    s.update({"row": name, "group": group, "exit": exitname, "counted": counted,
              "kept_pct_train": round(100 * s.get("n_train", 0) / max(1, (p0df.split == "train").sum()), 1),
              "kept_pct_valid": round(100 * s.get("n_valid", 0) / max(1, (p0df.split == "valid").sum()), 1)})
    rows.append(s)
    return s


score("P0", i0, "t1s1", "ref", False)
score("P1_window_1335_1500(ref)", ENTRY["P1_window_1335_1500(ref)"], "t1s1", "ref", False)
for k, v in ENTRY.items():
    if k in ("P0", "P1_window_1335_1500(ref)"):
        continue
    score(k, v, "t1s1", k[0])
for e in list(EXIT_ROWS) + ["F1_spyabove_hold", "F2_spyabove_t2"]:
    score(e, i0, e, e[0])
# G pairs: selected on TRAIN only
d = pd.DataFrame(rows)
ent_rows = d[d.group.isin(list("ABCE")) & (d.n_train >= 100)].sort_values("avg_train", ascending=False).head(3)
ex_rows = d[d.group.isin(["D", "F"])].sort_values("avg_train", ascending=False).head(2)
print("G picks:", ent_rows.row.tolist(), ex_rows.row.tolist())
for en in ent_rows.row:
    for xn in ex_rows.row:
        score(f"G_{en}+{xn}", ENTRY[en], xn, "G")
for k, v in POST.items():
    score(k, v, "t1s1", "H")
    for xn in ex_rows.row:
        score(f"{k}+{xn}", v, xn, "H")
d = pd.DataFrame(rows)
P = d.iloc[0]
d["vs_thin_train"] = d.tot_train - P.tot_train * d.n_train / P.n_train
d["vs_thin_valid"] = d.tot_valid - P.tot_valid * d.n_valid / P.n_valid
d["merit_nearmiss"] = (d.avg_train > 0) & (d.avg_valid > 0) & (d.excess_train > 0) & (d.excess_valid > 0) & \
    (d.n_train >= 30) & (d.n_valid >= 20) & (d.top_day_share_all.fillna(9) <= 0.25)
d["testing_bar"] = (d.avg_train > 0) & (d.avg_valid > 0) & (d.excess_train > 0) & (d.excess_valid > 0) & (d.t_all >= 4.97)
d["guard_up"] = (d.Up_train_avg > P.Up_train_avg) & (d.Up_valid_avg > P.Up_valid_avg)
d["guard_bear"] = (d.Bear_all_avg >= P.Bear_all_avg - 0.05) & (d.Bear_valid_tot >= 0.75 * P.Bear_valid_tot)
d["proposable"] = (d.merit_nearmiss | d.testing_bar) & d.guard_up & d.guard_bear
first = ["row", "group", "exit", "counted", "n_train", "avg_train", "tot_train", "n_valid", "avg_valid", "tot_valid", "t_all",
         "excess_train", "excess_valid", "top_day_share_all", "worst_day_all", "worst5pct_days", "Bull_all_avg", "Bear_all_avg",
         "Choppy_all_avg", "Quiet_all_avg", "Choppy-up_all_avg", "Up_train_avg", "Up_valid_avg", "Bear_train_avg",
         "Bear_valid_avg", "Bear_valid_tot", "vs_thin_train", "vs_thin_valid", "merit_nearmiss", "testing_bar", "guard_up",
         "guard_bear", "proposable"]
d = d[first + [c for c in d.columns if c not in first]]
d.to_csv(HERE / "variants.csv", index=False)
pd.set_option("display.width", 320); pd.set_option("display.max_rows", 200); pd.set_option("display.max_columns", 40)
print(d[first].to_string())
print("counted:", int(d.counted.sum()))
