"""Full combine.evaluate_combo of the near-miss seeds at all 3 geometries, window 10:00-11:00 (these 9 configurations
are already counted in stability.py's 243). Educational only - not financial advice."""
import json
import sys
from pathlib import Path

sys.argv = sys.argv[:2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import search as S  # noqa: E402
from mcf.research.arena.combine import evaluate_combo  # noqa: E402

N = 20282 + 22932 + 243
SEEDS = {
    "N1": [("sma20_slope_pct", "<=", -0.7373), ("day_vs_prev_range", "<=", 0.4091), ("buyPressure", ">=", 0.3115)],
    "N2": [("vwapDistPct", ">=", 0.9177), ("day_vs_prev_range", "<=", 0.4091), ("di_diff7", "<=", 0.0)],
    "N3": [("rv12", ">=", 0.6005), ("day_vs_prev_range", "<=", 0.4091), ("from_pc_atr", "<=", -0.3489)],
}
names = sorted({c[0] for v in SEEDS.values() for c in v})
A = S.load_rows(["symbol", "date", "tod"] + [f"{p}_short_{g}" for p in ("r", "c") for g in S.GEOMS] + names)
out = []
for sid, cs in SEEDS.items():
    for g in S.GEOMS:
        e = evaluate_combo(A, cs, "short", g, (1000, 1100), n_lineage=N)
        e["seed"] = sid
        out.append(e)
        print(sid, g, e["train"].get("exp_r"), e["train"].get("t"), e["valid"].get("exp_r"), e["valid"].get("t"),
              e["regime"]["up"]["exp_r"], e["regime"]["down"]["exp_r"], e["walk_forward"]["share_positive"], e["per_day"],
              [k for k, v in e["gates"].items() if not v], flush=True)
Path(Path(__file__).resolve().parent / "nearmiss.json").write_text(json.dumps(out, indent=1, default=str))
