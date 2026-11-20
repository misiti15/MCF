"""REMEDY-Q part 1, 2-year lab, the normal way: research/ultimate_1119/top10/bench10.py signals + 1-minute exits
(trades_t1.parquet of its WORK dir, live configs of 11-19, 2024-10-01..2026-11-04), costs add_r (LR8 basis + borrow),
the live book (bench10.book) applied AFTER the rule, so a cut changes caps/latch exactly as live would.
Views: Primary rules (cap 30, -2R latch, no CF; the parents' home) and Testing rules (cap 100, CF 0.15; where copies run).
FIT = 2024-10 + 2025-03-01..09-30, CHECK = 2025-10-01..2026-11-04; 2024-11-01..2025-02-28 never read (bench10 asserts).
Rules (all remove entries only, before the book):
  cut_C        no entry bar with close HHMM > C (window [950, C])
  sal_<x>_C    cut at C, but after C keep entries that pass x: mkt (QQQ since 09:30 open moves with the trade),
               gap4 (gap <= -4%), first (no signal of the setup on that symbol earlier that day), cost08 (stop cost R <= 0.08)
  b_gate       L3 only: gap > -5% and ATR >= 5% of price (ATR = 4 x risk for t1s1)
  c_gate       RW3/RW5 only: gap <= -1%
Usage (from this folder): python lab_tod.py TRADES_T1 ETB .   Educational only - not financial advice."""
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as pads

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from common import CUTOFFS, SHORT, TRIO, paired_day_t, st  # noqa: E402

spec = importlib.util.spec_from_file_location("bench10", ROOT / "research/ultimate_1119/top10/bench10.py")
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)

T = pd.read_parquet(sys.argv[1])
T = T[T.setup.isin(TRIO)].copy()
B.no_locked(T.date.unique())
etb = pd.read_parquet(sys.argv[2]).rate
out = Path(sys.argv[3])
T = B.add_r(T)
T["half"] = B.half(T.date)
T = T[T.half != "none"].reset_index(drop=True)

# QQQ since the 09:30 open at the decision bar close (last 1-minute close before the bar-close minute)
f = pads.field("__index_level_0__")
q = pads.dataset(str(B.CACHE / "QQQ.parquet"), format="parquet").to_table(
    filter=(f < pd.Timestamp(B.LOCK[0], tz=B.TZ)) | (f >= pd.Timestamp("2025-03-01", tz=B.TZ))).to_pandas()
if "__index_level_0__" in q.columns:
    q = q.set_index("__index_level_0__")
q.index = pd.DatetimeIndex(q.index).tz_convert(B.TZ)
q = q[(q.index.hour * 100 + q.index.minute >= 930) & (q.index.hour * 100 + q.index.minute < 1600)]
q = q[q.index.date.astype(str) >= "2024-10-01"]
B.no_locked(np.unique(q.index.date.astype(str)))
qd = pd.DataFrame({"date": q.index.date.astype(str), "m": q.index.hour * 60 + q.index.minute + 1, "c": q.close.values,
                   "o": q.open.values})
op = qd.groupby("date").o.first()
qd["qret"] = (qd.c / qd.date.map(op) - 1) * 100
qmap = qd.set_index(["date", "m"]).qret
T["qret"] = qmap.reindex(pd.MultiIndex.from_arrays([T.date, T.em])).values
SESS = {h: sorted(set(qd.date[B.half(qd.date) == h]) & set(qd.date[qd.date <= T.date.max()])) for h in ("fit", "check")}
T["atr_pct"] = 4 * T.risk / T.entry * 100
first_tod = T.groupby(["setup", "symbol", "date"]).tod.transform("min")
T["first"] = T.tod == first_tod
print("signals", T.groupby(["setup", "half"]).size().to_dict(), "qret NaN", int(T.qret.isna().sum()), "sessions",
      {k: len(v) for k, v in SESS.items()})

SAL = {"mkt": lambda x: (x.side * x.qret) > 0, "gap4": lambda x: x.gap <= -4, "first": lambda x: x["first"],
       "cost08": lambda x: x.stop_cost_r <= 0.08}
PRIM = B.BOOK["primary"]
TEST = B.TESTING_RULES


def rule_mask(x, rule):
    if rule == "base":
        return np.ones(len(x), bool)
    if rule.startswith("cut_"):
        return (x.tod <= int(rule[4:])).to_numpy()
    if rule.startswith("sal_"):
        _, k, c = rule.split("_")
        return ((x.tod <= int(c)) | SAL[k](x)).to_numpy()
    if rule == "b_gate":
        return ((x.gap > -5) & (x.atr_pct >= 5)).to_numpy() if x.setup.iloc[0].startswith("L3") else np.ones(len(x), bool)
    if rule == "c_gate":
        return (x.gap <= -1).to_numpy() if x.setup.iloc[0].startswith("RW") else np.ones(len(x), bool)
    raise ValueError(rule)


CACHE: dict = {}


def booked(setup, rule, view):
    k = (setup, rule, view)
    if k not in CACHE:
        x = T[T.setup == setup]
        CACHE[k] = B.book(x[rule_mask(x, rule)], PRIM if view == "primary" else TEST, etb)
    return CACHE[k]


def row(setup, rule, view, half):
    if setup == "pooled":
        b = pd.concat([booked(s, rule, view) for s in TRIO])
        b0 = pd.concat([booked(s, "base", view) for s in TRIO])
    else:
        b, b0 = booked(setup, rule, view), booked(setup, "base", view)
    b, b0 = b[b.half == half], b0[b0.half == half]
    z = st(b)
    z0 = st(b0)
    return dict(setup=SHORT.get(setup, setup), rule=rule, view=view, half=half, **z,
                r_per_sess=round(z["tot"] / len(SESS[half]), 4), kept_pct=round(100 * len(b) / max(len(b0), 1), 1),
                d_tot=round(z["tot"] - z0["tot"], 2), d_avg=round(z["avg"] - z0["avg"], 4),
                t_paired=round(paired_day_t(b0, b, SESS[half]), 2),
                excess_vs_random=round(z["tot"] - z0["tot"] - (1 - len(b) / max(len(b0), 1)) * (-z0["tot"]), 2))


RULES = ["base"] + [f"cut_{c}" for c in CUTOFFS if c != 1500]
rows = [row(s, r, v, h) for v in ("primary", "testing") for h in ("fit", "check") for s in TRIO + ["pooled"] for r in RULES]
sw = pd.DataFrame(rows)
sw.to_csv(out / "lab_cutoff_sweep.csv", index=False)
pd.set_option("display.width", 250)
pd.set_option("display.max_rows", 500)
cols = ["setup", "rule", "n", "avg", "tot", "wo_best", "tot_wo_top2", "t_day", "kept_pct", "d_tot", "d_avg", "t_paired"]
# --- FIT choice of the cutoff: per-trade quality (d_avg) of the pooled Primary-rules book, smoothed over the two
# one-step neighbours (plateau, not the single best); scored once on CHECK below.
fp = sw[(sw.view == "primary") & (sw.half == "fit") & (sw.setup == "pooled") & sw.rule.str.startswith("cut_")].copy()
fp["c"] = fp.rule.str[4:].astype(int)
fp = fp.sort_values("c").reset_index(drop=True)
fp["smooth"] = fp.d_avg.rolling(3, center=True, min_periods=2).mean()
chosen = int(fp.loc[fp.smooth.idxmax(), "c"])
print("FIT plateau (pooled d_avg smoothed):", fp[["c", "d_avg", "smooth"]].to_dict("records"), "-> chosen", chosen)

# --- slice view: the base book split at the cut (like the live table), per half
sl = []
for v in ("primary", "testing"):
    for h in ("fit", "check"):
        for s_ in TRIO + ["pooled"]:
            b = pd.concat([booked(x, "base", v) for x in TRIO]) if s_ == "pooled" else booked(s_, "base", v)
            b = b[b.half == h]
            for c in (1300, chosen):
                sl.append(dict(view=v, half=h, setup=SHORT.get(s_, s_), cut=c, side="<=", **st(b[b.tod <= c])))
                sl.append(dict(view=v, half=h, setup=SHORT.get(s_, s_), cut=c, side=">", **st(b[b.tod > c])))
sl = pd.DataFrame(sl).drop_duplicates()
sl.to_csv(out / "lab_slice_am_pm.csv", index=False)
print(sl[sl.view == "primary"].to_string(index=False))

# --- after-cut salvage (at 13:00 and at the FIT choice) + (b) + (c)
EXTRA = [f"sal_{k}_{c}" for c in sorted({1300, chosen}) for k in SAL] + ["b_gate", "c_gate"]
rows2 = [row(s_, r, v, h) for v in ("primary", "testing") for h in ("fit", "check") for s_ in TRIO + ["pooled"]
         for r in EXTRA + [f"cut_{c}" for c in sorted({1300, chosen})]]
ex = pd.DataFrame(rows2)
ex.to_csv(out / "lab_salvage_bc.csv", index=False)
cols2 = cols + ["excess_vs_random"]
for v in ("primary", "testing"):
    for h in ("fit", "check"):
        print(f"== EXTRA {v} {h}")
        print(ex[(ex.view == v) & (ex.half == h)][cols2].to_string(index=False))
N = len(RULES) - 1 + len(EXTRA)
json.dump({"chosen_cutoff_fit": chosen, "configs_per_setup": N, "configs_total": 3 * N,
           "t_bar": round(max(1.5, math.sqrt(2 * math.log(3 * N))), 2)}, open(out / "lab_choice.json", "w"))
print("configs", N, 3 * N, "bar", max(1.5, math.sqrt(2 * math.log(3 * N))))
json.dump({"n_signals": int(len(T)), "sessions": {k: len(v) for k, v in SESS.items()}}, open(out / "lab_meta.json", "w"))
