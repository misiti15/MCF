"""Stage 3: configurations passing the TRAIN screen gate are scored on VALID (held back) and on all open data
(regime gate, walk-forward, both random controls). Writes results.csv (every configuration; valid columns where
scored), finalists.json, counts.json. Usage: python stage3.py <rows_dir> <out_dir>. Educational only - not financial advice."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import GROUP, LINEAGE_PRIOR  # noqa: E402
from engine import Panel, cond_mat, first_trades, stats_split, trade_frame  # noqa: E402

from mcf.research import gates  # noqa: E402
from mcf.research.arena.indicators import INDICATORS  # noqa: E402

ROWS, OUT = sys.argv[1], Path(sys.argv[2])
R = pd.read_csv(OUT / "results_train.csv")
cnt = json.load(open(OUT / "count_stages.json"))
N_here = sum(cnt.values())
N_lin = sum(LINEAGE_PRIOR.values()) + N_here
bar = gates.t_required(N_lin)
P = Panel(ROWS)
cache = {}
LOCKED = ("2024-11", "2024-12", "2025-01", "2025-02")


def parse(s):
    return [(a, b, tuple(v) if isinstance(v, list) else v) for a, b, v in json.loads(s)]


def full(conds, side, geom, w):
    M = P.win_mask(w)[None, :]
    for c in conds:
        M = M & cond_mat(P, cache, c)
    sd, k, r, c, e = first_trades(P, M, f"{side}_{geom}")
    t = trade_frame(P, sd, k, r, c, e)
    tr, va = stats_split(P, sd, r, c, e, 0), stats_split(P, sd, r, c, e, 1)
    reg = gates.regime_split(t[["date", "r"]], P.regimes_df)
    wf = gates.walk_forward(t[["date", "r"]], exclude_months=LOCKED)
    allS = gates.summary(t[["date", "r"]])
    out = {"va_" + k_: v for k_, v in va.items()}
    out.update({"all_n": allS["n"], "all_exp": allS["exp_r"], "all_t": allS["t"], "ex_best_day": allS["ex_best_day"],
                "reg_up": reg["up"].get("exp_r"), "reg_down": reg["down"].get("exp_r"), "reg_flat": reg["flat"].get("exp_r"),
                "reg_n_up": reg["up"].get("n", 0), "reg_n_down": reg["down"].get("n", 0), "regime_pass": reg["pass"],
                "wf_share": wf["share_positive"], "wf_folds": wf["n_folds"],
                "per_day": round(len(t) / len(P.dates), 3),
                "lev_share": round(float(t.symbol.map(GROUP).eq("lev").mean()), 3) if len(t) else None,
                "top_symbol_share": round(float(t.symbol.value_counts(normalize=True).iloc[0]), 3) if len(t) else None})
    g = {"n_total>=200": allS["n"] >= 200, "exp_train>0": tr["exp"] > 0, "exp_valid>0": (va.get("exp") or -1) > 0,
         "t_train>=bar": (tr["t"] or 0) >= bar, "regime": bool(reg["pass"]), "wf>=0.6": (wf["share_positive"] or 0) >= 0.6,
         "beats_random_train": tr["exc_c"] > 0 and tr["exc_e"] > 0,
         "beats_random_valid": (va.get("exc_c") or -1) > 0 and (va.get("exc_e") or -1) > 0,
         "live": all(INDICATORS[c[0]].live for c in conds)}
    out["gates_failed"] = ",".join(k_ for k_, v in g.items() if not v)
    out["quality_pass"] = all(g.values())
    out["near_miss"] = all(v for k_, v in g.items() if k_ != "t_train>=bar")
    return out, t


extra = []
G = R[R.gate_train]
print("train-gate", len(G), "N_here", N_here, "N_lineage", N_lin, "bar", bar, flush=True)
for r in G.itertuples():
    w = tuple(int(v) for v in r.window.split("-"))
    o, _ = full(parse(r.conds), r.side, r.geom, w)
    extra.append({"idx": r.Index, **o})
X = pd.DataFrame(extra).set_index("idx") if extra else pd.DataFrame()
RR = R.join(X) if len(X) else R
RR.to_csv(HERE / "results.csv", index=False, float_format="%.4g")
fin = RR[RR.get("near_miss", pd.Series(False, index=RR.index)).fillna(False).astype(bool)] if len(X) else RR.iloc[:0]
fin = fin.sort_values("tr_t", ascending=False)
fin.to_json(HERE / "finalists.json", orient="records", indent=1)
vpos = int(((X["va_exp"] > 0) & (X["va_exc_e"] > 0) & (X["va_exc_c"] > 0)).sum()) if len(X) else 0
json.dump({"configs_scored": N_here, "by_stage": cnt, "lineage_prior": LINEAGE_PRIOR, "N_lineage": N_lin,
           "bar": bar, "train_gate": int(len(G)), "valid_positive_beats_random": vpos,
           "quality_pass": int(RR.get("quality_pass", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()),
           "near_miss": int(len(fin))}, open(HERE / "counts.json", "w"), indent=1)
print(json.load(open(HERE / "counts.json")))
