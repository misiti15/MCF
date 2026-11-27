"""PAIRS-1127 diagnostic (information only, not a config): the same 28 rules with ZERO latency - entry and exit at the
decision bar's close instead of the next minute's open - to see whether the residual reversal exists before the first
minute and costs. Usage: python pr_diag.py DATADIR OUTDIR. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr_sim  # noqa: E402

_orig = pr_sim.load


def load0(sym):
    C, O1, O2, dv, nmin = _orig(sym)
    O1z = np.c_[O1[:, :1], C[:, :-1]]       # "fill" at bar j+1 = close of bar j
    return C, O1z, O1z.copy(), dv, nmin


pr_sim.load = load0
pr_sim.load_g = lambda data, sym: load0(sym)

if __name__ == "__main__":
    pr_sim.DATA = Path(sys.argv[1])
    pr_sim.main(sys.argv[1], sys.argv[2])
