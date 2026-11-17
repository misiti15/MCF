"""Mechanic NM-RWN5: engine view + every live teardown chart (8 live trades: worst4 + best4 = all of them).
Educational only - not financial advice."""
from pathlib import Path
from common import WT, SETUP
from mcf.report import blueprint as B
out = Path(WT) / "research/workbench" / SETUP
for how in ("best4", "worst4"):
    B.build(SETUP, out, style="engine", trades=how)
    for f in sorted(out.glob(f"{SETUP}_trade*_*.png")):
        k, rest = f.name[len(SETUP) + 6:].split("_", 1)
        f.rename(out / f"{SETUP}_{how[:-1]}{k}_{rest}")
print(sorted(p.name for p in out.glob("*.png")))
