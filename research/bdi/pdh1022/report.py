"""pdh1022 report: score every pdh_scan.py variant against PLAN.md's pre-declared bars, the parent's history diagnosis,
and the TRAIN-only stage-2 pair choice. Educational only - not financial advice.

    python research/bdi/pdh1022/report.py stage1   # -> results_stage1.csv, hist_parent_detail.txt, stage2.json
    python research/bdi/pdh1022/report.py all      # stage1 + stage2 -> results.csv, summary.json (HOLD only for a pass)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "research" / "history2y"), str(ROOT / "research" / "bdi" / "top5_1014"),
                str(ROOT / "research" / "bdi" / "regime1022" / "scripts"), str(OUT), str(ROOT)]
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402
from report_top5 import boot_diff, split  # noqa: E402
import pdh_scan as PS  # noqa: E402

SCR = PS.SCR
N_STUDY = 48
LINEAGE_N = 121_396 + N_STUDY
T_STUDY = round(max(1.5, math.sqrt(2 * math.log(N_STUDY))), 2)
T_LIN = gates.t_required(LINEAGE_N)
SEED = 20261022
REG = ["Bull", "Bear", "Choppy", "Quiet"]


def regimes():
    import regime
    r = regime.day_table()["regime"]
    r.index = pd.to_datetime(r.index).date
    return r


def load(stage):
    T = pd.read_parquet(SCR / f"trades_{stage}.parquet")
    for c in ("var", "knob", "symbol"):
        T[c] = T[c].astype(str)
    T["date"] = pd.to_datetime(T["date"]).dt.date
    T["split"] = split(pd.Series(T["date"]))
    return T


def readout(d):
    r = d["r"].to_numpy(float)
    w, l = r[r > 0], r[r <= 0]
    aw, al = (w.mean() if len(w) else np.nan), (l.mean() if len(l) else np.nan)
    be = -al / (aw - al) if len(w) and len(l) else np.nan
    return {"avg_win": round(aw, 4), "avg_loss": round(al, 4), "be_win": round(be, 4),
            "win_margin": round((r > 0).mean() - be, 4) if np.isfinite(be) else np.nan}


def hist_detail(T, reg):
    d = T[(T["var"] == "P") & (T.split != "hold") & T.filled].copy()
    d["regime"] = d["date"].map(reg)
    r = d["r"]
    w, l = d[r > 0], d[r <= 0]
    ro = readout(d)
    agg = lambda g: g["r"].agg(n="size", avg="mean", win=lambda x: (x > 0).mean(), sum="sum").round(4)  # noqa: E731
    txt = ["Educational only - not financial advice. BACKTEST, open two-year history TRAIN+VALID (no HOLD), costs in.",
           f"Parent {PS.S}: n {len(d)}, sessions {d.date.nunique()}, win {(r > 0).mean():.3f}, exp {r.mean():+.4f}R, "
           f"total {r.sum():+.0f}R; avg win {ro['avg_win']:+.3f}, avg loss {ro['avg_loss']:+.3f}, BE win {ro['be_win']:.3f}",
           f"losers never > +0.2R: {(l.mfe < 0.2).mean():.3f}; losers that reached +0.4R: {(l.mfe >= 0.4).mean():.3f}; "
           f"loss beyond -1.05R (gap / slip through stop): {(l.r < -1.05).mean():.3f} of losers, avg {l.r[l.r < -1.05].mean():+.3f}; "
           f"winners with MAE <= -0.5R: {(w.mae <= -0.5).mean():.3f}; exit codes {d.code.value_counts().to_dict()}", ""]
    cuts = [("regime", d["regime"]),
            ("split x regime", d["split"] + " / " + d["regime"].astype(str)),
            ("entry time", pd.cut(d["tod"], [0, 959, 1029, 1059, 1129, 1200, 1600],
                                  labels=["09:50-09:59", "10:00-10:29", "10:30-10:59", "11:00-11:29", "11:30-12:00", ">12:00"])),
            ("poke extension above PDH (ATR)", pd.cut(d["ext_atr"], [0, .15, .2, .3, .5, 99])),
            ("bars from poke to failure", d["bars_to_fail"]),
            ("poke-bar volumeRatio", pd.cut(d["vr_poke"], [-1, .7, 1, 1.5, 3, 999])),
            ("failure-bar volumeRatio < poke-bar (fade)", (d["vr_fail"] < d["vr_poke"]).where(d["vr_poke"].notna())),
            ("gap %", pd.cut(d["gap"], [-99, -1, 0, .5, 1, 2, 4, 999])),
            ("RS vs SPY at entry (stock fromOpen - SPY, %)", pd.cut(d["rs"], [-99, -1, 0, .5, 1, 2, 999])),
            ("SPY vs VWAP at entry", np.where(d["spy_vwap"] < 0, "SPY below VWAP", np.where(d["spy_vwap"] >= 0, "SPY above VWAP", "n/a"))),
            ("QQQ vs open at entry", np.where(d["qqq_fo"] < 0, "QQQ below open", np.where(d["qqq_fo"] >= 0, "QQQ above open", "n/a"))),
            ("breadth (share above VWAP)", pd.cut(d["breadth"], [0, .3, .4, .5, .6, .7, 1])),
            ("breadth change over 3 bars", np.where(d["breadth_d3"] < 0, "falling", np.where(d["breadth_d3"] >= 0, "rising/flat", "n/a")))]
    tabs = {}
    for name, key in cuts:
        g = d.groupby(np.asarray(key, dtype=object) if not hasattr(key, "cat") else key, observed=True, dropna=False)
        tb = agg(g)
        tabs[name] = tb
        txt.append(f"by {name}:\n{tb.to_string()}")
    txt.append("losers by MFE reached (R):\n" + l.groupby(pd.cut(l.mfe, [-.01, .1, .2, .3, .4, 5]), observed=True)["r"].agg(["size", "mean"]).round(3).to_string())
    txt.append("losers by size (R):\n" + l.groupby(pd.cut(l.r, [-9, -1.5, -1.1, -1.0, -0.5, 0.01]), observed=True)["r"].agg(["size", "mean", "sum"]).round(3).to_string())
    txt.append("winners by MAE (R):\n" + w.groupby(pd.cut(w.mae, [-5, -.75, -.5, -.25, .01]), observed=True)["r"].agg(["size", "mean"]).round(3).to_string())
    dd = d.groupby("date")["r"].sum().sort_values()
    txt.append("worst 10 days (R): " + ", ".join(f"{k} {v:+.1f} ({reg.get(k)})" for k, v in dd.head(10).items()))
    txt.append(f"random same-minute control: parent {d.r.mean():+.4f} vs control {d.ctrl.mean():+.4f} (excess {(d.r - d.ctrl).mean():+.4f})")
    (OUT / "hist_parent_detail.txt").write_text("\n\n".join(txt) + "\n")
    return txt


def by_regime(d, reg):
    rg = d["date"].map(reg)
    return {k: {"n": int((rg == k).sum()), "avg_r": round(float(d.r[rg.to_numpy() == k].mean()), 4) if (rg == k).any() else None}
            for k in REG}


def score(T, reg, P):
    rows = []
    ptv = P[P.split != "hold"]
    sp = {k: gates.summary(P[P.split == k]) for k in ("train", "valid")}
    for v, d in T.groupby("var", sort=False):
        d = d[d.filled]
        tv = d[d.split != "hold"]
        st = {k: gates.summary(d[d.split == k]) for k in ("train", "valid")}
        ex = {k: gates.summary(d[d.split == k].assign(r=lambda z: z.r - z.ctrl).dropna(subset=["r"])) for k in ("train", "valid")}
        a = gates.summary(tv)
        ro = readout(tv)
        day = tv.groupby("date")["r"].sum()
        tot = float(day.sum())
        maxshare = float(day.max() / tot) if tot > 0 else np.nan
        if v == "P":
            dtr = dva = dtv = timp = np.nan
        else:
            dtr = st["train"]["exp_r"] - sp["train"]["exp_r"]
            dva = st["valid"]["exp_r"] - sp["valid"]["exp_r"]
            dtv, timp = boot_diff(tv, ptv, 1000, SEED)
        beats = bool(v != "P" and dtr > 0 and dva > 0 and timp >= T_STUDY)
        pos = st["train"].get("exp_r", -1) > 0 and st["valid"].get("exp_r", -1) > 0
        exc = (ex["train"].get("exp_r") or -1) > 0 and (ex["valid"].get("exp_r") or -1) > 0
        testing = bool(pos and exc and (st["valid"].get("t") or 0) >= T_STUDY and (a.get("t") or 0) >= T_LIN
                       and (a.get("ex_best_day") or -1) > 0)
        merit = bool(pos and exc and st["train"].get("n", 0) >= 30 and st["valid"].get("n", 0) >= 20
                     and np.isfinite(maxshare) and maxshare <= 0.25)
        br = by_regime(tv, reg)
        rows.append({"var": v, "knob": d["knob"].iloc[0], "n_train": st["train"].get("n"), "exp_train": st["train"].get("exp_r"),
                     "t_train": st["train"].get("t"), "n_valid": st["valid"].get("n"), "exp_valid": st["valid"].get("exp_r"),
                     "t_valid": st["valid"].get("t"), "n_tv": a.get("n"), "per_day": round(a["n"] / max(1, a["days"]), 1),
                     "kept_vs_parent": round(a["n"] / len(ptv), 3), "win_tv": a.get("win_rate"), **ro,
                     "exp_tv": a.get("exp_r"), "t_tv": a.get("t"), "total_R": round(tot, 1),
                     "worst_day_R": round(float(day.min()), 1), "worst5_days_R": round(float(day.nsmallest(5).sum()), 1),
                     "best_day_share": round(maxshare, 3) if np.isfinite(maxshare) else None,
                     "ex_best_day": a.get("ex_best_day"),
                     "excess_train": ex["train"].get("exp_r"), "excess_valid": ex["valid"].get("exp_r"),
                     **{f"{k}_avg_r": br[k]["avg_r"] for k in REG}, **{f"{k}_n": br[k]["n"] for k in REG},
                     "d_train": round(dtr, 4), "d_valid": round(dva, 4), "d_tv": round(dtv, 4), "t_improve": round(timp, 2),
                     "beats_parent": beats, "testing_bar": testing, "merit_rule": merit})
    return pd.DataFrame(rows)


def pick_stage2(R):
    x = R[(R["var"] != "P") & (R.n_train >= 1000)].set_index("var")
    ent = x.loc[[k for k in PS.ENTRY_KNOBS if k in x.index]].sort_values("exp_train", ascending=False).index[:3].tolist()
    fil = x.loc[[k for k in PS.FILTER_KNOBS if k in x.index]].sort_values("exp_train", ascending=False).index[:3].tolist()
    pairs = [[a, b] for a in ent for b in PS.EXIT_PAIR] + [[fil[0], fil[1]], [fil[0], fil[2]], [fil[1], fil[2]]]
    j = {"rule": "PLAN section 5: 3 best entry/window/lot/filter knobs by TRAIN exp (n_train >= 1000) x {S150, SO35, T075}"
                 " + the 3 pairs of the 3 best TRAIN filters", "entry_top3": ent, "filter_top3": fil, "pairs": pairs}
    json.dump(j, open(OUT / "stage2.json", "w"), indent=1)
    return j


def main(which):
    reg = regimes()
    T1 = load("stage1")
    P = T1[(T1["var"] == "P") & T1.filled]
    if which == "stage1":
        print("\n\n".join(hist_detail(T1, reg)))
        R = score(T1, reg, P)
        R.to_csv(OUT / "results_stage1.csv", index=False)
        print(R.to_string())
        print(pick_stage2(R))
        return
    T2 = load("stage2")
    T = pd.concat([T1, T2[T2["var"] != "P"]], ignore_index=True)
    R = score(T, reg, P)
    R["stage"] = np.where(R["var"].str.contains(r"\+"), 2, np.where(R["var"] == "P", 0, 1))
    hold = {}
    for v in R.loc[R.testing_bar | R.merit_rule, "var"]:
        h = T[(T["var"] == v) & (T.split == "hold") & T.filled]
        hold[v] = {**gates.summary(h), "excess": gates.summary(h.assign(r=h.r - h.ctrl).dropna(subset=["r"])).get("exp_r")}
    R["hold_n"] = R["var"].map(lambda v: hold.get(v, {}).get("n"))
    R["hold_exp"] = R["var"].map(lambda v: hold.get(v, {}).get("exp_r"))
    R["hold_t"] = R["var"].map(lambda v: hold.get(v, {}).get("t"))
    R = R.sort_values(["stage", "exp_tv"], ascending=[True, False], kind="mergesort")
    R.to_csv(OUT / "results.csv", index=False)
    summ = {"n_study": N_STUDY, "n_scored": int((R["var"] != "P").sum()), "t_study": T_STUDY, "t_lineage": T_LIN,
            "lineage_n": LINEAGE_N, "testing_bar": R[R.testing_bar]["var"].tolist(), "merit_rule": R[R.merit_rule]["var"].tolist(),
            "beats_parent": R[R.beats_parent]["var"].tolist(),
            "positive_train_and_valid": R[(R.exp_train > 0) & (R.exp_valid > 0)]["var"].tolist(),
            "hold_scored": hold}
    json.dump(summ, open(OUT / "summary.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 320)
    pd.set_option("display.max_columns", 60)
    print(R.to_string())
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1])
