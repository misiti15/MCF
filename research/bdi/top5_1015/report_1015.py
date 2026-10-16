"""top5_1015 report: score every variant of scan_1015.py against PLAN.md's pre-declared bars, plus the parents'
history diagnostics (step 2). Educational only - not financial advice.

    python research/bdi/top5_1015/report_1015.py    # -> results.csv, summary.json, hist_parent_detail.txt
HOLD (rule-2 holdouts Apr-Jun 2026, 2026-09-16..10-07) is scored only for variants that meet the Testing bar on
TRAIN+VALID. The rule-19 locked block is not in the data at all.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/user/MCF")
sys.path[:0] = [str(ROOT / "research" / "history2y"), str(ROOT / "research" / "bdi" / "top5_1014"), str(ROOT)]
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402
from report_top5 import boot_diff, split  # noqa: E402  (yesterday's split and day-block bootstrap)

OUT = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top5_1015")
N_STUDY = 89
GRID_N = {"CWT14-failbrk-orl-p05-long": 16, "CWT14-failbrk-orl-p05-lowvol-long": 16, "CWT14-failbrk-pdl-p05-long": 16,
          "heat_fade_short-FD": 19, "CWT12-coil-k4-long": 22}
LINEAGE_N = {"CWT14": 121_133 + 48, "heat_fade_short-FD": 19_721 + 19, "CWT12-coil-k4-long": 162 + 22}
ONE_VALUE = {"X12", "X13", "X14", "O1", "O2", "O3"}
OPP = {"O1", "O2", "O3"}
T_TEST = max(2.0, math.sqrt(2 * math.log(N_STUDY)))
SEED = 20261015


def lineage(s):
    return LINEAGE_N["CWT14" if s.startswith("CWT14") else s]


def readout(d):
    r = d["r"].to_numpy(float)
    if not len(r):
        return {}
    w, l = r[r > 0], r[r <= 0]
    aw, al = (w.mean() if len(w) else np.nan), (l.mean() if len(l) else np.nan)
    be = -al / (aw - al) if len(w) and len(l) else np.nan
    lo = d[d["r"] <= 0]
    return {"avg_win": round(aw, 4), "avg_loss": round(al, 4), "be_win": round(be, 4),
            "win_margin": round((r > 0).mean() - be, 4) if np.isfinite(be) else np.nan,
            "losers_never_worked": round(float((lo["mfe"] < 0.2).mean()), 3) if len(lo) else np.nan}


def hist_detail(T, reg):
    txt = ["Educational only - not financial advice. BACKTEST (open two-year history, TRAIN+VALID, production + tod costs).",
           "Parents only. code: 1 target, 2 stop, 6 flatten at 15:55.", ""]
    rows = []
    for s, d in T[(T["var"] == "P") & (T.split != "hold")].groupby("setup", observed=True):
        r = d["r"]
        w, l = d[r > 0], d[r <= 0]
        ro = readout(d)
        rows.append({"setup": s, "n": len(d), "win": round((r > 0).mean(), 4), "exp": round(r.mean(), 4), **ro,
                     "mfe_med": round(d.mfe.median(), 3), "mae_med": round(d.mae.median(), 3),
                     "loser_giveback": round((l.mfe - l.r).mean(), 3), "losers_mfe_ge_05": round(float((l.mfe >= 0.5).mean()), 3),
                     "winners_mae_le_m075": round(float((w.mae <= -0.75).mean()), 3),
                     "share_stop": round(float((d.code == 2).mean()), 3), "share_flat": round(float((d.code == 6).mean()), 3)})
        txt.append(f"=== {s}  n {len(d)}")
        b = pd.cut(d["tod"], [0, 959, 1029, 1129, 1259, 1359, 1600],
                   labels=["09:50-09:55", "10:00-10:25", "10:30-11:25", "11:30-12:55", "13:00-13:55", "14:00-15:00"])
        txt.append("by entry time:\n" + d.groupby(b, observed=True)["r"].agg(["size", "mean", lambda x: (x > 0).mean()]).round(4).to_string())
        rg = d["date"].map(reg["regime"])
        txt.append("by session regime:\n" + d.groupby(rg.to_numpy())["r"].agg(["size", "mean", lambda x: (x > 0).mean()]).round(4).to_string())
        txt.append("losers by MFE reached (R):\n" + l.groupby(pd.cut(l.mfe, [-.01, .1, .2, .3, .5, 5]), observed=True)["r"].agg(["size", "mean"]).round(3).to_string())
        txt.append("winners by MAE (R):\n" + w.groupby(pd.cut(w.mae, [-5, -.75, -.5, -.25, .01]), observed=True)["r"].agg(["size", "mean"]).round(3).to_string())
        txt.append("")
    H = pd.DataFrame(rows)
    (OUT / "hist_parent_detail.txt").write_text(H.to_string() + "\n\n" + "\n".join(txt))
    return H


def main():
    T = pd.read_parquet(SCR / "trades.parquet")
    for c in ("setup", "var", "knob", "symbol"):
        T[c] = T[c].astype(str)
    T["date"] = pd.to_datetime(T["date"]).dt.date
    T["split"] = split(pd.Series(T["date"]))
    sig_n = T.groupby(["setup", "var"])["filled"].agg(["size", "mean"])
    T = T[T.filled].copy()
    T["r"] = T["r"].astype(float)
    reg = lib.regimes()
    reg.index = pd.to_datetime(reg.index).date
    H = hist_detail(T, reg)
    print(H.to_string())
    rows = []
    for (s, v), d in T.groupby(["setup", "var"], sort=False):
        p = T[(T.setup == s) & (T["var"] == "P")]
        tv, ptv = d[d.split != "hold"], p[p.split != "hold"]
        st = {k: gates.summary(d[d.split == k]) for k in ("train", "valid")}
        sp = {k: gates.summary(p[p.split == k]) for k in ("train", "valid")}
        a = gates.summary(tv)
        rs = gates.regime_split(tv, reg)
        wf = gates.walk_forward(tv, exclude_months=lib.LOCKED_MONTHS)
        ex = gates.summary(tv.assign(r=tv["r"] - tv["ctrl"]).dropna(subset=["r"]))
        ro = readout(tv)
        pro = readout(ptv)
        opp = v in OPP
        bar_set = gates.t_required(GRID_N[s])
        LN = lineage(s)
        bar_lin = gates.t_required(LN)
        if v == "P" or opp:
            dtr = dva = dtv = timp = np.nan
            beats = opp and st["train"].get("exp_r", -1) > 0 and st["valid"].get("exp_r", -1) > 0 and (a.get("t") or 0) >= bar_set
        else:
            dtr = st["train"].get("exp_r", np.nan) - sp["train"].get("exp_r", np.nan)
            dva = st["valid"].get("exp_r", np.nan) - sp["valid"].get("exp_r", np.nan)
            dtv, timp = boot_diff(tv, ptv, 1000, SEED)
            beats = dtr > 0 and dva > 0 and timp >= bar_set
        core = (bool(beats) and st["train"].get("exp_r", -1) > 0 and st["valid"].get("exp_r", -1) > 0 and (a.get("t") or 0) >= T_TEST
                and rs["pass"] and (wf.get("share_positive") or 0) >= 0.6 and (a.get("ex_best_day") or -1) > 0
                and (ex.get("exp_r") or -1) > 0)
        verdict, fails = gates.verdict(a, rs, wf, LN)
        rows.append({"setup": s, "var": v, "knob": d["knob"].iloc[0], "is_parent": v == "P",
                     "signals": int(sig_n.loc[(s, v), "size"]), "fill_rate": round(float(sig_n.loc[(s, v), "mean"]), 3),
                     "n_train": st["train"].get("n"), "exp_train": st["train"].get("exp_r"), "t_train": st["train"].get("t"),
                     "n_valid": st["valid"].get("n"), "exp_valid": st["valid"].get("exp_r"), "t_valid": st["valid"].get("t"),
                     "n_tv": a.get("n"), "per_day_tv": round(a.get("n", 0) / max(1, a.get("days", 1)), 1),
                     "win_tv": a.get("win_rate"), **ro, "d_win": round(a.get("win_rate", np.nan) - gates.summary(ptv)["win_rate"], 4),
                     "d_margin": round(ro.get("win_margin", np.nan) - pro.get("win_margin", np.nan), 4),
                     "exp_tv": a.get("exp_r"), "t_tv": a.get("t"), "ex_best_day": a.get("ex_best_day"),
                     "up": rs["up"].get("exp_r"), "down": rs["down"].get("exp_r"), "flat": rs["flat"].get("exp_r"),
                     "wf_share": wf.get("share_positive"), "excess_vs_random": ex.get("exp_r"), "excess_t": ex.get("t"),
                     "d_train": round(dtr, 4), "d_valid": round(dva, 4), "d_tv": round(dtv, 4), "t_improve": round(timp, 2),
                     "bar_setup": bar_set, "bar_lineage": bar_lin, "beats_parent": bool(beats),
                     "t_improve_vs_lineage_bar": bool(np.isfinite(timp) and timp >= bar_lin),
                     "testing_core": bool(core), "t_testing_bar": round(T_TEST, 2), "lineage_N": LN,
                     "research_verdict": verdict, "research_fails": "; ".join(fails)})
    R = pd.DataFrame(rows)
    pl = []
    for r in R.itertuples():
        if r.is_parent:
            pl.append(None)
        elif r.var in ONE_VALUE:
            pl.append("needs +-50% check")
        else:
            sib = R[(R.setup == r.setup) & (R.knob == r.knob) & (R["var"] != r.var)]
            pl.append(bool((sib.exp_tv > 0).any()))
    R["plateau"] = pl
    R["testing_bar"] = R.testing_core & (R.plateau == True)  # noqa: E712
    R["needs_plateau_check"] = R.testing_core & (R.plateau == "needs +-50% check")
    hold = {}
    for r in R[R.testing_bar].itertuples():
        d = T[(T.setup == r.setup) & (T["var"] == r.var) & (T.split == "hold")]
        hold[(r.setup, r.var)] = gates.summary(d)
    R["hold_exp"] = [hold.get((a, b), {}).get("exp_r") for a, b in zip(R.setup, R["var"])]
    R["hold_t"] = [hold.get((a, b), {}).get("t") for a, b in zip(R.setup, R["var"])]
    R["hold_n"] = [hold.get((a, b), {}).get("n") for a, b in zip(R.setup, R["var"])]
    R = R.sort_values(["is_parent", "beats_parent", "setup"], ascending=[True, True, True], kind="mergesort")
    R.to_csv(OUT / "results.csv", index=False)
    summ = {"n_study": N_STUDY, "n_scored": int((~R.is_parent).sum()), "t_testing_bar": round(T_TEST, 2),
            "beats_parent": R[R.beats_parent][["setup", "var"]].values.tolist(),
            "testing_bar": R[R.testing_bar][["setup", "var"]].values.tolist(),
            "needs_plateau_check": R[R.needs_plateau_check][["setup", "var"]].values.tolist(),
            "research_keep": R[(R.research_verdict == "keep") & ~R.is_parent][["setup", "var"]].values.tolist(),
            "exp_tv_positive": R[(R.exp_tv > 0) & ~R.is_parent][["setup", "var"]].values.tolist(),
            "improve_train_and_valid": R[(R.d_train > 0) & (R.d_valid > 0)][["setup", "var"]].values.tolist(),
            "hold_scored": {f"{a}|{b}": v for (a, b), v in hold.items()}}
    json.dump(summ, open(OUT / "summary.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 300)
    pd.set_option("display.max_rows", 200)
    print(R[["setup", "var", "knob", "fill_rate", "n_tv", "per_day_tv", "win_tv", "avg_win", "avg_loss", "be_win", "win_margin",
             "exp_tv", "t_tv", "exp_train", "exp_valid", "up", "down", "wf_share", "excess_vs_random", "d_tv", "t_improve",
             "beats_parent", "testing_bar"]].to_string())
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
