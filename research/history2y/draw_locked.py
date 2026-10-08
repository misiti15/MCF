"""Random draw of the multi-year locked block (RESEARCH_RULES rule 19), done 2026-10-08 BEFORE any setup was scored on
the 2-year history. Candidate blocks: contiguous 4, 5 or 6 calendar months inside 2024-10 .. 2026-02 (the new history
before the existing data: data/cache_q2 starts 2026-03-10). Length drawn first (uniform), then the start (uniform over
the blocks that fit). Re-running prints the same block. Educational only - not financial advice."""
import numpy as np
import pandas as pd

SEED = 20261008
rng = np.random.default_rng(SEED)
months = pd.period_range("2024-10", "2026-02", freq="M")
L = int(rng.choice([4, 5, 6]))
starts = [i for i in range(len(months)) if i + L <= len(months)]
s = int(rng.choice(starts))
lo, hi = months[s].start_time.date(), months[s + L - 1].end_time.date()
print(f"seed {SEED}: {L} months, {lo} .. {hi} ({len(starts)} possible starts for that length)")
