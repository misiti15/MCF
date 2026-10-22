"""l3_1022 Part 3 step 2: score the 22 pre-declared variants (PLAN.md) from scan.py's signals. As-run sequencing =
regime1022 asrun.sequence (open lots per symbol <= cap, lots leave at their exit bar under that variant's exits).
Writes variants.csv, variants_days.csv, counts.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd

import l3c
from asrun import sequence          # regime1022/scripts/asrun.py
from rc import gates, no_locked, split_of
from regime import day_table

V = {  # id: (chain flag, exit, lot cap, filter(df) -> bool array, label)
    "P0": ("cd1", "P0", 3, None, "parent as-run (refire cd1, 3 lots, t1s1)"),
    "S1": ("cd1", "P0", 1, None, "one lot per symbol"),
    "S2": ("first", "P0", 3, None, "refire off (first signal per symbol-day)"),
    "S3": ("cd3", "P0", 3, None, "refire cooldown 3"),
    "S4": ("cd6", "P0", 3, None, "refire cooldown 6"),
    "W1": ("cd1", "P0", 3, lambda d: d["tod"] >= 1030, "entries from 10:30"),
    "W2": ("cd1", "P0", 3, lambda d: d["tod"] >= 1100, "entries from 11:00"),
    "W3": ("cd1", "P0", 3, lambda d: d["tod"] <= 1400, "entries until 14:00"),
    "X1": ("cd1", "X1", 3, None, "stop 1.5x wider, same $ risk"),
    "X2": ("cd1", "X2", 3, None, "stop 2x wider, same $ risk"),
    "X3": ("cd1", "X3", 3, None, "time stop 60 min"),
    "X4": ("cd1", "X4", 3, None, "time stop 120 min"),
    "X5": ("cd1", "X5", 3, None, "scale-out half at +0.5R, rest to 1R with stop at entry"),
    "G1": ("cd1", "P0", 3, lambda d: d["gap"] >= -10, "gap >= -10%"),
    "G2": ("cd1", "P0", 3, lambda d: d["gap"] >= -6, "gap >= -6%"),
    "G3": ("cd1", "P0", 3, lambda d: d["gap"] <= -4, "gap <= -4%"),
    "R1": ("cd1", "P0", 3, lambda d: ~(d["fromOpen"] - d["spy_fo"] > 8), "skip stock-minus-SPY from open > 8"),
    "R2": ("cd1", "P0", 3, lambda d: d["fromOpen"] - d["spy_fo"] >= 4.5, "only stock-minus-SPY from open >= 4.5"),
    "V1": ("cd1", "P0", 3, lambda d: ~(d["spy_vwap"] > 0), "skip when SPY above VWAP"),
    "V2": ("cd1", "P0", 3, lambda d: ~((d["spy_vwap"] > 0) & (d["qqq_vwap"] > 0)), "skip when SPY and QQQ above VWAP"),
    "C1": ("cd1", "P0", 1, lambda d: d["tod"] >= 1030, "combo: one lot + from 10:30"),
    "C2": ("cd3", "P0", 3, lambda d: ~(d["spy_vwap"] > 0), "combo: cooldown 3 + skip SPY above VWAP"),
}
N_STUDY = len(V)
N_LINEAGE = 11178 + 718 + 384 + N_STUDY
BAR_STUDY = max(1.5, math.sqrt(2 * math.log(N_STUDY)))
BAR_LINEAGE = max(1.5, math.sqrt(2 * math.log(N_LINEAGE)))


def load() -> pd.DataFrame:
    s = pd.concat([pd.read_parquet(p) for p in sorted((l3c.SCRATCH / "sig").glob("*.parquet"))], ignore_index=True)
    s["date"] = pd.to_datetime(s["date"]).dt.date
    no_locked(s["date"].unique())
    s["split"] = split_of(s["date"])
    dt = day_table()
    s = s.join(dt[["regime"]], on="date")
    s["key"] = s["symbol"] + "|" + s["date"].astype(str) + "|" + s["tod"].astype(str)
    return s


def run(s: pd.DataFrame, vid: str) -> pd.DataFrame:
    flag, ex, cap, flt, _ = V[vid]
    d = s[s[flag]]
    if flt is not None:
        d = d[np.asarray(flt(d), bool)]
    d = d[np.isfinite(d[f"r_{ex}"])]
    keep = sequence(d["date"].astype(str).to_numpy(), d["tod"].to_numpy(), d["symbol"].to_numpy(),
                    d[f"et_{ex}"].to_numpy(), cap=cap)
    d = d[keep]
    return d.assign(r=d[f"r_{ex}"], rc=d[f"rc_{ex}"])


def stats(d: pd.DataFrame) -> dict:
    if d.empty:
        return {"n": 0}
    sm = gates.summary(d[["date", "r"]])
    by = d.groupby("date")["r"].sum()
    tot = by.sum()
    bear = d[d["regime"] == "Bear"]["r"]
    rest = d[d["regime"] != "Bear"]["r"]
    return {"n": len(d), "days": d["date"].nunique(), "avg_r": sm["exp_r"], "t": sm["t"], "total_r": tot,
            "ctrl_avg_r": d["rc"].mean(), "beats_ctrl": d["r"].mean() > d["rc"].mean(),
            "bear_avg_r": bear.mean(), "nonbear_avg_r": rest.mean(), "bull_avg_r": d[d["regime"] == "Bull"]["r"].mean(),
            "max_day_share": (by.max() / tot) if tot > 0 else np.nan, "win_pct": 100 * (d["r"] > 0).mean()}


def delta_t(v: pd.DataFrame, p: pd.DataFrame) -> tuple[float, float]:
    a = v.groupby("date")["r"].sum()
    b = p.groupby("date")["r"].sum()
    x = a.reindex(a.index.union(b.index), fill_value=0) - b.reindex(a.index.union(b.index), fill_value=0)
    return x.mean(), x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))


def main():
    s = load()
    P = run(s, "P0")
    rows, days = [], []
    for vid, (_, _, _, flt, lab) in V.items():
        d = run(s, vid)
        row = {"id": vid, "variant": lab}
        for sp in ("all", "train", "valid"):
            dd = d if sp == "all" else d[d["split"] == sp]
            pp = P if sp == "all" else P[P["split"] == sp]
            st = stats(dd)
            row.update({f"{sp}_{k}": v for k, v in st.items()})
            row[f"{sp}_kept_pct"] = 100 * len(dd) / len(pp)
            dropped = pp[~pp["key"].isin(dd["key"])]
            row[f"{sp}_dropped_n"] = len(dropped)
            row[f"{sp}_dropped_avg_r"] = dropped["r"].mean() if len(dropped) else np.nan
            row[f"{sp}_delta_per_day"], row[f"{sp}_delta_t"] = delta_t(dd, pp) if vid != "P0" else (0.0, np.nan)
        tr, va = {k[6:]: v for k, v in row.items() if k.startswith("train_")}, {k[6:]: v for k, v in row.items() if k.startswith("valid_")}
        t1 = tr["avg_r"] > 0 and va["avg_r"] > 0 and tr["n"] >= 30 and va["n"] >= 20
        t2 = bool(tr["beats_ctrl"] and va["beats_ctrl"])
        t3 = bool(row["all_max_day_share"] == row["all_max_day_share"] and row["all_max_day_share"] <= 0.25)
        pt, pv = stats(P[P["split"] == "train"]), stats(P[P["split"] == "valid"])
        t4b = row["all_delta_t"]
        t4 = vid != "P0" and tr["avg_r"] > pt["avg_r"] and va["avg_r"] > pv["avg_r"]
        dr_ok = all((row[f"{sp}_dropped_avg_r"] != row[f"{sp}_dropped_avg_r"]) or row[f"{sp}_dropped_avg_r"] < 0
                    for sp in ("train", "valid")) if flt is not None else True
        t5 = row["train_kept_pct"] >= 50 and row["valid_kept_pct"] >= 50 and dr_ok
        row.update({"T1_positive_both": t1, "T2_beats_random_both": t2, "T3_no_day_gt_25pct": t3,
                    "T4_better_both": bool(t4), "T4_delta_t": t4b, "T5_not_over_restrictive": bool(t5),
                    "near_miss": bool(t1 and t2 and t3 and t4 and t5 and t4b == t4b and t4b >= BAR_STUDY),
                    "passes": bool(t1 and t2 and t3 and t4 and t5 and t4b == t4b and t4b >= BAR_LINEAGE)})
        rows.append(row)
        g = d.groupby(["date", "split", "regime"], dropna=False)["r"].agg(["size", "sum"]).reset_index()
        g["id"] = vid
        days.append(g)
        print(vid, lab, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()
                         if k in ("all_n", "train_avg_r", "valid_avg_r", "train_ctrl_avg_r", "valid_ctrl_avg_r",
                                  "all_bear_avg_r", "all_nonbear_avg_r", "all_delta_t", "train_kept_pct", "passes")},
              flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(l3c.HERE / "variants.csv", index=False, float_format="%.4f")
    pd.concat(days).to_csv(l3c.HERE / "variants_days.csv", index=False, float_format="%.4f")
    (l3c.HERE / "counts.json").write_text(json.dumps({
        "configs_scored": N_STUDY, "study_bar": round(BAR_STUDY, 3),
        "lineage_N": N_LINEAGE, "lineage_bar": round(BAR_LINEAGE, 3),
        "lineage_parts": "layering 11,178 + gates1021 718 + regime1022 384 + l3_1022 22",
        "descriptive_not_counted": "live record (Part 1), live-vs-backtest decomposition (Part 2)"}, indent=1))


if __name__ == "__main__":
    main()
