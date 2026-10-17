"""Threshold-neighbourhood check of the best near-miss (ret12 <= q05 & gap_atr <= q20 & rvol_day <= median, long t1s1
09:50-11:00): each threshold moved to the adjacent screen quantiles. 27 grid points (26 new configurations, counted).
python research/swarm1017/arena-am-long/neighbors.py <scratch rows dir>. Educational only - not financial advice."""
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import search  # noqa: E402
from mcf.research.arena.combine import evaluate_combo  # noqa: E402

N = 20282 + 23032 + 26
A = search.load_rows(["symbol", "date", "tod", "r_long_t1s1", "c_long_t1s1", "ret12", "gap_atr", "rvol_day"])
out = []
for a, b, c in itertools.product([-1.0594, -1.6145, -2.2], [-0.2207, -0.4056, -0.6103], [0.4297, 0.6515, 0.80]):
    e = evaluate_combo(A, [("ret12", "<=", a), ("gap_atr", "<=", b), ("rvol_day", "<=", c)], "long", "t1s1", (950, 1100), n_lineage=N)
    row = {"ret12": a, "gap_atr": b, "rvol_day": c, "n_tr": e["train"]["n"], "exp_tr": e["train"]["exp_r"], "t_tr": e["train"]["t"],
           "n_va": e["valid"]["n"], "exp_va": e["valid"]["exp_r"], "t_va": e["valid"]["t"], "x_va": e["valid"]["excess"],
           "up": e["regime"]["up"].get("exp_r"), "down": e["regime"]["down"].get("exp_r"), "wf": e["walk_forward"]["share_positive"],
           "per_day": e["per_day"], "fails": [k for k, v in e["gates"].items() if not v]}
    out.append(row)
    print(row, flush=True)
(Path(__file__).resolve().parent / "neighbors.json").write_text(json.dumps(out, indent=1))
