"""Rework BEG-06 (PLAN.md): the beginner runner (research/beginner_1120/BEG-06-noise-area-breakout/run.py, bench10
normal way) with this folder's variants and scratch dir.  python rw06.py fit|check NAME [NAME...]
Educational only - not financial advice."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = HERE.parents[3] / "research/beginner_1120/BEG-06-noise-area-breakout"
sys.path.insert(0, str(SRC))
import run as R  # noqa: E402
R.HERE = HERE / "beg06"; R.WORK = HERE.parent / "scratch/beg06"; R.ETB = HERE.parent / "scratch/etb_rate.parquet"
part = sys.argv[1]
for name in sys.argv[2:]:
    st, _ = R.score(name, part)
    print(name, part, json.dumps({k: st.get(k) for k in ("trades", "avg_r", "avg_r_gross", "avg_r_wo_best_day", "best_day",
          "best_day_share", "total_r", "t_day_clustered", "avg_r_spy_up", "avg_r_spy_flat", "avg_r_spy_down", "by_side",
          "by_symbol", "exit_mix")}, default=float), flush=True)
