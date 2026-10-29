"""bar90_1029: full BAR90 gate check on re-scored trades (pod1022 score_batch --trades-dir output).

Gates (RESEARCH_RULES 19 + 22): costs in (score_batch production costs), day-clustered t >= BAR90(N), exp > 0 in
up AND down sessions (rule-19 terciles of the universe median open-to-close, cut points on open sessions only,
n >= 30 each), walk-forward share of positive test months >= 0.54 (3-month train / 1-month test, locked months
skipped), beats the same-minute random control, avg R without the best session and its share of total R (flag >= 50%).
Locked block: only with --locked (the lead's one look per version; needs MCF_HIST_ALLOW_LOCKED=1 in the scorer run).

Usage: python research/bdi/bar90_1029/evaluate.py TRADES_DIR NAME=N [NAME=N ...] [--locked]
Educational only - not financial advice.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

from mcf.research import gates  # noqa: E402

TRAIN_END = pd.Timestamp("2025-12-31")


def bar90(n):
    return max(1.35, 0.9 * max(1.5, math.sqrt(2 * math.log(max(n, 1)))))


def evaluate(tr: pd.DataFrame, n_lineage: int, locked: bool = False) -> dict:
    tr = tr.copy()
    tr["date"] = pd.to_datetime(tr["date"]).dt.date
    rcol = "r" if "r" in tr else next(c for c in tr.columns if c in ("R", "r_prod", "rr"))
    tr["r"] = tr[rcol].astype(float)
    s = gates.summary(tr)
    g = tr.groupby("date")["r"].sum()
    best = g.idxmax()
    out = {"n": s["n"], "days": s["days"], "exp_2y": s["exp_r"], "t": s["t"], "win": s["win_rate"],
           "ex_best_day": s["ex_best_day"], "best_day": str(best),
           "best_share": round(float(g.max() / g.sum()), 3) if g.sum() > 0 else None,
           "top3_share": round(float(g.nlargest(3).sum() / g.sum()), 3) if g.sum() > 0 else None,
           "best_day_trades": int((tr["date"] == best).sum()), "per_day": round(s["n"] / 426, 3)}
    if locked:
        out["bar_note"] = "locked block"
        return out
    d = pd.to_datetime(pd.Series(tr["date"]))
    trn, val = tr[(d <= TRAIN_END).to_numpy()], tr[(d > TRAIN_END).to_numpy()]
    st, sv = gates.summary(trn), gates.summary(val)
    out.update(n_train=st.get("n"), exp_train=st.get("exp_r"), t_train=st.get("t"),
               n_valid=sv.get("n"), exp_valid=sv.get("exp_r"), t_valid=sv.get("t"))
    reg = lib.regimes()
    rs = gates.regime_split(tr, reg)
    out.update(up_n=rs["up"].get("n"), up_exp=rs["up"].get("exp_r"), down_n=rs["down"].get("n"),
               down_exp=rs["down"].get("exp_r"), flat_exp=rs["flat"].get("exp_r"), regime_pass=rs["pass"])
    # regime split without the best day (one-big-day check on the regime gate)
    rs2 = gates.regime_split(tr[tr["date"] != best], reg)
    out.update(up_exp_xbest=rs2["up"].get("exp_r"), down_exp_xbest=rs2["down"].get("exp_r"))
    wf = gates.walk_forward(tr, exclude_months=lib.LOCKED_MONTHS)
    out.update(wf_share=wf["share_positive"], wf_folds=wf["n_folds"])
    if "ctrl" in tr:
        ex = tr["r"] - tr["ctrl"].astype(float)
        e2 = tr.assign(r=ex)
        se = gates.summary(e2)
        out.update(excess=se["exp_r"], excess_t=se["t"])
    out["N_lineage"] = n_lineage
    out["bar90"] = round(bar90(n_lineage), 3)
    fails = []
    if not (out["exp_2y"] and out["exp_2y"] > 0):
        fails.append("exp<=0")
    if not ((out["t"] or 0) >= out["bar90"]):
        fails.append(f"t {out['t']} < {out['bar90']}")
    if not rs["pass"]:
        fails.append("regime")
    if not ((out["wf_share"] or 0) >= 0.54):
        fails.append(f"wf {out['wf_share']} < 0.54")
    if "excess" in out and not (out["excess"] > 0):
        fails.append("random")
    out["fails"] = fails
    out["clears_bar90"] = not fails
    out["one_day_flag"] = bool(out["best_share"] is not None and out["best_share"] >= 0.5)
    return out


def main(argv):
    locked = "--locked" in argv
    argv = [a for a in argv if a != "--locked"]
    tdir = Path(argv[0])
    res = {}
    for spec in argv[1:]:
        name, n = spec.split("=")
        f = tdir / f"{name}.parquet"
        tr = pd.read_parquet(f)
        res[name] = evaluate(tr, int(float(n)), locked=locked)
        print(name, json.dumps(res[name], default=str))
    return res


if __name__ == "__main__":
    main(sys.argv[1:])
