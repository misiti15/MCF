"""top5_1014 report: score every variant of scan_top5.py against PLAN.md's pre-declared bars.
Educational only - not financial advice.

    python research/bdi/top5_1014/report_top5.py    # -> results.csv, summary.json
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
sys.path[:0] = [str(ROOT / "research" / "history2y"), str(ROOT)]
import lib  # noqa: E402
from mcf.research import gates  # noqa: E402

OUT = Path(__file__).resolve().parent
SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/top5_1014")
N_STUDY = 75
LINEAGE = {"CWT14": 121_089, "heat_fade_short-FD": 19_706, "RW7-gapdn-bounce-early-short-FD": 82_964}
GRID_N = {"CWT14-failbrk-orl-p05-long": 14, "CWT14-failbrk-orl-p05-lowvol-long": 16, "CWT14-failbrk-pdl-p05-long": 14,
          "heat_fade_short-FD": 15, "RW7-gapdn-bounce-early-short-FD": 16}
ONE_VALUE = {"V13", "V14", "H11", "H12", "H13", "R07"}
T_TEST = max(2.0, math.sqrt(2 * math.log(N_STUDY)))


def split(d):
    s = pd.to_datetime(pd.Series(d)).dt.strftime("%Y-%m-%d")
    hold = ((s >= "2026-04-01") & (s <= "2026-06-30")) | (s >= "2026-09-16")
    train = s <= "2025-12-31"
    return np.where(hold, "hold", np.where(train, "train", "valid"))


def lineage_n(setup):
    k = "CWT14" if setup.startswith("CWT14") else setup
    return LINEAGE[k] + sum(v for s, v in GRID_N.items() if (s.startswith("CWT14") if k == "CWT14" else s == k))


def boot_diff(v, p, B=1000, seed=20261014):
    """Day-block bootstrap of exp(v) - exp(p) on the same session set."""
    dv = v.groupby("date")["r"].agg(["sum", "size"])
    dp = p.groupby("date")["r"].agg(["sum", "size"])
    days = dv.index.union(dp.index)
    dv, dp = dv.reindex(days, fill_value=0), dp.reindex(days, fill_value=0)
    a = np.c_[dv["sum"], dv["size"], dp["sum"], dp["size"]].astype(float)
    rng = np.random.default_rng(seed)
    out = np.empty(B)
    for b in range(B):
        x = a[rng.integers(0, len(a), len(a))].sum(0)
        out[b] = x[0] / max(x[1], 1) - x[2] / max(x[3], 1)
    obs = a[:, 0].sum() / a[:, 1].sum() - a[:, 2].sum() / a[:, 3].sum()
    se = out.std(ddof=1)
    return obs, (obs / se if se > 0 else np.nan)


def main():
    T = pd.read_parquet(SCR / "trades.parquet")
    T["date"] = pd.to_datetime(T["date"]).dt.date
    T["split"] = split(pd.Series(T["date"]))
    reg = lib.regimes()
    reg.index = pd.to_datetime(reg.index).date
    rows = []
    for (s, v), d in T.groupby(["setup", "var"], sort=False):
        p = T[(T.setup == s) & (T["var"] == "P")]
        tv, ptv = d[d.split != "hold"], p[p.split != "hold"]
        st = {k: gates.summary(d[d.split == k]) for k in ("train", "valid")}
        sp = {k: gates.summary(p[p.split == k]) for k in ("train", "valid")}
        a = gates.summary(tv)
        full = gates.summary(d)
        rs = gates.regime_split(tv, reg)
        wf = gates.walk_forward(tv, exclude_months=lib.LOCKED_MONTHS)
        ex = gates.summary(tv.assign(r=tv["r"] - tv["ctrl"]).dropna(subset=["r"]))
        dtr = st["train"].get("exp_r", np.nan) - sp["train"].get("exp_r", np.nan)
        dva = st["valid"].get("exp_r", np.nan) - sp["valid"].get("exp_r", np.nan)
        dtv, timp = (np.nan, np.nan) if v == "P" else boot_diff(tv, ptv)
        nset = GRID_N[s]
        bar_imp = gates.t_required(nset)
        LN = lineage_n(s)
        beats = v != "P" and dtr > 0 and dva > 0 and (timp or 0) >= bar_imp
        core = (beats and st["train"].get("exp_r", -1) > 0 and st["valid"].get("exp_r", -1) > 0 and (a.get("t") or 0) >= T_TEST
                and rs["pass"] and (wf.get("share_positive") or 0) >= 0.6 and (a.get("ex_best_day") or -1) > 0
                and (ex.get("exp_r") or -1) > 0)
        verdict, fails = gates.verdict(a, rs, wf, LN)
        rows.append({"setup": s, "var": v, "knob": d["knob"].iloc[0], "is_parent": v == "P",
                     "n_full_open": full.get("n"), "win_full_open": full.get("win_rate"), "exp_full_open": full.get("exp_r"), "t_full_open": full.get("t"),
                     "n_train": st["train"].get("n"), "exp_train": st["train"].get("exp_r"), "t_train": st["train"].get("t"),
                     "n_valid": st["valid"].get("n"), "exp_valid": st["valid"].get("exp_r"), "t_valid": st["valid"].get("t"),
                     "n_tv": a.get("n"), "days_tv": a.get("days"), "per_day_tv": round(a.get("n", 0) / max(1, a.get("days", 1)), 1),
                     "win_tv": a.get("win_rate"), "exp_tv": a.get("exp_r"), "t_tv": a.get("t"), "ex_best_day": a.get("ex_best_day"),
                     "up": rs["up"].get("exp_r"), "down": rs["down"].get("exp_r"), "flat": rs["flat"].get("exp_r"),
                     "wf_share": wf.get("share_positive"), "excess_vs_random": ex.get("exp_r"), "excess_t": ex.get("t"),
                     "d_train": round(dtr, 4), "d_valid": round(dva, 4), "d_tv": None if v == "P" else round(dtv, 4),
                     "t_improve": None if v == "P" else round(timp, 2), "bar_improve": bar_imp, "beats_parent": beats,
                     "testing_core": core, "t_testing_bar": round(T_TEST, 2), "lineage_N": LN, "t_research_bar": gates.t_required(LN),
                     "research_verdict": verdict, "research_fails": "; ".join(fails)})
    R = pd.DataFrame(rows)
    # plateau (PLAN section 4): another value of the same knob with exp_tv > 0
    pl = []
    for r in R.itertuples():
        if r.is_parent or r.var in ONE_VALUE:
            pl.append(None if r.is_parent else "needs +-50% check")
            continue
        sib = R[(R.setup == r.setup) & (R.knob == r.knob) & (R["var"] != r.var)]
        pl.append(bool((sib.exp_tv > 0).any()))
    R["plateau"] = pl
    R["testing_bar"] = R.testing_core & (R.plateau == True)  # noqa: E712
    R["needs_plateau_check"] = R.testing_core & (R.plateau == "needs +-50% check")
    # HOLD: scored once, only for testing-bar variants
    hold = {}
    for r in R[R.testing_bar].itertuples():
        d = T[(T.setup == r.setup) & (T["var"] == r.var) & (T.split == "hold")]
        hold[(r.setup, r.var)] = gates.summary(d)
    R["hold_exp"] = [hold.get((a, b), {}).get("exp_r") for a, b in zip(R.setup, R["var"])]
    R["hold_t"] = [hold.get((a, b), {}).get("t") for a, b in zip(R.setup, R["var"])]
    R["hold_n"] = [hold.get((a, b), {}).get("n") for a, b in zip(R.setup, R["var"])]
    R.to_csv(OUT / "results.csv", index=False)
    summ = {"n_study": N_STUDY, "n_scored": int((~R.is_parent).sum()), "t_testing_bar": round(T_TEST, 2),
            "beats_parent": R[R.beats_parent][["setup", "var"]].values.tolist(),
            "testing_bar": R[R.testing_bar][["setup", "var"]].values.tolist(),
            "needs_plateau_check": R[R.needs_plateau_check][["setup", "var"]].values.tolist(),
            "research_keep": R[(R.research_verdict == "keep") & ~R.is_parent][["setup", "var"]].values.tolist(),
            "exp_tv_positive": R[(R.exp_tv > 0) & ~R.is_parent][["setup", "var"]].values.tolist(),
            "hold_scored": {f"{a}|{b}": v for (a, b), v in hold.items()}}
    json.dump(summ, open(OUT / "summary.json", "w"), indent=1, default=str)
    pd.set_option("display.width", 250)
    print(R[["setup", "var", "knob", "n_tv", "per_day_tv", "win_tv", "exp_tv", "t_tv", "exp_train", "exp_valid", "up", "down",
             "wf_share", "excess_vs_random", "d_tv", "t_improve", "beats_parent", "testing_bar", "plateau"]].to_string())
    print(json.dumps(summ, indent=1, default=str))


if __name__ == "__main__":
    main()
