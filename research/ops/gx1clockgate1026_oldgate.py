"""GX1 evidence (2026-10-26): replay with the PRE-GX1 bar-count gate (len(bars) % 5 == 0), in-process only.
lab_decision_buckets is the single gate function used by LabStrategy.eligible, the runner's per-bucket tracking and the
replay fast path; here it answers as the old test did: eligible iff n >= 5 and n % 5 == 0, window on the latest bar + 1 min.

    PYTHONPATH=. python research/ops/gx1clockgate1026_oldgate.py <python -m mcf.replay run arguments>

Research only; nothing here trades. Educational only - not financial advice."""
import sys

import pandas as pd

from mcf.strategies import setups as S

_F = pd.Timedelta(minutes=4)


def old(index):
    n = len(index)
    if n >= 5 and n % 5 == 0:
        return [index[-1] - _F]          # b + 5 min = latest bar + 1 min: the old window check
    return []


S.lab_decision_buckets = old
if __name__ == "__main__":
    from mcf.replay.__main__ import main
    main(["run", *sys.argv[1:]])
